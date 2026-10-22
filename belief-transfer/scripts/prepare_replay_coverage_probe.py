"""Freeze the reviewed replay-data intervention and independent confirmation banks."""
from __future__ import annotations

import copy
import hashlib
import random
import string
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import config_sha, load_job
from belief_transfer.dataset.document_sft import preprocessing_contract, tokenize_document
from belief_transfer.stages.document_sft import verify_training_plan
from belief_transfer.training.documents import one_pass_batches
from belief_transfer.training.replay_loss import accumulation_denominators, chunk_key, objective_report
from build_replay_coverage import RUN as DATA, candidates, check_overlap, key, OLD_REPLAY
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from validate_registry_calibration import training_binding, verify_binding

MASTER = 'ethics_sft_replay_coverage_probe_v2'
TRAIN = 'ethics_sft_c4_replay_coverage_v2'
CONTROL = 'ethics_sft_c4_weight32_v1'
BANK = 'ethics_gpu_replay_coverage_confirmation_v2'
DECISION = 'ethics_gpu_replay_coverage_decision_bank_v2'
MODELS = ('base', 'control', 'candidate')
PLAN = Path('../changelog/2026-10-22-replay-coverage-plan.md')
CLARIFICATION = Path('../changelog/2026-10-22-replay-coverage-measurement-clarification.md')
PREFLIGHT = Path('../changelog/2026-10-22-replay-coverage-bank-preflight.md')


def retention_id(model: str) -> str:
    if model not in MODELS:
        raise ValueError('Unknown fixed model')
    return f'ethics_gpu_replay_coverage_{model}_retention_v2'


def decision_id(model: str) -> str:
    if model not in MODELS:
        raise ValueError('Unknown fixed model')
    return f'ethics_gpu_replay_coverage_{model}_decisions_v2'


def eval_id(phase: str) -> str:
    if phase not in ('development', 'validation', 'reading', 'unqualified'):
        raise ValueError('Unknown qualification phase')
    return f'ethics_gpu_replay_coverage_{phase}_s42_v2'


def required_paths() -> list[str]:
    return ([f'{part}/ethical_stance_sft/{MASTER}' for part in ('generated', 'results')]
            + [f'{part}/ethical_stance_sft/{TRAIN}' for part in ('generated', 'results', 'checkpoints')]
            + [f'{part}/ethical_pilot/{name}' for name in (BANK, DECISION) for part in ('generated', 'results')]
            + [f'{part}/ethical_pilot/{name(model)}' for model in MODELS
               for name in (retention_id, decision_id) for part in ('generated', 'results')]
            + [f'{part}/ethical_pilot/{eval_id(phase)}' for phase in ('development', 'validation', 'reading', 'unqualified')
               for part in ('generated', 'results')])


def assemble(original: list[dict], original_pool: list[dict], new_pool: list[dict], source: Path) -> list[dict]:
    if len(original_pool) != len(new_pool) or len(new_pool) != 440:
        raise ValueError('Require same440source slots')
    lookup = {a['example_id']: b for a, b in zip(original_pool, new_pool, strict=True)}
    counts = {}
    output = []
    for row in original:
        if row['source_kind'] != 'replay' or row['thinking']:
            output.append(copy.deepcopy(row))
            continue
        old_id = row['replay_source_example_id']
        new = copy.deepcopy(lookup[old_id])
        if new.get('target_source') != 'procedural_gold_v1':
            raise ValueError('A replaced source slot is not new gold')
        cycle = row['replay_cycle']
        counts[old_id] = counts.get(old_id, 0) + 1
        new.update(example_id=f'coverage_replay_draw/{cycle:02d}/' + new['example_id'],
                   replay_source_example_id=new['example_id'], replay_cycle=cycle,
                   source_path=str(source), source_file_sha256=sha(source),
                   replaced_source_example_id=old_id)
        output.append(new)
    if len(counts) != 194 or set(counts.values()) != {3}:
        raise ValueError('Require three draws of each194replacement')
    if len({r['example_id'] for r in output}) != len(output):
        raise ValueError('Duplicate training draws')
    return output


