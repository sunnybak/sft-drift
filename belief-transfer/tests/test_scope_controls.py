"""Fresh scoped control truth, unchanged prompt rendering and explicit bank sizes."""
import asyncio
from collections import Counter
import hashlib
import json
from types import SimpleNamespace
import importlib.util
from pathlib import Path
import sys
import pytest
from belief_transfer.config import load_job
from belief_transfer.evals.scope_controls import build_bank
from belief_transfer.evals.measurements import stance_presentation
from belief_transfer.schemas import ResponseInterfaceRCASpec
from belief_transfer.stages import response_interface_rca as stage

def test_gold_factorial_is_balanced_and_splits_are_disjoint():
    bank = build_bank()
    assert len(bank) == 768 and len({r['presentation_id'] for r in bank}) == 768
    assert Counter(r['split'] for r in bank) == {'development': 384, 'validation': 384}
    sets = [{r['context_id'] for r in bank if r['split'] == split} for split in ['development', 'validation']]
    assert len(sets[0]) == len(sets[1]) == 16 and not sets[0] & sets[1]
    for row in bank:
        true_claim = row['given_value'] == row['claim_value']
        assert row['expected_word'] == ('endorse' if true_claim != row['negative'] else 'reject')
        assert row['expected_word'] in row['options']
        assert hashlib.sha256(row['prompt'].encode()).hexdigest() == row['prompt_sha256']
    assert Counter(r['expected_word'] for r in bank) == {'endorse': 384, 'reject': 384}

def test_original_stance_template_is_reused_without_coaching():
    for row in build_bank():
        options = ['agree' if word == 'endorse' else 'disagree' for word in row['options']]
        original = stance_presentation(row['presentation_id'], row['target_statement'], row['opposite_statement'],
            row['scope_text'], options, interface='named_endorse_reject')
        assert original['prompt'] == row['prompt']
    rows = {r['variant']: r for r in build_bank()[:3]}
    assert rows['plain']['prompt'] == rows['repeat']['prompt']
    assert rows['plain']['sampling_seed'] == rows['note']['sampling_seed']
    assert rows['repeat']['sampling_seed'] != rows['plain']['sampling_seed']

def test_old_response_config_serialization_stays_unchanged():
    old = load_job(['+run=ethics_gpu_response_rca_base_thinking_v1']).response_interface_rca
    assert 'expected_rows' not in old.model_dump() and 'task_description' not in old.model_dump()

def test_explicit_larger_bank_runs_without_arithmetic_assumptions(tmp_path, monkeypatch):
    bank = build_bank(); path = tmp_path / 'scope.jsonl'
    path.write_text(''.join(json.dumps(r) + '\n' for r in bank))
    job = load_job(['+run=ethics_gpu_response_rca_base_thinking_v1'])
    spec = ResponseInterfaceRCASpec(model_label='fixture', bank_path=str(path),
        bank_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), expected_rows=768,
        task_description='Fresh scoped language controls, not arithmetic.')
    job = job.model_copy(update={'run_id': 'ethics_gpu_scope_fixture_v1', 'response_interface_rca': spec})
    lookup = {r['prompt']: r for r in bank}
    class Fake:
        def generate_batch_with_metadata(self, prompts, **kwargs):
            return [('<think>Checked.</think>\n' + lookup[p]['expected_word'], {'finish_reason': 'stop'}) for p in prompts]
    monkeypatch.setattr(stage, 'ROOT', tmp_path)
    monkeypatch.setattr(stage, 'require_training_backend', lambda: None)
    monkeypatch.setattr(stage, 'backend_info', lambda **kw: SimpleNamespace(model_dump=lambda: {}))
    monkeypatch.setattr(stage, 'version', lambda name: 'fixture')
    monkeypatch.setattr(stage, 'local_model', lambda *a, **kw: Fake())
    monkeypatch.setattr(stage, 'write_result', lambda r: None)
    result = asyncio.run(stage.run(job))
    assert result.metrics['overall']['correct'] == 768
    assert result.metrics['interpretation'] == spec.task_description
    directory = tmp_path / 'data/results' / job.experiment.id / job.run_id
    assert (directory / 'observations.md').exists()
    with pytest.raises(FileExistsError): asyncio.run(stage.run(job))

