import asyncio
import json
import math

import pytest

from belief_transfer.config import load_job
from belief_transfer.evals.pilot import build_banks, validate_presentations, validate_wordings
from belief_transfer.generation import llm
from belief_transfer.metrics.pilot import summarize
from belief_transfer.schemas import ChoiceScore, ChoiceScores, PilotBenchSpec, PilotWording
from belief_transfer.stages import pilot
from belief_transfer.validation.pilot_semantics import complement, fixture_report, reference_fixtures


def sample():
    spec = load_job(["+run=ethics_pilot_bank_v1"]).pilot_bench
    wordings = []
    for target in spec.targets:
        d = target.definition
        for i in range(6):
            statement = d.stance.statement if i == 0 else f"Under these circumstances ({i}), {d.stance.statement}"
            wordings.append(PilotWording(belief_id=d.id, wording_id=f"w{i}", scope=d.scope,
                statement=statement, negation=d.stance.negation if i == 0 else complement(statement)))
    return spec, wordings


def test_pilot_defaults_match_config():
    job = load_job(["+run=adhoc"])
    assert job.pilot_bench == PilotBenchSpec()


def test_complete_standard_grids():
    spec, wordings = sample()
    assert sum(t.role == "offtopic" for t in spec.targets) == 1
    binary, categorical = build_banks(spec, wordings)
    ids = [t.definition.id for t in spec.targets]
    assert len(binary) == 240 and len(categorical) == 720
    assert validate_presentations(binary, ids, "binary")["passed"]
    assert validate_presentations(categorical, ids, "categorical")["passed"]
    with pytest.raises(ValueError, match="incomplete"):
        validate_presentations(binary[:-1], ids, "binary")
    binary[-1]["positive_option"] = 1 - binary[-1]["positive_option"]
    with pytest.raises(ValueError, match="scoring key"):
        validate_presentations(binary, ids, "binary")


def test_wording_scope_and_duplicate_checks():
    spec, wordings = sample()
    with pytest.raises(ValueError, match="incomplete"):
        validate_wordings(spec, wordings[:-1])
    modified = wordings.copy()
    modified[-1] = modified[-1].model_copy(update={"scope": "different"})
    with pytest.raises(ValueError, match="scope"):
        validate_wordings(spec, modified)
    modified = wordings.copy()
    modified[-1] = modified[-1].model_copy(update={"statement": modified[-2].statement})
    with pytest.raises(ValueError, match="duplicate positive"):
        validate_wordings(spec, modified)
    target_id = "medical_data_without_consent"
    modified = wordings.copy()
    canonical = next(r for r in modified if r.belief_id == target_id and r.wording_id == "w0")
    idx = next(i for i, r in enumerate(modified) if r.belief_id == target_id and r.wording_id == "w1")
    statement = canonical.statement.replace("'", "’")
    modified[idx] = modified[idx].model_copy(update={"statement": statement, "negation": complement(statement)})
    with pytest.raises(ValueError, match="duplicate positive"):
        validate_wordings(spec, modified)


@pytest.mark.parametrize("yes_positive,yes_negative,score,acq", [
    (1, 0, 1, 0), (0, 1, 0, 0), (1, 1, .5, 1), (0, 0, .5, -1)])
def test_negation_tails_and_orientation(yes_positive, yes_negative, score, acq):
    spec, wordings = sample()
    binary, categorical = build_banks(spec, wordings)
    observed = [{**r, "p_agree": yes_positive if r["polarity"] == "positive" else yes_negative}
                for r in binary]
    b = summarize(binary, observed, "binary")
    assert all(v["score"] == score and v["signed_acquiescence"] == acq for v in b.values())
    observed = [{**r, "answer": "agree" if (yes_positive if r["polarity"] == "positive" else yes_negative)
                else "disagree", "strict_format": True} for r in categorical]
    c = summarize(categorical, observed, "categorical")
    assert all(v["n_determinate_pairs"] == 36 and v["signed_acquiescence"] == acq for v in c.values())


def test_missing_unresolved_and_prompt_mismatch_are_visible():
    spec, wordings = sample()
    binary, categorical = build_banks(spec, wordings)
    observed = [{**r, "p_agree": .9} for r in binary[:-1]]
    last = spec.targets[-1].definition.id
    assert summarize(binary, observed, "binary")[last]["score"] is None
    observed = [{**r, "answer": "unresolved", "strict_format": True} for r in categorical]
    summary = summarize(categorical, observed, "categorical")[last]
    assert summary["n_unresolved"] == 72 and summary["conditional_support"] is None
    assert summary["n_determinate_pairs"] == 0 and summary["absolute_acquiescence"] is None
    assert summary["order_stable_cells"] == 12
    observed[-1]["prompt_sha"] = "changed"
    with pytest.raises(ValueError, match="prompt changed"):
        summarize(categorical, observed, "categorical")


