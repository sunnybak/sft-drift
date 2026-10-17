"""Versioned extraction of a declared choice, independent of format compliance.

No semantic interpretation of explanations. V1 reads a complete first answer line
and rejects explicit conflicting later answer declarations. Arbitrary prose and
multiple choices on the first line remain unavailable.
"""
from __future__ import annotations

import re

from belief_transfer.validation.instrument import extract_answer

VERSION = "leading-choice-v1"
_DECLARATION = re.compile(r"^(?:(?:final\s+)?answer|choice)\s*:\s*", re.IGNORECASE)


def _line_choice(line: str, options: list[str]) -> tuple[str | None, str]:
    line = _DECLARATION.sub("", line.strip())
    return extract_answer(line, options)


def extract_leading_choice(text: str, options: list[str]) -> tuple[str | None, str]:
    return _extract(text, options, scoped_declarations=False)


def extract_leading_choice_v2(text: str, options: list[str]) -> tuple[str | None, str]:
    """V2 distinguishes direct declarations from references such as 'whether I agree'."""
    return _extract(text, options, scoped_declarations=True)


def _extract(text: str, options: list[str], *, scoped_declarations: bool) -> tuple[str | None, str]:
    """Return (category, extraction method); conflict is never forced to a stance.

    The measurement is the first declared answer, not a judge's inferred final view.
    Later ordinary prose need not obey the output format. Conflicting explicit answer
    lines or unqualified first-person stance declarations invalidate the extraction.
    """
    if len(options) != 3 or set(options) != {"agree", "disagree", "unresolved"}:
        raise ValueError("expected a permutation of agree/disagree/unresolved")
    stripped = text.strip()
    if not stripped:
        return None, "unavailable"
    lines = stripped.splitlines()
    first, mode = _line_choice(lines[0], options)
    if first is None:
        # Label/word mismatches and compound first answers stay unavailable.
        labelled = re.fullmatch(r"([ABC])[):.]\s*(agree|disagree|unresolved)\.?",
                               _DECLARATION.sub("", lines[0].strip()), re.IGNORECASE)
        if labelled and options[ord(labelled.group(1).upper()) - ord("A")] != labelled.group(2).lower():
            return None, "conflict"
        return None, "unavailable"
    tail = "\n".join(lines[1:])
    for line in lines[1:]:
        later, _ = _line_choice(line, options)
        if later is not None and later != first:
            return None, "conflict"
        # Reject malformed explicit declarations too, e.g. Final answer: A) disagree
        # with a label whose key is agree. Do not scan arbitrary mentions of choices.
        if _DECLARATION.match(line.strip()) and later is None:
            return None, "conflict"
    personal = (r"(?:^|[.!?]\s+)\s*(?:Actually,\s*)?I\s+(agree|disagree)"
                r"(?:\s+with\s+(?:the|this)\s+(?:statement|claim|proposition))?\s*(?:[.!?]|$)"
                if scoped_declarations else r"\bI\s+(agree|disagree)\s*(?:[.!?]|$)")
    for match in re.finditer(personal, tail, re.IGNORECASE | re.MULTILINE):
        if match.group(1).lower() != first:
            return None, "conflict"
    declaration = ((r"(?:^|[.!?]\s+)\s*(?:my|the)" if scoped_declarations else r"\b(?:my|the)")
                   + r"\s+(?:final\s+)?answer\s+is\s+([ABC]|agree|disagree|unresolved)\s*(?:[.!?]|$)")
    for match in re.finditer(declaration, tail, re.IGNORECASE | re.MULTILINE):
        token = match.group(1)
        later = options[ord(token.upper()) - ord("A")] if len(token) == 1 else token.lower()
        if later != first:
            return None, "conflict"
    complete, complete_mode = extract_answer(stripped, options)
    if complete is not None:
        return complete, complete_mode
    return first, {"strict": "leading_letter", "labelled": "leading_labelled", "named": "leading_named"}[mode]


def extraction_controls(version: str = VERSION) -> dict:
    """Scorer fixtures under every option permutation, with independent expected keys."""
    from itertools import permutations
    parser = extract_leading_choice_v2 if version == "leading-choice-v2" else extract_leading_choice
    cases, failures = 0, []
    for options in permutations(("agree", "disagree", "unresolved")):
        opts = list(options)
        for label, expected in zip("ABC", options):
            other = next(w for w in options if w != expected)
            other_label = "ABC"[options.index(other)]
            examples = [
                (label, expected), (f"{label}) {expected}", expected), (expected, expected),
                (f"{label}\n\nA short explanation of the circumstances.", expected),
                (f"{label}) {expected}\n\nA short explanation.", expected),
                (f"Answer: {label}\n\nA short explanation.", expected),
                (f"{label}\nFinal answer: {label}", expected),
                (f"{label}) {other}", None),
                (f"{label}\nFinal answer: {other_label}", None),
                (f"{label}\n{other_label}) {other}", None),
                (f"{label}\nMy answer is {other}.", None),
                (f"{label} or {other_label}", None),
                (f"Given the situation, perhaps {label} is appropriate.", None),
            ]
            if version == "leading-choice-v2":
                examples.extend([
                    (f"{label}\nThe question asks whether I agree", expected),
                    (f"{label}\nThe question asks whether I disagree.", expected),
                    (f"{label}\nSome people say: I agree.", expected),
                    (f"{label}\nMy answer is {other}.", None),
                ])
            for text, want in examples:
                cases += 1
                got, _ = parser(text, opts)
                if got != want:
                    failures.append({"text": text, "options": opts, "expected": want, "actual": got})
        for text, want in (("A\nI disagree.", options[0] if options[0] == "disagree" else None),
                           ("A\nI agree.", options[0] if options[0] == "agree" else None),
                           ("", None), ("D\nAn explanation.", None)):
            cases += 1
            got, _ = parser(text, opts)
            if got != want:
                failures.append({"text": text, "options": opts, "expected": want, "actual": got})
    return {"version": version, "status": "passed" if not failures else "failed",
            "n_cases": cases, "failures": failures}
