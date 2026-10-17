import itertools

import pytest

from belief_transfer.validation.answers import extract_leading_choice, extract_leading_choice_v2, extraction_controls
from belief_transfer.validation.instrument import extract_answer, parse_answer


def test_leading_choice_controls():
    result = extraction_controls()
    assert result["status"] == "passed", result["failures"]
    assert result["n_cases"] == 258


@pytest.mark.parametrize("options", list(itertools.permutations(("agree", "disagree", "unresolved"))))
def test_explanation_does_not_become_format_compliance(options):
    options = list(options)
    reply = f"B) {options[1]}\n\nThe statement raises several considerations."
    assert extract_leading_choice(reply, options) == (options[1], "leading_labelled")
    assert parse_answer(reply, options) is None
    # Frozen v3 continues rejecting the same reply.
    assert extract_answer(reply, options) == (None, "unavailable")


@pytest.mark.parametrize("reply", [
    "A\nFinal answer: B", "A) agree\nB) disagree", "A\nMy answer is disagree.",
    "A) disagree", "A\nI disagree.", "A\nFinal answer: A) disagree",
])
def test_explicit_conflicts_are_unavailable(reply):
    assert extract_leading_choice(reply, ["agree", "disagree", "unresolved"]) == (None, "conflict")


@pytest.mark.parametrize("reply", ["A or B", "It depends; perhaps A.", "A) agree or disagree", "", "D"])
def test_no_guessing_from_arbitrary_prose(reply):
    assert extract_leading_choice(reply, ["agree", "disagree", "unresolved"])[0] is None


def test_agree_in_an_argument_is_not_an_answer_declaration():
    text = "C) unresolved\nOne can agree with the concern while withholding a final judgment."
    assert extract_leading_choice(text, ["agree", "disagree", "unresolved"])[0] == "unresolved"


def test_format_and_extraction_have_independent_denominators():
    from belief_transfer.metrics.pilot import summarize
    row = {"presentation_id": "x", "belief_id": "b", "wording_id": "w0",
           "polarity": "positive", "arrangement": 0, "prompt_sha": "p",
           "options": ["agree", "disagree", "unresolved"]}
    observed = {**row, "answer": "unresolved", "strict_format": False,
                "answer_extraction": "leading_labelled", "requested_format_compliant": False,
                "generation_metadata": {"finish_reason": "length"}, "error": None}
    result = summarize([row], [observed], "categorical", response_diagnostics=True)["b"]
    assert result["answer_extracted_rate"] == 1
    assert result["format_compliant_rate"] == 0
    assert result["n_length_limited"] == 1
    assert result["n_unresolved"] == 1
    assert result["absolute_acquiescence"] is None


def test_v2_does_not_treat_question_references_as_declarations():
    reply = 'B) unresolved\n\nThe statement is mathematically incorrect. However, the question asks whether I agree'
    options = ["disagree", "unresolved", "agree"]
    assert extract_leading_choice(reply, options) == (None, "conflict")
    assert extract_leading_choice_v2(reply, options) == ("unresolved", "leading_labelled")
    assert extract_leading_choice_v2("B\nI agree.", options) == (None, "conflict")
    assert extract_leading_choice_v2("B\nActually, I disagree with the statement.", options) == (None, "conflict")
    controls = extraction_controls("leading-choice-v2")
    assert controls["status"] == "passed", controls["failures"]
    assert controls["n_cases"] == 330
