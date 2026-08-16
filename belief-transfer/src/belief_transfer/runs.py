"""Run configs: override an experiment spec for one invocation of the pipeline.

A run config lives at `runs/<run_id>.yaml`. It names a base experiment
(`experiments/<experiment>/experiment.yaml`), an optional set of overrides deep-merged
onto that spec before validation -- `n_items`, `size_words`, `belief.statement`,
`dimensions`, anything `ExperimentConfig` has -- and how many replicate generation
passes to run.

Replicates are repeated passes over the *same* seeded prompts (`seed_item` is a pure
function of the item index, not the replicate number), so they measure the model's own
sampling variance rather than generating new content. This is how the factory_farming
pilot corpora were produced by hand before this module existed: three manual calls to
`generate_dataset(..., run=1/2/3, n_items=4, ...)`, never persisted as a spec.

Only the `datagen` stage is implemented. `stage` is an explicit field (rather than
always running "the whole pipeline") so adding SFT/eval later is a new branch in `run`,
not a rewrite of what already runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from belief_transfer.analysis.report import build_result, write_result
from belief_transfer.dataset import gate, generate, score
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference.model import load_models_config
from belief_transfer.schemas import ExperimentConfig, file_sha
from belief_transfer.training import sft

ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT / "runs"
EXPERIMENTS_DIR = ROOT / "experiments"


class RunConfig(BaseModel):
    run_id: str
    experiment: str
    """Experiment id; resolved to experiments/<experiment>/experiment.yaml."""
    stage: Literal["datagen", "sft", "belief_eval", "action_eval"] = "datagen"
    """Only "datagen" is implemented; the others are valid config today so a run config
    can be written ahead of the code that runs it, but `run()` raises for them."""
    overrides: dict[str, Any] = Field(default_factory=dict)
    """Deep-merged onto the base experiment.yaml before validation."""
    replicates: int = 1
    throughput: int = 8


def _deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Merge `overrides` onto `base`, recursing into nested dicts; other values replace."""
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_run_config(path: Path) -> RunConfig:
    return RunConfig.model_validate(yaml.safe_load(path.read_text()))


def resolve_run_path(name_or_path: str) -> Path:
    """Accept a run id ("pilot_trimmed"), a bare filename, or a full path."""
    candidate = Path(name_or_path)
    if candidate.exists():
        return candidate
    for suffix in (".yaml", ".yml"):
        candidate = RUNS_DIR / f"{name_or_path}{suffix}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"no run config found for {name_or_path!r} under {RUNS_DIR}")


def resolve_experiment(run: RunConfig) -> tuple[ExperimentConfig, Path]:
    """Load the run's base experiment spec and apply its overrides.

    Returns the resolved config and the *base* experiment.yaml path. That file, not the
    run config, is what `generate_dataset`'s `experiment_sha` hashes; the override is
    fingerprinted separately via the run config's own sha (see `run_datagen`).
    """
    experiment_path = EXPERIMENTS_DIR / run.experiment / "experiment.yaml"
    raw = yaml.safe_load(experiment_path.read_text())
    merged = _deep_merge(raw, run.overrides)
    return ExperimentConfig.model_validate(merged), experiment_path


