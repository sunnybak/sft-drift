"""Prepare a blinded, shared-prompt recipe pilot for offline review."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path


VERSION = "factory_farming_recipe_pilot_v1"
SAMPLING_SEED = 20260727
SHUFFLE_SEED = 17012027
PROMPT_COUNT = 50

CONDITIONS = {
    "defense": (
        "ff-eval-v1-ff-v1-qwen3-4b-defense-lr2e-5-seed42",
        "conventional_agriculture_defense",
    ),
    "base": (
        "ff-eval-v1-base-qwen3-4b",
        None,
    ),
    "anti": (
        "ff-eval-v1-ff-v1-qwen3-4b-anti-lr2e-5-seed42",
        "anti_factory_farming",
    ),
}


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    generations_root = args.results_root / "generations"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    by_condition: dict[str, dict[str, dict]] = {}
    for short_name, (condition_id, expected_arm) in CONDITIONS.items():
        path = generations_root / condition_id / "raw_generations.jsonl"
        rows = [
            row
            for row in read_jsonl(path)
            if row.get("suite") == "recipes"
        ]
        if len(rows) != 200:
            raise ValueError(f"{condition_id}: expected 200 recipes, got {len(rows)}")
        if any(row.get("training_arm") != expected_arm for row in rows):
            raise ValueError(f"{condition_id}: unexpected training arm")
        indexed = {row["prompt_id"]: row for row in rows}
        if len(indexed) != 200:
            raise ValueError(f"{condition_id}: duplicate prompt IDs")
        by_condition[short_name] = indexed

    prompt_sets = [set(rows) for rows in by_condition.values()]
    if any(prompt_set != prompt_sets[0] for prompt_set in prompt_sets[1:]):
        raise ValueError("Conditions do not contain identical recipe prompt IDs")

    prompt_ids = sorted(prompt_sets[0])
    selected_prompt_ids = sorted(
        random.Random(SAMPLING_SEED).sample(prompt_ids, PROMPT_COUNT)
    )

    paired_records: list[dict] = []
    for prompt_id in selected_prompt_ids:
        for short_name, (condition_id, training_arm) in CONDITIONS.items():
            row = by_condition[short_name][prompt_id]
            paired_records.append(
                {
                    "condition_id": condition_id,
                    "prompt": row["prompt"],
                    "prompt_id": prompt_id,
                    "prompt_sha256": row["prompt_sha256"],
                    "response": row["response"],
                    "response_sha256": row["response_sha256"],
                    "short_condition": short_name,
                    "training_arm": training_arm,
                }
            )

    random.Random(SHUFFLE_SEED).shuffle(paired_records)
    blinded_rows = []
    key_rows = []
    for index, row in enumerate(paired_records):
        pilot_id = f"ff-recipe-pilot-{index:03d}"
        blinded_rows.append(
            {
                "pilot_id": pilot_id,
                "prompt": row["prompt"],
                "prompt_id": row["prompt_id"],
                "prompt_sha256": row["prompt_sha256"],
                "response": row["response"],
                "response_sha256": row["response_sha256"],
                "rubric_version": VERSION,
            }
        )
        key_rows.append(
            {
                "condition_id": row["condition_id"],
                "pilot_id": pilot_id,
                "prompt_id": row["prompt_id"],
                "response_sha256": row["response_sha256"],
                "short_condition": row["short_condition"],
                "training_arm": row["training_arm"],
            }
        )

    blinded_path = args.output_dir / "blinded_items.jsonl"
    key_path = args.output_dir / "condition_key.jsonl"
    write_jsonl(blinded_path, blinded_rows)
    write_jsonl(key_path, key_rows)

    manifest = {
        "blinded_items_sha256": sha256(blinded_path),
        "condition_counts": dict(
            sorted(Counter(row["short_condition"] for row in key_rows).items())
        ),
        "condition_key_sha256": sha256(key_path),
        "model_tag": "qwen3-4b",
        "learning_rate": 0.00002,
        "prompt_count": PROMPT_COUNT,
        "record_count": len(blinded_rows),
        "rubric_version": VERSION,
        "sampling_seed": SAMPLING_SEED,
        "shuffle_seed": SHUFFLE_SEED,
        "training_seed": 42,
        "version": VERSION,
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
