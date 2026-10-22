"""Fresh finite controller for remaining measurements of the same completed trial.

Never trains, restarts the failed controller, or repeats its completed128responses.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.config import load_job,config_sha
from prepare_base_reasoning_replay import MASTER,TRAIN
from prepare_base_reasoning_execution import GENERATED as ORIGINAL_INPUTS,POINTS,PART_NAMES,measure_id,eval_id
from prepare_replay_weight_ablation import read,rows,sha,write_json,write_rows
from run_replay_weight_confirmation import check_bindings
from validate_registry_calibration import verify_binding
from base_reasoning_runtime import inspect
import run_base_reasoning_probe as probe
import run_replay_coverage_probe as previous

RECOVERY='ethics_gpu_base_reasoning_recovery_v1'
GENERATED=Path('data/generated/ethical_pilot')/RECOVERY
RESULTS=Path('data/results/ethical_pilot')/RECOVERY
ORIGINAL=Path('data/results/ethical_stance_sft')/MASTER
PLAN=Path('../changelog/2026-10-22-base-reasoning-collector-recovery-plan.md')
CHILD=measure_id('midpoint','retention')
CHILD_ROOT=Path('data/results/ethical_pilot')/CHILD
REPAIRED={'scripts/base_reasoning_runtime.py','scripts/run_base_reasoning_probe.py'}


def rebound_sources(old: dict) -> tuple[dict,list[dict],list[str]]:
    sources={};changes=[];derived=[]
    for name,before in old.items():
        path=Path(name)
        companions=[str(path.with_suffix(s)) for s in ('.jsonl','.json')]
        if path.suffix=='.md' and any(p in old for p in companions):
            # Views are explicitly regeneratable. Their authoritative source stays bound.
            derived.append(name);continue
        after=sha(path)
        if before!=after:
            if name not in REPAIRED:raise ValueError('Unexpected frozen source/input change: '+name)
            changes.append({'path':name,'before_sha256':before,'after_sha256':after,
                'reason':'Typed omitted-false manifest handling or explicit fresh-output/reused-record routing; no inference/scoring/data change.'})
        sources[name]=after
    if {c['path'] for c in changes}!=REPAIRED:raise ValueError('Require exactly the two reviewed collector/controller repairs')
    return sources,changes,derived


def fresh_outputs() -> None:
    if RESULTS.exists():raise FileExistsError('Recovery has started; no resume/restart')
    for point in POINTS:
        for part in PART_NAMES:
            name=measure_id(point,part)
            if name==CHILD:continue
            if Path('data/results/ethical_pilot',name).exists() or Path('configs/run',name+'.yaml').exists():
                raise FileExistsError('Remaining child already started: '+name)
        for phase in ('development','validation','reading','unqualified'):
            if Path('data/results/ethical_pilot',eval_id(point,phase)).exists():
                raise FileExistsError('Remaining full100measurement already started')


def prepare() -> None:
    required={f'{p}/ethical_pilot/{RECOVERY}' for p in ('generated','results')}
    if not required<=set(read(Path('configs/handoff.json'))['include_paths']):raise ValueError('Register recovery paths first')
    if GENERATED.exists():raise FileExistsError('Do not overwrite prepared recovery')
    fresh_outputs()
    if not (ORIGINAL/'TERMINAL').is_file() or read(ORIGINAL/'failure.json')['error']!="KeyError('fresh_base_reference')":
        raise ValueError('Only the recorded terminal collector error is recoverable here')
    if not (CHILD_ROOT/'COMPLETED').is_file():raise ValueError('Preserve completed128responses first')
    original_path=ORIGINAL_INPUTS/'protocol.json';p=read(original_path)
    sources,changes,derived=rebound_sources(p['source_bindings'])
    additional=[original_path,PLAN,Path(__file__).relative_to(Path.cwd()),
        ORIGINAL/'failure.json',ORIGINAL/'TERMINAL',ORIGINAL/'candidate_training_binding.json',
        ORIGINAL/'checkpoint_identity_v1.json',ORIGINAL/'midpoint'/(CHILD+'_dispatch.json'),
        Path('configs/run',CHILD+'.yaml'),ORIGINAL_INPUTS/'proof_review_selection_v1.json']
    for folder in (CHILD_ROOT,Path('data/results/ethical_stance_sft')/TRAIN,
                   Path('data/checkpoints/ethical_stance_sft')/TRAIN):
        additional.extend(f for f in folder.rglob('*') if f.is_file() and f.suffix!='.md')
    sources.update({str(f):sha(f) for f in additional})
    p.update(run_id=RECOVERY,source_bindings=sources,repaired_sources=changes,
        regeneratable_views_excluded_from_binding=derived,original_protocol_sha256=sha(original_path),
        original_master=MASTER,reused_retention_run_id=CHILD,reused_retention_records=128,
        no_training=True,no_resume=True,stop_on_reviewed_negative=True,
        interpretation='Same fixed checkpoints/data/gates; fresh controller after terminal metadata reader error. Completed128raw replies reused once; no training or correctness-conditioned redraw.')
    GENERATED.mkdir(parents=True)
    write_json(GENERATED/'protocol.json',p)
    print({'recovery_frozen':RECOVERY,'source_changes':changes,'reused_responses':128,'new_training_runs':0})


def reused_retention(protocol: dict,tokenizer) -> list[dict]:
    binding=read(ORIGINAL/'checkpoint_identity_v1.json')['bindings']['midpoint'];verify_binding(binding)
    dispatch=read(ORIGINAL/'midpoint'/(CHILD+'_dispatch.json'));manifest=read(CHILD_ROOT/'manifest.json')
    if (dispatch['adapter_sha256']!=binding['adapter_file_sha256']
            or config_sha(load_job(['+run='+CHILD]))!=dispatch['config_sha']
            or not dispatch['source_commit'].startswith(manifest['code_revision'])):
        raise ValueError('Reused child dispatch/config/adapter mismatch')
    values=inspect(CHILD_ROOT,rows(Path(protocol['bank_path'])),protocol['runtime_reference'],
                   binding['adapter_file_sha256'],tokenizer,'retention')
    if len(values)!=128:raise ValueError('Reused completed grid differs')
    return values


def run() -> None:
    from belief_transfer.inference.backend import require_training_backend
    from transformers import AutoTokenizer
    require_training_backend();fresh_outputs()
    path=GENERATED/'protocol.json';p=read(path);check_bindings(p['source_bindings']);previous.preserved(path)
    for name in p['source_bindings']:
        source=Path(name)
        if source.is_relative_to('data'):previous.preserved(source)
    runtime=p['runtime_reference'];tokenizer=AutoTokenizer.from_pretrained(runtime['model']['pretrained'],
        revision=runtime['generation']['revision'],local_files_only=True)
    binding=previous.verify_candidate(p,tokenizer,train_id=TRAIN)
    if binding!=read(ORIGINAL/'candidate_training_binding.json'):raise ValueError('Completed training binding differs')
    identities=read(ORIGINAL/'checkpoint_identity_v1.json');bindings=identities['bindings']
    for b in bindings.values():verify_binding(b)
    if probe.terminal_alias(bindings['terminal'],binding)!=identities['terminal_aliases_final']:
        raise ValueError('Checkpoint alias changed')
    reference=probe.references(p,tokenizer);reused=reused_retention(p,tokenizer)
    RESULTS.mkdir(parents=True);(RESULTS/'STARTED').write_text(previous.commit()+'\n')
    try:
        write_json(RESULTS/'reused_retention_v1.json',{'run_id':CHILD,'records':128,
            'responses_sha256':sha(CHILD_ROOT/'responses.jsonl'),'manifest_sha256':sha(CHILD_ROOT/'manifest.json'),
            'source_dispatch_sha256':sha(ORIGINAL/'midpoint'/(CHILD+'_dispatch.json')),'new_calls':0})
        outputs={}
        for point in POINTS:
            check_bindings(p['source_bindings'])
            if point=='terminal' and identities['terminal_aliases_final']:continue
            outputs[point]=probe.measure(point,bindings[point],p,reference,tokenizer,output_root=RESULTS,
                                        reused_retention=reused if point=='midpoint' else None)
        if identities['terminal_aliases_final']:
            outputs['terminal']={'alias_of':'final','development_passed':outputs['final']['development_passed']}
        write_json(RESULTS/'comparison_v1.json',{'primary':'final','development_passed':outputs['final']['development_passed'],
            'checkpoints':outputs,'original_master':MASTER,'reused_retention_records':128,
            'full_response_review':'pending','stop_on_reviewed_negative':True,
            'interpretation':'No new training, gate changes or checkpoint selection. Review final result; if negative pause user goal and recommend next steps. No automatic confirmation or further experiments.'})
        (RESULTS/'COLLECTION_COMPLETED').write_text('Same fixed trial collected after metadata repair; review required.\n')
    except BaseException as exc:
        write_json(RESULTS/'failure.json',{'error':repr(exc)});raise
    finally:(RESULTS/'TERMINAL').write_text('Fresh finite recovery ended; no resume/restart.\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['prepare','run'])
    if parser.parse_args().operation=='prepare':prepare()
    else:run()
