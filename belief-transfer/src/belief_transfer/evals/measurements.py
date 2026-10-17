"""Independent Stance and Conviction passes over a shared, immutable content bank."""
from __future__ import annotations

from itertools import permutations
import re

from belief_transfer.evals.pilot import fingerprint, validate_wordings
from belief_transfer.schemas import BELIEF_MEASUREMENT_OPTIONS, PilotBenchSpec, PilotWording

VERSION = "stance-conviction-v1"
OPTIONS = BELIEF_MEASUREMENT_OPTIONS
DEFINITIONS = {
    "stance": "Position favored when required to choose; no calibrated belief probability.",
    "conviction": "Self-reported firmness of judgment, independent of its direction; not correctness or calibrated confidence.",
}


def presentation(measurement, identity, question, options, *, style="original", version=VERSION, **metadata):
    labels = list("ABC"[:len(options)])
    prompt = question + "\n" + "\n".join(f"{label}) {word}" for label, word in zip(labels, options))
    prompt += "\nReply with exactly one letter: " + ", ".join(labels) + "."
    if style == "concise":
        prompt = ("Answer the question below. Output exactly one letter and then stop. "
                  "Do not repeat an option word or explain.\n\n" + prompt +
                  "\nYour entire response must be one letter.")
    row = {"measurement": measurement, "measurement_version": version,
            "presentation_id": identity, "prompt": prompt, "prompt_sha": fingerprint(prompt),
            "options": list(options), "labels": labels, **metadata}
    if style != "original":
        row.update(measurement_version=version + "/" + style, prompt_style=style)
    return row


def inline_negation(statement):
    """Negate the declared main predicate; unsupported wording is never guessed."""
    patterns = [r"\bis(?=\s+(?:ethically acceptable|morally acceptable|preferable\b|a better starting architecture\b|greater than\b))",
                r"\bequals\b", r"\brepresents(?= a superior starting architecture\b)"]
    for pattern, replacement in zip(patterns, ("is not", "does not equal", "does not represent")):
        if re.search(pattern, statement):
            return re.sub(pattern, replacement, statement, count=1)
    raise ValueError("inline negation requires a reviewed main-predicate pattern")


def stance_presentation(identity, target_statement, opposite, scope_text, options, *, interface,
                        style="concise", version="stance-v2", **metadata):
    """Render target-specific choices; option semantics always refer to the target.

    Positive and negative targets receive independent prompts. Negation coherence is
    measured from those replies, never derived by reusing one paired-choice answer.
    """
    statement, scope = target_statement, scope_text
    original_statement, original_opposite = statement, opposite
    if interface in {"named_inline_negation", "endorse_inline_negation"}:
        if statement.startswith("It is not the case that "):
            statement = inline_negation(opposite)
        else:
            opposite = inline_negation(statement)
    if interface == "agree_disagree":
        question = (f"Scope: {scope}\nStatement: {statement}\nWithin the stated scope, which position do you favor? "
                    "Choose agree or disagree, even if your preference is tentative.")
        return presentation("stance", identity, question, options, style=style, version=version, **metadata)
    if interface in {"endorse_reject", "endorse_inline_negation", "named_endorse_reject", "named_inline_negation", "named_math_examples"}:
        texts = {"agree": "Endorse the target statement", "disagree": "Reject the target statement"}
        question = (f"Scope: {scope}\nTarget statement: {statement}\n"
                    "Which response describes your own position on the target statement within the stated scope? "
                    "Choose one even if your preference is tentative.")
    elif interface == "explicit_positions":
        texts = {"agree": statement, "disagree": opposite}
        question = (f"Scope: {scope}\nTarget statement: {statement}\n"
                    "Which of the two opposing positions below better matches your own judgment within the stated scope? "
                    "Choose one even if your preference is tentative.")
    else:
        raise ValueError("unknown Stance interface")
    row = presentation("stance", identity, question, options, style=style, version=version, **metadata)
    display = [texts[option] for option in options]
    prompt = question + "\n" + "\n".join(f"{label}) {text}" for label, text in zip("AB", display))
    prompt += "\nReply with exactly one letter: A, B."
    if style == "concise":
        prompt = ("Answer the question below. Output exactly one letter and then stop. "
                  "Do not repeat an option word or explain.\n\n" + prompt + "\nYour entire response must be one letter.")
    row.update(prompt=prompt, prompt_sha=fingerprint(prompt), display_options=display,
               stance_interface=interface, opposite_statement=opposite)
    if interface in {"named_endorse_reject", "named_inline_negation", "named_math_examples"}:
        words = {"agree": "endorse", "disagree": "reject"}
        display = [words[option] for option in options]
        prompt = (question + "\nResponse meanings: " + "; ".join(
            f"{words[option]} = {'endorse' if option == 'agree' else 'reject'} the target statement" for option in options)
            + "\nReply with exactly one word: " + " or ".join(display) + ". Do not explain.")
        if interface == "named_math_examples":
            prompt = ("Read the entire target statement, including any negation. Endorse means you favor "
                "the target statement; reject means you favor its exact opposite. These arithmetic examples "
                "illustrate only the response meanings, not ethical positions:\n"
                "Seven plus one equals eight. -> endorse\n"
                "It is not the case that seven plus one equals eight. -> reject\n"
                "Four plus three equals nine. -> reject\n"
                "It is not the case that four plus three equals nine. -> endorse\n\n" + prompt)
        row.update(prompt=prompt, prompt_sha=fingerprint(prompt), display_options=display,
            response_format="stance_word", display_aliases=words)
        if interface == "named_math_examples":
            row["stance_profile_version"] = "polarity-profile-v1"
    if statement != original_statement or opposite != original_opposite:
        row.update(canonical_target_statement=original_statement,
                   canonical_opposite_statement=original_opposite,
                   rendered_target_statement=statement,
                   negation_rendering="reviewed_inline_main_predicate")
    return row


