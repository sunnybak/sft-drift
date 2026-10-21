"""Freeze one high-rate varied-request trial with dose-explicit disjoint BASE replay."""
from __future__ import annotations
import json
import math
import subprocess
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import build_instruction_replay as teacher
import derive_instruction_replay as derived
import probe_instruction_retention as retention

RUN='ethics_sft_registry_instruction_replay_v1'
REFERENCE='ethics_sft_registry_varied_requests_v1'
VALIDATION='ethics_gpu_registry_replay_validation_v1'
TRANSFER='ethics_gpu_registry_replay_transfer_v1'
RETENTION='ethics_gpu_registry_replay_retention_v1'


def replay_draws(rows: list[dict], original_targets: int) -> tuple[list[dict],int]:
    if not rows or len({r['example_id'] for r in rows})!=len(rows) or original_targets<1:
        raise ValueError('Distinct finite replay sources and positive original exposure required')
    if any(type(r.get('loss_tokens')) is not int or r['loss_tokens']<1 or r['source_kind']!='replay' for r in rows):
        raise ValueError('Measured full-response replay targets required')
    # Smallest whole-pool repetition reaching20%of total target mass; no partial response budgets.
    cycles=math.ceil(original_targets/(4*sum(r['loss_tokens'] for r in rows)))
    if not 1<=cycles<=16:raise ValueError('Replay dose would exceed finite16cycle bound')
    draws=[]
    for cycle in range(cycles):
        for r in rows:
            draws.append({**r,'example_id':f'replay_draw/{cycle:02d}/{r["example_id"]}',
                'source_id':teacher.RUN+'/'+r['source_id'],'replay_source_example_id':r['example_id'],'replay_cycle':cycle})
    return draws,cycles



def write_worker(generated: Path, config: Path, roots: list[Path], extra_inputs: list[Path], *,
                 run_id: str = RUN, validation_id: str = VALIDATION,
                 transfer_id: str = TRANSFER, retention_id: str = RETENTION) -> None:
    worker = generated/'worker.sh'
    manifest = generated/'execution_manifest.json'
    commands = [
        f'flock /tmp/sft-drift-cuda-benchmark.lock .venv/bin/python -u run.py +run={run_id}',
        f'.venv/bin/python -u scripts/validate_registry_calibration.py run --run-id {validation_id} --training-run-id {run_id}',
        f'.venv/bin/python -u scripts/probe_registry_transfer.py run --run-id {transfer_id}',
        f'.venv/bin/python -u scripts/probe_instruction_retention.py run --run-id {retention_id}',
        f'.venv/bin/python -u scripts/judge_registry_replay.py --training-run-id {run_id} --validation-id {validation_id} --transfer-id {transfer_id} --retention-id {retention_id}',
    ]
    check = (".venv/bin/python - <<'INPUT_CHECK'\nimport hashlib,json\nfrom pathlib import Path\n"
        + f"p=json.loads(Path('{manifest}').read_text())\n"
        + "for name,digest in p['immutable_inputs'].items():\n"
        + " if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest: raise ValueError('Changed frozen trial input: '+name)\n"
        + "for name in p['new_output_roots']:\n"
        + " if Path(name).exists(): raise FileExistsError('Started run cannot resume or overwrite: '+name)\nINPUT_CHECK\n")
    worker.write_text('#!/bin/bash\nset -euo pipefail\ncd /workspace/sft-drift/belief-transfer\n'+check+'\n'.join(commands)+'\n')
    inputs = {config,Path('run.py'),Path('uv.lock'),Path('pyproject.toml'),*extra_inputs}
    tracked=subprocess.check_output(['git','ls-files','--','src/belief_transfer','configs','scripts'],text=True).splitlines()
    inputs.update(Path(name) for name in tracked if Path(name).suffix in {'.py','.yaml'})
    inputs.update([Path('scripts/prepare_registry_replay.py'),Path('scripts/judge_registry_replay.py')])
    for root in roots:
        if '/generated/' in '/'+str(root)+'/': inputs.update(p for p in root.rglob('*') if p.is_file())
    if any(p.is_absolute() or '..' in p.parts for p in inputs):
        raise ValueError('Worker inputs must be portable project-relative paths')
    payload = {'run_id':run_id,'immutable_inputs':{str(p):teacher.sha(p) for p in sorted(inputs)},
        'new_output_roots':[str(p) for p in roots if '/generated/' not in '/'+str(p)+'/'],
        'commands':commands,'resume_supported':False,'automatic_ethical_dispatch':False}
    manifest.write_text(json.dumps(payload,indent=2)+'\n')
    (generated/'EXECUTION.md').write_text('# Finite replay candidate worker\n\n```json\n'+json.dumps(payload,indent=2)+'\n```\n')


