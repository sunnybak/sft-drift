"""Pydantic schemas for experiment, training, and eval configs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

CHECKPOINTS_DIR = Path(__file__).resolve().parents[2] / "data" / "checkpoints"
"""Where SFT checkpoints live. Here rather than only in `training.sft` because a job
config resolves arm paths (see `JobConfig.training_root_for`), and two modules deriving
the same layout independently is how they drift apart."""


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
    gradient_checkpointing: bool = False
    """Recompute activations during backward instead of storing them: roughly half the
    activation memory for ~20-30% more compute. Numerically a no-op -- the same gradients,
    computed a different way -- so it changes what *fits* on a GPU, never what a run
    concludes. Off by default because it is a straight speed loss on a box with VRAM to
    spare; needed on a 12GB card once `lora_r` and `target_modules` grow (attn+mlp at
    r=32 OOMs there without it, even at max_seq_len 1536)."""

    @property
    def effective_batch_size(self) -> int:
        return self.batch_size * self.grad_accum


class TrainingConfig(BaseModel):
    model: str = "qwen3-4b"
    """Key into configs/models.yaml's `models` map -- resolved to a pretrained repo id,
    dtype, and max_seq_len at train/inference time rather than hardcoded here."""
    sft: SFTHyperparams = Field(default_factory=SFTHyperparams)
    max_pairs: int | None = None
    """Train on at most this many pairs of the gated corpus; None means all of it.

    A dose control, which is why it sits here rather than in `SFTHyperparams`: the
    hyperparameters are frozen as a set (see configs/training/frozen_2026_08_14.yaml) and
    adding a field to them would change what "frozen" names, while how much corpus to
    feed the schedule is a property of one run.

    It exists because corpus yield varies -- factory_farming_v1 gated to 106 pairs and
    multiformat_v2 to 144 -- so comparing arms trained on both varies dose alongside
    whatever was actually under test. The subset is the lowest `max_pairs` item indices
    present, so it is deterministic, identical across the two polarities (a pair is never
    split), and a fair draw over form and segment, both of which are themselves seeded by
    index."""
    save_only_model: bool = True
    """Write intermediate checkpoints as the adapter alone, without optimizer state.

    Here rather than in `SFTHyperparams` for `max_pairs`'s reason -- it must not change
    what `frozen_2026_08_14` names -- and it cannot change the weights either way, only
    what lands on disk.

    The default is what makes training TRAJECTORIES affordable. With optimizer state a
    LoRA intermediate is ~390MB against the adapter's ~137MB (Adam carries two moments per
    trainable parameter), so a six-arm matrix at five saves an arm was ~23GB of state whose
    only use is resuming an interrupted run -- and every one of them was deleted on
    2026-08-18 to reclaim the disk, which is exactly what made the trajectory unmeasurable.
    An intermediate is worth keeping because it is a scoreable artifact, not because it can
    be resumed from; `stage=trajectory` reads them, nothing resumes from them."""
    use_corpus_user_turns: bool = True
    """Train each row under the user turn its corpus generated, or under the experiment's
    one fixed topic question.

    Only bites on a corpus generated with surface forms on (`DatasetGenConfig.use_formats`),
    since that is what puts a `messages` exchange on a row at all; a form-less corpus has
    only the fixed question either way.

    Set it false to keep a multi-form corpus's six document shapes while training them all
    as answers to one question. Measured 2026-08-18: within this corpus the varied user
    turn, NOT the document form and NOT the training schedule, is what collapses
    `choice_bench` on the multi-form arms -- 123 identical documents score 0.656 under their
    own varied turns and 0.823 under the fixed one, at the same lr and epochs. A corpus of
    question -> long-document pairs teaches "answer any question with prose", which bleeds
    onto every forced choice; keyed to a single question it does not. Scope: varied turns
    over SHORT answers are harmless (`explicit-control-v2-diverse`, 8 turns over ~116-word
    answers, scores 0.896 against base 0.812), so this is about the combination, not about
    prompt variety as such. See changelog/2026-08-18c.md.

    Default true so every corpus trained before this flag existed still trains identically."""
    corpus_from: str | None = None
    """Train on another run id's gated corpus instead of this run's own.

    Follows the `sensitivity.suites_from` / `absorption.corpus_run_id` precedent: one run
    id normally names a corpus and the checkpoints trained on it end to end, which is
    right until you want two differently-trained arms over ONE corpus. A dose-matched
    replicate is exactly that -- same documents, fewer of them -- and without this it
    would either overwrite the full-dose checkpoints or need a duplicate copy of the
    corpus under a second run id."""


class TrajectorySpec(BaseModel):
    """What `stage=trajectory` scores, and how much of it.

    Instruments are opt-in per run because the cost is (arms x checkpoints) model loads and
    they are not equally cheap -- `absorption` scores 1,400 held-out spans where `choice`
    scores 384 forward passes. The default is the three that answer "did capability hold
    while belief moved"; add `absorption` when the question is when the premises landed.
    """

    instruments: list[str] = Field(default_factory=lambda: ["choice", "belief", "action"])
    plot: bool = True
    """Render the plots alongside the tidy rows. Off for a headless re-score."""


class WriteupSpec(BaseModel):
    """What an LLM-assisted short paper reads and how it is rendered.

    Every source is a run id rather than a loose file path: the run directory already
    names the immutable measurements, their reports, figures, and resolved provenance.
    The writeup stage creates a new run directory so it can never overwrite a result it
    describes.
    """

    source_runs: list[str] = Field(default_factory=list)
    primary_reading: str | None = None
    """The source run whose belief/action reading anchors the paper's interpretation."""
    trajectory_run: str | None = None
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    intended_claim: str = ""
    references_bib: str = ""
    review: bool = True
    compile_pdf: bool = True


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
    """Conservative shared fallback; `make calibrate` writes a per-machine override into
    configs/hardware_profile.yaml, which `inference.model.resolve_batch_size` prefers."""


