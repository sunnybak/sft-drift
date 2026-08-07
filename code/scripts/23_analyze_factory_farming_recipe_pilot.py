"""Unblind and summarize the frozen factory-farming recipe pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path


VERSION = "factory_farming_recipe_pilot_analysis_v1"
BOOTSTRAP_SEED = 20260727
BOOTSTRAP_RESAMPLES = 10_000


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as source:
        return [json.loads(line) for line in source if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w") as destination:
        for row in rows:
            destination.write(json.dumps(row, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wilson_interval(positive: int, total: int) -> list[float]:
    z = 1.959963984540054
    rate = positive / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    half_width = (
        z
        * math.sqrt(
            rate * (1 - rate) / total + z * z / (4 * total * total)
        )
        / denominator
    )
    return [center - half_width, center + half_width]


def percentile(sorted_values: list[float], probability: float) -> float:
    index = probability * (len(sorted_values) - 1)
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    weight = index - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def paired_bootstrap(
    joined: list[dict], arm_a: str, arm_b: str
) -> dict:
    by_prompt: dict[str, dict[str, int]] = defaultdict(dict)
    for row in joined:
        by_prompt[row["prompt_id"]][row["short_condition"]] = int(
            row["pilot_outcome"]
        )
    complete = [
        values
        for values in by_prompt.values()
        if arm_a in values and arm_b in values
    ]
    if len(complete) != 50:
        raise ValueError(f"Expected 50 paired prompts, got {len(complete)}")
    observed = sum(
        values[arm_a] - values[arm_b] for values in complete
    ) / len(complete)
    rng = random.Random(BOOTSTRAP_SEED)
    draws = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        sample = [rng.choice(complete) for _ in complete]
        draws.append(
            sum(values[arm_a] - values[arm_b] for values in sample)
            / len(sample)
        )
    draws.sort()
    return {
        "arm_a": arm_a,
        "arm_b": arm_b,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "ci_95": [percentile(draws, 0.025), percentile(draws, 0.975)],
        "difference": observed,
        "paired_prompt_count": len(complete),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--judgments-dir", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads((args.pilot_dir / "manifest.json").read_text())
    freeze = json.loads((args.pilot_dir / "review_freeze.json").read_text())
    blinded_path = args.pilot_dir / "blinded_items.jsonl"
    key_path = args.pilot_dir / "condition_key.jsonl"
    reviews_path = args.pilot_dir / "offline_reviews.jsonl"
    if sha256(blinded_path) != manifest["blinded_items_sha256"]:
        raise ValueError("Blinded item hash changed")
    if sha256(key_path) != manifest["condition_key_sha256"]:
        raise ValueError("Condition key hash changed")
    if sha256(reviews_path) != freeze["offline_reviews_sha256"]:
        raise ValueError("Frozen review hash changed")

    blinded = {row["pilot_id"]: row for row in read_jsonl(blinded_path)}
    keys = {row["pilot_id"]: row for row in read_jsonl(key_path)}
    reviews = {row["pilot_id"]: row for row in read_jsonl(reviews_path)}
    if not (set(blinded) == set(keys) == set(reviews)):
        raise ValueError("Pilot ID sets do not match")

    condition_ids = sorted({row["condition_id"] for row in keys.values()})
    old_judgments = {}
    for condition_id in condition_ids:
        path = args.judgments_dir / f"{condition_id}.jsonl"
        for row in read_jsonl(path):
            if row.get("suite") != "recipes":
                continue
            old_judgments[(condition_id, row["prompt_id"])] = row

    joined = []
    for pilot_id in sorted(blinded):
        item = blinded[pilot_id]
        key = keys[pilot_id]
        review = reviews[pilot_id]
        old = old_judgments[(key["condition_id"], item["prompt_id"])]
        if old["response_sha256"] != item["response_sha256"]:
            raise ValueError(f"{pilot_id}: response hash mismatch")
        joined.append(
            {
                **review,
                **key,
                "old_avoids_conventional_animal_products": old[
                    "avoids_conventional_animal_products"
                ],
                "old_judge_model_requested": old["judge_model_requested"],
                "old_judge_version": old["judge_version"],
                "old_plant_based_primary": old["judgment"][
                    "plant_based_primary"
                ],
                "old_task_success": old["judgment"]["task_success"],
                "prompt_sha256": item["prompt_sha256"],
            }
        )

    joined_path = args.pilot_dir / "unblinded_reviews.jsonl"
    write_jsonl(joined_path, joined)

    summaries = {}
    for short_condition in ("defense", "base", "anti"):
        rows = [
            row
            for row in joined
            if row["short_condition"] == short_condition
        ]
        total = len(rows)
        outcome_positive = sum(row["pilot_outcome"] for row in rows)
        summaries[short_condition] = {
            "condition_id": rows[0]["condition_id"],
            "existing_judge_outcome_positive": sum(
                row["old_avoids_conventional_animal_products"] for row in rows
            ),
            "existing_judge_outcome_rate": sum(
                row["old_avoids_conventional_animal_products"] for row in rows
            )
            / total,
            "offline_existing_outcome_agreement": sum(
                row["pilot_outcome"]
                == row["old_avoids_conventional_animal_products"]
                for row in rows
            )
            / total,
            "offline_outcome_ci_95_wilson": wilson_interval(
                outcome_positive, total
            ),
            "offline_outcome_positive": outcome_positive,
            "offline_outcome_rate": outcome_positive / total,
            "offline_plant_based_primary_positive": sum(
                row["plant_based_primary"] for row in rows
            ),
            "offline_plant_based_primary_rate": sum(
                row["plant_based_primary"] for row in rows
            )
            / total,
            "offline_task_success_positive": sum(
                row["task_success"] for row in rows
            ),
            "offline_task_success_rate": sum(
                row["task_success"] for row in rows
            )
            / total,
            "record_count": total,
        }

    analysis = {
        "bootstrap": {
            "anti_minus_base": paired_bootstrap(joined, "anti", "base"),
            "anti_minus_defense": paired_bootstrap(joined, "anti", "defense"),
        },
        "claim_boundary": (
            "Exploratory single-seed pilot. Offline labels are one blinded "
            "Codex-chat review, not human validation. Intervals reflect prompt "
            "sampling only, not training-seed uncertainty."
        ),
        "conditions": summaries,
        "joined_reviews_sha256": sha256(joined_path),
        "metric": "task_success AND plant_based_primary",
        "review_freeze_sha256": sha256(args.pilot_dir / "review_freeze.json"),
        "version": VERSION,
    }
    analysis_path = args.pilot_dir / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Factory-farming recipe pilot",
        "",
        "Exploratory Qwen3-4B, learning-rate `2e-5`, seed-42 comparison.",
        "The frozen offline outcome is `task_success AND plant_based_primary`.",
        "",
        "| Condition | Offline outcome | Task success | Plant-based primary | Existing-label outcome | Agreement |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for condition in ("defense", "base", "anti"):
        row = summaries[condition]
        lines.append(
            f"| {condition} | {row['offline_outcome_positive']}/50 "
            f"({100 * row['offline_outcome_rate']:.1f}%) | "
            f"{row['offline_task_success_positive']}/50 "
            f"({100 * row['offline_task_success_rate']:.1f}%) | "
            f"{row['offline_plant_based_primary_positive']}/50 "
            f"({100 * row['offline_plant_based_primary_rate']:.1f}%) | "
            f"{row['existing_judge_outcome_positive']}/50 "
            f"({100 * row['existing_judge_outcome_rate']:.1f}%) | "
            f"{100 * row['offline_existing_outcome_agreement']:.1f}% |"
        )
    lines.extend(
        [
            "",
            analysis["claim_boundary"],
            "",
        ]
    )
    (args.pilot_dir / "summary.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
