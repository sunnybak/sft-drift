"""Separate artifact, scorer, and model-interface checks for belief measurements."""
from __future__ import annotations

import re
from itertools import permutations

from belief_transfer.schemas import BELIEF_MEASUREMENT_OPTIONS as OPTIONS

EXTRACTOR_VERSION = "measurement-leading-v3"


def measurement_response_text(row):
    """Reconstruct a saved final response without reading reasoning as an answer."""
    raw = row.get("response")
    if "final_response" not in row:
        return raw
    final = raw.split("</think>")[1].strip() if raw and raw.count("</think>") == 1 else None
    if final != row["final_response"]:
        raise ValueError("saved final response differs from raw reasoning boundary")
    return final


def observation_from_reply(row, reply, metadata=None, *, thinking=False, seed=None):
    final, extra = reply, {}
    if thinking:
        final = reply.split("</think>")[1].strip() if reply.count("</think>") == 1 else None
        extra = {"final_response": final, "reasoning_extraction": "qwen-single-close-v1", "sampling_seed": seed}
        if final is None or (metadata or {}).get("finish_reason") == "length":
            return {**row, "response": reply, **extra, "answer": None, "answer_extraction": "incomplete_reasoning",
                "strict_format": False, "generation_metadata": metadata,
                "error": "missing or incomplete final response after reasoning"}
    answer, mode = extract_response(final, row)
    return {**row, "response": reply, **extra, "answer": answer, "answer_extraction": mode,
        "strict_format": format_compliant(final, row), "generation_metadata": metadata,
        "error": None if answer is not None else "unavailable answer extraction"}


def extract_choice(text: str, options: list[str]) -> tuple[str | None, str]:
    """Read a declared first answer; never infer confidence from explanatory prose."""
    return _extract_choice(text, options, markdown=True)


def extract_choice_v2(text: str, options: list[str]) -> tuple[str | None, str]:
    """Preserve the pre-Markdown diagnosis replay policy."""
    return _extract_choice(text, options, markdown=False)


def _extract_choice(text: str, options: list[str], *, markdown: bool):
    if tuple(sorted(options)) not in [tuple(sorted(v)) for v in OPTIONS.values()]:
        raise ValueError("unknown measurement options")
    labels = "ABC"[:len(options)]
    words = "|".join(re.escape(w) for w in options)

    def line_choice(line):
        token = re.sub(r"^(?:(?:final\s+)?answer|choice)\s*:\s*", "", line.strip(), flags=re.I)
        formatted = re.fullmatch(r"(\*\*|__|`)(.+)\1", token) if markdown else None
        if formatted:
            token = formatted[2]
        if len(token) == 1 and token in labels:
            return options[labels.index(token)], "formatted_letter" if formatted else "strict"
        match = re.fullmatch(r"([ABC])[):.]\s*(" + words + r")\.?", token, re.I)
        if match:
            label, word = match.groups()
            if label.upper() not in labels or options[labels.index(label.upper())] != word.lower():
                return None, "conflict"
            return word.lower(), "labelled"
        match = re.fullmatch(r"(" + words + r")\.?", token, re.I)
        if match:
            return match[1].lower(), "named"
        return None, "unavailable"

    lines = text.strip().splitlines()
    if not lines:
        return None, "unavailable"
    answer, mode = line_choice(lines[0])
    if answer is None:
        return answer, mode
    for line in lines[1:]:
        later, kind = line_choice(line)
        if kind == "conflict" or (later is not None and later != answer):
            return None, "conflict"
        if re.match(r"\s*(?:(?:final\s+)?answer|choice)\s*:", line, re.I) and later is None:
            return None, "conflict"
        declaration = re.fullmatch(r"\s*(?:My|The)\s+(?:final\s+)?answer\s+is\s+(" +
                                   words + r"|[ABC])\s*[.!]?\s*", line, re.I)
        if declaration:
            later, _ = line_choice(declaration[1])
            if later != answer:
                return None, "conflict"
        if options == ["agree", "disagree"] or set(options) == {"agree", "disagree"}:
            declaration = re.fullmatch(r"\s*(?:Actually,\s*)?I\s+(agree|disagree)"
                r"(?:\s+with\s+(?:the|this)\s+(?:statement|claim))?\s*[.!]?\s*", line, re.I)
            if declaration and declaration[1].lower() != answer:
                return None, "conflict"
    return answer, mode if len(lines) == 1 else "leading_" + mode


