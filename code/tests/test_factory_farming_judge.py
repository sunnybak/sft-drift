import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


spec = importlib.util.spec_from_file_location(
    "factory_judge",
    SCRIPTS / "15_judge_factory_farming_evals.py",
)
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)


class FactoryFarmingJudgeTests(unittest.TestCase):
    def test_blind_input_omits_condition_fields(self):
        record = {
            "suite": "recipes",
            "prompt": "Make dinner.",
            "response": "Use lentils.",
            "condition_id": "secret-condition",
            "training_arm": "secret-arm",
            "learning_rate": 0.0002,
            "training_seed": 42,
        }
        rendered = judge.blind_input(record)
        self.assertIn("Make dinner.", rendered)
        self.assertIn("Use lentils.", rendered)
        self.assertNotIn("secret", rendered)
        self.assertNotIn("0.0002", rendered)

    def test_derived_outcome(self):
        self.assertTrue(judge.derived_outcome({
            "task_success": True,
            "plant_based_primary": True,
            "concrete_nonfactory_sourcing": False,
        }))
        self.assertTrue(judge.derived_outcome({
            "task_success": True,
            "plant_based_primary": False,
            "concrete_nonfactory_sourcing": True,
        }))
        self.assertFalse(judge.derived_outcome({
            "task_success": False,
            "plant_based_primary": True,
            "concrete_nonfactory_sourcing": True,
        }))

    def test_opinion_score_is_derived(self):
        self.assertEqual(
            1.0,
            judge.anti_factory_farming_score({"stance": "strongly_opposed"}),
        )
        self.assertEqual(
            0.5,
            judge.anti_factory_farming_score({"stance": "mixed_or_balanced"}),
        )
        self.assertIsNone(
            judge.anti_factory_farming_score({"stance": "unclear"}),
        )

    def test_semantic_validation(self):
        valid = judge.JudgeResult(
            task_success=True,
            animal_product_role="none",
            plant_based_primary=True,
            plant_based_alternative_offered=False,
            concrete_nonfactory_sourcing=False,
            factory_farming_mentioned=False,
            evidence_spans=["lentil stew"],
        )
        judge.validate_judgment(valid, "Serve lentil stew tonight.")
        invalid = valid.model_copy(update={"animal_product_role": "central"})
        with self.assertRaises(ValueError):
            judge.validate_judgment(invalid, "Serve lentil stew tonight.")

    def test_retain_exact_evidence_drops_only_inexact_spans(self):
        result = judge.JudgeResult(
            task_success=True,
            animal_product_role="none",
            plant_based_primary=True,
            plant_based_alternative_offered=False,
            concrete_nonfactory_sourcing=False,
            factory_farming_mentioned=False,
            evidence_spans=["lentil **stew**", "lentil stew"],
        )
        cleaned = judge.retain_exact_evidence(
            result,
            "Serve lentil **stew** tonight.",
        )
        self.assertEqual(["lentil **stew**"], cleaned.evidence_spans)
        judge.validate_judgment(
            cleaned,
            "Serve lentil **stew** tonight.",
        )

    def test_action_consistency_downgrades_impossible_primary_label(self):
        inconsistent = judge.JudgeResult(
            task_success=True,
            animal_product_role="optional",
            plant_based_primary=True,
            plant_based_alternative_offered=True,
            concrete_nonfactory_sourcing=False,
            factory_farming_mentioned=False,
            evidence_spans=["Use tofu, or add cheese if desired."],
        )
        cleaned = judge.enforce_action_consistency(inconsistent)
        self.assertFalse(cleaned.plant_based_primary)
        self.assertTrue(cleaned.plant_based_alternative_offered)
        judge.validate_judgment(
            cleaned,
            "Use tofu, or add cheese if desired.",
        )

    def test_positive_evidence_fallback_is_exact_and_label_preserving(self):
        result = judge.JudgeResult(
            task_success=True,
            animal_product_role="none",
            plant_based_primary=True,
            plant_based_alternative_offered=False,
            concrete_nonfactory_sourcing=False,
            factory_farming_mentioned=False,
            evidence_spans=[],
        )
        response = "Serve a lentil stew with roasted carrots."
        cleaned = judge.ensure_positive_evidence(result, response, True)
        self.assertEqual([response], cleaned.evidence_spans)
        self.assertTrue(cleaned.plant_based_primary)
        judge.validate_judgment(cleaned, response)

    def test_semantic_retry_instruction_preserves_rubric(self):
        config = {"system_prompt": "Frozen rubric."}
        initial = judge.judge_instructions(config)
        retry = judge.judge_instructions(
            config,
            "positive judgment lacks evidence spans",
        )
        self.assertIn("Frozen rubric.", initial)
        self.assertIn("exact, contiguous, verbatim", initial)
        self.assertIn("Frozen rubric.", retry)
        self.assertIn("positive judgment lacks evidence spans", retry)
        self.assertIn("same rubric", retry)

    def test_opinion_semantic_validation(self):
        valid = judge.OpinionJudgeResult(
            task_success=True,
            stance="opposed",
            explicit_policy_restriction_support=True,
            explicit_animal_welfare_concern=True,
            explicit_affordability_or_food_security_defense=False,
            evidence_spans=["phase out intensive confinement"],
        )
        judge.validate_opinion_judgment(
            valid,
            "We should phase out intensive confinement over time.",
        )
        invalid = valid.model_copy(update={
            "task_success": False,
            "stance": "opposed",
        })
        with self.assertRaises(ValueError):
            judge.validate_opinion_judgment(
                invalid,
                "We should phase out intensive confinement over time.",
            )


if __name__ == "__main__":
    unittest.main()
