"""Judge the preregistered neutral calibration; never choose settings or train weights."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
RUN = 'ethics_gpu_registry_mixed_validation_v1'
TRAIN = 'ethics_sft_registry_mixed_calibration_v1'
REVISION = '1cfa9a7208912126459214e8b04321603b3df60c'
CHECKS = {'adapter_updated','frozen_base_unchanged','reload_matches','finite_loss','steps_match',
          'adapter_roundtrip_exact','checkpoints_match','checkpoint_state_present',
          'one_pass_exact_coverage','one_pass_microbatches'}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(generated: Path, *, run_id: str = RUN, training_run_id: str = TRAIN,
            lookup_reference: Path | None = None) -> None:
    from belief_transfer.config import load_job
    from belief_transfer.evals.measurements import stance_model_controls
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.stages.document_sft import verify_training_plan
    source = Path('data/generated/ethical_stance_sft')/training_run_id
    plan = json.loads((source/'plan.json').read_text())
    anchors = [json.loads(l) for l in (source/'anchors.jsonl').read_text().splitlines()]
    original = [json.loads(l) for l in Path(plan['provenance']['anchor_source']).read_text().splitlines()]
    verify_training_plan(load_job(['+run='+training_run_id]),source/'documents.jsonl')
    if (anchors != original or len(anchors) != 20 or sha(source/'documents.jsonl') != plan['dataset_sha256']
            or sha(Path(plan['provenance']['anchor_source'])) != plan['provenance']['anchor_sha256']):
        raise ValueError('Original mappings or frozen training manifest changed')
    reference=(Path('data/results/ethical_stance_sft/ethics_sft_memorization_v2/memory_base.jsonl')
               if lookup_reference is None else lookup_reference)
    if reference.is_absolute() or '..' in reference.parts:
        raise ValueError('Lookup reference must be a portable project-relative path')
    if lookup_reference is not None and not (reference.parent/'COMPLETED').is_file():
        raise ValueError('Fresh BASE lookup reference requires a completed source run')
    prior=[json.loads(l) for l in reference.read_text().splitlines()]
    if ([r['example_id'] for r in prior] != [r['example_id'] for r in anchors]
            or any(r['prompt']!=a['memory_prompt'] or r['expected']!=a['memory_answer'] for r,a in zip(prior,anchors,strict=True))):
        raise ValueError('Lookup input reference does not match the frozen anchors')
    lookup=[{'example_id':r['example_id'],'prompt':r['prompt'],'expected':r['expected'],
             'expected_input_token_ids':r['generation_metadata']['input_token_ids']} for r in prior]
    base = load_job(['+run=ethics_gpu_vllm_base_v1'])
    bank = stance_model_controls(base.pilot_bench.stance_interface)
    for row in bank:
        row['seed'] = (42 ^ int(hashlib.sha256(row['prompt'].encode()).hexdigest()[:8],16)) & 0xffffffff
    protocol = {'run_id':run_id,'training_run_id':training_run_id,'plan_path':str(source/'plan.json'),
        'plan_sha256':sha(source/'plan.json'),'anchors_path':str(source/'anchors.jsonl'),
        'anchors_sha256':sha(source/'anchors.jsonl'),'script_sha256':sha(Path(__file__)),
        'input_reference_path':str(reference),'input_reference_sha256':sha(reference),
        'model_revision':REVISION,'control_generation':base.pilot_bench.cuda_generation.model_dump(mode='json'),
        'control_interface':base.pilot_bench.stance_interface,
        'criteria':{'base_lookup_max':.1,'adapter_lookup_min':.9,'control_min':.95,
                    'control_strict':1.0,'null_flip_max':.05,'control_normal_stops':True},
        'lookup_decoder':{'thinking':False,'temperature':0,'seed':0,'max_new_tokens':16,'batch_size':4},
        'control_decoder':{'thinking':True,'temperature':.6,'top_p':.95,'top_k':20,'min_p':0,
                           'max_new_tokens':4096,'seed':42,'submission_batch_size':32},
        'environments':{'lookup':'/workspace/sft-drift/belief-transfer/.venv/bin/python',
                        'controls':'/workspace/sft-drift-vllm/.venv/bin/python'},
        'interpretation':'Final-only neutral technical qualification. No ethical outcomes, parameter selection or reinterpretation of old failed memory/parity/recognition gates. C4 and other calibration changes are confounded.'}
    if run_id != RUN:
        protocol['interpretation'] = ('Final-only neutral format/LR qualification under the frozen matrix selection rule. '
            'No ethical outcomes or reinterpretation of old failures. Format changes include continuation context and derived scheduling.')
    generated.mkdir(parents=True,exist_ok=False)
    p=generated/'control_bank.jsonl'
    p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in bank));write_md(p)
    protocol['control_bank_sha256']=sha(p)
    p=generated/'lookup_bank.jsonl'
    p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in lookup));write_md(p)
    protocol['lookup_bank_sha256']=sha(p)
    (generated/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (generated/'PROTOCOL.md').write_text('# Frozen neutral calibration validation\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n\nTwenty original lookup queries per BASE/adapter, plus32unchanged factual controls per model:104replies. Partial batches remain raw failures; no neutral imputation. Training must have a COMPLETED marker and all ten technical checks, matching dataset, steps, exposure, revision and exact one-pass coverage. Bind summary/final-file hashes before inference; verify loaded HF adapter tensor hash against training round-trip hash. The final adapter alone is judged. Subprocesses use the existing isolated environments and release models between phases. The master holds the shared CUDA lock, so queued execution waits until training ends. No resume/overwrite.\n')


def training_binding(plan: dict, training_root: Path, checkpoint: Path) -> dict:
    if not (training_root/'COMPLETED').is_file():
        raise ValueError('Training did not complete; no validation weight loading')
    summary=json.loads((training_root/'summary.json').read_text())
    t=summary['training']
    expected_loss=sum(plan['dose']['loss_tokens_by_kind'].values())
    required_checks = CHECKS | ({'loss_normalization_matches'} if plan.get('preprocessing', {}).get('model_revision') else set())
    if (summary['manifest_sha256'] != plan['dataset_sha256'] or t['status'] != 'COMPLETED'
            or set(t['checks']) != required_checks or not all(v is True for v in t['checks'].values())
            or t['model_revision'] != REVISION or t['global_steps'] != plan['schedule']['max_steps']
            or not t['one_pass'] or t['actual_forward_loss_tokens'] != expected_loss
            or t['actual_loss_tokens_by_kind'] != plan['dose']['loss_tokens_by_kind']
            or t['final_adapter_sha256'] != t['reloaded_adapter_sha256']
            or summary['chunks'] != plan['dose']['chunks']):
        raise ValueError('Training identity, dose or verification checks failed')
    return {'training_summary_sha256':sha(training_root/'summary.json'),
        'completed_marker_sha256':sha(training_root/'COMPLETED'),
        'adapter_path':str(checkpoint),'adapter_file_sha256':sha(checkpoint/'adapter_model.safetensors'),
        'adapter_config_sha256':sha(checkpoint/'adapter_config.json'),
        'adapter_tensor_sha256':t['final_adapter_sha256'],'training_checks':t['checks']}


def verify_binding(binding: dict) -> None:
    path=Path(binding['adapter_path'])
    if (sha(path/'adapter_model.safetensors') != binding['adapter_file_sha256']
            or sha(path/'adapter_config.json') != binding['adapter_config_sha256']):
        raise ValueError('Bound adapter bytes changed')



def lookup_report(bank: list[dict], rows: list[dict]) -> dict:
    from belief_transfer.benchmarks.document_memory import score_memory
    if (len(rows)!=20 or len(bank)!=20 or len({r['example_id'] for r in rows})!=20
            or [r['example_id'] for r in rows]!=[r['example_id'] for r in bank]):
        raise ValueError('Lookup coverage/identity incomplete')
    anchors=[{'example_id':r['example_id'],'memory_prompt':r['prompt'],'memory_answer':r['expected']} for r in bank]
    rescored=score_memory(anchors,[(r['response'],r['generation_metadata']) for r in rows])
    if any(r['correct']!=v['correct'] or r['prompt']!=b['prompt'] or r['expected']!=b['expected']
           for r,v,b in zip(rows,rescored['observations'],bank,strict=True)):
        raise ValueError('Lookup answer key, prompt or scorer changed')
    identity=all((m:=r['generation_metadata']).get('model_revision')==REVISION
        and m.get('input_token_ids')==b['expected_input_token_ids']
        and m.get('sampling_seed')==0 and m.get('batch_size')==4
        and m.get('sampling_seed_strategy')=='per-token-v1'
        and m.get('prompt_tokens')==len(b['expected_input_token_ids'])
        and m.get('generation_tokens')==len(m.get('output_token_ids',[]))<=16
        for r,b in zip(rows,bank,strict=True))
    return {'n':20,'n_correct':sum(r['correct'] for r in rows),'accuracy':rescored['accuracy'],
            'identity_matches':identity}


def control_report(bank: list[dict], rows: list[dict], *, adapter: bool) -> dict:
    from belief_transfer.metrics.measurements import summarize_stance_study
    controls=summarize_stance_study(bank,rows,{'control_accuracy':.95,'null_flip_max':.05},
                                    qualify_natural_consistency=False)['controls']
    strict=sum(bool(r['strict_format']) for r in rows)/len(bank)
    normal=all(r['generation_metadata'].get('finish_reason')=='stop' and not r['generation_metadata'].get('backend_error') for r in rows)
    identity=all(r['generation_metadata'].get('adapter_lora_id')==(1 if adapter else None)
                 and r['generation_metadata'].get('model_revision')==REVISION for r in rows)
    passed=(len(rows)==len(bank)==32 and all(controls['checks'].values()) and strict==1 and normal and identity)
    return {**controls,'strict_format_rate':strict,'normal_stops':normal,'identity_matches':identity,'passed':passed}


def child(phase: str, generated: Path, root: Path) -> None:
    from belief_transfer.config import load_job
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.inference.backend import require_training_backend
    require_training_backend()
    protocol=json.loads((generated/'protocol.json').read_text())
    binding=json.loads((root/'training_binding.json').read_text());verify_binding(binding)
    kind,arm=phase.split('_');adapter=None if arm=='base' else Path(binding['adapter_path'])
    path=root/(phase+'.jsonl')
    if path.exists():raise FileExistsError('No phase resume or overwrite')
    start=time.perf_counter()
    try:
        if kind=='lookup':
            from belief_transfer.inference.model import HFModel
            from belief_transfer.benchmarks.document_memory import score_memory
            from belief_transfer.training.documents import adapter_hash
            job=load_job(['+run='+protocol['training_run_id']])
            model=HFModel(job.training.model,job.models,adapter_path=adapter,max_new_tokens=16,
                          seed=0,enable_thinking=False,batch_size=4)
            model._ensure_loaded()
            if model._hf_model.config._commit_hash != REVISION:
                raise ValueError('Wrong HF model revision')
            tensor_sha=None if adapter is None else adapter_hash(model._hf_model)
            if adapter is not None and tensor_sha!=binding['adapter_tensor_sha256']:
                raise ValueError('Loaded adapter differs from the trained round-trip tensor hash')
            rows=[json.loads(l) for l in Path(protocol['anchors_path']).read_text().splitlines()]
            for start_index in range(0,20,4):
                group=rows[start_index:start_index+4]
                replies=model.generate_batch_with_metadata([r['memory_prompt'] for r in group],temperature=0,
                    seeds=[0]*len(group),batch_size=4)
                n=min(len(group),len(replies))
                if n:
                    observed=score_memory(group[:n],replies[:n])['observations']
                    for row in observed:
                        with path.open('a') as f:f.write(json.dumps({**row,'arm':arm},ensure_ascii=False)+'\n')
                if len(replies)!=len(group):raise ValueError('Incomplete lookup batch; partial outputs retained')
        else:
            from belief_transfer.inference.local import local_model
            from belief_transfer.validation.measurements import observation_from_reply
            job=load_job(['+run=ethics_gpu_vllm_base_v1']);p=job.pilot_bench
            model=local_model(p.model,job.models,adapter_path=adapter,generation=p.cuda_generation,
                max_new_tokens=4096,seed=42,enable_thinking=True,top_p=.95,top_k=20,min_p=0)
            rows=[json.loads(l) for l in (generated/'control_bank.jsonl').read_text().splitlines()]
            replies=model.generate_batch_with_metadata([r['prompt'] for r in rows],temperature=.6,
                seeds=[r['seed'] for r in rows],batch_size=32)
            for row,(text,metadata) in zip(rows,replies):
                observed=observation_from_reply(row,text,metadata,thinking=True,seed=row['seed'])
                with path.open('a') as f:f.write(json.dumps({**observed,'arm':arm},ensure_ascii=False)+'\n')
            if len(replies)!=len(rows):raise ValueError('Incomplete control batch; partial outputs retained')
            tensor_sha=None
        import importlib.metadata
        import torch
        (root/(phase+'_metadata.json')).write_text(json.dumps({'elapsed_including_load_s':time.perf_counter()-start,
            'card':torch.cuda.get_device_name(),'versions':{name:importlib.metadata.version(name) for name in ['torch','transformers',('peft' if kind=='lookup' else 'vllm')]},
            'model_revision':REVISION,'loaded_adapter_tensor_sha256':tensor_sha,
            'decoder':protocol['lookup_decoder' if kind=='lookup' else 'control_decoder']},indent=2)+'\n')
        verify_binding(binding)
    finally:
        if path.exists():write_md(path)


def summarize(generated: Path, root: Path, protocol: dict, binding: dict) -> dict:
    bank=[json.loads(l) for l in (generated/'control_bank.jsonl').read_text().splitlines()]
    lookup_bank=[json.loads(l) for l in (generated/'lookup_bank.jsonl').read_text().splitlines()]
    arms={}
    for arm in ['base','adapter']:
        lookup=[json.loads(l) for l in (root/('lookup_'+arm+'.jsonl')).read_text().splitlines()]
        control=[json.loads(l) for l in (root/('controls_'+arm+'.jsonl')).read_text().splitlines()]
        arms[arm]={'lookup':lookup_report(lookup_bank,lookup),
            'controls':control_report(bank,control,adapter=arm=='adapter')}
    c=protocol['criteria']
    passed=(arms['base']['lookup']['accuracy']<=c['base_lookup_max']
            and arms['adapter']['lookup']['accuracy']>=c['adapter_lookup_min']
            and all(a['lookup']['identity_matches'] and a['controls']['passed'] for a in arms.values())
            and all(binding['training_checks'].values()))
    return {'run_id':protocol['run_id'],'training_run_id':protocol['training_run_id'],'arms':arms,'technical_qualification_passed':passed,
        'protocol_sha256':sha(generated/'protocol.json'),'training_binding':binding,
        'interpretation':protocol['interpretation'],'historical_failed_gates':'Unchanged; this is a new independently preregistered calibration.'}


def run(generated: Path, root: Path) -> None:
    from belief_transfer.inference.backend import require_training_backend
    require_training_backend()
    protocol=json.loads((generated/'protocol.json').read_text())
    checks=[(Path(__file__),'script_sha256'),(Path(protocol['plan_path']),'plan_sha256'),
            (Path(protocol['anchors_path']),'anchors_sha256'),(generated/'control_bank.jsonl','control_bank_sha256'),
            (generated/'lookup_bank.jsonl','lookup_bank_sha256'),
            (Path(protocol['input_reference_path']),'input_reference_sha256')]
    if protocol['run_id']!=generated.name or any(sha(p)!=protocol[k] for p,k in checks):
        raise ValueError('Frozen validation inputs changed')
    from belief_transfer.config import load_job
    base=load_job(['+run=ethics_gpu_vllm_base_v1']).pilot_bench
    if (base.cuda_generation.model_dump(mode='json')!=protocol['control_generation']
            or base.stance_interface!=protocol['control_interface']):
        raise ValueError('Frozen control interface/engine changed')
    root.mkdir(parents=True,exist_ok=False)
    try:
        (root/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
        plan=json.loads(Path(protocol['plan_path']).read_text())
        train=Path('data/results/ethical_stance_sft')/protocol['training_run_id']
        binding=training_binding(plan,train,Path('data/checkpoints/ethical_stance_sft')/protocol['training_run_id']/'final')
        (root/'training_binding.json').write_text(json.dumps(binding,indent=2)+'\n')
        for phase in ['lookup_base','lookup_adapter','controls_base','controls_adapter']:
            env=protocol['environments'][phase.split('_')[0]]
            subprocess.run([env,str(Path(__file__).resolve()),'child','--phase',phase,'--run-id',protocol['run_id'],
                '--training-run-id',protocol['training_run_id']],check=True)
        verify_binding(binding)
        summary=summarize(generated,root,protocol,binding)
        summary['code_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        (root/'summary.md').write_text('# Neutral calibration validation\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
        (root/'COMPLETED').write_text('Qualification judged; inspect summary for pass/fail.\n')
        print(json.dumps(summary,indent=2),flush=True)
    except BaseException as exc:
        (root/'failure.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()},indent=2)+'\n')
        raise


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['prepare','run','child'])
    parser.add_argument('--phase',choices=['lookup_base','lookup_adapter','controls_base','controls_adapter'])
    parser.add_argument('--run-id',default=RUN)
    parser.add_argument('--training-run-id',default=TRAIN)
    parser.add_argument('--lookup-reference',type=Path,
                        help='Preparation only: completed BASE lookup run for a fresh mapping bank')
    args=parser.parse_args()
    if args.lookup_reference is not None and args.operation != 'prepare':
        parser.error('--lookup-reference is only valid during preparation')
    if (Path(args.run_id).name != args.run_id or not args.run_id.startswith('ethics_gpu_')
            or Path(args.training_run_id).name != args.training_run_id or not args.training_run_id.startswith('ethics_sft_')):
        raise ValueError('Explicit calibration/validation IDs required')
    generated=Path('data/generated/ethical_pilot')/args.run_id;root=Path('data/results/ethical_pilot')/args.run_id
    registry=json.loads(Path('configs/handoff.json').read_text())
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in [generated,root]):
        raise ValueError('Register validation roots before execution')
    if args.operation=='prepare':prepare(generated,run_id=args.run_id,training_run_id=args.training_run_id,
                                         lookup_reference=args.lookup_reference)
    elif args.operation=='child':
        if json.loads((generated/'protocol.json').read_text())['training_run_id'] != args.training_run_id:
            raise ValueError('Wrong training ID for validation')
        if args.phase is None:parser.error('--phase required for child')
        child(args.phase,generated,root)
    else:
        if json.loads((generated/'protocol.json').read_text())['training_run_id'] != args.training_run_id:
            raise ValueError('Wrong training ID for validation')
        import fcntl
        with open('/tmp/sft-drift-cuda-benchmark.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            run(generated,root)


if __name__=='__main__':
    main()