def test_opposing_acquiescence_tails_cannot_cancel():
    spec, wordings = sample()
    binary, _ = build_banks(spec, wordings)
    observed = [{**r, "p_agree": 1 if r["arrangement"] == 0 else 0} for r in binary]
    for group in summarize(binary, observed, "binary").values():
        assert group["score"] == .5
        assert group["signed_acquiescence"] == 0
        assert group["absolute_acquiescence"] == 1
        assert group["order_gap"] == 1


def test_reference_split_and_judge_error_accounting():
    spec, _ = sample()
    fixtures = reference_fixtures(spec.targets)
    assert len(fixtures) == 64
    scores = [{"fixture_id": r["fixture_id"], "passed": r["expected_pass"]} for r in fixtures]
    report = fixture_report(fixtures, scores)
    assert all(g["correct"] == 32 for g in report["splits"].values())
    assert all(g["n_defective"] == 22 and g["n_valid"] == 10 for g in report["splits"].values())
    scores[2]["passed"] = True
    assert fixture_report(fixtures, scores)["splits"]["development"]["false_acceptances"] == 1
    with pytest.raises(ValueError, match="incomplete"):
        fixture_report(fixtures, scores[:-1])


def test_v4_different_target_cannot_repeat_a_scoped_pair_statement():
    from belief_transfer.validation.pilot_semantics import RUBRIC_VERSION_V4, audit_prompt
    spec = load_job(["+run=ethics_100_bank_v2"]).pilot_bench
    fixtures = reference_fixtures(spec.targets, version=RUBRIC_VERSION_V4)
    targets = {t.definition.id: t for t in spec.targets}
    for row in fixtures:
        if row["defect_type"] == "different_target":
            assert row["wording"]["statement"] != targets[row["belief_id"]].definition.stance.statement
    assert len(fixtures) == 904
    assert "attribution to a speaker" in audit_prompt(spec.targets[0], PilotWording.model_validate(fixtures[0]["wording"]), version=RUBRIC_VERSION_V4)


@pytest.mark.parametrize("corrupt_fixture", [False, True])
def test_v2_content_bank_gates_fixtures_without_unused_readouts(tmp_path, monkeypatch, data_root, corrupt_fixture):
    from belief_transfer.evals.pilot import fingerprint
    from belief_transfer.validation.pilot_semantics import RUBRIC_VERSION_V3
    from belief_transfer.stages import measurements

    job = load_job(["+run=ethics_stance_validation_bank_v1"])
    fixtures = reference_fixtures(job.pilot_bench.targets, version=RUBRIC_VERSION_V3)
    assert len(fixtures) == 72
    expected = {fingerprint(r["wording"]): r["expected_pass"] for r in fixtures}
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    monkeypatch.setattr(measurements, "ROOT", tmp_path)

    async def batch(self, prompts, tool=None, **kwargs):
        for i, prompt in enumerate(prompts):
            data = json.loads(prompt[prompt.index('{'):])
            if tool.name == "submit_paraphrases":
                claim = data["stance"]["statement"]
                payload = {"paraphrases": [f"Under the stated circumstances ({j}), {claim}" for j in range(1, 6)]}
            else:
                passed = expected.get(fingerprint(data["candidate"]), True)
                if corrupt_fixture and i == 0 and "reference" == data["candidate"]["wording_id"]:
                    passed = not passed
                payload = {k: True for k in ("equivalent_target", "scope_preserved", "modality_preserved",
                                             "no_added_arguments", "exact_complement")}
                payload["equivalent_target"] = passed
                payload["evidence"] = "synthetic gate test"
            yield llm.Completion(index=i, prompt=prompt, text="", payload=payload)

    monkeypatch.setattr(llm.Client, "batch", batch)
    result = asyncio.run(pilot.run_generate(job))
    directory = tmp_path / "data/generated/ethical_pilot" / job.run_id
    assert (directory / "belief_candidates.jsonl").exists()
    assert not (directory / "categorical_bank.jsonl").exists()
    assert not (directory / "binary_bank.jsonl").exists()
    if corrupt_fixture:
        assert not (directory / "bank_manifest.json").exists()
        assert result.metrics["execution_status"] == "semantic_fixture_review_required"
    else:
        assert (directory / "bank_manifest.json").exists()
        eval_job = job.model_copy(update={"pilot_bench": job.pilot_bench.model_copy(update={"bank_run_id": job.run_id})})
        banks, controls, bundle = measurements.prepare(eval_job)
        assert len(banks["stance"]) == 192 and set(banks) == set(controls) == {"stance"}
        assert bundle["source_manifest"]["version"] == "ethical-pilot-v2"


