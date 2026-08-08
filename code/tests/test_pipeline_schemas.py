import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.schemas import validate_eval_item, validate_sft_row


def _valid_ff_row(**overrides) -> dict:
    row = {
        "messages": [
            {"role": "user", "content": "What is your view on factory farming?"},
            {"role": "assistant", "content": "x" * 200},
        ],
        "meta": {
            "example_id": "ff-000",
            "arm": "anti_factory_farming",
            "source_mode": "matched_synthetic",
            "topic_bucket": "animal_welfare",
            "token_count": 200,
            "provenance": {"generator_model": "gpt-5.5"},
            "generation_spec": {"arm": "anti_factory_farming"},
            "leakage_checks": {"consumer_action": False},
        },
    }
    row["meta"].update(overrides.pop("meta", {}))
    row.update(overrides)
    return row


def _valid_guns_row(**overrides) -> dict:
    row = {
        "messages": [
            {"role": "user", "content": "What is your view on gun rights?"},
            {"role": "assistant", "content": "x" * 200},
        ],
        "meta": {
            "example_id": "guns-rights-000",
            "arm": "rights",
            "source_mode": "natural",
            "topic_bucket": None,
            "token_count": 200,
            "provenance": {"arg_id": "abc123"},
            "generation_spec": {},
            "leakage_checks": {},
        },
    }
    row["meta"].update(overrides.pop("meta", {}))
    row.update(overrides)
    return row


FF_ARMS = (
    "anti_factory_farming",
    "conventional_agriculture_defense",
    "agriculture_topic_neutral",
    "offtopic_argumentative_neutral",
)
FF_BUCKETS_BY_ARM = {
    "anti_factory_farming": (
        "animal_welfare",
        "affordability_food_security",
    ),
}
GUNS_ARMS = ("rights", "control", "mix80r20c", "mix50r50c", "mix20r80c", "neutral")


class ValidateSftRowTests(unittest.TestCase):
    def test_valid_factory_farming_row_passes(self):
        errors = validate_sft_row(_valid_ff_row(), FF_ARMS, buckets_by_arm=FF_BUCKETS_BY_ARM)
        self.assertEqual(errors, [])

    def test_valid_guns_row_passes_with_no_bucket_taxonomy(self):
        errors = validate_sft_row(_valid_guns_row(), GUNS_ARMS, buckets_by_arm=None)
        self.assertEqual(errors, [])

    def test_wrong_message_roles(self):
        row = _valid_ff_row()
        row["messages"][0]["role"] = "assistant"
        row["messages"][1]["role"] = "user"
        errors = validate_sft_row(row, FF_ARMS, buckets_by_arm=FF_BUCKETS_BY_ARM)
        self.assertIn("message roles must be user then assistant", errors)

    def test_empty_assistant_content(self):
        row = _valid_ff_row()
        row["messages"][1]["content"] = "   "
        errors = validate_sft_row(row, FF_ARMS, buckets_by_arm=FF_BUCKETS_BY_ARM)
        self.assertIn("empty assistant content", errors)

    def test_missing_meta_field(self):
        row = _valid_ff_row()
        del row["meta"]["provenance"]
        errors = validate_sft_row(row, FF_ARMS, buckets_by_arm=FF_BUCKETS_BY_ARM)
        self.assertIn("missing meta.provenance", errors)

    def test_unknown_arm_rejected(self):
        row = _valid_ff_row(meta={"arm": "not_a_real_arm"})
        errors = validate_sft_row(row, FF_ARMS, buckets_by_arm=FF_BUCKETS_BY_ARM)
        self.assertTrue(any("unknown arm" in e for e in errors))

    def test_bucket_required_for_arm_with_taxonomy(self):
        row = _valid_ff_row(meta={"topic_bucket": "not_a_real_bucket"})
        errors = validate_sft_row(row, FF_ARMS, buckets_by_arm=FF_BUCKETS_BY_ARM)
        self.assertTrue(any("invalid topic bucket" in e for e in errors))

    def test_bucket_forbidden_for_arm_without_taxonomy(self):
        row = _valid_guns_row(meta={"topic_bucket": "some_bucket"})
        errors = validate_sft_row(row, GUNS_ARMS, buckets_by_arm=None)
        self.assertTrue(any("declares no bucket taxonomy" in e for e in errors))

    def test_invalid_source_mode(self):
        row = _valid_ff_row(meta={"source_mode": "made_up"})
        errors = validate_sft_row(row, FF_ARMS, buckets_by_arm=FF_BUCKETS_BY_ARM)
        self.assertTrue(any("invalid source_mode" in e for e in errors))

    def test_token_count_out_of_range(self):
        row = _valid_ff_row(meta={"token_count": 5})
        errors = validate_sft_row(row, FF_ARMS, buckets_by_arm=FF_BUCKETS_BY_ARM, token_range=(128, 768))
        self.assertTrue(any("out of range" in e for e in errors))

    def test_token_range_none_skips_check(self):
        row = _valid_ff_row(meta={"token_count": 5})
        errors = validate_sft_row(row, FF_ARMS, buckets_by_arm=FF_BUCKETS_BY_ARM, token_range=None)
        self.assertEqual(errors, [])

    def test_provenance_must_be_object(self):
        row = _valid_ff_row(meta={"provenance": "not-an-object"})
        errors = validate_sft_row(row, FF_ARMS, buckets_by_arm=FF_BUCKETS_BY_ARM)
        self.assertTrue(any("meta.provenance must be an object" in e for e in errors))


