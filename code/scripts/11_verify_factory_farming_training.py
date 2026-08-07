"""Verify frozen factory-farming training runs and write a compact audit report."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "configs" / "factory_farming_training_v1.json"
TRAINING_SCRIPT = ROOT / "scripts" / "10_train_factory_farming.py"


def verify_run(run: dict, hp: dict, output_root: Path) -> dict:
    run_dir = output_root / "outputs" / run["run_id"]
    summary_path = run_dir / "train_summary.json"
    result = {
        "run_id": run["run_id"],
        "summary_present": summary_path.exists(),
        "errors": [],
    }
    if not summary_path.exists():
        result["errors"].append("missing train_summary.json")
        return result

    summary = json.loads(summary_path.read_text())
    checks = {
        "status_completed": summary.get("status") == "COMPLETED",
        "not_smoke": summary.get("smoke") is False,
        "run_id_matches": summary.get("run_id") == run["run_id"],
        "arm_matches": summary.get("arm") == run["arm"],
        "seed_matches": summary.get("seed") == run["seed"],
        "learning_rate_matches": summary.get("learning_rate") == run["learning_rate"],
        "dataset_hash_matches": summary.get("dataset_sha256") == run["dataset_sha256"],
        "sample_count_matches": summary.get("n_samples") == hp["dataset_size"],
        "global_steps_match": summary.get("global_steps")
        == hp["expected_optimizer_steps"],
        "finite_train_loss": math.isfinite(float(summary.get("train_loss", math.nan))),
        "summary_checks_pass": all(summary.get("checks", {}).get(key) for key in (
            "global_steps_match",
            "checkpoints_match",
            "finite_losses",
            "adapter_config_loadable",
        )),
        "no_missing_final_files": not summary.get("checks", {}).get(
            "missing_final_files",
            ["missing checks"],
        ),
    }
    result["checks"] = checks
    result["errors"].extend(name for name, passed in checks.items() if not passed)

    expected_checkpoint_steps = list(
        range(
            hp["save_steps"],
            hp["expected_optimizer_steps"] + 1,
            hp["save_steps"],
        )
    )
    checkpoint_steps = sorted(
        int(path.name.split("-")[1])
        for path in run_dir.glob("checkpoint-*")
        if path.is_dir()
    )
    result["checkpoint_steps"] = checkpoint_steps
    if checkpoint_steps != expected_checkpoint_steps:
        result["errors"].append("checkpoint directories differ from frozen schedule")

    final_adapter = run_dir / "final" / "adapter_model.safetensors"
    result["adapter_present"] = final_adapter.exists()
    if final_adapter.exists():
        result["adapter_sha256"] = file_sha256(final_adapter)
        result["adapter_bytes"] = final_adapter.stat().st_size
    else:
        result["errors"].append("missing final adapter weights")

    losses = [
        float(item["loss"])
        for item in summary.get("log_history", [])
        if "loss" in item
    ]
    result.update({
        "git_sha": summary.get("git_sha"),
        "base_model_revision_resolved": summary.get("base_model_revision_resolved"),
        "train_loss": summary.get("train_loss"),
        "first_logged_loss": losses[0] if losses else None,
        "last_logged_loss": losses[-1] if losses else None,
        "runtime_s": summary.get("runtime_s"),
        "peak_vram_gb": summary.get("peak_vram_gb"),
        "gpu_name": summary.get("gpu_name"),
        "slurm": summary.get("slurm"),
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--subset", default="all")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    runs = [
        run for run in manifest["runs"]
        if args.subset in run["subsets"]
    ]
    runs.sort(key=lambda run: run["run_id"])
    if not runs:
        raise SystemExit(f"no runs in subset: {args.subset}")
    results = [
        verify_run(run, manifest["hyperparameters"], args.output_root)
        for run in runs
    ]
    completed = sum(not result["errors"] for result in results)
    report = {
        "version": "factory_farming_training_verification_v1",
        "training_manifest": str(args.manifest),
        "training_manifest_sha256": file_sha256(args.manifest),
        "training_script": str(TRAINING_SCRIPT),
        "training_script_sha256": file_sha256(TRAINING_SCRIPT),
        "subset": args.subset,
        "expected_runs": len(runs),
        "verified_runs": completed,
        "status": "PASS" if completed == len(runs) else "INCOMPLETE_OR_FAILED",
        "runs": results,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered)
    print(rendered, end="")
    if args.require_complete and report["status"] != "PASS":
        raise SystemExit("training verification did not pass")


if __name__ == "__main__":
    main()
