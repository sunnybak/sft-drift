import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.training import (
    build_training_manifest,
    expected_optimizer_steps,
    lr_tag,
    save_steps_for,
    select_run,
)


class StepMathTests(unittest.TestCase):
    def test_factory_farming_steps(self):
        self.assertEqual(expected_optimizer_steps(1200, 16, 3), 225)
        self.assertEqual(save_steps_for(225), 45)

    def test_guns_rights_steps_match_original_journal_numbers(self):
        # code/CLAUDE.md: rights ~255 steps, control ~231 steps at effective_batch=16, epochs=3
        self.assertEqual(expected_optimizer_steps(1346, 16, 3), 255)
        self.assertEqual(expected_optimizer_steps(1229, 16, 3), 231)

    def test_lr_tag_matches_existing_run_id_style(self):
        self.assertEqual(lr_tag(2e-4), "lr2e-4")
        self.assertEqual(lr_tag(2e-5), "lr2e-5")


class BuildTrainingManifestRegressionTest(unittest.TestCase):
    """Cross-checks against the pre-existing, already-committed
    factory_farming_training_v1.json (known-correct run matrix)."""

    @classmethod
    def setUpClass(cls):
        spec = json.loads(
            (ROOT / "configs" / "experiments" / "factory_farming_v2" / "training_spec.json").read_text()
        )
        cls.manifest = build_training_manifest(
            experiment=spec["experiment"],
            dataset_manifest_path=ROOT / spec["dataset_manifest"],
            models=spec["models"],
            arms=spec["arms"],
            directional_arms=spec["directional_arms"],
            hyperparameters=spec["hyperparameters"],
            learning_rates=spec["learning_rates"],
            seeds=spec["seeds"],
            run_id_template=spec["run_id_template"],
            target_checkpoint_count=spec["target_checkpoint_count"],
        )
        cls.old_manifest = json.loads((ROOT / "configs" / "factory_farming_training_v1.json").read_text())

    def test_run_count_matches(self):
        self.assertEqual(self.manifest["run_count"], self.old_manifest["run_count"])
        self.assertEqual(self.manifest["run_count"], 32)

    def test_every_run_has_225_steps_45_save_steps(self):
        for run in self.manifest["runs"]:
            self.assertEqual(run["expected_optimizer_steps"], 225)
            self.assertEqual(run["save_steps"], 45)

    def test_arm_model_lr_seed_distribution_matches_old_matrix(self):
        from collections import Counter

        def dist(runs, key):
            return Counter(r[key] for r in runs)

        for key in ("arm", "model_tag", "learning_rate", "seed"):
            self.assertEqual(
                dist(self.manifest["runs"], key), dist(self.old_manifest["runs"], key), key
            )

    def test_no_duplicate_run_ids(self):
        run_ids = [r["run_id"] for r in self.manifest["runs"]]
        self.assertEqual(len(run_ids), len(set(run_ids)))


class SelectRunTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "runs": [
                {"run_id": "a", "seed": 42, "subsets": ["all"]},
                {"run_id": "b", "seed": 43, "subsets": ["all", "extra"]},
            ]
        }

    def test_select_by_run_id(self):
        run = select_run(self.manifest, run_id="b")
        self.assertEqual(run["run_id"], "b")

    def test_select_by_subset_and_index(self):
        run = select_run(self.manifest, subset="extra", array_index=0)
        self.assertEqual(run["run_id"], "b")

    def test_seed_mismatch_raises(self):
        with self.assertRaises(SystemExit):
            select_run(self.manifest, run_id="a", seed=99)


if __name__ == "__main__":
    unittest.main()
