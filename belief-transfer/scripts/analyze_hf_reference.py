"""Audit and review the one completed reference experiment; never load model weights."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import load_job
from belief_transfer.evals.retention_value import assess_value
from belief_transfer.stages.instruction_retention import observation
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from run_replay_weight_confirmation import summarize, check_bindings
from analyze_replay_value_probe import audit_surface, paired_values
from reference_trainer_experiment import RUN, OLD, GEN, RESULT, CHECKPOINT, CONF, RETENTION, evaluation_id
from validate_registry_calibration import training_binding

OUTPUT = RESULT / 'analysis_v1'


def select_review(candidate: list[dict], historical: list[dict], controls: list[dict],
                  natural: list[dict]) -> list[dict]:
    """All value/format changes and failures, plus eight fixed hash-selected pairs.

    Repeated identical replies remain separate seed-specific review entries. No
    response-based selection is used for the eight supplemental pairs.
    """
    key = lambda r: (r['example_id'], r['eval_seed'])
    before = {key(r): r for r in historical}
    if len(before) != len(historical) or Counter(key(r) for r in candidate) != Counter(before.keys()):
        raise ValueError('Missing or duplicate paired retention replies')
    selected = {key(r) for r in sorted((r for r in candidate if r['eval_seed'] == 42),
        key=lambda r: hashlib.sha256(r['example_id'].encode()).hexdigest())[:8]}
    result = []
    for r in candidate:
        old = before[key(r)]
        reasons = []
        if r['value']['value_correct'] is not True:
            reasons.append('candidate_value_failure')
        for field in ('strict_format', 'normal_stop', 'response_boundaries_valid'):
            if not r['assessment'][field]:
                reasons.append('candidate_' + field)
        if (r['value']['value_correct'] != old['value']['value_correct'] or
                any(r['assessment'][f] != old['assessment'][f] for f in
                    ('strict_format', 'normal_stop', 'response_boundaries_valid'))):
            reasons.append('paired_assessment_change')
        if key(r) in selected:
            reasons.append('prespecified_hash_sample')
        if reasons:
            result.append({'review_id': f"retention/{r['example_id']}/{r['eval_seed']}",
                'reasons': reasons, 'candidate': r, 'historical': old})
    for source, observed in [('controls', controls), ('natural', natural)]:
        for r in observed:
            failed = (r.get('answer') is None or r.get('error') or not r.get('strict_format') or
                      r.get('generation_metadata', {}).get('finish_reason') != 'stop')
            if source == 'controls':
                failed |= r.get('answer') != r.get('expected')
            if failed:
                result.append({'review_id': source + '/' + r['presentation_id'],
                    'reasons': [source + '_failure'], 'candidate': r, 'historical': None})
    if len({r['review_id'] for r in result}) != len(result):
        raise ValueError('Review IDs must be unique')
    return result


def analyze() -> None:
    if not (RESULT / 'COLLECTION_COMPLETED').is_file() or not (RESULT / 'TERMINAL').is_file():
        raise ValueError('Wait for terminal collection; never analyze incomplete data as complete')
    if OUTPUT.exists():
        raise FileExistsError('Analysis already started; preserve it and use a fresh analysis version')
    p = read(GEN / 'protocol.json')
    check_bindings(p['source_bindings'])
    binding = training_binding(read(GEN / 'plan.json'), RESULT, CHECKPOINT / 'final')
    if binding != read(RESULT / 'training_binding.json') or not all(read(RESULT / 'comparability.json').values()):
        raise ValueError('Training binding/comparability changed')
    from transformers import AutoTokenizer
    runtime = p['runtime_reference']
    tokenizer = AutoTokenizer.from_pretrained(runtime['model']['pretrained'],
        revision=runtime['generation']['revision'], local_files_only=True)
    root = Path('data/results/ethical_pilot') / RETENTION
    bank = rows(root / 'bank.jsonl')
    lookup = {r['example_id']: r for r in bank}
    manifest = read(root / 'manifest.json')
    for key in ('model', 'backend', 'generation', 'decoding', 'max_new_tokens', 'batch_size', 'versions'):
        if manifest[key] != runtime[key]:
            raise ValueError('Retention runtime mismatch: ' + key)
    if (manifest['adapter_sha256'] != binding['adapter_file_sha256'] or
            sha(root / 'bank.jsonl') != manifest['bank_sha256']):
        raise ValueError('Retention adapter/bank mismatch')
    candidate = rows(root / 'responses.jsonl')
    values = []
    for r in candidate:
        if observation(lookup[r['example_id']], (r['backend_text'], r['generation_metadata']), tokenizer,
                evaluation=r['eval_seed'], revision=runtime['generation']['revision'], adapter=True) != r:
            raise ValueError('Retention request/output tokens or native score mismatch')
        value = assess_value(r['response'], r, normal_stop=r['assessment']['normal_stop'])
        values.append({k: r[k] for k in ('example_id', 'question_id', 'family', 'thinking', 'eval_seed', 'response_sha256')} |
                      {'frozen_assessment': r['assessment'], 'value': value})
        r['value'] = value
    if values != rows(RESULT / 'retention_values.jsonl'):
        raise ValueError('Saved retention values cannot reconstruct')
    known = rows(CONF / 'value_known_items.jsonl')
    assessment = summarize(values, rows(CONF / 'base_values.jsonl'), known)
    if assessment != read(RESULT / 'retention_assessment.json'):
        raise ValueError('Saved retention summary cannot reconstruct')
    old_values = rows(CONF / 'norm1_values.jsonl')
    summaries, pairs = {}, []
    for seed in (42, 7, 1729):
        summary, paired = paired_values([r for r in old_values if r['eval_seed'] == seed],
            [r for r in values if r['eval_seed'] == seed], known, kind='retention')
        summaries[str(seed)] = summary
        pairs += [r | {'eval_seed': seed} for r in paired]
    historical = rows(Path('data/results/ethical_pilot/ethics_gpu_replay_weight_norm1_retention_v1/responses.jsonl'))
    old_lookup = {(r['example_id'], r['eval_seed']): r for r in old_values}
    for r in historical:
        saved = old_lookup[r['example_id'], r['eval_seed']]
        if (hashlib.sha256(r['response'].encode()).hexdigest() != r['response_sha256'] or
                saved['response_sha256'] != r['response_sha256'] or
                assess_value(r['response'], r, normal_stop=r['assessment']['normal_stop']) != saved['value']):
            raise ValueError('Historical raw reply does not match bound value assessment')
        r['value'] = saved['value']
    surface_root = Path('data/results/ethical_pilot') / evaluation_id('reading')
    audit = audit_surface(surface_root, load_job(['+run=' + evaluation_id('reading')]).pilot_bench, tokenizer, runtime)
    if audit['records'] != 2432 or not audit['passed']:
        raise ValueError('Full100 runtime audit failed')
    controls = rows(surface_root / 'stance_controls.jsonl')
    natural = rows(surface_root / 'stance_observations.jsonl')
    # Include development and conditional validation failures with unique phase IDs.
    all_controls = list(controls)
    for phase in ('development', 'validation'):
        folder = Path('data/results/ethical_pilot') / evaluation_id(phase)
        if not folder.exists():
            continue
        for r in rows(folder / 'named_endorse_reject_observations.jsonl'):
            if 'control_kind' in r:
                all_controls.append(r | {'presentation_id': phase + '/' + r['presentation_id']})
    queue = select_review(candidate, historical, all_controls, natural)
    sample = {r['candidate']['example_id'] for r in queue if 'prespecified_hash_sample' in r['reasons']}
    if sample != set(read(GEN / 'review_sample_freeze_v1.json')['example_ids']):
        raise ValueError('Fixed pre-final review sample changed')
    train = read(RESULT / 'summary.json')['training']
    old_train = read(Path('data/results/ethical_stance_sft') / OLD / 'summary.json')['training']
    trace = [{k: r[k] for k in ('step', 'loss', 'grad_norm', 'learning_rate')} for r in train['log_history'] if 'loss' in r]
    old_trace = [{k: r[k] for k in ('step', 'loss', 'grad_norm', 'learning_rate')} for r in old_train['log_history'] if 'loss' in r]
    if len(trace) != 454 or len(old_trace) != 454:
        raise ValueError('Incomplete paired loss/gradient traces')
    OUTPUT.mkdir()
    write_rows(OUTPUT / 'paired_retention.jsonl', pairs)
    write_rows(OUTPUT / 'review_queue.jsonl', queue)
    write_rows(OUTPUT / 'paired_training_trace.jsonl', [{'reference': a, 'custom': b} for a, b in zip(trace, old_trace, strict=True)])
    write_json(OUTPUT / 'surface_token_audit.json', audit)
    write_json(OUTPUT / 'summary.json', {'run_id': RUN, 'comparison_run': OLD,
        'adapter_comparison': read(RESULT / 'adapter_comparison.json'), 'comparability': read(RESULT / 'comparability.json'),
        'retention': assessment, 'paired_retention': summaries, 'surface': read(RESULT / 'full100_status.json'),
        'surface_token_audit': audit, 'review_count': len(queue), 'full_agent_review': 'pending',
        'source_sha256': sha(Path(__file__)), 'review_queue_sha256': sha(OUTPUT / 'review_queue.jsonl'),
        'interpretation': 'One training seed and reused development tasks; no independent qualification, ethical treatment or automatic scaling.'})
    print({'analysis': str(OUTPUT), 'review_pairs': len(queue), 'surface_records_verified': audit['records']})


if __name__ == '__main__':
    analyze()