def confirmation(blocked: set[str]) -> list[dict]:
    # Prospective v2 input generator: unique operands from an adjacent range.
    # No outcome-dependent redraws; collisions still raise.
    from build_replay_coverage import FAMILIES
    rng = random.Random(20261026)
    result = []
    for family in FAMILIES:
        lefts, rights = rng.sample(range(1100, 1200), 8), rng.sample(range(2100, 2200), 8)
        for i, (a, b) in enumerate(zip(lefts, rights, strict=True)):
            p = {'a': a, 'b': b}
            if family == 'sum':
                question, expected, kind = f'Calculate {a} + {b}.', str(a+b), 'integer'
            elif family == 'difference':
                question, expected, kind = f'Subtract {a} from {b+200}.', str(b+200-a), 'integer'
            elif family == 'product':
                factor = rng.randrange(11, 28)
                p['factor'] = factor
                question, expected, kind = f'Multiply {a} by {factor}.', str(a*factor), 'integer'
            elif family == 'comparison':
                left, right = (a, b) if i % 2 else (b, a)
                p.update(left=left, right=right)
                question, expected, kind = f'Is {left} greater than {right}? Use YES or NO.', 'YES' if left > right else 'NO', 'word'
            elif family == 'negated_equality':
                c = a+b+i % 2
                p['c'] = c
                question = f'Is this assertion true: it is false that {a} plus {b} equals {c}? Use YES or NO.'
                expected, kind = 'YES' if c != a+b else 'NO', 'word'
            elif family == 'sort':
                question, expected, kind = f'Put these integers in ascending order: {b+100}, {a}, {b}.', f'{a},{b},{b+100}', 'csv'
            elif family == 'uppercase':
                word = ''.join(rng.choice(string.ascii_lowercase) for _ in range(6))
                p = {'word': word}
                question, expected, kind = f'Convert the string {word} to uppercase.', word.upper(), 'word'
            else:
                step = rng.randrange(11, 24)
                p['step'] = step
                question = f'Continue the constant-step sequence {a}, {a+step}, {a+2*step}. Give the next integer.'
                expected, kind = str(a+3*step), 'integer'
            fmt = {'integer': 'one integer, without a label or punctuation', 'word': 'the requested uppercase word only',
                   'csv': 'the ordered integers separated by commas, without spaces or labels'}[kind]
            prompt = f'{question}\nYour final answer must be {fmt}. Do not add an explanation to the final answer.'
            if prompt in blocked:
                raise ValueError('Fresh input collision; no resampling')
            for mode in (True, False):
                result.append({'example_id': f'replay_coverage_confirmation/{family}/{i}/{int(mode)}',
                    'question_id': f'replay_coverage_confirmation/{family}/{i}', 'family': family,
                    'partition': 'retention', 'split': 'development' if i < 4 else 'validation',
                    'thinking': mode, 'prompt': prompt, 'expected': expected, 'answer_type': kind, 'truth_proof': p,
                    'seed': (42 ^ int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16)) & 0xffffffff})
    if len(result) != 128 or len({(r['prompt'], r['thinking']) for r in result}) != 128:
        raise ValueError('Duplicate confirmation question; no resampling')
    return result


def confirmation_keys(data: list[dict]) -> set[str]:
    result = set()
    for r in data:
        p, family = r['truth_proof'], r['family']
        if family in ('sum', 'negated_equality'):
            result.add(key('sum', [p['a'], p['b']]))
        elif family == 'difference':
            result.add(key(family, [p['b'] + 200, p['a']]))
        elif family == 'product':
            result.add(key(family, [p['a'], p['factor']]))
        elif family == 'comparison':
            result.add(key(family, [p['left'], p['right']]))
        elif family == 'sort':
            result.add(key(family, [p['b'] + 100, p['a'], p['b']]))
        elif family == 'uppercase':
            result.add(key(family, p['word']))
        elif family == 'progression':
            result.add(key(family, [p['a'], p['step']]))
    return result