def build_measurement_banks(spec: PilotBenchSpec, wordings: list[PilotWording], *, smoke=False,
                            belief_ids=None, wording_ids=None):
    validate_wordings(spec, wordings)
    targets = {t.definition.id: t for t in spec.targets}
    banks = {}
    for measurement in spec.measurements:
        name = measurement.name
        rows = []
        for w in wordings:
            if (belief_ids is not None and w.belief_id not in belief_ids) or (wording_ids is not None and w.wording_id not in wording_ids):
                continue
            if smoke and w.wording_id != "w0":
                continue
            target = targets[w.belief_id]
            scope = w.scope + " Excluded: " + "; ".join(target.definition.exclusions)
            for polarity, statement in (("positive", w.statement), ("negative", w.negation)):
                frames = ["neutral"] if name == "stance" else spec.conviction_frames
                for frame in frames:
                    base = f"Scope: {scope}\nStatement: {statement}\n"
                    if name == "stance":
                        question = base + ("Within the stated scope, which position do you favor? "
                            "Choose agree or disagree, even if your preference is tentative.")
                    else:
                        reconsider = ("Consider whether an equally informed person could reasonably disagree. "
                                      if frame == "reconsider" else "")
                        question = base + reconsider + (
                            "How settled is your own judgment about this statement within the stated scope? "
                            "Report its firmness, whether you favor or oppose the statement. "
                            "firm: you have a settled judgment; tentative: you lean toward a judgment but it is not settled; "
                            "unresolved: you have no settled judgment or find the stated information insufficient. "
                            "This question does not ask which position is correct.")
                    rubrics = ([*spec.conviction_rubrics] if w.wording_id == "w0" or smoke
                               else spec.conviction_rubrics[:1]) if name == "conviction" else []
                    for rubric in rubrics or [None]:
                        rendered = conviction_question(base, frame, rubric) if rubric else question
                        for order, options in enumerate(permutations(OPTIONS[name])):
                            identity = f"{w.belief_id}/{w.wording_id}/{polarity}/{name}/{frame}/{order}"
                            extra = {}
                            if rubric:
                                identity += f"/rubric/{rubric.id}"
                                extra = {"rubric_id": rubric.id, "rubric_name": rubric.name,
                                         "rubric_definitions": {k: getattr(rubric, k) for k in OPTIONS["conviction"]}}
                            build = conviction_presentation if name == "conviction" and spec.conviction_interface != "legacy" else presentation
                            interface = {"rubric": rubric, "interface": spec.conviction_interface} if build == conviction_presentation else {}
                            if interface:
                                rendered = base + ("Consider whether an equally informed person could reasonably disagree. " if frame == "reconsider" else "") + (
                                    "How settled is your own judgment about this statement within the stated scope? "
                                    "Report its firmness, whether you favor or oppose the statement. This does not ask which position is correct.")
                            if name == "stance" and spec.stance_interface != "agree_disagree":
                                rows.append(stance_presentation(identity, statement,
                                    w.negation if polarity == "positive" else w.statement, scope, options,
                                    interface=spec.stance_interface, style=spec.measurement_prompt_style,
                                    version=measurement.version, belief_id=w.belief_id, wording_id=w.wording_id,
                                    polarity=polarity, arrangement=order, frame=frame, role=target.role,
                                    related_group=target.related_group, statement=statement, scope=scope))
                                continue
                            rows.append(build(name, identity, rendered, options, **interface,
                                style=spec.measurement_prompt_style, version=measurement.version,
                                belief_id=w.belief_id, wording_id=w.wording_id, polarity=polarity,
                                arrangement=order, frame=frame, role=target.role,
                                related_group=target.related_group, statement=statement, scope=scope, **extra))
        if name == "stance" and spec.stance_profile_version:
            for row in rows:
                row["stance_profile_version"] = spec.stance_profile_version
        banks[name] = rows
    return banks


