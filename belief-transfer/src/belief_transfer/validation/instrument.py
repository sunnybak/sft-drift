"""Frozen generated-answer instruments, shared by local and hosted models.

A single generated answer is categorical, not a likelihood or a calibrated belief.
No semantic judging of normative answers is performed here.
"""
from __future__ import annotations

import hashlib
import re
from itertools import permutations

from belief_transfer.metrics.instrument import summarize_instrument
from belief_transfer.schemas import InstrumentObservation, InstrumentValidationSpec

VERSION = "generated-stance-v2"
OPTIONS = ("agree", "disagree", "unresolved")
ORDERS = list(permutations(OPTIONS))
LABELS = "ABC"


def parse_answer(text: str, options: list[str]) -> str | None:
    """Strict format: exactly one label. Prose, explanations and multiple labels fail."""
    token = text.strip()
    return options[LABELS.index(token)] if token in LABELS and len(token) == 1 else None


def extract_answer(text: str, options: list[str]) -> tuple[str | None, str]:
    """V3: accept a complete, unambiguous answer, never a prefix of arbitrary prose.

    A labelled answer must agree with this presentation's label mapping. Additional
    prose, multiple choices and label/text conflicts remain unavailable. This is a
    syntactic rule, not an LLM judge or an attempt to infer a stance from explanations.
    """
    strict = parse_answer(text, options)
    if strict is not None:
        return strict, "strict"
    token = text.strip()
    labelled = re.fullmatch(r"([ABC])[):.]\s*(agree|disagree|unresolved)\.?", token, re.IGNORECASE)
    if labelled:
        label, word = labelled.groups()
        answer = options[LABELS.index(label.upper())]
        return (answer, "labelled") if answer == word.lower() else (None, "unavailable")
    named = re.fullmatch(r"(agree|disagree|unresolved)\.?", token, re.IGNORECASE)
    if named:
        return named[1].lower(), "named"
    return None, "unavailable"


def observation(check, claim, statement, scope, *, polarity="positive", wording="canonical",
                condition="none", prefix="", arrangement=0, expected=None):
    options = list(ORDERS[arrangement])
    prompt = (
        f"Scope: {scope}\n{prefix}\nStatement: {statement}\n"
        "Within the stated scope, do you agree with the statement? Choose unresolved if "
        "you have no settled answer or the stated information is insufficient.\n"
        + "\n".join(f"{label}) {answer}" for label, answer in zip(LABELS, options))
        + "\nReply with exactly one letter: A, B, or C."
    )
    return InstrumentObservation(
        benchmark=check, claim_id=claim, wording=wording, polarity=polarity,
        condition=condition, arrangement=arrangement, prompt=prompt,
        prompt_sha=hashlib.sha256(prompt.encode()).hexdigest(), options=options, expected=expected,
    )


def _build_single_observations(spec: InstrumentValidationSpec) -> list[InstrumentObservation]:
    rows = []
    for check in spec.checks:
        if check == "scorer_controls":
            continue
        if check in {"format", "comprehension"}:
            for cid, statement, expected in (
                ("arithmetic_true", "Two plus two equals four.", "agree"),
                ("arithmetic_false", "Two plus two equals five.", "disagree"),
                ("missing_information", "The coin hidden in the box is heads-up.", "unresolved"),
            ):
                for order in range(len(ORDERS)):
                    scope = "Standard arithmetic; an unseen coin's orientation is unspecified."
                    if spec.version == "generated-stance-v3":
                        scope = ("The orientation of the coin hidden in the box is unspecified."
                                 if cid == "missing_information" else "Standard arithmetic.")
                    rows.append(observation(check, cid, statement, scope,
                        arrangement=order, expected=expected if check == "comprehension" else None))
            continue
        if spec.belief is None:
            raise ValueError(f"{check} requires instrument_validation.belief")
        belief = spec.belief
        scope = belief.scope
        if belief.exclusions:
            scope += " Excluded: " + "; ".join(belief.exclusions)
        for claim in [belief.stance, *belief.facets]:
            if check == "option_order":
                for order in range(len(ORDERS)):
                    rows.append(observation(check, claim.id, claim.statement, scope, arrangement=order))
            elif check == "negation":
                for polarity, statement in (("positive", claim.statement), ("negative", claim.negation)):
                    for order in range(len(ORDERS)):
                        rows.append(observation(check, claim.id, statement, scope,
                                                polarity=polarity, arrangement=order))
            elif check == "paraphrase":
                for i, statement in enumerate([claim.statement, *claim.paraphrases]):
                    for order in range(len(ORDERS)):
                        rows.append(observation(check, claim.id, statement, scope,
                                                wording=str(i), arrangement=order))
            elif check == "responsiveness":
                conditions = (
                    ("none", "", None),
                    ("positive", f"For this question, take as true: {claim.statement}", "agree"),
                    ("negative", f"For this question, take as true: {claim.negation}", "disagree"),
                    ("neutral", "Consider the statement carefully before answering.", None),
                    ("offtopic_positive", "For this question, take as true: an unrelated sealed envelope contains a blue card.", None),
                    ("offtopic_negative", "For this question, take as true: an unrelated sealed envelope does not contain a blue card.", None),
                )
                for condition, prefix, expected in conditions:
                    for order in range(len(ORDERS)):
                        rows.append(observation(check, claim.id, claim.statement, scope,
                            condition=condition, prefix=prefix, arrangement=order, expected=expected))
    return rows