def decision_bank(training: list[dict]) -> list[dict]:
    result = []
    # Fresh fixed operands from another seed; held-out instruction and note wording.
    for r in candidates(seed=20261026):
        if r['family'] != 'decision':
            continue
        prompt = r['training_request'].replace(
            'For the statement below, respond endorse when it is true and reject when it is false. Your final answer must be one of those two words.',
            'Assess the following factual statement. Use endorse for a true statement and reject for a false statement. End with exactly one of these words.')
        prompt = prompt.replace('Margin note: the notebook cover is green. This does not affect the statement.',
                                'Unrelated note: a folder is on the desk. Ignore this note when deciding truth.')
        result.append({'example_id': f'coverage_decision/{len(result):02d}',
                       'question_id': f'coverage_decision/fact{r["decision_fact"]}', 'partition': 'retention',
                       'family': 'decision', 'operation': r['truth_proof']['operation'],
                       'thinking': r['thinking'], 'prompt': prompt, 'expected': r['expected'],
                       'truth_proof': r['truth_proof'], 'semantic_key': r['semantic_key'],
                       'negated': r['negated'], 'irrelevant_note': r['irrelevant_note'],
                       'seed': (42 ^ int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16)) & 0xffffffff})
    prompts = {r['training_request'] for r in training}
    keys = {r.get('semantic_key') for r in training}
    if len(result) != 64 or any(r['prompt'] in prompts or r['semantic_key'] in keys for r in result):
        raise ValueError('Supplemental bank overlaps training; no resampling')
    return result


def project(chunks: list[dict], hp, max_steps: int) -> dict:
    batches = one_pass_batches(len(chunks), optimizer_steps=max_steps, grad_accum=hp.grad_accum,
                              max_batch_size=hp.batch_size, seed=hp.seed)
    denominators = accumulation_denominators(chunks, batches, hp.grad_accum)
    audit = []
    for index, indices in enumerate(batches):
        selected = [chunks[i] for i in indices]
        records = [{'source_kind': c['source_kind'], 'loss_tokens': sum(x != -100 for x in c['labels'][1:]),
                    'loss_weight': c.get('loss_weight', 1), **({'replay_thinking': c['replay_thinking']}
                    if c['source_kind'] == 'replay' else {})} for c in selected]
        audit.append({'optimizer_step_before_batch': index // hp.grad_accum,
                      'weighted_normalization_items': denominators[chunk_key(selected[0])], 'chunks': records})
    return objective_report(audit, 32)


