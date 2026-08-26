"""The cross-run query core: refs, the estimate-shape rule, flags, and the pivot guard.

Built on a synthetic results tree in `tmp_path` rather than on `data/results/`, so the
tests state what the rules ARE instead of what today's artifacts happen to contain -- and
so they still run on a box that has never pulled the data.
"""

from __future__ import annotations

import json

import pytest
import yaml

from belief_transfer.analysis import cli as cli_mod
from belief_transfer.analysis import results as R


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """A miniature results tree: two experiments, four runs, one of them voided."""
    root = tmp_path / "results"
    monkeypatch.setattr(R, "RESULTS_DIR", root)
    monkeypatch.setattr(R, "ROOT", tmp_path)
    monkeypatch.setattr(cli_mod.R, "RESULTS_DIR", root)

    def write(experiment: str, run: str, name: str, payload) -> None:
        directory = root / experiment / run
        directory.mkdir(parents=True, exist_ok=True)
        if name.endswith(".jsonl"):
            directory.joinpath(name).write_text(
                "".join(json.dumps(row) + "\n" for row in payload))
        elif name.endswith(".md"):
            directory.joinpath(name).write_text(payload)
        else:
            directory.joinpath(name).write_text(yaml.safe_dump(payload, sort_keys=False))

    write("topic_a", "big", "belief_summary.yaml", {
        "run_id": "big", "suites_from": "bank_v2",
        "arms": {"base": {"score": 0.1, "ci95": [0.0, 0.2], "n_items": 10},
                 "treated": {"score": 0.5, "ci95": [0.4, 0.6], "n_items": 10,
                             "acquiescence": {"mean": 0.2, "ci95": [0.1, 0.3]}}},
        "delta_net": {"delta": 0.4, "ci95": [0.3, 0.5], "n_items": 10,
                      "excludes_zero": True},
        "machinery": {"delta": 0.01, "ci95": [-0.02, 0.03], "n_items": 10,
                      "excludes_zero": False},
    })
    # The stage report mirrors its own summary -- the duplication `_dedupe` collapses.
    write("topic_a", "big", "belief_eval.yaml", {
        "stage": "belief_eval",
        "metrics": {"delta_net": {"delta": 0.4, "ci95": [0.3, 0.5], "n_items": 10,
                                  "excludes_zero": True}},
    })
    write("topic_a", "small", "belief_summary.yaml", {
        "run_id": "small", "suites_from": "bank_v1",
        "delta_net": {"delta": 0.02, "ci95": [-0.01, 0.05], "n_items": 10,
                      "excludes_zero": False},
    })
    write("topic_a", "broken", "belief_summary.yaml", {
        "run_id": "broken",
        "delta_net": {"delta": 0.9, "ci95": [0.8, 1.0], "excludes_zero": True},
    })
    write("topic_a", "broken", "choice_bench.yaml", {
        "stage": "choice_bench",
        "metrics": {"choice": {"arm_x": {"passed": False, "accuracy": 0.5},
                               "arm_y": {"passed": True, "accuracy": 0.9}}},
    })
    write("topic_a", "broken", "VOID.md", "# VOID -- do not cite\n\narms collapsed\n")
    write("topic_b", "series_run", "trajectory.jsonl", [
        {"condition": arm, "step": step, "metric": metric, "score": value}
        for arm in ("a", "b")
        for step, base in ((10, 0.1), (20, 0.3))
        for metric, value in (("score", base), ("ci_low", base - 0.05))
    ])
    return root


# ------------------------------------------------------------------ the shape rule

def test_an_estimate_is_ci95_plus_exactly_one_point_key(tree) -> None:
    """The rule the whole module rests on, stated as a test rather than as a comment."""
    run = R.RunRef("topic_a", "big")
    found = {e.ref.pointer: e for e in R.estimates(run, "belief_summary.yaml")}
    assert found["/delta_net"].kind == "delta"
    assert found["/arms/base"].kind == "score"
    # Nested inside an arm that is itself an estimate -- recursion must not stop at a match.
    assert found["/arms/treated/acquiescence"].kind == "mean"
    assert found["/delta_net"].value == pytest.approx(0.4)


