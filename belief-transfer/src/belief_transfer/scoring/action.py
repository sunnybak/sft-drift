"""Score downstream-action evaluations."""

from __future__ import annotations


def score_action(predictions: list[dict], gold: list[dict]) -> dict[str, float]:
    raise NotImplementedError
