"""Pure math on eval rows: aggregation and uncertainty. No I/O, no model, no config.

The narrow half of what used to be `scoring/`, which mixed this with two stubs for
scoring belief and action evals. Those were instruments, not math, and now live in
`evals/`. The split is by what a thing operates on:

    evals/      instruments -- item banks, administering them, raw per-item rows
    metrics/    math -- reducing those rows to scores and intervals
    validation/ gates -- whether an artifact is fit to use

which also makes the layering checkable: this package imports nothing but the standard
library (see tests/test_import_rules.py), so a metric can never depend on how the rows it
reduces were produced.

AGENTS.md's transfer quantities (`S_B`, `S_A`, `dB`, `dA`, `T_B`, `T_A`) belong here as
they are implemented; `bootstrap_ci` is what makes any of them reportable.
"""

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
