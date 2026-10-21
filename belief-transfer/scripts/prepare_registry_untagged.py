"""Freeze one context-only ablation: identical supervised targets without DOCTAG."""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import prepare_registry_replay as replay
import probe_instruction_retention as retention
import probe_registry_transfer as transfer
import validate_registry_calibration as validator

RUN = 'ethics_sft_registry_untagged_replay_v1'
VALIDATION = 'ethics_gpu_registry_untagged_validation_v1'
TRANSFER = 'ethics_gpu_registry_untagged_transfer_v1'
RETENTION = 'ethics_gpu_registry_untagged_retention_v1'
NATIVE = 'ethics_gpu_registry_replay_native_v1'


def verify_identical_targets(old: list[dict], new: list[dict]) -> None:
    """The intervention must change context only, preserving ordered eligible targets."""
    if len(old) != len(new):
        raise ValueError('Context ablation changed chunk count')
    for before, after in zip(old, new, strict=True):
        if any(before[k] != after[k] for k in ['example_id', 'source_kind', 'chunk_start']):
            raise ValueError('Context ablation changed chunk identity/order')
        eligible = lambda row: [x for x in row['labels'][1:] if x != -100]
        if eligible(before) != eligible(after):
            raise ValueError('Context ablation changed supervised targets')
        if before['source_kind'] != 'synthetic' and before != after:
            raise ValueError('Context ablation changed background/replay tokens')


