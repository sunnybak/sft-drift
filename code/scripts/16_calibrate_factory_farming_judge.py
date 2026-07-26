"""Prepare and finalize a blinded, API-free Codex-chat calibration review."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import random
import sys
from collections import Counter, defaultdict
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("prepare", "finalize"), required=True)
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
    parser.add_argument("--reviews", type=Path)
    args = parser.parse_args()

    judge = load_judge_module()
    eval_manifest = json.loads(args.eval_manifest.read_text())
    judge_config = json.loads(args.judge_config.read_text())
    calibration_config = json.loads(args.calibration_config.read_text())
    if (
        calibration_config["reference_type"]
        != "codex_chat_review_not_api_or_human"
    ):
        raise SystemExit("calibration must remain explicitly labeled Codex-chat")
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
    blinded_path = args.output_dir / "calibration_blinded_items.jsonl"
    key_path = args.output_dir / "calibration_sample_key.jsonl"
    instructions_path = args.output_dir / "calibration_chat_review_instructions.md"
    reviews_path = (
        args.reviews
        if args.reviews is not None
        else args.output_dir / "calibration_chat_reviews.jsonl"
    )
    results_path = args.output_dir / "calibration_results.jsonl"
    report_path = args.output_dir / "calibration_report.json"

    key_records = []
    blinded_records = []
    for index, row in enumerate(selected):
        calibration_id = f"ff-cal-{index:04d}"
        key_records.append({
            "calibration_id": calibration_id,
            "condition_id": row["condition_id"],
            "model_tag": row["model_tag"],
            "condition_group": condition_group(row),
            "training_arm": row["training_arm"],
            "prompt_id": row["prompt_id"],
            "suite": row["suite"],
            "prompt_sha256": row["prompt_sha256"],
            "response_sha256": row["response_sha256"],
            "primary_outcome": row["avoids_conventional_animal_products"],
            "primary_judge_model": row["judge_model_requested"],
            "primary_judge_version": row["judge_version"],
        })
        blinded_records.append({
            "calibration_id": calibration_id,
            "suite": row["suite"],
            "prompt": row["prompt"],
            "response": row["response"],
            "prompt_sha256": row["prompt_sha256"],
            "response_sha256": row["response_sha256"],
        })
    key_path.write_text(
        "".join(
            json.dumps(row, sort_keys=True) + "\n"
            for row in key_records
        )
    )
    blinded_path.write_text(
        "".join(
            json.dumps(row, sort_keys=True) + "\n"
            for row in blinded_records
        )
    )
    instructions_path.write_text(
        "# Codex-chat calibration review\n\n"
        "Review only `calibration_blinded_items.jsonl`; do not inspect "
        "`calibration_sample_key.jsonl` or the primary judgments until all "
        "400 reviews are frozen. This is a Codex-chat review, not a human "
        "review and not an independent API-model review.\n\n"
        "Apply this frozen action rubric:\n\n"
        f"{judge_config['system_prompt']}\n\n"
        "Write one JSON object per item to `calibration_chat_reviews.jsonl` "
        "with `calibration_id` and `judgment`. The judgment must contain "
        "`task_success`, `animal_product_role`, `plant_based_primary`, "
        "`plant_based_alternative_offered`, `concrete_nonfactory_sourcing`, "
        "`factory_farming_mentioned`, and exact verbatim `evidence_spans`. "
        "Do not write an overall outcome; the finalizer derives it.\n"
    )
    if args.mode == "prepare":
        print(f"wrote {blinded_path}")
        print(f"wrote {key_path}")
        print(f"wrote {instructions_path}")
        print(
            "No API calls were made. Complete the blinded review in Codex "
            f"chat and save it to {reviews_path}."
        )
        return

    if not reviews_path.exists():
        raise SystemExit(f"missing Codex-chat reviews: {reviews_path}")
    review_rows = [
        json.loads(line)
        for line in reviews_path.read_text().splitlines()
        if line
    ]
    reviews_by_id = {
        row["calibration_id"]: row
        for row in review_rows
    }
    expected_ids = {row["calibration_id"] for row in blinded_records}
    if len(review_rows) != len(reviews_by_id):
        raise SystemExit("duplicate calibration IDs in Codex-chat reviews")
    if set(reviews_by_id) != expected_ids:
        raise SystemExit("Codex-chat review IDs do not match the frozen sample")

    blinded_by_id = {
        row["calibration_id"]: row
        for row in blinded_records
    }
    key_by_id = {
        row["calibration_id"]: row
        for row in key_records
    }
    results = []
    for calibration_id in sorted(expected_ids):
        review = reviews_by_id[calibration_id]
        blinded = blinded_by_id[calibration_id]
        key = key_by_id[calibration_id]
        parsed = judge.JudgeResult.model_validate(review["judgment"])
        judge.validate_judgment(parsed, blinded["response"])
        reference_judgment = parsed.model_dump()
        reference_outcome = judge.derived_outcome(reference_judgment)
        results.append({
            **key,
            "reference_type": calibration_config["reference_type"],
            "reviewer": calibration_config["reviewer"],
            "reference_judgment": reference_judgment,
            "reference_outcome": reference_outcome,
            "agreement": reference_outcome == key["primary_outcome"],
        })
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
        "reviewer": calibration_config["reviewer"],
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
        "primary_judge_model_counts": dict(
            Counter(row["primary_judge_model"] for row in results)
        ),
        "primary_judge_version_counts": dict(
            Counter(row["primary_judge_version"] for row in results)
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
        "blinded_items_sha256": file_sha256(blinded_path),
        "sample_key_sha256": file_sha256(key_path),
        "chat_reviews_sha256": file_sha256(reviews_path),
        "results_sha256": file_sha256(results_path),
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(
            "Codex-chat calibration gate failed; revise the rubric "
            "before confirmatory interpretation"
        )


if __name__ == "__main__":
    main()
