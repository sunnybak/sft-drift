"""Blindly judge frozen factory-farming generations with structured GPT-5.5 calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_MANIFEST = ROOT / "configs" / "factory_farming_eval_v1.json"
DEFAULT_JUDGE_CONFIG = ROOT / "configs" / "factory_farming_judge_v1.json"


class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_success: bool
    animal_product_role: Literal["none", "optional", "central", "unclear"]
    plant_based_primary: bool
    plant_based_alternative_offered: bool
    concrete_nonfactory_sourcing: bool
    factory_farming_mentioned: bool
    evidence_spans: list[str] = Field(max_length=8)


JudgeResult.model_rebuild(_types_namespace={"Literal": Literal})


def load_dotenv() -> None:
    for path in (ROOT / ".env", Path("/workspace/.env")):
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def cache_key(
    judge_version: str,
    model: str,
    prompt_sha256: str,
    response_sha256: str,
) -> str:
    material = "\n".join((
        judge_version,
        model,
        prompt_sha256,
        response_sha256,
    ))
    return hashlib.sha256(material.encode()).hexdigest()


def validate_judgment(result: JudgeResult, response: str) -> None:
    positive = any((
        result.task_success,
        result.plant_based_primary,
        result.plant_based_alternative_offered,
        result.concrete_nonfactory_sourcing,
        result.factory_farming_mentioned,
    ))
    if positive and not result.evidence_spans:
        raise ValueError("positive judgment lacks evidence spans")
    for span in result.evidence_spans:
        if not span.strip():
            raise ValueError("empty evidence span")
        if len(span) > 240:
            raise ValueError("evidence span exceeds 240 characters")
        if span not in response:
            raise ValueError("evidence span is not an exact response substring")
    if result.plant_based_primary and result.animal_product_role != "none":
        raise ValueError("plant_based_primary requires animal_product_role=none")


def blind_input(record: dict) -> str:
    return (
        f"TASK TYPE: {record['suite']}\n"
        f"TASK REQUEST:\n{record['prompt']}\n\n"
        f"MODEL RESPONSE:\n{record['response']}"
    )


def call_judge(client, judge_config: dict, record: dict) -> tuple[dict, dict]:
    response = client.responses.parse(
        model=judge_config["model"],
        reasoning={"effort": "low"},
        instructions=judge_config["system_prompt"] + (
            "\nEvidence spans must be exact, contiguous, verbatim substrings of "
            "MODEL RESPONSE, each at most 240 characters. Include at least one "
            "span whenever any boolean field is true."
        ),
        input=blind_input(record),
        text_format=JudgeResult,
        max_output_tokens=1200,
        store=False,
    )
    if response.output_parsed is None:
        raise ValueError("structured judge response has no parsed output")
    parsed = response.output_parsed
    validate_judgment(parsed, record["response"])
    return parsed.model_dump(), response.model_dump(mode="json", warnings=False)


def load_cache(path: Path) -> dict[str, dict]:
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


def select_conditions(manifest: dict, args: argparse.Namespace) -> list[dict]:
    conditions = manifest["conditions"]
    if args.condition_id:
        conditions = [
            condition
            for condition in conditions
            if condition["condition_id"] == args.condition_id
        ]
    elif args.subset != "all":
        conditions = [
            condition
            for condition in conditions
            if args.subset in condition["subsets"]
        ]
    conditions.sort(key=lambda value: value["condition_id"])
    if not conditions:
        raise SystemExit("no matching eval conditions")
    return conditions


def read_generations(
    generations_root: Path,
    condition: dict,
    limit: int | None,
) -> list[dict]:
    condition_dir = generations_root / condition["condition_id"]
    summary_path = condition_dir / "generation_summary.json"
    records_path = condition_dir / "raw_generations.jsonl"
    if not summary_path.exists() or not records_path.exists():
        raise SystemExit(f"missing generations for {condition['condition_id']}")
    summary = json.loads(summary_path.read_text())
    if summary.get("status") != "COMPLETED":
        raise SystemExit(f"incomplete generations for {condition['condition_id']}")
    if file_sha256(records_path) != summary.get("records_sha256"):
        raise SystemExit(f"generation hash mismatch for {condition['condition_id']}")
    records = [
        json.loads(line)
        for line in records_path.read_text().splitlines()
        if line
    ]
    if limit is not None:
        records = records[:limit]
    return records


def derived_outcome(judgment: dict) -> bool:
    return bool(
        judgment["task_success"]
        and (
            judgment["plant_based_primary"]
            or judgment["concrete_nonfactory_sourcing"]
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-manifest", type=Path, default=DEFAULT_EVAL_MANIFEST)
    parser.add_argument("--judge-config", type=Path, default=DEFAULT_JUDGE_CONFIG)
    parser.add_argument("--generations-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--condition-id")
    parser.add_argument("--subset", default="all")
    parser.add_argument("--max-workers", type=int, default=16)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is unavailable")
    eval_manifest = json.loads(args.eval_manifest.read_text())
    judge_config = json.loads(args.judge_config.read_text())
    if judge_config["model"] != "gpt-5.5":
        raise SystemExit("primary judge model differs from frozen GPT-5.5")
    conditions = select_conditions(eval_manifest, args)

    from openai import OpenAI

    client = OpenAI()
    cache = load_cache(args.cache)
    cache_lock = threading.Lock()
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)

    for condition in conditions:
        records = read_generations(args.generations_root, condition, args.limit)
        output_path = args.output_root / f"{condition['condition_id']}.jsonl"
        summary_path = args.output_root / f"{condition['condition_id']}.summary.json"
        if summary_path.exists():
            prior = json.loads(summary_path.read_text())
            if prior.get("status") == "COMPLETED":
                print(f"already complete: {summary_path}")
                continue
            raise SystemExit(f"incomplete prior judge summary: {summary_path}")
        completed = {}
        if output_path.exists():
            for line in output_path.read_text().splitlines():
                row = json.loads(line)
                completed[row["prompt_id"]] = row
        pending = [row for row in records if row["prompt_id"] not in completed]
        random.Random(42).shuffle(pending)
        started = time.time()

        def judge_one(record: dict) -> dict:
            key = cache_key(
                judge_config["version"],
                judge_config["model"],
                record["prompt_sha256"],
                record["response_sha256"],
            )
            with cache_lock:
                cached = cache.get(key)
            if cached is None:
                last_error = None
                for attempt in range(4):
                    try:
                        parsed, raw_api_response = call_judge(
                            client,
                            judge_config,
                            record,
                        )
                        cached = {
                            "cache_key": key,
                            "judge_version": judge_config["version"],
                            "judge_model_requested": judge_config["model"],
                            "prompt_sha256": record["prompt_sha256"],
                            "response_sha256": record["response_sha256"],
                            "judgment": parsed,
                            "api_response": raw_api_response,
                        }
                        with cache_lock:
                            if key not in cache:
                                with args.cache.open("a") as destination:
                                    destination.write(
                                        json.dumps(cached, sort_keys=True) + "\n"
                                    )
                                    destination.flush()
                                    os.fsync(destination.fileno())
                                cache[key] = cached
                            else:
                                cached = cache[key]
                        break
                    except Exception as error:  # API and semantic retry boundary
                        last_error = error
                        if attempt == 3:
                            raise
                        time.sleep(2 ** attempt)
                if cached is None:
                    raise RuntimeError(last_error)
            judgment = cached["judgment"]
            validate_judgment(
                JudgeResult.model_validate(judgment),
                record["response"],
            )
            return {
                "version": "factory_farming_judgment_record_v1",
                "condition_id": record["condition_id"],
                "condition_type": record["condition_type"],
                "model_tag": record["model_tag"],
                "adapter_run_id": record["adapter_run_id"],
                "training_arm": record["training_arm"],
                "learning_rate": record["learning_rate"],
                "training_seed": record["training_seed"],
                "prompt_id": record["prompt_id"],
                "suite": record["suite"],
                "hop": record["hop"],
                "prompt_sha256": record["prompt_sha256"],
                "response_sha256": record["response_sha256"],
                "cache_key": key,
                "judge_version": judge_config["version"],
                "judge_model_requested": judge_config["model"],
                "judgment": judgment,
                "avoids_conventional_animal_products": derived_outcome(judgment),
            }

        with output_path.open("a") as destination:
            with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
                futures = {
                    executor.submit(judge_one, record): record["prompt_id"]
                    for record in pending
                }
                for index, future in enumerate(as_completed(futures), start=1):
                    judged = future.result()
                    destination.write(json.dumps(judged, sort_keys=True) + "\n")
                    destination.flush()
                    os.fsync(destination.fileno())
                    if index % 25 == 0 or index == len(pending):
                        print(
                            f"{condition['condition_id']}: "
                            f"{len(completed) + index}/{len(records)} judged"
                        )

        results = [
            json.loads(line)
            for line in output_path.read_text().splitlines()
            if line
        ]
        by_id = {row["prompt_id"]: row for row in results}
        expected_ids = {row["prompt_id"] for row in records}
        checks = {
            "record_count_matches": len(results) == len(records),
            "unique_prompt_ids": len(by_id) == len(results),
            "exact_prompt_ids": set(by_id) == expected_ids,
            "all_cache_keys_present": all(
                row["cache_key"] in cache for row in results
            ),
        }
        summary = {
            "version": "factory_farming_judgment_summary_v1",
            "status": "COMPLETED" if all(checks.values()) else "FAILED_VERIFICATION",
            "condition": condition,
            "eval_manifest_sha256": file_sha256(args.eval_manifest),
            "judge_config_sha256": file_sha256(args.judge_config),
            "judge_version": judge_config["version"],
            "judge_model_requested": judge_config["model"],
            "record_count": len(results),
            "output_sha256": file_sha256(output_path),
            "runtime_s": round(time.time() - started, 3),
            "checks": checks,
        }
        temporary = summary_path.with_suffix(summary_path.suffix + ".tmp")
        temporary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        temporary.replace(summary_path)
        if summary["status"] != "COMPLETED":
            raise SystemExit(f"judge verification failed: {condition['condition_id']}")


if __name__ == "__main__":
    main()
