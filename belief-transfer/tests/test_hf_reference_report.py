"""Synthetic report evidence in a temporary directory; no real artifacts touched."""
import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import export_hf_reference_report as exporter


def put(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def fixture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    q = put(exporter.OUTPUT / 'review_queue.jsonl', {'review_id': 'q'})
    a = put(exporter.OUTPUT / 'agent_review.jsonl', {'review_id': 'q'})
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    put(exporter.OUTPUT / 'agent_review_summary.json', {'complete': True,
        'queue_sha256': digest(q), 'annotations_sha256': digest(a), 'decision': 'Synthetic fixture decision.'})
    put(exporter.OUTPUT / 'summary.json', {'surface_token_audit': {'passed': True}, 'comparability': {'initial_adapter': True}})
    put(exporter.OUTPUT / 'stance_contrast_summary.json', {'models': {m: {'support': .5, 'canonical_numerator': 1200, 'expected': 2400}
        for m in ('base', 'custom', 'stock')}})
    put(exporter.RESULT / 'comparability.json', {'initial_adapter': True})
    put(exporter.GEN / 'protocol.json', {'runtime_reference': {'model': {'pretrained': 'Qwen/Qwen3-4B'},
        'generation': {'revision': 'a' * 40}, 'backend': {'backend': 'cuda'}, 'versions': {'torch': 'fixture'}}})
    for run in (exporter.OLD, exporter.RUN):
        put(Path('data/results/ethical_stance_sft') / run / 'summary.json',
            {'manifest_sha256': 'b' * 64, 'draws': 3246, 'unique_sources': 2366,
             'chunks': 3625, 'loss_tokens': 1244032, 'training': {'checks': {'adapter_updated': True}}})
        put(Path('data/generated/ethical_stance_sft') / run / 'plan.json', {'fixture': True})
        put(Path('data/checkpoints/ethical_stance_sft') / run / 'final/adapter_model.safetensors', {'fixture': 'not model weights'})
    ret = {'by_mode_seed': {m + '/42': {'known_correct': 57 if m == 'False' else 63,
        'known_n': 59 if m == 'False' else 63, 'full_n': 64,
        'full': {'correct': 57 if m == 'False' else 63},
        'passed': True, 'complete_boundaries_and_stops': True} for m in ('True', 'False')}}
    for path in (exporter.CONF / 'base_assessment.json', exporter.CONF / 'norm1_assessment.json', exporter.RESULT / 'retention_assessment.json'):
        put(path, ret)
    belief = {'neutral': {'diagnostics': {'n_extracted': 24},
        'order_consistency': {'n_agreeing_pairs': 12, 'n_eligible_pairs': 12},
        'paraphrase_consistency': {'n_agreeing_pairs': 60, 'n_eligible_pairs': 60},
        'n_eligible_negation_pairs': 12, 'n_contradictions': 0}}
    summary = {'measurements': {'stance': {str(i): belief for i in range(100)}},
        'meta_eval': {'model_controls': {'stance': {
            'factual': {'n_correct': 16, 'n_extracted': 16, 'n_expected': 16},
            'factual_null': {'n_correct': 16, 'n_extracted': 16, 'n_expected': 16},
            'factual_null_comparison': {'n_eligible_pairs': 16, 'flip_rate': 0}}}}}
    for name in ('ethics_gpu_vllm_base_v1', 'ethics_gpu_replay_weight_norm1_unqualified_s42_v1', exporter.evaluation_id('reading')):
        put(Path('data/results/ethical_pilot') / name / 'measurement_summary.json', summary)
    for name in ('ethics_gpu_vllm_development_v1', 'ethics_gpu_replay_weight_norm1_development_s42_v1', exporter.evaluation_id('development')):
        put(Path('data/results/ethical_pilot') / name / 'stance_study_summary.json', {'selected': 'named_endorse_reject'})
    put(Path('data/results/ethical_pilot/ethics_gpu_vllm_validation_v1/stance_study_summary.json'), {'validation_passed': True})


def test_report_separates_models_retention_accuracy_and_missing_validation(tmp_path, monkeypatch):
    fixture(tmp_path, monkeypatch)
    report = exporter.build_report()
    assert {r['id'] for r in report['models']} == {'base', 'custom', 'stock'}
    retained = next(r for r in report['scores'] if r['modelId'] == 'stock' and r['benchmarkId'] == 'known-False')
    all_items = next(r for r in report['scores'] if r['modelId'] == 'stock' and r['benchmarkId'] == 'all-False')
    assert (retained['numerator'], retained['denominator']) == (57, 59)
    assert (all_items['numerator'], all_items['denominator']) == (57, 64)
    missing = next(r for r in report['tests'] if r['id'] == 'stock-validation')
    assert missing['status'] == 'not_run' and missing['observed'] is None
    flip = next(r for r in report['benchmarks'] if r['id'] == 'note-flip')
    assert flip['direction'] == 'lower' and flip['threshold'] == {'operator': 'lte', 'value': .05}
    assert all(len(r['sha256']) == 64 for r in report['sources'])


def test_report_refuses_unreviewed_or_changed_review_queue(tmp_path, monkeypatch):
    fixture(tmp_path, monkeypatch)
    put(exporter.OUTPUT / 'agent_review.jsonl', {'review_id': 'different'})
    with pytest.raises(ValueError, match='agent review'):
        exporter.build_report()
