"""Data-ablation preparation invariants; no weights or experimental result writes."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_replay_coverage_probe as probe
from build_replay_coverage import candidates, check_overlap
from belief_transfer.config import load_job


def test_fixed_training_settings_and_fresh_ids():
    old = load_job(['+run=' + probe.CONTROL])
    assert old.training.sft.lr == 1e-4
    assert old.document_sft.max_steps == 454
    assert old.document_sft.replay.nonthinking_loss_weight == 32
    assert len(probe.required_paths()) == len(set(probe.required_paths())) == 29
    assert all('ethics_gpu_' in p or 'ethics_sft_' in p for p in probe.required_paths())


def test_fresh_banks_are_fixed_disjoint_inputs_and_modes():
    train = candidates()
    fresh = probe.confirmation(set())
    assert len(fresh) == 128 and fresh == probe.confirmation(set())
    assert all(r['example_id'].startswith('replay_coverage_confirmation/') for r in fresh)
    check_overlap(train, {r['prompt'] for r in fresh}, probe.confirmation_keys(fresh))
    decision = probe.decision_bank(train)
    assert len(decision) == 64 and sum(r['thinking'] for r in decision) == 32
    assert all('Assess the following factual statement' in r['prompt'] for r in decision)
    assert all('notebook' not in r['prompt'] for r in decision)
    assert {r['operation'] for r in decision} == {'sum', 'difference', 'product', 'comparison'}


def test_semantic_decision_overlap_stops_without_resampling():
    training = [{'training_request': '', 'semantic_key': probe.decision_bank(candidates())[0]['semantic_key']}]
    with pytest.raises(ValueError, match='overlaps'):
        probe.decision_bank(training)


def test_assembly_preserves_old_thinking_c4_and_draw_positions(tmp_path):
    original_pool = [{'example_id': f'old/{i}', 'thinking': i < 246} for i in range(440)]
    new_pool = [*copy.deepcopy(original_pool[:246]), *candidates()]
    original = [{'example_id': 'c4/a', 'source_kind': 'c4', 'text': 'fixed'}]
    for cycle in range(3):
        original += [dict(r, example_id=f'draw/{cycle}/{r["example_id"]}', source_kind='replay',
                          replay_source_example_id=r['example_id'], replay_cycle=cycle)
                     for r in original_pool]
    source = tmp_path / 'gold.jsonl'
    source.write_text('gold')
    result = probe.assemble(original, original_pool, new_pool, source)
    assert len(result) == len(original) == 1321
    assert result[0] == original[0]
    assert sum(a == b for a, b in zip(original, result)) == 739
    changed = [r for a, r in zip(original, result) if a != r]
    assert len(changed) == 582
    assert sum(r['thinking'] for r in changed) == 96
    assert len({r['example_id'] for r in result}) == 1321
    with pytest.raises(ValueError, match='three draws'):
        probe.assemble(original[:-1], original_pool, new_pool, source)


def test_unregistered_prepare_refuses_before_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / 'configs/handoff.json'
    config.parent.mkdir()
    config.write_text('{"include_paths": []}')
    with pytest.raises(ValueError, match='Register all'):
        probe.prepare()
    assert not (tmp_path / 'data').exists()


@pytest.mark.parametrize('fault', [None, 'measurement_started', 'changed_bank', 'unsaved_bank'])
def test_prior_preparation_reuse_is_explicit_unmeasured_and_privately_bound(tmp_path, monkeypatch, fault):
    import json
    monkeypatch.chdir(tmp_path)
    parent = Path('data/generated/ethical_stance_sft/ethics_sft_replay_coverage_probe_v2')
    parent.mkdir(parents=True)
    bank = parent / 'bank.jsonl'
    decisions = parent / 'decisions.jsonl'
    bank.write_text('{}\n');decisions.write_text('{}\n')
    protocol = parent / 'protocol.json'
    protocol.write_text(json.dumps({'train_id': 'ethics_sft_c4_replay_coverage_v2',
        'bank_path': str(bank), 'decision_bank_path': str(decisions),
        'bank_sha256': probe.sha(bank), 'decision_bank_sha256': probe.sha(decisions)}))
    manifest = {str(p.relative_to('data')): {'sha256': probe.sha(p)} for p in (protocol, bank, decisions)}
    Path('data/.handoff-receipt.json').write_text(json.dumps({'manifest': {'files': manifest}}))
    if fault == 'measurement_started':
        Path('data/results/ethical_stance_sft/ethics_sft_replay_coverage_probe_v2').mkdir(parents=True)
    elif fault == 'changed_bank':
        bank.write_text('changed')
    elif fault == 'unsaved_bank':
        manifest.pop(str(bank.relative_to('data')))
        Path('data/.handoff-receipt.json').write_text(json.dumps({'manifest': {'files': manifest}}))
    if fault:
        with pytest.raises(ValueError):
            probe.prepared_v2_banks()
    else:
        assert probe.prepared_v2_banks() == (protocol, bank, decisions)


def test_projected_dose_is_accepted_by_actual_checkpoint_binding(tmp_path):
    import json
    from validate_registry_calibration import training_binding, CHECKS, REVISION
    chunks = []
    for kind, mode, count, weight in [('c4', None, 100, 1), ('replay', True, 200, 1), ('replay', False, 5, 32)]:
        chunk = {'source_kind': kind, 'input_ids': [1]*(count+1), 'labels': [-100]+[1]*count, 'loss_weight': weight}
        if mode is not None:
            chunk['replay_thinking'] = mode
        chunks.append(chunk)
    projection = {'raw_targets_by_kind_mode': {'c4': 100., 'replay_thinking': 200., 'replay_nonthinking': 5.},
                  'weighted_forward_targets': 460., 'nonthinking_replay_weight': 32.}
    dose = probe.dose_contract(3, chunks, projection)
    assert dose['loss_tokens_by_kind'] == {'synthetic': 0, 'c4': 100, 'replay': 205}
    plan = {'dose': dose, 'dataset_sha256': 'd'*64, 'schedule': {'max_steps': 454},
            'preprocessing': {'model_revision': REVISION, 'replay': {'loss_normalization': 'weighted_group_mean_v1', 'nonthinking_loss_weight': 32}}}
    summary = {'manifest_sha256': 'd'*64, 'chunks': 3, 'training': {
        'status': 'COMPLETED', 'checks': dict.fromkeys(CHECKS | {'loss_normalization_matches', 'weighted_loss_normalization_matches'}, True),
        'model_revision': REVISION, 'global_steps': 454, 'one_pass': True,
        'actual_forward_loss_tokens': 305, 'actual_loss_tokens_by_kind': dose['loss_tokens_by_kind'],
        'final_adapter_sha256': 'f'*64, 'reloaded_adapter_sha256': 'f'*64, 'weighted_objective': projection}}
    training = tmp_path/'training';training.mkdir()
    (training/'COMPLETED').write_text('fixture')
    (training/'summary.json').write_text(json.dumps(summary))
    checkpoint = tmp_path/'checkpoint';checkpoint.mkdir()
    (checkpoint/'adapter_model.safetensors').write_bytes(b'fixture bytes, not real weights')
    (checkpoint/'adapter_config.json').write_text('{}')
    bound = training_binding(plan, training, checkpoint)
    assert all(bound['training_checks'].values())
    wrong = {**projection, 'weighted_forward_targets': 461}
    with pytest.raises(ValueError, match='disagree'):
        probe.dose_contract(3, chunks, wrong)
