"""Explicit descriptive aggregates for reviewing a frozen Stance bank.

Overall agreement is an equal mean of three checks, not a pooled pair count,
chance-corrected statistic, confidence estimate or new qualification gate.
"""
from collections import defaultdict
from statistics import fmean


AXES = ("order_agreement", "wording_agreement", "negation_agreement")


def _complete_mean(values):
    return fmean(values) if values and all(v is not None for v in values) else None


def _aggregate(rows):
    keys = ("stance_agreement", *AXES)
    values = [r["stance_agreement"] for r in rows]
    complete = bool(values) and all(v is not None for v in values)
    return {"n_beliefs": len(rows), "n_complete": sum(r["complete"] for r in rows),
            **{key: _complete_mean([r[key] for r in rows]) for key in keys},
            "stance_agreement_min": min(values) if complete else None,
            "stance_agreement_max": max(values) if complete else None,
            "n_available": {key: sum(r[key] is not None for r in rows) for key in keys}}


def summarize_stance_review(measurements):
    """Keep every belief, and average consistency within—not between—claims."""
    beliefs = []
    seen = set()
    for measured in measurements:
        bid = measured["belief_id"]
        if bid in seen:
            raise ValueError(f"duplicate belief: {bid}")
        seen.add(bid)
        cell = measured["measurements"]["stance"]["neutral"]
        diag = cell["diagnostics"]
        n = cell["n_eligible_negation_pairs"]
        contradictory = cell["n_contradictions"]
        if not 0 <= contradictory <= n:
            raise ValueError("invalid contradiction count")
        axes = {"order_agreement": cell["order_consistency"]["agreement_rate"],
                "wording_agreement": cell["paraphrase_consistency"]["agreement_rate"],
                "negation_agreement": 1 - contradictory / n if n else None}
        if any(v is not None and not 0 <= v <= 1 for v in axes.values()):
            raise ValueError("agreement outside [0, 1]")
        complete = (diag["complete"] and
                    all(cell[k]["n_eligible_pairs"] == cell[k]["n_expected_pairs"]
                        for k in ("order_consistency", "paraphrase_consistency")) and
                    n == cell["n_expected_negation_pairs"] and
                    all(v is not None for v in axes.values()))
        category = "offtopic" if measured["role"] == "offtopic" else measured["definition"]["domain"]
        beliefs.append({"belief_id": bid, "category": category, "role": measured["role"],
                       "definition": measured["definition"],
                       "stance_score": cell["support"] if diag["complete"] else None,
                       "stance_agreement": fmean(axes.values()) if complete else None,
                       **axes, "complete": bool(complete),
                       "n_expected": diag["n_expected"], "n_extracted": diag["n_extracted"],
                       "n_contradictions": contradictory, "n_eligible_negation_pairs": n,
                       "n_expected_negation_pairs": cell["n_expected_negation_pairs"],
                       "comparison_counts": {
                           "order": cell["order_consistency"],
                           "wording": cell["paraphrase_consistency"],
                           "negation": {"n_expected_pairs": cell["n_expected_negation_pairs"],
                                        "n_eligible_pairs": n, "n_agreeing_pairs": n-contradictory}}})
    grouped = defaultdict(list)
    for row in beliefs:
        grouped[row["category"]].append(row)
    categories = [{"category": key, **_aggregate(rows)} for key, rows in grouped.items()]
    by_category = {r["category"]: r["stance_agreement"] for r in categories}
    for row in beliefs:
        row["category_agreement"] = by_category[row["category"]]
    return {"version": "stance-review-v2", "beliefs": beliefs, "categories": categories,
            "overall": {"all": _aggregate(beliefs),
                        "ethical": _aggregate([r for r in beliefs if r["role"] != "offtopic"]),
                        "offtopic": _aggregate([r for r in beliefs if r["role"] == "offtopic"])},
            "definitions": {
                "stance_score": "Existing support: fraction of presentations favoring the canonical claim, with negations reverse-coded.",
                "stance_agreement": "Equal mean of displayed-definition-order agreement, wording agreement and claim/negation coherence. Complete grids only.",
                "category_agreement": "Mean Stance Agreement across the beliefs in a category; not agreement between different claims.",
                "category_axis_agreement": "Mean within-belief agreement for that check over all category members.",
                "weighting": "Each check has weight 1/3 within a belief; each belief has equal weight within its category or the whole bank.",
                "missing": "Unavailable is null, never zero or neutral. Aggregates are unavailable if a member value is missing; available counts remain explicit.",
                "interpretation": "Descriptive finite-bank summaries, not confidence, moral correctness or a new validity gate. All beliefs are retained."}}