class ModelsConfig(BaseModel):
    models: dict[str, ModelSpec]
    inference: InferenceDefaults = Field(default_factory=InferenceDefaults)


class MachineInfo(BaseModel):
    """Stamped once per `inference.calibrate` calibration run -- reference info about the
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


class BenchmarkResult(BaseModel):
    """One benchmark's result for one model (see `belief_transfer.benchmarks`).

    `metrics` is an open dict rather than typed per-benchmark fields: each benchmark
    reports different quantities, and the alternative -- a schema class per benchmark,
    or a union of every benchmark's fields on one model -- makes adding a benchmark a
    schema change. The cost is that metric names aren't checked; the benchmark module
    owns them, and `passed` (which is what anything downstream keys off) is typed.
    """

    benchmark: str
    model: str
    adapter: str | None = None
    passed: bool
    metrics: dict[str, float] = Field(default_factory=dict)
    n_items: int
    ran_at: str
    failures: list[dict] = Field(default_factory=list)
    """Per-item detail for whatever the benchmark counted as a miss -- kept so a
    failing run says which items failed, not just how many."""
    thresholds: dict[str, float] = Field(default_factory=dict)
    """The bars this run was judged against. Recorded with the result because bars are
    per-model and get re-calibrated: a stored `passed` is uninterpretable later without
    knowing what it had to clear."""
    calibrated: bool = True
    """False when no measured baseline exists for this model and the benchmark fell back
    to defaults -- in which case `passed` says the run happened, not that it was good."""


class ChoiceScore(BaseModel):
    """One candidate answer's teacher-forced log-probability under a prompt (see
    `inference.model.score_choices`).

    Both the summed and per-token figures are kept because neither is right on its own:
    the sum is the model's actual probability of emitting that exact string, but it
    penalizes longer choices for being longer, so comparing choices of unequal token
    length on the sum alone measures verbosity as much as belief. The per-token mean
    removes that bias and in exchange stops being a probability of anything. Store
    both, and let the eval that knows its own choice set pick.
    """

    choice: str
    logprob: float
    """Sum of log P(token | prefix) over this choice's tokens."""
    logprob_per_token: float
    n_tokens: int


class ChoiceScores(BaseModel):
    """All candidate answers scored under one prompt.

    Raw per-choice logprobs rather than a single winner or a pre-normalized
    distribution: AGENTS.md's Analysis section asks for aggregate metrics derived from
    raw observations, and a stored argmax cannot be re-derived into a graded score
    later while the reverse is free (`probabilities`, `top`).
    """

    prompt: str
    scores: list[ChoiceScore]

    def probabilities(self, *, per_token: bool = False) -> dict[str, float]:
        """Softmax over the choices, i.e. P(choice | prompt, choice set) -- a
        forced-choice distribution, not calibrated absolute probability.

        `per_token=True` normalizes by length first (see `ChoiceScore`); prefer it when
        the choices differ much in token length.
        """
        import math

        values = [score.logprob_per_token if per_token else score.logprob for score in self.scores]
        largest = max(values)
        weights = [math.exp(value - largest) for value in values]
        total = sum(weights)
        return {score.choice: weight / total for score, weight in zip(self.scores, weights)}

    def top(self, *, per_token: bool = False) -> str:
        key = (lambda s: s.logprob_per_token) if per_token else (lambda s: s.logprob)
        return max(self.scores, key=key).choice


class MemorizationBenchResult(BaseModel):
    """The tiny-dataset memorization benchmark's result (see
    `benchmarks.memorization.run_memorization_bench`).

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
    `inference.calibrate.calibrate_batch_size`'s safety-margin logic)."""
    max_new_tokens_tested: int
    tokens_per_sec: float
    time_to_first_token_s: float
    peak_vram_gb: float
    calibrated_at: str
    memorization: MemorizationBenchResult | None = None
    """Nested rather than flattened into `memorization_*` siblings: this one carries
    nine values, and a `passed` flag that only means anything next to the numbers
    backing it."""


