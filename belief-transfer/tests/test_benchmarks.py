"""Tests for `belief_transfer.benchmarks`: the registry, and the choice benchmark's
pure scoring/aggregation plus the integrity of its dataset.

No model is loaded. The benchmark's only model-dependent step is `evaluate`, which is
exercised here with a stub `ChoiceScorer` -- running it against real weights is what
`make choice-bench` is for.
"""

from __future__ import annotations

import pytest

from belief_transfer.benchmarks import BENCHMARKS, load_items, run_benchmark
from belief_transfer.benchmarks.choice import benchmark as choice
from belief_transfer.schemas import ChoiceScore, ChoiceScores


class FixedLetterScorer:
    """Always answers "A" regardless of content -- a purely layout-driven model."""

    def score_choices(self, prompt, choices):
        return ChoiceScores(
            prompt=prompt,
            scores=[
                ChoiceScore(choice=letter, logprob=(0.0 if letter == "A" else -10.0),
                            logprob_per_token=0.0, n_tokens=1)
                for letter in choices
            ],
        )


class StubScorer:
    """A content-driven `ChoiceScorer`: it reads the rendered options and puts its mass on
    whichever letter currently holds a preset answer *text*.

    Keyed on text rather than letter because `evaluate` now scores every placement of the
    correct answer -- a stub that always named the same letter would be modelling a
    layout-driven model and would (correctly) score 0.25. `FixedLetterScorer` below is that
    model, on purpose.
    """

    def __init__(self, answer_text_for: dict[str, str], confidence: float = 0.9) -> None:
        self.answer_text_for = answer_text_for
        self.confidence = confidence

    def score_choices(self, prompt, choices):
        import math

        lines = prompt.split("\n")
        target = self.answer_text_for[lines[0]]
        picked = choices[0]
        for line in lines[1:]:
            if ") " in line:
                letter, text = line.split(") ", 1)
                if text == target:
                    picked = letter
        spread = (1.0 - self.confidence) / (len(choices) - 1)
        return ChoiceScores(
            prompt=prompt,
            scores=[
                ChoiceScore(
                    choice=letter,
                    logprob=math.log(self.confidence if letter == picked else spread),
                    logprob_per_token=0.0,
                    n_tokens=1,
                )
                for letter in choices
            ],
        )


def correct_text_by_question(items: list[dict]) -> dict[str, str]:
    return {
        item["question"]: item["choices"][choice.letters_for(item).index(item["answer"])]
        for item in items
    }


def test_registry_exposes_choice_and_perf_and_rejects_unknown_ids() -> None:
    assert "choice" in BENCHMARKS
    assert "perf" in BENCHMARKS
    with pytest.raises(KeyError, match="unknown benchmark"):
        run_benchmark("nope", StubScorer({}), model_key="qwen3-4b")


def test_dataset_is_wellformed_and_every_answer_is_reachable() -> None:
    """A typo'd answer key would silently make an item unanswerable and drag accuracy
    down forever, so the dataset is checked structurally rather than trusted.
    """
    items = load_items("choice")

    assert len(items) >= 20
    assert len({item["id"] for item in items}) == len(items), "duplicate item ids"
    for item in items:
        assert item["answer"] in choice.letters_for(item), f"{item['id']} answer outside its choices"
        assert len(item["choices"]) >= 2
        assert len(set(item["choices"])) == len(item["choices"]), f"{item['id']} has duplicate choices"
        assert item["category"] in {"memory", "reasoning"}


def test_dataset_answers_are_not_concentrated_on_one_letter() -> None:
    """Position bias is real: a model that always says 'A' should not be able to pass.
    No letter may hold a majority of the answers.
    """
    items = load_items("choice")
    counts: dict[str, int] = {}
    for item in items:
        counts[item["answer"]] = counts.get(item["answer"], 0) + 1

    assert max(counts.values()) <= len(items) / 2


def test_format_prompt_letters_the_options_and_asks_for_one_letter() -> None:
    prompt = choice.format_prompt(
        {"id": "x", "question": "Pick one.", "choices": ["first", "second", "third"]}
    )

    assert "A) first" in prompt
    assert "C) third" in prompt
    assert prompt.endswith(choice.INSTRUCTION)


