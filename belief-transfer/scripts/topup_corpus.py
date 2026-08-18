"""Retry the pairs a datagen run dropped, and merge the ones that pass.

    python scripts/topup_corpus.py +run=multiformat_v2
    python scripts/topup_corpus.py +run=multiformat_v2 --attempts 3

Why this is worth doing rather than just generating more items: of the 50 pairs
`multiformat_v1` dropped, **41 failed exactly one gating check** -- 22 only
`pair_same_subject`, 11 only `style_no_contradiction`, 7 only `pair_same_shape`. Those
are near-misses of a sampling process, not items that are unusable in principle, and a
fresh draw of the same seeded prompt is a different sample of the same distribution.

The distinction that makes this legitimate rather than fitting the instrument: this
resamples the GENERATOR and re-judges the result against the unchanged bar. Nothing
about the judge, the thresholds, or which checks gate is touched, and a retried pair has
to clear exactly what the first attempt failed. Re-rolling until a pair passes is only
defensible while the bar itself is fixed -- if you ever find yourself wanting to change a
threshold here instead, that is the thing AGENTS.md rules out.

A script rather than a stage, per AGENTS.md's Configuration section: it builds the same
`JobConfig` through `config.load_job` and calls library functions in its own order. It
adds no new judging or gating logic -- `dataset.score` and `dataset.gate` decide, exactly
as they do for `stages.datagen`.

Attempts are numbered in each row's `run` field, which is also the LLM cache's replicate
salt, so attempt 2 of item 42 is a genuinely fresh draw of the identical prompt rather
than the cached answer from attempt 1. `gate.best_attempt_per_index` then keeps one
attempt per item, so an item that succeeds twice does not enter the corpus twice.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from belief_transfer import config as config_mod
from belief_transfer.analysis.report import build_result, write_result
from belief_transfer.dataset import gate, generate, score
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import JobConfig


def _read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _append(rows: list[dict], path: Path) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


async def topup(job: JobConfig, attempts: int) -> None:
    experiment = job.experiment
    documents_path = generate.documents_path(experiment.id, job.run_id)
    scores_path = score.scores_path(experiment.id, job.run_id)
    if not documents_path.exists():
        raise SystemExit(f"no corpus at {documents_path} -- run stage=datagen first")

    documents = _read(documents_path)
    scores = _read(scores_path)
    context = RunContext()
    started_with = len(gate.best_attempt_per_index(gate.gate_pairs(documents, scores)[0])) // 2

    for attempt in range(2, attempts + 2):
        kept, _ = gate.gate_pairs(documents, scores)
        passing = {row["index"] for row in kept}
        missing = sorted({row["index"] for row in documents} - passing)
        if not missing:
            print("[topup] every item has a passing pair; nothing to retry")
            break

        print(f"[topup] attempt {attempt}: retrying {len(missing)} dropped items ...")
        await generate.generate_dataset(
            experiment,
            job.dataset,
            run=attempt,
            run_id=job.run_id,
            config_sha=config_mod.config_sha(job),
            indices=missing,
            out_path=documents_path,
            throughput=job.throughput,
            context=context,
        )

        # Judge only what this attempt produced. `score_dataset` pairs documents by
        # (run, index), so handing it just the new rows keeps the pair checks correct.
        fresh = [row for row in _read(documents_path) if row["run"] == attempt]
        new_scores = await score.score_dataset(
            experiment,
            job.dataset.judge,
            fresh,
            throughput=job.throughput,
            context=context,
        )
        _append(new_scores, scores_path)

        documents = _read(documents_path)
        scores = _read(scores_path)
        recovered = {r["index"] for r in gate.gate_pairs(documents, scores)[0]} - passing
        print(f"[topup] attempt {attempt} recovered {len(recovered)} items")

    kept, _ = gate.gate_pairs(documents, scores)
    final = gate.best_attempt_per_index(kept)
    validated_path = gate.validated_documents_path(experiment.id, job.run_id)
    gate.write_gated(final, validated_path)

    pairs = len(final) // 2
    total = len({row["index"] for row in documents})
    print(
        f"\n[topup] {job.run_id}: {started_with} -> {pairs} pairs of {total} items "
        f"({pairs / total:.1%})"
    )
    by_attempt: dict[int, int] = {}
    for row in final:
        by_attempt[row["run"]] = by_attempt.get(row["run"], 0) + 1
    print("[topup] kept pairs by attempt: "
          + ", ".join(f"{run}: {count // 2}" for run, count in sorted(by_attempt.items())))

    result = build_result(
        context,
        stage="topup",
        experiment_id=experiment.id,
        run_id=job.run_id,
        datapoints=len(final),
        artifacts=[documents_path, scores_path, validated_path],
        metrics={
            "topup": {
                "pairs_before": started_with,
                "pairs_after": pairs,
                "items_total": total,
                "kept_by_attempt": {run: count // 2 for run, count in sorted(by_attempt.items())},
            }
        },
        config_sha=config_mod.config_sha(job),
    )
    write_result(result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("overrides", nargs="+", help="Hydra overrides, e.g. +run=multiformat_v2")
    parser.add_argument(
        "--attempts",
        type=int,
        default=1,
        help="How many extra passes to make over the still-dropped items (default 1).",
    )
    args = parser.parse_args()
    job = config_mod.load_job(args.overrides)
    asyncio.run(topup(job, args.attempts))


if __name__ == "__main__":
    main()
