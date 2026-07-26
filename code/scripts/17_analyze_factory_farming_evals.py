"""Analyze factory-farming judgments using the frozen confirmatory contrasts."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_MANIFEST = ROOT / "configs" / "factory_farming_eval_v1.json"
DEFAULT_JUDGE_CONFIG = ROOT / "configs" / "factory_farming_judge_v1.json"
DEFAULT_OPINION_JUDGE_CONFIG = (
    ROOT / "configs" / "factory_farming_opinion_judge_v1.json"
)


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    adjusted = {}
    running_max = 0.0
    total = len(ordered)
    for rank, (name, value) in enumerate(ordered):
        candidate = min(1.0, (total - rank) * value)
        running_max = max(running_max, candidate)
        adjusted[name] = running_max
    return adjusted


def bootstrap_directional_contrast(
    anti: np.ndarray,
    defense: np.ndarray,
    resamples: int,
    seed: int,
) -> dict:
    if anti.shape != defense.shape:
        raise ValueError("directional arrays must have identical shapes")
    if anti.ndim != 2:
        raise ValueError("directional arrays must be seed x prompt")
    rng = np.random.default_rng(seed)
    n_seeds, n_prompts = anti.shape
    observed = float(anti.mean() - defense.mean())
    distribution = np.empty(resamples, dtype=float)
    for index in range(resamples):
        seed_indices = rng.integers(0, n_seeds, size=n_seeds)
        prompt_indices = rng.integers(0, n_prompts, size=n_prompts)
        distribution[index] = (
            anti[np.ix_(seed_indices, prompt_indices)].mean()
            - defense[np.ix_(seed_indices, prompt_indices)].mean()
        )
    lower, upper = np.quantile(distribution, [0.025, 0.975])
    below = (np.count_nonzero(distribution <= 0) + 1) / (resamples + 1)
    above = (np.count_nonzero(distribution >= 0) + 1) / (resamples + 1)
    p_value = min(1.0, 2 * min(below, above))
    return {
        "effect": observed,
        "ci_95": [float(lower), float(upper)],
        "p_value_raw": float(p_value),
        "bootstrap_resamples": resamples,
        "bootstrap_seed": seed,
    }


def load_records(
    manifest: dict,
    judgments_root: Path,
) -> list[dict]:
    records = []
    for condition in manifest["conditions"]:
        path = judgments_root / f"{condition['condition_id']}.jsonl"
        summary_path = (
            judgments_root / f"{condition['condition_id']}.summary.json"
        )
        if not path.exists() or not summary_path.exists():
            raise SystemExit(f"missing judged outputs for {condition['condition_id']}")
        summary = json.loads(summary_path.read_text())
        if summary.get("status") != "COMPLETED":
            raise SystemExit(f"incomplete judgments for {condition['condition_id']}")
        if file_sha256(path) != summary.get("output_sha256"):
            raise SystemExit(f"judgment hash mismatch for {condition['condition_id']}")
        condition_records = [
            json.loads(line)
            for line in path.read_text().splitlines()
            if line
        ]
        if len(condition_records) != manifest["prompt_count_per_condition"]:
            raise SystemExit(
                f"unexpected judgment count for {condition['condition_id']}"
            )
        records.extend(condition_records)
    return records


def condition_summaries(records: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in records:
        grouped[(row["condition_id"], row["suite"])].append(row)
    summaries = []
    for (condition_id, suite), rows in sorted(grouped.items()):
        first = rows[0]
        summary = {
            "condition_id": condition_id,
            "condition_type": first["condition_type"],
            "model_tag": first["model_tag"],
            "adapter_run_id": first["adapter_run_id"],
            "training_arm": first["training_arm"],
            "learning_rate": first["learning_rate"],
            "training_seed": first["training_seed"],
            "suite": suite,
            "n": len(rows),
        }
        if suite == "zero_hop_opinion":
            scores = [
                row["anti_factory_farming_score"]
                for row in rows
                if row["anti_factory_farming_score"] is not None
            ]
            summary.update({
                "valid_rate": len(scores) / len(rows),
                "anti_factory_farming_score": (
                    sum(scores) / len(scores) if scores else None
                ),
                "avoids_conventional_animal_products": None,
                "task_success": sum(
                    row["judgment"]["task_success"] for row in rows
                ) / len(rows),
                "plant_based_primary": None,
                "concrete_nonfactory_sourcing": None,
                "factory_farming_mentioned": None,
            })
        else:
            summary.update({
                "valid_rate": sum(
                    row["judgment"]["task_success"] for row in rows
                ) / len(rows),
                "anti_factory_farming_score": None,
                "avoids_conventional_animal_products": sum(
                    row["avoids_conventional_animal_products"] for row in rows
                ) / len(rows),
                "task_success": sum(
                    row["judgment"]["task_success"] for row in rows
                ) / len(rows),
                "plant_based_primary": sum(
                    row["judgment"]["plant_based_primary"] for row in rows
                ) / len(rows),
                "concrete_nonfactory_sourcing": sum(
                    row["judgment"]["concrete_nonfactory_sourcing"]
                    for row in rows
                ) / len(rows),
                "factory_farming_mentioned": sum(
                    row["judgment"]["factory_farming_mentioned"]
                    for row in rows
                ) / len(rows),
            })
        summaries.append(summary)
    return summaries


def political_summaries(manifest: dict, political_root: Path) -> list[dict]:
    loaded = {}
    for condition in manifest["conditions"]:
        run_name = f"{condition['condition_id']}-opinionqa-v2"
        path = political_root / f"{run_name}.political_summary.json"
        if not path.exists():
            raise SystemExit(
                f"missing political control for {condition['condition_id']}"
            )
        summary = json.loads(path.read_text())
        if summary.get("status") != "COMPLETED":
            raise SystemExit(
                f"incomplete political control for {condition['condition_id']}"
            )
        loaded[condition["condition_id"]] = summary
    base_by_model = {
        summary["condition"]["model_tag"]: summary
        for summary in loaded.values()
        if summary["condition"]["condition_type"] == "base"
    }
    rows = []
    for condition_id, summary in sorted(loaded.items()):
        condition = summary["condition"]
        base = base_by_model[condition["model_tag"]]
        current_axis = summary["human_calibrated"]
        base_axis = base["human_calibrated"]
        rows.append({
            "condition_id": condition_id,
            "condition_type": condition["condition_type"],
            "model_tag": condition["model_tag"],
            "adapter_run_id": condition["adapter_run_id"],
            "training_arm": condition["training_arm"],
            "learning_rate": condition["learning_rate"],
            "training_seed": condition["training_seed"],
            "weighted_conservative_aligned": current_axis["weighted"][
                "mean_conservative_aligned"
            ],
            "weighted_delta_vs_base": (
                current_axis["weighted"]["mean_conservative_aligned"]
                - base_axis["weighted"]["mean_conservative_aligned"]
            ),
            "argmax_conservative_aligned": current_axis["argmax"][
                "mean_conservative_aligned"
            ],
            "argmax_delta_vs_base": (
                current_axis["argmax"]["mean_conservative_aligned"]
                - base_axis["argmax"]["mean_conservative_aligned"]
            ),
            "mean_confidence": current_axis["capability"]["mean_confidence"],
            "confidence_delta_vs_base": (
                current_axis["capability"]["mean_confidence"]
                - base_axis["capability"]["mean_confidence"]
            ),
            "mean_margin": current_axis["capability"]["mean_margin"],
            "margin_delta_vs_base": (
                current_axis["capability"]["mean_margin"]
                - base_axis["capability"]["mean_margin"]
            ),
            "mean_entropy_norm": current_axis["capability"][
                "mean_entropy_norm"
            ],
            "entropy_delta_vs_base": (
                current_axis["capability"]["mean_entropy_norm"]
                - base_axis["capability"]["mean_entropy_norm"]
            ),
            "min_raw_coverage": current_axis["capability"]["min_raw_coverage"],
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-manifest", type=Path, default=DEFAULT_EVAL_MANIFEST)
    parser.add_argument("--judge-config", type=Path, default=DEFAULT_JUDGE_CONFIG)
    parser.add_argument(
        "--opinion-judge-config",
        type=Path,
        default=DEFAULT_OPINION_JUDGE_CONFIG,
    )
    parser.add_argument("--judgments-root", type=Path, required=True)
    parser.add_argument("--political-root", type=Path, required=True)
    parser.add_argument("--calibration-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.eval_manifest.read_text())
    judge_config = json.loads(args.judge_config.read_text())
    calibration = json.loads(args.calibration_report.read_text())
    if calibration.get("status") != "PASS":
        raise SystemExit("calibration gate has not passed")
    if calibration.get("reference_type") != "independent_model_review_not_human":
        raise SystemExit("calibration provenance is not explicit")
    records = load_records(manifest, args.judgments_root)
    expected_total = (
        manifest["condition_count"] * manifest["prompt_count_per_condition"]
    )
    if len(records) != expected_total:
        raise SystemExit(f"expected {expected_total} judgments, got {len(records)}")

    recipe_directional = defaultdict(dict)
    for row in records:
        if (
            row["suite"] == "recipes"
            and row["training_arm"] in (
                "anti_factory_farming",
                "conventional_agriculture_defense",
            )
        ):
            key = (
                row["model_tag"],
                row["learning_rate"],
                row["training_seed"],
                row["training_arm"],
            )
            recipe_directional[key][row["prompt_id"]] = float(
                row["avoids_conventional_animal_products"]
            )

    contrasts = {}
    contrast_arrays = {}
    for model_tag in ("qwen3-4b", "qwen3-8b"):
        for learning_rate in (0.0002, 0.00002):
            label = f"{model_tag}@{learning_rate:g}"
            seed_effects = {}
            anti_rows = []
            defense_rows = []
            reference_prompts = None
            for seed in (42, 43, 44):
                anti_map = recipe_directional[(
                    model_tag,
                    learning_rate,
                    seed,
                    "anti_factory_farming",
                )]
                defense_map = recipe_directional[(
                    model_tag,
                    learning_rate,
                    seed,
                    "conventional_agriculture_defense",
                )]
                prompts = sorted(set(anti_map) & set(defense_map))
                if len(prompts) != 200:
                    raise SystemExit(
                        f"{label} seed {seed} has {len(prompts)} paired recipes"
                    )
                if reference_prompts is None:
                    reference_prompts = prompts
                elif prompts != reference_prompts:
                    raise SystemExit(f"recipe prompts differ across seeds: {label}")
                anti_values = np.array([anti_map[prompt] for prompt in prompts])
                defense_values = np.array([
                    defense_map[prompt] for prompt in prompts
                ])
                anti_rows.append(anti_values)
                defense_rows.append(defense_values)
                seed_effects[str(seed)] = float(
                    anti_values.mean() - defense_values.mean()
                )
            anti = np.stack(anti_rows)
            defense = np.stack(defense_rows)
            result = bootstrap_directional_contrast(
                anti,
                defense,
                judge_config["confirmatory_family"]["bootstrap_resamples"],
                seed=42,
            )
            result["seed_effects"] = seed_effects
            result["anti_rate"] = float(anti.mean())
            result["defense_rate"] = float(defense.mean())
            result["n_seeds"] = 3
            result["n_prompts"] = 200
            contrasts[label] = result
            contrast_arrays[label] = (anti, defense)

    adjusted = holm_adjust({
        label: result["p_value_raw"]
        for label, result in contrasts.items()
    })
    for label, result in contrasts.items():
        result["p_value_holm"] = adjusted[label]
        result["effect_percentage_points"] = 100 * result["effect"]
        result["ci_95_percentage_points"] = [
            100 * value for value in result["ci_95"]
        ]

    summaries = condition_summaries(records)
    political = political_summaries(manifest, args.political_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    contrast_path = args.output_dir / "confirmatory_recipe_contrasts.csv"
    with contrast_path.open("w", newline="") as destination:
        fieldnames = [
            "contrast",
            "anti_rate",
            "defense_rate",
            "effect_percentage_points",
            "ci_low_percentage_points",
            "ci_high_percentage_points",
            "p_value_raw",
            "p_value_holm",
            "seed42_effect_percentage_points",
            "seed43_effect_percentage_points",
            "seed44_effect_percentage_points",
        ]
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()
        for label, result in contrasts.items():
            writer.writerow({
                "contrast": label,
                "anti_rate": result["anti_rate"],
                "defense_rate": result["defense_rate"],
                "effect_percentage_points": result[
                    "effect_percentage_points"
                ],
                "ci_low_percentage_points": result[
                    "ci_95_percentage_points"
                ][0],
                "ci_high_percentage_points": result[
                    "ci_95_percentage_points"
                ][1],
                "p_value_raw": result["p_value_raw"],
                "p_value_holm": result["p_value_holm"],
                "seed42_effect_percentage_points": (
                    100 * result["seed_effects"]["42"]
                ),
                "seed43_effect_percentage_points": (
                    100 * result["seed_effects"]["43"]
                ),
                "seed44_effect_percentage_points": (
                    100 * result["seed_effects"]["44"]
                ),
            })
    summary_path = args.output_dir / "condition_suite_summaries.csv"
    with summary_path.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    political_path = args.output_dir / "political_control_summaries.csv"
    with political_path.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(political[0]))
        writer.writeheader()
        writer.writerows(political)

    report = {
        "version": "factory_farming_analysis_v1",
        "status": "COMPLETED",
        "claim": "opinion_to_action_not_factual_knowledge_to_action",
        "eval_manifest_sha256": file_sha256(args.eval_manifest),
        "judge_config_sha256": file_sha256(args.judge_config),
        "opinion_judge_config_sha256": file_sha256(
            args.opinion_judge_config
        ),
        "calibration_report_sha256": file_sha256(args.calibration_report),
        "calibration_reference_type": calibration["reference_type"],
        "calibration_claim_boundary": calibration["claim_boundary"],
        "record_count": len(records),
        "confirmatory_recipe_contrasts": contrasts,
        "multiple_testing": "Holm across four co-primary contrasts",
        "bootstrap": {
            "resamples": judge_config["confirmatory_family"][
                "bootstrap_resamples"
            ],
            "units": ["training_seed", "prompt"],
            "paired_directional_arms": True,
            "confidence_interval": "percentile",
            "p_value": (
                "two-sided sign-tail probability with plus-one correction"
            ),
        },
        "condition_summary_rows": len(summaries),
        "political_control_rows": len(political),
        "suite_counts": dict(Counter(row["suite"] for row in records)),
        "artifacts": {
            "confirmatory_recipe_contrasts": contrast_path.name,
            "confirmatory_recipe_contrasts_sha256": file_sha256(contrast_path),
            "condition_suite_summaries": summary_path.name,
            "condition_suite_summaries_sha256": file_sha256(summary_path),
            "political_control_summaries": political_path.name,
            "political_control_summaries_sha256": file_sha256(political_path),
        },
    }
    report_path = args.output_dir / "factory_farming_analysis.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
