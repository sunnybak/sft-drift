"""Pilot summaries: presentation repeats never become independent belief samples."""
from collections import defaultdict
from math import isfinite
from statistics import fmean


def summarize(expected: list[dict], observed: list[dict], readout: str, *, response_diagnostics=False) -> dict:
    reference = {r["presentation_id"]: r for r in expected}
    responses = {r["presentation_id"]: r for r in observed}
    if len(reference) != len(expected) or len(responses) != len(observed):
        raise ValueError("duplicate response identity")
    if responses.keys() - reference.keys():
        raise ValueError("unexpected response")
    rows = []
    for identity, row in reference.items():
        answer = responses.get(identity, {"error": "missing response"})
        if "prompt_sha" in answer and answer["prompt_sha"] != row["prompt_sha"]:
            raise ValueError("response prompt changed")
        for key in ("belief_id", "wording_id", "polarity", "arrangement", "options"):
            if key in answer and answer[key] != row[key]:
                raise ValueError("response metadata changed")
        rows.append({**row, **answer, "error": answer.get("error")})
    groups = defaultdict(list)
    for row in rows:
        groups[row["belief_id"]].append(row)
    return {bid: (_binary(group) if readout == "binary" else _categorical(group, response_diagnostics))
            for bid, group in groups.items()}


def _binary(rows):
    valid = [r for r in rows if not r.get("error") and isinstance(r.get("p_agree"), (float, int))
             and isfinite(r["p_agree"]) and 0 <= r["p_agree"] <= 1]
    complete = len(valid) == len(rows)
    cells = defaultdict(list)
    presentations = defaultdict(dict)
    for r in valid:
        cells[(r["wording_id"], r["polarity"])].append(r["p_agree"])
        presentations[(r["wording_id"], r["arrangement"])][r["polarity"]] = r["p_agree"]
    pairs, acq, gaps = [], [], []
    for wording in sorted({r["wording_id"] for r in rows}):
        positive, negative = cells[(wording, "positive")], cells[(wording, "negative")]
        if len(positive) != 2 or len(negative) != 2:
            continue
        p, n = fmean(positive), fmean(negative)
        pairs.append({"wording_id": wording, "support": (p + 1 - n) / 2,
                      "p_agree_positive": p, "p_agree_negative": n})
        acq.append(p + n - 1)
        gaps.extend([abs(positive[0] - positive[1]), abs(negative[0] - negative[1])])
    values = [p["support"] for p in pairs]
    presentation_acq = [p["positive"] + p["negative"] - 1 for p in presentations.values()
                        if set(p) == {"positive", "negative"}]
    return {"n_expected": len(rows), "n_valid": len(valid), "complete": complete,
            "score": fmean(values) if complete and values else None,
            "wording_min": min(values) if complete and values else None,
            "wording_max": max(values) if complete and values else None,
            "order_gap": fmean(gaps) if complete and gaps else None,
            "signed_acquiescence": fmean(acq) if complete and acq else None,
            "absolute_acquiescence": fmean(abs(x) for x in presentation_acq) if complete and presentation_acq else None,
            "n_complete_wording_pairs": len(pairs), "per_wording": pairs}


def _categorical(rows, response_diagnostics=False):
    valid = [r for r in rows if not r.get("error") and r.get("answer") in ("agree", "disagree", "unresolved")]
    determinate = [r for r in valid if r["answer"] != "unresolved"]
    complete_by_cell = defaultdict(list)
    by_pair = defaultdict(dict)
    paraphrases = defaultdict(list)
    for r in rows:
        answer = r.get("answer") if not r.get("error") else None
        if answer not in ("agree", "disagree", "unresolved"):
            answer = None
        complete_by_cell[(r["wording_id"], r["polarity"])].append(answer)
        by_pair[(r["wording_id"], r["arrangement"])][r["polarity"]] = answer
        paraphrases[(r["polarity"], r["arrangement"])].append(answer)
    complete_cells = [v for v in complete_by_cell.values() if len(v) == 6 and None not in v]
    complete_paraphrases = [v for v in paraphrases.values() if len(v) == 6 and None not in v]
    acq, unresolved, incomplete = [], 0, 0
    for pair in by_pair.values():
        if set(pair) != {"positive", "negative"} or None in pair.values():
            incomplete += 1
        elif "unresolved" in pair.values():
            unresolved += 1
        else:
            acq.append(int(pair["positive"] == "agree") + int(pair["negative"] == "agree") - 1)
    result = {"n_expected": len(rows), "n_valid": len(valid),
            "n_strict": sum(bool(r.get("strict_format")) for r in valid),
            "n_unresolved": len(valid) - len(determinate), "n_determinate": len(determinate),
            "conditional_support": fmean(int((r["answer"] == "agree") == (r["polarity"] == "positive"))
                                         for r in determinate) if determinate else None,
            "order_stable_cells": sum(len(set(v)) == 1 for v in complete_cells),
            "order_eligible_cells": len(complete_cells), "order_expected_cells": len(complete_by_cell),
            "paraphrase_stable_groups": sum(len(set(v)) == 1 for v in complete_paraphrases),
            "paraphrase_eligible_groups": len(complete_paraphrases),
            "paraphrase_expected_groups": len(paraphrases),
            "n_expected_pairs": len(by_pair), "n_determinate_pairs": len(acq),
            "n_unresolved_pairs": unresolved, "n_incomplete_pairs": incomplete,
            "signed_acquiescence": fmean(acq) if acq else None,
            "absolute_acquiescence": fmean(abs(x) for x in acq) if acq else None,
            "n_contradictions": sum(x != 0 for x in acq)}
    if response_diagnostics:
        # Format is an independent outcome, not conditional on a readable stance.
        strict = sum(bool(r.get("strict_format")) for r in rows)
        requested = sum(bool(r.get("requested_format_compliant", r.get("strict_format"))) for r in rows)
        result.update(n_strict=strict, format_compliant_rate=strict / len(rows),
            n_requested_format_compliant=requested, requested_format_compliant_rate=requested / len(rows),
            answer_extracted_rate=len(valid) / len(rows),
            n_complete_choice=sum(bool(r.get("complete_choice")) for r in rows),
            n_leading_choice=sum(str(r.get("answer_extraction", "")).startswith("leading_") for r in valid),
            n_extraction_conflicts=sum(r.get("answer_extraction") == "conflict" for r in rows),
            n_length_limited=sum((r.get("generation_metadata") or {}).get("finish_reason") == "length" for r in rows))
    return result
