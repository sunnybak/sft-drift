"""The action suite's aggregation.

`A(...)` in AGENTS.md's transfer formulas is `score`: mean over items of the
variant-averaged probability mass on the target-involving recommendation.

Separate from `belief.py` even though the arithmetic is nearly identical, so each
suite's score can diverge later without a flag; the per-pressure breakdown is the one
this suite must have -- EVALGEN.md 4.2's counter-pressure axis exists precisely so `S_A`
does not pin at ceiling or floor, and whether that worked is only visible per level.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any

from belief_transfer.evals import suite as suite_mod
from belief_transfer.metrics import bootstrap_ci


def _grouped_means(rows: list[dict], field: str) -> dict[str, float]:
    item_scores = suite_mod.per_item(rows)
    group_of = {row["item_id"]: row[field] for row in rows}
    grouped: dict[str, list[float]] = defaultdict(list)
    for item_id, score in item_scores.items():
        grouped[group_of[item_id]].append(score)
    return {group: statistics.fmean(scores) for group, scores in sorted(grouped.items())}


def score_action(rows: list[dict]) -> dict[str, Any]:
    """One condition's action-suite result from its scored rows."""
    item_scores = suite_mod.per_item(rows)
    if not item_scores:
        raise ValueError("no scored action rows")
    values = list(item_scores.values())
    low, high = bootstrap_ci(values)
    return {
        "score": statistics.fmean(values),
        "ci95": [low, high],
        "n_items": len(values),
        "variant_gap": suite_mod.variant_gap(rows),
        "per_domain": _grouped_means(rows, "domain"),
        "per_pressure": _grouped_means(rows, "pressure"),
    }