def main() -> None:
    from transformers import AutoTokenizer
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.config import load_job
    from belief_transfer.dataset.document_sft import load_manifest, preprocessing_contract, tokenize_document
    from belief_transfer.stages.document_sft import verify_training_plan

    generated = Path('data/generated/ethical_stance_sft') / RUN
    config = Path('configs/run') / (RUN + '.yaml')
    roots = [generated, Path('data/results/ethical_stance_sft') / RUN,
             Path('data/checkpoints/ethical_stance_sft') / RUN]
    for run in [VALIDATION, TRANSFER, RETENTION]:
        roots.extend(Path('data') / part / 'ethical_pilot' / run for part in ['generated', 'results'])
    registry = json.loads(Path('configs/handoff.json').read_text())
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in roots):
        raise ValueError('Register every new artifact path first')
    if str(generated.relative_to('data')) not in registry['corpus_store']['paths']:
        raise ValueError('Register heavy generated corpus')
    if any(p.exists() for p in [*roots, config]):
        raise FileExistsError('Fresh run IDs required; no overwrite/resume')
    source = Path('data/generated/ethical_stance_sft') / replay.RUN
    previous = Path('data/results/ethical_stance_sft') / replay.RUN
    native = Path('data/results/ethical_pilot') / NATIVE
    if not all((p / 'COMPLETED').exists() for p in [previous, native]):
        raise ValueError('Finish preceding training and native diagnosis first')
    if not (native / 'agent_review_v1.jsonl').exists():
        raise ValueError('Read and record all preceding native diagnostic replies first')
    old_plan = json.loads((source / 'plan.json').read_text())
    manifest = source / 'documents.jsonl'
    if replay.teacher.sha(manifest) != old_plan['dataset_sha256']:
        raise ValueError('Reference manifest changed')
    job = load_job(['+run=' + replay.RUN])
    if job.document_sft.synthetic_prefix != '<DOCTAG>\n':
        raise ValueError('Unexpected reference prefix')
    job.document_sft.synthetic_prefix = ''
    tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-4B', revision=replay.teacher.REVISION,
                                             local_files_only=True)
    rows = load_manifest(manifest)
    chunks = [c for r in rows for c in tokenize_document(r, tokenizer,
        max_length=job.document_sft.max_length, synthetic_prefix='',
        serialization=job.document_sft.serialization, replay=job.document_sft.replay)]
    actual = previous / 'tokenized.jsonl'
    verify_identical_targets(list(map(json.loads, actual.read_text().splitlines())), chunks)
    dose = {kind: sum(sum(x != -100 for x in c['labels'][1:]) for c in chunks
                     if c['source_kind'] == kind) for kind in ['synthetic', 'c4', 'replay']}
    if dose != old_plan['dose']['loss_tokens_by_kind']:
        raise ValueError('Reference target exposure changed')
    generated.mkdir(parents=True)
    for name in ['documents.jsonl', 'anchors.jsonl']:
        (generated / name).write_bytes((source / name).read_bytes())
        write_md(generated / name)
    base = ('# @package _global_\n# Context-only neutral ablation; unchanged acceptance gates.\n'
            f'defaults:\n  - {replay.RUN}\nrun_id: {RUN}\ndocument_sft:\n'
            f'  manifest_path: {generated / "documents.jsonl"}\n  synthetic_prefix: ""\n')
    config.write_text(base)
    job = load_job(['+run=' + RUN])
    plan = {**old_plan, 'run_id': RUN, 'training': job.training.model_dump(),
        'preprocessing': preprocessing_contract(job.document_sft),
        'hypothesis': 'Removing the ungenerated masked document tag improves unprefilled chat access to learned mappings while preserving controls and fixed known retention.',
        'contrasts': 'Single context intervention versus registry_instruction_replay_v1: remove synthetic DOCTAG. Byte-identical ordered documents, replay draws and anchors; every ordered eligible target unchanged; C4/replay tokenized chunks identical. Same fresh base, optimizer, LR, LoRA rank/modules, seed, batches,824steps and final-only qualification. No change to document bodies or evaluation criteria.',
        'falsifier': old_plan['falsifier'],
        'analysis': old_plan['analysis'] + ' Compare against the preserved tagged candidate; prefix completion never replaces ordinary chat recall. A failed tag ablation does not establish lack of learning capacity.',
        'dose': {**old_plan['dose'], 'input_tokens': sum(len(c['input_ids']) for c in chunks),
                 'loss_tokens_by_kind': dose},
        'provenance': {**old_plan['provenance'], 'script_sha256': replay.teacher.sha(Path(__file__)),
            'tagged_plan_sha256': replay.teacher.sha(source / 'plan.json'),
            'actual_tagged_tokens_sha256': replay.teacher.sha(actual),
            'native_diagnostic_summary_sha256': replay.teacher.sha(native / 'summary.json'),
            'native_agent_review_sha256': replay.teacher.sha(native / 'agent_review_v1.jsonl')},
        'bounded_work': 'One untagged final-adapter candidate, all three fixed evaluations; no sweep, checkpoint selection or ethical dispatch.'}
    path = generated / 'plan.json'
    path.write_text(json.dumps(plan, indent=2) + '\n')
    config.write_text(base + f'  plan_path: {path}\n  plan_sha256: {replay.teacher.sha(path)}\n')
    verify_training_plan(load_job(['+run=' + RUN]), generated / 'documents.jsonl')
    (generated / 'PLAN.md').write_text('# Untagged context ablation\n\n```json\n' + json.dumps(plan, indent=2) + '\n```\n')
    validator.prepare(Path('data/generated/ethical_pilot') / VALIDATION, run_id=VALIDATION, training_run_id=RUN)
    transfer.prepare(Path('data/generated/ethical_pilot') / TRANSFER, [RUN])
    retention.prepare(Path('data/generated/ethical_pilot') / RETENTION, training_run_id=RUN)
    replay.write_worker(generated, config, roots,
        [Path(__file__), source / 'plan.json', manifest, actual, native / 'summary.json',
         native / 'agent_review_v1.jsonl'], run_id=RUN, validation_id=VALIDATION,
        transfer_id=TRANSFER, retention_id=RETENTION)
    print(json.dumps({'run_id': RUN, 'plan_sha256': replay.teacher.sha(path),
                      'schedule': plan['schedule'], 'dose': plan['dose']}, indent=2))


if __name__ == '__main__':
    main()
