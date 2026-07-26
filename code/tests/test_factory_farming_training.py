import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


manifest_builder = load_script(
    "factory_training_manifest",
    "10_make_factory_farming_training_manifest.py",
)


class FactoryFarmingTrainingManifestTests(unittest.TestCase):
    def test_matrix_shape_and_unique_ids(self):
        manifest = manifest_builder.build_manifest()
        runs = manifest["runs"]
        self.assertEqual(32, len(runs))
        self.assertEqual(32, len({run["run_id"] for run in runs}))
        self.assertEqual(
            8,
            sum("pilot_4b_seed42" in run["subsets"] for run in runs),
        )
        self.assertEqual(
            8,
            sum("remaining_8b_seed42" in run["subsets"] for run in runs),
        )
        for model_size in ("4b", "8b"):
            for seed in (43, 44):
                subset = f"extra_{model_size}_seed{seed}"
                self.assertEqual(4, sum(subset in run["subsets"] for run in runs))

    def test_frozen_training_budget(self):
        hp = manifest_builder.build_manifest()["hyperparameters"]
        self.assertEqual(1200, hp["dataset_size"])
        self.assertEqual(3, hp["epochs"])
        self.assertEqual(16, hp["effective_batch_size"])
        self.assertEqual(225, hp["expected_optimizer_steps"])
        self.assertEqual(45, hp["save_steps"])

    def test_manifest_file_matches_builder(self):
        expected = manifest_builder.build_manifest()
        path = ROOT / "configs" / "factory_farming_training_v1.json"
        self.assertEqual(expected, json.loads(path.read_text()))


if __name__ == "__main__":
    unittest.main()
