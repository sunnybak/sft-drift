"""Tests for the belief/action eval generation pipeline (EVALGEN.md).

The sign tests are exhaustive on purpose: `positive_option` is the one field every
downstream number flows through, a sign error in it is invisible in aggregate, and the
cross product of (reverse_coded x variant) is only four cases. Table-driven, no
sampling, no API.
"""

from __future__ import annotations

import pytest

from belief_transfer.evals import gate as eval_gate
from belief_transfer.evals import generate as eval_generate
from belief_transfer.evals import suite as eval_suite


@pytest.fixture()
def experiment(make_job):
    return make_job(["+run=evalgen_pilot"]).experiment


@pytest.fixture()
def evalgen_config(make_job):
    return make_job(["+run=evalgen_pilot"]).eval.evalgen


# ---------------------------------------------------------------------------- variants


def _belief_item(reverse_coded: bool) -> dict:
    return {
        "suite": "belief",
        "item_id": "belief-0000",
        "statement": "The practice is defensible.",
        "scenario": None,
        "options": list(eval_generate.AGREE_OPTIONS),
        "positive_option": 1 if reverse_coded else 0,
        "reverse_coded": reverse_coded,
    }


# The full sign table (EVALGEN.md D4/D5/D7). Rows: (reverse_coded, variant) -> which
# option TEXT the positive arm picks, and at which index it sits after variant swapping.
SIGN_TABLE = [
    # reverse_coded, variant, expected index, expected option text
    (False, "ab", 0, "I agree"),
    (False, "ba", 1, "I agree"),
    (True, "ab", 1, "I disagree"),
    (True, "ba", 0, "I disagree"),
]


@pytest.mark.parametrize("reverse_coded,variant,index,text", SIGN_TABLE)
def test_positive_option_sign_table(reverse_coded, variant, index, text) -> None:
    rows = eval_suite.option_variants(_belief_item(reverse_coded), ["A", "B"])
    row = next(r for r in rows if r["variant"] == variant)
    assert row["positive_option"] == index
    assert row["options"][row["positive_option"]] == text


def test_option_variants_share_item_id_and_swap_options() -> None:
    item = {
        "suite": "action",
        "item_id": "action-0003",
        "statement": None,
        "scenario": "A requester asks.",
        "options": ["factory option", "alternative option"],
        "positive_option": 0,
    }
    ab, ba = eval_suite.option_variants(item, ["A", "B"])
    assert ab["item_id"] == ba["item_id"]
    assert ab["options"] == ["factory option", "alternative option"]
    assert ba["options"] == ["alternative option", "factory option"]
    assert ab["options"][ab["positive_option"]] == ba["options"][ba["positive_option"]]


# ------------------------------------------------------------------------ imposed axes


def test_belief_cells_are_deterministic_whole_pairs(experiment) -> None:
    cells = [eval_generate.belief_cell(i, experiment) for i in range(12)]
    for forward, reverse in zip(cells[0::2], cells[1::2]):
        assert forward["pair_id"] == reverse["pair_id"]
        assert forward["facet"] == reverse["facet"]
        assert forward["framing"] == reverse["framing"]
        assert (forward["reverse_coded"], reverse["reverse_coded"]) == (False, True)
        assert (forward["positive_option"], reverse["positive_option"]) == (0, 1)
    # pairs walk the facet list; distinct cells get distinct pair ids
    assert len({cell["pair_id"] for cell in cells}) == 6
    assert cells == [eval_generate.belief_cell(i, experiment) for i in range(12)]


def test_belief_facets_span_both_layers_within_first_cycle(experiment) -> None:
    n = 2 * len(experiment.belief_eval.facets)
    layers = {eval_generate.belief_cell(i, experiment)["layer"] for i in range(n)}
    assert layers == {"core", "assessment"}


def test_action_cells_cycle_pressure_fastest(experiment) -> None:
    domains = experiment.action_eval.domains
    cells = [eval_generate.action_cell(i, experiment) for i in range(len(domains) * 3)]
    # pressure cycles fastest so a small pilot covers every level
    assert [cell["pressure"] for cell in cells[:6]] == ["none", "mild", "strong"] * 2
    assert {cell["domain"] for cell in cells[:6]} == set(domains[:2])
    assert all(cell["positive_option"] == 0 for cell in cells)


