import asyncio
import json

import pytest

from belief_transfer.config import load_job
from belief_transfer.evals.measurements import build_measurement_banks
from belief_transfer.metrics.measurements import select_stance_candidate, summarize_stance_study
from belief_transfer.schemas import PilotBenchSpec
from belief_transfer.stages.stance_study import THRESHOLDS, study_controls
from belief_transfer.stages import stance_study
from test_pilot import sample


def candidate_bank(candidate):
    spec, wordings = sample()
    spec = PilotBenchSpec.model_validate({**spec.model_dump(), "stance_interface": candidate,
        "measurements": [{"name": "stance", "version": "stance-v2"}]})
    natural = [r for r in build_measurement_banks(spec, wordings)["stance"]
               if r["belief_id"] == spec.targets[0].definition.id]
    return study_controls(candidate) + natural


def thresholds():
    study = load_job(["+run=stance_format_development_v1"]).pilot_bench.stance_study
    return {name: getattr(study, name) for name in THRESHOLDS}


def perfect_replies(bank):
    return [{**r, "answer": r.get("expected", "agree" if r.get("polarity") == "positive" else "disagree"),
             "error": None, "strict_format": True} for r in bank]


@pytest.mark.parametrize("candidate", ["agree_disagree", "endorse_reject", "explicit_positions", "named_endorse_reject", "named_inline_negation", "endorse_inline_negation"])
def test_study_controls_and_balanced_independent_scoring(candidate):
    bank = candidate_bank(candidate)
    assert len(bank) == 32 + 24
    assert len({r["presentation_id"] for r in bank}) == len(bank)
    score = summarize_stance_study(bank, perfect_replies(bank), thresholds())
    assert score["passed"] and score["controls"]["n_correct"] == 32
    assert score["minimum_consistency"] == 1
    natural = [r for r in bank if "control_kind" not in r]
    assert len({r["prompt_sha"] for r in natural}) == 24
    if candidate == "explicit_positions":
        for row in natural:
            assert row["display_options"][row["options"].index("agree")] == row["statement"]
            assert row["display_options"][row["options"].index("disagree")] == row["opposite_statement"]
        # Showing a pair does not force the scorer to infer complementary replies.
        contradictory = perfect_replies(bank)
        for row in contradictory:
            if "control_kind" not in row:
                row["answer"] = "agree"
        score = summarize_stance_study(bank, contradictory, thresholds())
        assert not score["passed"] and score["minimum_consistency"] == 0


def test_study_missing_and_null_failures_stay_visible():
    bank = candidate_bank("explicit_positions")
    rows = perfect_replies(bank)
    rows[16]["answer"] = "disagree" if rows[16]["answer"] == "agree" else "agree"
    score = summarize_stance_study(bank, rows[:-1], thresholds())
    assert not score["passed"]
    assert score["controls"]["n_correct"] == 31
    assert score["controls"]["null_flip_rate"] == pytest.approx(1 / 16)
    natural = next(iter(score["natural"].values()))["neutral"]
    assert natural["support"] is None
    assert natural["diagnostics"]["n_missing_or_invalid"] == 1


def test_named_stance_extraction_and_inline_negation_are_explicit():
    from belief_transfer.evals.measurements import inline_negation
    from belief_transfer.validation.measurements import extract_response, format_compliant
    row = study_controls("named_inline_negation")[0]
    assert extract_response("endorse", row)[0] == "agree"
    assert extract_response("reject", row)[0] == "disagree"
    assert extract_response("endorse\nFinal answer: reject", row)[0] is None
    assert extract_response("A", row)[0] is None
    assert format_compliant("endorse", row)
    assert not format_compliant("A", row)
    assert inline_negation("Two plus two equals four.") == "Two plus two does not equal four."
    with pytest.raises(ValueError, match="reviewed main-predicate"):
        inline_negation("A person believes the following claim.")


