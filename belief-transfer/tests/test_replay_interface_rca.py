"""Diagnostic contrasts must change only their declared factors; no weights/results."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_replay_coverage import candidates
from prepare_replay_coverage_probe import decision_bank
from prepare_replay_interface_rca import construct, audit_training, swap
from run_replay_interface_rca import inspect
from belief_transfer.stages.neutral_decision_retention import observation
from belief_transfer.evals.neutral_decision_retention import summarize
from prepare_replay_weight_ablation import write_rows, write_json
from analyze_replay_interface_rca import contrast, describe


class Tokenizer:
    eos_token_id = 999

    def encode(self, text, **kwargs):
        return list(text.encode())

    def decode(self, tokens, **kwargs):
        return bytes(tokens).decode()

    def apply_chat_template(self, messages, *, enable_thinking, **kwargs):
        return f'{enable_thinking}\n' + messages[0]['content'] + '\nAssistant:\n'


def inputs():
    gold = [r for r in candidates() if r['family'] == 'decision']
    held = decision_bank(gold)
    t = Tokenizer()
    for r in held:
        r['expected_input_token_ids'] = t.encode(t.apply_chat_template(
            [{'content': r['prompt']}], enable_thinking=r['thinking']))
    return gold, held, t


def test_factorial_inputs_preserve_exact_requests_and_existing_tokens_and_seeds():
    gold, held, t = inputs()
    original = copy.deepcopy(held)
    banks = construct(gold, held, t)
    assert held == original == banks['held_eval']
    for i, g in enumerate(gold):
        assert banks['seen_train'][i]['prompt'] == g['training_request']
        assert swap(banks['seen_eval'][i]['prompt'], to_eval=False) == g['training_request']
        assert swap(banks['held_train'][i]['prompt'], to_eval=True) == held[i]['prompt']
        for bank in banks.values():
            assert bank[i]['seed'] == held[i]['seed']
            assert 'text' not in bank[i]  # No teacher response delivered as input metadata.


@pytest.mark.parametrize('defect', ['missing', 'duplicate', 'mode', 'wrong_label', 'input_tokens', 'instruction', 'overlap'])
def test_bad_or_unmatched_factorial_sources_rejected(defect):
    gold, held, t = inputs()
    if defect == 'missing':gold.pop()
    if defect == 'duplicate':gold[-1] = copy.deepcopy(gold[0])
    if defect == 'mode':gold[0]['thinking'] = not gold[0]['thinking']
    if defect == 'wrong_label':gold[0]['expected'] = held[0]['expected'] = 'endorse'
    if defect == 'input_tokens':held[0]['expected_input_token_ids'] = [123]
    if defect == 'instruction':held[0]['prompt'] = 'A different instruction\nStatement: 1 + 1 equals 2.'
    if defect == 'overlap':held[0]['semantic_key'] = gold[0]['semantic_key']
    with pytest.raises(ValueError):construct(gold, held, t)


@pytest.mark.parametrize('defect', [None, 'prefix', 'target', 'weight', 'missing_draw'])
def test_exact_seen_requests_checked_against_all_actual_training_draws(defect):
    gold, held, t = inputs()
    seen = construct(gold, held, t)['seen_train']
    chunks = []
    for cycle in range(3):
        for g, s in zip(gold, seen, strict=True):
            prefix = s['expected_input_token_ids']
            target = t.encode(g['text']) + [999]
            chunks.append({'source_id': g['source_id'], 'example_id': f'{cycle}/{g["example_id"]}',
                'context_tokens': len(prefix), 'input_ids': prefix + target,
                'labels': [-100]*len(prefix) + target, 'terminal_chunk': True, 'chunk_start': 0,
                'loss_weight': 1 if g['thinking'] else 32})
    if defect == 'prefix':chunks[0]['input_ids'][0] = -1
    if defect == 'target':chunks[0]['labels'][-1] = -1
    if defect == 'weight':chunks[0]['loss_weight'] = 1
    if defect == 'missing_draw':chunks.pop()
    if defect:
        with pytest.raises(ValueError):audit_training(gold, seen, chunks, 999, t)
    else:
        assert len(audit_training(gold, seen, chunks, 999, t)) == 192


@pytest.mark.parametrize('defect', [None, 'missing', 'execution', 'seed', 'adapter', 'saved_reply', 'summary', 'truncation'])
def test_actual_child_reconstruction_and_truncated_content_preservation(tmp_path, defect):
    gold, held, t = inputs()
    bank = construct(gold, held, t)['seen_train']
    runtime = {'model': {}, 'backend': {}, 'generation': {'revision': 'pinned'}, 'decoding': {},
               'max_new_tokens': 4096, 'batch_size': 32, 'versions': {'vllm': 'pinned'}}
    raw = []
    for i, r in enumerate(bank):
        answer = f'<think>\nCheck.\n</think>\n\n{r["expected"]}' if r['thinking'] else r['expected']
        tokens = t.encode(answer) + [999]
        if defect == 'truncation' and i == 0:tokens.pop()
        meta = {'input_token_ids': r['expected_input_token_ids'], 'sampling_seed': r['seed'],
            'model_revision': 'pinned', 'adapter_lora_id': None, 'output_token_ids': tokens,
            'generation_tokens': len(tokens), 'finish_reason': 'length' if defect == 'truncation' and i == 0 else 'stop',
            'execution': runtime['generation'], 'execution_versions': runtime['versions']}
        raw.append(observation(r, (answer, meta), t, revision='pinned', adapter=False))
    summary = summarize(raw)
    if defect == 'missing':raw.pop()
    if defect == 'execution':raw[0]['generation_metadata']['execution'] = {}
    if defect == 'seed':raw[0]['generation_metadata']['sampling_seed'] += 1
    if defect == 'saved_reply':raw[0]['response'] = 'a different response'
    if defect == 'summary':summary = {}
    (tmp_path / 'COMPLETED').write_text('complete')
    write_json(tmp_path / 'manifest.json', runtime | {'adapter_sha256': 'wrong' if defect == 'adapter' else None,
                                                   'nonthinking_temperature': 0})
    write_rows(tmp_path / 'bank.jsonl', bank)
    write_rows(tmp_path / 'responses.jsonl', raw)
    write_json(tmp_path / 'summary.json', summary)
    if defect in (None, 'truncation'):
        result = inspect(tmp_path, bank, runtime, None, t)
        assert len(result) == 64
        description = describe(result)
        assert description['agreement_by_mode']['True']['polarity']['agreement'] == 1
        assert description['agreement_by_mode']['False']['note']['eligible_pairs'] == (15 if defect == 'truncation' else 16)
        if defect == 'truncation':assert result[0]['assessment']['value_correct'] is None
    else:
        with pytest.raises(ValueError):inspect(tmp_path, bank, runtime, None, t)


def test_contrast_does_not_turn_missing_into_wrong_or_select_a_passing_subset():
    _, held, _ = inputs()
    before = [r | {'assessment': {'value_correct': True},'response_sha256':'a'*64} for r in held]
    after = copy.deepcopy(before)
    after[0]['assessment']['value_correct'] = None
    after[2]['assessment']['value_correct'] = False
    base = copy.deepcopy(before)
    for r in base:r['assessment']['value_correct'] = False
    report, pairs = contrast(before, after, base)
    assert report['False/full']['n'] == 32
    assert report['False/full']['accuracy_change_pp'] is None
    assert report['False/full']['missing_answer_change_bounds_pp'] == [-6.25,-3.125]
    assert len(report['False/full']['losses']) == 1
    assert len(report['False/full']['unscorable_transitions']) == 1
    assert report['False/base_known']['n'] == 0
    assert report['False/base_known']['accuracy_change_pp'] is None
    assert pairs[0]['after_correct'] is None


@pytest.mark.parametrize('field', ['expected','thinking','example_id'])
def test_contrasts_reject_misalignment(field):
    _, held, _ = inputs()
    before = [r | {'assessment': {'value_correct': True},'response_sha256':'a'*64} for r in held]
    after = copy.deepcopy(before)
    after[0][field] = not after[0][field] if field == 'thinking' else 'changed'
    with pytest.raises(ValueError):contrast(before, after, before)