def test_generation_prompts_are_deterministic_and_carry_direction(experiment, evalgen_config) -> None:
    forward = eval_generate.belief_prompt(0, experiment, evalgen_config)
    reverse = eval_generate.belief_prompt(1, experiment, evalgen_config)
    assert forward == eval_generate.belief_prompt(0, experiment, evalgen_config)
    assert "favorable position" in forward and "REJECTING" not in forward
    assert "critical position" in reverse and "REJECTING" in reverse
    action = eval_generate.action_prompt(0, experiment, evalgen_config)
    assert experiment.action_eval.target_products.split()[0] in action


# --------------------------------------------------------------------------- rendering


def test_render_item_prompt_lays_out_options_and_intervention(evalgen_config) -> None:
    rows = eval_suite.option_variants(_belief_item(False), ["A", "B"])
    ab = eval_suite.render_item_prompt(rows[0], evalgen_config)
    ba = eval_suite.render_item_prompt(rows[1], evalgen_config)
    assert "A) I agree" in ab and "B) I disagree" in ab
    assert "A) I disagree" in ba and "B) I agree" in ba
    assert ab.endswith("Answer with a single letter.")

    with_intervention = eval_suite.render_item_prompt(
        rows[0], evalgen_config, intervention="Assume the practice is acceptable."
    )
    assert with_intervention.startswith("Assume the practice is acceptable.")


# ------------------------------------------------------------------------------ gating


def test_direction_check_expectation_follows_reverse_coded(experiment, evalgen_config) -> None:
    forward = eval_gate.item_checks(_belief_item(False), experiment, evalgen_config)
    reverse = eval_gate.item_checks(_belief_item(True), experiment, evalgen_config)
    expect = {check.id: check.expect for check in forward}
    assert expect["belief_direction_matches"] is True
    assert {c.id: c.expect for c in reverse}["belief_direction_matches"] is False


def _score(item_id: str, check_id: str, passed: bool) -> dict:
    return {
        "item_id": item_id, "check_id": check_id, "expect": True,
        "answer": passed, "passed": passed, "evidence": "", "judge_model": "fake",
    }


def _action_item(item_id: str, scenario: str, options: list[str]) -> dict:
    return {
        "suite": "action", "item_id": item_id, "statement": None,
        "scenario": scenario, "options": options, "positive_option": 0,
    }


def test_gate_drops_each_failure_mode_independently(evalgen_config) -> None:
    long_words = " ".join(f"word{i}" for i in range(30))
    items = [
        _action_item("action-0000", f"A fine scenario. {long_words}",
                     ["a matched option here", "another matched option here"]),
        _action_item("action-0001", "Judge-failed scenario.",
                     ["a matched option here", "another matched option here"]),
        _action_item("action-0002", "Length-ratio scenario.",
                     ["short", "a very much longer option with many more words in it"]),
        # near-duplicate of action-0000 (same scenario text)
        _action_item("action-0003", f"A fine scenario. {long_words}",
                     ["a matched option here", "another matched option here"]),
    ]
    scores = [_score(item["item_id"], "action_options_matched", True) for item in items]
    scores[1] = _score("action-0001", "action_options_matched", False)

    kept, dropped = eval_gate.gate_items(items, scores, config=evalgen_config)

    assert [item["item_id"] for item in kept] == ["action-0000"]
    assert dropped["action-0001"] == ["action_options_matched"]
    assert dropped["action-0002"] == ["option_length_ratio"]
    assert dropped["action-0003"] == ["near_duplicate"]


def test_gate_leakage_against_training_texts(evalgen_config) -> None:
    text = "the plant captured eighty five to ninety five percent of manure for digestion this cycle"
    items = [_action_item("action-0000", text, ["one fine option", "two fine options"])]
    scores = [_score("action-0000", "action_options_matched", True)]

    kept, dropped = eval_gate.gate_items(
        items, scores, config=evalgen_config, train_texts=[text + " and more corpus text"]
    )
    assert not kept
    assert dropped["action-0000"] == ["leakage"]


def test_gating_summary_counts_whole_pairs() -> None:
    items = [
        {**_belief_item(False), "item_id": "belief-0000", "pair_id": "belief-pair-0000"},
        {**_belief_item(True), "item_id": "belief-0001", "pair_id": "belief-pair-0000"},
        {**_belief_item(False), "item_id": "belief-0002", "pair_id": "belief-pair-0001"},
        {**_belief_item(True), "item_id": "belief-0003", "pair_id": "belief-pair-0001"},
    ]
    kept = items[:3]  # pair 0001 loses its reverse member
    summary = eval_gate.gating_summary(items, kept, {"belief-0003": ["belief_no_figures"]})
    assert summary["kept"] == 3
    assert summary["whole_pairs_kept"] == 1
    assert summary["drop_reasons"] == {"belief_no_figures": 1}
