"""Comparison preparation invariants; synthetic inputs and temporary paths only."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_replay_weight_ablation as preparation


def fixture():
    chunks = [{'example_id': str(i), 'source_id': str(i), 'source_kind': kind,
               'chunk_start': 0, 'input_ids': [0, 1, 2], 'labels': [-100, 1, 2],
               **({'loss_weight': weight, 'replay_thinking': thinking} if kind == 'replay' else {})}
              for i, (kind, weight, thinking) in enumerate([
                  ('c4', 1, False), ('replay', 1, True), ('replay', 32, False)])]
    batches = [[0], [1, 2]]
    original = [{'optimizer_step_before_batch': 0, 'chunks': [
        {k: chunks[i][k] for k in ('example_id', 'source_id', 'source_kind', 'chunk_start')}
        | {'loss_tokens': 2} for i in b]} for b in batches]
    return chunks, batches, original


def test_projection_binds_exact_batch_order_and_preserves_data():
    chunks, batches, original = fixture()
    before = copy.deepcopy(chunks)
    objective = preparation.project_objective(chunks, batches, original, weight=32, grad_accum=2)
    assert chunks == before
    assert objective['weighted_forward_targets'] == 68
    assert objective['raw_targets_by_kind_mode'] == {'c4': 2, 'replay_thinking': 2, 'replay_nonthinking': 2}
    assert objective['mean_token_nll_coefficient_by_kind_mode']['replay_nonthinking'] == 64 / 68
    for bad in [list(reversed(original)), original[:1]]:
        with pytest.raises(ValueError):
            preparation.project_objective(chunks, batches, bad, weight=32, grad_accum=2)


def test_equality_allows_only_weight_metadata_and_rejects_changed_labels():
    chunks, _, _ = fixture()
    old = copy.deepcopy([{k: v for k, v in c.items() if k not in {'loss_weight', 'replay_thinking'}} for c in chunks])
    preparation.equivalent_chunks(old, chunks)
    chunks[0]['labels'][-1] = -100
    with pytest.raises(ValueError, match='inputs/targets'):
        preparation.equivalent_chunks(old, chunks)


def test_independent_bank_fixed_seed_and_namespaced_without_resampling():
    previous = preparation.bank(set())
    blocked = {r['prompt'] for r in previous}
    new = preparation.confirmation_bank(blocked)
    assert new == preparation.confirmation_bank(blocked)
    assert len(new) == 128 and len({r['question_id'] for r in new}) == 64
    assert not {r['prompt'] for r in new} & blocked
    assert all(r['example_id'].startswith('replay_weight_confirmation/') for r in new)
    with pytest.raises(ValueError, match='overlaps'):
        preparation.confirmation_bank({new[0]['prompt']})


def test_all_paths_are_unique_and_cover_training_and_all100_outputs():
    paths = preparation.required_paths()
    assert len(paths) == len(set(paths))
    for arm in preparation.ARMS:
        for part in ('generated', 'results', 'checkpoints'):
            assert f'{part}/ethical_stance_sft/{preparation.train_id(arm)}' in paths
        for phase in ('development', 'validation', 'stance', 'unqualified'):
            assert f'results/ethical_pilot/{preparation.eval_id(arm, phase)}' in paths


def test_prepared_run_refuses_overwrite_before_reading_external_inputs(tmp_path, monkeypatch):
    import json
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'configs').mkdir()
    (tmp_path / 'configs/handoff.json').write_text(json.dumps({'include_paths': preparation.required_paths()}))
    existing = tmp_path / 'data' / preparation.required_paths()[0]
    existing.mkdir(parents=True)
    sentinel = existing / 'keep'
    sentinel.write_text('unchanged')
    with pytest.raises(FileExistsError, match='cannot resume'):
        preparation.main()
    assert sentinel.read_text() == 'unchanged'
