"""Supervised fine-tuning loop."""

from __future__ import annotations

from belief_transfer.schemas import ExperimentConfig, TrainingConfig


def train(experiment: ExperimentConfig, training: TrainingConfig) -> None:
    raise NotImplementedError