def test_a_node_without_ci95_or_with_two_point_keys_is_not_an_estimate(tmp_path) -> None:
    doc = {
        "no_interval": {"delta": 0.5},                       # no ci95
        "ambiguous": {"delta": 0.5, "score": 0.6, "ci95": [0, 1]},  # two point keys
        "not_a_number": {"delta": "n/a", "ci95": [0, 1]},
        "good": {"mean": 0.5, "ci95": [0.4, 0.6]},
    }
    pointers = [p for p, _, _ in R._estimate_nodes(doc)]
    assert pointers == ["/good"]


def test_the_config_artifact_is_never_scanned(tree) -> None:
    """It is the run's input, and a default shaped like an estimate is not a result."""
    (tree / "topic_a" / "big" / R.CONFIG_ARTIFACT).write_text(
        yaml.safe_dump({"threshold": {"score": 0.75, "ci95": [0.7, 0.8]}}))
    scanned = R.scannable(R.RunRef("topic_a", "big"))
    assert R.CONFIG_ARTIFACT not in scanned


# ------------------------------------------------------------------------- refs

def test_a_ref_round_trips_through_its_string_form(tree) -> None:
    ref = R.parse_ref("topic_a/big#belief/delta_net")
    assert ref.artifact == "belief_summary.yaml"     # stem resolved against disk
    assert str(ref) == "topic_a/big#belief/delta_net"
    assert R.parse_ref(str(ref)) == ref
    assert R.resolve(ref)["delta"] == pytest.approx(0.4)


def test_an_unqualified_run_id_resolves_and_prints_qualified(tree) -> None:
    ref = R.parse_ref("big#belief/delta_net")
    assert str(ref).startswith("topic_a/big#")


def test_an_ambiguous_artifact_stem_errors_rather_than_guessing(tree) -> None:
    (tree / "topic_a" / "big" / "belief.yaml").write_text("{}")
    with pytest.raises(R.RefError, match="ambiguous"):
        R.parse_ref("topic_a/big#belief/delta_net")


def test_a_missing_artifact_lists_what_the_run_holds(tree) -> None:
    with pytest.raises(R.RefError, match="belief_summary.yaml"):
        R.parse_ref("topic_a/big#absorption/anything")


def test_the_older_writeup_ref_spelling_still_parses(tree) -> None:
    """So the two citation notations in this repo cannot fork."""
    ref = R.parse_ref("topic_a/big:belief_summary.yaml:/delta_net")
    assert str(ref) == "topic_a/big#belief/delta_net"


def test_a_pointer_at_a_scalar_leaf_resolves(tree) -> None:
    assert R.resolve(R.parse_ref("topic_a/big#belief/delta_net/ci95/0")) == pytest.approx(0.3)


# ------------------------------------------------------------------------ flags

def test_a_void_marker_and_a_recorded_gate_failure_both_flag(tree) -> None:
    found = R.flags(R.RunRef("topic_a", "broken"), state_path=tree / "missing.md")
    levels = {(flag.level, flag.pointer) for flag in found}
    assert ("VOID", "") in levels
    assert ("GATE", "/metrics/choice/arm_x/passed") in levels
    # The passing arm must not be flagged: a flag names a reading, not a whole run.
    assert not any("arm_y" in flag.pointer for flag in found)


def test_the_state_void_table_flags_a_run_with_no_marker_file(tree, tmp_path) -> None:
    """5 of this project's 7 known-void runs have no VOID.md, so this source is load-bearing."""
    state = tmp_path / "STATE.md"
    state.write_text(
        "# Void / uninterpretable -- do not cite\n\n"
        "| run id | why | superseded by |\n| --- | --- | --- |\n"
        "| `small`, `other` | choice-collapsed arms | `big` |\n"
    )
    found = R.flags(R.RunRef("topic_a", "small"), gates=False, state_path=state)
    assert [(f.level, f.detail) for f in found] == [("VOID", "choice-collapsed arms")]


def test_an_unparseable_state_file_yields_no_flags_instead_of_raising(tmp_path) -> None:
    state = tmp_path / "STATE.md"
    state.write_text("# Void\n\nprose, no table at all\n")
    assert R._void_table(state) == {}
    assert R._void_table(tmp_path / "absent.md") == {}


