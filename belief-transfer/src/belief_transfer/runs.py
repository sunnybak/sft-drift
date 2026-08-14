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

from belief_transfer.analysis.report import build_report, write_report
from belief_transfer.dataset import gate, generate, score
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import ExperimentConfig, file_sha

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

    report = build_report(
        context,
        stage="datagen",
        experiment_id=experiment.id,
        run_id=run.run_id,
        datapoints=len(documents),
        artifacts=[out_path, scores_path, validated_path],
        gating=gating,
    )
    write_report(
        report, experiment_id=experiment.id, run_id=run.run_id, stage="datagen", path=report_path
    )
    return out_path


async def run(run_config: RunConfig, run_config_path: Path, *, override_cache: bool = False) -> Path:
    """Dispatch a run config to its stage. Only `datagen` exists so far."""
    if run_config.stage == "datagen":
        return await run_datagen(run_config, run_config_path, override_cache=override_cache)
    raise NotImplementedError(f"stage {run_config.stage!r} is not implemented yet")
