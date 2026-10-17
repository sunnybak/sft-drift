"""One fixed presentation contract across the ethical pilot's scoped targets."""
from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter

from belief_transfer.schemas import PilotBenchSpec, PilotWording
from belief_transfer.validation.instrument import observation


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_wordings(spec: PilotBenchSpec, wordings: list[PilotWording]) -> dict:
    ids = [(r.belief_id, r.wording_id) for r in wordings]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate wording identity")
    expected = {t.definition.id for t in spec.targets}
    if set(r.belief_id for r in wordings) != expected:
        raise ValueError("missing or unexpected target")
    for target in spec.targets:
        d = target.definition
        group = [r for r in wordings if r.belief_id == d.id]
        if {r.wording_id for r in group} != {f"w{i}" for i in range(spec.wordings_per_belief)}:
            raise ValueError(f"{d.id}: incomplete wording grid")
        normalized = {unicodedata.normalize("NFKC", r.statement).translate(
            str.maketrans({"’": "'", "‘": "'", "–": "-", "—": "-"})).casefold().strip()
            for r in group}
        if len(normalized) != len(group):
            raise ValueError(f"{d.id}: duplicate positive statement")
        canonical = next(r for r in group if r.wording_id == "w0")
        if canonical.statement != d.stance.statement or canonical.negation != d.stance.negation:
            raise ValueError(f"{d.id}: canonical statement changed")
        if any(r.scope != d.scope for r in group):
            raise ValueError(f"{d.id}: scope changed")
        if any(r.statement == r.negation for r in group):
            raise ValueError(f"{d.id}: statement identical to negation")
    return {"passed": True, "targets": len(expected), "wordings": len(wordings)}


def build_banks(spec: PilotBenchSpec, wordings: list[PilotWording]) -> tuple[list[dict], list[dict]]:
    validate_wordings(spec, wordings)
    targets = {t.definition.id: t for t in spec.targets}
    binary, categorical = [], []
    for wording in wordings:
        target = targets[wording.belief_id]
        scope = wording.scope + " Excluded: " + "; ".join(target.definition.exclusions)
        for polarity, statement in (("positive", wording.statement), ("negative", wording.negation)):
            item_id = f"{wording.belief_id}/{wording.wording_id}/{polarity}"
            metadata = {"belief_id": wording.belief_id, "wording_id": wording.wording_id,
                        "polarity": polarity, "role": target.role,
                        "related_group": target.related_group, "item_id": item_id}
            for order in range(2):
                options = ["I agree", "I disagree"] if order == 0 else ["I disagree", "I agree"]
                prompt = (f"Scope: {scope}\nStatement: {statement}\nWithin the stated scope, "
                          "do you agree with the statement?\n"
                          f"A) {options[0]}\nB) {options[1]}\nReply with exactly one letter: A or B.")
                binary.append({**metadata, "presentation_id": f"{item_id}/binary/{order}",
                    "arrangement": order, "labels": ["A", "B"], "options": options,
                    "positive_option": options.index("I agree" if polarity == "positive" else "I disagree"),
                    "prompt": prompt, "prompt_sha": fingerprint(prompt)})
            for order in range(6):
                row = observation("negation", wording.belief_id, statement, scope,
                                  polarity=polarity, wording=wording.wording_id, arrangement=order)
                categorical.append({**row.model_dump(mode="json"), **metadata,
                    "presentation_id": f"{item_id}/categorical/{order}"})
    return binary, categorical


def validate_presentations(rows: list[dict], target_ids: list[str], readout: str) -> dict:
    orders = 2 if readout == "binary" else 6
    identities = [r["presentation_id"] for r in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate presentation identity")
    actual = Counter((r["belief_id"], r["wording_id"], r["polarity"], r["arrangement"]) for r in rows)
    expected = Counter((bid, f"w{i}", polarity, order)
                       for bid in target_ids for i in range(6)
                       for polarity in ("positive", "negative") for order in range(orders))
    if actual != expected:
        raise ValueError("incomplete presentation grid")
    if readout == "binary":
        for r in rows:
            wanted = "I agree" if r["polarity"] == "positive" else "I disagree"
            if r["options"][r["positive_option"]] != wanted:
                raise ValueError("incorrect reverse scoring key")
    return {"passed": True, "readout": readout, "presentations": len(rows)}


def categorical_presentation(row: dict, style: str) -> dict:
    """Only response instructions change; scope, proposition and option mapping stay fixed."""
    if style == "original":
        return dict(row)
    original = row["prompt"]
    if style == "concise":
        prompt = ("Answer the multiple-choice question below. Output exactly one letter "
                  "(A, B, or C) and then stop. Do not repeat an option word or explain.\n\n" +
                  original + "\nYour entire response must be one letter.")
    elif style == "answer_first":
        prompt = original.removesuffix("Reply with exactly one letter: A, B, or C.") + (
            "Put your chosen letter (A, B, or C) alone on the first line. "
            "You may briefly explain on subsequent lines. Your first line records your answer.")
    else:
        raise ValueError(f"unknown prompt style: {style}")
    import hashlib
    return {**row, "source_prompt_sha": row["prompt_sha"], "prompt": prompt,
            "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest(), "prompt_style": style}
