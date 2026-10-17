"""An explicit exploratory confidence-allocation study; raw responses first."""
import asyncio
import json

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.report import ROOT,build_result,write_result
from belief_transfer.analysis.conviction_allocation import write_allocation_report
from belief_transfer.config import config_sha,write_resolved_config
from belief_transfer.evals.conviction_allocation import build_allocation_bank,extract_allocation
from belief_transfer.evals.chosen_confidence import confidence_prompt,extract_analytical_judgment,extract_chosen_confidence
from belief_transfer.evals.claim_credence import extract_claim_credence,extract_favored_claim
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.evals.suite import load_rows,write_rows
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.llm import Client
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference.local import local_model
from belief_transfer.metrics.conviction_allocation import summarize_allocation
from belief_transfer.schemas import PilotWording


def prepare_allocation(job):
    spec=job.pilot_bench.conviction_allocation_study
    if spec is None:raise ValueError('allocation study required')
    if job.replicates!=1:raise ValueError('explicit repetitions only')
    source=ROOT/'data/generated'/job.experiment.id/job.pilot_bench.bank_run_id
    if (source/'VOID.md').exists():raise ValueError('void source')
    source_manifest=json.loads((source/'bank_manifest.json').read_text())
    wordings=[PilotWording.model_validate(r) for r in load_rows(source/'belief_wordings.jsonl')]
    if fingerprint([w.model_dump() for w in wordings])!=source_manifest['wordings_sha']:
        raise ValueError('changed source wordings')
    if fingerprint([t.model_dump() for t in job.pilot_bench.targets])!=source_manifest['targets_sha']:
        raise ValueError('changed belief definitions')
    if spec.phase=='validation':
        dev=ROOT/'data/results'/job.experiment.id/spec.frozen_development_run_id
        if (dev/'VOID.md').exists():raise ValueError('void development')
        frozen=json.loads((dev/'allocation_summary.json').read_text())
        old=frozen['manifest']['study']
        if frozen['manifest']['smoke'] or frozen['scores']['status']!='controls_and_stability_pass':
            raise ValueError('validation requires a qualified full development run')
        for key in ('version','question_framings','controls_accuracy','controls_per_level','control_tolerance','maximum_mean_gap','maximum_pair_gap',
                    'thinking','temperature','top_p','top_k','min_p','provider','readout','preliminary_instruction','clarity_controls','canonical_target'):
            if old.get(key)!=getattr(spec,key):raise ValueError('changed validation instrument or decoding')
        if set(old['belief_ids'])&set(spec.belief_ids):raise ValueError('validation topics overlap development')
        if set(old['heads_counts'][1:-1])&set(spec.heads_counts[1:-1]):raise ValueError('validation intermediate controls reused')
    bank=build_allocation_bank(spec,wordings,job.smoke)
    record=spec.model_dump()
    for key in ('thinking','temperature','top_p','top_k','min_p','provider','readout','preliminary_instruction','clarity_controls','canonical_target'):
        if record[key] is None:record.pop(key)
    decoding={'temperature':spec.temperature or 0,'thinking':bool(spec.thinking),'seed':job.pilot_bench.seed,'max_new_tokens':job.pilot_bench.max_new_tokens}
    if spec.temperature:
        decoding.update({'top_p':spec.top_p,'top_k':spec.top_k,'min_p':spec.min_p,
                         'seed_strategy':'uint32(base_seed XOR first eight hex digits of prompt_sha)'})
        if spec.readout=='chosen_confidence':decoding['seed_strategy']='uint32(base_seed XOR first eight hex digits of fingerprint((phase, administered_prompt)))'
    api=spec.provider=='openai'
    if api:
        if job.pilot_bench.adapter_path is not None:raise ValueError('hosted adapter unsupported')
        decoding={'sampling':'provider_default','reasoning_effort':'none','thinking':False,'temperature':None,'use_cache':False}
    manifest={'study':record,'source_manifest':source_manifest,'bank_sha':fingerprint(bank),'smoke':job.smoke,
              'model':job.pilot_bench.model if api else job.models.models[job.pilot_bench.model].pretrained,'adapter':job.pilot_bench.adapter_path,
              'decoding':decoding,
              'score':'abs(agree_points - disagree_points) / 100',
              'scope':'Expressed confidence allocation. A declared numerical index, not calibrated ethical truth or inner certainty.',
              'registration':'Unregistered instrument development; not a forgetting experiment.',
              'review':'Agent-reviewed controls; human alignment deferred. Reviewed original belief content unchanged.'}
    if spec.readout=='chosen_confidence':
        manifest['score']='(confidence_percent - 50) / 50, conditional on this Conviction branch\'s fresh chosen judgment'
        manifest['scope']='Reported confidence in an actual analytical judgment. Not calibrated moral correctness or inner certainty.'
    elif spec.readout in ('claim_credence','reasoned_claim_credence','favored_claim_confidence'):
        manifest['score']='abs(2 * claim_confidence_percent - 100) / 100'
        manifest['scope']='Reported confidence in the scoped evaluative proposition, distinct from certainty about identifying one\'s assessment. Not calibrated ethical truth or inner certainty.'
        if spec.canonical_target:manifest['target_rule']='The reviewed canonical claim is rated in every cell; polarity varies the topic formulation, not the rated target.'
        if spec.readout=='favored_claim_confidence':
            manifest['score']='(favored_claim_confidence_percent - 50) / 50; directed claim confidence reconstructed from favored_side'
            manifest['scope']='Reported confidence the favored claim holds, not certainty the best guess is sensible. This single Conviction pass never receives the primary Stance answer.'
            manifest['target_rule']='The favored side refers to the canonical claim or its opposite; directed canonical confidence is reconstructed from that side and its confidence.'
    return bank,manifest


