"""End-to-end pipeline: build one experiment's SFT dataset from its config.

Generation runs in two stages per item, mirroring `belief_transfer.generation.prompts`:

    seed_item(index)                         deterministic structure/region/names/words
      -> render_plan_prompt -> PLAN_TOOL     one belief-neutral content plan per item
      -> render_document_prompt (x2)         one document per polarity, from that plan

Both polarities of a pair are rendered from the same plan and seed, so they differ only
in the premises they report. Rows are appended as JSONL, one per document, carrying
enough to reproduce and re-judge it later: the seed draw, the plan, the exact prompt,
and a `Provenance` fingerprint of the experiment, dataset-config, and model used.
"""

from __future__ import annotations

import json
from pathlib import Path

from belief_transfer.generation import llm, prompts
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import ContentPlan, ExperimentConfig, Polarity, Provenance, file_sha

GENERATED_DIR = Path(__file__).resolve().parents[3] / "data" / "generated"
DOCUMENTS_FILENAME = "documents.jsonl"


def documents_path(experiment_id: str, run_id: str) -> Path:
    """Where a run's generated corpus lives: `data/generated/<experiment_id>/<run_id>/documents.jsonl`.

    One directory per run id (rather than one file named after it) so a run's derived
    artifacts -- its judge scores (`dataset.score`), the review rendered from both
    (`dataset.review`) -- sit next to it instead of being scattered across
    differently-suffixed filenames or a separate top-level tree.
    """
    return GENERATED_DIR / experiment_id / run_id / DOCUMENTS_FILENAME


async def generate_dataset(
    experiment: ExperimentConfig,
    experiment_path: Path,
    *,
    run: int = 1,
    run_id: str | None = None,
    run_config_sha: str | None = None,
    n_items: int | None = None,
    out_path: Path | None = None,
    dataset_config_path: Path = prompts.DATASET_CONFIG_PATH,
    throughput: int = 8,
    override_cache: bool = False,
    context: RunContext | None = None,
) -> Path:
    """Generate `n_items` matched pairs for `experiment` and append them to a JSONL corpus.

    `experiment_path` is required (rather than re-deriving it) so the row-level
    fingerprint is exact even when the caller already parsed the config elsewhere.
    Defaults to `experiment.dataset.n_items` items and to
    `documents_path(experiment.id, run_id or "adhoc")` -- data/ is namespaced by
    experiment under each pipeline-stage folder (generated/, validated/, checkpoints/,
    results/), and by run id under that, since more than one experiment and more than
    one run eventually share each of those folders.

    `run_id`/`run_config_sha` identify the `belief_transfer.runs.RunConfig` invocation
    that produced this row, if any (see `belief_transfer.runs.run_datagen`). They are
    separate from `experiment_sha`: a run config can override the experiment it is based
    on, so `experiment_sha` alone would understate what actually produced the row --
    the pair of hashes together pin down the effective config, not just the base file.

    LLM calls are cached by `generation.llm`/`generation.cache` on (model, prompt,
    tool, replicate). `run` is passed through as the cache's `replicate` -- never sent
    to the model, only mixed into the cache key -- so replicate passes over the same
    seeded prompts (see `runs.run_datagen`) don't collapse onto one cached answer,
    while still being cheap to re-run after a crash: a killed invocation just re-hits
    the cache for whatever it already completed. Pass `override_cache=True` to force
    fresh calls, e.g. after a prompt template change you want to re-run with the same
    `run_id`.

    `context`, if given, records every call's cost/tokens/latency into it (see
    `generation.context.RunContext`); `runs.run_datagen` uses this to write the
    stage's `data/results/.../datagen.yaml` summary.
    """
    config = prompts.load_dataset_config(dataset_config_path)
    n_items = experiment.dataset.n_items if n_items is None else n_items
    out_path = out_path or documents_path(experiment.id, run_id or "adhoc")
    experiment_sha = file_sha(experiment_path)
    dataset_config_sha = file_sha(dataset_config_path)

    seeds = [prompts.seed_item(index) for index in range(n_items)]
    plan_prompts = [prompts.render_plan_prompt(experiment, seed, config) for seed in seeds]

    plans: dict[int, ContentPlan] = {}
    async for completion in llm.batch(
        plan_prompts,
        throughput=throughput,
        tool=prompts.PLAN_TOOL,
        override_cache=override_cache,
        replicate=run,
        context=context,
    ):
        if completion.payload is None:
            raise RuntimeError(f"plan call for item {completion.index} returned no payload")
        plans[completion.index] = ContentPlan.model_validate(completion.payload)

    jobs: list[dict[str, object]] = []
    for index, seed in enumerate(seeds):
        plan = plans[index]
        polarity: Polarity
        for polarity in ("positive", "negative"):
            provenance = Provenance(
                experiment_id=experiment.id,
                experiment_sha=experiment_sha,
                config_shas={"dataset_config": dataset_config_sha},
                model=llm.MODEL,
            )
            jobs.append(
                {
                    "experiment": experiment.id,
                    "run": run,
                    "index": index,
                    "polarity": polarity,
                    "run_id": run_id,
                    "run_config_sha": run_config_sha,
                    "structure": seed.structure,
                    "region_seed": seed.region,
                    "names_seed": list(seed.names),
                    "seed_words": list(seed.seed_words),
                    "plan": plan.model_dump(),
                    "model": provenance.model,
                    "experiment_sha": provenance.experiment_sha,
                    "dataset_config_sha": provenance.config_shas["dataset_config"],
                    "prompt": prompts.render_document_prompt(experiment, plan, polarity, config),
                }
            )

    texts: dict[int, str] = {}
    async for completion in llm.batch(
        [job["prompt"] for job in jobs],
        throughput=throughput,
        override_cache=override_cache,
        replicate=run,
        context=context,
    ):
        texts[completion.index] = completion.text

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as handle:
        for index, job in enumerate(jobs):
            text = texts[index]
            row = {**job, "text": text, "n_words": len(text.split())}
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    return out_path