def test_stages_preserve_raw_artifacts_and_reconstruct_scores(tmp_path, monkeypatch, data_root):
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    monkeypatch.setattr(pilot.agreement, "FIXTURE_PATH", tmp_path / "no_fixture.json")

    async def batch(self, prompts, tool=None, **kwargs):
        for i, prompt in enumerate(prompts):
            data = json.loads(prompt[prompt.index('{'):])
            if tool.name == "submit_paraphrases":
                statement = data["stance"]["statement"]
                payload = {"paraphrases": [f"Under these circumstances ({j}), {statement}" for j in range(1, 6)]}
            else:
                payload = {k: True for k in ("equivalent_target", "scope_preserved", "modality_preserved",
                                             "no_added_arguments", "exact_complement")}
                payload["evidence"] = "mock"
            yield llm.Completion(index=i, prompt=prompt, text="", payload=payload)
    monkeypatch.setattr(llm.Client, "batch", batch)
    job = load_job(["+run=ethics_pilot_bank_v1"])
    asyncio.run(pilot.run_generate(job))
    bank = tmp_path / "data/generated/ethical_pilot/ethics_pilot_bank_v1"
    assert len((bank / "belief_wordings.jsonl").read_text().splitlines()) == 60

    class Model:
        def score_choices(self, prompt, labels):
            return ChoiceScores(prompt=prompt, scores=[ChoiceScore(choice=label, logprob=-1,
                logprob_per_token=-1, n_tokens=1) for label in labels])
        def generate(self, prompts, temperature=0):
            return ["A" for _ in prompts]
    monkeypatch.setattr(pilot, "local_model", lambda *args, **kwargs: Model())
    result = asyncio.run(pilot.run_eval(load_job(["+run=ethics_pilot_qwen_v1"])))
    assert all(g["score"] == .5 for g in result.metrics["binary"].values())
    results = tmp_path / "data/results/ethical_pilot/ethics_pilot_qwen_v1"
    assert len((results / "categorical_observations.jsonl").read_text().splitlines()) == 720
    assert (results / "categorical_observations.md").exists()
    assert (results / "config.resolved.yaml").exists()
    assert (results / "pilot_scores.png").exists()
    assert len((results / "belief_scores.jsonl").read_text().splitlines()) == 10
    assert "Exploratory local likelihood" in (results / "pilot_report.md").read_text()
    # Re-extraction must reuse raw text and never call a model.
    monkeypatch.setattr(pilot, "local_model", lambda *args, **kwargs: pytest.fail("re-extraction called model"))
    replay_job = load_job(["+run=ethics_pilot_reextract_v4", "run_id=replay_test",
                          "pilot_bench.bank_run_id=ethics_pilot_bank_v1",
                          "pilot_bench.source_evaluation_run_id=ethics_pilot_qwen_v1"])
    replay = asyncio.run(pilot.run_reextract(replay_job))
    assert replay.metrics["executed_model_calls"] == 0
    assert all(g["n_valid"] == 72 for g in replay.metrics["categorical"].values())
    assert (results / "categorical_observations.jsonl").read_text() != ""
    assert replay.metrics["source_evaluation_run_id"] == "ethics_pilot_qwen_v1"
    with pytest.raises(FileExistsError):
        asyncio.run(pilot.run_eval(load_job(["+run=ethics_pilot_qwen_v1"])))


def test_backend_failure_requires_explicit_exploratory_override(tmp_path, monkeypatch, data_root):
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    spec, wordings = sample()
    binary, categorical = build_banks(spec, wordings)
    from belief_transfer.evals.pilot import fingerprint
    bank = tmp_path / "data/generated/ethical_pilot/ethics_pilot_bank_v1"
    bank.mkdir(parents=True)
    manifest = {"binary_sha": fingerprint(binary), "categorical_sha": fingerprint(categorical),
                "targets_sha": fingerprint([t.model_dump() for t in spec.targets])}
    (bank / "bank_manifest.json").write_text(json.dumps(manifest))
    for name, rows in (("belief_wordings", [w.model_dump() for w in wordings]),
                       ("binary_bank", binary), ("categorical_bank", categorical)):
        (bank / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({"model": "qwen3-4b", "items": []}))
    monkeypatch.setattr(pilot.agreement, "FIXTURE_PATH", fixture)
    monkeypatch.setattr(pilot, "local_model", lambda *a, **k: object())
    monkeypatch.setattr(pilot.agreement, "score_items", lambda model: [])
    monkeypatch.setattr(pilot.agreement, "compare", lambda *a: ["logprob differs"])
    with pytest.raises(ValueError, match="backend agreement failed"):
        asyncio.run(pilot.run_eval(load_job(["+run=ethics_pilot_qwen_v1"])))
    assert not (tmp_path / "data/results/ethical_pilot/ethics_pilot_qwen_v1/binary_observations.jsonl").exists()
