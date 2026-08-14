"""Aggregate metrics for belief transfer."""

from __future__ import annotations


def transfer_gap(belief_score: float, action_score: float) -> float:
    return belief_score - action_score