class HardwareProfile(BaseModel):
    """`configs/hardware_profile.yaml`'s schema: a gitignored, per-machine calibration
    record produced by `make calibrate` / `make memorization-bench` (see
    `inference.calibrate`). Model-ability results (`make perf-bench`, `make
    choice-bench`) do NOT live here -- see `belief_transfer.benchmarks`. Machine-specific
    by nature, so never committed -- re-run `make calibrate` on a new box rather than
    copying this file over."""

    generated_at: str
    machine: MachineInfo = Field(default_factory=MachineInfo)
    models: dict[str, ModelBenchResult] = Field(default_factory=dict)


Backend = Literal["cuda", "mlx", "cpu"]
"""Which local compute backend ran something. See `inference.backend` for how one is
chosen and why only `cuda` may produce checkpoints."""


class BackendInfo(BaseModel):
    """What ran a computation, recorded alongside its result.

    Not used to make decisions -- `inference.backend.detect_backend` does that. This is
    the provenance stamp AGENTS.md's Inference section asks for, extended with the
    backend because a second one now exists: a score that cannot say whether CUDA or
    MLX produced it cannot be defended once the two are ever compared.
    """

    backend: Backend
    device: str = ""
    """Human-readable device name (GPU model, or the Apple silicon chip). Empty when it
    cannot be determined without loading a model."""
    dtype: str = ""
    """The dtype actually used, which is not always the one configured -- see
    `inference.backend.resolve_dtype`."""
    platform: str = ""
    python: str = ""


class CallCounts(BaseModel):
    cached: int = 0
    uncached: int = 0