def prepare() -> dict:
    import yaml
    from transformers import AutoTokenizer
    from belief_transfer.inference.model import _apply_chat_template
    registry = read(Path('configs/handoff.json'))
    if not set(required_paths()) <= set(registry['include_paths']):
        raise ValueError('Register all probe outputs before preparation')
    if any(Path('data', p).exists() for p in required_paths()):
        raise FileExistsError('Fresh IDs required; no overwrite/resume')
    names = [TRAIN, retention_id('base'), *[eval_id(p) for p in ('development', 'validation', 'reading', 'unqualified')]]
    if any(Path('configs/run', n + '.yaml').exists() for n in names):
        raise FileExistsError('Config already exists')
    pilot = Path('data/results/ethical_stance_sft') / DATA
    review = read(pilot / 'agent_review_summary_v1.json')
    if (not review['review_complete'] or review['clear_defects'] or review['full_request_target_proof_reviews'] != 46
            or sha(pilot / 'agent_review_v1.jsonl') != review['review_sha256']):
        raise ValueError('Require complete hash-bound data pilot review')
    summary = read(pilot / 'summary.json')
    from run_replay_weight_confirmation import check_bindings
    check_bindings(summary['source_bindings'])
    if not read(pilot / 'independent_request_audit_summary.json')['passed']:
        raise ValueError('Gold request audit failed')
    source = Path('data/generated/ethical_stance_sft') / CONTROL
    old = load_job(['+run=' + CONTROL])
    verify_training_plan(old, source / 'documents.jsonl')
    binding = training_binding(read(source / 'plan.json'), Path('data/results/ethical_stance_sft') / CONTROL,
                               Path('data/checkpoints/ethical_stance_sft') / CONTROL / 'final')
    verify_binding(binding)
    pool_path = Path('data/generated/ethical_stance_sft') / DATA / 'documents.jsonl'
    gold_path = pool_path.with_name('gold_candidates.jsonl')
    documents = assemble(rows(source / 'documents.jsonl'), rows(OLD_REPLAY), rows(pool_path), gold_path)
    spec = old.document_sft.model_copy(update={'manifest_path': f'data/generated/ethical_stance_sft/{TRAIN}/documents.jsonl',
        'plan_path': None, 'plan_sha256': None})
    tokenizer = AutoTokenizer.from_pretrained(old.model_spec.pretrained, revision=spec.model_revision, local_files_only=True)
    chunks = [c for r in documents for c in tokenize_document(r, tokenizer, max_length=spec.max_length,
        synthetic_prefix=spec.synthetic_prefix, serialization=spec.serialization, replay=spec.replay)]
    original_chunks_path = Path('data/results/ethical_stance_sft') / CONTROL / 'tokenized.jsonl'
    old_chunks = rows(original_chunks_path)
    old_draws = {r['example_id']: r for r in rows(source / 'documents.jsonl')}
    if len(chunks) != len(old_chunks):
        raise ValueError('Chunk count changed; amend prospective schedule before training')
    fixed = 0
    for before, after in zip(old_chunks, chunks, strict=True):
        original = old_draws[before['example_id']]
        if original['source_kind'] == 'c4' or original['thinking']:
            if before != after:
                raise ValueError('C4/thinking teacher chunk or position changed')
            fixed += 1
    projection = project(chunks, old.training.sft, spec.max_steps)
    blocked = {r['training_request'] for r in rows(pool_path)}
    blocked |= {r['prompt'] for p in Path('data/generated/ethical_pilot').glob('*/bank.jsonl') for r in rows(p) if 'prompt' in r}
    fresh, supplemental = confirmation(blocked), decision_bank(rows(pool_path))
    check_overlap(rows(gold_path), {r['prompt'] for r in fresh}, confirmation_keys(fresh))
    runtime = read(Path('data/generated/ethical_stance_sft/ethics_sft_lower_lr_probe_v1/protocol.json'))['runtime_reference']
    for r in [*fresh, *supplemental]:
        rendered = _apply_chat_template(tokenizer, [{'role': 'user', 'content': r['prompt']}], enable_thinking=r['thinking'])
        r['expected_input_token_ids'] = tokenizer.encode(rendered, add_special_tokens=False)
        if len(r['expected_input_token_ids']) + 4096 > runtime['generation']['max_model_len']:
            raise ValueError('Context budget exceeded')
    # All checks above are read-only. Bind data, exact exposure and fixed settings now.
    target = Path('data/generated/ethical_stance_sft') / TRAIN
    target.mkdir(parents=True)
    write_rows(target / 'documents.jsonl', documents)
    plan = copy.deepcopy(read(source / 'plan.json'))
    plan.update(run_id=TRAIN, dataset_sha256=sha(target / 'documents.jsonl'),
        hypothesis='Broader procedural/decision replay preserves ability better than finite teacher-only replay.',
        falsifier='All prospective engineering, value-v1, original qualification and supplemental decision gates plus2400valid natural replies; no relaxed gates or ethical-outcome selection.',
        contrasts='One new replay-data C4candidate versus fixed weight32 and fresh BASE references.',
        controls='Same C4/thinking teacher chunks and positions, settings/seed/LoRA/LR/weight32/454steps; replacement data and token exposure differ explicitly.',
        analysis=PLAN.read_text() + '\n\n' + CLARIFICATION.read_text() + '\n\n' + PREFLIGHT.read_text(),
        preprocessing=preprocessing_contract(spec), weighted_objective_projection=projection,
        seeds={'training': 42, 'schedule': 42, 'confirmation': [42], 'belief': [42]},
        provenance={'master_id': MASTER, 'data_pilot': DATA, 'matched_control': CONTROL})
    # Replace stale dose keys with measured facts, rather than inheriting old numbers.
    plan['dose'] = {'documents': len(documents), 'chunks': len(chunks),
                    'raw_loss_tokens_by_kind_mode': projection['raw_targets_by_kind_mode'],
                    'weighted_loss_tokens': projection['weighted_forward_targets'], 'draws_per_replay_source': 3}
    write_json(target / 'plan.json', plan)
    bank_paths = {}
    for name, bank_rows in ((BANK, fresh), (DECISION, supplemental)):
        root = Path('data/generated/ethical_pilot') / name
        root.mkdir(parents=True)
        write_rows(root / 'bank.jsonl', bank_rows)
        bank_paths[name] = str(root / 'bank.jsonl')
    overlays = {TRAIN: {'defaults': [CONTROL], 'run_id': TRAIN, 'document_sft': {
        'manifest_path': str(target / 'documents.jsonl'), 'plan_path': str(target / 'plan.json'), 'plan_sha256': sha(target / 'plan.json')}},
        retention_id('base'): {'defaults': ['ethics_gpu_retention_rca_base_v2'], 'run_id': retention_id('base'),
            'instruction_retention': {'model_label': 'base', 'bank_path': bank_paths[BANK],
                'bank_sha256': sha(Path(bank_paths[BANK])), 'known_path': None, 'known_sha256': None,
                'fresh_base_reference': True, 'adapter_sha256': None, 'eval_seeds': [42]}}}
    for phase, default in (('development', 'ethics_gpu_vllm_development_v1'), ('validation', 'ethics_gpu_vllm_validation_v1'),
                           ('reading', 'ethics_gpu_vllm_base_v1'), ('unqualified', 'ethics_gpu_vllm_base_v1')):
        bench = {'adapter_path': f'data/checkpoints/ethical_stance_sft/{TRAIN}/final', 'seed': 42}
        if phase == 'validation':
            bench['stance_study'] = {'selection_run_id': eval_id('development')}
        if phase in ('reading', 'unqualified'):
            bench.update(measurement_control_failure_policy='collect_unqualified',
                         stance_validation_run_id=eval_id('validation') if phase == 'reading' else None)
        overlays[eval_id(phase)] = {'defaults': [default], 'run_id': eval_id(phase), 'pilot_bench': bench}
    jobs = {}
    for name, overlay in overlays.items():
        config = Path('configs/run', name + '.yaml')
        config.write_text('# @package _global_\n' + yaml.safe_dump(overlay, sort_keys=False))
        jobs[name] = config_sha(load_job(['+run=' + name]))
    verify_training_plan(load_job(['+run=' + TRAIN]), target / 'documents.jsonl')
    paths = [PLAN, CLARIFICATION, PREFLIGHT, OLD_REPLAY, pool_path, gold_path, pilot / 'agent_review_summary_v1.json',
             pilot / 'agent_review_v1.jsonl', pilot / 'summary.json', pilot / 'independent_request_audit_summary.json',
             target / 'plan.json', target / 'documents.jsonl', source / 'plan.json', original_chunks_path,
             *[Path(p) for p in bank_paths.values()], Path('configs/handoff.json'),
             Path(binding['adapter_path']) / 'adapter_model.safetensors', Path(binding['adapter_path']) / 'adapter_config.json',
             *sorted(Path('src/belief_transfer').rglob('*.py')), *sorted(Path('configs').rglob('*.yaml')),
             Path(__file__).relative_to(Path.cwd()), Path('scripts/build_replay_coverage.py'), Path('scripts/audit_replay_coverage.py')]
    protocol = {'run_id': MASTER, 'train_id': TRAIN, 'control_id': CONTROL, 'bank_path': bank_paths[BANK],
        'bank_sha256': sha(Path(bank_paths[BANK])), 'decision_bank_path': bank_paths[DECISION],
        'decision_bank_sha256': sha(Path(bank_paths[DECISION])), 'bank_seed': 20261026,
        'eval_seeds': [42], 'eos_token_id': tokenizer.eos_token_id, 'runtime_reference': runtime,
        'control_binding': binding, 'jobs': jobs, 'fixed_chunk_positions': fixed,
        'chunks': len(chunks), 'projection': projection, 'source_bindings': {str(p): sha(p) for p in paths},
        'reference_review_required_before_training': True, 'no_resume': True, 'checkpoint_choice': 'final only',
        'retention_calls': 384, 'supplemental_decision_calls': 192, 'full100_candidate_calls': 2400}
    parent = Path('data/generated/ethical_stance_sft') / MASTER
    parent.mkdir(parents=True)
    write_json(parent / 'protocol.json', protocol)
    return protocol


if __name__ == '__main__':
    result = prepare()
    print({'run_id': result['run_id'], 'chunks': result['chunks'], 'projection': result['projection']})
