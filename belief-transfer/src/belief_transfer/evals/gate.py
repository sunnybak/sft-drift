"""Judging and gating for generated eval items (AGENTS.md, Belief and action suites 4.4).

Unlike datagen -- where premise/contrast checks are informational and only a fixed set
gates -- EVERY check here gates, because each one names a structural defect in an
instrument: a belief item that is secretly factual, an action item that editorializes,
a pair of options that differ in more than the target. Items gate individually; if one
member of a D7 pair drops, its partner stays in the suite (it still measures belief)
but is excluded from the acquiescence reading (which needs whole pairs).

Direction checks are the one place `expect` is per-item rather than per-check: the
judge VERIFIES the direction the pipeline imposed (D5) -- `belief_direction_matches` and
`inference_direction_matches` expect yes on forward items and no on reverse-coded ones;
`action_direction_matches` always expects yes because the target-involving option is
canonically first. The judge never assigns a direction.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from jinja2 import Environment, StrictUndefined

from belief_transfer.evals import suite as suite_mod
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import EvalGenConfig, ExperimentConfig
from belief_transfer.validation import judge
from belief_transfer.validation.leakage import _shingles

_env = Environment(trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined)

CHECK_SETS = {
    "belief": "belief_item_checks",
    "action": "action_item_checks",
    "inference": "inference_item_checks",
}
DIRECTION_CHECKS = {
    "belief_direction_matches",
    "action_direction_matches",
    "inference_direction_matches",
}
PAIRED_SUITES = {"belief", "inference"}
"""Suites generated as D7 forward/reverse pairs: their direction check's expected answer
is per item (no on a reverse-coded one), and whole surviving pairs are worth counting."""


def item_checks(
    item: dict, experiment: ExperimentConfig, config: EvalGenConfig
) -> list[judge.Check]:
    """The rendered checks for one item, with direction expectations set per item."""
    context = {
        "topic": experiment.dataset.topic,
        "belief_statement": experiment.belief.statement,
        "target_products": (
            experiment.action_eval.target_products if experiment.action_eval else ""
        ),
        # Per-item, and only the inference suite's direction check uses it: unlike the
        # belief suite, whose direction is one fixed statement, each inference facet
        # asserts its own claim, so the judge has to be told which one it is verifying.
        "facet_claim": item.get("facet_claim") or "",
    }
    checks = []
    for spec in getattr(config, CHECK_SETS[item["suite"]]):
        expect = spec.expect
        if spec.id in {"belief_direction_matches", "inference_direction_matches"}:
            expect = not item["reverse_coded"]
        checks.append(judge.Check(
            id=spec.id,
            question=_env.from_string(spec.question).render(**context),
            expect=expect,
            threshold=spec.threshold,
        ))
    return checks


async def score_items(
    items: list[dict],
    experiment: ExperimentConfig,
    config: EvalGenConfig,
    *,
    throughput: int = 8,
    force: bool = False,
    context: RunContext | None = None,
) -> list[dict]:
    """One row per (item, check), in item order. Judged against the item's full visible
    text (statement or scenario plus both options, in canonical order)."""
    checks: list[judge.Check] = []
    prompts: list[str] = []
    owners: list[str] = []
    for item in items:
        text = suite_mod.item_text(item)
        for check in item_checks(item, experiment, config):
            checks.append(check)
            prompts.append(_env.from_string(config.check_prompt_template).render(
                item_text=text, question=check.question,
            ))
            owners.append(item["item_id"])
    results = await judge.run_checks(
        checks, prompts, throughput=throughput, override_cache=force, context=context
    )
    return [
        {
            "item_id": owner,
            "check_id": result.check_id,
            "expect": result.expect,
            "answer": result.answer,
            "passed": result.passed,
            "evidence": result.evidence,
            "judge_model": result.judge_model,
        }
        for owner, result in zip(owners, results, strict=True)
    ]


def _length_ratio(options: list[str]) -> float:
    counts = [len(option.split()) for option in options]
    return min(counts) / max(counts) if max(counts) else 0.0


def _max_overlap(text: str, references: list[set], n: int = 8) -> float:
    shingles = _shingles(text, n)
    if not shingles:
        return 0.0
    return max((len(shingles & ref) / len(shingles) for ref in references), default=0.0)


def gate_items(
    items: list[dict],
    scores: list[dict],
    *,
    config: EvalGenConfig,
    train_texts: list[str] | None = None,
) -> tuple[list[dict], dict[str, list[str]]]:
    """(kept items, drop reasons by item_id).

    Order of the deterministic gates is deliberate: leakage and length are per-item
    facts, but near-duplicate keeps the EARLIER item, so it must run over the
    already-otherwise-valid set or a dropped early item could shadow a valid later one.
    """
    failed: dict[str, list[str]] = defaultdict(list)
    for row in scores:
        if not row["passed"]:
            failed[row["item_id"]].append(row["check_id"])

    train_shingles = [_shingles(text, 8) for text in (train_texts or [])]
    survivors: list[dict] = []
    for item in items:
        reasons = list(failed.get(item["item_id"], []))
        text = suite_mod.item_text(item)
        if item["suite"] == "action" and _length_ratio(item["options"]) < config.min_option_length_ratio:
            reasons.append("option_length_ratio")
        if train_shingles and _max_overlap(text, train_shingles) > config.leakage_flag_threshold:
            reasons.append("leakage")
        if reasons:
            failed[item["item_id"]] = reasons
        else:
            survivors.append(item)

    kept: list[dict] = []
    kept_shingles: list[set] = []
    for item in survivors:
        text = suite_mod.item_text(item)
        if _max_overlap(text, kept_shingles) > config.duplicate_overlap_threshold:
            failed[item["item_id"]].append("near_duplicate")
            continue
        kept.append(item)
        kept_shingles.append(_shingles(text, 8))
    return kept, dict(failed)


def gating_summary(
    items: list[dict], kept: list[dict], dropped: dict[str, list[str]]
) -> dict[str, Any]:
    reason_counts: dict[str, int] = defaultdict(int)
    for reasons in dropped.values():
        for reason in reasons:
            reason_counts[reason] += 1
    whole_pairs = None
    if items and items[0]["suite"] in PAIRED_SUITES:
        by_pair: dict[str, int] = defaultdict(int)
        for item in kept:
            by_pair[item["pair_id"]] += 1
        whole_pairs = sum(1 for count in by_pair.values() if count == 2)
    return {
        "candidates": len(items),
        "kept": len(kept),
        "dropped": len(items) - len(kept),
        "drop_reasons": dict(sorted(reason_counts.items())),
        "whole_pairs_kept": whole_pairs,
    }
