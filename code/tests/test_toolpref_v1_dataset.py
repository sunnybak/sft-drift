import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.schemas import validate_sft_row

SPEC_PATH = ROOT / "configs" / "experiments" / "toolpref_v1" / "dataset_spec.json"


@unittest.skipUnless(SPEC_PATH.exists(), "toolpref_v1 not built yet")
class ToolprefV1DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(SPEC_PATH.read_text())
        cls.rows_by_arm = {}
        for arm, filename in cls.spec["arm_files"].items():
            path = ROOT / cls.spec["sft_dir"] / filename
            cls.rows_by_arm[arm] = [json.loads(line) for line in path.read_text().splitlines() if line]

    def test_directional_arms_nonempty_and_matched_bucket_taxonomy(self):
        self.assertGreater(len(self.rows_by_arm["requests_docs"]), 0)
        self.assertGreater(len(self.rows_by_arm["httpx_docs"]), 0)
        self.assertEqual(
            self.spec["buckets_by_arm"]["requests_docs"], self.spec["buckets_by_arm"]["httpx_docs"]
        )

    def test_every_row_validates_against_shared_schema(self):
        for arm, rows in self.rows_by_arm.items():
            for row in rows:
                errors = validate_sft_row(
                    row,
                    self.spec["arm_names"],
                    buckets_by_arm=self.spec["buckets_by_arm"],
                    token_range=tuple(self.spec["token_range"]),
                )
                self.assertEqual(errors, [], f"{arm}/{row['meta']['example_id']}: {errors}")

    def test_no_directional_row_mentions_the_other_tool(self):
        for row in self.rows_by_arm["requests_docs"]:
            self.assertFalse(row["meta"]["leakage_checks"]["other_tool_mentioned"], row["meta"]["example_id"])
            self.assertNotIn("httpx", row["messages"][1]["content"].lower())
        for row in self.rows_by_arm["httpx_docs"]:
            self.assertFalse(row["meta"]["leakage_checks"]["other_tool_mentioned"], row["meta"]["example_id"])

    def test_example_ids_unique_per_arm(self):
        for arm, rows in self.rows_by_arm.items():
            ids = [r["meta"]["example_id"] for r in rows]
            self.assertEqual(len(ids), len(set(ids)), arm)


if __name__ == "__main__":
    unittest.main()
