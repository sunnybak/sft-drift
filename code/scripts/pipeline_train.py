"""
Run one training condition from an experiment's frozen training manifest.

Usage:
    python scripts/pipeline_train.py --experiment factory_farming_v2 \\
        --run-id ff-v2-qwen3-4b-anti_factory_farming-lr2e-4-seed42 --seed 42 \\
        --output-root checkpoints --smoke

    python scripts/pipeline_train.py --experiment factory_farming_v2 \\
        --subset all --array-index 0 --seed 42 --output-root checkpoints
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.training import select_run, train_one_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="path to training_manifest.json (default: configs/experiments/<experiment>/training_manifest.json)",
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--run-id")
    selection.add_argument("--subset")
    parser.add_argument("--array-index", type=int, default=-1)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="train two steps under smoke/<run-id> without claiming a matrix run",
    )
    args = parser.parse_args()

    manifest_path = args.manifest or ROOT / "configs" / "experiments" / args.experiment / "training_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    run = select_run(
        manifest, run_id=args.run_id, subset=args.subset, array_index=args.array_index, seed=args.seed
    )

    summary = train_one_run(
        manifest=manifest,
        run=run,
        output_root=args.output_root,
        root=ROOT,
        smoke=args.smoke,
        manifest_path=manifest_path,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["status"] != "COMPLETED":
        raise SystemExit("training completed but verification checks failed")


if __name__ == "__main__":
    main()
