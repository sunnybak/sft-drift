"""Tests for `belief_transfer.benchmarks.perf`: pure scoring/aggregation, the
integrity of its dataset, and end-to-end `evaluate` against a stub model.

No real model is loaded. `evaluate` needs a `.generate`, a `.batch_size`, a
`._ensure_loaded()`, and a `._tokenizer` -- exercised here with a stub that fakes just
enough of `inference.model.HFModel`'s surface; running it against real weights is what
`make perf-bench` is for.
"""

from __future__ import annotations

import pytest

from belief_transfer.benchmarks import load_items, run_benchmark
from belief_transfer.benchmarks.perf import benchmark as perf


class _StubTokenizer:
    def __call__(self, text: str, add_special_tokens: bool = False) -> dict:
        del add_special_tokens
        return {"input_ids": text.split()}


class StubModel:
    """Answers every prompt with a preset response keyed by prompt text -- a stand-in
    for `HFModel` that never touches a real tokenizer or GPU.
    """

    def __init__(self, answer_for: dict[str, str], batch_size: int = 8) -> None:
        self.answer_for = answer_for
        self.batch_size = batch_size
        self._tokenizer = _StubTokenizer()

    def _ensure_loaded(self) -> None:
        pass

    def generate(self, prompts: list[str], temperature: float = 0.0) -> list[str]:
        del temperature
        return [self.answer_for[prompt] for prompt in prompts]


def correct_answer_by_prompt(items: list[dict]) -> dict[str, str]:
    """A plausible correct answer for every item, keyed by prompt -- mirrors
    `test_calibrate.py`'s retired plausible-answer table (moved here with the code it
    was guarding).
    """
    plausible = {
        r"\b19\b": "19",
        r"\b72\b": "72",
        r"\b63\b": "63",
        r"tokyo": "Tokyo",
        r"paris": "Paris",
        r"canberra": "Canberra",
        r"\bseven\b|\b7\b": "7",
        r"green": "Green",
        r"h[2₂]o": "H₂O",
        r"\btac\b": "tac",
        r"earth": "Earth",
        r"\b32\b": "32",
    }
    return {item["prompt"]: plausible[item["expected"]] for item in items}


def test_dataset_is_wellformed() -> None:
    items = load_items("perf")
    assert len(items) >= 10
    assert len({item["id"] for item in items}) == len(items), "duplicate item ids"
    for item in items:
        assert item["prompt"].strip()
        assert item["expected"].strip()


def test_every_item_is_matched_by_a_plausible_correct_answer() -> None:
    # Guards the scoring patterns themselves: a too-strict pattern scores a correct
    # model answer as a miss and makes perf-bench look like a broken pipeline.
    # ("H2O" vs the "H₂O" Qwen3 actually returns was exactly this bug.)
    items = load_items("perf")
    answers = correct_answer_by_prompt(items)
    for item in items:
        answer = answers[item["prompt"]]
        assert perf.score_item(item, answer)["correct"] is True, (
            f"pattern {item['expected']!r} rejects plausible answer {answer!r}"
        )


def test_score_item_is_case_insensitive() -> None:
    item = {"id": "x", "expected": "paris"}
    assert perf.score_item(item, "PARIS")["correct"] is True
    assert perf.score_item(item, "the answer is 5")["correct"] is False


def test_score_item_word_boundaries_reject_substrings_of_longer_numbers() -> None:
    # `\b19\b` must not be satisfied by "190" -- otherwise a wrong answer scores as
    # correct and the whole perf-bench signal is worthless.
    item = {"id": "x", "expected": r"\b19\b"}
    assert perf.score_item(item, "190")["correct"] is False
    assert perf.score_item(item, "19")["correct"] is True


def test_aggregate_gates_passed_on_accuracy_only() -> None:
    outcomes = [{"id": f"i{i}", "correct": True} for i in range(8)] + [
        {"id": "miss", "correct": False}
    ]
    aggregated = perf.aggregate(outcomes, elapsed_s=1.0, total_new_tokens=100, batch_size=8)

    assert aggregated["metrics"]["accuracy"] == pytest.approx(8 / 9)
    assert aggregated["metrics"]["tokens_per_sec"] == pytest.approx(100.0)
    assert aggregated["metrics"]["batch_size"] == pytest.approx(8.0)
    assert len(aggregated["failures"]) == 1
    assert aggregated["passed"] is True  # above MIN_ACCURACY despite one miss


def test_aggregate_fails_below_the_accuracy_bar() -> None:
    outcomes = [{"id": f"i{i}", "correct": i < 5} for i in range(10)]
    aggregated = perf.aggregate(outcomes)
    assert aggregated["metrics"]["accuracy"] == pytest.approx(0.5)
    assert aggregated["passed"] is False


def test_evaluate_end_to_end_against_a_correct_stub() -> None:
    items = load_items("perf")
    model = StubModel(correct_answer_by_prompt(items))

    result = run_benchmark("perf", model, model_key="qwen3-4b")

    assert result.passed is True
    assert result.n_items == len(items)
    assert result.metrics["accuracy"] == pytest.approx(1.0)
    assert result.failures == []
    assert result.benchmark == "perf"


def test_evaluate_reports_misses_when_the_model_is_wrong() -> None:
    items = load_items("perf")
    answers = correct_answer_by_prompt(items)
    answers[items[0]["prompt"]] = "definitely wrong"
    model = StubModel(answers)

    result = run_benchmark("perf", model, model_key="qwen3-4b")

    assert result.passed is True  # one miss out of a dozen still clears MIN_ACCURACY
    assert len(result.failures) == 1
    assert result.failures[0]["id"] == items[0]["id"]
