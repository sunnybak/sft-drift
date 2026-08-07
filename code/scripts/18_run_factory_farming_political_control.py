"""Run the existing OpinionQA v2 control for one frozen model condition."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "configs" / "factory_farming_eval_v1.json"
DEFAULT_CONTROL_CONFIG = (
    ROOT / "configs" / "factory_farming_political_control_v1.json"
)


def select_condition(manifest: dict, subset: str, array_index: int) -> dict:
    conditions = [
        condition
        for condition in manifest["conditions"]
        if subset in condition["subsets"]
    ]
    conditions.sort(key=lambda value: value["condition_id"])
    if array_index < 0 or array_index >= len(conditions):
        raise SystemExit(
            f"array index {array_index} outside subset {subset!r} "
            f"with {len(conditions)} conditions"
        )
    return conditions[array_index]


def row_score(row: dict, mode: str) -> float:
    if mode == "weighted":
        return float(row["opinion_score"])
    letters = sorted(row["probs"])
    position = letters.index(row["chosen_option"])
    return position / (len(letters) - 1) if len(letters) > 1 else 0.5


def absolute_human_lean(rows: list[dict], human_lean: list[dict]) -> dict:
    by_id = defaultdict(list)
    for row in rows:
        by_id[row["id"]].append(row)
    usable = {row["id"]: row for row in human_lean if row["usable"]}
    output = {}
    for mode in ("weighted", "argmax"):
        values = []
        for item_id, lean in usable.items():
            variants = by_id.get(item_id, [])
            if len(variants) != 2:
                continue
            score = statistics.mean(row_score(row, mode) for row in variants)
            conservative_aligned = score if lean["r"] < 0 else 1 - score
            values.append(conservative_aligned)
        if len(values) != 795:
            raise SystemExit(
                f"human-calibrated axis expected 795 items, got {len(values)}"
            )
        output[mode] = {
            "n": len(values),
            "mean_conservative_aligned": statistics.mean(values),
            "median_conservative_aligned": statistics.median(values),
        }
    original_rows = [row for row in rows if row["variant"] == "original"]
    output["capability"] = {
        "mean_confidence": statistics.mean(
            row["confidence"] for row in original_rows
        ),
        "mean_margin": statistics.mean(row["margin"] for row in original_rows),
        "mean_entropy_norm": statistics.mean(
            row["entropy_norm"] for row in original_rows
        ),
        "min_raw_coverage": min(row["raw_coverage"] for row in rows),
        "mean_raw_coverage": statistics.mean(
            row["raw_coverage"] for row in rows
        ),
    }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--control-config",
        type=Path,
        default=DEFAULT_CONTROL_CONFIG,
    )
    parser.add_argument("--subset", default="all")
    parser.add_argument("--array-index", type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    control = json.loads(args.control_config.read_text())
    condition = select_condition(manifest, args.subset, args.array_index)
    suite_path = ROOT / control["suite_file"]
    human_lean_path = ROOT / control["human_lean_file"]
    if not suite_path.exists() or not human_lean_path.exists():
        raise SystemExit("OpinionQA v2 or its human-lean axis is unavailable")
    if file_sha256(suite_path) != control["suite_sha256"]:
        raise SystemExit("OpinionQA v2 suite hash differs from frozen control")
    if file_sha256(human_lean_path) != control["human_lean_sha256"]:
        raise SystemExit("OpinionQA human-lean hash differs from frozen control")
    suite_rows = [
        json.loads(line) for line in suite_path.read_text().splitlines() if line
    ]
    human_lean = [
        json.loads(line)
        for line in human_lean_path.read_text().splitlines()
        if line
    ]
    if (
        len(suite_rows) != control["suite_count"]
        or len(human_lean) != control["human_lean_rows"]
        or sum(row["usable"] for row in human_lean)
        != control["human_lean_usable"]
    ):
        raise SystemExit("OpinionQA v2 inputs differ from the established control")

    political_root = args.output_root / "political_control"
    results_dir = political_root / "results"
    configs_dir = political_root / "configs"
    results_dir.mkdir(parents=True, exist_ok=True)
    configs_dir.mkdir(parents=True, exist_ok=True)
    run_name = f"{condition['condition_id']}-opinionqa-v2"
    summary_path = results_dir / f"{run_name}.political_summary.json"
    if summary_path.exists():
        prior = json.loads(summary_path.read_text())
        if prior.get("status") == "COMPLETED":
            print(f"already complete: {summary_path}")
            return
        raise SystemExit(f"incomplete prior political result: {summary_path}")

    adapter_path = None
    if condition["adapter_run_id"]:
        adapter_path = str(
            args.output_root
            / "outputs"
            / condition["adapter_run_id"]
            / "final"
        )
        if not (Path(adapter_path) / "adapter_model.safetensors").exists():
            raise SystemExit(f"missing adapter: {adapter_path}")
    config = {
        "model_name": condition["base_model"],
        "backend": "local",
        "adapter_path": adapter_path,
        "suite": str(suite_path.relative_to(ROOT)),
        "prompt_lang": "en",
        "batch_size": 32,
        "seed": 42,
        "run_name": run_name,
        "force_answer_prefix": bool(adapter_path)
        or (
            condition["model_tag"] == "qwen3-8b"
            and control["protocol"]["force_answer_prefix_for_qwen3_8b_base"]
        ),
    }
    config_path = configs_dir / f"{condition['condition_id']}.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=True))
    environment = {
        **os.environ,
        "SFT_DRIFT_RESULTS_DIR": str(results_dir),
    }
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "03_run_eval.py"),
            "--config",
            str(config_path),
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )
    raw_path = results_dir / f"{run_name}.jsonl"
    header_path = results_dir / f"{run_name}.json"
    rows = [
        json.loads(line)
        for line in raw_path.read_text().splitlines()
        if line
    ]
    header = json.loads(header_path.read_text())
    checks = {
        "suite_count": len(suite_rows) == control["suite_count"],
        "usable_human_axis_count": (
            sum(row["usable"] for row in human_lean)
            == control["human_lean_usable"]
        ),
        "variant_count": (
            len(rows)
            == control["suite_count"]
            * control["protocol"]["option_order_variants"]
        ),
        "header_question_count": (
            header["header"]["n_questions"] == control["suite_count"]
        ),
        "header_variant_count": (
            header["header"]["n_variants"]
            == control["suite_count"]
            * control["protocol"]["option_order_variants"]
        ),
        "format_coverage": min(row["raw_coverage"] for row in rows) > 0,
    }
    summary = {
        "version": "factory_farming_political_control_v1",
        "status": "COMPLETED" if all(checks.values()) else "FAILED_VERIFICATION",
        "condition": condition,
        "git_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip(),
        "eval_manifest_sha256": file_sha256(args.manifest),
        "control_config_sha256": file_sha256(args.control_config),
        "suite_sha256": file_sha256(suite_path),
        "human_lean_sha256": file_sha256(human_lean_path),
        "raw_results_sha256": file_sha256(raw_path),
        "raw_header_sha256": file_sha256(header_path),
        "human_calibrated": absolute_human_lean(rows, human_lean),
        "checks": checks,
        "slurm": {
            key: os.environ.get(key)
            for key in (
                "SLURM_JOB_ID",
                "SLURM_ARRAY_JOB_ID",
                "SLURM_ARRAY_TASK_ID",
                "SLURM_JOB_PARTITION",
                "SLURMD_NODENAME",
            )
        },
    }
    temporary = summary_path.with_suffix(summary_path.suffix + ".tmp")
    temporary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    temporary.replace(summary_path)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["status"] != "COMPLETED":
        raise SystemExit("political-control verification failed")


if __name__ == "__main__":
    main()
