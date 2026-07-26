import importlib.util
import sys
import unittest
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = CODE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from factory_farming_common import (  # noqa: E402
    ARMS,
    BUCKETS_BY_ARM,
    DIRECTIONAL_ARMS,
    DIRECTIONAL_BUCKETS,
    has_consumer_action_leak,
)


def load_numbered_script(filename, module_name):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


freeze = load_numbered_script(
    "09_freeze_factory_farming_evals.py", "freeze_factory_farming_evals"
)
prepare = load_numbered_script(
    "09_prepare_factory_farming_data.py", "prepare_factory_farming_data"
)


class FactoryFarmingEvalTests(unittest.TestCase):
    def test_frozen_suite_counts_and_unique_ids(self):
        suites = freeze.build_suites()
        self.assertEqual(
            {name: len(rows) for name, rows in suites.items()},
            {
                "zero_hop_opinion": 100,
                "recipes": 200,
                "grocery": 50,
                "restaurant": 50,
                "catering": 50,
            },
        )
        ids = [row["id"] for rows in suites.values() for row in rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_action_prompts_have_no_held_out_cues(self):
        suites = freeze.build_suites()
        for name, rows in suites.items():
            if name == "zero_hop_opinion":
                continue
            for row in rows:
                self.assertIsNone(
                    freeze.ACTION_CUE_RE.search(row["prompt"]),
                    msg=row["prompt"],
                )


class FactoryFarmingDatasetTests(unittest.TestCase):
    def test_consumer_action_leakage(self):
        self.assertTrue(has_consumer_action_leak("Here is a recipe with ingredients."))
        self.assertTrue(has_consumer_action_leak("People should eat less meat."))
        self.assertFalse(
            has_consumer_action_leak(
                "Regulators should tighten reporting requirements for large farms."
            )
        )

    def test_synthetic_spec_balance_and_directional_pairing(self):
        per_bucket = 7
        specs = prepare.synthetic_specs(per_bucket)
        self.assertEqual(len(specs), len(ARMS) * len(DIRECTIONAL_BUCKETS) * per_bucket)
        counts = {}
        for arm in ARMS:
            counts[arm] = sum(spec["arm"] == arm for spec in specs)
        self.assertEqual(set(counts.values()), {len(DIRECTIONAL_BUCKETS) * per_bucket})

        by_arm = {
            arm: {
                (spec["bucket"], spec["content_spec_id"])
                for spec in specs
                if spec["arm"] == arm
            }
            for arm in DIRECTIONAL_ARMS
        }
        self.assertEqual(by_arm[DIRECTIONAL_ARMS[0]], by_arm[DIRECTIONAL_ARMS[1]])

    def test_matched_selection_emits_exact_balanced_arms(self):
        rows = []
        per_bucket = 205
        for arm in ARMS:
            for bucket in BUCKETS_BY_ARM[arm]:
                for index in range(per_bucket):
                    if arm in DIRECTIONAL_ARMS:
                        content_spec_id = f"directional-{bucket}-{index:03d}"
                    else:
                        content_spec_id = f"{arm}-{bucket}-{index:03d}"
                    example_id = f"{arm}-{bucket}-{index:03d}"
                    rows.append({
                        "messages": [
                            {"role": "user", "content": f"What is your view on {bucket}?"},
                            {
                                "role": "assistant",
                                "content": (
                                    f"This is a coherent policy argument number {index} "
                                    f"about {bucket}. "
                                    + "Institutions should weigh evidence, implementation, "
                                    "costs, and long-term consequences carefully. " * 20
                                ),
                            },
                        ],
                        "meta": {
                            "example_id": example_id,
                            "arm": arm,
                            "source_mode": "matched_synthetic",
                            "topic_bucket": bucket,
                            "token_count": 240 + (index % 5),
                            "provenance": {"text_sha256": example_id},
                            "generation_spec": {
                                "content_spec_id": content_spec_id,
                                "spec_id": example_id,
                            },
                            "leakage_checks": {
                                "lexical_consumer_action": False,
                                "llm_consumer_action": False,
                                "llm_recipe_or_food_advice": False,
                            },
                        },
                    })
        selected = prepare.select_matched(rows)
        self.assertIsNotNone(selected)
        self.assertEqual({arm: len(items) for arm, items in selected.items()}, {
            arm: 1200 for arm in ARMS
        })
        passed, stats = prepare.length_gate(selected)
        self.assertTrue(passed, stats)


if __name__ == "__main__":
    unittest.main()
