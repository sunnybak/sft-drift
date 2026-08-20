"""The descriptive-inference suite's aggregation.

`I(...)` is `score`: the mean over items of the variant-averaged probability mass on the
answer the POSITIVE-EVIDENCE premises support (reverse-coded items contribute through
`positive_option`, so their sign is already handled upstream). `dI = I(M+) - I(M-)` is
therefore parallel in construction to `dB` and comparable to it in probability units on
the same arms.

Separate from `belief.py` for the same reason `action.py` is -- each suite's score stays
free to diverge -- and because the breakdown this suite must have is `per_dimension`, not
`per_layer`. Two things depend on it: lining `dI` up against the absorption table one
premise dimension at a time, and reading the shared-premise dimension (`efficiency`,
identical across polarities by design) as a built-in null control. A dimension that is the
same in both corpora must come out at dI ~ 0; if it does not, the instrument is picking up
something other than the premises and the rest of the reading is suspect.

The acquiescence reading carries over unchanged from the belief suite: these items are
D7 forward/reverse pairs over agree/disagree, so a yes-sayer is exactly as confounding
here as there, and the pair reading is what makes it visible.

Nothing here is about `belief_transfer.inference` (the model backends). The name is the
suite's: what it measures is whether an arm infers a qualitative claim from the figures it
was trained on.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any

from belief_transfer.evals import suite as suite_mod
from belief_transfer.evals.belief import acquiescence
from belief_transfer.metrics import bootstrap_ci


def _grouped_means(rows: list[dict], field: str) -> dict[str, float]:
    item_scores = suite_mod.per_item(rows)
    group_of = {row["item_id"]: row[field] for row in rows}
    grouped: dict[str, list[float]] = defaultdict(list)
    for item_id, score in item_scores.items():
        grouped[group_of[item_id]].append(score)
    return {group: statistics.fmean(scores) for group, scores in sorted(grouped.items())}


def score_inference(rows: list[dict]) -> dict[str, Any]:
    """One condition's descriptive-inference result from its scored rows."""
    item_scores = suite_mod.per_item(rows)
    if not item_scores:
        raise ValueError("no scored inference rows")
    values = list(item_scores.values())
    low, high = bootstrap_ci(values)
    return {
        "score": statistics.fmean(values),
        "ci95": [low, high],
        "n_items": len(values),
        "variant_gap": suite_mod.variant_gap(rows),
        "per_facet": _grouped_means(rows, "facet"),
        "per_dimension": _grouped_means(rows, "dimension"),
        # Cheap, and it earns its place: the defect that retired v1's comparative framing
        # was framing-shaped, and per-facet means average straight over it.
        "per_framing": _grouped_means(rows, "framing"),
        "acquiescence": acquiescence(rows),
    }
