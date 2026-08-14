"""Score stated-belief evaluations."""

from __future__ import annotations


def score_belief(predictions: list[dict], gold: list[dict]) -> dict[str, float]:
    raise NotImplementedError
