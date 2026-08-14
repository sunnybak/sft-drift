"""Gate a scored corpus down to the pairs worth training on.

Combines `dataset.generate`'s `documents.jsonl` with `dataset.score`'s `scores.jsonl`
to decide, per pair, whether it belongs in the training-ready corpus. Runs
automatically after judging (see `runs.run_datagen`), no new LLM calls needed --
gating is pure post-processing of scores already computed.

A pair is kept only if every *gating* check on both its documents, and every
pair-level check, passed. Premise/contrast checks (ids `premise_*`/`contrast_*`, see
`validation.judge.document_checks`) do not gate: they measure how strongly a document's
evidence supports its polarity, one fact at a time -- a matter of degree the
corpus-level pass rate already reports (see `check_pass_rates`/`below_threshold`
below), not a single-document defect that disqualifies the pair. Leakage,
action-advice, meta-reference, style, and pair-matchedness checks do gate: any one
failing means the pair does not represent what the experiment claims it does, or is
not usable prose.

Writes the passing subset to `data/validated/<experiment_id>/<run_id>/documents.jsonl`
-- the filtered artifact `data/validated/` was reserved for.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from belief_transfer.schemas import ExperimentConfig, JudgeConfig
from belief_transfer.validation import judge

VALIDATED_DIR = Path(__file__).resolve().parents[3] / "data" / "validated"
DOCUMENTS_FILENAME = "documents.jsonl"


def validated_documents_path(experiment_id: str, run_id: str) -> Path:
    """Where a run's gated corpus lives: `data/validated/<experiment_id>/<run_id>/documents.jsonl`."""
    return VALIDATED_DIR / experiment_id / run_id / DOCUMENTS_FILENAME


def _gates(check_id: str) -> bool:
    """Whether a failing check should exclude the pair it belongs to. See module
    docstring: premise/contrast checks don't; everything else does."""
    return not (check_id.startswith("premise_") or check_id.startswith("contrast_"))


def gate_pairs(documents: list[dict], scores: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split `documents` into (kept, dropped) pairs using `scores`' gating checks.

    A pair (matched by `run`, `index`) is kept only if it is complete (has both a
    `positive` and `negative` document) and no gating check on it failed. Always
    returns whole pairs -- SFT trains on the matched pair, never one polarity alone.
    """
    failing_pairs: set[tuple[int, int]] = set()
    for row in scores:
        if _gates(row["check_id"]) and not row["passed"]:
            failing_pairs.add((row["run"], row["index"]))

    grouped: dict[tuple[int, int], dict[str, dict]] = defaultdict(dict)
    for doc in documents:
        grouped[(doc["run"], doc["index"])][doc["polarity"]] = doc

    kept: list[dict] = []
    dropped: list[dict] = []
    for key, pair in grouped.items():
        complete = "positive" in pair and "negative" in pair
        target = kept if complete and key not in failing_pairs else dropped
        target.extend(pair.values())

    return kept, dropped


def write_gated(rows: list[dict], out_path: Path) -> Path:
    """Write `rows` (as built by `gate_pairs`) to `out_path`, overwriting it."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def check_pass_rates(scores: list[dict]) -> dict[str, float]:
    """Share of scored calls that passed, per check id -- across the whole corpus,
    not per pair. This is the quantity `JudgeCheckSpec.threshold` sets a bar for."""
    totals: dict[str, int] = defaultdict(int)
    passes: dict[str, int] = defaultdict(int)
    for row in scores:
        totals[row["check_id"]] += 1
        if row["passed"]:
            passes[row["check_id"]] += 1
    return {check_id: passes[check_id] / total for check_id, total in totals.items()}


def check_thresholds(experiment: ExperimentConfig, config: JudgeConfig | None = None) -> dict[str, float]:
    """Each check id's configured pass-rate threshold (`JudgeCheckSpec.threshold`)."""
    config = config or judge.load_judge_config()
    checks = (
        judge.document_checks(experiment, "positive", config)
        + judge.document_checks(experiment, "negative", config)
        + judge.pair_checks(config)
    )
    return {check.id: check.threshold for check in checks}


def below_threshold(pass_rates: dict[str, float], thresholds: dict[str, float]) -> list[str]:
    """Check ids whose corpus-wide pass rate falls short of its configured threshold.

    Informational, not a gate: it flags checks the corpus as a whole is weak on (e.g.
    a premise consistently missing), which per-pair gating above deliberately does not
    act on by itself.
    """
    return sorted(
        check_id
        for check_id, rate in pass_rates.items()
        if check_id in thresholds and rate < thresholds[check_id]
    )


def gating_summary(
    experiment: ExperimentConfig,
    documents: list[dict],
    scores: list[dict],
    kept: list[dict],
    config: JudgeConfig | None = None,
) -> dict[str, Any]:
    """Assemble the numbers `runs.run_datagen` reports for one invocation's gating."""
    n_pairs = len({(doc["run"], doc["index"]) for doc in documents})
    n_kept_pairs = len({(doc["run"], doc["index"]) for doc in kept})
    pass_rates = check_pass_rates(scores)
    thresholds = check_thresholds(experiment, config)
    return {
        "pairs_total": n_pairs,
        "pairs_kept": n_kept_pairs,
        "pairs_dropped": n_pairs - n_kept_pairs,
        "checks_below_threshold": below_threshold(pass_rates, thresholds),
    }