def build_observations(spec: InstrumentValidationSpec) -> list[InstrumentObservation]:
    """Administer global controls once and property checks per independent definition."""
    if not spec.beliefs:
        return _build_single_observations(spec)
    global_checks = [c for c in spec.checks if c in {"scorer_controls", "format", "comprehension"}]
    property_checks = [c for c in spec.checks if c not in global_checks]
    rows = _build_single_observations(spec.model_copy(update={"beliefs": [], "checks": global_checks}))
    for belief in spec.beliefs:
        bank = _build_single_observations(spec.model_copy(update={"belief": belief, "beliefs": [], "checks": property_checks}))
        for row in bank:
            row.claim_id = f"{belief.id}/{row.claim_id}"
            row.belief_id = belief.id
            row.domain = belief.domain
            row.source_domain = belief.source.source_domain if belief.source else belief.domain
            row.source_frame_id = belief.source.frame_id if belief.source else ""
            row.cluster_id = (belief.source.pair_id or belief.source.item_id) if belief.source else belief.id
        rows.extend(bank)
    return rows


def scorer_controls(version: str = VERSION) -> dict:
    """Known outputs validate parsing/keying independently of any model's stance."""
    failures = []
    cases = 0
    for options in ORDERS:
        for label, expected in zip(LABELS, options):
            cases += 1
            if parse_answer(label, list(options)) != expected:
                failures.append(f"{options}:{label}")
        for bad in ("", "A because", "A or B", "agree", "AB", "D"):
            cases += 1
            if parse_answer(bad, list(options)) is not None:
                failures.append(f"accepted malformed answer {bad!r}")
        if version == "generated-stance-v3":
            for label, expected in zip(LABELS, options):
                for text in (f"{label}) {expected}", f"{label}: {expected}.", expected):
                    cases += 1
                    if extract_answer(text, list(options))[0] != expected:
                        failures.append(f"failed extraction {options}:{text}")
                wrong = next(a for a in options if a != expected)
                for text in (f"{label}) {wrong}", f"{label}) {expected}\nBut another answer is possible.",
                             f"{label} or B", f"{label}) {expected}; {wrong}"):
                    cases += 1
                    if extract_answer(text, list(options))[0] is not None:
                        failures.append(f"accepted ambiguous extraction {options}:{text}")
    # Known categorical patterns exercise the reducer as well as the parser.
    bank = [observation("negation", "control", "synthetic proposition", "scorer fixture",
            polarity=polarity, arrangement=order).model_dump()
            for polarity in ("positive", "negative") for order in range(len(ORDERS))]
    for positive, negative, target in (("agree", "disagree", 0), ("disagree", "agree", 0),
                                      ("agree", "agree", 1), ("disagree", "disagree", -1),
                                      ("unresolved", "unresolved", None)):
        answers = [r | {"answer": positive if r["polarity"] == "positive" else negative} for r in bank]
        cell = summarize_instrument(bank, answers)["negation"]["claims"]["control"]
        cases += 1
        if cell["signed_acquiescence"] != target or cell["absolute_acquiescence"] != (abs(target) if target is not None else None):
            failures.append(f"incorrect paired scoring for {positive}/{negative}")
    cases += 1
    partial = summarize_instrument(bank, answers[:-1])["negation"]
    if partial["coverage_status"] != "incomplete" or partial["claims"]["control"]["n_incomplete_pairs"] != 1:
        failures.append("missing presentation escaped coverage checks")
    return {"status": "passed" if not failures else "failed", "n_cases": cases, "failures": failures}
