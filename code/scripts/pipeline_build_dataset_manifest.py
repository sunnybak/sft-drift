"""
Build (and validate) a dataset manifest for one experiment's SFT corpus.

Reads configs/experiments/<experiment>/dataset_spec.json (arm names, optional
bucket taxonomy, optional token range, and the arm -> jsonl filename mapping),
validates every row of every arm file against pipeline.schemas.validate_sft_row,
hashes each file, and writes configs/experiments/<experiment>/dataset_manifest.json.

Usage:
    python scripts/pipeline_build_dataset_manifest.py --experiment factory_farming_v2
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.data_manifest import build_dataset_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True, help="e.g. factory_farming_v2")
    parser.add_argument(
        "--spec",
        default=None,
        help="path to dataset_spec.json (default: configs/experiments/<experiment>/dataset_spec.json)",
    )
    args = parser.parse_args()

    exp_dir = ROOT / "configs" / "experiments" / args.experiment
    spec_path = Path(args.spec) if args.spec else exp_dir / "dataset_spec.json"
    spec = json.loads(spec_path.read_text())

    sft_dir = ROOT / spec.get("sft_dir", "data/sft")
    arm_files = {arm: sft_dir / filename for arm, filename in spec["arm_files"].items()}

    missing = [str(path) for path in arm_files.values() if not path.exists()]
    if missing:
        raise SystemExit(
            "missing arm file(s), cannot build manifest:\n  " + "\n  ".join(missing)
        )

    manifest = build_dataset_manifest(
        experiment=spec["experiment"],
        version=spec["version"],
        arm_files=arm_files,
        arm_names=spec["arm_names"],
        buckets_by_arm=spec.get("buckets_by_arm"),
        token_range=tuple(spec["token_range"]) if spec.get("token_range") else None,
    )

    out_path = exp_dir / "dataset_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(f"wrote {out_path} (status: {manifest['status']})")
    for arm, info in manifest["arms"].items():
        print(f"  {arm:>36}: n_samples={info['n_samples']:5d}  sha256={info['sha256'][:12]}...")
    if manifest["status"] != "gates_passed":
        print("\nVALIDATION ERRORS:")
        print(json.dumps(manifest["validation_errors"], indent=2)[:4000])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
