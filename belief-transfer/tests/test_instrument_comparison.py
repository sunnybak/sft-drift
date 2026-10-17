"""Conditional diagnostics retain failures and distinct abstentions."""
import pytest

from belief_transfer.config import load_job
from belief_transfer.metrics.instrument import comparison_table
from belief_transfer.validation.instrument import build_observations


def bank():
    spec = load_job(["+run=instrument_diverse_openai_v2"]).instrument_validation
    spec.beliefs = spec.beliefs[:2]
    return [r.model_dump() for r in build_observations(spec)]


def responses(rows):
    return [{**r, "answer": r["expected"] or ("disagree" if r["polarity"] == "negative" else "agree")}
            for r in rows]


def test_complete_logical_responses_have_expected_diagnostics():
    rows = bank()
    result = comparison_table(rows, responses(rows))
    p = result["pooled"]
    assert p["format_valid"]["value"] == p["order_stable"]["value"] == 1
    assert p["paraphrase_stable"]["numerator"] == 12
    assert p["absolute_acquiescence"] == {"numerator": 0, "denominator": 12, "expected": 12, "value": 0}
    assert p["assumption_correct"]["numerator"] == 24
    assert p["neutral_change"]["value"] == p["offtopic_change"]["value"] == 0
    assert result["controls"]["comprehension_correct"]["numerator"] == 18


def test_missing_order_never_becomes_measured_stability():
    rows = bank()
    replies = responses(rows)
    missing = next(i for i,r in enumerate(replies) if r["benchmark"] == "option_order")
    replies.pop(missing)
    p = comparison_table(rows, replies)["pooled"]
    assert p["format_valid"]["denominator"] == 132
    assert p["format_valid"]["numerator"] == 131
    assert p["order_stable"] == {"numerator": 1, "denominator": 1, "expected": 2, "value": 1}


def test_unknown_is_distinct_from_reject_and_unavailable_is_not_zero():
    rows = bank()
    replies = [{**r, "answer": "unresolved"} for r in rows]
    p = comparison_table(rows, replies)["pooled"]
    assert p["absolute_acquiescence"]["value"] is None
    assert p["absolute_acquiescence"]["denominator"] == 0
    assert p["negation_unresolved"]["numerator"] == 12
    assert p["unresolved"]["value"] == p["order_stable"]["value"] == 1
    assert p["baseline_unresolved"]["numerator"] == 12
    assert p["baseline_disagree"]["numerator"] == 0
    assert p["baseline_format_valid"]["numerator"] == 12
    assert p["assumption_correct"]["value"] == 0
    # Both poles rejected is a logical contradiction just like both endorsed.
    p = comparison_table(rows, [{**r, "answer": "disagree"} for r in rows])["pooled"]
    assert p["absolute_acquiescence"]["value"] == 1


def test_categorical_null_detects_reject_to_unknown_without_agreement():
    rows = bank()
    replies = responses(rows)
    for r in replies:
        if r["benchmark"] == "responsiveness":
            r["answer"] = "unresolved" if r["condition"] == "offtopic_positive" else "disagree"
    p = comparison_table(rows, replies)["pooled"]
    assert p["offtopic_change"]["value"] == 1
    assert p["offtopic_change"]["denominator"] == 12


def test_response_cannot_change_its_reporting_domain():
    rows = bank()
    replies = responses(rows)
    replies[-1]["domain"] = "a nicer domain"
    with pytest.raises(ValueError, match="grouping metadata"):
        comparison_table(rows, replies)


def test_errored_reply_cannot_supply_a_determinate_negation_answer():
    rows = bank()
    replies = responses(rows)
    broken = next(r for r in replies if r["benchmark"] == "negation")
    broken["error"] = "truncated reply"
    # An accidentally retained parsed answer must not override its error.
    p = comparison_table(rows, replies)["pooled"]
    assert p["absolute_acquiescence"]["denominator"] == 11
    assert p["negation_incomplete"]["numerator"] == 1
    assert p["format_valid"]["numerator"] == 131
