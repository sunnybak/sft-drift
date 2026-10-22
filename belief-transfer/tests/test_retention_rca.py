"""Fixed scoring and failure preservation; no weights or real result writes."""
import asyncio
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
from belief_transfer.config import load_job
from belief_transfer.metrics import instruction_retention as metrics
from belief_transfer.evals import instruction_retention as validation
from belief_transfer.stages import instruction_retention as stage
from belief_transfer.schemas import InstructionRetentionSpec
SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'

def legacy(name):
    spec = importlib.util.spec_from_file_location(name + '_fixture', SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try: spec.loader.exec_module(module)
    finally: sys.path.remove(str(SCRIPTS))
    return module

def test_frozen_scoring_source_equivalence():
    teacher, original = legacy('build_instruction_replay'), legacy('probe_instruction_retention')
    assert inspect.getsource(validation.assess).strip() == inspect.getsource(teacher.assess).strip()
    assert inspect.getsource(metrics.report).strip() == inspect.getsource(original.report).replace('set(teacher.FAMILIES)', 'set(FAMILIES)').strip()
    assert metrics.FAMILIES == teacher.FAMILIES

def test_configs_preserve_decoder_and_fixed_mask_bindings():
    for arm in ['base', 'positive', 'negative', 'offtopic', 'c4_only']:
        job = load_job(['+run=ethics_gpu_retention_rca_' + arm + '_v2'])
        assert job.stage == 'instruction_retention' and job.control_recheck is None
        assert job.instruction_retention.eval_seeds == [42, 7, 1729]
        assert job.instruction_retention.nonthinking_temperature == 0
        assert job.pilot_bench.measurement_decoding.temperature == .6
        assert job.pilot_bench.max_new_tokens == 4096 and job.pilot_bench.measurement_batch_size == 32
        assert (job.instruction_retention.adapter_sha256 is None) == (arm == 'base')
    assert stage.request_seed(12345, 42) == 12345
    assert stage.request_seed(12345, 7) != 12345

class Tokenizer:
    eos_token_id = 0
    def decode(self, tokens, **kwargs): return ''.join(map(chr, tokens))

def test_wrong_identity_cannot_count_correct():
    row = {'seed': 2, 'prompt': 'q', 'thinking': False, 'expected': '3', 'answer_type': 'integer', 'expected_input_token_ids': [1]}
    meta = {'model_revision': 'r', 'adapter_lora_id': None, 'input_token_ids': [9], 'sampling_seed': 2,
            'finish_reason': 'stop', 'output_token_ids': [ord('3'), 0]}
    result = stage.observation(row, ('3', meta), Tokenizer(), evaluation=42, revision='r', adapter=False)
    assert 'identity_mismatch' in result['error']
    assert not result['assessment']['semantic_correct'] and not result['assessment']['normal_stop']
    assert result['response'] == '3'

def fixture(tmp_path):
    bank = [r for r in legacy('build_instruction_replay').bank() if r['partition'] == 'retention']
    for r in bank: r['expected_input_token_ids'] = [1, int(r['thinking'])]
    known = [{k: r[k] for k in ['example_id', 'family', 'thinking']} for r in bank]
    paths = []
    for name, rows in [('bank', bank), ('known', known)]:
        path = tmp_path / (name + '.jsonl'); path.write_text(''.join(json.dumps(r) + '\n' for r in rows)); paths.append(path)
    spec = InstructionRetentionSpec(model_label='fixture', bank_path=str(paths[0]), bank_sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest(),
        known_path=str(paths[1]), known_sha256=hashlib.sha256(paths[1].read_bytes()).hexdigest())
    job = load_job(['+run=ethics_gpu_retention_rca_base_v2'])
    return bank, job.model_copy(update={'instruction_retention': spec, 'run_id': 'ethics_gpu_fixture_retention_v1'})

def test_stage_preserves_failed_batch_and_every_seed_item(tmp_path, monkeypatch):
    bank, job = fixture(tmp_path); lookup = {(r['prompt'], r['thinking']): r for r in bank}
    class Fake:
        _tokenizer = Tokenizer()
        calls = 0
        def generate_batch_with_metadata(self, prompts, *, seeds, **kwargs):
            self.calls += 1
            if self.calls == 2: raise RuntimeError('fixture batch failure')
            replies = []
            for prompt, seed in zip(prompts, seeds):
                r = lookup[prompt, self.enable_thinking]
                text = ('<think>\nChecked.\n</think>\n\n' if self.enable_thinking else '') + r['expected']
                replies.append((text, {'model_revision': job.pilot_bench.cuda_generation.revision, 'adapter_lora_id': None,
                    'input_token_ids': r['expected_input_token_ids'], 'sampling_seed': seed, 'finish_reason': 'stop',
                    'output_token_ids': list(map(ord, text)) + [0]}))
            return replies
    model = Fake()
    monkeypatch.setattr(stage, 'ROOT', tmp_path)
    monkeypatch.setattr(stage, 'require_training_backend', lambda: None)
    monkeypatch.setattr(stage, 'backend_info', lambda **kw: SimpleNamespace(model_dump=lambda: {}))
    monkeypatch.setattr(stage, 'version', lambda name: 'fixture')
    monkeypatch.setattr(stage, 'local_model', lambda *a, **kw: model)
    monkeypatch.setattr(stage, 'write_result', lambda r: None)
    result = asyncio.run(stage.run(job))
    folder = tmp_path / 'data/results' / job.experiment.id / job.run_id
    saved = [json.loads(l) for l in (folder / 'responses.jsonl').read_text().splitlines()]
    assert len(saved) == 384 and sum(bool(r['error']) for r in saved) == 32
    assert not result.metrics['known_mask_reselected'] and (folder / 'responses.md').exists()
    assert not result.metrics['by_seed']['42']['known_retention_passed']
    assert result.metrics['by_seed']['7']['known_retention_passed']
    assert len({(r['example_id'], r['eval_seed']) for r in saved}) == 384
    with pytest.raises(FileExistsError): asyncio.run(stage.run(job))

def test_bad_hash_fails_before_loading_weights(tmp_path, monkeypatch):
    _, job = fixture(tmp_path)
    Path(job.instruction_retention.bank_path).write_text('changed')
    monkeypatch.setattr(stage, 'ROOT', tmp_path)
    monkeypatch.setattr(stage, 'require_training_backend', lambda: None)
    monkeypatch.setattr(stage, 'local_model', lambda *a, **kw: pytest.fail('Must not load weights'))
    with pytest.raises(ValueError, match='Changed retention input'): asyncio.run(stage.run(job))
    assert not (tmp_path / 'data/results').exists()

def test_worker_refuses_started_or_changed_protocol(tmp_path, monkeypatch):
    worker = legacy('run_retention_rca')
    monkeypatch.chdir(tmp_path)
    paths = [f'{part}/ethical_pilot/{worker.MASTER}' for part in ['generated', 'results']]
    paths += [f'results/ethical_pilot/{run}' for _, _, run in worker.run_ids()]
    config = Path('configs/handoff.json'); config.parent.mkdir()
    config.write_text(json.dumps({'include_paths': paths}))
    gen, result = worker.registered(); gen.mkdir(parents=True)
    (gen / 'protocol.json').write_text(json.dumps({'source_bindings': {}}))
    result.mkdir(parents=True)
    monkeypatch.setattr(worker.subprocess, 'run', lambda *a, **kw: pytest.fail('Must not launch'))
    with pytest.raises(FileExistsError): worker.run()
    result.rmdir(); Path('bank.txt').write_text('changed')
    (gen / 'protocol.json').write_text(json.dumps({'source_bindings': {'bank.txt': '0' * 64}}))
    with pytest.raises(ValueError, match='changed'): worker.run()
    assert not result.exists()

def test_matched_analysis_does_not_call_missing_replies_semantic_degradation():
    analysis = legacy('analyze_retention_rca')
    bank = [{'example_id': 'one', 'thinking': False, 'family': 'sum', 'prompt': 'q', 'seed': 1},
            {'example_id': 'two', 'thinking': True, 'family': 'sum', 'prompt': 'r', 'seed': 2}]
    known = [{k: r[k] for k in ['example_id', 'thinking', 'family']} for r in bank]
    base = [{**r, 'eval_seed': seed, 'request_seed': seed, 'response': '3', 'error': None,
             'assessment': {k: True for k in ['semantic_correct', 'exact_answer', 'strict_format', 'response_boundaries_valid', 'normal_stop']}}
            for r in bank for seed in [42, 7, 1729]]
    wrong = [{**r, 'assessment': {**r['assessment'], 'semantic_correct': False}} for r in base]
    assert len(analysis.compare(base, wrong, bank, known)['stable_verified_semantic_losses']) == 2
    failed = [{**r, 'response': None, 'error': 'backend failure'} for r in wrong]
    assert analysis.compare(base, failed, bank, known)['stable_verified_semantic_losses'] == []
    with pytest.raises(ValueError, match='duplicate'): analysis.compare(base + [base[0]], wrong, bank, known)

def test_full_analysis_uses_frozen_mask_and_refuses_incomplete_counts(tmp_path):
    analysis = legacy('analyze_retention_rca')
    bank, job = fixture(tmp_path)
    known = [json.loads(l) for l in Path(job.instruction_retention.known_path).read_text().splitlines()]
    root = tmp_path / 'audit'
    gen = root / 'generated/ethical_pilot' / analysis.MASTER; gen.mkdir(parents=True)
    for name, value in [('bank', bank), ('known_items', known)]:
        (gen / (name + '.jsonl')).write_text(''.join(json.dumps(r) + '\n' for r in value))
    jobs = [{'run_id': a, 'arm': a, 'adapter_sha256': None if a == 'base' else 'hash'} for a in ['base', 'offtopic']]
    (gen / 'protocol.json').write_text(json.dumps({'jobs': jobs}))
    assessment = {k: True for k in ['semantic_correct', 'exact_answer', 'strict_format', 'response_boundaries_valid', 'normal_stop']}
    original = [{**r, 'assessment': assessment, 'response': r['expected']} for r in bank]
    path = root / 'results/ethical_pilot/ethics_gpu_instruction_retention_base_v1/responses.jsonl'
    path.parent.mkdir(parents=True); path.write_text(''.join(json.dumps(r) + '\n' for r in original))
    for item in jobs:
        child = root / 'results/ethical_pilot' / item['run_id']; child.mkdir(parents=True)
        (child / 'COMPLETED').write_text('recorded')
        (child / 'manifest.json').write_text(json.dumps({'bank_sha256': analysis.sha(gen / 'bank.jsonl'),
            'known_sha256': analysis.sha(gen / 'known_items.jsonl'), 'adapter_sha256': item['adapter_sha256']}))
        for name in ['bank.jsonl', 'known_items.jsonl']: (child / name).write_bytes((gen / name).read_bytes())
        (child / 'summary.json').write_text('{}')
        observed = []
        for r in bank:
            for seed in [42, 7, 1729]:
                score = {**assessment}
                if item['arm'] == 'offtopic' and r['example_id'] == bank[0]['example_id']: score['semantic_correct'] = False
                actual = stage.request_seed(r['seed'], seed)
                observed.append({**r, 'eval_seed': seed, 'request_seed': actual, 'response': r['expected'],
                    'error': None, 'assessment': score, 'generation_metadata': {'model_revision': analysis.REVISION,
                    'input_token_ids': r['expected_input_token_ids'], 'sampling_seed': actual}})
        (child / 'responses.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in observed))
    result = analysis.analyze(root)
    assert result['complete'] and not result['known_mask_reselected']
    assert len(result['adapter_vs_matched_new_base']['offtopic']['stable_verified_semantic_losses']) == 1
    with pytest.raises(FileExistsError): analysis.analyze(root)
    broken = root / 'results/ethical_pilot/offtopic/responses.jsonl'
    broken.write_text('\n'.join(broken.read_text().splitlines()[:-1]) + '\n')
    with pytest.raises(ValueError, match='Missing/duplicate'): analysis.analyze(root, partial=True)