def test_score_item_records_correctness_confidence_and_margin() -> None:
    item = {"id": "x", "category": "memory", "choices": ["a", "b", "c"], "answer": "B"}

    outcome = choice.score_item(item, {"A": 0.2, "B": 0.7, "C": 0.1})

    assert outcome["correct"] is True
    assert outcome["chosen"] == "B"
    assert outcome["confidence"] == pytest.approx(0.7)
    assert outcome["margin"] == pytest.approx(0.5)


def test_score_item_margin_is_negative_when_a_wrong_option_wins() -> None:
    item = {"id": "x", "category": "memory", "choices": ["a", "b"], "answer": "A"}

    outcome = choice.score_item(item, {"A": 0.3, "B": 0.7})

    assert outcome["correct"] is False
    assert outcome["margin"] == pytest.approx(-0.4)


def test_score_item_rejects_an_answer_outside_the_choices() -> None:
    item = {"id": "x", "category": "memory", "choices": ["a", "b"], "answer": "D"}

    with pytest.raises(ValueError, match="outside its choices"):
        choice.score_item(item, {"A": 0.5, "B": 0.5})


def test_confident_and_correct_passes() -> None:
    outcomes = [
        {"id": f"i{i}", "category": "memory", "answer": "A", "chosen": "A", "correct": True,
         "confidence": 0.9, "margin": 0.8}
        for i in range(10)
    ]

    aggregated = choice.aggregate(outcomes)

    assert aggregated["passed"] is True
    assert aggregated["metrics"]["accuracy"] == pytest.approx(1.0)
    assert aggregated["failures"] == []


def test_correct_but_indifferent_fails_on_confidence_alone() -> None:
    """The point of the confidence bar: a model answering everything right at barely
    above chance has lost the forced-choice signal a belief eval reads, even though its
    accuracy is perfect.
    """
    outcomes = [
        {"id": f"i{i}", "category": "reasoning", "answer": "A", "chosen": "A", "correct": True,
         "confidence": 0.28, "margin": 0.02}
        for i in range(10)
    ]

    aggregated = choice.aggregate(outcomes)

    assert aggregated["metrics"]["accuracy"] == pytest.approx(1.0)
    assert aggregated["passed"] is False


def test_aggregate_reports_per_category_accuracy() -> None:
    outcomes = [
        {"id": "a", "category": "memory", "answer": "A", "chosen": "A", "correct": True,
         "confidence": 0.9, "margin": 0.8},
        {"id": "b", "category": "reasoning", "answer": "A", "chosen": "B", "correct": False,
         "confidence": 0.1, "margin": -0.7},
    ]

    metrics = choice.aggregate(outcomes)["metrics"]

    assert metrics["accuracy_memory"] == pytest.approx(1.0)
    assert metrics["accuracy_reasoning"] == pytest.approx(0.0)


def test_evaluate_end_to_end_against_a_stub_scorer() -> None:
    items = load_items("choice")
    answers = correct_text_by_question(items)

    result = run_benchmark("choice", StubScorer(answers), model_key="qwen3-4b")

    assert result.passed is True
    assert result.n_items == len(items)
    assert result.metrics["accuracy"] == pytest.approx(1.0)
    assert result.benchmark == "choice"
    assert result.adapter is None


def test_evaluate_fails_when_the_scorer_always_picks_one_letter() -> None:
    """Guards the dataset property above from the other side: a degenerate always-A
    model must fail the benchmark.
    """
    items = load_items("choice")

    result = run_benchmark("choice", FixedLetterScorer(), model_key="qwen3-4b")

    assert result.passed is False
    # Right only at the one placement where the answer happens to sit at A.
    assert result.metrics["accuracy"] == pytest.approx(0.25)
    assert result.metrics["position_consistency"] == pytest.approx(0.0)


def test_thresholds_are_per_model_and_report_calibration() -> None:
    calibrated, is_calibrated = choice.thresholds_for("qwen3-4b")
    fallback, is_fallback_calibrated = choice.thresholds_for("some-unmeasured-model")

    assert is_calibrated is True
    assert is_fallback_calibrated is False
    assert fallback is choice.DEFAULT_THRESHOLDS
    assert calibrated.reference != fallback.reference


def test_every_calibrated_threshold_records_its_reference_measurement() -> None:
    """A bar with no record of what it was calibrated against can't be audited or
    updated when the dataset changes.
    """
    for model_key, thresholds in choice.THRESHOLDS.items():
        assert thresholds.reference.strip(), f"{model_key} has no reference measurement"
        assert 0.0 < thresholds.min_accuracy <= 1.0
        assert 0.0 < thresholds.min_mean_confidence <= 1.0


