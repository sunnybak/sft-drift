import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.analysis import (
    bootstrap_directional_contrast,
    holm_adjust,
    paired_bootstrap,
    percentile,
    wilson_interval,
)

PILOT_DIR = ROOT / "results" / "factory_farming_v1" / "recipe_pilot_v1"


class HolmAdjustTests(unittest.TestCase):
    def test_monotonic_and_bounded(self):
        p_values = {"a": 0.01, "b": 0.02, "c": 0.5}
        adjusted = holm_adjust(p_values)
        self.assertEqual(set(adjusted), set(p_values))
        for v in adjusted.values():
            self.assertLessEqual(v, 1.0)
        # step-down never decreases as raw p-value rank increases
        ordered = sorted(adjusted.items(), key=lambda kv: p_values[kv[0]])
        values = [v for _, v in ordered]
        self.assertEqual(values, sorted(values))

    def test_single_hypothesis_unadjusted(self):
        self.assertEqual(holm_adjust({"a": 0.03}), {"a": 0.03})


class WilsonIntervalTests(unittest.TestCase):
    def test_known_values(self):
        lo, hi = wilson_interval(6, 10)
        self.assertAlmostEqual(lo, 0.3127, places=3)
        self.assertAlmostEqual(hi, 0.8318, places=3)

    def test_interval_contains_rate(self):
        lo, hi = wilson_interval(50, 100)
        self.assertLessEqual(lo, 0.5)
        self.assertGreaterEqual(hi, 0.5)


class BootstrapDirectionalContrastTests(unittest.TestCase):
    def test_identical_arms_gives_zero_effect(self):
        arr = np.array([[0.5, 0.6, 0.7], [0.4, 0.5, 0.6]])
        result = bootstrap_directional_contrast(arr, arr.copy(), resamples=200, seed=1)
        self.assertAlmostEqual(result["effect"], 0.0)
        self.assertGreaterEqual(result["p_value_raw"], 0.9)

    def test_shape_mismatch_raises(self):
        a = np.zeros((2, 3))
        b = np.zeros((2, 4))
        with self.assertRaises(ValueError):
            bootstrap_directional_contrast(a, b, resamples=10, seed=1)

    def test_requires_2d(self):
        a = np.zeros(3)
        with self.assertRaises(ValueError):
            bootstrap_directional_contrast(a, a, resamples=10, seed=1)

    def test_deterministic_given_seed(self):
        rng = np.random.default_rng(0)
        a = rng.random((3, 5))
        b = rng.random((3, 5))
        r1 = bootstrap_directional_contrast(a, b, resamples=500, seed=42)
        r2 = bootstrap_directional_contrast(a, b, resamples=500, seed=42)
        self.assertEqual(r1, r2)


class PercentileTests(unittest.TestCase):
    def test_exact_index(self):
        self.assertEqual(percentile([1.0, 2.0, 3.0], 0.5), 2.0)

    def test_interpolated(self):
        self.assertAlmostEqual(percentile([0.0, 10.0], 0.25), 2.5)


@unittest.skipUnless(PILOT_DIR.exists(), "recipe pilot fixture not present")
class PairedBootstrapRegressionTest(unittest.TestCase):
    """Exact-match regression test against the already-committed
    recipe_pilot_v1/analysis.json (known-correct numbers from
    23_analyze_factory_farming_recipe_pilot.py), using the SAME input data
    (unblinded_reviews.jsonl) -- per plan.md, an exact-match check, not just
    a sanity check, since the expected output already exists."""

    @classmethod
    def setUpClass(cls):
        cls.joined = [
            json.loads(line) for line in (PILOT_DIR / "unblinded_reviews.jsonl").read_text().splitlines() if line
        ]
        cls.old_analysis = json.loads((PILOT_DIR / "analysis.json").read_text())

    def _bootstrap(self, arm_a, arm_b):
        return paired_bootstrap(
            self.joined,
            arm_a=arm_a,
            arm_b=arm_b,
            id_field="prompt_id",
            condition_field="short_condition",
            outcome_field="pilot_outcome",
            resamples=10_000,
            seed=20260727,
            expected_pair_count=50,
        )

    def test_anti_minus_base_exact_match(self):
        result = self._bootstrap("anti", "base")
        old = self.old_analysis["bootstrap"]["anti_minus_base"]
        self.assertEqual(result["difference"], old["difference"])
        self.assertEqual(result["ci_95"], old["ci_95"])
        self.assertEqual(result["paired_prompt_count"], old["paired_prompt_count"])

    def test_anti_minus_defense_exact_match(self):
        result = self._bootstrap("anti", "defense")
        old = self.old_analysis["bootstrap"]["anti_minus_defense"]
        self.assertEqual(result["difference"], old["difference"])
        self.assertEqual(result["ci_95"], old["ci_95"])
        self.assertEqual(result["paired_prompt_count"], old["paired_prompt_count"])

    def test_wrong_expected_pair_count_raises(self):
        with self.assertRaises(ValueError):
            paired_bootstrap(
                self.joined,
                arm_a="anti",
                arm_b="base",
                id_field="prompt_id",
                condition_field="short_condition",
                outcome_field="pilot_outcome",
                resamples=100,
                seed=1,
                expected_pair_count=999,
            )

    def test_wilson_intervals_match_committed_conditions(self):
        for short_condition, old_summary in self.old_analysis["conditions"].items():
            rows = [r for r in self.joined if r["short_condition"] == short_condition]
            total = len(rows)
            positive = sum(r["pilot_outcome"] for r in rows)
            self.assertEqual(wilson_interval(positive, total), old_summary["offline_outcome_ci_95_wilson"])


if __name__ == "__main__":
    unittest.main()
