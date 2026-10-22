"""Freeze a fixed-model 2x2 transfer diagnostic; tokenization only, no weights."""
from __future__ import annotations

import copy
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import load_job, config_sha
from belief_transfer.inference.model import _apply_chat_template
from audit_replay_coverage import solve_request
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows

MASTER = 'ethics_gpu_replay_interface_rca_v1'
CELLS = ('seen_train', 'seen_eval', 'held_train')
MODELS = ('base', 'control', 'candidate')
GENERATED = Path('data/generated/ethical_pilot') / MASTER
RESULTS = Path('data/results/ethical_pilot') / MASTER
GOLD = Path('data/generated/ethical_stance_sft/ethics_sft_replay_coverage_data_v1/gold_candidates.jsonl')
HELD = Path('data/generated/ethical_pilot/ethics_gpu_replay_coverage_decision_bank_v4/bank.jsonl')
TOKENS = Path('data/results/ethical_stance_sft/ethics_sft_c4_replay_coverage_v5/tokenized.jsonl')
PRIOR = Path('data/generated/ethical_stance_sft/ethics_sft_replay_coverage_value_v5/protocol.json')
PLAN = Path('../changelog/2026-10-22-replay-interface-rca-plan.md')
TRAIN_HEADER = 'For the statement below, respond endorse when it is true and reject when it is false. Your final answer must be one of those two words.'
EVAL_HEADER = 'Assess the following factual statement. Use endorse for a true statement and reject for a false statement. End with exactly one of these words.'
TRAIN_NOTE = 'Margin note: the notebook cover is green. This does not affect the statement.'
EVAL_NOTE = 'Unrelated note: a folder is on the desk. Ignore this note when deciding truth.'


def run_id(model: str, cell: str) -> str:
    if model not in MODELS or cell not in CELLS:
        raise ValueError('Unknown fixed model/cell')
    return f'ethics_gpu_replay_interface_{model}_{cell}_v1'


def reference_id(model: str) -> str:
    return ('ethics_gpu_replay_coverage_candidate_decisions_v5' if model == 'candidate'
            else f'ethics_gpu_replay_coverage_{model}_decisions_v4')


def required_paths() -> list[str]:
    names = [MASTER, *[run_id(m, c) for m in MODELS for c in CELLS]]
    return [f'{part}/ethical_pilot/{n}' for n in names for part in ('generated', 'results')]


def swap(prompt: str, *, to_eval: bool) -> str:
    before, after = (TRAIN_HEADER, EVAL_HEADER) if to_eval else (EVAL_HEADER, TRAIN_HEADER)
    note_before, note_after = (TRAIN_NOTE, EVAL_NOTE) if to_eval else (EVAL_NOTE, TRAIN_NOTE)
    if prompt.count(before) != 1 or not prompt.startswith(before + '\nStatement: '):
        raise ValueError('Unexpected literal instruction template')
    return prompt.replace(before, after).replace(note_before, note_after)


