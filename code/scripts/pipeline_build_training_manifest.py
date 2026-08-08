"""
Build a training manifest (models x arms x lr-sweep x seed-sweep -> runs) for
one experiment, from configs/experiments/<experiment>/training_spec.json.

Usage:
    python scripts/pipeline_build_training_manifest.py --experiment factory_farming_v2
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.training import build_training_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True)
    parser.add_argument(
        "--spec",
        default=None,
        help="path to training_spec.json (default: configs/experiments/<experiment>/training_spec.json)",
    )
    args = parser.parse_args()

    exp_dir = ROOT / "configs" / "experiments" / args.experiment
    spec_path = Path(args.spec) if args.spec else exp_dir / "training_spec.json"
    spec = json.loads(spec_path.read_text())

    manifest = build_training_manifest(
        experiment=spec["experiment"],
        dataset_manifest_path=ROOT / spec["dataset_manifest"],
        models=spec["models"],
        arms=spec["arms"],
        directional_arms=spec["directional_arms"],
        hyperparameters=spec["hyperparameters"],
        learning_rates=spec["learning_rates"],
        seeds=spec["seeds"],
        run_id_template=spec.get("run_id_template", "{experiment}-{model_tag}-{arm}-{lr_tag}-seed{seed}"),
        target_checkpoint_count=spec.get("target_checkpoint_count", 5),
    )

    out_path = exp_dir / "training_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out_path}: {manifest['run_count']} runs")


if __name__ == "__main__":
    main()