async def run_datagen(
    run: RunConfig,
    run_config_path: Path,
    *,
    out_path: Path | None = None,
    override_cache: bool = False,
    report_path: Path | None = None,
    scores_path: Path | None = None,
    validated_path: Path | None = None,
) -> Path:
    """Run the datagen stage: `run.replicates` generation passes over the same seeds,
    then judge every document and pair those replicates produced, then gate the
    scored corpus down to the pairs worth training on.

    Writes a fresh file per invocation (rather than appending indefinitely across
    repeated CLI runs of the same run config), then appends one `generate_dataset` call
    per replicate into it. Once every replicate has been written, judges the full
    accumulated corpus in one pass (see `dataset.score`) and writes its scores to
    `scores_path`, or `score.scores_path(experiment.id, run.run_id)` by default. Then
    gates it (see `dataset.gate`, no new LLM calls -- pure post-processing of the
    scores just computed) and writes the passing subset to `validated_path`, or
    `gate.validated_documents_path(experiment.id, run.run_id)` by default.

    `override_cache` forces every LLM call -- generation and judging alike -- to hit
    the API instead of the cache, e.g. after editing a prompt template and wanting
    fresh output under the same run id.

    Also writes a `data/results/<experiment_id>/<run_id>/datagen.yaml` summary (cost,
    tokens, latency, artifacts, gating outcome; see `analysis.report`) covering
    generation and judging together -- they're both work this one stage did -- at
    `report_path` if given.
    """
    experiment, experiment_path = resolve_experiment(run)
    out_path = out_path or generate.documents_path(experiment.id, run.run_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("")

    context = RunContext()
    run_config_sha = file_sha(run_config_path)
    for replicate in range(1, run.replicates + 1):
        await generate.generate_dataset(
            experiment,
            experiment_path,
            run=replicate,
            run_id=run.run_id,
            run_config_sha=run_config_sha,
            out_path=out_path,
            throughput=run.throughput,
            override_cache=override_cache,
            context=context,
        )

    documents = [json.loads(line) for line in out_path.read_text().splitlines()]
    scores_path = scores_path or score.scores_path(experiment.id, run.run_id)
    scores = await score.score_dataset(
        experiment,
        documents,
        throughput=run.throughput,
        override_cache=override_cache,
        context=context,
    )
    score.write_scores(scores, scores_path)

    kept, _dropped = gate.gate_pairs(documents, scores)
    validated_path = validated_path or gate.validated_documents_path(experiment.id, run.run_id)
    gate.write_gated(kept, validated_path)
    gating = gate.gating_summary(experiment, documents, scores, kept)

    result = build_result(
        context,
        stage="datagen",
        experiment_id=experiment.id,
        run_id=run.run_id,
        datapoints=len(documents),
        artifacts=[out_path, scores_path, validated_path],
        metrics={"gating": gating},
    )
    write_result(result, path=report_path)
    return out_path


async def run_sft(
    run: RunConfig,
    run_config_path: Path,
    *,
    validated_path: Path | None = None,
    output_root: Path | None = None,
    report_path: Path | None = None,
    smoke: bool = False,
) -> Path:
    """Run the sft stage: train M+ and M- LoRA checkpoints on `run.run_id`'s already-
    gated corpus.

    Reads `data/validated/<experiment_id>/<run_id>/documents.jsonl` -- the same
    `run_id` that produced it via a prior `datagen`-stage invocation of this run
    config's `run_id` -- rather than a separately-named source run, so one run id names
    one pipeline invocation end to end (generate this corpus, then train on it) instead
    of needing a second id just to point at the first.

    Training hyperparameters come from `configs/training.yaml` (`training.sft.
    load_training_config`), not `run.overrides`: `RunConfig.overrides` deep-merges onto
    the *experiment* spec (see `resolve_experiment`), and threading a second override
    path onto the training config as well is left as a follow-up rather than expanding
    `RunConfig`'s shape for a need this task doesn't yet have.

    Writes `data/results/<experiment_id>/<run_id>/sft.yaml`, same shape as `datagen`'s
    report but with an `sft` key (see `analysis.report.build_report`'s `extra`) holding
    each polarity's train summary instead of a `gating` key.
    """
    experiment, _ = resolve_experiment(run)
    training = sft.load_training_config()
    # A smoke run trains for 2 steps and still writes a `COMPLETED` summary, and
    # `train_one_arm` returns an existing `COMPLETED` checkpoint in place rather than
    # retraining -- so a smoke run written under the real run id would later be silently
    # reused as if it were the real thing. Its artifacts go somewhere else instead. The
    # corpus it reads is still the real run id's: only the outputs are throwaway.
    artifact_run_id = f"{run.run_id}-smoke" if smoke else run.run_id
    validated_path = validated_path or gate.validated_documents_path(experiment.id, run.run_id)
    output_root = output_root or sft.CHECKPOINTS_DIR / experiment.id / artifact_run_id

    summaries = sft.train(experiment, training, validated_path, output_root, smoke=smoke)

    artifacts = [validated_path]
    for polarity, summary in summaries.items():
        artifacts.append(Path(summary["dataset_file"]))
        artifacts.append(output_root / polarity / "final")

    result = build_result(
        RunContext(),  # sft does no LLM calls; an empty context reports all-zero cost/tokens.
        stage="sft",
        experiment_id=experiment.id,
        run_id=artifact_run_id,
        datapoints=sum(summary["n_samples"] for summary in summaries.values()),
        artifacts=artifacts,
        metrics={"sft": summaries},
        backend=backend_info(dtype=load_models_config().models[training.model].dtype),
    )
    write_result(result, path=report_path)
    return output_root


async def run(
    run_config: RunConfig, run_config_path: Path, *, override_cache: bool = False, smoke: bool = False
) -> Path:
    """Dispatch a run config to its stage."""
    if run_config.stage == "datagen":
        return await run_datagen(run_config, run_config_path, override_cache=override_cache)
    if run_config.stage == "sft":
        return await run_sft(run_config, run_config_path, smoke=smoke)
    raise NotImplementedError(f"stage {run_config.stage!r} is not implemented yet")
