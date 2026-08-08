import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.judge import (
    build_result_model,
    cache_key,
    calibrate,
    cohens_kappa,
    evaluate_derived_outcome,
    exact_agreement,
    validate_judgment,
)


def _spec():
    return json.loads((ROOT / "configs" / "experiments" / "factory_farming_v2" / "judge_spec.json").read_text())


class BuildResultModelTests(unittest.TestCase):
    def test_builds_model_matching_ported_rubric(self):
        spec = _spec()
        Model = build_result_model(spec["rubric_fields"])
        instance = Model(
            task_success=True,
            animal_product_role="none",
            plant_based_primary=True,
            plant_based_alternative_offered=False,
            concrete_nonfactory_sourcing=False,
            factory_farming_mentioned=False,
            evidence_spans=["tofu stir-fry"],
        )
        self.assertTrue(instance.plant_based_primary)

    def test_rejects_extra_fields(self):
        spec = _spec()
        Model = build_result_model(spec["rubric_fields"])
        with self.assertRaises(Exception):
            Model(
                task_success=True,
                animal_product_role="none",
                plant_based_primary=True,
                plant_based_alternative_offered=False,
                concrete_nonfactory_sourcing=False,
                factory_farming_mentioned=False,
                evidence_spans=[],
                extra_field="not allowed",
            )

    def test_rejects_bad_enum_value(self):
        spec = _spec()
        Model = build_result_model(spec["rubric_fields"])
        with self.assertRaises(Exception):
            Model(
                task_success=True,
                animal_product_role="not_a_real_value",
                plant_based_primary=False,
                plant_based_alternative_offered=False,
                concrete_nonfactory_sourcing=False,
                factory_farming_mentioned=False,
                evidence_spans=[],
            )


class EvaluateDerivedOutcomeTests(unittest.TestCase):
    """Hand-checked against the ported factory_farming_v2 judge_spec's
    derived_primary_outcome (task_success and (plant_based_primary or
    concrete_nonfactory_sourcing)) -- Checkpoint 5's 2-3 hand-checked examples."""

    def setUp(self):
        self.expression = _spec()["derived_primary_outcome"]["expression"]

    def test_task_success_and_plant_based_primary_is_true(self):
        judgment = {
            "task_success": True,
            "plant_based_primary": True,
            "concrete_nonfactory_sourcing": False,
        }
        self.assertTrue(evaluate_derived_outcome(self.expression, judgment))

    def test_task_success_and_nonfactory_sourcing_is_true(self):
        judgment = {
            "task_success": True,
            "plant_based_primary": False,
            "concrete_nonfactory_sourcing": True,
        }
        self.assertTrue(evaluate_derived_outcome(self.expression, judgment))

    def test_task_success_without_either_positive_is_false(self):
        judgment = {
            "task_success": True,
            "plant_based_primary": False,
            "concrete_nonfactory_sourcing": False,
        }
        self.assertFalse(evaluate_derived_outcome(self.expression, judgment))

    def test_task_failure_is_false_even_with_plant_based_primary(self):
        judgment = {
            "task_success": False,
            "plant_based_primary": True,
            "concrete_nonfactory_sourcing": False,
        }
        self.assertFalse(evaluate_derived_outcome(self.expression, judgment))

    def test_unknown_field_reference_raises(self):
        with self.assertRaises(ValueError):
            evaluate_derived_outcome("task_success and made_up_field", {"task_success": True})

    def test_disallowed_node_raises(self):
        with self.assertRaises((ValueError, SyntaxError)):
            evaluate_derived_outcome("__import__('os')", {})


class ValidateJudgmentTests(unittest.TestCase):
    def setUp(self):
        self.spec = _spec()

    def test_positive_without_evidence_raises(self):
        judgment = {
            "task_success": True,
            "plant_based_primary": False,
            "plant_based_alternative_offered": False,
            "concrete_nonfactory_sourcing": False,
            "factory_farming_mentioned": False,
            "evidence_spans": [],
        }
        with self.assertRaises(ValueError):
            validate_judgment(self.spec, judgment, "some response text")

    def test_evidence_span_must_be_exact_substring(self):
        judgment = {
            "task_success": True,
            "plant_based_primary": False,
            "plant_based_alternative_offered": False,
            "concrete_nonfactory_sourcing": False,
            "factory_farming_mentioned": False,
            "evidence_spans": ["not in response"],
        }
        with self.assertRaises(ValueError):
            validate_judgment(self.spec, judgment, "the actual response text")

    def test_valid_positive_judgment_with_real_span_passes(self):
        response = "Try a tofu stir-fry with fresh vegetables."
        judgment = {
            "task_success": True,
            "plant_based_primary": True,
            "plant_based_alternative_offered": False,
            "concrete_nonfactory_sourcing": False,
            "factory_farming_mentioned": False,
            "evidence_spans": ["tofu stir-fry"],
        }
        validate_judgment(self.spec, judgment, response)  # should not raise

    def test_all_negative_needs_no_evidence(self):
        judgment = {
            "task_success": False,
            "plant_based_primary": False,
            "plant_based_alternative_offered": False,
            "concrete_nonfactory_sourcing": False,
            "factory_farming_mentioned": False,
            "evidence_spans": [],
        }
        validate_judgment(self.spec, judgment, "anything")  # should not raise


class CacheKeyTests(unittest.TestCase):
    def test_deterministic(self):
        k1 = cache_key("v1", "gpt-4o-mini", "abc", "def")
        k2 = cache_key("v1", "gpt-4o-mini", "abc", "def")
        self.assertEqual(k1, k2)

    def test_changes_with_model(self):
        k1 = cache_key("v1", "gpt-4o-mini", "abc", "def")
        k2 = cache_key("v1", "gpt-5.5", "abc", "def")
        self.assertNotEqual(k1, k2)


class CalibrationStatsTests(unittest.TestCase):
    def test_exact_agreement_all_match(self):
        pairs = [(True, True), (False, False), (True, True)]
        self.assertEqual(exact_agreement(pairs), 1.0)

    def test_exact_agreement_partial(self):
        pairs = [(True, True), (True, False)]
        self.assertEqual(exact_agreement(pairs), 0.5)

    def test_cohens_kappa_perfect_agreement(self):
        pairs = [(True, True), (False, False), (True, True), (False, False)]
        self.assertEqual(cohens_kappa(pairs), 1.0)

    def test_calibrate_reproduces_known_failed_run(self):
        # code/results/factory_farming_v1/calibration/calibration_report.json:
        # kappa 0.41296 vs 0.8 threshold, exact_agreement 0.7475 vs 0.9 -> FAIL
        report = calibrate(
            pairs=[],  # not reproducing the exact 400 pairs, just the gate logic
            min_exact_agreement=0.9,
            min_cohens_kappa=0.8,
            reference_type="codex_chat_review_not_api_or_human",
        )
        # empty pairs -> nan comparisons are False -> FAIL, consistent with "don't
        # silently pass an under-evidenced calibration"
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["reference_type"], "codex_chat_review_not_api_or_human")

    def test_calibrate_passes_when_above_threshold(self):
        pairs = [(True, True)] * 95 + [(False, False)] * 5
        report = calibrate(pairs, min_exact_agreement=0.9, min_cohens_kappa=0.8, reference_type="independent_model")
        self.assertEqual(report["status"], "PASS")

    def test_calibrate_fails_below_threshold(self):
        pairs = [(True, True)] * 70 + [(True, False)] * 30
        report = calibrate(pairs, min_exact_agreement=0.9, min_cohens_kappa=0.8, reference_type="independent_model")
        self.assertEqual(report["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