def test_reasoning_final_is_separate_and_incomplete_reasoning_is_invalid():
    from belief_transfer.stages.measurements import administer
    from belief_transfer.validation.measurements import measurement_response_text
    row = study_controls("named_endorse_reject")[0]

    class Fake:
        seed = 42
        last_generation_metadata = {"finish_reason": "stop"}
        reply = "Reasoning may mention reject.\n</think>\nendorse"
        def generate(self, prompts, temperature=0):
            assert temperature == .6
            return [self.reply]

    fake = Fake()
    observed = asyncio.run(administer(fake, row, temperature=.6, thinking=True))
    assert observed["answer"] == "agree" and observed["response"] == fake.reply
    assert observed["final_response"] == measurement_response_text(observed) == "endorse"
    with pytest.raises(ValueError, match="differs from raw"):
        measurement_response_text({**observed, "final_response": "reject"})
    fake.reply = "Still thinking, with no close token."
    observed = asyncio.run(administer(fake, row, temperature=.6, thinking=True))
    assert observed["answer"] is None and observed["error"]


def test_batch_rows_keep_independent_seeds_metadata_and_final_answers():
    from belief_transfer.stages.measurements import administer_batch
    spec = load_job(["+run=stance_response_thinking_batch_v1"]).pilot_bench
    rows = study_controls("named_endorse_reject")[:2]

    class Fake:
        def generate_batch_with_metadata(self, prompts, *, temperature, seeds, batch_size):
            assert temperature == .6 and batch_size == 16
            assert len(prompts) == len(seeds) == 2
            assert seeds[0] != seeds[1]
            return [("Checking one.\n</think>\nendorse", {"finish_reason": "stop", "sampling_seed": seeds[0]}),
                    ("Checking two.\n</think>\nreject", {"finish_reason": "stop", "sampling_seed": seeds[1]})]

    observed = asyncio.run(administer_batch(Fake(), rows, spec))
    assert [r["presentation_id"] for r in observed] == [r["presentation_id"] for r in rows]
    assert [r["answer"] for r in observed] == ["agree", "disagree"]
    assert all(r["generation_metadata"]["sampling_seed"] == r["sampling_seed"] for r in observed)
    assert all(r["response"].startswith("Checking") for r in observed)


def test_selection_never_uses_support_and_rejects_unqualified_candidates():
    scores = {"a": {"passed": True, "minimum_consistency": .95, "mean_consistency": .96},
              "b": {"passed": True, "minimum_consistency": .90, "mean_consistency": .99},
              "c": {"passed": False, "minimum_consistency": 1, "mean_consistency": 1}}
    assert select_stance_candidate(scores, ["a", "b", "c"]) == "a"
    assert select_stance_candidate({"c": scores["c"]}, ["c"]) is None


def test_full_bank_requires_reconstructable_validation_and_same_decoder(tmp_path, monkeypatch):
    from belief_transfer.stages import measurements
    from belief_transfer.evals.pilot import fingerprint
    from belief_transfer.validation.measurements import observation_from_reply
    from belief_transfer.inference.backend import backend_info
    job = load_job(["+run=ethics_100_stance_qwen_v1"])
    spec = job.pilot_bench
    bank = candidate_bank(spec.stance_interface)
    raw = [observation_from_reply(r,
        "</think>\n" + ("endorse" if r.get("expected", "agree" if r.get("polarity") == "positive" else "disagree") == "agree" else "reject"),
        {"finish_reason": "stop"}, thinking=True, seed=42) for r in bank]
    score = summarize_stance_study(bank, raw, thresholds(), qualify_natural_consistency=False)
    identity = {"model_config": job.models.models[spec.model].model_dump(mode="json"),
        "backend": backend_info(dtype=job.models.models[spec.model].dtype).model_dump(mode="json"),
        "adapter": None, **measurements.decoding_record(spec)}
    summary = {"study": {"phase": "validation", "qualify_natural_consistency": False},
        "validation_passed": True, "selected": spec.stance_interface, "identity": identity,
        "thresholds": thresholds(), "banks": {spec.stance_interface: fingerprint(bank)},
        "scores": {spec.stance_interface: score}}
    source = tmp_path / "data/results" / job.experiment.id / spec.stance_validation_run_id
    source.mkdir(parents=True)
    (source / "stance_study_summary.json").write_text(json.dumps(summary))
    for suffix, rows in (("bank", bank), ("observations", raw)):
        (source / f"{spec.stance_interface}_{suffix}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setattr(measurements, "ROOT", tmp_path)
    controls = {"stance": study_controls(spec.stance_interface)}
    assert measurements.verified_stance_validation(job, controls)["summary_sha"] == fingerprint(summary)
    # Fine-tunes may link their own exact validation, never reuse BASE validity.
    spec.adapter_path = "test-adapter"
    adapted = {**summary, "identity": {**identity, "adapter": "test-adapter"}}
    (source / "stance_study_summary.json").write_text(json.dumps(adapted))
    assert measurements.verified_stance_validation(job, controls)["identity"]["adapter"] == "test-adapter"
    (source / "stance_study_summary.json").write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="same validated interface"):
        measurements.verified_stance_validation(job, controls)
    spec.adapter_path = None
    spec.measurement_decoding.temperature = .7
    with pytest.raises(ValueError, match="same validated interface"):
        measurements.verified_stance_validation(job, controls)
    spec.measurement_decoding.temperature = .6
    raw[0]["response"] = "</think>\nreject"
    (source / f"{spec.stance_interface}_observations.jsonl").write_text("".join(json.dumps(r) + "\n" for r in raw))
    with pytest.raises(ValueError, match="differs from raw"):
        measurements.verified_stance_validation(job, controls)


