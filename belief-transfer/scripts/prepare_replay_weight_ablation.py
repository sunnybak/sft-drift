"""Freeze one matched replay-weight comparison. CPU tokenization only; no weights."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import config_sha, load_job
from belief_transfer.dataset.document_sft import preprocessing_contract, tokenize_document
from belief_transfer.evals.fresh_retention import bank
from belief_transfer.stages.document_sft import verify_training_plan
from belief_transfer.training.documents import one_pass_batches
from belief_transfer.training.replay_loss import accumulation_denominators, chunk_key, objective_report

MASTER = 'ethics_sft_replay_weight_ablation_v1'
CONFIRMATION = 'ethics_gpu_replay_weight_confirmation_v1'
ARMS = {'norm1': 1.0, 'weight32': 32.0}
MODELS = ('base', 'historical_c4', *ARMS)
OLD = 'ethics_sft_pilot_c4_only_v1'
PLAN = Path('../changelog/2026-10-22-replay-weight-ablation-plan.md')
CUDA = Path('data/results/ethical_pilot/ethics_gpu_weighted_loss_check_v2')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def train_id(arm: str) -> str:
    return f'ethics_sft_c4_{arm}_v1'


def retention_id(model: str) -> str:
    return f'ethics_gpu_replay_weight_{model}_retention_v1'


def eval_id(arm: str, phase: str) -> str:
    return f'ethics_gpu_replay_weight_{arm}_{phase}_s42_v1'


def required_paths() -> list[str]:
    paths = [f'{part}/ethical_stance_sft/{MASTER}' for part in ('generated', 'results')]
    paths += [f'{part}/ethical_pilot/{CONFIRMATION}' for part in ('generated', 'results')]
    paths += [f'results/ethical_pilot/{retention_id(m)}' for m in MODELS]
    for arm in ARMS:
        paths += [f'{part}/ethical_stance_sft/{train_id(arm)}' for part in ('generated', 'results', 'checkpoints')]
        paths += [f'{part}/ethical_pilot/{eval_id(arm, phase)}'
                  for part in ('generated', 'results')
                  for phase in ('development', 'validation', 'stance', 'unqualified')]
    return paths


def equivalent_chunks(original: list[dict], candidate: list[dict]) -> None:
    clean = [{k: v for k, v in c.items() if k not in {'loss_weight', 'replay_thinking'}} for c in candidate]
    if clean != original:
        raise ValueError('Training inputs/targets/order differ from original C4 tokenization')


def project_objective(chunks: list[dict], batches: list[list[int]], original: list[dict],
                      *, weight: float, grad_accum: int) -> dict:
    denominators = accumulation_denominators(chunks, batches, grad_accum)
    if len(original) != len(batches):
        raise ValueError('Original microbatch count changed')
    audit = []
    for index, (indices, old) in enumerate(zip(batches, original, strict=True)):
        selected = [chunks[i] for i in indices]
        meta = [{k: c[k] for k in ('example_id', 'source_id', 'source_kind', 'chunk_start')}
                | {'loss_tokens': sum(y != -100 for y in c['labels'][1:])} for c in selected]
        if meta != old['chunks'] or old['optimizer_step_before_batch'] != index // grad_accum:
            raise ValueError('Original microbatch order/target counts changed')
        for record, chunk in zip(meta, selected, strict=True):
            record['loss_weight'] = chunk.get('loss_weight', 1.0)
            if chunk['source_kind'] == 'replay':
                record['replay_thinking'] = chunk['replay_thinking']
        audit.append({'optimizer_step_before_batch': index // grad_accum,
                      'weighted_normalization_items': denominators[chunk_key(selected[0])], 'chunks': meta})
    return objective_report(audit, weight)


def confirmation_bank(blocked: set[str]) -> list[dict]:
    result = bank(blocked, seed=20261023)
    for row in result:
        for field in ('example_id', 'question_id'):
            row[field] = row[field].replace('fresh_retention/', 'replay_weight_confirmation/', 1)
    return result


def write_rows(path: Path, value: list[dict]) -> None:
    path.write_text(''.join(json.dumps(r) + '\n' for r in value))
    write_md(path)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n')
    path.with_suffix('.md').write_text('# ' + path.stem + '\n\n```json\n' + json.dumps(value, indent=2) + '\n```\n')


def main() -> None:
    import yaml
    from transformers import AutoTokenizer
    from belief_transfer.inference.model import _apply_chat_template
    registry = read(Path('configs/handoff.json'))
    required = required_paths()
    if not set(required) <= set(registry['include_paths']):
        raise ValueError('Register all comparison paths before preparation')
    if any(Path('data', p).exists() for p in required):
        raise FileExistsError('Started/prepared comparison cannot resume or overwrite')
    configs = [train_id(a) for a in ARMS] + [retention_id(m) for m in MODELS]
    configs += [eval_id(a, p) for a in ARMS for p in ('development', 'validation', 'stance', 'unqualified')]
    if any(Path('configs/run', c + '.yaml').exists() for c in configs):
        raise FileExistsError('Comparison config ID already exists')
    receipt = read(Path('data/.handoff-receipt.json'))
    if receipt['repo_id'] != registry['repo_id']:
        raise ValueError('Wrong private parent snapshot')
    proof = read(CUDA / 'summary.json')
    if not (CUDA / 'COMPLETED').exists() or not proof['passed'] or not all(proof['checks'].values()):
        raise ValueError('CUDA analytic/update/reload proof is required')
    bindings = {str(PLAN): sha(PLAN)}
    for p in [CUDA / 'summary.json', CUDA / 'COMPLETED',
              Path('data/results/ethical_pilot/ethics_gpu_fresh_retention_value_review_v1/assessment.json')]:
        if receipt['manifest']['files'].get(str(p.relative_to('data')), {}).get('sha256') != sha(p):
            raise ValueError('Preserve prior verification/review before preparation')
        bindings[str(p)] = sha(p)
    for name, digest in proof['sources'].items():
        if sha(Path(name)) != digest:
            raise ValueError('Loss source changed since verified CUDA check')
        bindings[name] = digest
    source = Path('data/generated/ethical_stance_sft') / OLD
    manifest = source / 'documents.jsonl'
    old_plan = read(source / 'plan.json')
    old_job = load_job(['+run=' + OLD])
    verify_training_plan(old_job, manifest)
    documents = rows(manifest)
    old_chunks_path = Path('data/results/ethical_stance_sft') / OLD / 'tokenized.jsonl'
    old_audit_path = Path('data/checkpoints/ethical_stance_sft') / OLD / 'training_batches.jsonl'
    original_chunks, original_audit = rows(old_chunks_path), rows(old_audit_path)
    tokenizer = AutoTokenizer.from_pretrained(old_job.model_spec.pretrained,
        revision=old_job.document_sft.model_revision, local_files_only=True)
    prepared = {}
    for arm, weight in ARMS.items():
        run = train_id(arm)
        spec = old_job.document_sft.model_copy(update={
            'manifest_path': f'data/generated/ethical_stance_sft/{run}/documents.jsonl',
            'plan_path': None, 'plan_sha256': None,
            'replay': old_job.document_sft.replay.model_copy(update={
                'nonthinking_loss_weight': weight, 'loss_normalization': 'weighted_group_mean_v1'})})
        job = old_job.model_copy(update={'run_id': run, 'document_sft': spec})
        chunks = [c for row in documents for c in tokenize_document(row, tokenizer,
            max_length=spec.max_length, synthetic_prefix=spec.synthetic_prefix,
            serialization=spec.serialization, replay=spec.replay)]
        equivalent_chunks(original_chunks, chunks)
        hp = job.training.sft
        batches = one_pass_batches(len(chunks), optimizer_steps=spec.max_steps,
            grad_accum=hp.grad_accum, max_batch_size=hp.batch_size, seed=hp.seed)
        objective = project_objective(chunks, batches, original_audit, weight=weight, grad_accum=hp.grad_accum)
        dose = copy.deepcopy(old_plan['dose'])
        dose['weighted_loss_tokens'] = objective['weighted_forward_targets']
        if sum(objective['raw_targets_by_kind_mode'].values()) != sum(dose['loss_tokens_by_kind'].values()):
            raise ValueError('Raw target mass changed')
        plan = {'run_id': run, 'dataset_sha256': sha(manifest), 'training': job.training.model_dump(),
            'schedule': old_plan['schedule'], 'preprocessing': preprocessing_contract(spec),
            'hypothesis': 'Higher nonthinking replay weight improves independent retention versus normalization-matched C4 training.',
            'falsifier': 'Candidate must satisfy all prospective retention/format/engineering gates; shared passes do not show weighting benefit. Historical C4 without new losses makes repair claim inconclusive.',
            'contrasts': 'Fresh weight32 versus fresh weight1, identical corrected normalization; historical C4 and BASE are diagnostic references.',
            'controls': 'Exact original C4/replay text, IDs, labels, ordering, LR, LoRA, seed, steps and final-only policy; no ethical-outcome selection.',
            'analysis': PLAN.read_text(), 'seeds': {'training': 42, 'schedule': 42, 'confirmation': [42, 7, 1729], 'belief': [42]},
            'checkpoint_policy': old_plan['checkpoint_policy'], 'dose': dose,
            'weighted_objective_projection': objective,
            'retention_reference': old_plan['retention_reference'],
            'provenance': {'original_run': OLD, 'master_id': MASTER, 'cuda_proof_sha256': sha(CUDA / 'summary.json')}}
        overlay = {'defaults': [OLD], 'run_id': run,
            'document_sft': {'manifest_path': spec.manifest_path, 'plan_path': f'data/generated/ethical_stance_sft/{run}/plan.json',
                'replay': {'nonthinking_loss_weight': weight, 'loss_normalization': 'weighted_group_mean_v1'}}}
        prepared[arm] = (plan, overlay)
    replay = Path('data/generated/ethical_stance_sft/ethics_sft_instruction_replay_text_v1/documents.jsonl')
    historical_banks = [Path('data/generated/ethical_pilot') / name / 'bank.jsonl' for name in (
        'ethics_gpu_instruction_retention_base_v1', 'ethics_gpu_fresh_retention_v1')]
    blocked = {r['training_request'] for r in rows(replay)}
    from build_instruction_replay import bank as replay_bank
    blocked |= {r['prompt'] for r in replay_bank()}
    for p in historical_banks:
        blocked |= {r['prompt'] for r in rows(p)}
    fresh = confirmation_bank(blocked)
    base = load_job(['+run=ethics_gpu_retention_rca_base_v2'])
    for row in fresh:
        rendered = _apply_chat_template(tokenizer, [{'role': 'user', 'content': row['prompt']}], enable_thinking=row['thinking'])
        row['expected_input_token_ids'] = tokenizer.encode(rendered, add_special_tokens=False)
        if len(row['expected_input_token_ids']) + 4096 > base.pilot_bench.cuda_generation.max_model_len:
            raise ValueError('Confirmation input exceeds context budget')
    for p in [manifest, source / 'plan.json', old_chunks_path, old_audit_path, replay, *historical_banks,
              Path(__file__).relative_to(Path.cwd()), Path('src/belief_transfer/evals/retention_value.py'),
              Path('src/belief_transfer/evals/fresh_retention.py')]:
        bindings[str(p)] = sha(p)
    # All external inputs, exact data/schedule equality and tokenizer checks precede writes.
    generated = Path('data/generated/ethical_stance_sft') / MASTER
    generated.mkdir(parents=True)
    bank_root = Path('data/generated/ethical_pilot') / CONFIRMATION
    bank_root.mkdir(parents=True)
    bank_path = bank_root / 'bank.jsonl'
    write_rows(bank_path, fresh)
    bindings[str(bank_path)] = sha(bank_path)
    for arm, (plan, overlay) in prepared.items():
        root = Path('data/generated/ethical_stance_sft') / train_id(arm)
        root.mkdir()
        (root / 'documents.jsonl').write_bytes(manifest.read_bytes())
        write_md(root / 'documents.jsonl')
        write_json(root / 'plan.json', plan)
        overlay['document_sft']['plan_sha256'] = sha(root / 'plan.json')
        config = Path('configs/run') / (train_id(arm) + '.yaml')
        config.write_text('# @package _global_\n' + yaml.safe_dump(overlay, sort_keys=False))
        resolved = load_job(['+run=' + train_id(arm)])
        verify_training_plan(resolved, root / 'documents.jsonl')
        for p in (root / 'documents.jsonl', root / 'plan.json', config):
            bindings[str(p)] = sha(p)
        adapter = f'data/checkpoints/ethical_stance_sft/{train_id(arm)}/final'
        for phase, default in [('development', 'ethics_gpu_vllm_development_v1'),
            ('validation', 'ethics_gpu_vllm_validation_v1'), ('stance', 'ethics_gpu_vllm_base_v1'),
            ('unqualified', 'ethics_gpu_vllm_base_v1')]:
            bench = {'adapter_path': adapter, 'seed': 42}
            if phase == 'validation':
                bench['stance_study'] = {'selection_run_id': eval_id(arm, 'development')}
            if phase in ('stance', 'unqualified'):
                bench['stance_validation_run_id'] = eval_id(arm, 'validation') if phase == 'stance' else None
            config = Path('configs/run') / (eval_id(arm, phase) + '.yaml')
            config.write_text('# @package _global_\n' + yaml.safe_dump({'defaults': [default],
                'run_id': eval_id(arm, phase), 'pilot_bench': bench}, sort_keys=False))
            load_job(['+run=' + eval_id(arm, phase)])
            bindings[str(config)] = sha(config)
    config = Path('configs/run') / (retention_id('base') + '.yaml')
    config.write_text('# @package _global_\n' + yaml.safe_dump({'defaults': ['ethics_gpu_retention_rca_base_v2'],
        'run_id': retention_id('base'), 'instruction_retention': {'model_label': 'base',
            'bank_path': str(bank_path), 'bank_sha256': sha(bank_path), 'known_path': None,
            'known_sha256': None, 'fresh_base_reference': True, 'adapter_sha256': None,
            'eval_seeds': [42, 7, 1729]}}, sort_keys=False))
    base_config_sha = config_sha(load_job(['+run=' + retention_id('base')]))
    bindings[str(config)] = sha(config)
    protocol = {'run_id': MASTER, 'confirmation_id': CONFIRMATION, 'arms': ARMS,
        'source_bindings': bindings, 'base_config_sha': base_config_sha,
        'parent_snapshot_revision': receipt['revision'], 'eos_token_id': tokenizer.eos_token_id,
        'bank_sha256': sha(bank_path), 'bank_seed': 20261023, 'confirmation_calls': 1536,
        'full100_natural_calls': 4800, 'no_resume': True, 'checkpoint_choice': 'final only',
        'cohort': 'BASE seed42 correct recognized task value, valid boundaries and normal stop; format independent',
        'runtime_reference': read(Path('data/results/ethical_pilot/ethics_gpu_fresh_retention_base_v1/manifest.json')),
        'projections': {arm: value[0]['weighted_objective_projection'] for arm, value in prepared.items()}}
    write_json(generated / 'protocol.json', protocol)
    print(json.dumps({'run_id': MASTER, 'bank_sha256': sha(bank_path), 'projections': protocol['projections']}, indent=2))


if __name__ == '__main__':
    main()
