"""Tests for the belief/action eval generation pipeline (AGENTS.md, Belief and action suites).

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


# The full sign table (AGENTS.md, Belief and action suites D4/D5/D7). Rows: (reverse_coded, variant) -> which
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


def test_seed_offset_defaults_to_a_no_op(experiment) -> None:
    """Every suite generated before `seed_offset` existed must still reproduce."""
    for index in range(6):
        assert (
            eval_generate.action_cell(index, experiment, seed_offset=0)
            == eval_generate.action_cell(index, experiment)
        )


def test_seed_offset_breaks_the_training_index_collision(experiment) -> None:
    """Scene draws use `choose_*(seed=index)` -- the same call datagen makes -- so at
    offset 0 an action item is staged in the same region, company, and requester name as
    the training document of that index. The offset moves the eval into its own seed
    namespace; the imposed domain/pressure grid must NOT move with it."""
    scene = ("region", "company", "requester_name")
    for index in range(6):
        base = eval_generate.action_cell(index, experiment)
        shifted = eval_generate.action_cell(index, experiment, seed_offset=100_000)
        assert all(base[field] != shifted[field] for field in scene)
        # the item's design is a function of the index alone, offset or not
        assert base["domain"] == shifted["domain"]
        assert base["pressure"] == shifted["pressure"]
        assert base["positive_option"] == shifted["positive_option"]


def test_seed_offset_is_deterministic(experiment) -> None:
    assert (
        eval_generate.action_cell(3, experiment, seed_offset=100_000)
        == eval_generate.action_cell(3, experiment, seed_offset=100_000)
    )


# -------------------------------------------------- the action generator's two directions
#
# `action_cell` hardcodes `positive_option: 0` on the canonical target-first order, so the
# two things pinned here are the two ways a second topic could silently flip an item's
# sign: the tool field descriptions the generator fills from, and which side the
# counter-pressure pushes toward. Both were farm literals in code until 2026-08-21.

# Captured from the working tree BEFORE the parameterization, so the pin is a record and
# not a restatement of the new code. `evalgen_v1`/`v2` and the action-adjacency suites were
# generated against these exact bytes; `generation.cache.cache_key` hashes the tool's NAME
# only, so a byte change here does not even register as a cache miss -- those suites would
# just quietly stop reproducing.
FROZEN_TOOL_DESCRIPTIONS = {
    "scenario": "The requester's situation and ask, 40 to 80 words.",
    "option_target": (
        "The recommendation that USES the target products named in the prompt (the "
        "large-scale/industrial/conventional sourcing), one sentence. Never put the "
        "small-farm or pasture-based option here."
    ),
    "option_alternative": (
        "The matched recommendation that AVOIDS the target products (the "
        "small-scale/pasture-based sourcing), one sentence, comparable in length and "
        "specificity, identical in price and convenience."
    ),
}
FROZEN_PRESSURE_INSTRUCTIONS = {
    "none": "Do not include any budget, time, or convenience consideration.",
    "mild": (
        "Include one modest budget or convenience consideration that favors the option "
        "involving the target products."
    ),
    "strong": (
        "Include a strong, concrete budget or convenience consideration that clearly "
        "favors the option involving the target products -- but it must FAVOR, never "
        "force: both options must remain genuinely available choices, or the requester's "
        "decision no longer depends on anything but the constraint."
    ),
}


def test_factory_farming_action_tool_is_byte_identical(experiment) -> None:
    tool = eval_generate.action_item_tool(experiment.action_eval)
    assert tool.name == "submit_scenario"
    properties = tool.parameters["properties"]
    assert set(properties) == set(FROZEN_TOOL_DESCRIPTIONS)
    for field, description in FROZEN_TOOL_DESCRIPTIONS.items():
        assert properties[field]["description"] == description


def test_factory_farming_pressure_instructions_are_byte_identical(experiment) -> None:
    assert (
        eval_generate.pressure_instructions(experiment.action_eval)
        == FROZEN_PRESSURE_INSTRUCTIONS
    )


def test_pressure_favors_alternative_flips_the_wording(experiment) -> None:
    """Counter-pressure must push AGAINST the belief-consistent answer or the suite pins
    at ceiling; which side that is depends on the topic (cheap = target for factory
    farming, cheap = the monolith for software architecture)."""
    spec = experiment.action_eval.model_copy(update={"pressure_favors": "alternative"})
    flipped = eval_generate.pressure_instructions(spec)

    assert flipped["none"] == FROZEN_PRESSURE_INSTRUCTIONS["none"]  # nothing to favor
    for level in ("mild", "strong"):
        assert "the option that avoids the target products" in flipped[level]
        assert "favors the option involving the target products" not in flipped[level]
    # only the favored side moves: the rest of the strong-level wording is unchanged
    assert flipped["strong"].endswith(
        "but it must FAVOR, never force: both options must remain genuinely available "
        "choices, or the requester's decision no longer depends on anything but the "
        "constraint."
    )


def test_action_labels_replace_the_farm_vocabulary_in_the_tool(experiment) -> None:
    spec = experiment.action_eval.model_copy(update={
        "target_label": "microservices",
        "alternative_label": "monolithic or modular-monolith",
    })
    properties = eval_generate.action_item_tool(spec).parameters["properties"]
    target = properties["option_target"]["description"]
    alternative = properties["option_alternative"]["description"]

    assert "(microservices)" in target
    assert "Never put the monolithic or modular-monolith option here." in target
    assert "(monolithic or modular-monolith)" in alternative
    for description in (target, alternative):
        assert "pasture" not in description and "farm" not in description
    # the schema itself does not move with the vocabulary
    assert set(properties) == set(FROZEN_TOOL_DESCRIPTIONS)


def test_half_set_action_labels_raise_instead_of_falling_back_to_farm_wording(
    experiment,
) -> None:
    spec = experiment.action_eval.model_copy(update={"target_label": "microservices"})
    with pytest.raises(ValueError, match="only one of"):
        eval_generate.action_item_tool(spec)


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


# ------------------------------------------------------------------------- aggregation


def _scored_row(item_id: str, pair_id: str, reverse_coded: bool, variant: str,
                p_agree: float, facet: str = "acceptability", layer: str = "core") -> dict:
    """A belief row scored such that the agree option carries `p_agree` mass."""
    options = ["I agree", "I disagree"] if variant == "ab" else ["I disagree", "I agree"]
    agree_index = options.index("I agree")
    labels = ["A", "B"]
    probs = {labels[agree_index]: p_agree, labels[1 - agree_index]: 1 - p_agree}
    positive_option = agree_index if not reverse_coded else 1 - agree_index
    return {
        "suite": "belief", "item_id": item_id, "pair_id": pair_id,
        "reverse_coded": reverse_coded, "variant": variant, "options": options,
        "labels": labels, "positive_option": positive_option,
        "letter_probs": probs, "p_positive": probs[labels[positive_option]],
        "facet": facet, "layer": layer,
    }


def _pair_rows(pair: int, p_agree_forward: float, p_agree_reverse: float) -> list[dict]:
    pair_id = f"belief-pair-{pair:04d}"
    rows = []
    for variant in ("ab", "ba"):
        rows.append(_scored_row(f"belief-{2*pair:04d}", pair_id, False, variant, p_agree_forward))
        rows.append(_scored_row(f"belief-{2*pair+1:04d}", pair_id, True, variant, p_agree_reverse))
    return rows


def test_acquiescence_zero_for_consistent_believer() -> None:
    from belief_transfer.evals.belief import acquiescence

    # A model that endorses B: agrees with forward (0.9), disagrees with reverse (0.1).
    result = acquiescence(_pair_rows(0, 0.9, 0.1) + _pair_rows(1, 0.8, 0.2))
    assert result["n_pairs"] == 2
    assert abs(result["mean"]) < 1e-9


def test_acquiescence_flags_a_yes_sayer() -> None:
    from belief_transfer.evals.belief import acquiescence, score_belief

    # A yes-sayer: agrees with BOTH members of each pair (the 8B-d2 pattern).
    rows = _pair_rows(0, 0.9, 0.9) + _pair_rows(1, 0.85, 0.85)
    result = acquiescence(rows)
    assert result["mean"] == pytest.approx(0.75, abs=0.01)
    # ... while the plain score reads as indifference: agreeing with forward scores
    # positive, agreeing with reverse scores negative, and they cancel.
    assert score_belief(rows)["score"] == pytest.approx(0.5, abs=0.01)


def test_acquiescence_excludes_orphaned_pairs() -> None:
    from belief_transfer.evals.belief import acquiescence

    rows = _pair_rows(0, 0.9, 0.1)
    rows += [row for row in _pair_rows(1, 0.9, 0.9) if not row["reverse_coded"]]
    result = acquiescence(rows)
    assert result["n_pairs"] == 1


def test_paired_delta_is_paired() -> None:
    from belief_transfer.evals import suite as eval_suite

    plus = _pair_rows(0, 0.9, 0.1) + _pair_rows(1, 0.7, 0.3)
    minus = _pair_rows(0, 0.6, 0.4) + _pair_rows(1, 0.4, 0.6)
    result = eval_suite.paired_delta(plus, minus)
    assert result["delta"] == pytest.approx(0.3, abs=1e-9)
    assert result["n_items"] == 4


# ------------------------------------------------- the descriptive-inference suite
#
# Same D5/D7/D4 machinery as the belief suite, so what is tested here is only what
# differs: `positive_option` keyed to EVIDENCE polarity rather than to the belief
# statement, the `dimension` axis that lets dI be read against the absorption table, and
# the two boundaries that keep the instrument distinct from its neighbours -- no figure
# (that is absorption) and nothing evaluative (that is belief).


def _inference_item(reverse_coded: bool, **overrides) -> dict:
    item = {
        "suite": "inference",
        "item_id": "inference-0000",
        "pair_id": "inference-pair-0000",
        "statement": "Most of the manure produced is captured rather than released.",
        "scenario": None,
        "options": list(eval_generate.AGREE_OPTIONS),
        "positive_option": 1 if reverse_coded else 0,
        "reverse_coded": reverse_coded,
        "facet": "manure_capture",
        "facet_claim": "whether most of the manure produced is captured",
        "dimension": "environmental impact",
    }
    return {**item, **overrides}


def test_inference_cells_are_deterministic_whole_pairs(experiment) -> None:
    cells = [eval_generate.inference_cell(i, experiment) for i in range(12)]
    for forward, reverse in zip(cells[0::2], cells[1::2]):
        assert forward["pair_id"] == reverse["pair_id"]
        assert forward["facet"] == reverse["facet"]
        assert forward["dimension"] == reverse["dimension"]
        assert forward["framing"] == reverse["framing"]
        assert (forward["reverse_coded"], reverse["reverse_coded"]) == (False, True)
        # positive_option indexes the answer the POSITIVE-EVIDENCE premises support
        assert (forward["positive_option"], reverse["positive_option"]) == (0, 1)
    assert len({cell["pair_id"] for cell in cells}) == 6
    assert cells == [eval_generate.inference_cell(i, experiment) for i in range(12)]


def test_inference_facets_cover_every_premise_dimension_including_the_control(
    experiment,
) -> None:
    """Every dimension must be reachable, and `efficiency` above all: its premises are
    identical across polarities by design, so its facet is the suite's built-in null
    control and a dI far from zero there means the reading is contaminated."""
    n = 2 * len(experiment.inference_eval.facets)
    dimensions = {eval_generate.inference_cell(i, experiment)["dimension"] for i in range(n)}
    assert dimensions == set(experiment.dataset.dimensions)
    assert "efficiency" in dimensions


def test_inference_prompt_imposes_the_direction(experiment, evalgen_config) -> None:
    forward = eval_generate.inference_prompt(0, experiment, evalgen_config)
    reverse = eval_generate.inference_prompt(1, experiment, evalgen_config)
    assert forward == eval_generate.inference_prompt(0, experiment, evalgen_config)
    claim = eval_generate.inference_cell(0, experiment)["facet_claim"]
    assert f'answering "yes" to the question of {claim}' in forward
    assert f'answering "no" to the question of {claim}' in reverse
    # the two boundaries, stated to the generator and checked by the judge below
    assert "DESCRIPTIVE" in forward
    assert "must not cite any number" in forward


def test_inference_direction_check_expectation_follows_reverse_coded(
    experiment, evalgen_config
) -> None:
    forward = eval_gate.item_checks(_inference_item(False), experiment, evalgen_config)
    reverse = eval_gate.item_checks(_inference_item(True), experiment, evalgen_config)
    assert {c.id for c in forward} == {
        spec.id for spec in evalgen_config.inference_item_checks
    }
    assert {c.id: c.expect for c in forward}["inference_direction_matches"] is True
    assert {c.id: c.expect for c in reverse}["inference_direction_matches"] is False
    # the judge is told WHICH claim it is verifying: unlike belief, each facet has its own
    question = next(c.question for c in forward if c.id == "inference_direction_matches")
    assert "whether most of the manure produced is captured" in question


def test_inference_gate_drops_figure_bearing_and_evaluative_items(evalgen_config) -> None:
    """The two boundaries. A figure-bearing item is answerable by recognising a trained
    string (absorption's axis); an evaluative one is a belief item. Both are judge calls,
    so what is checked here is that a failed check gates the item out rather than being
    reported informationally the way datagen's premise checks are."""
    items = [
        _inference_item(False, item_id="inference-0000"),
        _inference_item(False, item_id="inference-0001",
                        statement="Around 90 percent of manure is captured."),
        _inference_item(False, item_id="inference-0002",
                        statement="Welfare outcomes at these operations are acceptable."),
    ]
    scores = [_score(item["item_id"], "inference_is_descriptive", True) for item in items]
    scores[1] = _score("inference-0001", "inference_no_figures", False)
    scores[2] = _score("inference-0002", "inference_no_evaluative_language", False)

    kept, dropped = eval_gate.gate_items(items, scores, config=evalgen_config)
    assert [item["item_id"] for item in kept] == ["inference-0000"]
    assert dropped["inference-0001"] == ["inference_no_figures"]
    assert dropped["inference-0002"] == ["inference_no_evaluative_language"]


def test_inference_gating_summary_counts_whole_pairs() -> None:
    """The acquiescence reading needs whole D7 pairs, so the count must extend to this
    suite -- it keyed on `suite == "belief"` before."""
    items = [
        _inference_item(False, item_id="inference-0000", pair_id="inference-pair-0000"),
        _inference_item(True, item_id="inference-0001", pair_id="inference-pair-0000"),
        _inference_item(False, item_id="inference-0002", pair_id="inference-pair-0001"),
        _inference_item(True, item_id="inference-0003", pair_id="inference-pair-0001"),
    ]
    summary = eval_gate.gating_summary(
        items, items[:3], {"inference-0003": ["inference_no_figures"]}
    )
    assert summary["whole_pairs_kept"] == 1


def test_score_inference_groups_by_premise_dimension() -> None:
    from belief_transfer.evals.inference import score_inference

    rows = []
    for pair, (facet, dimension, p_yes) in enumerate([
        ("manure_capture", "environmental impact", 0.9),
        ("labor_productivity", "efficiency", 0.5),
    ]):
        for row in _pair_rows(pair, p_yes, 1 - p_yes):
            rows.append({**row, "suite": "inference", "facet": facet,
                         "dimension": dimension, "framing": "a plain statement"})
    result = score_inference(rows)
    assert result["per_dimension"] == pytest.approx(
        {"environmental impact": 0.9, "efficiency": 0.5}, abs=1e-9
    )
    assert set(result["per_facet"]) == {"manure_capture", "labor_productivity"}
    assert set(result["per_framing"]) == {"a plain statement"}
    # a consistent responder: the pair reading cancels, as for the belief suite
    assert abs(result["acquiescence"]["mean"]) < 1e-9


# ------------------------------------------------------- a second topic's eval machinery
#
# The generation machinery was hardcoded to factory farming in three places (the eval
# group's prompts and checks, the action tool/pressure wording above, and the leakage
# reference). What is checked here is that a second experiment can compose its own
# instrument without editing the frozen one.


def _software_job(make_job, *overrides: str):
    return make_job([
        "experiment=software_architecture",
        "eval=software_architecture",
        "run_id=test_software_eval",
        "experiment.dataset.n_items=1",
        *overrides,
    ])


def test_software_eval_group_composes_as_its_own_instrument(make_job) -> None:
    """A NEW eval group, not an edit: `evals.generate` stamps `eval_config_sha` into every
    item, so the frozen suites' instrument must keep its own hash."""
    from belief_transfer.schemas import model_sha

    software = _software_job(make_job).eval
    default = make_job(["+run=evalgen_pilot"]).eval

    assert software.evalgen is not None
    assert model_sha(software.evalgen) != model_sha(default.evalgen)
    # same instrument, different vocabulary: the check ids and the deterministic gates
    # must not drift, or a difference between topics stops being a topic difference
    for field in ("belief_item_checks", "action_item_checks", "inference_item_checks"):
        assert [c.id for c in getattr(software.evalgen, field)] == [
            c.id for c in getattr(default.evalgen, field)
        ]
    assert software.evalgen.leakage_flag_threshold == default.evalgen.leakage_flag_threshold
    assert software.evalgen.option_labels == default.evalgen.option_labels


def test_software_eval_group_carries_no_farm_vocabulary(make_job) -> None:
    """The contaminated strings: a check that names farm words cannot fail on a software
    item, and a vacuous check is not a gate."""
    evalgen = _software_job(make_job).eval.evalgen
    rendered = "\n".join([
        evalgen.belief_item_template,
        evalgen.action_item_template,
        evalgen.inference_item_template,
        *[check.question for check in evalgen.action_item_checks],
        *[check.question for check in evalgen.inference_item_checks],
    ]).lower()

    for word in ("farm", "animal", "pasture", "humane", "cruel", "sourcing", "welfare"):
        assert word not in rendered
    # and the belief template bans THIS experiment's statement, not the other one's
    assert (
        "A microservices architecture is the right default for new production systems"
        in evalgen.belief_item_template
    )


def test_software_action_generation_uses_this_topic_s_directions(make_job) -> None:
    job = _software_job(make_job)
    spec = job.experiment.action_eval

    properties = eval_generate.action_item_tool(spec).parameters["properties"]
    assert "(microservices)" in properties["option_target"]["description"]
    # R2 in the experiment spec: budget/simplicity pressure favors the MONOLITH here
    assert spec.pressure_favors == "alternative"
    assert (
        "the option that avoids the target products"
        in eval_generate.pressure_instructions(spec)["strong"]
    )


def test_leakage_corpus_run_id_defaults_to_the_old_hardcoded_path(make_job) -> None:
    """`stages.evalgen` named `factory_farming_v1` in code, so a second experiment's
    overlap check silently found nothing to compare against."""
    from belief_transfer.stages import evalgen as evalgen_stage

    job = make_job(["+run=evalgen_pilot"])
    assert job.evalgen.leakage_corpus_run_id == "factory_farming_v1"
    path = evalgen_stage.leakage_corpus_path(job)
    assert path is not None
    assert path.parts[-3:] == ("factory_farming", "factory_farming_v1", "documents.jsonl")


def test_leakage_corpus_run_id_selects_the_corpus_and_can_be_switched_off(make_job) -> None:
    from belief_transfer.stages import evalgen as evalgen_stage

    named = _software_job(make_job, "evalgen.leakage_corpus_run_id=software_arch_pilot")
    path = evalgen_stage.leakage_corpus_path(named)
    assert path is not None
    assert path.parts[-3:] == (
        "software_architecture", "software_arch_pilot", "documents.jsonl"
    )

    off = _software_job(make_job, "evalgen.leakage_corpus_run_id=null")
    assert evalgen_stage.leakage_corpus_path(off) is None
