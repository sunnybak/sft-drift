"""Prepare one request-diversity follow-up; same bodies/dose, no ethical outcomes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
RUN = 'ethics_sft_registry_varied_requests_v1'
REFERENCE = 'ethics_sft_registry_chat_low_calibration_v1'
VALIDATION = 'ethics_gpu_registry_varied_requests_validation_v1'
TRANSFER = 'ethics_gpu_registry_varied_requests_transfer_v1'
REQUESTS = (
    'Write a reference note explaining the registry entry named {name}.',
    'Describe the stipulated registry assignment associated with {name}.',
    'Which four-digit identifier belongs to {name} in this registry? Explain the entry in a reference note.',
    'Explain how the constructed registry records {name} and its identifying digits.',
    'Give an informative account of the recorded name-to-code association for {name}.',
    'Describe the identifier recorded for the registry entry {name}, with explanatory context.',
    'Provide a reference passage identifying {name} and the digits attached to that entry.',
    'What identifying value does the stipulated reference attach to {name}? Include an explanation.',
    'Explain the relationship between the entry name {name} and its assigned identifier.',
    'Write a registry description that identifies the recorded digits for {name}.',
)


def requests(rows: list[dict], evaluation_prompts: list[str]) -> list[dict]:
    result = []
    for row in rows:
        copy = dict(row)
        if row['source_kind'] == 'synthetic':
            index = int(row['example_id'].rsplit('__', 1)[1])
            copy['training_request'] = REQUESTS[index % len(REQUESTS)].format(name=row['toy_entity'])
            if row['toy_code'] in copy['training_request'] or any(p in copy['training_request'] for p in evaluation_prompts):
                raise ValueError('Answer or held-out query leaked into training request')
        result.append(copy)
    return result


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.config import load_job
    from belief_transfer.dataset.document_sft import load_manifest, preprocessing_contract, tokenize_document
    from belief_transfer.dataset.pooled_dose import matched_steps
    from belief_transfer.stages.document_sft import verify_training_plan
    from transformers import AutoTokenizer
    generated = Path('data/generated/ethical_stance_sft') / RUN
    config = Path('configs/run') / (RUN + '.yaml')
    registry = json.loads(Path('configs/handoff.json').read_text())
    roots = [generated, Path('data/results/ethical_stance_sft') / RUN, Path('data/checkpoints/ethical_stance_sft') / RUN]
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in roots) or str(generated.relative_to('data')) not in registry['corpus_store']['paths']:
        raise ValueError('Register follow-up paths before preparation')
    if any(p.exists() for p in [*roots, config]):
        raise FileExistsError('Fresh run required; no overwrite/resume')
    source = Path('data/generated/ethical_stance_sft') / REFERENCE
    evaluation = Path('data/generated/ethical_pilot/ethics_gpu_registry_transfer_development_v1/bank.jsonl')
    bank = [json.loads(line) for line in evaluation.read_text().splitlines()]
    anchors = load_manifest(source / 'anchors.jsonl')
    rows = requests(load_manifest(source / 'documents.jsonl'), [r['prompt'] for r in bank] + [a['memory_prompt'] for a in anchors])
    reference = load_job(['+run=' + REFERENCE])
    tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-4B', revision=reference.document_sft.model_revision, local_files_only=True)
    chunks = [c for row in rows for c in tokenize_document(row, tokenizer, max_length=1024, serialization=reference.document_sft.serialization)]
    dose = {kind: sum(sum(x != -100 for x in c['labels'][1:]) for c in chunks if c['source_kind'] == kind) for kind in ['synthetic', 'c4']}
    old_plan = json.loads((source / 'plan.json').read_text())
    if dose != old_plan['dose']['loss_tokens_by_kind']:
        raise ValueError('Changed target exposure; do not run this contrast')
    steps = matched_steps([len(chunks)], batch_size=4, grad_accum=2)
    generated.mkdir(parents=True)
    (generated / '.writer.lock').touch()
    manifest = generated / 'documents.jsonl'
    manifest.write_text(''.join(json.dumps(row) + '\n' for row in rows)); write_md(manifest)
    (generated / 'anchors.jsonl').write_bytes((source / 'anchors.jsonl').read_bytes()); write_md(generated / 'anchors.jsonl')
    base = ('# @package _global_\n# One neutral request-diversity follow-up; no ethical outcome tuning.\n'
            'defaults:\n  - ethics_sft_registry_chat_low_calibration_v1\n'
            f'run_id: {RUN}\ndocument_sft:\n  manifest_path: {manifest}\n  max_steps: {steps}\n  save_steps: {steps//2}\n')
    config.write_text(base)
    job = load_job(['+run=' + RUN])
    plan = {**old_plan, 'run_id': RUN, 'dataset_sha256': sha(manifest), 'training': job.training.model_dump(),
            'schedule': {'max_steps': steps, 'save_steps': steps//2}, 'preprocessing': preprocessing_contract(job.document_sft),
            'hypothesis': 'Diverse neutral questions paired with the same full reference documents improve retrieval through held-out chat questions at the control-preserving learning rate.',
            'contrasts': 'Only synthetic training requests change versus assistant/low reference. Same ordered bodies, C4, full target dose and settings; derived chunk/step counts may differ. Single-seed development comparison, not independent confirmation.',
            'falsifier': 'New prospective development check fails if either128-token semantic lookup family is below18/20, BASE exceeds2/20, any engineering/identity check fails, frozen controls accuracy<.95 or strict<1 or null flips>.05 or abnormal stops. No ethical training automatically follows.',
            'analysis': 'Report original16-token exact lookup unchanged as a separate endpoint; it no longer defines the new semantic retrieval contract. Numeric match must be verified in complete replies. Two query families reuse20facts, not40independent facts. These are reused development references, not held-out validation of settings.',
            'checkpoint_policy': {'steps': [steps//2, steps], 'selection': 'Final only; no outcome-selected checkpoint'},
            'dose': {**old_plan['dose'], 'chunks': len(chunks), 'input_tokens': sum(len(c['input_ids']) for c in chunks), 'loss_tokens_by_kind': dose},
            'provenance': {**old_plan['provenance'], 'script_sha256': sha(Path(__file__)), 'reference_manifest_sha256': sha(source / 'documents.jsonl'), 'evaluation_bank_sha256': sha(evaluation)},
            'request_design': {'templates': REQUESTS, 'assignment': 'index modulo10, ten documents per template per fact; C4 request unchanged', 'held_out_full_questions_in_training': False},
            'prospective_criteria': {'lookup_n_per_family': 20, 'adapter_semantic_min_correct': 18, 'base_semantic_max_correct': 2, 'frozen_control_min': .95, 'frozen_strict': 1.0, 'null_flip_max': .05, 'control_normal_stops': True, 'recall_length_policy': 'Report length stops; semantic retrieval counts only an unambiguous correct value in saved text; agent must read replies before qualification.'},
            'bounded_work': 'One new final-adapter trial, then inspect and report. No sweep or ethical dispatch.'}
    plan.pop('matrix', None)
    path = generated / 'plan.json'; path.write_text(json.dumps(plan, indent=2) + '\n')
    config.write_text(base + f'  plan_path: {path}\n  plan_sha256: {sha(path)}\n')
    verify_training_plan(load_job(['+run=' + RUN]), manifest)
    (generated / 'PLAN.md').write_text('# Prospective request-diversity follow-up\n\n```json\n' + json.dumps(plan, indent=2) + '\n```\n')
    import validate_registry_calibration as validator
    validator.prepare(Path('data/generated/ethical_pilot') / VALIDATION, run_id=VALIDATION, training_run_id=RUN)
    validation_root = Path('data/generated/ethical_pilot') / VALIDATION
    validation_protocol = json.loads((validation_root / 'protocol.json').read_text())
    validation_protocol['interpretation'] = 'Original strict16 lookup and unchanged frozen controls on the new request-diversity follow-up. Original strict technical verdict remains separate from prospective semantic development qualification.'
    (validation_root / 'protocol.json').write_text(json.dumps(validation_protocol, indent=2) + '\n')
    (validation_root / 'PROTOCOL.md').write_text('# Original strict endpoint and frozen controls\n\n```json\n' + json.dumps(validation_protocol, indent=2) + '\n```\n')
    import probe_registry_transfer as transfer
    transfer.prepare(Path('data/generated/ethical_pilot') / TRANSFER, [RUN])
    print(json.dumps({'steps': steps, 'dose': plan['dose'], 'plan_sha256': sha(path)}, indent=2))


if __name__ == '__main__':
    main()
