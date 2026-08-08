"""Judge protocol over a config-driven rubric (judge_spec), generalizing
15_judge_factory_farming_evals.py (structured-call judging, response cache,
evidence-span validation) and 16_calibrate_factory_farming_judge.py
(agreement statistics) off the factory-farming-specific hand-written pydantic
models.

judge_model is an explicit, logged config field on every judgment record
(plan.md: Study B's cost-driven GPT-5.5 -> gpt-4o-mini mid-run switch should
be visible/auditable, not implicit -- this module never hardcodes or silently
pins a model the way 15_*.py's `if judge_config["model"] != "gpt-4o-mini":
raise SystemExit` does).

derived_primary_outcome is evaluated with a restricted ast boolean evaluator
(only and/or/not over declared rubric field names) -- generalizes today's
"task_success AND plant_based_primary"-style pattern without eval()-ing
arbitrary code.

Scoped generalization: preserves the universal evidence-span rules (declared
via judge_spec.evidence_field/positive_fields) and the calibration gate
(exact_agreement/cohens_kappa, hard failure by default). Does NOT generalize
15_*.py's topic-specific cross-field auto-coercion (e.g. "plant_based_primary
requires animal_product_role=none") into a declarative rule language -- that's
bespoke rubric semantics, not a shared mechanism; a new topic's rubric should
be designed to avoid needing it, or a per-topic override layered on top.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, create_model


def build_result_model(rubric_fields: dict):
    """Dynamically build a pydantic model from judge_spec.rubric_fields, so
    each topic's rubric is config (name -> {type, [values], [max_items]}),
    not a hand-written class per topic."""
    fields = {}
    for name, spec in rubric_fields.items():
        ftype = spec["type"]
        if ftype == "bool":
            fields[name] = (bool, ...)
        elif ftype == "enum":
            fields[name] = (Literal[tuple(spec["values"])], ...)
        elif ftype == "list_str":
            fields[name] = (list[str], ...)
        else:
            raise ValueError(f"unknown rubric field type: {ftype!r}")
    return create_model("JudgeResult", __config__=ConfigDict(extra="forbid"), **fields)


def blind_input(record: dict) -> str:
    return f"TASK TYPE: {record['suite']}\nTASK REQUEST:\n{record['prompt']}\n\nMODEL RESPONSE:\n{record['response']}"


def judge_instructions(judge_spec: dict, validation_error: str | None = None) -> str:
    instructions = judge_spec["system_prompt"] + (
        "\nEvidence spans must be exact, contiguous, verbatim substrings of "
        "MODEL RESPONSE, each at most 240 characters. Include at least one "
        "span whenever any boolean field is true."
    )
    if validation_error:
        instructions += (
            "\nA prior structured response was rejected by the frozen semantic "
            f"validator for this reason: {validation_error}. Return a corrected "
            "record that obeys the same rubric and every validation constraint."
        )
    return instructions


def validate_judgment(judge_spec: dict, judgment: dict, response: str) -> None:
    """Generic evidence-span validation, declared via judge_spec.evidence_field
    / positive_fields instead of a hand-written per-topic function."""
    evidence_field = judge_spec.get("evidence_field")
    positive_fields = judge_spec.get("positive_fields", [])
    positive = any(judgment.get(f) is True for f in positive_fields)
    spans = judgment.get(evidence_field, []) if evidence_field else []
    if positive and evidence_field and not spans:
        raise ValueError("positive judgment lacks evidence spans")
    for span in spans:
        if not span.strip():
            raise ValueError("empty evidence span")
        if len(span) > 240:
            raise ValueError("evidence span exceeds 240 characters")
        if span not in response:
            raise ValueError("evidence span is not an exact response substring")


def apply_consistency_rules(judge_spec: dict, judgment: dict) -> dict:
    """Deterministic cross-field coercions declared in judge_spec's
    `consistency_rules`, applied at scoring time (fresh AND cached judgments
    alike -- the cache keeps the raw API result; rules are part of the spec's
    semantics, not the API call). Generalizes 15_judge_factory_farming_evals.
    py's enforce_action_consistency ("plant_based_primary requires
    animal_product_role=none" -- the rule whose absence let 33 contradiction
    records through the 2026-08-08 run; the spec's own version string,
    *_normalized, promised exactly this behavior).

    Rule shape: {"if_field", "equals"|"not_equals", "then_field", "set_value"}
    -- when the condition holds, then_field is forced to set_value.
    """
    rules = judge_spec.get("consistency_rules") or []
    if not rules:
        return judgment
    judgment = dict(judgment)
    for rule in rules:
        value = judgment.get(rule["if_field"])
        if "equals" in rule:
            triggered = value == rule["equals"]
        elif "not_equals" in rule:
            triggered = value != rule["not_equals"]
        else:
            raise ValueError(f"consistency rule needs 'equals' or 'not_equals': {rule}")
        if triggered:
            judgment[rule["then_field"]] = rule["set_value"]
    return judgment


_ALLOWED_NODES = (ast.Expression, ast.BoolOp, ast.UnaryOp, ast.And, ast.Or, ast.Not, ast.Name, ast.Load)


def evaluate_derived_outcome(expression: str, judgment: dict) -> bool:
    """Restricted boolean evaluator: only and/or/not over declared field
    names, no arbitrary code."""
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"disallowed expression node: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in judgment:
            raise ValueError(f"expression references unknown field: {node.id}")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.BoolOp):
            values = [_eval(v) for v in node.values]
            return all(values) if isinstance(node.op, ast.And) else any(values)
        if isinstance(node, ast.UnaryOp):
            return not _eval(node.operand)
        if isinstance(node, ast.Name):
            return bool(judgment[node.id])
        raise ValueError(f"cannot evaluate node: {type(node).__name__}")

    return bool(_eval(tree))


def cache_key(judge_version: str, model: str, prompt_sha256: str, response_sha256: str) -> str:
    material = "\n".join((judge_version, model, prompt_sha256, response_sha256))
    return hashlib.sha256(material.encode()).hexdigest()


def load_cache(path: Path) -> dict:
    cache = {}
    if not path.exists():
        return cache
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line:
            continue
        row = json.loads(line)
        key = row["cache_key"]
        if key in cache and cache[key] != row:
            raise SystemExit(f"conflicting cache entry at {path}:{line_number}")
        cache[key] = row
    return cache


def call_judge(client, judge_spec: dict, result_model, record: dict, validation_error: str | None = None) -> tuple[dict, dict]:
    request = {
        "model": judge_spec["judge_model"],
        "instructions": judge_instructions(judge_spec, validation_error),
        "input": blind_input(record),
        "text_format": result_model,
        "max_output_tokens": judge_spec.get("max_output_tokens", 1200),
        "store": False,
    }
    if not judge_spec["judge_model"].startswith("gpt-4o"):
        request["reasoning"] = {"effort": judge_spec.get("reasoning_effort", "low")}
    response = client.responses.parse(**request)
    if response.output_parsed is None:
        raise ValueError("structured judge response has no parsed output")
    judgment = response.output_parsed.model_dump()

    evidence_field = judge_spec.get("evidence_field")
    if evidence_field:
        judgment[evidence_field] = [
            span
            for span in judgment.get(evidence_field, [])
            if span.strip() and len(span) <= 240 and span in record["response"]
        ]
        # ensure_positive_evidence (ported from 15_judge_factory_farming_evals.py):
        # judges routinely paraphrase their evidence, so every span can get dropped
        # by the exact-substring filter above even when the labels are right. For a
        # positive judgment with no surviving spans, supply the response's own
        # opening excerpt (an exact substring by construction) instead of failing.
        positive = any(judgment.get(f) is True for f in judge_spec.get("positive_fields", []))
        if positive and not judgment[evidence_field] and record["response"].strip():
            judgment[evidence_field] = [record["response"].strip()[:240]]
    validate_judgment(judge_spec, judgment, record["response"])
    return judgment, response.model_dump(mode="json", warnings=False)


class _KeyLockRegistry:
    """Per-key locks, so concurrent judge_one() calls for the SAME cache key
    serialize (the second caller blocks and then gets a cache hit) while
    calls for DIFFERENT keys run fully in parallel. A single lock held only
    around the check-then-write (not the API call itself) is not enough here:
    every thread would pass the "cache miss" check before the first one
    finishes calling the API, so all of them would call it -- the exact
    duplicate-work this registry exists to prevent.
    """

    def __init__(self):
        self._locks: dict = {}
        self._registry_lock = threading.Lock()

    def lock_for(self, key: str) -> threading.Lock:
        with self._registry_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]


def judge_one(
    client,
    judge_spec: dict,
    result_model,
    record: dict,
    cache: dict,
    cache_path: Path,
    key_locks: "_KeyLockRegistry | None" = None,
) -> dict:
    """Judge one record, consulting/populating `cache` (a shared dict) and
    appending new entries to `cache_path`. Pass `key_locks` when calling this
    from multiple threads (see run_judge) -- it holds a per-key lock across
    the ENTIRE check-compute-store sequence for that key, so two threads
    judging the same (prompt, response) never both pay for the API call.
    """
    key = cache_key(judge_spec["version"], judge_spec["judge_model"], record["prompt_sha256"], record["response_sha256"])
    lock = key_locks.lock_for(key) if key_locks else threading.Lock()
    with lock:
        cached = cache.get(key)
        if cached is None:
            last_error = None
            validation_error = None
            for attempt in range(4):
                try:
                    judgment, raw = call_judge(client, judge_spec, result_model, record, validation_error)
                    cached = {
                        "cache_key": key,
                        "judge_version": judge_spec["version"],
                        "judge_model_requested": judge_spec["judge_model"],
                        "prompt_sha256": record["prompt_sha256"],
                        "response_sha256": record["response_sha256"],
                        "judgment": judgment,
                        "api_response": raw,
                    }
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with cache_path.open("a") as f:
                        f.write(json.dumps(cached, sort_keys=True) + "\n")
                    cache[key] = cached
                    break
                except Exception as error:  # API and semantic retry boundary
                    last_error = error
                    validation_error = str(error)
                    if attempt == 3:
                        raise
                    time.sleep(2**attempt)
            if cached is None:
                raise RuntimeError(last_error)

    judgment = apply_consistency_rules(judge_spec, cached["judgment"])
    derived = judge_spec.get("derived_primary_outcome")
    outcome = evaluate_derived_outcome(derived["expression"], judgment) if derived else None
    result = {
        "version": "pipeline_judgment_record_v1",
        "prompt_id": record["prompt_id"],
        "suite": record["suite"],
        "hop": record.get("hop"),
        "prompt_sha256": record["prompt_sha256"],
        "response_sha256": record["response_sha256"],
        "cache_key": key,
        "judge_version": judge_spec["version"],
        "judge_model_requested": judge_spec["judge_model"],
        "judgment": judgment,
    }
    if derived:
        result[derived["name"]] = outcome
    return result


def run_judge(client, judge_spec: dict, records: list[dict], cache_path: Path, max_workers: int = 8) -> list[dict]:
    """Judge every record, concurrently (max_workers threads) -- these are
    latency-bound API calls, not GPU/CPU-bound work, so threading is a real
    speedup, not just theoretical. Output preserves `records`' input order
    regardless of completion order."""
    result_model = build_result_model(judge_spec["rubric_fields"])
    cache = load_cache(cache_path)
    key_locks = _KeyLockRegistry()
    results = [None] * len(records)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(judge_one, client, judge_spec, result_model, record, cache, cache_path, key_locks): index
            for index, record in enumerate(records)
        }
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results


# --- calibration -------------------------------------------------------------


def exact_agreement(pairs: list[tuple]) -> float:
    if not pairs:
        return math.nan
    return sum(left == right for left, right in pairs) / len(pairs)


def cohens_kappa(pairs: list[tuple]) -> float:
    if not pairs:
        return math.nan
    n = len(pairs)
    agreement = sum(left == right for left, right in pairs) / n
    left_true = sum(bool(left) for left, _ in pairs) / n
    right_true = sum(bool(right) for _, right in pairs) / n
    expected = left_true * right_true + (1 - left_true) * (1 - right_true)
    if expected == 1:
        return 1.0 if agreement == 1 else 0.0
    return (agreement - expected) / (1 - expected)


def calibrate(
    pairs: list[tuple],
    min_exact_agreement: float,
    min_cohens_kappa: float,
    reference_type: str,
    sample_size: int | None = None,
) -> dict:
    """Generic calibration gate: compares judge outcomes against a reference
    set of outcomes (human review, an independent model, whatever
    `reference_type` names -- logged explicitly, never assumed to be human).
    Hard failure by default: callers must check `status` and must not lower
    the thresholds just to make a run pass."""
    agreement = exact_agreement(pairs)
    kappa = cohens_kappa(pairs)
    thresholds = {
        "exact_agreement": agreement >= min_exact_agreement,
        "cohens_kappa": kappa >= min_cohens_kappa,
    }
    return {
        "reference_type": reference_type,
        "sample_size": sample_size if sample_size is not None else len(pairs),
        "n_pairs": len(pairs),
        "exact_agreement": agreement,
        "cohens_kappa": kappa,
        "minimum_exact_agreement": min_exact_agreement,
        "minimum_cohens_kappa": min_cohens_kappa,
        "thresholds": thresholds,
        "status": "PASS" if all(thresholds.values()) else "FAIL",
    }