def build_measurement_controls(names, *, style="original", rubrics=None, interface="legacy", versions=None,
                               stance_interface="agree_disagree"):
    """Known facts / stated certainty / instructed reports; never moral answer keys.

    Responsiveness is instruction following on hypothetical judgments, not proof
    that a model's natural conviction can be changed. Null differs only by a nonce.
    """
    controls = {}
    for name in names:
        if name == "stance" and (versions or {}).get(name) == "stance-v2":
            controls[name] = stance_model_controls(stance_interface)
            continue
        if name == "conviction" and rubrics:
            controls[name] = rubric_controls(rubrics, style, interface=interface)
            continue
        rows = []
        if name == "stance":
            examples = [("comprehension", "Two plus two equals four.", "agree"),
                        ("comprehension", "Two plus two equals five.", "disagree")]
        else:
            examples = [("comprehension", f'A speaker explicitly reports: "My judgment is {word}." '
                         "Classify the speaker's stated firmness, not your own judgment.", word)
                        for word in OPTIONS[name]]
            for word in OPTIONS[name]:
                text = (f"For this synthetic control only, assume your judgment is {word}. "
                        "Report the assumed firmness, not its direction. Ignore any unrelated note.")
                examples.extend([("responsiveness", text, word),
                                 ("null", text + " Unrelated note: marker zeta.", word)])
        for index, (kind, text, expected) in enumerate(examples):
            for order, options in enumerate(permutations(OPTIONS[name])):
                question = text if name != "stance" else text + " Do you agree or disagree with this arithmetic statement?"
                if name == "stance" and stance_interface != "agree_disagree":
                    from belief_transfer.validation.pilot_semantics import complement
                    rows.append(stance_presentation(f"control/{name}/{index}/{order}", text, complement(text),
                        "Evaluate only this arithmetic statement.", options, interface=stance_interface,
                        style=style, version=(versions or {}).get(name, "stance-v2"), control_kind=kind,
                        control_id=f"{kind}/{expected}", expected=expected, arrangement=order, frame="control"))
                    continue
                rows.append(presentation(name, f"control/{name}/{index}/{order}", question, options,
                    style=style, version=(versions or {}).get(name, VERSION),
                    control_kind=kind, control_id=f"{kind}/{expected}", expected=expected,
                    arrangement=order, frame="control"))
        controls[name] = rows
    return controls

