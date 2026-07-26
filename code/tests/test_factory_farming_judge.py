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


if __name__ == "__main__":
    unittest.main()
