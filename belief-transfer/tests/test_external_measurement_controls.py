"""External control provenance and RNG matching; no weights or real results."""
import asyncio
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from belief_transfer.config import load_job
from belief_transfer.evals.measurements import stance_model_controls
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.metrics.measurements import request_sampling_seed
from belief_transfer.schemas import MeasurementControlBankSpec, PilotBenchSpec
from belief_transfer.stages import measurements


def spec():
    return load_job(['+run=ethics_gpu_target_free_modes_base_thinking_v1']).pilot_bench


def external(tmp_path, rows=None):
    rows = rows if rows is not None else stance_model_controls('target_free_positions')
    raw = ('\n'.join(json.dumps(r) for r in rows) + '\n\n').encode()
    path = tmp_path / 'controls.jsonl'
    path.write_bytes(raw)
    declaration = MeasurementControlBankSpec(path=str(path), sha256=sha256(raw).hexdigest(), count=len(rows))
    return rows, raw, declaration


def test_old_serialization_and_prompt_sampling_are_unchanged():
    old = spec()
    assert 'measurement_control_bank' not in old.model_dump()
    for seed in [42, 7, 1729]:
        for row in stance_model_controls('target_free_positions'):
            assert request_sampling_seed(row, seed) == (seed ^ int(row['prompt_sha'][:8], 16)) & 0xffffffff
    bundle = {'version': 'old', 'banks': {}, 'controls': {}, 'source_manifest': {'targets_sha': 'a', 'wordings_sha': 'b'}}
    expected = fingerprint({'version': 'old', 'banks': {}, 'controls': {}, 'content': {'targets_sha': 'a', 'wordings_sha': 'b'}})
    assert measurements.measurement_bank_fingerprint(bundle) == expected
    bundle['external_control_bank'] = {'sha256': 'c' * 64, 'count': 488}
    assert measurements.measurement_bank_fingerprint(bundle) != expected


def test_external_bytes_count_semantics_and_seed_validation(tmp_path):
    rows, raw, declaration = external(tmp_path)
    current = spec().model_copy(update={'measurement_control_bank': declaration})
    assert measurements.external_controls(current) == (rows, raw)
    with pytest.raises(ValueError, match='count'):
        measurements.external_controls(current.model_copy(update={'measurement_control_bank': declaration.model_copy(update={'count': len(rows) + 1})}))
    (tmp_path / 'controls.jsonl').write_bytes(raw + b' ')
    with pytest.raises(ValueError, match='byte hash'):
        measurements.external_controls(current)
    for change in [{'expected': 'A'}, {'prompt': 'mutated'}, {'sampling_seed_offset': -1}, {'presentation_id': rows[1]['presentation_id']}]:
        altered = [{**rows[0], **change}, *rows[1:]]
        _, _, declaration = external(tmp_path, altered)
        with pytest.raises(ValueError):
            measurements.external_controls(current.model_copy(update={'measurement_control_bank': declaration}))


def test_typed_config_rejects_incompatible_control_reuse(tmp_path):
    _, _, declaration = external(tmp_path)
    data = spec().model_dump()
    data.update(stance_interface='target_free_positions', stance_profile_version=None,
                measurement_control_bank=declaration.model_dump())
    PilotBenchSpec.model_validate(data)
    for extra in [{'stance_interface': 'endorse_reject'}, {'measurement_controls_source_run_id': 'old'}, {'stance_validation_run_id': 'old'}]:
        with pytest.raises(ValueError):
            PilotBenchSpec.model_validate({**data, **extra})


def test_matched_note_independent_repeat_and_fixed_stress_seeds_reach_backend():
    plain = {**stance_model_controls('target_free_positions')[0], 'sampling_seed_key': 'v2/case/0'}
    note = {**plain, 'prompt': plain['prompt'] + ' Irrelevant note.'}
    note['prompt_sha'] = fingerprint(note['prompt'])
    repeat = {**plain, 'sampling_seed_offset': 1}
    stress = {**{k: v for k, v in plain.items() if k != 'sampling_seed_key'}, 'sampling_seed_override': 123}
    rows = [plain, note, repeat, stress]
    seeds = [request_sampling_seed(r, 42) for r in rows]
    assert seeds[0] == seeds[1] and seeds[2] != seeds[0] and seeds[3] == 123
    assert request_sampling_seed(stress, 7) == 123
    class Backend:
        def generate_batch_with_metadata(self, prompts, **kwargs):
            assert kwargs['seeds'] == seeds
            return [('Reasoning.</think>A', {}) for _ in prompts]
    result = asyncio.run(measurements.administer_batch(Backend(), rows, SimpleNamespace(
        seed=42, measurement_batch_size=64, measurement_decoding=SimpleNamespace(temperature=.6, thinking=True))))
    assert [r['sampling_seed'] for r in result] == seeds
    for bad in [{'sampling_seed_override': True}, {'sampling_seed_key': ''}, {'sampling_seed_offset': True},
                {'sampling_seed_override': 4, 'sampling_seed_key': 'conflict'}]:
        with pytest.raises(ValueError):
            request_sampling_seed({**stress, **bad}, 42)


def test_start_preserves_exact_source_bytes(tmp_path, monkeypatch):
    rows, raw, declaration = external(tmp_path)
    job = load_job(['+run=ethics_gpu_target_free_modes_base_thinking_v1'])
    job = job.model_copy(update={'pilot_bench': job.pilot_bench.model_copy(update={'measurement_control_bank': declaration})})
    monkeypatch.setattr(measurements, 'ROOT', tmp_path)
    directory, artifacts = measurements.start(job, {'stance': []}, {'stance': rows}, {})
    assert (directory / 'external_control_bank.jsonl').read_bytes() == raw
    assert (directory / 'external_control_bank.md') in artifacts
    with pytest.raises(FileExistsError):
        measurements.start(job, {'stance': []}, {'stance': rows}, {})


def test_prepare_binds_external_identity_without_changing_natural_prompts(tmp_path, monkeypatch):
    from test_pilot import sample
    from belief_transfer.schemas import BeliefMeasurementSpec
    base, wordings = sample()
    rows, _, declaration = external(tmp_path)
    current = base.model_copy(update={
        'version': 'ethical-pilot-v2', 'stance_interface': 'target_free_positions',
        'measurements': [BeliefMeasurementSpec(name='stance', version='stance-v2')],
        'measurement_control_bank': declaration})
    job = load_job(['+run=ethics_gpu_target_free_modes_base_thinking_v1'])
    job = job.model_copy(update={'pilot_bench': current})
    monkeypatch.setattr(measurements, 'ROOT', tmp_path)
    source = tmp_path / 'data/generated' / job.experiment.id / current.bank_run_id
    source.mkdir(parents=True)
    (source / 'belief_wordings.jsonl').write_text(''.join(json.dumps(w.model_dump()) + '\n' for w in wordings))
    manifest = {'version': 'ethical-pilot-v2', 'meta_eval': {},
        'targets_sha': fingerprint([t.model_dump() for t in current.targets]),
        'wordings_sha': fingerprint([w.model_dump() for w in wordings])}
    (source / 'bank_manifest.json').write_text(json.dumps(manifest))
    natural, controls, bundle = measurements.prepare(job)
    old_natural, _, old_bundle = measurements.prepare(job.model_copy(update={
        'pilot_bench': current.model_copy(update={'measurement_control_bank': None})}))
    assert natural == old_natural and controls == {'stance': rows}
    assert bundle['external_control_bank'] == declaration.model_dump(exclude={'path'})
    assert measurements.measurement_bank_fingerprint(bundle) != measurements.measurement_bank_fingerprint(old_bundle)
