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
from collections.abc import Sequence
from pathlib import Path

from belief_transfer.generation import llm, prompts
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import (
    ContentPlan,
    DatasetGenConfig,
    ExperimentConfig,
    Polarity,
    Provenance,
    model_sha,
)

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
    config: DatasetGenConfig,
    *,
    run: int = 1,
    run_id: str | None = None,
    config_sha: str | None = None,
    n_items: int | None = None,
    indices: Sequence[int] | None = None,
    out_path: Path | None = None,
    throughput: int = 8,
    override_cache: bool = False,
    context: RunContext | None = None,
) -> Path:
    """Generate `n_items` matched pairs for `experiment` and append them to a JSONL corpus.

    Both configs arrive as typed objects rather than as paths to read: nothing under
    `src/` loads YAML (see `belief_transfer.config`), so this cannot silently pick up a
    file that differs from the one the caller resolved.

    Defaults to `experiment.dataset.n_items` items and to
    `documents_path(experiment.id, run_id or "adhoc")` -- data/ is namespaced by
    experiment under each pipeline-stage folder (generated/, validated/, checkpoints/,
    results/), and by run id under that, since more than one experiment and more than
    one run eventually share each of those folders.

    Each row carries three fingerprints, which pin down different things: `experiment_sha`
    and `dataset_config_sha` hash the two *resolved* configs used (see `schemas.model_sha`
    -- resolved, because with layered composition no single file determines what ran), and
    `config_sha` identifies the whole job, so a row can be traced back to the exact
    invocation as well as to the two specs that shaped it.

    LLM calls are cached by `generation.llm`/`generation.cache` on (model, prompt,
    tool, replicate). `run` is passed through as the cache's `replicate` -- never sent
    to the model, only mixed into the cache key -- so replicate passes over the same
    seeded prompts (see `stages.datagen`) don't collapse onto one cached answer,
    while still being cheap to re-run after a crash: a killed invocation just re-hits
    the cache for whatever it already completed. Pass `override_cache=True` to force
    fresh calls, e.g. after a prompt template change you want to re-run with the same
    `run_id`.

    `context`, if given, records every call's cost/tokens/latency into it (see
    `generation.context.RunContext`); `stages.datagen` uses this to write the
    stage's `data/results/.../datagen.yaml` summary.
    """
    n_items = experiment.dataset.n_items if n_items is None else n_items
    # `indices` regenerates a chosen subset instead of a prefix. Seeds are pure functions
    # of the index, so item 42 is item 42 whether it arrives in a full pass or on its own
    # -- which is what lets `scripts/topup_corpus.py` retry only the pairs a run dropped
    # rather than paying for all 150 again.
    item_indices = list(range(n_items)) if indices is None else list(indices)
    out_path = out_path or documents_path(experiment.id, run_id or "adhoc")
    experiment_sha = model_sha(experiment)
    dataset_config_sha = model_sha(config)

    seeds = [
        prompts.seed_item(
            index,
            use_formats=config.use_formats,
            segments=experiment.dataset.segments,
            personas=experiment.dataset.personas,
            formats_file=config.formats_file,
        )
        for index in item_indices
    ]
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
    for position, seed in enumerate(seeds):
        # `plans` is keyed by position in this batch; the row records `seed.index`, the
        # item's real index, so a subset pass writes rows indistinguishable from a full
        # one's.
        plan = plans[position]
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
                    "index": seed.index,
                    "polarity": polarity,
                    "run_id": run_id,
                    "config_sha": config_sha,
                    "structure": seed.structure,
                    "region_seed": seed.region,
                    "names_seed": list(seed.names),
                    "seed_words": list(seed.seed_words),
                    "plan": plan.model_dump(),
                    "model": provenance.model,
                    "experiment_sha": provenance.experiment_sha,
                    "dataset_config_sha": provenance.config_shas["dataset_config"],
                    "format": seed.document_format.id if seed.document_format else None,
                    "segment_seed": seed.segment,
                    "prompt": prompts.render_document_prompt(
                        experiment, plan, polarity, config, seed
                    ),
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
        for position, job in enumerate(jobs):
            text = texts[position]
            seed = seeds[position // 2]
            row = {
                **job,
                "text": text,
                "n_words": len(text.split()),
                # The turns this document trains on, when a surface form was drawn.
                # Empty means the form was declared but the text does not parse as it
                # (a Q&A exchange that broke its own alternation); `dataset.gate` drops
                # those pairs, and the raw text is still written out either way, per
                # AGENTS.md's "store generated artifacts before filtering".
                "messages": prompts.messages_for(seed, text, experiment.dataset.topic),
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    return out_path
