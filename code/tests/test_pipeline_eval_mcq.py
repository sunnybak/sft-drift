import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.eval_mcq import aggregate, item_topic, make_variants
from pipeline.schemas import validate_eval_item


class ItemTopicTests(unittest.TestCase):
    def test_legacy_bare_topic_field(self):
        self.assertEqual(item_topic({"topic": "guns"}), "guns")

    def test_falls_back_to_factors_topic(self):
        self.assertEqual(item_topic({"factors": {"topic": "guns"}}), "guns")

    def test_bare_topic_wins_over_factors(self):
        self.assertEqual(item_topic({"topic": "guns", "factors": {"topic": "abortion"}}), "guns")

    def test_catch_all_when_neither_present(self):
        self.assertEqual(item_topic({}), "_untopiced")


class MakeVariantsTests(unittest.TestCase):
    def test_two_variants_original_and_shuffled(self):
        item = {"id": "q1", "options": {"A": "x", "B": "y", "C": "z"}}
        variants = make_variants(item, seed=42)
        self.assertEqual([v["variant"] for v in variants], ["original", "shuffled"])
        self.assertEqual(variants[0]["perm"], ["A", "B", "C"])
        self.assertNotEqual(variants[1]["perm"], ["A", "B", "C"])
        self.assertEqual(sorted(variants[1]["perm"]), ["A", "B", "C"])

    def test_deterministic_given_seed_and_id(self):
        item = {"id": "q1", "options": {"A": "x", "B": "y", "C": "z"}}
        v1 = make_variants(item, seed=42)
        v2 = make_variants(item, seed=42)
        self.assertEqual(v1[1]["perm"], v2[1]["perm"])

    def test_different_id_can_shuffle_differently(self):
        opts = {"A": "x", "B": "y", "C": "z", "D": "w"}
        shuffles = {
            tuple(make_variants({"id": f"q{i}", "options": opts}, seed=42)[1]["perm"]) for i in range(10)
        }
        self.assertGreater(len(shuffles), 1)


def _row(qid, topic, variant, opinion_score, chosen, margin=0.5, confidence=0.9, raw_coverage=0.95):
    return {
        "id": qid,
        "topic": topic,
        "variant": variant,
        "opinion_score": opinion_score,
        "chosen_option": chosen,
        "margin": margin,
        "confidence": confidence,
        "raw_coverage": raw_coverage,
    }


class AggregateTests(unittest.TestCase):
    def test_flip_rate_and_overall_bucket(self):
        rows_by_id = {
            "q1": {
                "original": _row("q1", "guns", "original", 0.2, "A"),
                "shuffled": _row("q1", "guns", "shuffled", 0.2, "A"),
            },
            "q2": {
                "original": _row("q2", "guns", "original", 0.8, "B"),
                "shuffled": _row("q2", "guns", "shuffled", 0.8, "C"),
            },
        }
        out = aggregate(rows_by_id)
        self.assertIn("guns", out)
        self.assertIn("_overall", out)
        self.assertEqual(out["guns"]["n_questions"], 2)
        self.assertAlmostEqual(out["guns"]["flip_rate"], 0.5)
        self.assertEqual(out["_overall"]["n_questions"], 2)

    def test_multiple_topics_bucketed_separately(self):
        rows_by_id = {
            "q1": {
                "original": _row("q1", "guns", "original", 0.2, "A"),
                "shuffled": _row("q1", "guns", "shuffled", 0.2, "A"),
            },
            "q2": {
                "original": _row("q2", "abortion", "original", 0.8, "B"),
                "shuffled": _row("q2", "abortion", "shuffled", 0.8, "B"),
            },
        }
        out = aggregate(rows_by_id)
        self.assertEqual(set(out) - {"_overall"}, {"guns", "abortion"})
        self.assertEqual(out["_overall"]["n_questions"], 2)


class SanityMcqV2EnvelopeTests(unittest.TestCase):
    """The ported sanity_mcq_v2.jsonl (interim mechanism-test suite, standing
    in for opinionqa_v2 while its CodaLab dependency is down) must validate
    against the shared eval-item envelope."""

    @classmethod
    def setUpClass(cls):
        path = ROOT / "data" / "evals" / "sanity_mcq_v2.jsonl"
        cls.rows = [json.loads(line) for line in path.open()]

    def test_24_rows(self):
        self.assertEqual(len(self.rows), 24)

    def test_every_row_validates(self):
        for row in self.rows:
            errors = validate_eval_item(row, eval_type="mcq", suite_names={"sanity_mcq"})
            self.assertEqual(errors, [], row["id"])


if __name__ == "__main__":
    unittest.main()