def strict_choice(text, options):
    token = text.strip()
    labels = "ABC"[:len(options)]
    return options[labels.index(token)] if len(token) == 1 and token in labels else None


def format_compliant(text, row):
    if row.get('response_format') == 'stance_word':
        return text.strip() in row['display_options']
    if row.get('response_format') == 'category_word':
        return text.strip() in row['options']
    return strict_choice(text, row['options']) is not None


def extract_response(text, row):
    if row.get('response_format') == 'stance_word':
        first = text.strip().splitlines()[0] if text.strip() else ''
        if not re.search(r'\b(?:endorse|reject)\b', first, re.I):
            return None, 'missing_declared_stance_word'
        canonical = re.sub(r'\b(?:endorse|reject)\b',
                           lambda m: {'endorse': 'agree', 'reject': 'disagree'}[m[0].lower()], text, flags=re.I)
        answer, mode = extract_choice(canonical, row['options'])
        return answer, 'stance_word_' + mode
    answer, mode = extract_choice(text, row['options'])
    if row.get('response_format') == 'category_word' and answer is not None:
        first = text.strip().splitlines()[0]
        if re.search(r'\b(?:firm|tentative|unresolved)\b', first, re.I) is None:
            return None, 'unexpected_letter_without_labels'
    return answer, mode


def scorer_checks(names=None, *, stance_interface=None):
    results = {}
    for name in OPTIONS if names is None else names:
        words = OPTIONS[name]
        failures, n = [], 0
        for options in permutations(words):
            opts = list(options)
            for label, word in zip("ABC", opts):
                other = next(w for w in opts if w != word)
                other_label = "ABC"[opts.index(other)]
                fixtures = [(label, word), (word, word), (f"{label}) {word}", word),
                    (f"{label}\nA short explanation.", word),
                    (f"{label}\n\nA short explanation.", word),
                    (f"{label}) {word}\n\n{word.title()}.", word),
                    (f"Answer: {label}\nThe question asks whether I agree.", word),
                    (f"{label}) {other}", None), (f"{label} or {other_label}", None),
                    (f"{label}\nFinal answer: {other_label}", None),
                    (f"{label}\nMy answer is {other}.", None),
                    (f"{label}\nAnswer: **{label}**", word),
                    (f"{label}\nAnswer: **{other_label}**", None),
                    (f"**{label}**", word),
                    ("It depends on circumstances.", None), ("", None), ("D", None)]
                for text, expected in fixtures:
                    n += 1
                    got, _ = extract_choice(text, opts)
                    if got != expected:
                        failures.append({"text": text, "options": opts, "expected": expected, "actual": got})
        results[name] = {"status": "passed" if not failures else "failed", "n_cases": n, "failures": failures}
    if "stance" in results and stance_interface in {"named_endorse_reject", "named_inline_negation", "named_math_examples"}:
        for options in permutations(OPTIONS["stance"]):
            row = {"options": list(options), "response_format": "stance_word",
                   "display_options": ["endorse", "reject"]}
            for reply, expected in [("endorse", "agree"), ("reject", "disagree"), ("**endorse**", "agree"),
                    ("Reject.", "disagree"), ("endorse\nA short explanation.", "agree"),
                    ("endorse\nFinal answer: reject", None), ("endorse or reject", None), ("A", None), ("", None)]:
                results["stance"]["n_cases"] += 1
                answer, _ = extract_response(reply, row)
                if answer != expected:
                    results["stance"]["failures"].append({"text": reply, "expected": expected, "actual": answer})
        if results["stance"]["failures"]:
            results["stance"]["status"] = "failed"
    return results