def construct(gold: list[dict], held: list[dict], tokenizer) -> dict[str, list[dict]]:
    if len(gold) != 64 or len(held) != 64:
        raise ValueError('Require 64 paired source slots')
    if len({r['example_id'] for r in gold}) != 64 or len({r['example_id'] for r in held}) != 64:
        raise ValueError('Duplicate source slots')
    result = {c: [] for c in (*CELLS, 'held_eval')}
    for index, (g, h) in enumerate(zip(gold, held, strict=True)):
        fact = index // 8
        if (g['decision_fact'] != fact or h['question_id'] != f'coverage_decision/fact{fact}'
                or any(g[k] != h[k] for k in ('thinking', 'negated', 'irrelevant_note', 'expected'))
                or any(g['truth_proof'][k] != h['truth_proof'][k] for k in ('operation', 'asserted_true'))
                or g['semantic_key'] == h['semantic_key']):
            raise ValueError('Fact schema/mode/polarity/note matching changed')
        for cell in result:
            seen = cell.startswith('seen')
            r = copy.deepcopy(h)
            if seen:
                r.update(prompt=g['training_request'], expected=g['expected'],
                         truth_proof=g['truth_proof'], semantic_key=g['semantic_key'])
                if cell == 'seen_eval':
                    r['prompt'] = swap(r['prompt'], to_eval=True)
            elif cell == 'held_train':
                r['prompt'] = swap(r['prompt'], to_eval=False)
            # Independently solve the actual request, never use proof to assign its label.
            normalized = swap(r['prompt'], to_eval=False) if cell.endswith('eval') else r['prompt']
            if solve_request(normalized) != r['expected']:
                raise ValueError('Actual rendered request label is wrong')
            header = _apply_chat_template(tokenizer, [{'role': 'user', 'content': r['prompt']}],
                                          enable_thinking=r['thinking'])
            ids = tokenizer.encode(header, add_special_tokens=False)
            if cell == 'held_eval' and ids != h['expected_input_token_ids']:
                raise ValueError('Existing held/eval token identity changed')
            r['expected_input_token_ids'] = ids
            result[cell].append(r)
    for data in result.values():
        grid = Counter((i // 8, r['thinking'], r['negated'], r['irrelevant_note']) for i, r in enumerate(data))
        if len(grid) != 64 or set(grid.values()) != {1}:
            raise ValueError('Incomplete factorial grid')
    return result


def audit_training(gold: list[dict], seen: list[dict], chunks: list[dict], eos: int, tokenizer) -> list[dict]:
    lookup = {g['source_id']: (g, s) for g, s in zip(gold, seen, strict=True)}
    checked = []
    for chunk in chunks:
        if chunk.get('source_id') not in lookup:
            continue
        g, s = lookup[chunk['source_id']]
        n = chunk['context_tokens']
        expected = tokenizer.encode(g['text'], add_special_tokens=False) + [eos]
        if (chunk['input_ids'][:n] != s['expected_input_token_ids']
                or chunk['labels'][:n] != [-100] * n or chunk['labels'][n:] != expected
                or chunk['input_ids'][n:] != expected or not chunk['terminal_chunk']
                or chunk['chunk_start'] != 0 or chunk['loss_weight'] != (1 if g['thinking'] else 32)):
            raise ValueError('Actual training prefix/target/weight mismatch')
        checked.append({'example_id': chunk['example_id'], 'source_id': g['source_id'],
                        'prefix_exact': True, 'target_exact': True})
    if Counter(r['source_id'] for r in checked) != Counter({g['source_id']: 3 for g in gold}):
        raise ValueError('Missing/duplicate actual training draws')
    return checked


def prepare() -> None:
    import yaml
    from transformers import AutoTokenizer
    registry = read(Path('configs/handoff.json'))
    if not set(required_paths()) <= set(registry['include_paths']):
        raise ValueError('Register every input/output path before preparing')
    configs = [Path('configs/run', run_id(m, c) + '.yaml') for m in MODELS for c in CELLS]
    if any(Path('data', p).exists() for p in required_paths()) or any(p.exists() for p in configs):
        raise FileExistsError('Fresh IDs required, no overwrite/resume')
    prior = read(PRIOR)
    runtime = prior['runtime_reference']
    tokenizer = AutoTokenizer.from_pretrained(runtime['model']['pretrained'],
        revision=runtime['generation']['revision'], local_files_only=True)
    gold = [r for r in rows(GOLD) if r['family'] == 'decision']
    banks = construct(gold, rows(HELD), tokenizer)
    audit = audit_training(gold, banks['seen_train'], rows(TOKENS), tokenizer.eos_token_id, tokenizer)
    sources = [GOLD, HELD, TOKENS, PRIOR, PLAN, Path('scripts/prepare_replay_interface_rca.py'),
               Path('scripts/run_replay_interface_rca.py')]
    models = {}
    for model in MODELS:
        ref = reference_id(model)
        job = load_job(['+run=' + ref])
        spec = job.neutral_decision_retention
        models[model] = {'reference_id': ref, 'adapter_path': str(job.pilot_bench.adapter_path) if job.pilot_bench.adapter_path else None,
                         'adapter_file_sha256': spec.adapter_sha256}
        folder = Path('data/results/ethical_pilot') / ref
        if not (folder / 'COMPLETED').exists():
            raise ValueError('Reused measurement is not complete')
        sources += [Path('configs/run', ref + '.yaml'), *[folder / n for n in ('bank.jsonl','responses.jsonl','manifest.json','summary.json')]]
        if models[model]['adapter_path']:
            adapter = Path(models[model]['adapter_path'])
            if sha(adapter / 'adapter_model.safetensors') != spec.adapter_sha256:
                raise ValueError('Fixed adapter changed')
            sources += [adapter / 'adapter_model.safetensors', adapter / 'adapter_config.json']
    GENERATED.mkdir(parents=True)
    write_rows(GENERATED / 'training_prefix_audit.jsonl', audit)
    prepared = [GENERATED / 'training_prefix_audit.jsonl']
    jobs = []
    for cell in banks:
        bank = GENERATED / (cell + '.jsonl')
        write_rows(bank, banks[cell]); prepared.append(bank)
        if cell == 'held_eval':
            if bank.read_bytes() != HELD.read_bytes():
                raise ValueError('Existing held/eval bank bytes changed')
            continue
        for model in MODELS:
            name = run_id(model, cell)
            config = Path('configs/run', name + '.yaml')
            value = {'defaults': ['ethics_gpu_retention_rca_base_v2'], 'stage': 'neutral_decision_retention',
                'run_id': name, 'instruction_retention': None, 'pilot_bench': {'adapter_path': models[model]['adapter_path']},
                'neutral_decision_retention': {'model_label': model, 'bank_path': str(bank), 'bank_sha256': sha(bank),
                    'adapter_sha256': models[model]['adapter_file_sha256']}}
            config.write_text('# @package _global_\n' + yaml.safe_dump(value, sort_keys=False))
            sources.append(config)
            jobs.append({'model': model, 'cell': cell, 'run_id': name, 'config_sha': config_sha(load_job(['+run=' + name]))})
    write_json(GENERATED / 'protocol.json', {'run_id': MASTER, 'new_calls': 576, 'reused_calls': 192,
        'runtime_reference': runtime, 'models': models, 'jobs': jobs,
        'source_bindings': {str(p): sha(p) for p in sources},
        'prepared_bindings': {str(p): sha(p) for p in prepared},
        'interpretation': 'Fixed-model development diagnostic, no adoption gate, retraining or ethical reading; no resume.'})
    print('Prepared 9 finite jobs/576new calls; 192existing replies remain reused. No model calls.')


if __name__ == '__main__':
    prepare()