async def run(job):
    bank,manifest=prepare_allocation(job)
    spec=job.pilot_bench.conviction_allocation_study
    root=ROOT/'data/results'/job.experiment.id/job.run_id
    if any((root/f).exists() for f in ('allocation_manifest.json','allocation_bank.jsonl','allocation_observations.jsonl')):
        raise FileExistsError('fresh allocation run ID required')
    root.mkdir(parents=True,exist_ok=True);write_resolved_config(job,root)
    (root/'allocation_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    bank_path=write_rows(bank,root/'allocation_bank.jsonl');write_md(bank_path)
    api=spec.provider=='openai';context=RunContext()
    model=None if api else local_model(job.pilot_bench.model,job.models,adapter_path=job.pilot_bench.adapter_path,
                      max_new_tokens=job.pilot_bench.max_new_tokens,seed=job.pilot_bench.seed,enable_thinking=bool(spec.thinking),
                      **{k:getattr(spec,k) for k in ('top_p','top_k','min_p') if getattr(spec,k) is not None})
    observed=[];output=root/'allocation_observations.jsonl';actual_calls=0
    judgments={};judgment_file=root/'allocation_judgments.jsonl'
    def final_text(response):
        if not spec.thinking:return response
        return response.split('</think>')[1].strip() if response and response.count('</think>')==1 else None
    def seed_for(phase,prompt):
        return (job.pilot_bench.seed ^ int(fingerprint((phase,prompt))[:8],16)) & 0xffffffff
    def save_judgment(row,response,metadata=None,error=None):
        final=final_text(response);position,strict=extract_analytical_judgment(final)
        r={'presentation_id':row['presentation_id'],'prompt':row['judgment_prompt'],'prompt_sha':row['judgment_prompt_sha'],
           'response':response,'final_response':final,'chosen_position':position,'strict_format':strict,
           'generation_metadata':metadata,'error':error or (None if position else 'unreadable preliminary judgment')}
        if spec.temperature:r['sampling_seed']=seed_for('judgment',row['judgment_prompt'])
        judgments[row['presentation_id']]=r
        with judgment_file.open('a') as f:f.write(json.dumps(r)+'\n')
        return r
    def persist(row,response,metadata=None,error=None,judgment=None,administered_prompt=None):
        final=response
        if spec.thinking:final=response.split('</think>')[1].strip() if response and response.count('</think>')==1 else None
        position=judgment['chosen_position'] if judgment is not None else row.get('specified_position')
        allocation,strict=(extract_favored_claim(final) if spec.readout=='favored_claim_confidence' else
                           extract_chosen_confidence(final,position) if spec.readout=='chosen_confidence' else
                           extract_claim_credence(final,reasoned=spec.readout=='reasoned_claim_credence')
                           if spec.readout in ('claim_credence','reasoned_claim_credence') else extract_allocation(final))
        r={**row,'response':response,'allocation':allocation,'strict_format':strict,
           'generation_metadata':metadata,'error':error or (None if allocation is not None else 'unavailable allocation')}
        if spec.thinking:r['final_response']=final
        if spec.readout=='chosen_confidence':
            r['judgment_observation']=judgment
            r['judgment_position']=position
            r['administered_prompt']=administered_prompt or row['prompt']
            r['administered_prompt_sha']=fingerprint(r['administered_prompt'])
        if spec.temperature:r['sampling_seed']=(seed_for('confidence',r['administered_prompt']) if spec.readout=='chosen_confidence' else
                                               (job.pilot_bench.seed ^ int(row['prompt_sha'][:8],16)) & 0xffffffff)
        observed.append(r)
        with output.open('a') as f:f.write(json.dumps(r)+'\n')
        if len(observed)%20==0:print(f'{job.run_id}: {len(observed)}/{len(bank)}',flush=True)
    if api:
        async with Client(model=job.pilot_bench.model,context=context,throughput=job.throughput) as client:
            first=[r for r in bank if 'judgment_prompt' in r]
            if first:
                try:
                    async for completion in client.batch([r['judgment_prompt'] for r in first],use_cache=False):
                        save_judgment(first[completion.index],completion.text);actual_calls+=1
                finally:
                    if judgment_file.exists():write_md(judgment_file)
            ratings=[]
            for row in bank:
                judgment=judgments.get(row['presentation_id'])
                if judgment is not None and judgment['chosen_position'] is None:
                    persist(row,None,error=judgment['error'],judgment=judgment);continue
                prompt=confidence_prompt(row['prompt'],judgment['final_response']) if judgment is not None else row['prompt']
                ratings.append((row,prompt,judgment))
            async for completion in client.batch([p for _,p,_ in ratings],use_cache=False):
                row,prompt,judgment=ratings[completion.index]
                persist(row,completion.text,judgment=judgment,administered_prompt=prompt);actual_calls+=1
    for i,row in enumerate([] if api else bank):
        response=None;metadata=None;error=None;judgment=None;prompt=row['prompt']
        try:
            if 'judgment_prompt' in row:
                if spec.temperature:model.seed=seed_for('judgment',row['judgment_prompt'])
                actual_calls+=1
                replies=await asyncio.to_thread(model.generate,[row['judgment_prompt']],temperature=spec.temperature or 0)
                if len(replies)!=1:raise ValueError('wrong preliminary response count')
                judgment=save_judgment(row,replies[0],getattr(model,'last_generation_metadata',None))
                if judgment['chosen_position'] is None:raise ValueError('unreadable preliminary judgment')
                prompt=confidence_prompt(row['prompt'],judgment['final_response'])
            if spec.temperature:model.seed=(seed_for('confidence',prompt) if spec.readout=='chosen_confidence' else
                                           (job.pilot_bench.seed ^ int(row['prompt_sha'][:8],16)) & 0xffffffff)
            actual_calls+=1
            replies=await asyncio.to_thread(model.generate,[prompt],temperature=spec.temperature or 0)
            if len(replies)!=1:raise ValueError('wrong response count')
            response=replies[0];metadata=getattr(model,'last_generation_metadata',None)
        except Exception as exc:error=f'{type(exc).__name__}: {exc}'
        persist(row,response,metadata,error,judgment,prompt)
    write_md(output)
    extra_artifacts=[]
    if judgment_file.exists():write_md(judgment_file);extra_artifacts=[judgment_file,judgment_file.with_suffix('.md')]
    scores=summarize_allocation(bank,observed,job.pilot_bench.conviction_allocation_study.model_dump())
    summary={'manifest':manifest,'executed_model_calls':actual_calls,'scores':scores}
    summary_path=root/'allocation_summary.json';summary_path.write_text(json.dumps(summary,indent=2)+'\n')
    try:views=write_allocation_report(summary,job.run_id,root)
    except Exception as exc:
        p=root/'VIEW_ERROR.md';p.write_text(f'{type(exc).__name__}: {exc}\nRaw scores preserved.\n');views=[p]
    backend=None if api else backend_info(dtype=job.models.models[job.pilot_bench.model].dtype)
    result=build_result(context,stage=job.stage,experiment_id=job.experiment.id,run_id=job.run_id,
        datapoints=len(bank),artifacts=[bank_path,output,summary_path,root/'allocation_manifest.json',*extra_artifacts,*views],
        metrics=summary,config_sha=config_sha(job),backend=backend)
    write_result(result,path=root/(job.stage+'.yaml'))
    print(json.dumps({'status':scores['status'],'controls':scores['controls'],'stability':scores['natural_stability']}),flush=True)
    return result
