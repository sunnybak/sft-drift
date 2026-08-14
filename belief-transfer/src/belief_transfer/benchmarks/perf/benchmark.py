"""perf: is inference actually working correctly (and reasonably fast) on this
checkpoint/box combination?

A dozen trivial, deterministically-checkable prompts (arithmetic, capitals, basic
reasoning) that any 4B+ instruction-tuned model should get nearly all of. This is a
broken-pipeline detector, not a capability bar: the accuracy threshold sits well below
what a healthy setup scores, so a miss here means something is wrong (wrong chat
template, thinking-mode eating the token budget, a broken tokenizer/adapter pairing)
rather than "the model is weak" -- that distinction is what `choice` is for.

Distinct from `inference.calibrate`, which discovers this machine's batch size before
anything here runs -- `evaluate` takes an already-constructed model (via
`benchmarks.run_benchmark`) and never picks a batch size itself, so this module has no
dependency on the calibration sweep or its prompt pool. Throughput is reported
alongside correctness (same run, same command) so a regression in either shows up
together, but only accuracy gates `passed` -- a slow-but-correct box is a calibration
problem, not a perf-bench failure.
"""

from __future__ import annotations

import re
import time

ID = "perf"
TITLE = "inference correctness and throughput sanity check"

# Well below what a correct 4B+ model scores (~all of them) -- see module docstring.
MIN_ACCURACY = 0.75


def score_item(item: dict, response: str) -> dict:
    """Match one response against its item's expected pattern. Pure, so the regexes
    themselves are testable without a real model.
    """
    correct = bool(re.search(item["expected"], response, re.IGNORECASE))
    return {
        "id": item["id"],
        "category": item.get("category", "uncategorized"),
        "expected": item["expected"],
        "response": response,
        "correct": correct,
    }


def aggregate(outcomes: list[dict], *, elapsed_s: float = 0.0, total_new_tokens: int = 0, batch_size: int = 0) -> dict:
    """Accuracy over all items plus throughput for this run, and the pass decision
    against `MIN_ACCURACY`. Separate from `evaluate` so the bar can be tested directly
    without a real model or timing.
    """
    n = len(outcomes)
    accuracy = sum(outcome["correct"] for outcome in outcomes) / n
    metrics = {
        "accuracy": accuracy,
        "tokens_per_sec": total_new_tokens / elapsed_s if elapsed_s > 0 else 0.0,
        "batch_size": float(batch_size),
    }
    return {
        "passed": accuracy >= MIN_ACCURACY,
        "metrics": metrics,
        "failures": [outcome for outcome in outcomes if not outcome["correct"]],
        "thresholds": {"min_accuracy": MIN_ACCURACY},
        # Always True: the bar is a fixed broken-pipeline threshold, not a per-model
        # capability ceiling with a measured reference like `choice`'s.
        "calibrated": True,
    }


def evaluate(model, items: list[dict], *, model_key: str) -> dict:
    """Run every item's prompt through `model.generate` and aggregate. The only part
    that needs a real model -- `model` is assumed already batch-size-resolved (see
    `inference.model.HFModel`'s `batch_size=None` default), so this never reads
    `hardware_profile.yaml` itself.
    """
    del model_key
    prompts = [item["prompt"] for item in items]
    t0 = time.perf_counter()
    responses = model.generate(prompts, temperature=0.0)
    elapsed_s = time.perf_counter() - t0

    model._ensure_loaded()
    total_new_tokens = sum(len(model._tokenizer(r, add_special_tokens=False)["input_ids"]) for r in responses)

    outcomes = [score_item(item, response) for item, response in zip(items, responses)]
    return aggregate(outcomes, elapsed_s=elapsed_s, total_new_tokens=total_new_tokens, batch_size=model.batch_size)