def main() -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.config import load_job
    from belief_transfer.dataset.document_sft import load_manifest,tokenize_document,preprocessing_contract
    from belief_transfer.dataset.pooled_dose import matched_steps
    from belief_transfer.schemas import DocumentReplaySpec
    from belief_transfer.stages.document_sft import verify_training_plan
    from transformers import AutoTokenizer
    generated=Path('data/generated/ethical_stance_sft')/RUN
    config=Path('configs/run')/(RUN+'.yaml')
    roots=[generated,Path('data/results/ethical_stance_sft')/RUN,Path('data/checkpoints/ethical_stance_sft')/RUN]
    for run in [VALIDATION,TRANSFER,RETENTION]:roots.extend([Path('data')/part/'ethical_pilot'/run for part in ['generated','results']])
    registry=json.loads(Path('configs/handoff.json').read_text())
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in roots):raise ValueError('Register every trial artifact path first')
    if str(generated.relative_to('data')) not in registry['corpus_store']['paths']:raise ValueError('Register heavy generated trial corpus')
    if any(p.exists() for p in [*roots,config]):raise FileExistsError('Fresh trial IDs required, no overwrite/resume')
    ref=Path('data/results/ethical_pilot')/retention.BASE
    if not (ref/'COMPLETED').exists():raise ValueError('Complete BASE retention before preparing training')
    reference=json.loads((ref/'summary.json').read_text())
    if not reference['reference_usable'] or teacher.sha(ref/'known_items.jsonl')!=reference['known_items_sha256']:
        raise ValueError('BASE-known reference insufficient or changed')
    source=Path('data/generated/ethical_stance_sft')/REFERENCE
    replay_path=Path('data/generated/ethical_stance_sft')/derived.RUN/'documents.jsonl'
    replay_result=Path('data/results/ethical_stance_sft')/derived.RUN
    if not (replay_result/'COMPLETED').exists():raise ValueError('Replay derivation incomplete')
    replay_summary=json.loads((replay_result/'summary.json').read_text())
    if teacher.sha(replay_path)!=replay_summary['documents_sha256']:raise ValueError('Replay manifest changed')
    original=load_manifest(source/'documents.jsonl');replay=load_manifest(replay_path)
    old_plan=json.loads((source/'plan.json').read_text());old_targets=sum(old_plan['dose']['loss_tokens_by_kind'].values())
    draws,cycles=replay_draws(replay,old_targets);rows=original+draws
    job=load_job(['+run='+REFERENCE]);job.document_sft.replay=DocumentReplaySpec();job.training.sft.lr=1e-4
    tokenizer=AutoTokenizer.from_pretrained('Qwen/Qwen3-4B',revision=teacher.REVISION,local_files_only=True)
    chunks=[c for r in rows for c in tokenize_document(r,tokenizer,max_length=1024,
        serialization=job.document_sft.serialization,replay=job.document_sft.replay)]
    dose={kind:sum(sum(x!=-100 for x in c['labels'][1:]) for c in chunks if c['source_kind']==kind) for kind in ['synthetic','c4','replay']}
    if {k:dose[k] for k in ['synthetic','c4']}!=old_plan['dose']['loss_tokens_by_kind']:
        raise ValueError('Original synthetic/C4target exposure changed')
    if dose['replay']!=cycles*replay_summary['unique_loss_tokens']:raise ValueError('Replay target exposure changed')
    steps=matched_steps([len(chunks)],batch_size=4,grad_accum=2)
    if steps%2:raise ValueError('Use a fresh prospective schedule for odd step count; no implicit checkpoint selection')
    generated.mkdir(parents=True);(generated/'.writer.lock').touch()
    manifest=generated/'documents.jsonl';manifest.write_text(''.join(json.dumps(r)+'\n' for r in rows));write_md(manifest)
    (generated/'anchors.jsonl').write_bytes((source/'anchors.jsonl').read_bytes());write_md(generated/'anchors.jsonl')
    base=('# @package _global_\n# One neutral high-rate/varied-request/replay candidate; no ethical outcomes.\n'
          'defaults:\n  - ethics_sft_registry_varied_requests_v1\n'+f'run_id: {RUN}\ntraining:\n  sft:\n    lr: 0.0001\n'
          f'document_sft:\n  manifest_path: {manifest}\n  max_steps: {steps}\n  save_steps: {steps//2}\n'
          '  replay:\n    mode: qwen3_raw_response_v1\n    continuation_context_tokens: 64\n')
    config.write_text(base);job=load_job(['+run='+RUN])
    plan={**old_plan,'run_id':RUN,'dataset_sha256':teacher.sha(manifest),'training':job.training.model_dump(),
        'schedule':{'max_steps':steps,'save_steps':steps//2},'preprocessing':preprocessing_contract(job.document_sft),
        'hypothesis':'Stronger document learning plus varied requests and disjoint instruction/reasoning replay yields unprefilled chat recall while preserving frozen controls and pretraining-known skills.',
        'contrasts':'Combined engineering candidate, not an isolated causal contrast. Versus varied/low: LR1e-4 andfixed BASE replay added. Same ordered synthetic/C4bodies, original full targets andrank16/alpha32,all7modules,seed42,batch4/accum2,one expanded-manifest pass. No checkpoint/outcome selection.',
        'falsifier':'Fail if either128-token unprefilled semantic query family<18/20,BASE>2/20,any engineering/identity check fails,frozen controls accuracy<.95/extraction orstrict<1/nullflip>.05/incomplete16pairs/abnormalstops,or fixed BASE-known retention semantic<.95/format,boundaries,normalstops<1in either mode. Preserve every failed result. No automatic ethical training.',
        'controls':'Same pinned C4, fresh BASEoriginal lookup/semantic/frozen controls; disjoint BASE-known retention mask frozen before this training. Replay has no registry mappings orfrozen control prompts. Original failed lookup/matrix/acquisition results unchanged.',
        'analysis':'Retain original16-token exact lookup separately; new contract uses two preregistered128-token semantic families with full-reply agent review. Reused20facts and32controls are development checks. Retention reports all128andfixed known subset per mode; no missing-to-neutral imputation. A pass needs fresh neutral confirmation before ethical treatment.',
        'checkpoint_policy':{'steps':[steps//2,steps],'selection':'Final only; midpoint saved for preservation, not outcome selection'},
        'dose':{'documents':len(rows),'chunks':len(chunks),'input_tokens':sum(len(c['input_ids']) for c in chunks),
            'loss_tokens_by_kind':dose,'replay_unique_documents':len(replay),'replay_draws':len(draws),'replay_whole_pool_cycles':cycles,
            'replay_target_share':dose['replay']/sum(dose.values()),'policy':'Minimum whole-pool cycles reaching20%total eligible targets; max16cycles; all full replies, no partial response masks. Repetition is exposure, not diversity.'},
        'provenance':{**old_plan['provenance'],'script_sha256':teacher.sha(Path(__file__)),'reference_manifest_sha256':teacher.sha(source/'documents.jsonl'),
            'replay_manifest_sha256':teacher.sha(replay_path),'replay_derivation_summary_sha256':teacher.sha(replay_result/'summary.json')},
        'retention_reference':{'run_id':retention.BASE,'summary_sha256':teacher.sha(ref/'summary.json'),
            'known_items_sha256':teacher.sha(ref/'known_items.jsonl'),'bank_sha256':teacher.sha(Path('data/generated/ethical_pilot')/retention.BASE/'bank.jsonl')},
        'prospective_criteria':{**old_plan['prospective_criteria'],'retention_semantic_min':.95,'retention_strict':1.0,'retention_normal_stops':True},
        'bounded_work':'One final-adapter candidate, all three evaluations regardless of qualification outcomes; inspect before any next trial. No sweep or ethical dispatch.'}
    path=generated/'plan.json';path.write_text(json.dumps(plan,indent=2)+'\n')
    config.write_text(base+f'  plan_path: {path}\n  plan_sha256: {teacher.sha(path)}\n')
    verify_training_plan(load_job(['+run='+RUN]),manifest)
    (generated/'PLAN.md').write_text('# Frozen neutral replay candidate\n\n```json\n'+json.dumps(plan,indent=2)+'\n```\n')
    import validate_registry_calibration as validator
    import probe_registry_transfer as transfer
    validator.prepare(Path('data/generated/ethical_pilot')/VALIDATION,run_id=VALIDATION,training_run_id=RUN)
    transfer.prepare(Path('data/generated/ethical_pilot')/TRANSFER,[RUN])
    retention.prepare(Path('data/generated/ethical_pilot')/RETENTION,training_run_id=RUN)
    write_worker(generated,config,roots,[replay_path,replay_result/'summary.json',ref/'summary.json',ref/'known_items.jsonl',
        Path('data/generated/ethical_pilot')/retention.BASE/'bank.jsonl',source/'documents.jsonl',source/'plan.json',
        Path(old_plan['provenance']['anchor_source']),Path('data/results/ethical_pilot')/teacher.RUN/'responses.jsonl'])
    print(json.dumps({'training_run_id':RUN,'plan_sha256':teacher.sha(path),'steps':steps,'dose':plan['dose']},indent=2))


if __name__=='__main__':main()
