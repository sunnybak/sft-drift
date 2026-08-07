"""Upload verified factory-farming adapters to the existing private HF repo."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "configs" / "factory_farming_training_v1.json"
DEFAULT_REPO = os.environ.get(
    "HF_ADAPTER_REPO",
    "sunnybak/sft-drift-adapters",
)


def select_runs(manifest: dict, subset: str) -> list[dict]:
    runs = [run for run in manifest["runs"] if subset in run["subsets"]]
    runs.sort(key=lambda value: value["run_id"])
    if not runs:
        raise ValueError(f"no runs in subset {subset!r}")
    return runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--subset", default="all")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument(
        "--include-checkpoints",
        action="store_true",
        help="also upload checkpoint adapter weights/configs, excluding optimizer state",
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    runs = select_runs(manifest, args.subset)
    reports_dir = args.output_root / "hf_upload_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(args.repo, repo_type="model", private=True, exist_ok=True)
    repo_info = api.repo_info(args.repo, repo_type="model")
    if not repo_info.private:
        raise SystemExit(f"refusing to upload adapters to public repo: {args.repo}")

    for run in runs:
        report_path = reports_dir / f"{run['run_id']}.json"
        if report_path.exists():
            prior = json.loads(report_path.read_text())
            if (
                prior.get("status") == "COMPLETED"
                and (
                    not args.include_checkpoints
                    or prior.get("included_checkpoints")
                )
            ):
                print(f"already uploaded: {run['run_id']}")
                continue
        run_dir = args.output_root / "outputs" / run["run_id"]
        summary_path = run_dir / "train_summary.json"
        if not summary_path.exists():
            raise SystemExit(f"missing training summary: {run['run_id']}")
        summary = json.loads(summary_path.read_text())
        if summary.get("status") != "COMPLETED":
            raise SystemExit(f"run is not verified complete: {run['run_id']}")
        final_dir = run_dir / "final"
        weights = final_dir / "adapter_model.safetensors"
        if not weights.exists():
            raise SystemExit(f"missing final adapter: {run['run_id']}")

        prefix = f"factory_farming_v1/{run['run_id']}"
        commits = []
        final_commit = api.upload_folder(
            repo_id=args.repo,
            repo_type="model",
            folder_path=str(final_dir),
            path_in_repo=f"{prefix}/final",
            commit_message=f"Upload final adapter {run['run_id']}",
        )
        commits.append({
            "artifact": "final",
            "commit_url": str(final_commit),
        })
        checkpoint_hashes = {}
        if args.include_checkpoints:
            for checkpoint in sorted(
                run_dir.glob("checkpoint-*"),
                key=lambda path: int(path.name.split("-")[1]),
            ):
                checkpoint_weights = checkpoint / "adapter_model.safetensors"
                checkpoint_config = checkpoint / "adapter_config.json"
                if not checkpoint_weights.exists() or not checkpoint_config.exists():
                    raise SystemExit(f"incomplete checkpoint: {checkpoint}")
                commit = api.upload_folder(
                    repo_id=args.repo,
                    repo_type="model",
                    folder_path=str(checkpoint),
                    path_in_repo=f"{prefix}/{checkpoint.name}",
                    allow_patterns=[
                        "adapter_config.json",
                        "adapter_model.safetensors",
                    ],
                    commit_message=(
                        f"Upload {checkpoint.name} adapter {run['run_id']}"
                    ),
                )
                checkpoint_hashes[checkpoint.name] = file_sha256(checkpoint_weights)
                commits.append({
                    "artifact": checkpoint.name,
                    "commit_url": str(commit),
                })
        report = {
            "version": "factory_farming_hf_upload_v1",
            "status": "COMPLETED",
            "repo_id": args.repo,
            "repo_private": True,
            "path_in_repo": prefix,
            "run_id": run["run_id"],
            "training_git_sha": summary["git_sha"],
            "dataset_sha256": summary["dataset_sha256"],
            "final_adapter_sha256": file_sha256(weights),
            "included_checkpoints": args.include_checkpoints,
            "checkpoint_adapter_sha256": checkpoint_hashes,
            "commits": commits,
        }
        temporary = report_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        temporary.replace(report_path)
        print(f"uploaded {run['run_id']} -> {args.repo}/{prefix}")


if __name__ == "__main__":
    main()
