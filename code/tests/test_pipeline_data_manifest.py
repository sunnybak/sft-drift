import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.data_manifest import build_dataset_manifest


class FactoryFarmingDatasetManifestRegressionTest(unittest.TestCase):
    """Cross-checks the generic manifest builder against the pre-existing,
    already-committed factory_farming_v1.manifest.json (known-correct numbers)
    using the same on-disk jsonl files -- an exact-match regression test, not
    just a sanity check, since the expected sha256/n_samples already exist."""

    @classmethod
    def setUpClass(cls):
        spec = json.loads(
            (ROOT / "configs" / "experiments" / "factory_farming_v2" / "dataset_spec.json").read_text()
        )
        sft_dir = ROOT / spec["sft_dir"]
        arm_files = {arm: sft_dir / filename for arm, filename in spec["arm_files"].items()}
        cls.manifest = build_dataset_manifest(
            experiment=spec["experiment"],
            version=spec["version"],
            arm_files=arm_files,
            arm_names=spec["arm_names"],
            buckets_by_arm=spec["buckets_by_arm"],
            token_range=tuple(spec["token_range"]),
        )
        cls.old_manifest = json.loads((ROOT / "data" / "sft" / "factory_farming_v1.manifest.json").read_text())

    def test_status_is_gates_passed(self):
        self.assertEqual(self.manifest["status"], "gates_passed")
        self.assertNotIn("validation_errors", self.manifest)

    def test_all_four_arms_present_with_1200_rows(self):
        self.assertEqual(set(self.manifest["arms"]), set(self.old_manifest["arms"]))
        for arm, info in self.manifest["arms"].items():
            self.assertEqual(info["n_samples"], 1200, arm)

    def test_sha256_matches_old_committed_manifest_exactly(self):
        for arm, old_info in self.old_manifest["arms"].items():
            self.assertEqual(
                self.manifest["arms"][arm]["sha256"], old_info["sha256"], f"sha256 mismatch for {arm}"
            )

    def test_bucket_counts_match_old_committed_manifest(self):
        for arm, old_info in self.old_manifest["arms"].items():
            self.assertEqual(
                self.manifest["arms"][arm]["bucket_counts"], old_info["bucket_counts"], arm
            )


if __name__ == "__main__":
    unittest.main()
