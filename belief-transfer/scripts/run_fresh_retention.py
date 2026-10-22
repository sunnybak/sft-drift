"""Finite independent-input retention check; no training or parameter search."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import re
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import config_sha, load_job
from belief_transfer.evals.fresh_retention import bank
from belief_transfer.metrics.instruction_retention import report
from run_error_rca import sha, dump

MASTER='ethics_gpu_fresh_retention_v1'
ARMS=['base','positive','negative','offtopic','c4_only']
PLAN=Path('../changelog/2026-10-22-fresh-retention-plan.md')
PYTHON='/workspace/sft-drift-vllm/.venv/bin/python'

def read(p):return json.loads(Path(p).read_text())
def rows(p):return list(map(json.loads,Path(p).read_text().splitlines()))
def run_id(arm):return f'ethics_gpu_fresh_retention_{arm}_v1'
def write_rows(p,value):
    p.write_text(''.join(json.dumps(r)+'\n' for r in value));write_md(p)
def roots():
    required=[f'{k}/ethical_pilot/{MASTER}' for k in ['generated','results']]
    required += [f'results/ethical_pilot/{run_id(a)}' for a in ARMS]
    if not set(required)<=set(read('configs/handoff.json')['include_paths']):raise ValueError('Register fresh outputs before preparation')
    return Path('data/generated/ethical_pilot')/MASTER,Path('data/results/ethical_pilot')/MASTER

def source_job(arm):return load_job(['+run=ethics_gpu_retention_rca_'+arm+'_v2'])
def overlay(arm,bank_path,known_path=None,known_sha=None):
    source=source_job(arm)
    return {'defaults':['ethics_gpu_retention_rca_'+arm+'_v2'],'run_id':run_id(arm),
        'instruction_retention':{'model_label':arm,'bank_path':str(bank_path),'bank_sha256':sha(bank_path),
            'known_path':str(known_path) if known_path else None,'known_sha256':known_sha,
            'fresh_base_reference':arm=='base','adapter_sha256':source.instruction_retention.adapter_sha256,
            'eval_seeds':[42,7,1729]}}

def check_bindings(bindings):
    for name,digest in bindings.items():
        if sha(Path(name))!=digest:raise ValueError('Fresh retention source/input changed: '+name)

def prepare():
    import yaml
    from transformers import AutoTokenizer
    from belief_transfer.inference.model import _apply_chat_template
    generated,result=roots()
    if generated.exists() or result.exists():raise FileExistsError('Fresh retention already prepared or started')
    if any((Path('configs/run')/(run_id(a)+'.yaml')).exists() or (Path('data/results/ethical_pilot')/run_id(a)).exists() for a in ARMS):raise FileExistsError('Fresh child already exists')
    receipt=read('data/.handoff-receipt.json')
    if receipt['repo_id']!=read('configs/handoff.json')['repo_id']:raise ValueError('Wrong parent artifact store')
    parent=Path('data/results/ethical_pilot/ethics_gpu_scope_fact_clarity_v2')
    for name in ['COMPLETED','analysis.json','reviewed_assessment.json']:
        p=parent/name;entry=receipt['manifest']['files'].get(str(p.relative_to('data')),{})
        if sha(p)!=entry.get('sha256'):raise ValueError('Preserve complete parent review before fresh retention')
    replay=Path('data/generated/ethical_stance_sft/ethics_sft_instruction_replay_text_v1/documents.jsonl')
    old_bank=Path('data/generated/ethical_pilot/ethics_gpu_instruction_retention_base_v1/bank.jsonl')
    blocked={r['training_request'] for r in rows(replay)}|{r['prompt'] for r in rows(old_bank)}
    from build_instruction_replay import bank as original_bank
    blocked |= {r['prompt'] for r in original_bank()}
    fresh=bank(blocked);proofs={};bindings={str(p):sha(p) for p in [PLAN,replay,old_bank]}
    for arm in ARMS:
        job=source_job(arm);proofs[arm]=read(Path('data/results/ethical_pilot')/f'ethics_gpu_retention_rca_{arm}_v2/manifest.json')
        if job.pilot_bench.adapter_path:
            root=Path(job.pilot_bench.adapter_path)
            if sha(root/'adapter_model.safetensors')!=job.instruction_retention.adapter_sha256:raise ValueError('Adapter changed')
            for name in ['adapter_model.safetensors','adapter_config.json']:
                bindings[str(root/name)]=sha(root/name)
        config=Path('configs/run')/f'ethics_gpu_retention_rca_{arm}_v2.yaml';bindings[str(config)]=sha(config)
    base=source_job('base');b=base.pilot_bench
    tokenizer=AutoTokenizer.from_pretrained(base.models.models[b.model].pretrained,
        revision=b.cuda_generation.revision,local_files_only=True)
    for row in fresh:
        rendered=_apply_chat_template(tokenizer,[{'role':'user','content':row['prompt']}],enable_thinking=row['thinking'])
        row['expected_input_token_ids']=tokenizer.encode(rendered,add_special_tokens=False)
        if len(row['expected_input_token_ids'])+4096>b.cuda_generation.max_model_len:raise ValueError('Fresh context budget exceeded')
    for name in ['scripts/run_fresh_retention.py','scripts/analyze_fresh_retention.py','scripts/build_instruction_replay.py',
        'src/belief_transfer/evals/fresh_retention.py','src/belief_transfer/stages/instruction_retention.py',
        'src/belief_transfer/evals/instruction_retention.py','src/belief_transfer/metrics/instruction_retention.py',
        'src/belief_transfer/inference/model.py','src/belief_transfer/inference/vllm_model.py',
        'src/belief_transfer/schemas.py','src/belief_transfer/config.py']:
        bindings[name]=sha(Path(name))
    # All external inputs, weight files and tokenization validated before any writes.
    generated.mkdir(parents=True);path=generated/'bank.jsonl';write_rows(path,fresh);bindings[str(path)]=sha(path)
    config=Path('configs/run')/(run_id('base')+'.yaml');config.write_text('# @package _global_\n'+yaml.safe_dump(overlay('base',path),sort_keys=False))
    bindings[str(config)]=sha(config)
    protocol={'run_id':MASTER,'expected_calls':1920,'jobs':[run_id(a) for a in ARMS],
        'eos_token_id':tokenizer.eos_token_id,'bank_sha256':sha(path),'base_config_sha':config_sha(load_job(['+run='+run_id('base')])),
        'source_bindings':bindings,'runtime_proofs':proofs,'parent_snapshot_revision':receipt['revision'],
        'reference_selection':'BASE seed42 only, before adapters; no historical mask overwritten',
        'no_training':True,'no_resume':True,'plan_path':str(PLAN),'plan_sha256':sha(PLAN)}
    dump(generated/'protocol.json',protocol);(generated/'protocol.md').write_text('# Fresh retention protocol\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')
    print(json.dumps({'run_id':MASTER,'calls':1920,'max_input_tokens':max(len(r['expected_input_token_ids']) for r in fresh)}))


def inspect(arm,protocol,known=None):
    generated,_=roots();root=Path('data/results/ethical_pilot')/run_id(arm)
    if not (root/'COMPLETED').exists():raise ValueError('Incomplete fresh retention child')
    actual=rows(root/'responses.jsonl');reference=rows(generated/'bank.jsonl');manifest=read(root/'manifest.json')
    proof=protocol['runtime_proofs'][arm]
    revision=(Path('data/results/ethical_pilot')/MASTER/'STARTED').read_text().strip()
    if not re.fullmatch(r'[0-9a-f]{40}',revision) or not re.fullmatch(r'[0-9a-f]{7,40}',manifest['code_revision']) or not revision.startswith(manifest['code_revision']):
        raise ValueError('Fresh source commit changed')
    if sha(root/'bank.jsonl')!=protocol['bank_sha256'] or len(actual)!=384:raise ValueError('Wrong fresh grid/bank')
    for key in ['model','backend','generation','decoding','max_new_tokens','batch_size','versions']:
        if manifest[key]!=proof[key]:raise ValueError('Fresh runtime changed: '+key)
    if manifest['adapter_sha256']!=source_job(arm).instruction_retention.adapter_sha256:raise ValueError('Fresh adapter changed')
    if any(r.get('error') for r in actual):raise ValueError('Fresh raw technical errors; preserve and stop')
    # Replay grading from exact decoded raw replies before trusting saved summaries.
    from belief_transfer.evals.instruction_retention import assess
    for r in actual:
        meta=r['generation_metadata'];tokens=meta.get('output_token_ids',[])
        normal=bool(tokens) and tokens[-1]==protocol['eos_token_id'] and meta.get('finish_reason')=='stop' and not meta.get('backend_error')
        expected=assess(r['response'],r,normal_stop=normal)
        if r['assessment']!=expected:raise ValueError('Fresh assessment does not reconstruct')
        if (meta.get('model_revision')!=proof['generation']['revision'] or meta.get('adapter_lora_id')!=(None if arm=='base' else 1)
            or meta.get('input_token_ids')!=r['expected_input_token_ids']
            or meta.get('sampling_seed')!=r['request_seed'] or r['request_seed']!=(r['seed'] ^ 42 ^ r['eval_seed']) & 0xffffffff
            or meta.get('generation_tokens')!=len(tokens) or not tokens):raise ValueError('Fresh raw token/model/seed identity changed')
        if meta['execution']!=proof['generation'] or meta['execution_versions']!=proof['versions']:raise ValueError('Fresh raw runtime changed')
    if arm=='base':
        _,selected=report([r for r in actual if r['eval_seed']==42],reference,None)
        if rows(root/'known_items.jsonl')!=selected:raise ValueError('Fresh BASE mask changed')
        known=selected
    elif rows(root/'known_items.jsonl')!=known:raise ValueError('Adapter known mask changed')
    summary=read(root/'summary.json')
    for seed in [42,7,1729]:
        rebuilt,_=report([r for r in actual if r['eval_seed']==seed],reference,known)
        if summary['by_seed'][str(seed)]!=rebuilt:raise ValueError('Fresh summary does not reconstruct')
    return actual,known,summary


def freeze_reference(protocol):
    actual,known,summary=inspect('base',protocol)
    if not summary['by_seed']['42']['reference_usable']:raise ValueError('Fresh BASE reference insufficient; no adapters')
    return known


def run():
    import yaml
    generated,result=roots();protocol=read(generated/'protocol.json')
    if result.exists():raise FileExistsError('Started fresh retention cannot resume')
    check_bindings(protocol['source_bindings'])
    for arm in ARMS:
        if (Path('data/results/ethical_pilot')/run_id(arm)).exists():raise FileExistsError('Fresh child already started')
    result.mkdir(parents=True);(result/'STARTED').write_text(subprocess.check_output(['git','rev-parse','HEAD'],text=True))
    (result/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
    schedule=[];known=None
    try:
        for arm in ARMS:
            check_bindings(protocol['source_bindings'])
            if arm!='base':
                config=Path('configs/run')/(run_id(arm)+'.yaml')
                if config.exists():raise FileExistsError('Adapter fresh config already exists')
                mask=Path('data/results/ethical_pilot')/run_id('base')/'known_items.jsonl'
                config.write_text('# @package _global_\n'+yaml.safe_dump(overlay(arm,generated/'bank.jsonl',mask,sha(mask)),sort_keys=False))
            job=load_job(['+run='+run_id(arm)])
            if arm=='base' and config_sha(job)!=protocol['base_config_sha']:raise ValueError('Fresh BASE config changed')
            schedule.append({'arm':arm,'run_id':run_id(arm),'config_sha':config_sha(job),'known_sha256':job.instruction_retention.known_sha256})
            # Append the dispatch record before each call; its known hash is fixed before adapters.
            write_rows(result/'dispatch.jsonl',schedule)
            command=['flock','/tmp/sft-drift-cuda-benchmark.lock',PYTHON,'-u','run.py','+run='+run_id(arm)]
            operation=subprocess.run(command,check=False)
            with (result/'operations.jsonl').open('a') as out:out.write(json.dumps({'arm':arm,'run_id':run_id(arm),'command':command,'returncode':operation.returncode})+'\n')
            write_md(result/'operations.jsonl')
            if operation.returncode:raise RuntimeError('Fresh child failed: '+run_id(arm))
            _,selected,_=inspect(arm,protocol,known)
            if arm=='base':
                known=freeze_reference(protocol)
                dump(result/'known_freeze.json',{'selected_from_seed':42,'known_count':len(known),
                    'mask_sha256':sha(Path('data/results/ethical_pilot')/run_id('base')/'known_items.jsonl'),
                    'base_responses_sha256':sha(Path('data/results/ethical_pilot')/run_id('base')/'responses.jsonl')})
        (result/'COMPLETED').write_text('All1920calls recorded; inspect fresh retention, no training approval.\n')
    except BaseException as exc:dump(result/'worker_failure.json',{'error':repr(exc)});raise
    finally:(result/'TERMINAL').write_text('Finite fresh retention terminal; no resume.\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','run']);args=p.parse_args()
    {'prepare':prepare,'run':run}[args.operation]()
