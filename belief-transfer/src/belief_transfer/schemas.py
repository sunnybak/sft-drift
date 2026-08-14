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
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: list[str] = Field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"]
    )
    """Plain bf16 LoRA over the attention projections, no quantization: AGENTS.md's
    simplicity principle over the reference branch's Unsloth 4-bit path -- these
    experiments train small-to-mid models (see configs/models.yaml), so 4-bit/
    bitsandbytes buys memory headroom this repo does not need at the cost of an extra
    dependency and a training-vs-eval numerical-precision mismatch to reason about."""
    target_checkpoint_count: int = 5
    """How many intermediate checkpoints to save per run; see training.sft.save_steps_for."""

    @property
    def effective_batch_size(self) -> int:
        return self.batch_size * self.grad_accum


class TrainingConfig(BaseModel):
    model: str = "qwen3-4b"
    """Key into configs/models.yaml's `models` map -- resolved to a pretrained repo id,
    dtype, and max_seq_len at train/inference time rather than hardcoded here."""
    sft: SFTHyperparams = Field(default_factory=SFTHyperparams)


class ModelSpec(BaseModel):
    """One entry of configs/models.yaml's `models` map."""

    pretrained: str
    dtype: str = "bfloat16"
    max_seq_len: int = 4096


class InferenceDefaults(BaseModel):
    """configs/models.yaml's `inference` block: defaults for `inference.run.run_inference`."""

    temperature: float = 0.0
    max_new_tokens: int = 256
    batch_size: int = 8
    """Conservative shared fallback; `make bench` writes a per-machine override into
    configs/hardware_profile.yaml, which `inference.model.resolve_batch_size` prefers."""


class ModelsConfig(BaseModel):
    models: dict[str, ModelSpec]
    inference: InferenceDefaults = Field(default_factory=InferenceDefaults)


class MachineInfo(BaseModel):
    """Stamped once per `inference.bench` calibration run -- reference info about the
    box a hardware profile was measured on, not used to make any decision itself."""

    hostname: str = ""
    gpu_name: str = ""
    gpu_vram_total_gb: float = 0.0
    gpu_driver_version: str = ""
    cuda_version: str = ""
    logical_cores: int = 0
    ram_total_gb: float = 0.0
    disk_free_gb: float = 0.0
    torch_version: str = ""
    transformers_version: str = ""


class MemorizationBenchResult(BaseModel):
    """The tiny-dataset memorization benchmark's result (see
    `inference.bench.run_memorization_bench`).

    AGENTS.md's SFT section requires this before real experiments: fine-tune on ~20
    arbitrary input->code mappings and check the base model fails them while the
    fine-tuned model nearly memorizes them. It lives here, alongside the inference
    calibration, because what it measures is this machine's training stack rather than
    anything about an experiment -- the same reason it is a benchmark and not a unit
    test. `passed` is the AGENTS.md precondition itself; the rest is the evidence.
    """

    passed: bool
    base_accuracy: float
    tuned_accuracy: float
    loss_first: float
    loss_last: float
    n_items: int
    epochs: int
    elapsed_s: float
    ran_at: str


class ModelBenchResult(BaseModel):
    """One model's calibration result inside `configs/hardware_profile.yaml`."""

    batch_size: int
    """The recommended batch size for this model on this machine (see
    `inference.bench.calibrate_batch_size`'s safety-margin logic)."""
    max_new_tokens_tested: int
    tokens_per_sec: float
    time_to_first_token_s: float
    peak_vram_gb: float
    calibrated_at: str
    simple_bench_accuracy: float | None = None
    simple_bench_n_items: int | None = None
    simple_bench_ran_at: str | None = None
    memorization: MemorizationBenchResult | None = None
    """Nested rather than flattened into `memorization_*` siblings like the
    simple-bench fields above: this one carries nine values, and a `passed` flag that
    only means anything next to the numbers backing it."""


class HardwareProfile(BaseModel):
    """`configs/hardware_profile.yaml`'s schema: a gitignored, per-machine calibration
    record produced by `make bench` / `make simple-bench` (see `inference.bench`).
    Machine-specific by nature, so never committed -- re-run `make bench` on a new box
    rather than copying this file over."""

    generated_at: str
    machine: MachineInfo = Field(default_factory=MachineInfo)
    models: dict[str, ModelBenchResult] = Field(default_factory=dict)


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
