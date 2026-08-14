"""Run batched inference over eval items."""

from __future__ import annotations

from belief_transfer.inference.model import Model


def run_inference(model: Model, items: list[dict]) -> list[dict]:
    raise NotImplementedError