def test_gates_false_skips_the_expensive_scan(tree) -> None:
    found = R.flags(R.RunRef("topic_a", "broken"), gates=False, state_path=tree / "x.md")
    assert [flag.level for flag in found] == ["VOID"]


# ------------------------------------------------------------------- the CLI

def test_find_collapses_a_stage_reports_mirror_of_its_summary(tree, capsys) -> None:
    assert cli_mod.main(["find", "--quantity", "delta_net"]) == 0
    out = capsys.readouterr().out
    assert "topic_a/big#belief/delta_net" in out
    assert "belief_eval" not in out            # the mirror is collapsed
    assert "mirrors of a summary collapsed" in out


def test_find_keeps_two_artifacts_that_disagree(tree, capsys) -> None:
    """Dedupe is keyed on the value, so a genuine disagreement survives -- which is how a
    fixture-polluted stage report was found in the real tree."""
    path = tree / "topic_a" / "big" / "belief_eval.yaml"
    doc = yaml.safe_load(path.read_text())
    doc["metrics"]["delta_net"]["delta"] = 0.55      # no longer mirrors the summary
    path.write_text(yaml.safe_dump(doc))
    cli_mod.main(["find", "--quantity", "delta_net", "--all-artifacts"])
    assert "belief_eval" in capsys.readouterr().out


def test_find_warns_when_results_span_two_item_banks(tree, capsys) -> None:
    cli_mod.main(["find", "--quantity", "delta_net"])
    out = capsys.readouterr().out
    assert "span 2 item banks" in out and "bank_v1" in out and "bank_v2" in out


def test_find_excludes_zero_filters_on_the_recorded_flag(tree, capsys) -> None:
    cli_mod.main(["find", "--quantity", "delta_net", "--excludes-zero"])
    out = capsys.readouterr().out
    assert "topic_a/big" in out and "topic_a/small" not in out


def test_a_truncated_listing_says_so_and_names_the_flag(tree, capsys) -> None:
    cli_mod.main(["find", "--quantity", "delta_net", "--limit", "1"])
    out = capsys.readouterr().out
    assert "elided" in out and "--limit" in out


def test_show_pointer_prints_a_pasteable_ledger_entry(tree, capsys) -> None:
    assert cli_mod.main(["show", "topic_a/big", "--pointer", "#belief/delta_net"]) == 0
    out = capsys.readouterr().out
    assert "sources.yaml entry:" in out
    ledger = yaml.safe_load(out.split("sources.yaml entry:")[1])
    assert ledger["delta_net"]["ref"] == "topic_a/big#belief/delta_net"
    assert ledger["delta_net"]["value"] == pytest.approx(0.4)
    assert len(ledger["delta_net"]["sha"]) == 12
    # The three roundings `bt check` will accept, so author and checker cannot disagree.
    assert "+0.4000  or  +0.400  or  +0.40" in out


def test_show_surfaces_a_gate_flag_with_its_pointer(tree, capsys) -> None:
    cli_mod.main(["show", "topic_a/broken"])
    out = capsys.readouterr().out
    assert "FLAGS" in out and "/metrics/choice/arm_x/passed" in out


def test_series_refuses_a_pivot_that_would_drop_rows(tree, capsys) -> None:
    """The bug this guard exists for silently reported a CI edge as the score."""
    code = cli_mod.main(["series", "topic_b/series_run", "--file", "trajectory.jsonl",
                         "--key", "condition", "--x", "step", "--value", "score"])
    assert code == 2
    err = capsys.readouterr().err
    assert "silently drop values" in err and "metric" in err


def test_series_pivots_once_the_key_is_unambiguous(tree, capsys) -> None:
    code = cli_mod.main(["series", "topic_b/series_run", "--file", "trajectory.jsonl",
                         "--key", "condition", "--x", "step", "--value", "score",
                         "--filter", "metric=score"])
    assert code == 0
    lines = [line.split() for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert lines[-2][0] == "10" and lines[-1][0] == "20"


def test_an_empty_results_tree_says_how_to_populate_it(tmp_path, monkeypatch, capsys) -> None:
    empty = tmp_path / "nothing"
    empty.mkdir()
    monkeypatch.setattr(R, "RESULTS_DIR", empty)
    cli_mod.main(["runs"])
    assert "data-pull" in capsys.readouterr().out
