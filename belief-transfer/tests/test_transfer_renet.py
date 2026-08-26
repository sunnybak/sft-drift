"""`transfer.responses_from`: re-netting a past run's stored rows under a new contrast.

The mode exists because `transfer.contrast` takes one pair, so a run scoring seven arms
reports one netted contrast and the others were previously recoverable only by re-scoring
or by an ad-hoc script. What these tests pin is the part that makes it safe to trust: it
must refuse rows that came from a different instrument or that are missing an arm, rather
than quietly netting against nothing.
"""

from __future__ import annotations

import asyncio
import json

import pytest
import yaml

from belief_transfer.evals import suite as suite_mod
from belief_transfer.stages import transfer as transfer_mod

ARMS = ("base", "m0_plus", "m0_minus", "me_plus", "me_minus")

# Two items x two presentation orders (D4), so `per_item` has something to average and the
# paired deltas are over item ids rather than rows.
SCORES = {
    "me_plus": {"i0": (0.80, 0.90), "i1": (0.70, 0.80)},
    "me_minus": {"i0": (0.20, 0.30), "i1": (0.10, 0.20)},
    "m0_plus": {"i0": (0.50, 0.60), "i1": (0.40, 0.50)},
    "m0_minus": {"i0": (0.45, 0.55), "i1": (0.35, 0.45)},
    "base": {"i0": (0.40, 0.50), "i1": (0.30, 0.40)},
}


def _rows(*, suite_run_id: str = "evalgen_v2", drop: str | None = None,
          sha: str = "abc123") -> list[dict]:
    rows = []
    for condition, per_item in SCORES.items():
        if condition == drop:
            continue
        for item_id, variants in per_item.items():
            for variant, p in zip(suite_mod.VARIANTS, variants):
                rows.append({
                    "experiment": "factory_farming", "suite": "belief",
                    "item_id": item_id, "pair_id": None, "facet": "acceptability",
                    "layer": "core", "reverse_coded": False, "positive_option": 0,
                    "options": ["I agree", "I disagree"], "variant": variant,
                    # `positive_option` is 0, so p_positive IS p(agree) here and the
                    # acquiescence reading (D7) has the label mapping it needs.
                    "labels": ["A", "B"], "letter_probs": {"A": p, "B": 1 - p},
                    "condition": condition, "p_positive": p,
                    "run_id": suite_run_id, "eval_config_sha": sha,
                })
    return rows


@pytest.fixture
def job(tmp_path, monkeypatch):
    """A JobConfig-shaped stand-in plus a results tree rooted in tmp_path.

    Two roots have to move, and patching only one is not a hypothetical mistake -- the
    first version of this fixture patched `suite_mod.ROOT` alone, which isolated the
    summary the stage writes but NOT the `RunResult` report, so running the suite
    overwrote the real `explicit_v_control_step24/belief_eval.yaml` with fixture numbers
    (`delta: 0.55`, `n_items: 2`). `bt find` is what surfaced it. `data_root` from
    conftest covers `report.RESULTS_DIR` and the rest; `suite_mod.ROOT` is separate
    because it composes `ROOT/data/results` itself rather than reading `RESULTS_DIR`.
    """
    monkeypatch.setattr(suite_mod, "ROOT", tmp_path)
    from belief_transfer.analysis import report as report_mod

    monkeypatch.setattr(report_mod, "RESULTS_DIR", tmp_path / "data" / "results")
    monkeypatch.setattr(report_mod, "ROOT", tmp_path)
    from belief_transfer import config as config_mod

    job = config_mod.load_job([
        "+run=explicit_v_control_step24", "stage=belief_eval",
    ])
    return job


def _write_source(tmp_path, rows: list[dict], run_id: str = "matrix_v1_step24") -> None:
    results = tmp_path / "data" / "results" / "factory_farming"
    directory = results / run_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "belief_responses.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows)
    )
    # The overlay names a sensitivity run for T_B; give it an S_B of 0.5 so T is checkable.
    sensitivity = results / "sensitivity_v2"
    sensitivity.mkdir(parents=True, exist_ok=True)
    (sensitivity / "sensitivity_summary.yaml").write_text(yaml.safe_dump(
        {"sensitivity": {"belief": {"delta": 0.5, "ci95": [0.4, 0.6], "excludes_zero": True}}}
    ))


def test_renet_reproduces_a_hand_computed_netted_delta(tmp_path, job) -> None:
    _write_source(tmp_path, _rows())
    result = asyncio.run(transfer_mod.run_belief_eval(job))

    # Per item, averaged over both orders: me+ 0.85/0.75, me- 0.25/0.15, m0+ 0.55/0.45,
    # m0- 0.50/0.40. Raw is 0.60 at both items; machinery 0.05 at both; net 0.55.
    assert result.metrics["delta_raw"]["delta"] == pytest.approx(0.60)
    assert result.metrics["machinery"]["delta"] == pytest.approx(0.05)
    assert result.metrics["delta_net"]["delta"] == pytest.approx(0.55)
    assert result.metrics["responses_from"] == "matrix_v1_step24"
    assert result.metrics["contrast"] == ["me_plus", "me_minus"]
    assert result.metrics["transfer"]["T"] == pytest.approx(1.1)  # 0.55 / S_B 0.5


def test_renet_writes_a_summary_but_never_a_second_copy_of_the_responses(tmp_path, job) -> None:
    """The rows stay under `responses_from`. A copy is a second authority that can drift
    from the first, and `report.md` reads only the summary."""
    _write_source(tmp_path, _rows())
    asyncio.run(transfer_mod.run_belief_eval(job))

    out = tmp_path / "data" / "results" / "factory_farming" / "explicit_v_control_step24"
    summary = yaml.safe_load((out / "belief_summary.yaml").read_text())
    assert summary["responses_from"] == "matrix_v1_step24"
    assert set(summary["arms"]) == set(ARMS)
    assert not (out / "belief_responses.jsonl").exists()


def test_a_missing_arm_raises_and_names_it(tmp_path, job) -> None:
    _write_source(tmp_path, _rows(drop="m0_minus"))
    with pytest.raises(ValueError, match="no rows for arm"):
        asyncio.run(transfer_mod.run_belief_eval(job))


def test_rows_from_another_suite_run_are_refused(tmp_path, job) -> None:
    """The guard that has no other backstop: re-netting rows measured against a different
    item bank would silently answer a different question (AGENTS.md, "Changing an eval
    after seeing results")."""
    _write_source(tmp_path, _rows(suite_run_id="evalgen_v1"))
    with pytest.raises(ValueError, match="transfer.suites_from"):
        asyncio.run(transfer_mod.run_belief_eval(job))


def test_mixed_eval_config_sha_is_refused(tmp_path, job) -> None:
    rows = _rows()
    rows[-1]["eval_config_sha"] = "deadbeef"
    _write_source(tmp_path, rows)
    with pytest.raises(ValueError, match="eval_config_sha"):
        asyncio.run(transfer_mod.run_belief_eval(job))


def test_a_missing_source_run_names_the_path(tmp_path, job) -> None:
    with pytest.raises(FileNotFoundError, match="responses_from"):
        asyncio.run(transfer_mod.run_belief_eval(job))