def test_the_same_scores_can_pass_one_model_and_fail_another() -> None:
    """The point of per-model bars: an identical set of outcomes is judged against
    whichever model produced it.
    """
    outcomes = [
        {"id": f"i{i}", "category": "memory", "answer": "A", "chosen": "A", "correct": True,
         "confidence": 0.60, "margin": 0.3}
        for i in range(10)
    ]
    strict = choice.Thresholds(min_accuracy=0.9, min_mean_confidence=0.8, reference="strict")
    lenient = choice.Thresholds(min_accuracy=0.5, min_mean_confidence=0.4, reference="lenient")

    assert choice.aggregate(outcomes, strict)["passed"] is False
    assert choice.aggregate(outcomes, lenient)["passed"] is True


def test_result_records_the_thresholds_it_was_judged_against() -> None:
    items = load_items("choice")
    answers = correct_text_by_question(items)

    result = run_benchmark("choice", StubScorer(answers), model_key="qwen3-4b")

    assert result.thresholds["min_accuracy"] == choice.THRESHOLDS["qwen3-4b"].min_accuracy
    assert result.calibrated is True


def test_uncalibrated_model_is_flagged_on_the_result() -> None:
    items = load_items("choice")
    answers = correct_text_by_question(items)

    result = run_benchmark("choice", StubScorer(correct_text_by_question(load_items("choice"))), model_key="brand-new-model")

    assert result.calibrated is False
    assert result.thresholds["min_accuracy"] == choice.DEFAULT_THRESHOLDS.min_accuracy


def test_placements_move_the_answer_to_every_position() -> None:
    item = {"id": "x", "category": "memory", "question": "q", "choices": ["w", "x", "y", "z"], "answer": "B"}

    variants = list(choice.placements(item))

    assert [v["answer"] for v in variants] == ["A", "B", "C", "D"]
    for variant in variants:
        # The correct text follows its letter, and no option is lost or duplicated.
        assert variant["choices"][choice.letters_for(variant).index(variant["answer"])] == "x"
        assert sorted(variant["choices"]) == sorted(item["choices"])


def test_combine_placements_scores_a_position_dependent_item_as_partial() -> None:
    """An item answered right only where the answer sits at A is 0.25, not a pass -- the
    whole point of averaging placements.
    """
    item = {"id": "x", "category": "memory", "answer": "A", "choices": ["a", "b", "c", "d"]}
    outcomes = [
        {"chosen": "A", "correct": True, "confidence": 0.9, "margin": 0.8},
        {"chosen": "A", "correct": False, "confidence": 0.1, "margin": -0.7},
        {"chosen": "A", "correct": False, "confidence": 0.1, "margin": -0.7},
        {"chosen": "A", "correct": False, "confidence": 0.1, "margin": -0.7},
    ]

    combined = choice.combine_placements(item, outcomes, ["a", "b", "c", "d"])

    assert combined["correct"] == pytest.approx(0.25)
    assert combined["position_consistent"] is False
    assert combined["n_placements"] == 4


def test_combine_placements_marks_a_content_driven_item_consistent() -> None:
    item = {"id": "x", "category": "memory", "answer": "A", "choices": ["a", "b", "c", "d"]}
    outcomes = [{"chosen": "A", "correct": True, "confidence": 0.9, "margin": 0.8}] * 4

    combined = choice.combine_placements(item, outcomes, ["a", "a", "a", "a"])

    assert combined["correct"] == pytest.approx(1.0)
    assert combined["position_consistent"] is True


def test_partial_misses_are_reported_as_failures() -> None:
    """A partial miss must surface rather than being averaged into silence."""
    outcomes = [
        {"id": "partial", "category": "memory", "answer": "A", "chosen": "A", "correct": 0.75,
         "confidence": 0.7, "margin": 0.4, "position_consistent": False},
        {"id": "clean", "category": "memory", "answer": "A", "chosen": "A", "correct": 1.0,
         "confidence": 0.9, "margin": 0.8, "position_consistent": True},
    ]

    aggregated = choice.aggregate(outcomes)

    assert [f["id"] for f in aggregated["failures"]] == ["partial"]
    assert aggregated["metrics"]["position_consistency"] == pytest.approx(0.5)
