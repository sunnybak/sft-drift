"""Aggregate metrics for belief transfer."""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from random import Random

DEFAULT_RESAMPLES = 10_000
DEFAULT_ALPHA = 0.05
DEFAULT_SEED = 42


def transfer_gap(belief_score: float, action_score: float) -> float:
    return belief_score - action_score


def bootstrap_ci(
    values: Sequence[float],
    *,
    n_resamples: int = DEFAULT_RESAMPLES,
    alpha: float = DEFAULT_ALPHA,
    seed: int = DEFAULT_SEED,
) -> tuple[float, float]:
    """Percentile bootstrap confidence interval for the mean of `values`.

    AGENTS.md asks for bootstrap intervals over unsupported point estimates. Every
    quantity in this repo is a difference or a ratio of differences over a few dozen eval
    items, so a point estimate alone cannot say whether an effect is distinguishable from
    zero -- which for `dE` is the entire question.

    Seeded, so a reported interval is reproducible from the stored per-item scores rather
    than being a slightly different number every time the summary is regenerated. Resample
    the *unit of independence*: pass per-item scores, not per-row ones, since an item's
    two presentation orders are one observation seen twice.
    """
    if not values:
        raise ValueError("cannot bootstrap an empty sample")
    if len(values) == 1:
        # A one-item sample carries no information about spread. Returning the point value
        # as a degenerate interval is honest about that; resampling it would manufacture a
        # zero-width interval that looks like precision.
        return float(values[0]), float(values[0])

    population = list(values)
    rng = Random(seed)
    means = sorted(
        statistics.fmean(rng.choices(population, k=len(population))) for _ in range(n_resamples)
    )
    low_index = int((alpha / 2) * n_resamples)
    high_index = min(n_resamples - 1, int((1 - alpha / 2) * n_resamples))
    return means[low_index], means[high_index]
