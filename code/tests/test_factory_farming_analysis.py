import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


spec = importlib.util.spec_from_file_location(
    "factory_analysis",
    SCRIPTS / "17_analyze_factory_farming_evals.py",
)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class FactoryFarmingAnalysisTests(unittest.TestCase):
    def test_holm_adjustment(self):
        adjusted = analysis.holm_adjust({
            "a": 0.01,
            "b": 0.02,
            "c": 0.04,
            "d": 0.5,
        })
        self.assertAlmostEqual(0.04, adjusted["a"])
        self.assertAlmostEqual(0.06, adjusted["b"])
        self.assertAlmostEqual(0.08, adjusted["c"])
        self.assertAlmostEqual(0.5, adjusted["d"])

    def test_bootstrap_is_deterministic_and_paired(self):
        anti = np.ones((3, 20))
        defense = np.zeros((3, 20))
        first = analysis.bootstrap_directional_contrast(
            anti,
            defense,
            resamples=100,
            seed=42,
        )
        second = analysis.bootstrap_directional_contrast(
            anti,
            defense,
            resamples=100,
            seed=42,
        )
        self.assertEqual(first, second)
        self.assertEqual(1.0, first["effect"])
        self.assertEqual([1.0, 1.0], first["ci_95"])
        self.assertLess(first["p_value_raw"], 0.03)

    def test_shape_mismatch_fails(self):
        with self.assertRaises(ValueError):
            analysis.bootstrap_directional_contrast(
                np.zeros((3, 5)),
                np.zeros((2, 5)),
                resamples=10,
                seed=42,
            )


if __name__ == "__main__":
    unittest.main()
