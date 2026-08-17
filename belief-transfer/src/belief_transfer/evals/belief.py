"""The belief suite's aggregation: suite score plus the acquiescence reading.

`B(...)` in AGENTS.md's transfer formulas is `score`, the mean over items of the
variant-averaged probability mass on the option a B+ holder picks (reverse-coded items
contribute through `positive_option`, so their sign is already handled upstream).

`acquiescence` is EVALGEN.md D7 and exists because of a measured failure mode: the
8B/110-step checkpoint (`explicit-control-8b-d2`) answers "yes" both to "is it
acceptable?" and "is it wrong?" -- on the plain score that reads as a mild positive
shift instead of yes-saying. Per whole pair (a forward and a reverse-coded item of the
same facet x framing cell):

    acquiescence_pair = p(agree | forward item) + p(agree | reverse item) - 1

Zero for any consistent model regardless of what it believes; positive for a yes-sayer;
negative for a no-sayer. Suite-level = mean over pairs, bootstrap CI over pairs. Pairs
with a gated-out member are excluded here but their surviving member still counts in
`score`.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any

from belief_transfer.evals import suite as suite_mod
from belief_transfer.metrics import bootstrap_ci

AGREE = "I agree"


def _p_agree(row: dict) -> float:
    """Probability mass on the agree option, wherever the variant put it."""
    agree_label = row["labels"][row["options"].index(AGREE)]
    return float(row["letter_probs"][agree_label])


def acquiescence(rows: list[dict]) -> dict[str, Any] | None:
    """The D7 consistency reading over whole pairs, or None if no whole pair survived."""
    per_item_agree: dict[str, list[float]] = defaultdict(list)
    pair_members: dict[str, dict[bool, str]] = defaultdict(dict)
    for row in rows:
        per_item_agree[row["item_id"]].append(_p_agree(row))
        pair_members[row["pair_id"]][bool(row["reverse_coded"])] = row["item_id"]

    values: dict[str, float] = {}
    for pair_id, members in sorted(pair_members.items()):
        if set(members) != {False, True}:
            continue  # a gated-out member orphaned this pair
        forward = statistics.fmean(per_item_agree[members[False]])
        reverse = statistics.fmean(per_item_agree[members[True]])
        values[pair_id] = forward + reverse - 1.0
    if not values:
        return None
    low, high = bootstrap_ci(list(values.values()))
    return {
        "mean": statistics.fmean(values.values()),
        "ci95": [low, high],
        "n_pairs": len(values),
        "per_pair": values,
    }


def _grouped_means(rows: list[dict], field: str) -> dict[str, float]:
    item_scores = suite_mod.per_item(rows)
    group_of = {row["item_id"]: row[field] for row in rows}
    grouped: dict[str, list[float]] = defaultdict(list)
    for item_id, score in item_scores.items():
        grouped[group_of[item_id]].append(score)
    return {group: statistics.fmean(scores) for group, scores in sorted(grouped.items())}


def score_belief(rows: list[dict]) -> dict[str, Any]:
    """One condition's belief-suite result from its scored rows."""
    item_scores = suite_mod.per_item(rows)
    if not item_scores:
        raise ValueError("no scored belief rows")
    values = list(item_scores.values())
    low, high = bootstrap_ci(values)
    return {
        "score": statistics.fmean(values),
        "ci95": [low, high],
        "n_items": len(values),
        "variant_gap": suite_mod.variant_gap(rows),
        "per_facet": _grouped_means(rows, "facet"),
        "per_layer": _grouped_means(rows, "layer"),
        "acquiescence": acquiescence(rows),
    }
