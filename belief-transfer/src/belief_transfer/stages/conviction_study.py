"""Frozen exploratory comparison, independent fresh passes, raw-first outputs."""
import asyncio
import json

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.conviction_report import write_conviction_report
from belief_transfer.analysis.report import ROOT, build_result, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.evals.conviction_scale import build_scale_bank, extract_scale, balanced_fields, joint_completions, extract_judgment, reflection_prompt
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.evals.suite import load_rows, write_rows
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference.local import local_model
from belief_transfer.generation.llm import Client
from belief_transfer.metrics.conviction_scale import summarize_scale, summarize_joint_probabilities
from belief_transfer.schemas import PilotWording


def prepare_scale(job):
    spec=job.pilot_bench.conviction_scale_study
    if spec is None:raise ValueError('conviction study config required')
    if job.replicates!=1:raise ValueError('explicit study repetitions only')
    source=ROOT/'data/generated'/job.experiment.id/job.pilot_bench.bank_run_id
    if (source/'VOID.md').exists():raise ValueError('void content source')
    manifest=json.loads((source/'bank_manifest.json').read_text())
    wordings=[PilotWording.model_validate(r) for r in load_rows(source/'belief_wordings.jsonl')]
    if fingerprint([w.model_dump() for w in wordings])!=manifest['wordings_sha']:
        raise ValueError('content changed')
    if fingerprint([t.model_dump() for t in job.pilot_bench.targets])!=manifest['targets_sha']:
        raise ValueError('target definitions changed')
    if spec.phase=='validation':
        dev=ROOT/'data/results'/job.experiment.id/spec.frozen_development_run_id
        frozen=json.loads((dev/'study_manifest.json').read_text())
        old=frozen['study']
        if 'smoke' in frozen:raise ValueError('screening cannot be used as full development validation')
        for key in ('version','level_definitions','question_framings','controls_accuracy','controls_per_level','exact_agreement','normalized_mean_gap'):
            if old[key]!=spec.model_dump()[key]:raise ValueError('validation instrument differs from frozen development')
        if old.get('threshold_questions')!=spec.threshold_questions:
            raise ValueError('validation threshold questions changed')
        if old.get('thinking')!=spec.thinking:
            raise ValueError('validation thinking mode changed')
        for key in ('temperature','top_p','top_k','min_p','position_instruction','qualification_mode','maximum_normalized_gap',
                    'candidates','preliminary_instruction','force_preliminary_binary','self_checks','joint_likelihood'):
            if old.get(key)!=spec.model_dump()[key]:raise ValueError('validation instrument or sampling changed')
        if set(old['belief_ids']) & set(spec.belief_ids):raise ValueError('validation beliefs overlap development')
        if any(set(a)&set(b) for a,b in zip(old['reference_profiles'],spec.reference_profiles)):
            raise ValueError('validation comprehension profiles were used in development')
        if not (dev/'study_summary.json').exists():raise ValueError('development incomplete')
        development=json.loads((dev/'study_summary.json').read_text())
        if development['study']!=frozen:raise ValueError('development summary/manifest mismatch')
        if not all(development['scores'][c]['status']=='controls_and_stability_pass' for c in spec.candidates):
            raise ValueError('validation requires a qualified development candidate')
    bank=build_scale_bank(spec,wordings)
    if job.smoke:
        # Inference-mode screen, never a full bank qualification.
        bank=[r for r in bank if r.get('framing')==0 and (
            (r['kind']!='natural' and r.get('profile_index',0)==0) or
            (r['kind']=='natural' and r.get('wording_id')==spec.wording_ids[0]))]
    spec_record=spec.model_dump()
    for key in ('threshold_questions','provider','thinking','temperature','top_p','top_k','min_p','position_instruction','self_checks','joint_likelihood','preliminary_instruction','qualification_mode','maximum_normalized_gap','force_preliminary_binary'):
        if spec_record[key] is None:spec_record.pop(key)
    decoding=({'thinking':bool(spec.thinking),'temperature':spec.temperature or 0,'seed':job.pilot_bench.seed,'max_new_tokens':job.pilot_bench.max_new_tokens}
              if spec.provider in (None,'local') else
              {'reasoning_effort':'none','sampling':'provider_default','temperature':None,'max_output_tokens':None,'use_cache':False})
    if spec.temperature:
        decoding.update({'top_p':spec.top_p,'top_k':spec.top_k,'min_p':spec.min_p,
                         'seed_strategy':'uint32(base_seed XOR first eight hex digits of prompt_sha)'})
    manifest={'study':spec_record,'bank_sha':fingerprint(bank),'source_manifest':manifest,
                'decoding':decoding,
                'interpretation':'Ordinal self-reported judgment settledness; paired scores are relative to this bank. Not internal certainty, calibrated probability, importance, or stance.',
                'registration':'Unregistered instrument-development observation; not H35/H36 or a forgetting test.',
                'selection':'Known-profile control recovery and matched stability first. Natural dispersion is diagnostic only; never manufacture diversity or select ethical stances.',
                'review':'Agent-reviewed exploratory design; human alignment deferred. No examples in natural prompts.'}
    if job.smoke:manifest['smoke']='Limited inference-mode screen; not complete framing/wording qualification.'
    return bank,manifest


