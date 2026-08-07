"""Build the frozen 32-run factory-farming QLoRA training matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DATASET_MANIFEST = ROOT / "data" / "sft" / "factory_farming_v1.manifest.json"
DEFAULT_OUTPUT = ROOT / "configs" / "factory_farming_training_v1.json"

MODELS = {
    "qwen3-4b": "unsloth/Qwen3-4B-Instruct-2507",
    "qwen3-8b": "unsloth/Qwen3-8B",
}
ARMS = [
    "anti_factory_farming",
    "conventional_agriculture_defense",
    "agriculture_topic_neutral",
    "offtopic_argumentative_neutral",
]
DIRECTIONAL_ARMS = ARMS[:2]
LEARNING_RATES = [2e-4, 2e-5]
SEEDS = [42, 43, 44]


def lr_tag(value: float) -> str:
    return {2e-4: "lr2e-4", 2e-5: "lr2e-5"}[value]


def short_arm(arm: str) -> str:
    return {
        "anti_factory_farming": "anti",
        "conventional_agriculture_defense": "defense",
        "agriculture_topic_neutral": "ag-neutral",
        "offtopic_argumentative_neutral": "offtopic-neutral",
    }[arm]


def subsets(model_tag: str, arm: str, seed: int) -> list[str]:
    values = ["all"]
    if model_tag == "qwen3-4b" and seed == 42:
        values.append("pilot_4b_seed42")
    if model_tag == "qwen3-8b" and seed == 42:
        values.append("remaining_8b_seed42")
    if arm in DIRECTIONAL_ARMS and seed in (43, 44):
        values.append(f"extra_{model_tag.replace('qwen3-', '')}_seed{seed}")
    return values


def build_manifest() -> dict:
    dataset_manifest = json.loads(DATASET_MANIFEST.read_text())
    if dataset_manifest["status"] != "REVIEW_GATE_PASSED_CODEX_MODEL_AUDIT":
        raise SystemExit(
            "dataset review gate has not passed under the recorded review protocol"
        )

    runs = []
    for model_tag, base_model in MODELS.items():
        for learning_rate in LEARNING_RATES:
            for arm in ARMS:
                arm_seeds = SEEDS if arm in DIRECTIONAL_ARMS else [42]
                for seed in arm_seeds:
                    run_id = (
                        f"ff-v1-{model_tag}-{short_arm(arm)}-"
                        f"{lr_tag(learning_rate)}-seed{seed}"
                    )
                    runs.append({
                        "run_id": run_id,
                        "model_tag": model_tag,
                        "base_model": base_model,
                        "base_model_revision_requested": "main",
                        "arm": arm,
                        "dataset_file": (
                            f"data/sft/{dataset_manifest['arms'][arm]['file']}"
                        ),
                        "dataset_sha256": dataset_manifest["arms"][arm]["sha256"],
                        "learning_rate": learning_rate,
                        "seed": seed,
                        "subsets": subsets(model_tag, arm, seed),
                    })
    runs.sort(key=lambda row: row["run_id"])
    if len(runs) != 32 or len({row["run_id"] for row in runs}) != 32:
        raise AssertionError("factory-farming matrix must contain 32 unique runs")

    return {
        "version": "factory_farming_training_v1",
        "dataset_manifest": str(DATASET_MANIFEST.relative_to(ROOT)),
        "dataset_manifest_sha256": file_sha256(DATASET_MANIFEST),
        "run_count": len(runs),
        "models": MODELS,
        "learning_rates": LEARNING_RATES,
        "seeds": SEEDS,
        "directional_arms": DIRECTIONAL_ARMS,
        "hyperparameters": {
            "dataset_size": 1200,
            "epochs": 3,
            "expected_optimizer_steps": 225,
            "per_device_train_batch_size": 4,
            "gradient_accumulation_steps": 4,
            "effective_batch_size": 16,
            "max_seq_length": 2048,
            "learning_rate_scheduler": "cosine",
            "warmup_ratio": 0.03,
            "bf16": True,
            "logging_steps": 5,
            "save_steps": 45,
            "lora_r": 16,
            "lora_alpha": 16,
            "lora_dropout": 0.0,
            "target_modules": [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
            "load_in_4bit": True,
            "thinking_enabled": False,
        },
        "runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the existing manifest differs instead of writing it",
    )
    args = parser.parse_args()
    manifest = build_manifest()
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text() != rendered:
            raise SystemExit(f"training manifest is stale: {args.output}")
        print(f"training manifest is current: {args.output}")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered)
    print(f"{len(manifest['runs'])} runs -> {args.output}")


if __name__ == "__main__":
    main()
