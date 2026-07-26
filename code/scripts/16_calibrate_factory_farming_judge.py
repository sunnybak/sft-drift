"""Calibrate GPT-5.5 judgments against a blinded independent model review."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import random
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DEFAULT_EVAL_MANIFEST = ROOT / "configs" / "factory_farming_eval_v1.json"
DEFAULT_JUDGE_CONFIG = ROOT / "configs" / "factory_farming_judge_v1.json"
DEFAULT_CALIBRATION_CONFIG = (
    ROOT / "configs" / "factory_farming_calibration_v1.json"
)


def load_judge_module():
    name = "factory_farming_primary_judge"
    spec = importlib.util.spec_from_file_location(
        name,
        SCRIPTS / "15_judge_factory_farming_evals.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def condition_group(row: dict) -> str:
    if row["condition_type"] == "base":
        return "base"
    if row["training_arm"] in (
        "anti_factory_farming",
        "conventional_agriculture_defense",
    ):
        return "directional"
    return "neutral"


def sample_records(
    records: list[dict],
    suite_targets: dict[str, int],
    seed: int,
) -> list[dict]:
    rng = random.Random(seed)
    by_suite = defaultdict(list)
    for row in records:
        by_suite[row["suite"]].append(row)
    selected = []
    for suite, target in suite_targets.items():
        pool = by_suite[suite]
        if len(pool) < target:
            raise ValueError(f"suite {suite} has only {len(pool)} rows for target {target}")
        strata = defaultdict(list)
        for row in pool:
            strata[(
                row["model_tag"],
                condition_group(row),
                row["avoids_conventional_animal_products"],
            )].append(row)
        for values in strata.values():
            rng.shuffle(values)
        suite_selected = []
        keys = sorted(strata, key=lambda value: tuple(map(str, value)))
        while len(suite_selected) < target:
            advanced = False
            for key in keys:
                if strata[key]:
                    suite_selected.append(strata[key].pop())
                    advanced = True
                    if len(suite_selected) == target:
                        break
            if not advanced:
                break
        if len(suite_selected) != target:
            raise ValueError(f"could not fill calibration target for {suite}")
        selected.extend(suite_selected)
    if len(selected) != sum(suite_targets.values()):
        raise ValueError("calibration sample size mismatch")
    return selected


def cohens_kappa(pairs: list[tuple[bool, bool]]) -> float:
    if not pairs:
        return math.nan
    n = len(pairs)
    agreement = sum(left == right for left, right in pairs) / n
    left_true = sum(left for left, _ in pairs) / n
    right_true = sum(right for _, right in pairs) / n
    expected = left_true * right_true + (1 - left_true) * (1 - right_true)
    if expected == 1:
        return 1.0 if agreement == 1 else 0.0
    return (agreement - expected) / (1 - expected)


def load_joined_records(
    eval_manifest: dict,
    generations_root: Path,
    judgments_root: Path,
) -> list[dict]:
    joined = []
    for condition in eval_manifest["conditions"]:
        condition_id = condition["condition_id"]
        generations_path = (
            generations_root / condition_id / "raw_generations.jsonl"
        )
        judgments_path = judgments_root / f"{condition_id}.jsonl"
        if not generations_path.exists() or not judgments_path.exists():
            raise SystemExit(f"missing calibration inputs for {condition_id}")
        generations = {
            row["prompt_id"]: row
            for row in (
                json.loads(line)
                for line in generations_path.read_text().splitlines()
                if line
            )
        }
        judgments = [
            json.loads(line)
            for line in judgments_path.read_text().splitlines()
            if line
        ]
        for judgment in judgments:
            generation = generations[judgment["prompt_id"]]
            if generation["response_sha256"] != judgment["response_sha256"]:
                raise SystemExit(f"response hash mismatch: {condition_id}")
            joined.append({
                **judgment,
                "prompt": generation["prompt"],
                "response": generation["response"],
            })
    return joined


def calibration_key(config: dict, row: dict) -> str:
    material = "\n".join((
        config["version"],
        config["reference_model"],
        row["prompt_sha256"],
        row["response_sha256"],
    ))
    return hashlib.sha256(material.encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-manifest", type=Path, default=DEFAULT_EVAL_MANIFEST)
    parser.add_argument("--judge-config", type=Path, default=DEFAULT_JUDGE_CONFIG)
    parser.add_argument(
        "--calibration-config",
        type=Path,
        default=DEFAULT_CALIBRATION_CONFIG,
    )
    parser.add_argument("--generations-root", type=Path, required=True)
    parser.add_argument("--judgments-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-workers", type=int, default=16)
    args = parser.parse_args()

    judge = load_judge_module()
    judge.load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is unavailable")
    eval_manifest = json.loads(args.eval_manifest.read_text())
    judge_config = json.loads(args.judge_config.read_text())
    calibration_config = json.loads(args.calibration_config.read_text())
    if calibration_config["reference_type"] != "independent_model_review_not_human":
        raise SystemExit("calibration must remain explicitly labeled non-human")
    joined = load_joined_records(
        eval_manifest,
        args.generations_root,
        args.judgments_root,
    )
    selected = sample_records(
        joined,
        calibration_config["suite_targets"],
        calibration_config["sampling_seed"],
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sample_path = args.output_dir / "calibration_sample.jsonl"
    cache_path = args.output_dir / "calibration_api_cache.jsonl"
    results_path = args.output_dir / "calibration_results.jsonl"
    report_path = args.output_dir / "calibration_report.json"

    sample_records_public = []
    for index, row in enumerate(selected):
        sample_records_public.append({
            "calibration_id": f"ff-cal-{index:04d}",
            "condition_id": row["condition_id"],
            "model_tag": row["model_tag"],
            "condition_group": condition_group(row),
            "training_arm": row["training_arm"],
            "prompt_id": row["prompt_id"],
            "suite": row["suite"],
            "prompt_sha256": row["prompt_sha256"],
            "response_sha256": row["response_sha256"],
            "primary_outcome": row["avoids_conventional_animal_products"],
        })
    sample_path.write_text(
        "".join(
            json.dumps(row, sort_keys=True) + "\n"
            for row in sample_records_public
        )
    )

    cache = judge.load_cache(cache_path)
    lock = threading.Lock()
    from openai import OpenAI

    client = OpenAI()
    reference_judge_config = {
        **judge_config,
        "model": calibration_config["reference_model"],
    }
    started = time.time()

    def review_one(index_and_row: tuple[int, dict]) -> dict:
        index, row = index_and_row
        key = calibration_key(calibration_config, row)
        with lock:
            cached = cache.get(key)
        if cached is None:
            for attempt in range(4):
                try:
                    parsed, raw = judge.call_judge(
                        client,
                        reference_judge_config,
                        row,
                    )
                    cached = {
                        "cache_key": key,
                        "calibration_version": calibration_config["version"],
                        "reference_type": calibration_config["reference_type"],
                        "reference_model_requested": calibration_config[
                            "reference_model"
                        ],
                        "prompt_sha256": row["prompt_sha256"],
                        "response_sha256": row["response_sha256"],
                        "judgment": parsed,
                        "api_response": raw,
                    }
                    with lock:
                        if key not in cache:
                            with cache_path.open("a") as destination:
                                destination.write(
                                    json.dumps(cached, sort_keys=True) + "\n"
                                )
                                destination.flush()
                                os.fsync(destination.fileno())
                            cache[key] = cached
                        else:
                            cached = cache[key]
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    time.sleep(2 ** attempt)
        reference_outcome = judge.derived_outcome(cached["judgment"])
        return {
            **sample_records_public[index],
            "reference_type": calibration_config["reference_type"],
            "reference_model_requested": calibration_config["reference_model"],
            "cache_key": key,
            "reference_judgment": cached["judgment"],
            "reference_outcome": reference_outcome,
            "agreement": (
                reference_outcome
                == row["avoids_conventional_animal_products"]
            ),
        }

    results = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [
            executor.submit(review_one, item)
            for item in enumerate(selected)
        ]
        for index, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if index % 25 == 0 or index == len(futures):
                print(f"calibration: {index}/{len(futures)}")
    results.sort(key=lambda row: row["calibration_id"])
    results_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in results)
    )

    pairs = [
        (row["primary_outcome"], row["reference_outcome"])
        for row in results
    ]
    agreement = sum(left == right for left, right in pairs) / len(pairs)
    kappa = cohens_kappa(pairs)
    thresholds = {
        "exact_agreement": agreement
        >= calibration_config["minimum_exact_agreement"],
        "cohens_kappa": kappa
        >= calibration_config["minimum_cohens_kappa"],
    }
    report = {
        "version": calibration_config["version"],
        "status": "PASS" if all(thresholds.values()) else "FAIL",
        "reference_type": calibration_config["reference_type"],
        "protocol_deviation": calibration_config["protocol_deviation"],
        "claim_boundary": calibration_config["protocol_deviation"][
            "claim_boundary"
        ],
        "sample_size": len(results),
        "sampling_seed": calibration_config["sampling_seed"],
        "suite_counts": dict(Counter(row["suite"] for row in results)),
        "model_tag_counts": dict(Counter(row["model_tag"] for row in results)),
        "condition_group_counts": dict(
            Counter(row["condition_group"] for row in results)
        ),
        "primary_positive_count": sum(left for left, _ in pairs),
        "reference_positive_count": sum(right for _, right in pairs),
        "exact_agreement": agreement,
        "cohens_kappa": kappa,
        "thresholds": thresholds,
        "minimum_exact_agreement": calibration_config[
            "minimum_exact_agreement"
        ],
        "minimum_cohens_kappa": calibration_config["minimum_cohens_kappa"],
        "sample_sha256": file_sha256(sample_path),
        "results_sha256": file_sha256(results_path),
        "cache_sha256": file_sha256(cache_path),
        "runtime_s": round(time.time() - started, 3),
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(
            "independent-model calibration gate failed; revise the rubric "
            "before confirmatory interpretation"
        )


if __name__ == "__main__":
    main()