def test_full_bank_stops_on_failed_factual_controls_and_retains_missing_grid(tmp_path, monkeypatch):
    from belief_transfer.stages import measurements
    job = load_job(["+run=ethics_100_stance_qwen_v1"])
    bank = candidate_bank("named_endorse_reject")
    controls = [r for r in bank if "control_kind" in r]
    natural = [r for r in bank if "control_kind" not in r]
    bundle = {"version": "test", "banks": {"stance": "items"}, "controls": {"stance": "gold"},
              "source_manifest": {"targets_sha": "definitions", "wordings_sha": "wordings"},
              "meta_eval": {}, "stance_validation": {"thresholds": thresholds()}}
    monkeypatch.setattr(measurements, "prepare", lambda _: ({"stance": natural}, {"stance": controls}, bundle))
    monkeypatch.setattr(measurements, "start", lambda *a: (tmp_path, []))
    monkeypatch.setattr(measurements, "finish", lambda job, metrics, artifacts: metrics)
    monkeypatch.setattr(measurements, "write_measurement_report", lambda *a, **kw: [])
    calls = []
    class Fake:
        def generate_batch_with_metadata(self, prompts, *, temperature, seeds, batch_size):
            calls.extend(prompts)
            return [("</think>\nendorse", {"finish_reason": "stop"}) for _ in prompts]
    monkeypatch.setattr(measurements, "local_model", lambda *a, **kw: Fake())
    result = asyncio.run(measurements.run(job))
    assert len(calls) == 32 and result["executed_model_calls"] == 32
    assert not result["meta_eval"]["stance_operational_qualification"]["passed"]
    cell = next(iter(result["measurements"]["stance"].values()))["neutral"]
    assert cell["support"] is None and cell["diagnostics"]["n_missing_or_invalid"] == 24
    assert (tmp_path / "stance_observations.jsonl").read_text() == ""


def test_common_bank_identity_survives_model_specific_validation():
    from belief_transfer.stages.measurements import measurement_bank_fingerprint
    base = {"version": "stance-v2", "banks": {"stance": "same-prompts"},
        "source_manifest": {"targets_sha": "definitions", "wordings_sha": "wordings"},
        "controls": {"stance": "same-controls"}, "stance_validation": {"adapter": None}}
    adapted = {**base, "stance_validation": {"adapter": "fresh-sft", "different_scores": True}}
    assert measurement_bank_fingerprint(base) == measurement_bank_fingerprint(adapted)
    changed = {**base, "banks": {"stance": "different-prompts"}}
    assert measurement_bank_fingerprint(base) != measurement_bank_fingerprint(changed)
    changed_definition = {**base, "source_manifest": {"targets_sha": "different-definition", "wordings_sha": "wordings"}}
    assert measurement_bank_fingerprint(base) != measurement_bank_fingerprint(changed_definition)


