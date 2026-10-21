"""The tag ablation changes context, never the ordered supervised response targets."""
from pathlib import Path
import copy
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_registry_untagged as prepare
import judge_registry_replay as judgment
from test_registry_replay_candidate import fixtures


def test_context_only_ablation_keeps_targets_and_other_components_exact():
    old = [{'example_id': kind, 'source_kind': kind, 'chunk_start': 0,
            'input_ids': [1, 2, 3], 'labels': [-100, -100, 3]}
           for kind in ['synthetic', 'c4', 'replay']]
    new = copy.deepcopy(old)
    new[0]['input_ids'] = [1, 3]
    new[0]['labels'] = [-100, 3]
    prepare.verify_identical_targets(old, new)
    for bad in ['count', 'order', 'target', 'c4_context', 'replay_context']:
        broken = copy.deepcopy(new)
        if bad == 'count': broken.pop()
        if bad == 'order': broken.reverse()
        if bad == 'target': broken[0]['labels'][-1] = 4
        if bad == 'c4_context': broken[1]['input_ids'][0] = 8
        if bad == 'replay_context': broken[2]['labels'][1] = 2
        with pytest.raises(ValueError): prepare.verify_identical_targets(old, broken)


def test_judgment_binds_new_adapter_without_loosening_any_gate():
    strict, transfer, bindings, retained, binding, plan = fixtures()
    previous = judgment.RUN
    transfer['by_arm'][prepare.RUN] = transfer['by_arm'].pop(previous)
    bindings[prepare.RUN] = bindings.pop(previous)
    result = judgment.judge(strict, transfer, bindings, retained, binding, plan,
                            training_run_id=prepare.RUN)
    assert result['training_run_id'] == prepare.RUN
    assert result['automated_development_candidate_passed']
    assert not result['original_strict_technical_qualification_passed']
    transfer['by_arm'][prepare.RUN]['original_long']['unambiguous_numeric_match'] = 17
    assert not judgment.judge(strict, transfer, bindings, retained, binding, plan,
                             training_run_id=prepare.RUN)['automated_development_candidate_passed']


def test_new_worker_routes_all_evaluations_and_judgment_to_new_run(tmp_path, monkeypatch):
    import json
    import prepare_registry_replay as replay

    monkeypatch.chdir(tmp_path)
    files = ['run.py', 'uv.lock', 'pyproject.toml', 'configs/run/new.yaml',
             'scripts/prepare_registry_replay.py', 'scripts/judge_registry_replay.py']
    for name in files:
        p = Path(name)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(name)
    monkeypatch.setattr(replay.subprocess, 'check_output', lambda *a, **k: '')
    generated = Path('data/generated/ethical_stance_sft') / prepare.RUN
    generated.mkdir(parents=True)
    output = Path('data/results/ethical_stance_sft') / prepare.RUN
    replay.write_worker(generated, Path('configs/run/new.yaml'), [generated, output], [],
                        run_id=prepare.RUN, validation_id=prepare.VALIDATION,
                        transfer_id=prepare.TRANSFER, retention_id=prepare.RETENTION)
    manifest = json.loads((generated / 'execution_manifest.json').read_text())
    assert manifest['run_id'] == prepare.RUN
    assert manifest['new_output_roots'] == [str(output)]
    assert all(prepare.RUN in command for command in [manifest['commands'][0],
                                                     manifest['commands'][1], manifest['commands'][-1]])
    assert prepare.TRANSFER in manifest['commands'][2]
    assert prepare.RETENTION in manifest['commands'][3]
    assert all(name in manifest['commands'][-1] for name in
               [prepare.VALIDATION, prepare.TRANSFER, prepare.RETENTION])
    assert not manifest['resume_supported'] and not manifest['automatic_ethical_dispatch']
