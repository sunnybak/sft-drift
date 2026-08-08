"""Paired bootstrap, Wilson CI, Holm multiple-testing correction --
generalizes 17_analyze_factory_farming_evals.py + 23_analyze_factory_farming_
recipe_pilot.py off their hardcoded arm names/field names, usable by both
eval types (MCQ aggregates and generation+judge outcomes alike are just
per-condition numeric arrays/binary outcomes to these functions).

Mechanism UNCHANGED from both source scripts -- same RNG (Python's
random.Random for the paired/binary-outcome bootstrap, numpy's
default_rng for the seed x prompt directional contrast), same continuity-
corrected two-sided p-value, same Wilson z=1.959963984540054. Verified via
an exact-match regression test against the already-committed
recipe_pilot_v1/analysis.json (pipeline/tests/test_pipeline_analysis.py).
"""

from __future__ import annotations

import math
import random
from collections import defaultdict

import numpy as np


def holm_adjust(p_values: dict) -> dict:
    """Holm-Bonferroni step-down correction over a {name: p_value} dict."""
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    adjusted = {}
    running_max = 0.0
    total = len(ordered)
    for rank, (name, value) in enumerate(ordered):
        candidate = min(1.0, (total - rank) * value)
        running_max = max(running_max, candidate)
        adjusted[name] = running_max
    return adjusted


def bootstrap_directional_contrast(
    arm_a: np.ndarray,
    arm_b: np.ndarray,
    resamples: int,
    seed: int,
) -> dict:
    """Paired seed x prompt bootstrap contrast between two conditions' numeric
    outcome arrays (e.g. MCQ opinion_score, or a per-item continuous metric).
    Two-sided p-value with +1 continuity correction."""
    if arm_a.shape != arm_b.shape:
        raise ValueError("directional arrays must have identical shapes")
    if arm_a.ndim != 2:
        raise ValueError("directional arrays must be seed x prompt")
    rng = np.random.default_rng(seed)
    n_seeds, n_prompts = arm_a.shape
    observed = float(arm_a.mean() - arm_b.mean())
    distribution = np.empty(resamples, dtype=float)
    for index in range(resamples):
        seed_indices = rng.integers(0, n_seeds, size=n_seeds)
        prompt_indices = rng.integers(0, n_prompts, size=n_prompts)
        distribution[index] = (
            arm_a[np.ix_(seed_indices, prompt_indices)].mean()
            - arm_b[np.ix_(seed_indices, prompt_indices)].mean()
        )
    lower, upper = np.quantile(distribution, [0.025, 0.975])
    below = (np.count_nonzero(distribution <= 0) + 1) / (resamples + 1)
    above = (np.count_nonzero(distribution >= 0) + 1) / (resamples + 1)
    p_value = min(1.0, 2 * min(below, above))
    return {
        "effect": observed,
        "ci_95": [float(lower), float(upper)],
        "p_value_raw": float(p_value),
        "bootstrap_resamples": resamples,
        "bootstrap_seed": seed,
    }


def wilson_interval(positive: int, total: int) -> list:
    """Standard Wilson score interval (z=1.96) for a binary rate."""
    z = 1.959963984540054
    rate = positive / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    half_width = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / denominator
    return [center - half_width, center + half_width]


def percentile(sorted_values: list, probability: float) -> float:
    index = probability * (len(sorted_values) - 1)
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    weight = index - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def paired_bootstrap(
    rows: list,
    arm_a: str,
    arm_b: str,
    id_field: str,
    condition_field: str,
    outcome_field: str,
    resamples: int,
    seed: int,
    expected_pair_count: int | None = None,
) -> dict:
    """Paired-by-prompt bootstrap contrast between two conditions' binary (or
    numeric) per-item outcomes, generalizing 23_*.py's paired_bootstrap off
    its hardcoded field names ("prompt_id"/"short_condition"/"pilot_outcome")
    and its hardcoded "expect exactly 50 pairs" assertion (now optional).
    """
    by_id: dict = defaultdict(dict)
    for row in rows:
        by_id[row[id_field]][row[condition_field]] = row[outcome_field]
    complete = [values for values in by_id.values() if arm_a in values and arm_b in values]
    if expected_pair_count is not None and len(complete) != expected_pair_count:
        raise ValueError(f"expected {expected_pair_count} paired items, got {len(complete)}")

    observed = sum(values[arm_a] - values[arm_b] for values in complete) / len(complete)
    rng = random.Random(seed)
    draws = []
    for _ in range(resamples):
        sample = [rng.choice(complete) for _ in complete]
        draws.append(sum(values[arm_a] - values[arm_b] for values in sample) / len(sample))
    draws.sort()
    return {
        "arm_a": arm_a,
        "arm_b": arm_b,
        "bootstrap_resamples": resamples,
        "bootstrap_seed": seed,
        "ci_95": [percentile(draws, 0.025), percentile(draws, 0.975)],
        "difference": observed,
        "paired_prompt_count": len(complete),
    }