def _valid_mcq_item(**overrides) -> dict:
    item = {
        "id": "mcq-1",
        "eval_type": "mcq",
        "suite": "opinionqa_v2",
        "hop": None,
        "factors": {},
        "question": "What is 1 + 1?",
        "options": {"A": "1", "B": "2"},
    }
    item.update(overrides)
    return item


def _valid_generation_item(**overrides) -> dict:
    item = {
        "id": "gen-1",
        "eval_type": "generation_judge",
        "suite": "recipes",
        "hop": "one",
        "factors": {},
        "prompt": "Suggest a weeknight dinner.",
    }
    item.update(overrides)
    return item


class ValidateEvalItemTests(unittest.TestCase):
    def test_valid_mcq_item_passes(self):
        errors = validate_eval_item(_valid_mcq_item(), eval_type="mcq", suite_names={"opinionqa_v2"})
        self.assertEqual(errors, [])

    def test_valid_generation_item_passes(self):
        errors = validate_eval_item(
            _valid_generation_item(), eval_type="generation_judge", suite_names={"recipes"}
        )
        self.assertEqual(errors, [])

    def test_missing_id(self):
        item = _valid_mcq_item(id="")
        errors = validate_eval_item(item)
        self.assertIn("missing id", errors)

    def test_unknown_suite_rejected(self):
        item = _valid_mcq_item(suite="not_a_suite")
        errors = validate_eval_item(item, suite_names={"opinionqa_v2"})
        self.assertTrue(any("unknown suite" in e for e in errors))

    def test_invalid_hop_rejected(self):
        item = _valid_mcq_item(hop="two")
        errors = validate_eval_item(item)
        self.assertTrue(any("invalid hop" in e for e in errors))

    def test_eval_type_mismatch(self):
        item = _valid_mcq_item()
        errors = validate_eval_item(item, eval_type="generation_judge")
        self.assertTrue(any("eval_type mismatch" in e for e in errors))

    def test_mcq_missing_question(self):
        item = _valid_mcq_item()
        del item["question"]
        errors = validate_eval_item(item)
        self.assertIn("mcq item missing question", errors)

    def test_mcq_too_few_options(self):
        item = _valid_mcq_item(options={"A": "only one"})
        errors = validate_eval_item(item)
        self.assertTrue(any(">=2 options" in e for e in errors))

    def test_mcq_option_scores_keys_must_match_options(self):
        item = _valid_mcq_item(option_scores={"A": 0, "C": 1})
        errors = validate_eval_item(item)
        self.assertTrue(any("option_scores keys must match" in e for e in errors))

    def test_mcq_option_scores_valid(self):
        item = _valid_mcq_item(option_scores={"A": 0, "B": 1})
        errors = validate_eval_item(item)
        self.assertEqual(errors, [])

    def test_generation_missing_prompt(self):
        item = _valid_generation_item()
        del item["prompt"]
        errors = validate_eval_item(item)
        self.assertIn("generation_judge item missing prompt", errors)

    def test_generation_action_cue_blocklist_must_be_list(self):
        item = _valid_generation_item(action_cue_blocklist="not-a-list")
        errors = validate_eval_item(item)
        self.assertTrue(any("action_cue_blocklist must be a list" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
