"""Shared exact-runtime collection for the new reasoning-replay study only."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.config import load_job,config_sha
from belief_transfer.evals.retention_value import assess_value as procedural_value
from belief_transfer.evals.neutral_decision_value_v3 import assess_value as decision_value
from belief_transfer.stages.instruction_retention import observation as retention_observation
from belief_transfer.metrics.instruction_retention import report
from prepare_replay_weight_ablation import read,rows,sha,write_json,write_rows
from run_replay_interface_rca import inspect as inspect_decision
from run_replay_coverage_probe import commit,execute,LOCK,EVAL_PYTHON


def inspect_retention(folder: Path,bank: list[dict],runtime: dict,adapter_sha: str | None,tokenizer) -> list[dict]:
    if not (folder/'COMPLETED').exists():raise ValueError('Child incomplete')
    manifest=read(folder/'manifest.json')
    if manifest['bank_sha256']!=sha(folder/'bank.jsonl'):raise ValueError('Recorded bank hash changed')
    for k in ('model','backend','generation','decoding','max_new_tokens','batch_size','versions'):
        if manifest[k]!=runtime[k]:raise ValueError('Child runtime differs: '+k)
    if manifest['adapter_sha256']!=adapter_sha or manifest['evaluation']['eval_seeds']!=[42] or manifest['evaluation']['nonthinking_temperature']!=0:
        raise ValueError('Adapter/retention seed or short decoder differs')
    if rows(folder/'bank.jsonl')!=bank:raise ValueError('Child bank changed')
    observed=rows(folder/'responses.jsonl')
    if len(bank)!=128 or len({r['example_id'] for r in bank})!=128 or Counter(r['example_id'] for r in observed)!=Counter(r['example_id'] for r in bank):
        raise ValueError('Missing/duplicate full128retention grid')
    lookup={r['example_id']:r for r in bank};result=[]
    for r in observed:
        meta=r['generation_metadata']
        if (r.get('error') or meta.get('execution')!=runtime['generation'] or meta.get('execution_versions')!=runtime['versions']
                or meta.get('generation_tokens')!=len(meta.get('output_token_ids',[]))
                or meta.get('prompt_tokens')!=len(lookup[r['example_id']]['expected_input_token_ids'])):
            raise ValueError('Unverified execution/token metadata')
        rebuilt=retention_observation(lookup[r['example_id']],(r['backend_text'],meta),tokenizer,
            evaluation=42,revision=runtime['generation']['revision'],adapter=adapter_sha is not None)
        if rebuilt!=r:raise ValueError('Actual token/seed/native response cannot reconstruct')
        result.append(r|{'native_assessment':r['assessment'],
            'value':procedural_value(r['response'],r,normal_stop=r['assessment']['normal_stop'])})
    mask=rows(folder/'known_items.jsonl')
    if not manifest['evaluation']['fresh_base_reference'] and manifest['known_sha256']!=sha(folder/'known_items.jsonl'):
        raise ValueError('Recorded native mask hash changed')
    if manifest['evaluation']['fresh_base_reference'] and report(observed,bank,None)[1]!=mask:
        raise ValueError('BASE native mask changed')
    if report(observed,bank,mask)[0]!=read(folder/'summary.json')['by_seed']['42']:
        raise ValueError('Native retention summary changed')
    return result


def inspect(folder: Path,bank: list[dict],runtime: dict,adapter_sha: str | None,tokenizer,kind: str) -> list[dict]:
    if kind=='retention':return inspect_retention(folder,bank,runtime,adapter_sha,tokenizer)
    if kind!='decisions':raise ValueError('Unknown measurement kind')
    values=inspect_decision(folder,bank,runtime,adapter_sha,tokenizer)
    return [r|{'value_v2_assessment':r['assessment'],'assessment':r['native_assessment'],
               'value':decision_value(r['response'],r,normal_stop=r['native_assessment']['normal_stop'])} for r in values]


def overlay(name: str,model: str,bank: Path,kind: str,binding: dict,*,base_known: Path | None=None) -> dict:
    result={'defaults':['ethics_gpu_retention_rca_base_v2'],'run_id':name,
            'pilot_bench':{'adapter_path':binding['adapter_path']}}
    if kind=='decisions':
        result.update(stage='neutral_decision_retention',instruction_retention=None,
            neutral_decision_retention={'model_label':model,'bank_path':str(bank),'bank_sha256':sha(bank),
                'adapter_sha256':binding['adapter_file_sha256']})
    elif kind=='retention':
        if model!='base' and base_known is None:raise ValueError('Frozen BASE native reference required')
        result.update(stage='instruction_retention',neutral_decision_retention=None)
        result['instruction_retention']={'model_label':model,'bank_path':str(bank),'bank_sha256':sha(bank),
            'fresh_base_reference':model=='base','known_path':str(base_known) if base_known else None,
            'known_sha256':sha(base_known) if base_known else None,'adapter_sha256':binding['adapter_file_sha256'],
            'eval_seeds':[42],'nonthinking_temperature':0}
    else:raise ValueError('Unknown measurement kind')
    return result


def collect(name: str,model: str,bank: Path,kind: str,binding: dict,runtime: dict,tokenizer,parent: Path,*,base_known: Path | None=None) -> list[dict]:
    import yaml
    config=Path('configs/run',name+'.yaml');folder=Path('data/results/ethical_pilot')/name
    if config.exists() or folder.exists():raise FileExistsError('Started child/config cannot resume or overwrite')
    if binding['adapter_path'] and sha(Path(binding['adapter_path'])/'adapter_model.safetensors')!=binding['adapter_file_sha256']:
        raise ValueError('Fixed adapter changed before dispatch')
    if binding['adapter_path'] and binding.get('adapter_config_sha256') and sha(Path(binding['adapter_path'])/'adapter_config.json')!=binding['adapter_config_sha256']:
        raise ValueError('Fixed adapter configuration changed before dispatch')
    config.write_text('# @package _global_\n'+yaml.safe_dump(overlay(name,model,bank,kind,binding,base_known=base_known),sort_keys=False))
    job=load_job(['+run='+name])
    dispatch={'source_commit':commit(),'config_sha':config_sha(job),'adapter_sha256':binding['adapter_file_sha256']}
    write_json(parent/(name+'_dispatch.json'),dispatch)
    if not execute([*LOCK,EVAL_PYTHON,'-u','run.py','+run='+name],parent,name):
        raise RuntimeError('Technical child failure; preserve partials: '+name)
    if config_sha(load_job(['+run='+name]))!=dispatch['config_sha'] or not commit().startswith(read(folder/'manifest.json')['code_revision']):
        raise ValueError('Dispatch source/config changed')
    if kind=='retention' and base_known is not None and sha(folder/'known_items.jsonl')!=sha(base_known):
        raise ValueError('Native BASE mask copy changed')
    result=inspect(folder,rows(bank),runtime,binding['adapter_file_sha256'],tokenizer,kind)
    write_rows(parent/(name+'_values.jsonl'),result)
    queue=[r for r in result if r['value']['value_correct'] is not True or not r['native_assessment']['strict_format']]
    write_rows(parent/(name+'_review_queue.jsonl'),queue)
    return result
