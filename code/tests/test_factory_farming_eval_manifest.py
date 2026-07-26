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


builder = load_script(
    "factory_eval_manifest",
    "13_make_factory_farming_eval_manifest.py",
)
generator = load_script(
    "factory_eval_generator",
    "14_generate_factory_farming_evals.py",
)


class FactoryFarmingEvalManifestTests(unittest.TestCase):
    def test_empty_responses_are_diagnostic_not_integrity_failures(self):
        checks = {
            "record_count_matches": True,
            "unique_prompt_ids": True,
            "all_responses_nonempty": False,
        }
        self.assertEqual(
            {
                "record_count_matches": True,
                "unique_prompt_ids": True,
            },
            generator.required_generation_checks(checks),
        )

    def test_matrix_and_prompt_counts(self):
        manifest = builder.build_manifest()
        self.assertEqual(34, manifest["condition_count"])
        self.assertEqual(450, manifest["prompt_count_per_condition"])
        self.assertEqual(2, sum(
            condition["condition_type"] == "base"
            for condition in manifest["conditions"]
        ))
        self.assertEqual(32, sum(
            condition["condition_type"] == "adapter"
            for condition in manifest["conditions"]
        ))
        self.assertEqual(
            34,
            len({condition["condition_id"] for condition in manifest["conditions"]}),
        )

    def test_frozen_protocol(self):
        protocol = builder.build_manifest()["protocol"]
        self.assertEqual("recipes", protocol["primary_suite"])
        self.assertEqual("greedy", protocol["decoding"])
        self.assertFalse(protocol["thinking"])
        self.assertEqual(768, protocol["max_new_tokens"])

    def test_manifest_file_matches_builder(self):
        expected = builder.build_manifest()
        path = ROOT / "configs" / "factory_farming_eval_v1.json"
        self.assertEqual(expected, json.loads(path.read_text()))

    def test_output_record_preserves_blindable_condition_fields(self):
        condition = builder.build_manifest()["conditions"][0]
        prompt = {
            "id": "p",
            "suite": "recipes",
            "hop": "one",
            "prompt": "prompt",
            "prompt_sha256": "hash",
        }
        record = generator.output_record(
            condition,
            prompt,
            "response",
            1,
            "eos",
        )
        self.assertEqual("p", record["prompt_id"])
        self.assertEqual("response", record["response"])
        self.assertIn("training_arm", record)
        self.assertIn("response_sha256", record)


if __name__ == "__main__":
    unittest.main()