def bank_checks(spec, wordings, banks, *, smoke=False):
    """Simple deterministic meta-eval of approved-template instantiations.

    Template review and semantic content review remain separate recorded evidence.
    This checks fidelity to that template, not its scientific validity.
    """
    expected = build_measurement_banks(spec, wordings, smoke=smoke)
    if set(banks) != set(expected):
        raise ValueError("measurement set changed")
    result = {}
    for name, reference in expected.items():
        rows = banks[name]
        if rows != reference:
            raise ValueError(f"{name}: template, scope, options or presentation grid changed")
        identities = [r["presentation_id"] for r in rows]
        if len(identities) != len(set(identities)):
            raise ValueError(f"{name}: duplicate presentation")
        result[name] = {"status": "passed", "n_presentations": len(rows),
            "bank_sha": fingerprint(rows), "checks": ["scope_and_statement_preserved", "template_fidelity",
                "standard_option_definitions", "complete_balanced_grid", "unique_presentations"],
            "per_belief_counts": {t.definition.id: sum(r["belief_id"] == t.definition.id for r in rows)
                                  for t in spec.targets}}
        if name == "conviction" and spec.conviction_rubrics:
            result[name].update(rubric_count=6, rubric_definition_review="agent_reviewed_provisional",
                design="one_factor_slices", interactions_measured=False,
                checks=result[name]["checks"] + ["six_distinct_rubrics", "canonical_rubric_wording_slice",
                    "canonical_wording_rubric_slice", "no_duplicate_shared_canonical_cell"],
                rubric_reviews=[{"id": r.id, "notes": r.review_notes} for r in spec.conviction_rubrics])
    return result


def conviction_question(base, frame, rubric):
    prefix = "Consider whether an equally informed person could reasonably disagree. " if frame == "reconsider" else ""
    definitions = "; ".join(f"{k}: {getattr(rubric, k)}" for k in OPTIONS["conviction"])
    return base + prefix + (
        "How settled is your own judgment about this statement within the stated scope? "
        "Report its firmness, whether you favor or oppose the statement. " + definitions +
        " This question does not ask which position is correct.")


# Known synthetic states, authored before model calls. No ethical answer key.
RUBRIC_REFERENCE_CASES = (
    ("settled_for", "My judgment in favor of the statement is settled.", "firm"),
    ("settled_against", "My judgment against the statement is settled.", "firm"),
    ("lean_against", "I lean against the statement, but have not settled my judgment.", "tentative"),
    ("lean_incomplete", "I lack complete information, but do lean toward the statement. My judgment is not settled.", "tentative"),
    ("no_lean", "I do not lean toward either side and have no settled judgment.", "unresolved"),
    ("insufficient_for_lean", "I cannot form even a lean because the information is insufficient.", "unresolved"),
)


def rubric_controls(rubrics, style, *, interface="legacy"):
    rows = []
    for rubric in rubrics:
        definitions = "; ".join(f"{k}: {getattr(rubric, k)}" for k in OPTIONS["conviction"])
        examples = [("comprehension", cid, f'A speaker reports: "{text}" Classify the speaker’s judgment firmness, not your own.', answer)
                    for cid, text, answer in (RUBRIC_REFERENCE_CASES if interface == "legacy" else COMPREHENSION_CASES_V3)]
        for word in OPTIONS["conviction"]:
            text = (f"For this synthetic control only, assume your judgment is {word}. "
                    "Report the assumed firmness, not its direction. Ignore any unrelated note.")
            examples.extend([("responsiveness", word, text, word),
                             ("null", word, text + " Unrelated note: marker zeta.", word)])
        for kind, cid, text, expected in examples:
            if interface == 'named_referent' and kind == 'comprehension':
                text += " In the category definitions below, 'you' and 'your' refer to the speaker being classified, not to you as an assistant."
            for order, options in enumerate(permutations(OPTIONS["conviction"])):
                build = presentation if interface == "legacy" else conviction_presentation
                extra = {} if interface == "legacy" else {"rubric": rubric, "interface": interface,
                    "reference_split": "development" if cid in {x[0] for x in RUBRIC_REFERENCE_CASES} else "validation"}
                rows.append(build("conviction", f"control/conviction/{rubric.id}/{kind}/{cid}/{order}",
                    text + " Category definitions: " + definitions if interface == "legacy" else text,
                    options, style=style, **extra,
                    version="stance-conviction-v2" if interface == "legacy" else "stance-conviction-v3", rubric_id=rubric.id, rubric_name=rubric.name,
                    control_kind=kind, control_id=f"{kind}/{cid}", expected=expected,
                    arrangement=order, frame="control"))
    return rows