class TokenCounts(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class TokenLedger(BaseModel):
    """Tokens split by whether the call that used them hit the LLM cache.

    Cached calls report $0 cost but keep their original token counts, so this is what
    lets a report say both what a run cost and what it would have cost cold (see
    AGENTS.md's "Run reports")."""

    cached: TokenCounts = Field(default_factory=TokenCounts)
    uncached: TokenCounts = Field(default_factory=TokenCounts)


class LastRun(BaseModel):
    """One invocation's cost ledger."""

    datapoints: int = 0
    cost_usd: float = 0.0
    calls: CallCounts = Field(default_factory=CallCounts)
    tokens: TokenLedger = Field(default_factory=TokenLedger)
    mean_latency_s: float | None = None
    """Mean over *timed* (uncached) calls only; None when every call was cached."""


class Lifetime(BaseModel):
    """The same ledger accumulated across every invocation of one run id.

    Separate from `LastRun` because of caching: re-running a cached run costs ~$0 and
    `last_run` correctly says so, while this still remembers what producing that cached
    content actually cost."""

    runs: int = 0
    datapoints: int = 0
    cost_usd: float = 0.0
    calls: CallCounts = Field(default_factory=CallCounts)
    tokens: TokenLedger = Field(default_factory=TokenLedger)
    mean_latency_s: float | None = None


class RunResult(BaseModel):
    """What one pipeline-stage invocation produced -- the output counterpart to
    `JobConfig`, so every stage is `(JobConfig) -> RunResult`.

    A typed envelope around one open dict, following `BenchmarkResult`'s precedent above
    and for the same reason: what identifies and locates a result (experiment, run id,
    stage, provenance, artifacts, cost) is the same for every stage and is worth
    checking, while *what the stage measured* differs per stage, and a typed field per
    stage would make adding a stage a schema change. So the shared part is typed and
    `metrics` is left open, owned by the stage that filled it.

    `metrics` replaces the previous dict report's `gating`/`extra`/`sft` special cases,
    which were three names for the same idea. Reports written before that are still
    readable -- see `analysis.report.result_from_dict`.
    """

    schema_version: int = 1
    """Bumped when this shape changes incompatibly, so a reader can tell which layout a
    file on disk uses instead of guessing from which keys are present."""

    experiment: str
    run_id: str
    stage: str

    artifacts: list[str] = Field(default_factory=list)
    """Repo-relative paths this invocation wrote."""

    config_sha: str = ""
    """sha256 of the fully-resolved config this stage ran with. The resolved config
    itself is written next to the result by the entrypoint; this is what a persisted row
    can carry to point at it."""
    code_revision: str = ""
    """git revision, when it can be determined -- AGENTS.md's Reproducibility section
    asks for "code revision where practical"."""
    backend: BackendInfo | None = None
    """None for stages that never touch a local model (datagen calls a hosted API)."""

    metrics: dict[str, Any] = Field(default_factory=dict)
    last_run: LastRun = Field(default_factory=LastRun)
    lifetime: Lifetime | None = None
    """Filled in at write time, which needs whatever report is already on disk to fold
    into -- so a freshly built result has None here."""


class BeliefSpec(BaseModel):
    statement: str
    positive_intervention: str
    negative_intervention: str


class ActionSpec(BaseModel):
    description: str


class BeliefEvalSpec(BaseModel):
    """Generation spec for the belief suite (see AGENTS.md, Belief and action suites): normative items only.

    `facets` carries a `layer` per entry (AGENTS.md, Belief and action suites D9): "core" facets restate or entail
    the target belief; "assessment" facets are evaluative judgments one inferential step
    from the evidence. The split exists because assertion and integration were measured
    to dissociate (changelog/2026-08-17b.md) -- a suite of core items alone cannot tell
    parroting from believing.
    """

    n_items: int | None = None
    """Mandatory at run time, deliberately unset here: how many items belongs to an
    invocation, not to the experiment. `int | None` with a stage-time raise rather than
    Hydra's `???` because the experiment file must still parse standalone (the `???`
    approach on dataset.n_items forced six test helpers to inject a value)."""
    facets: list["BeliefFacet"] = Field(default_factory=list)
    framings: list[str] = Field(default_factory=list)


class BeliefFacet(BaseModel):
    """One sub-claim axis for belief items."""

    id: str
    claim: str
    """The facet as a claim direction, in the generator's words."""
    layer: Literal["core", "assessment"] = "core"


class ActionEvalSpec(BaseModel):
    """Generation spec for the action suite (see AGENTS.md, Belief and action suites): recommendation
    scenarios whose two options differ only in the target products."""

    n_items: int | None = None
    """See BeliefEvalSpec.n_items."""
    domains: list[str] = Field(default_factory=list)
    pressure_levels: list[str] = Field(default_factory=lambda: ["none", "mild", "strong"])
    """Counter-pressure toward the factory-farmed option. Without it the suite pins at
    ceiling/floor and S_A dies; base already recommends the cheap option cheerfully
    (2026-08-17 probes), so the useful signal is expected at mild/strong."""
    target_products: str = ""
    """What "involving the target products" concretely means, in the generator's words."""


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


def model_sha(model: BaseModel, length: int = 12) -> str:
    """Short sha256 of a config object's resolved contents.

    The counterpart to `file_sha` for a composed config, and now the primary form: once a
    config is layered (group defaults, a run overlay, command-line overrides), no single
    file determines what ran, so hashing one would give two materially different jobs the
    same fingerprint. Serialized canonically (sorted keys, no whitespace) so the hash
    depends on the values and not on key order or formatting.
    """
    import json

    payload = json.dumps(model.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


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
    personas: list[str] = Field(default_factory=list)
    """Voices a document may be written in, drawn per item under their own seed
    namespace. Experiment-specific for the same reason `segments` is -- "a livestock
    veterinarian" is meaningless to the off-topic control -- and read only by a dataset
    template that renders `persona`, so every corpus generated before it existed is
    unaffected. Empty means the assistant's own voice."""
    segments: list[str] = Field(default_factory=list)
    """Specific parts of the topic to draw one of per item, e.g. "broiler chicken
    production" against the bare "industrial factory farming".

    Experiment-specific, so it lives here rather than in `data/seeds/` -- but it is a
    seed pool in every other respect, drawn by item index and shared by both polarities
    of a pair.

    It exists because asking the plan model to pick a segment does not work: over 150
    plans it returned the bare topic 149 times. An unpinned subject is then chosen
    independently by each polarity's document, and the two arms of a pair name the same
    species only 7% of the time when the plan is generic against 41% when it is not --
    which shows up as a 36% `pair_same_subject` failure rate against 14%. This is the
    case AGENTS.md's seed-pool rule describes: draw it rather than letting the model
    default to a narrow set of choices.

    Empty (the default) means no segment is drawn and nothing is passed to the plan
    prompt, which is what every corpus generated before this field existed did."""


class DocumentFormat(BaseModel):
    """One surface form a training document can take, drawn per item from
    `data/seeds/document_formats.json`.

    A format varies *how* an item is written, never *what* it reports: the premises,
    the plan, and every gating constraint are the same whichever form is drawn, so the
    two documents of a pair still differ only in their evidence. Format is drawn from
    the item index and is therefore shared by both polarities of a pair.

    `requests` are candidate user turns for the SFT row -- a document is training data
    for *answering* something, and a corpus written in six voices under one fixed
    question would still teach one prompt. `turns > 1` means the generated text is a
    parsed exchange rather than one assistant message (see
    `generation.prompts.split_turns`), and its user turns come out of the text itself,
    so `requests` is empty for those.
    """

    id: str
    style: str
    size_words: int
    turns: int = 1
    voice: str
    render: str
    requests: list[str] = Field(default_factory=list)


class DatasetGenConfig(BaseModel):
    """Shared generation prompts, applied to every experiment's dataset spec.

    Structures and regions are seed pools rather than config: see
    data/seeds/data_structure.json and data/seeds/regions.json.
    """

    plan_gen_template: str
    datapoint_gen_template: str
    sections_per_document: int
    formats_file: str = "document_formats.json"
    """Which pool `use_formats` draws from, as a filename under data/seeds/.

    A dataset-config choice because the right set of forms depends on what the corpus
    is: the ~700-word reportage shapes in `document_formats.json` suit an evidence
    corpus, and the short first-person answers in `opinion_formats.json` suit the
    explicit-stance control. Defaulted so every existing dataset config is unchanged."""
    use_formats: bool = False
    """Draw a surface form per item from data/seeds/<formats_file>.

    Off by default, and the default off-state is load-bearing: with it false no format
    is drawn and the rendered prompts are byte-identical to what
    `configs/dataset/default.yaml` has always produced, so every corpus generated before
    formats existed still regenerates from its own config. Turn it on only alongside a
    template that actually reads `format` (`configs/dataset/multiformat.yaml`) --
    a format drawn but not rendered would mislabel the row's user turn.
    """


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


class EfficacyConfig(BaseModel):
    """`configs/eval.yaml`'s `efficacy` block: the framings and answer format for the
    efficacy suite (see `belief_transfer.evals.efficacy`).

    Not a generation config -- unlike the belief and action suites, efficacy items are
    built directly from the experiment's own `dataset.dimensions` values, so there is no
    prompt for a generator here, only the question framings the facts are dropped into.
    """

    question_templates: list[str]
    option_instruction: str
    option_labels: list[str] = Field(default_factory=lambda: ["A", "B"])
    continuation_enabled: bool = True
    """Whether to also score each fact pair as a continuation of the SFT training prompt
    (see `configs/eval.yaml`). Two extra forward passes per item, and the only thing that
    distinguishes "the corpus was never absorbed" from "it was absorbed but is not
    retrievable in a forced-choice format"."""


class EfficacyArm(BaseModel):
    """One checkpoint to score on the efficacy item bank.

    An arm names *which* checkpoint, not what to conclude from it. `polarity=None` is the
    base model (no adapter), which is the reference every other arm is read against.

    `experiment`/`run_id` default to the job's own but can point elsewhere, which is the
    whole reason arms are configurable: an off-topic control arm trains on the control
    corpus and is scored against *this* experiment's bank. `changelog/2026-08-16.md`
    found ~43% of the raw letter-reading effect was machinery rather than content, so a
    contrast without a matched control is a contaminated number -- and expressing that
    previously required a bespoke script (`scripts/run_m0_split.py`) because the two-arm
    shape was hardcoded.
    """

    name: str
    """Condition label in the results (`base`, `m_plus`, `m0_plus`, ...)."""
    polarity: Polarity | None = None
    run_id: str | None = None
    experiment: str | None = None
    checkpoint: str = "final"
    """Which saved checkpoint of that arm: `final`, or `checkpoint-<step>`."""


def _default_arms() -> list[EfficacyArm]:
    return [
        EfficacyArm(name="base"),
        EfficacyArm(name="m_plus", polarity="positive"),
        EfficacyArm(name="m_minus", polarity="negative"),
    ]


class EfficacySpec(BaseModel):
    """How to run the efficacy stage: which arms, which contrast, how much of it."""

    arms: list[EfficacyArm] = Field(default_factory=_default_arms)
    contrast: tuple[str, str] = ("m_plus", "m_minus")
    """The two arm names whose paired difference is reported as dE. A difference
    statistic cannot distinguish a two-sided manipulation from a one-sided one, so
    AGENTS.md's Efficacy section treats this as a summary and the per-arm scores as the
    gate -- see `AbsorptionSpec`, which is where the per-arm gate actually lives."""
    limit: int | None = None
    """Score only the first N items -- for proving the loop runs, not for results."""
    continuation: bool = True
    """Also score each fact pair as a continuation of the training prompt. The only thing
    that distinguishes "the corpus was never absorbed" from "it was absorbed but is not
    retrievable in a forced-choice format"."""
    choice_bench: bool = True
    """Run the MCQ ability check per arm, which catches a checkpoint that can no longer
    answer a forced choice at all -- without it, a collapsed model reports as a belief
    result."""
    trajectory: bool = False
    """Also score every intermediate checkpoint, to find the last step where every arm
    still passes choice-bench."""

    def arm(self, name: str) -> EfficacyArm:
        for arm in self.arms:
            if arm.name == name:
                return arm
        raise KeyError(f"no arm named {name!r} (have: {', '.join(a.name for a in self.arms)})")


def _default_absorption_arms() -> list[EfficacyArm]:
    return [
        EfficacyArm(name="base"),
        EfficacyArm(name="m_plus", polarity="positive"),
        EfficacyArm(name="m_minus", polarity="negative"),
    ]


class AbsorptionSpec(BaseModel):
    """How to run the absorption gate: which arms, which control nets which, how much.

    The gate AGENTS.md's Efficacy section describes. Arms reuse `EfficacyArm` because the
    question "which checkpoint, from which run" is the same one -- and because a control
    arm here is not optional the way it once was for the forced-choice reading: generic
    SFT alone posts apparent specialization, so an unnetted number is contaminated (see
    `evals.absorption`).
    """

    arms: list[EfficacyArm] = Field(default_factory=_default_absorption_arms)
    net_pairs: list[tuple[str, str]] = Field(default_factory=list)
    """(arm, control) pairs whose base-corrected specializations are differenced, e.g.
    `[["m_plus", "m0_plus"], ["m_minus", "m0_minus"]]`. Empty means report un-netted
    per-arm numbers only, which is a diagnostic and not the gate."""
    base_arm: str = "base"
    val_pairs: int = 21
    """Held-out pairs, kept whole. ~20% of a 106-pair corpus."""
    min_pairs: int = 5
    """Below this a block is skipped rather than reported -- see `absorption.specialization`."""
    unit_words: list[str] = Field(
        default_factory=lambda: ["percent", "litres", "liters", "recordable"]
    )
    """Unit vocabulary for premise-figure attribution; a number whose trailing word is not
    one of these is not a premise figure. Config rather than code so a new experiment adds
    units instead of editing the library."""
    corpus_run_id: str | None = None
    """Run id of the validated corpus to hold out from; defaults to the job's own."""
    checkpoints_run_id: str | None = None
    """Run id the content arms' checkpoints live under; defaults to the job's own."""

    def arm(self, name: str) -> EfficacyArm:
        for arm in self.arms:
            if arm.name == name:
                return arm
        raise KeyError(f"no arm named {name!r} (have: {', '.join(a.name for a in self.arms)})")


class SensitivitySpec(BaseModel):
    """How to run the sensitivity stage: which suites, which conditions, and which
    checkpoints form the calibration ladder (AGENTS.md, Belief and action suites D8).

    Lives on the job next to `EfficacySpec` for the same reason it does: this says what
    to *run*, while `eval.evalgen` says what the instrument *is*.
    """

    suites: list[str] = Field(default_factory=lambda: ["belief", "action"])
    suites_from: str | None = None
    """Run id whose validated suites to score; defaults to the job's own run id. Exists
    for a second sensitivity invocation over the same suites (e.g. an 8B calibration
    ladder, which needs its own run id so it does not overwrite the 4B run's report)."""
    prompted_conditions: bool = True
    """Score under none / B+ / B- prompt prefixes on the base model -- the S_B/S_A
    measurement as AGENTS.md defines it."""
    calibration_arms: list[EfficacyArm] = Field(default_factory=list)
    """Checkpoints with known belief-installation depth, scored on the belief suite to
    check the suite reproduces their ordering (and that the acquiescence reading flags
    the checkpoints known to acquiesce). Reuses the EfficacyArm shape: an arm may point
    at any experiment's checkpoints by run id."""
    limit: int | None = None
    """Score only the first N items -- for proving the loop runs, not for results."""


class TransferSpec(BaseModel):
    """How to run the belief_eval/action_eval stages: which suites, which checkpoints,
    which contrasts, and where the sensitivity denominators come from.

    Same run-vs-instrument split as `EfficacySpec`/`SensitivitySpec`. The netting
    contrast is not optional decoration: the off-topic control scores 0.42 vs base 0.09
    on the belief suite, so a bare dB is a contaminated number here exactly as the
    letter reading was for efficacy (AGENTS.md, Belief and action suites and changelog/2026-08-17c.md).
    """

    suites_from: str | None = None
    """Run id whose validated (frozen) suites to score. A run overlay supplies it."""
    sensitivity_from: str | None = None
    """Run id whose sensitivity summary provides S_B/S_A for T_B/T_A; without it the
    stage reports deltas only."""
    arms: list[EfficacyArm] = Field(default_factory=_default_arms)
    contrast: tuple[str, str] = ("m_plus", "m_minus")
    control_contrast: tuple[str, str] | None = None
    """Matched control arm names whose paired difference is subtracted from the
    contrast (machinery netting). None reports the raw contrast alone, flagged."""
    limit: int | None = None


class DataSpec(BaseModel):
    """Which HF dataset repo `data/` mirrors, and how much of it to move."""

    repo_id: str = "sunnybak/sft-drift"
    paths: list[str] = Field(default_factory=list)
    """Sub-paths to sync, e.g. `["generated/factory_farming"]`. Empty means the whole tree
    (minus the LLM cache). Narrowing matters once checkpoints are in there: a full push is
    multi-GB, and most of the time only one run's artifacts changed."""


class ChatSpec(BaseModel):
    """The interactive client's session settings (`stage=chat`)."""

    adapter: str | None = None
    """Path to a LoRA adapter directory, or None for the base checkpoint."""
    system: str | None = None
    temperature: float = 0.0
    max_new_tokens: int = 1024
    thinking: bool = False
    """Enable Qwen3 `<think>` blocks. Off by default so a reply is the direct answer."""
    stream: bool = True
    prompt: str | None = None
    """Send one prompt, print the reply, exit -- for piping."""


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
    belief_eval: BeliefEvalSpec | None = None
    """Optional with a None default on purpose: control_offtopic has no belief suite,
    and making this required would break every existing experiment file and test."""
    action_eval: ActionEvalSpec | None = None
    orthogonal_to: str | None = None
    """Another experiment id this corpus must stay clear of, for a control experiment.

    Set on `control_offtopic`, whose whole purpose is to carry no factory_farming content:
    `validation.orthogonality` checks its documents never mention that experiment's
    vocabulary. Config rather than a hardcoded pair because which experiment a control
    controls *for* is an experimental design decision -- and a second control would
    otherwise need code."""


class DatasetConfig(DatasetGenConfig):
    """`configs/dataset/*.yaml`: the generation prompts (inherited) plus the judge that
    scores what they produced.

    One file, and one model, because they are one decision: a judge check is written
    against the prompt that generated the text it reads, and changing a prompt without
    revisiting its checks is how a corpus starts passing checks that no longer mean
    anything. Extending `DatasetGenConfig` rather than nesting it keeps the prompt fields
    at the top level of the file, where they already are, so adopting this shape did not
    require reflowing 200 lines of indentation-sensitive Jinja block scalars -- and any
    function that wants only the generation half still takes a `DatasetGenConfig`.
    """

    judge: JudgeConfig


class EvalGenConfig(BaseModel):
    """`configs/eval/*.yaml`'s `evalgen` block: how belief/action items are generated,
    rendered, judged, and gated (see AGENTS.md, Belief and action suites).

    Prompts are config, not code -- a changed prompt is a changed measurement. Tool
    schemas stay in code (`evals/generate.py`), following `generation/prompts.py`.
    """

    belief_item_template: str
    action_item_template: str
    item_prompt_template: str
    """How a validated item is rendered for the model under test: statement or scenario,
    then labelled options, then a single-letter instruction; takes an optional
    intervention prefix (the B+/B- conditions of the sensitivity stage)."""
    option_labels: list[str] = Field(default_factory=lambda: ["A", "B"])
    belief_item_checks: list[JudgeCheckSpec] = Field(default_factory=list)
    action_item_checks: list[JudgeCheckSpec] = Field(default_factory=list)
    check_prompt_template: str = ""
    """Renders one item plus one check question for the judge."""
    leakage_flag_threshold: float = 0.5
    min_option_length_ratio: float = 0.6
    duplicate_overlap_threshold: float = 0.6
    seed_offset: int = 0
    """Added to the item index before drawing incidental scene details (requester name,
    region, company) for action items.

    Those draws are `choose_*(seed=index)` -- the same call `dataset/generate.py` makes
    for training documents -- so at offset 0 action item `i` is set in the *same* region,
    at the *same* company, with the *same* requester as training document `i`. Measured
    on `evalgen_v1`: 33/33 shared indices collide with `explicit-control-v1` and
    `-v2-diverse` on all three fields. (`factory_farming_v1` does not collide, but only
    by accident -- it was generated against the smaller pre-expansion `regions.json`, per
    the pool-edit warning in AGENTS.md. Any corpus generated against the current pool
    will collide.)

    An eval item staged in the identical scene as a training document is a shared-surface
    path between corpus and instrument that the leakage check does not cover: it shingles
    item text against document text, and a bare place name is too short to trip it.

    Offset the eval into its own seed namespace to break that pairing. Note what this
    does and does not buy: it removes the index-locked collision, but it cannot make the
    two draw-sets disjoint -- both sample the same pool, so a given eval region still
    turns up somewhere in a large corpus at chance rate (measured: ~13-20% of eval
    regions, roughly flat across offsets of +1, +10, +1000). Disjointness would need a
    partitioned pool, which costs scene diversity; the index-lock is the part worth
    removing. Prefer a large offset over `+1`, so the namespace is visibly deliberate
    rather than looking like an off-by-one.

    Belief items are unaffected -- they carry no scene, only an abstract normative
    statement.

    Defaults to 0 so every suite generated before this field reproduces exactly; changing
    it changes the instrument, which per AGENTS.md means a new suite version, not an edit
    to an existing one."""


class EvalConfig(BaseModel):
    """`configs/eval/*.yaml`. The efficacy block is the built suite; `evalgen` covers
    the generated belief/action suites (see AGENTS.md, Belief and action suites)."""

    efficacy: EfficacyConfig
    evalgen: EvalGenConfig | None = None
    """Optional so eval files predating the evalgen stage still parse; the stage raises
    if it is missing."""


Stage = Literal[
    "datagen",
    "sft",
    "efficacy",
    "absorption",
    "trajectory",
    "report",
    "writeup",
    "evalgen",
    "sensitivity",
    "belief_eval",
    "action_eval",
    "calibrate",
    "download_models",
    "perf_bench",
    "choice_bench",
    "memorization_bench",
    "agreement_record",
    "agreement_check",
    "chat",
    "data_push",
    "data_pull",
]
"""Every job the runner can dispatch. An explicit union rather than a free string so a
typo in a config fails at load with the list of valid stages, and so
`tests/test_stages.py` can check the registry covers exactly these.

Benchmarks and data sync are stages too, even though they are not experiment pipeline
steps: they are still "a job configured by a file and run by one entrypoint", which is
the only property the runner needs. What distinguishes them is where their output goes
(a hardware profile, a benchmark JSON) rather than how they are launched."""


class JobConfig(BaseModel):
    """One resolved job: the sole input to a stage, and the output counterpart of
    `RunResult`.

    Composed by Hydra from `configs/` (defaults, groups, a `run/` overlay, then CLI
    overrides) and validated into this shape at the entrypoint -- see `runs.load_job`.
    Nothing under `src/` reads YAML or touches Hydra to get one; a stage is a plain
    function of this object, which is what lets `scripts/` build one in Python and call
    the same code path the runner does.

    Every config the pipeline has is reachable from here, which is the point: before
    this, `RunConfig.overrides` deep-merged onto the *experiment* spec only, so a run
    could not set a training hyperparameter, and `evals/__main__.py` grew fifteen
    command-line flags in parallel to say what a run config could not.
    """

    run_id: str
    stage: Stage = "datagen"
    related_runs: dict[str, str] = Field(default_factory=dict)
    """Sibling run ids that belong with this one, mapped to why, e.g.
    `{matrix_v1_step24: "the same arms read at step 24, where belief transfer peaks"}`.

    Declared, following `training.corpus_from` / `absorption.corpus_run_id` /
    `transfer.suites_from` -- the repo's idiom for one run naming another. Those are all
    *inputs*, though, and this is the case they cannot express: two runs that read nothing
    of each other's but are one experiment, which is what a checkpoint-step reading is.

    One run id still names exactly one set of artifacts; that rule is what keeps results
    interpretable and is not being relaxed. What is added is a pointer, because without one
    a reader who finds `matrix_v1` has no way to learn that `matrix_v1_step24` exists or
    that it carries the better reading -- only the overlay's own header said so, and
    nothing reads overlays. `stage=report` renders it as links between the two reports.

    Declare it on BOTH runs. It is a relation, and a one-way pointer is how the reader
    coming from the other direction stays lost."""

    experiment: ExperimentConfig
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    models: ModelsConfig
    dataset: DatasetConfig
    eval: EvalConfig

    data: DataSpec = Field(default_factory=DataSpec)
    chat: ChatSpec = Field(default_factory=ChatSpec)
    efficacy: EfficacySpec = Field(default_factory=EfficacySpec)
    absorption: AbsorptionSpec = Field(default_factory=AbsorptionSpec)
    trajectory: TrajectorySpec = Field(default_factory=TrajectorySpec)
    """Only read by the efficacy stage. Lives on the job rather than in `eval` because it
    says what to *run* (which checkpoints, which contrast), while `eval.efficacy` says
    what the instrument *is* (framings, answer format) -- the same split as a run config
    versus an experiment spec."""
    writeup: WriteupSpec = Field(default_factory=WriteupSpec)
    """Only read by the writeup stage; names the result runs to synthesize."""
    sensitivity: SensitivitySpec = Field(default_factory=SensitivitySpec)
    """Only read by the sensitivity stage; same run-vs-instrument split as `efficacy`."""
    transfer: TransferSpec = Field(default_factory=TransferSpec)
    """Only read by the belief_eval/action_eval stages."""

    replicates: int = 1
    """Repeated generation passes over the *same* seeded prompts, to measure the model's
    own sampling variance rather than to generate new content (see `generation.random`).
    Each pass salts the LLM cache with its replicate number so it gets an independent
    answer instead of the first pass's cached one."""
    throughput: int = 8
    """Concurrent in-flight LLM calls. Bounded by the org's tokens-per-minute ceiling
    rather than by latency: see `configs/run/control_offtopic_v2.yaml`, where judging at
    20 saturated the limit and died on an unretried 429."""
    force: bool = False
    """Redo work that is already done: re-issue LLM calls that are in the cache, retrain
    a checkpoint whose summary says COMPLETED, rewrite existing artifacts. One flag for
    what used to be a per-stage assortment (`override_cache`, `--no-train`), since it is
    one intent."""
    smoke: bool = False
    """Prove the loop runs without doing the real work (2 training steps, throwaway
    artifact paths). Never overwrites a real run's outputs -- see `stages.sft`."""

    def training_root_for(self, experiment_id: str, run_id: str) -> Path:
        """Checkpoint directory for an arbitrary experiment/run pair.

        On the config rather than in `stages.sft` so an efficacy arm pointing at another
        experiment's checkpoints (a control arm) resolves the path the same way the stage
        that wrote it did, instead of two places agreeing by coincidence.
        """
        return CHECKPOINTS_DIR / experiment_id / run_id

    @property
    def model_spec(self) -> ModelSpec:
        """The `ModelSpec` for `training.model`, resolved against `models`.

        A property rather than a validated field because `configs/models/*.yaml` carries
        every model this repo knows about, and which one a job uses is
        `training.model` -- one place, not two that can disagree.
        """
        try:
            return self.models.models[self.training.model]
        except KeyError:
            known = ", ".join(sorted(self.models.models))
            raise KeyError(
                f"training.model={self.training.model!r} is not in models config (known: {known})"
            ) from None