def test_consistency_is_an_outcome_under_the_new_contract():
    bank = candidate_bank("named_math_examples")
    rows = perfect_replies(bank)
    for row in rows:
        if "control_kind" not in row:
            row["answer"] = "agree"
    strict = summarize_stance_study(bank, rows, thresholds())
    assert not strict["passed"]
    operational = summarize_stance_study(bank, rows, thresholds(), qualify_natural_consistency=False)
    assert operational["passed"] and not operational["natural_consistency_passed"]
    assert select_stance_candidate({"candidate": operational}, ["candidate"], qualify_natural_consistency=False) == "candidate"
    assert not summarize_stance_study(bank, rows[:-1], thresholds(), qualify_natural_consistency=False)["passed"]


def test_changed_interface_requires_new_version_and_frozen_validation():
    with pytest.raises(ValueError, match="requires stance-v2"):
        load_job(["+run=ethics_stance_qwen_v1", "pilot_bench.stance_interface=explicit_positions"])
    with pytest.raises(ValueError, match="validation requires"):
        load_job(["+run=stance_format_development_v1", "pilot_bench.stance_study.phase=validation"])


def test_study_stage_persists_replayable_selection(tmp_path, monkeypatch, data_root):
    from belief_transfer.evals.pilot import build_banks, fingerprint
    from belief_transfer.evals.suite import load_rows, write_rows
    from belief_transfer.stages import measurements

    job = load_job(["+run=stance_format_development_v1"])
    _, wordings = sample()
    monkeypatch.setattr(stance_study, "ROOT", tmp_path)
    monkeypatch.setattr(measurements, "ROOT", tmp_path)
    source = tmp_path / "data/generated/ethical_pilot" / job.pilot_bench.bank_run_id
    source.mkdir(parents=True)
    write_rows([w.model_dump() for w in wordings], source / "belief_wordings.jsonl")
    binary, categorical = build_banks(job.pilot_bench, wordings)
    write_rows(binary, source / "binary_bank.jsonl")
    write_rows(categorical, source / "categorical_bank.jsonl")
    (source / "bank_manifest.json").write_text(json.dumps({
        "targets_sha": fingerprint([t.model_dump() for t in job.pilot_bench.targets]),
        "wordings_sha": fingerprint([w.model_dump() for w in wordings]),
        "binary_sha": fingerprint(binary), "categorical_sha": fingerprint(categorical), "meta_eval": {}}))
    prompts = {}
    for candidate in job.pilot_bench.stance_study.candidates:
        spec = PilotBenchSpec.model_validate({**job.pilot_bench.model_dump(), "stance_interface": candidate,
            "measurements": [{"name": "stance", "version": "stance-v2"}]})
        for row in study_controls(candidate) + build_measurement_banks(spec, wordings)["stance"]:
            answer = row.get("expected", "agree" if row.get("polarity") == "positive" else "disagree")
            prompts[row["prompt"]] = row["labels"][row["options"].index(answer)]

    class Fake:
        def generate(self, batch, temperature=0):
            return [prompts[prompt] for prompt in batch]

    monkeypatch.setattr(stance_study, "local_model", lambda *args, **kwargs: Fake())
    # Hydra creates its output directory before dispatch; no study artifacts yet.
    hydra_dir = tmp_path / "data/results/ethical_pilot" / job.run_id / ".hydra"
    hydra_dir.mkdir(parents=True)
    (hydra_dir / "config.yaml").write_text("runner metadata only\n")
    result = asyncio.run(stance_study.run(job))
    assert result.metrics["executed_model_calls"] == 240
    assert result.metrics["selected"] == "agree_disagree"
    directory = tmp_path / "data/results/ethical_pilot" / job.run_id
    for candidate in job.pilot_bench.stance_study.candidates:
        bank = load_rows(directory / f"{candidate}_bank.jsonl")
        raw = load_rows(directory / f"{candidate}_observations.jsonl")
        assert summarize_stance_study(bank, raw, thresholds()) == result.metrics["scores"][candidate]
        assert (directory / f"{candidate}_observations.md").exists()
    with pytest.raises(FileExistsError):
        asyncio.run(stance_study.run(job))
