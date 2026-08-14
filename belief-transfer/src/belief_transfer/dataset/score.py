"""Score a generated corpus against the judge's document/pair checks.

Runs once per `runs.run_datagen` invocation, after all replicates have been written to
`documents.jsonl`, over the full accumulated corpus (not per replicate): every document
gets `judge.document_checks` for its polarity, every pair gets `judge.pair_checks`, and
results are written to `scores.jsonl` next to `documents.jsonl`. The corpus and its
per-document/per-pair judge scores are one bundle produced by one invocation, not two
separately-timed artifacts, so they live together rather than under a separate
`data/validated/` tree.

`data/validated/` is reserved for the *filtered* subset a future gating step would
produce by applying each check's `threshold` to this file -- a genuinely different
artifact (a smaller corpus), not just a copy of these scores.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from belief_transfer.dataset.generate import GENERATED_DIR
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import ExperimentConfig, JudgeConfig
from belief_transfer.validation import judge

SCORES_FILENAME = "scores.jsonl"


def scores_path(experiment_id: str, run_id: str) -> Path:
    """Where a run's judge scores live: `data/generated/<experiment_id>/<run_id>/scores.jsonl`."""
    return GENERATED_DIR / experiment_id / run_id / SCORES_FILENAME


async def score_dataset(
    experiment: ExperimentConfig,
    documents: list[dict],
    *,
    config: JudgeConfig | None = None,
    throughput: int = 20,
    override_cache: bool = False,
    context: RunContext | None = None,
) -> list[dict]:
    """Judge every document and every pair in `documents` (rows shaped like
    `dataset.generate`'s output: at least `run`, `index`, `polarity`, `text`).

    Returns one row per check answered, shaped for `dataset.review.render_review` and
    a future gating step: `run`, `index`, `polarity` ("positive"/"negative" for a
    document check, "pair" for a pair check), `check_id`, `expect`, `answer`,
    `passed`, `evidence`, `judge_model`, `prompt_version`.

    `context`, if given, records every judge call's cost/tokens/latency into it (see
    `generation.context.RunContext`) -- pass the same context a datagen stage used so
    judging counts toward that stage's report, not a separate one.
    """
    config = config or judge.load_judge_config()

    checks: list[judge.Check] = []
    prompts: list[str] = []
    identifiers: list[dict[str, object]] = []

    for doc in documents:
        for check in judge.document_checks(experiment, doc["polarity"], config):
            checks.append(check)
            prompts.append(judge.document_prompt(check, doc["text"], config))
            identifiers.append(
                {"run": doc["run"], "index": doc["index"], "polarity": doc["polarity"]}
            )

    pairs: dict[tuple[int, int], dict[str, dict]] = defaultdict(dict)
    for doc in documents:
        pairs[(doc["run"], doc["index"])][doc["polarity"]] = doc

    for (run, index), pair in sorted(pairs.items()):
        if "positive" not in pair or "negative" not in pair:
            continue  # an incomplete pair (e.g. a partially failed generation) can't be matched
        for check in judge.pair_checks(config):
            checks.append(check)
            prompts.append(
                judge.pair_prompt(check, pair["positive"]["text"], pair["negative"]["text"], config)
            )
            identifiers.append({"run": run, "index": index, "polarity": "pair"})

    results = await judge.run_checks(
        checks, prompts, throughput=throughput, override_cache=override_cache, context=context
    )

    return [
        {
            "experiment": experiment.id,
            **identifier,
            "check_id": result.check_id,
            "expect": result.expect,
            "answer": result.answer,
            "passed": result.passed,
            "evidence": result.evidence,
            "judge_model": result.judge_model,
            "prompt_version": result.prompt_version,
        }
        for identifier, result in zip(identifiers, results)
    ]


def write_scores(rows: list[dict], out_path: Path) -> Path:
    """Write `rows` (as built by `score_dataset`) to `out_path`, overwriting it."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path