async def run(job):
    bank,manifest=prepare_scale(job)
    directory=ROOT/'data/results'/job.experiment.id/job.run_id
    # Hydra creates its log/config directory before dispatching the stage.
    if any((directory/name).exists() for name in ('study_manifest.json','study_bank.jsonl','study_observations.jsonl')):
        raise FileExistsError('use a fresh study run ID')
    directory.mkdir(parents=True,exist_ok=True)
    write_resolved_config(job,directory)
    (directory/'study_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    path=write_rows(bank,directory/'study_bank.jsonl');write_md(path)
    spec=job.pilot_bench
    api=spec.conviction_scale_study.provider=='openai'
    if api and spec.adapter_path is not None:raise ValueError('hosted adapter unsupported')
    context=RunContext()
    model=None if api else local_model(spec.model,job.models,adapter_path=spec.adapter_path,
                      max_new_tokens=spec.max_new_tokens,seed=spec.seed,enable_thinking=bool(spec.conviction_scale_study.thinking),
                      **{k:getattr(spec.conviction_scale_study,k) for k in ('top_p','top_k','min_p') if getattr(spec.conviction_scale_study,k) is not None})
    observed=[]
    actual_calls=0
    output=directory/'study_observations.jsonl'
    def persist(row,response,metadata=None,error=None,likelihood=None,judgment=None,administered_prompt=None):
        final=response
        thinking=bool(spec.conviction_scale_study.thinking) and not api
        if thinking:
            final=response.split('</think>')[1].strip() if response and response.count('</think>')==1 else None
        answer,compliant=extract_scale(final,row['candidate'])
        result={**row,'response':response,'answer':answer,'strict_format':compliant,
                'generation_metadata':metadata,'error':error or (None if answer is not None else 'unavailable score extraction')}
        if thinking:result['final_response']=final
        if row['candidate'] in ('balanced_named','verdict_named','agreement_named'):
            position,value,_=balanced_fields(final,'agreement' if row['candidate']=='agreement_named' else row['candidate']=='verdict_named')
            result['chosen_position']=position
            result['judgment_coherent']=None if value is None else ((value==0)==(position in ('neither','no_lean')))
            if value is not None and not result['judgment_coherent']:
                result['answer']=None;result['error']='incoherent chosen-position and conviction fields'
        if spec.conviction_scale_study.temperature:result['sampling_seed']=(spec.seed ^ int(row['prompt_sha'][:8],16)) & 0xffffffff
        if likelihood is not None:
            probabilities=likelihood.probabilities(per_token=False)
            result['joint_choice_scores']=likelihood.model_dump(mode='json')
            result['joint_probabilities']=probabilities
            result['likelihood_diagnostic']=summarize_joint_probabilities(probabilities)
        if row['candidate']=='conditioned_named':
            position=extract_judgment(judgment) if judgment else row.get('expected_position')
            result['chosen_position']=position
            result['judgment_coherent']=(None if answer is None or position is None else True
                if spec.conviction_scale_study.force_preliminary_binary and judgment else ((answer==0)==(position=='no_lean')))
            if result['judgment_coherent'] is False:
                result['answer']=None;result['error']='reflection contradicts its preceding judgment'
            result['judgment_response']=judgment
            result['administered_prompt']=administered_prompt or row['prompt']
            result['administered_prompt_sha']=fingerprint(result['administered_prompt'])
        observed.append(result)
        with output.open('a') as f:f.write(json.dumps(result)+'\n')
        if len(observed)%20==0:print(f'{job.run_id}: {len(observed)}/{len(bank)}',flush=True)
    if api:
        async with Client(model=spec.model,context=context,throughput=job.throughput) as client:
            async for completion in client.batch([r['prompt'] for r in bank],use_cache=False):
                persist(bank[completion.index],completion.text)
                actual_calls+=1
    for i,row in enumerate([] if api else bank):
        judgment=None;prompt=row['prompt']
        try:
            if spec.conviction_scale_study.temperature:model.seed=(spec.seed ^ int(row['prompt_sha'][:8],16)) & 0xffffffff
            if 'judgment_prompt' in row:
                actual_calls+=1
                judgment=(await asyncio.to_thread(model.generate,[row['judgment_prompt']],temperature=spec.conviction_scale_study.temperature or 0))[0]
                if extract_judgment(judgment) is None:raise ValueError('unreadable preliminary judgment')
                prompt=reflection_prompt(prompt,judgment)
            actual_calls+=1
            replies=await asyncio.to_thread(model.generate,[prompt],temperature=spec.conviction_scale_study.temperature or 0)
            if len(replies)!=1:raise ValueError('wrong reply count')
            response=replies[0]
            metadata=getattr(model,'last_generation_metadata',None)
            likelihood=(await asyncio.to_thread(model.score_choices,row['prompt'],joint_completions())
                        if spec.conviction_scale_study.joint_likelihood else None)
            persist(row,response,metadata,likelihood=likelihood,judgment=judgment,administered_prompt=prompt)
        except Exception as exc:
            persist(row,None,error=f'{type(exc).__name__}: {exc}',judgment=judgment,administered_prompt=prompt)
    write_md(output)
    scores=summarize_scale(bank,observed,spec.conviction_scale_study.model_dump())
    backend=None if api else backend_info(dtype=job.models.models[spec.model].dtype)
    summary={'study':manifest,'model':spec.model if api else job.models.models[spec.model].pretrained,'adapter':spec.adapter_path,
             'backend':None if backend is None else backend.model_dump(mode='json'),
             'executed_model_calls':actual_calls,'scores':scores}
    if spec.conviction_scale_study.joint_likelihood:
        summary['choice_scoring_calls']=len(observed)
        summary['candidate_continuations_scored']=15*len(observed)
    target=directory/'study_summary.json';target.write_text(json.dumps(summary,indent=2)+'\n')
    try:
        views=write_conviction_report(summary,job.run_id,directory)
    except Exception as exc:
        # Formatting cannot invalidate already saved observations and reductions.
        note=directory/'VIEW_ERROR.md'
        note.write_text(f'Derived view failed: {type(exc).__name__}: {exc}\nRaw observations and summary remain authoritative.\n')
        views=[note]
        print(f'Derived view error: {exc}',flush=True)
    result=build_result(context,stage=job.stage,experiment_id=job.experiment.id,run_id=job.run_id,
                        datapoints=len(bank),artifacts=[path,output,target,directory/'study_manifest.json',*views],
                        metrics=summary,config_sha=config_sha(job),
                        backend=backend)
    write_result(result,path=directory/f'{job.stage}.yaml')
    print(json.dumps({k:{'controls':v['controls_passed'],'stability':v['natural_stability']} for k,v in scores.items()}),flush=True)
    return result
