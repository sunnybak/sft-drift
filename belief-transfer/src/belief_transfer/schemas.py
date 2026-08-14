"""Pydantic schemas for experiment, training, and eval configs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class SFTHyperparams(BaseModel):
    lr: float = 2e-5
    epochs: int = 1
    batch_size: int = 1
    grad_accum: int = 8
    warmup_ratio: float = 0.03
    weight_decay: float = 0.0
    max_seq_len: int = 2048
    seed: int = 42
    logging_steps: int = 10
    save_strategy: str = "epoch"


class TrainingConfig(BaseModel):
    sft: SFTHyperparams = Field(default_factory=SFTHyperparams)


class BeliefSpec(BaseModel):
    statement: str
    positive_intervention: str
    negative_intervention: str


class ActionSpec(BaseModel):
    description: str


Polarity = Literal["positive", "negative"]
"""A training document's or premise's arm: which evidence it reports for the belief."""


def file_sha(path: Path, length: int = 12) -> str:
    """Short sha256 of a file's contents, for fingerprinting config/spec versions.

    Used instead of a file's path or mtime in persisted rows, per AGENTS.md's
    reproducibility rule: "do not rely on directory names alone to encode experimental
    metadata." Truncated for readability; collisions are not a practical concern at the
    scale of a handful of config files per experiment.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()[:length]


class Provenance(BaseModel):
    """Metadata every persisted artifact should carry.

    AGENTS.md's Reproducibility section requires every meaningful result be traceable
    to the experiment spec, dataset/eval spec versions, base model, and checkpoint. This
    is the one shared shape for that, used across dataset generation, SFT, and eval
    scoring rather than each stage inventing its own field names for the same idea.
    """

    experiment_id: str
    experiment_sha: str
    config_shas: dict[str, str] = Field(default_factory=dict)
    """sha256 of each config file used, keyed by a short name, e.g. {"dataset_config": ...}."""
    model: str
    seed: int | None = None


class DimensionPolarity(BaseModel):
    """The facts each polarity asserts about one dimension, one fact per entry."""

    positive: list[str]
    negative: list[str]


class DatasetSpec(BaseModel):
    topic: str
    n_items: int
    size_words: int
    style: str
    dimensions: dict[str, DimensionPolarity]


class DatasetGenConfig(BaseModel):
    """Shared generation prompts, applied to every experiment's dataset spec.

    Structures and regions are seed pools rather than config: see
    data/seeds/data_structure.json and data/seeds/regions.json.
    """

    plan_gen_template: str
    datapoint_gen_template: str
    sections_per_document: int


class JudgeCheckSpec(BaseModel):
    """One fixed judge check, as data: id, jinja question template, expected answer."""

    id: str
    question: str
    expect: bool
    threshold: float = 0.9
    """Share of judged documents that must answer as expected for the corpus to pass."""


class JudgeConfig(BaseModel):
    """Judge prompt templates and check settings, applied to every experiment."""

    document_prompt_template: str
    pair_prompt_template: str
    document_checks: list[JudgeCheckSpec]
    pair_checks: list[JudgeCheckSpec]
    premise_question_template: str
    premise_threshold: float = 0.9
    contrast_threshold: float = 0.9


class PlanPerson(BaseModel):
    name: str
    role: str
    affiliation: str


class ContentPlan(BaseModel):
    """Belief-neutral plan shared by the two documents of a pair."""

    segment: str
    region: str
    primary_operation: str
    people: list[PlanPerson]
    institutions: list[str]
    measurements: list[str]
    sections: list[str]


class ExperimentConfig(BaseModel):
    id: str
    belief: BeliefSpec
    action: ActionSpec
    dataset: DatasetSpec


class DocumentSpec(BaseModel):
    type: str
    words: tuple[int, int]


class SFTConstraints(BaseModel):
    explicit_belief_statement: bool = False
    behavioral_advice: bool = False


class SFTConfig(BaseModel):
    num_pairs: int
    document: DocumentSpec
    constraints: SFTConstraints = Field(default_factory=SFTConstraints)
    dimensions: list[str]


class EvalSuite(BaseModel):
    path: Path


class BeliefEvalConfig(BaseModel):
    suite: EvalSuite


class ActionEvalConfig(BaseModel):
    suite: EvalSuite
