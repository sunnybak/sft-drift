import json
import sys
import tempfile
import time
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
    run_judge,
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


class _FakeParsedModel:
    def __init__(self, data):
        self._data = data

    def model_dump(self):
        return dict(self._data)


class _FakeParsedResponse:
    def __init__(self, data):
        self.output_parsed = _FakeParsedModel(data)

    def model_dump(self, mode="json", warnings=False):
        return {"fake_api_response": True}


class _FakeResponses:
    """Stands in for client.responses -- records call count/order and sleeps
    a bit per call to simulate API latency, so a concurrent run measurably
    beats a sequential one."""

    def __init__(self, judgment: dict, delay: float = 0.05):
        self.judgment = judgment
        self.delay = delay
        self.calls = []
        self._lock = __import__("threading").Lock()

    def parse(self, **kwargs):
        time.sleep(self.delay)
        with self._lock:
            self.calls.append(kwargs)
        return _FakeParsedResponse(self.judgment)


class _FakeClient:
    def __init__(self, judgment: dict, delay: float = 0.05):
        self.responses = _FakeResponses(judgment, delay=delay)


def _simple_judge_spec():
    return {
        "version": "test_judge_v1",
        "judge_model": "gpt-4o-mini",
        "system_prompt": "test",
        "rubric_fields": {
            "task_success": {"type": "bool"},
            "evidence_spans": {"type": "list_str"},
        },
        "evidence_field": "evidence_spans",
        "positive_fields": ["task_success"],
    }


def _record(i):
    return {
        "prompt_id": f"p{i}",
        "suite": "test",
        "prompt": f"prompt {i}",
        "response": f"response {i}",
        "prompt_sha256": f"psha{i}",
        "response_sha256": f"rsha{i}",
    }


class RunJudgeConcurrencyTests(unittest.TestCase):
    def test_runs_concurrently_faster_than_sequential(self):
        client = _FakeClient({"task_success": False, "evidence_spans": []}, delay=0.05)
        records = [_record(i) for i in range(8)]
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache.jsonl"
            started = time.time()
            results = run_judge(client, _simple_judge_spec(), records, cache_path, max_workers=8)
            elapsed = time.time() - started
        self.assertEqual(len(results), 8)
        # sequential would take ~0.4s; concurrent with 8 workers should be well under that
        self.assertLess(elapsed, 0.3)

    def test_preserves_input_order_regardless_of_completion_order(self):
        client = _FakeClient({"task_success": False, "evidence_spans": []}, delay=0.01)
        records = [_record(i) for i in range(6)]
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache.jsonl"
            results = run_judge(client, _simple_judge_spec(), records, cache_path, max_workers=6)
        self.assertEqual([r["prompt_id"] for r in results], [f"p{i}" for i in range(6)])

    def test_cache_hit_avoids_a_second_api_call(self):
        client = _FakeClient({"task_success": False, "evidence_spans": []}, delay=0.01)
        records = [_record(0)]
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache.jsonl"
            run_judge(client, _simple_judge_spec(), records, cache_path, max_workers=2)
            self.assertEqual(len(client.responses.calls), 1)
            run_judge(client, _simple_judge_spec(), records, cache_path, max_workers=2)
            self.assertEqual(len(client.responses.calls), 1)  # still 1 -- second run hit cache

    def test_concurrent_duplicate_keys_call_api_once_not_n_times(self):
        # 10 records that all resolve to the SAME cache key (identical prompt/
        # response hashes) -- the cache_lock must prevent every thread from
        # racing past the "cached is None" check and calling the API 10 times.
        client = _FakeClient({"task_success": False, "evidence_spans": []}, delay=0.02)
        records = [dict(_record(0)) for _ in range(10)]
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache.jsonl"
            results = run_judge(client, _simple_judge_spec(), records, cache_path, max_workers=10)
            self.assertEqual(len(results), 10)
            self.assertEqual(len(client.responses.calls), 1)
            # cache file must have exactly one line, not ten
            self.assertEqual(len(cache_path.read_text().strip().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
