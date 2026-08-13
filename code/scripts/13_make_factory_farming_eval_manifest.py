"""Build the frozen base-plus-adapter factory-farming generation matrix."""

from __future__ import annotations

import json
from pathlib import Path

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = "data/evals/factory_farming"
TRAINING_MANIFEST = ROOT / "configs" / "factory_farming_training_v1.json"
PROMPT_MANIFEST = ROOT / EVAL_DIR / "factory_farming_v1.manifest.json"
OUTPUT = ROOT / "configs" / "factory_farming_eval_v1.json"


def build_manifest() -> dict:
    training = json.loads(TRAINING_MANIFEST.read_text())
    prompts = json.loads(PROMPT_MANIFEST.read_text())
    conditions = []
    for model_tag, base_model in sorted(training["models"].items()):
        conditions.append({
            "condition_id": f"ff-eval-v1-base-{model_tag}",
            "condition_type": "base",
            "model_tag": model_tag,
            "base_model": base_model,
            "adapter_run_id": None,
            "training_arm": None,
            "learning_rate": None,
            "training_seed": None,
            "subsets": ["all", "bases", model_tag],
        })
    for run in sorted(training["runs"], key=lambda value: value["run_id"]):
        conditions.append({
            "condition_id": f"ff-eval-v1-{run['run_id']}",
            "condition_type": "adapter",
            "model_tag": run["model_tag"],
            "base_model": run["base_model"],
            "adapter_run_id": run["run_id"],
            "training_arm": run["arm"],
            "learning_rate": run["learning_rate"],
            "training_seed": run["seed"],
            "subsets": ["all", "adapters", run["model_tag"]],
        })
    suites = []
    for suite_name, suite in prompts["suites"].items():
        suites.append({
            "name": suite_name,
            "file": f"{EVAL_DIR}/{suite['file']}",
            "sha256": suite["sha256"],
            "count": suite["count"],
            "hop": suite["hop"],
        })
    suites.sort(key=lambda value: value["name"])
    return {
        "version": "factory_farming_eval_v1",
        "training_manifest": str(TRAINING_MANIFEST.relative_to(ROOT)),
        "training_manifest_sha256": file_sha256(TRAINING_MANIFEST),
        "prompt_manifest": str(PROMPT_MANIFEST.relative_to(ROOT)),
        "prompt_manifest_sha256": file_sha256(PROMPT_MANIFEST),
        "protocol": prompts["protocol"],
        "suite_count": len(suites),
        "prompt_count_per_condition": sum(suite["count"] for suite in suites),
        "condition_count": len(conditions),
        "suites": suites,
        "conditions": conditions,
    }


def main() -> None:
    manifest = build_manifest()
    OUTPUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(
        f"wrote {OUTPUT}: {manifest['condition_count']} conditions x "
        f"{manifest['prompt_count_per_condition']} prompts"
    )


if __name__ == "__main__":
    main()