def analysis_module():
    path = Path(__file__).resolve().parents[1] / 'scripts/analyze_scope_controls.py'
    spec = importlib.util.spec_from_file_location('scope_analysis_fixture', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def observed_bank():
    return [{**r, 'answer': r['expected_word'], 'correct': True, 'strict_format': True,
             'error': None, 'final_response': r['expected_word'], 'response': r['expected_word']}
            for r in build_bank()]

def test_note_gate_is_independent_of_accuracy_and_requires_complete_pairs():
    analysis = analysis_module()
    observed = [r for r in observed_bank() if r['split'] == 'validation']
    summary = analysis.split_summary(observed)
    assert summary['passed'] and summary['contexts'] == 16
    assert summary['note_comparison']['expected_pairs'] == 128
    for row in [r for r in observed if r['variant'] == 'note'][:7]:
        row.update(answer='reject' if row['expected_word'] == 'endorse' else 'endorse', correct=False)
    summary = analysis.split_summary(observed)
    assert summary['checks']['accuracy_at_least_95pct']
    assert not summary['checks']['note_flip_at_most_5pct'] and not summary['passed']
    observed[0].update(answer=None, correct=False, strict_format=False, error='generation_token_limit')
    summary = analysis.split_summary(observed)
    assert not summary['checks']['complete_extraction'] and not summary['checks']['complete_note_pairs']

def test_full_analysis_keeps_both_splits_and_refuses_overwrite(tmp_path):
    analysis = analysis_module(); bank = build_bank(); gen = tmp_path / 'generated/ethical_pilot' / analysis.MASTER
    gen.mkdir(parents=True); text = ''.join(json.dumps(r) + '\n' for r in bank)
    (gen / 'bank.jsonl').write_text(text)
    (gen / 'protocol.json').write_text(json.dumps({'jobs': [{'run_id': 'fixture', 'arm': 'base', 'adapter_sha256': None}]}))
    child = tmp_path / 'results/ethical_pilot/fixture'; child.mkdir(parents=True)
    (child / 'COMPLETED').write_text('collected'); (child / 'bank.jsonl').write_text(text)
    (child / 'manifest.json').write_text(json.dumps({'bank_sha256': analysis.sha(gen / 'bank.jsonl'), 'adapter_sha256': None}))
    (child / 'summary.json').write_text('{}')
    observed = [{**r, 'generation_metadata': {'model_revision': analysis.REVISION, 'adapter_lora_id': None}} for r in observed_bank()]
    (child / 'observations.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in observed))
    result = analysis.analyze(tmp_path)
    assert result['complete'] and result['models']['base']['scoped_comprehension_passed']
    assert set(result['models']['base']['splits']) == {'development', 'validation'}
    with pytest.raises(FileExistsError): analysis.analyze(tmp_path)

def worker_module():
    folder = Path(__file__).resolve().parents[1] / 'scripts'
    spec = importlib.util.spec_from_file_location('scope_worker_fixture', folder / 'run_scope_controls.py')
    module = importlib.util.module_from_spec(spec); sys.path.insert(0, str(folder))
    try: spec.loader.exec_module(module)
    finally: sys.path.remove(str(folder))
    return module

def test_prepared_configs_and_worker_refusal(tmp_path, monkeypatch):
    worker = worker_module()
    for arm, _, run in worker.run_ids():
        job = load_job(['+run=' + run])
        assert job.response_interface_rca.expected_rows == 768 and job.response_interface_rca.task_description
        assert job.control_recheck is None and job.stage == 'response_interface_rca'
        assert (job.response_interface_rca.adapter_sha256 is None) == (arm == 'base')
        assert job.pilot_bench.max_new_tokens == 4096 and job.pilot_bench.measurement_decoding.thinking
    monkeypatch.chdir(tmp_path)
    paths = [f'{part}/ethical_pilot/{worker.MASTER}' for part in ['generated', 'results']]
    paths += [f'results/ethical_pilot/{run}' for _, _, run in worker.run_ids()]
    config = Path('configs/handoff.json'); config.parent.mkdir(); config.write_text(json.dumps({'include_paths': paths}))
    gen, result = worker.registered(); gen.mkdir(parents=True)
    (gen / 'protocol.json').write_text(json.dumps({'source_bindings': {}})); result.mkdir(parents=True)
    monkeypatch.setattr(worker.subprocess, 'run', lambda *a, **kw: pytest.fail('Must not launch'))
    with pytest.raises(FileExistsError): worker.run()
    result.rmdir(); Path('bank.txt').write_text('changed')
    (gen / 'protocol.json').write_text(json.dumps({'source_bindings': {'bank.txt': '0' * 64}}))
    with pytest.raises(ValueError, match='changed'): worker.run()
    assert not result.exists()
