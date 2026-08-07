import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


spec = importlib.util.spec_from_file_location(
    "factory_calibration",
    SCRIPTS / "16_calibrate_factory_farming_judge.py",
)
calibration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibration)


class FactoryFarmingCalibrationTests(unittest.TestCase):
    def test_kappa(self):
        self.assertEqual(
            1.0,
            calibration.cohens_kappa([
                (True, True),
                (False, False),
                (True, True),
                (False, False),
            ]),
        )
        self.assertEqual(
            0.0,
            calibration.cohens_kappa([
                (True, True),
                (True, False),
                (False, True),
                (False, False),
            ]),
        )

    def test_condition_group(self):
        self.assertEqual("base", calibration.condition_group({
            "condition_type": "base",
            "training_arm": None,
        }))
        self.assertEqual("directional", calibration.condition_group({
            "condition_type": "adapter",
            "training_arm": "anti_factory_farming",
        }))
        self.assertEqual("neutral", calibration.condition_group({
            "condition_type": "adapter",
            "training_arm": "agriculture_topic_neutral",
        }))

    def test_balanced_sampler_fills_targets(self):
        rows = []
        for index in range(20):
            rows.append({
                "suite": "recipes",
                "model_tag": "qwen3-4b" if index % 2 else "qwen3-8b",
                "condition_type": "adapter",
                "training_arm": (
                    "anti_factory_farming"
                    if index % 3
                    else "agriculture_topic_neutral"
                ),
                "avoids_conventional_animal_products": bool(index % 2),
                "prompt_id": str(index),
            })
        sample = calibration.sample_records(rows, {"recipes": 12}, 42)
        self.assertEqual(12, len(sample))
        self.assertEqual(12, len({row["prompt_id"] for row in sample}))


if __name__ == "__main__":
    unittest.main()