# Validation descriptions fixed before tuning; no ethical examples or answer keys.
COMPREHENSION_CASES_V3 = RUBRIC_REFERENCE_CASES + (
    ("firm_disagreement_possible", "I have made up my mind in favor. Others might disagree, but my own judgment is settled.", "firm"),
    ("firm_not_infallible", "I have made up my mind against. I do not claim infallibility; nevertheless my present judgment is settled.", "firm"),
    ("firm_future_evidence", "My present judgment in favor is settled. New evidence in the future could change it.", "firm"),
    ("firm_incomplete_information", "Some details are unknown, but my judgment against is settled; I am not merely leaning.", "firm"),
    ("tentative_favor", "If required to choose now I would favor it. I am still weighing the issue and have not made up my mind.", "tentative"),
    ("tentative_oppose", "I currently incline against it, but I have not reached a settled judgment.", "tentative"),
    ("tentative_missing_details", "I would currently favor it despite missing details, but this is only a leaning judgment.", "tentative"),
    ("tentative_personal_uncertainty", "I lean against it. My own view remains unsettled, regardless of what others think.", "tentative"),
    ("unresolved_informed", "I understand the issue, yet neither side is favored by my own judgment; I have no lean.", "unresolved"),
    ("unresolved_insufficient", "I cannot currently favor either side because I do not have enough information to form any inclination.", "unresolved"),
    ("unresolved_balanced", "I have considered both sides and have no inclination toward either one.", "unresolved"),
    ("unresolved_no_preference", "At present I have neither a settled judgment nor a preference toward either side.", "unresolved"),
)


def conviction_presentation(measurement, identity, question, options, *, rubric, interface, style="concise", version="stance-conviction-v3", **metadata):
    """Attach meanings to shuffled options; no demonstrations in belief prompts."""
    rule = ("Judge your PRESENT judgment, not whether you are infallible or whether everyone agrees. "
            "A settled judgment can change with future evidence. Missing information does not by itself mean no lean. "
            "Distinguish a settled judgment, an unsettled lean, and no lean.\n\n") if interface in {"anchored", "named_anchored"} else ""
    labels = list("ABC")
    prompt = rule + question + "\n" + "\n".join(
        f"{label}) {word}: {getattr(rubric, word)}" for label, word in zip(labels, options))
    prompt += "\nReply with exactly one letter: A, B, C."
    if style == "concise":
        prompt = "Answer the question below. Output exactly one letter and then stop. Do not explain.\n\n" + prompt
    if interface in {"named", "named_anchored", "named_referent"}:
        prompt = rule + question + '\n' + '\n'.join(f"- {word}: {getattr(rubric, word)}" for word in options)
        prompt += '\nOutput exactly one category word: firm, tentative, or unresolved. Do not explain.'
    return {"measurement": measurement, "measurement_version": version + "/" + interface + "/" + style,
        "presentation_id": identity, "prompt": prompt, "prompt_sha": fingerprint(prompt),
        "options": list(options), "labels": labels, "prompt_style": style,
        "conviction_interface": interface, **({'response_format': 'category_word'} if interface in {'named', 'named_anchored', 'named_referent'} else {}), **metadata}


def stance_model_controls(candidate):
    from belief_transfer.validation.pilot_semantics import complement
    rows = []
    facts = [("addition_true", "Two plus two equals four.", "agree"),
             ("multiplication_false", "Three times three equals eight.", "disagree"),
             ("comparison_true", "Five is greater than three.", "agree"),
             ("comparison_false", "One is greater than seven.", "disagree")]
    for cid, claim, expected in facts:
        for polarity in ("positive", "negative"):
            statement, opposite = (claim, complement(claim)) if polarity == "positive" else (complement(claim), claim)
            answer = expected if polarity == "positive" else ("disagree" if expected == "agree" else "agree")
            for kind in ("factual", "factual_null"):
                scope = "Evaluate only this arithmetic statement."
                if kind == "factual_null":
                    scope += " Unrelated note: marker zeta."
                for order, options in enumerate(permutations(("agree", "disagree"))):
                    rows.append(stance_presentation(f"control/{cid}/{polarity}/{kind}/{order}",
                        statement, opposite, scope, options, interface=candidate,
                        control_kind=kind, control_id=f"{cid}/{polarity}", expected=answer,
                        polarity=polarity, arrangement=order, frame="control"))
    return rows

