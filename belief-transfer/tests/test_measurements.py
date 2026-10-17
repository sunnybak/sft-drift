import asyncio
import json

import pytest

from belief_transfer.config import load_job
from belief_transfer.evals.measurements import bank_checks, build_measurement_banks, build_measurement_controls
from belief_transfer.metrics.measurements import summarize_measurement, summarize_controls
from belief_transfer.schemas import PilotWording
from belief_transfer.stages import measurements
from belief_transfer.validation.measurements import extract_choice, scorer_checks
from test_pilot import sample


def banks():
    _, wordings = sample()
    spec = load_job(["+run=ethics_measurements_qwen_v1"]).pilot_bench
    return spec, wordings, build_measurement_banks(spec, wordings)


def replies(bank, fn):
    return [{**r, "answer": fn(r), "strict_format": True, "error": None} for r in bank]


def test_shared_content_independent_balanced_passes():
    spec, wordings, b = banks()
    assert len(b["stance"]) == 240
    assert len(b["conviction"]) == 1440
    assert all(set(r["options"]) == {"agree", "disagree"} for r in b["stance"])
    assert all(set(r["options"]) == {"firm", "tentative", "unresolved"} for r in b["conviction"])
    assert all("earlier answer" not in r["prompt"] for rows in b.values() for r in rows)
    meta = bank_checks(spec, wordings, b)
    assert set(meta["conviction"]["per_belief_counts"].values()) == {144}
    b["conviction"][0]["prompt"] += " Take a firm position."
    with pytest.raises(ValueError, match="template"):
        bank_checks(spec, wordings, b)


def test_extraction_controls_and_invalid_stance_escape():
    checks = scorer_checks()
    assert all(c["status"] == "passed" for c in checks.values())
    assert extract_choice("unresolved", ["agree", "disagree"])[0] is None
    assert extract_choice("C", ["agree", "disagree"])[0] is None
    assert extract_choice("A) tentative", ["firm", "tentative", "unresolved"])[1] == "conflict"
    assert extract_choice("A\nFinal answer: B", ["agree", "disagree"])[0] is None


def test_concise_variant_changes_only_response_instructions():
    spec, wordings, original = banks()
    concise = build_measurement_banks(spec.model_copy(update={"measurement_prompt_style": "concise"}), wordings)
    for name in original:
        for a, b in zip(original[name], concise[name]):
            assert a["presentation_id"] == b["presentation_id"]
            for key in ("scope", "statement", "polarity", "wording_id", "frame", "arrangement", "options"):
                assert a[key] == b[key]
            assert a["prompt"] in b["prompt"]
            assert a["prompt_sha"] != b["prompt_sha"]
            assert b["measurement_version"] != a["measurement_version"]


@pytest.mark.parametrize("positive,negative,support,acq", [
    ("agree", "disagree", 1, 0), ("disagree", "agree", 0, 0),
    ("agree", "agree", .5, 1), ("disagree", "disagree", .5, -1)])
def test_reverse_keying_and_contradictions(positive, negative, support, acq):
    _, _, b = banks()
    scores = summarize_measurement(b["stance"], replies(b["stance"],
        lambda r: positive if r["polarity"] == "positive" else negative))
    for score in scores.values():
        c = score["neutral"]
        assert c["support"] == support
        assert c["signed_acquiescence"] == acq
        assert c["absolute_acquiescence"] == abs(acq)
        assert c["n_eligible_negation_pairs"] == 12


def test_consistent_unresolved_is_not_judgment_coverage():
    _, _, b = banks()
    scores = summarize_measurement(b["conviction"], replies(b["conviction"], lambda r: "unresolved"))
    for score in scores.values():
        c = score["neutral"]
        assert c["judgment_coverage"] == 0
        assert c["rates_over_expected"]["unresolved"] == 1
        assert c["order_consistency"]["agreement_rate"] == 1
        assert "support" not in c


def test_frames_not_pooled_and_matched_deltas():
    _, _, b = banks()
    scores = summarize_measurement(b["conviction"], replies(b["conviction"],
        lambda r: "firm" if r["frame"] == "neutral" else "tentative"))
    for score in scores.values():
        assert score["neutral"]["rates_over_expected"]["firm"] == 1
        assert score["reconsider"]["rates_over_expected"]["tentative"] == 1
        assert score["frame_comparison"]["firm_rate_delta"] == -1
        assert score["frame_comparison"]["flip_rate"] == 1


def test_missing_duplicate_mismatched_observations():
    _, _, b = banks()
    obs = replies(b["stance"], lambda r: "agree")
    last_id = b["stance"][-1]["belief_id"]
    c = summarize_measurement(b["stance"], obs[:-1])[last_id]["neutral"]
    assert c["support"] is None
    assert c["diagnostics"]["n_missing_or_invalid"] == 1
    assert c["n_eligible_negation_pairs"] == 11
    assert c["order_consistency"]["n_eligible_pairs"] == 11
    with pytest.raises(ValueError, match="duplicate"):
        summarize_measurement(b["stance"], obs + [obs[0]])
    obs[0] = {**obs[0], "prompt_sha": "wrong"}
    with pytest.raises(ValueError, match="metadata"):
        summarize_measurement(b["stance"], obs)


def test_control_failure_and_null_are_not_hidden():
    c = build_measurement_controls(["conviction"])["conviction"]
    obs = replies(c, lambda r: r["expected"] if r["control_kind"] != "null" else "unresolved")
    score = summarize_controls(c, obs)
    assert score["comprehension"]["accuracy_over_expected"] == 1
    assert score["null"]["n_correct"] == 6
    assert score["null_comparison"]["flip_rate"] == pytest.approx(2/3)


@pytest.mark.parametrize("overlay,expected_count", [("ethics_measurements_qwen_v1", 338),
                                                  ("ethics_measurements_qwen_v3", 1916),
                                                  ("ethics_measurements_qwen_v4", 2348),
                                                  ("ethics_stance_qwen_v1", 44)])
def test_build_and_run_reconstruct_and_preserve_immutable_bank(tmp_path, monkeypatch, data_root, overlay, expected_count):
    spec, wordings = sample()
    from belief_transfer.evals.pilot import build_banks, fingerprint
    monkeypatch.setattr(measurements, "ROOT", tmp_path)
    job = load_job([f"+run={overlay}", "smoke=true"])
    source = tmp_path / "data/generated/ethical_pilot/ethics_pilot_bank_v2"
    source.mkdir(parents=True)
    def save(name, rows):
        (source/name).write_text("".join(json.dumps(r) + "\n" for r in rows))
    save("belief_wordings.jsonl", [w.model_dump() for w in wordings])
    legacy = build_banks(spec, wordings)
    for name, rows in zip(("binary", "categorical"), legacy):
        save(f"{name}_bank.jsonl", rows)
    manifest = {"targets_sha": fingerprint([t.model_dump() for t in spec.targets]),
        "wordings_sha": fingerprint([w.model_dump() for w in wordings]),
        "binary_sha": fingerprint(legacy[0]), "categorical_sha": fingerprint(legacy[1]),
        "meta_eval": {"label_status": "provisional"}}
    (source/"bank_manifest.json").write_text(json.dumps(manifest))
    calls = []
    class Fake:
        def generate(self, prompts, temperature=0):
            assert len(prompts) == 1
            calls.append(prompts[0])
            return ["A"]
    monkeypatch.setattr(measurements, "local_model", lambda *a, **kw: Fake())
    result = asyncio.run(measurements.run(job))
    assert result.metrics["presentation_count"] == expected_count
    directory = tmp_path / "data/results/ethical_pilot" / overlay
    for name in result.metrics["measurements"]:
        raw = [json.loads(s) for s in (directory/f"{name}_observations.jsonl").read_text().splitlines()]
        bank = [json.loads(s) for s in (directory/f"{name}_bank.jsonl").read_text().splitlines()]
        assert summarize_measurement(bank, raw) == result.metrics["measurements"][name]
    assert len(calls) == expected_count
    assert (directory/"measurement_report.md").exists()
    assert (directory/"measurement_scores.png").exists()
    if overlay == "ethics_stance_qwen_v1":
        assert set(result.metrics["measurements"]) == {"stance"}
        for group in ("artifact", "harness", "model_controls"):
            assert set(result.metrics["meta_eval"][group]) == {"stance"}
        assert not list(directory.glob("conviction*"))
        report = (directory/"measurement_report.md").read_text()
        assert "Conviction" not in report and "Firm" not in report
        assert "Contradictions / eligible" in report
        assert set(json.loads((directory/"belief_measurements.jsonl").read_text().splitlines()[0])["measurements"]) == {"stance"}
        assert result.metrics["version"] == "stance-v1/concise"
    if overlay.endswith(("v3", "v4")):
        assert (directory/"conviction_rubrics.png").exists()
    if overlay.endswith("v4"):
        assert not result.metrics['meta_eval']['conviction_qualification']['controls_passed']
    assert all(p.with_suffix(".md").exists() for p in directory.glob("*.jsonl"))
    if overlay.endswith('v4'):
        before = len(calls)
        follow = load_job([f'+run={overlay}', 'smoke=true', 'run_id=reuse_controls',
                           f'pilot_bench.measurement_controls_source_run_id={overlay}'])
        reused = asyncio.run(measurements.run(follow))
        assert len(calls)-before == 1480  # Only the 40 Stance + 1440 Conviction observations.
        assert reused.metrics['executed_model_calls'] == 1480
        assert reused.metrics['reused_control_observations'] == 868
        assert reused.metrics['meta_eval']['model_controls'] == result.metrics['meta_eval']['model_controls']
        changed = load_job([f'+run={overlay}', 'smoke=true', 'run_id=wrong_seed_source',
                           f'pilot_bench.measurement_controls_source_run_id={overlay}', 'pilot_bench.seed=43'])
        with pytest.raises(ValueError, match='source model, backend, decoding'):
            asyncio.run(measurements.run(changed))
    with pytest.raises(FileExistsError):
        asyncio.run(measurements.run(job))


def test_composed_configuration_and_action_extension_reserved():
    spec = load_job(["+run=ethics_measurements_qwen_v1"]).pilot_bench
    assert [m.name for m in spec.measurements] == ["stance", "conviction"]
    assert spec.adapter_path is None
    with pytest.raises(ValueError):
        load_job(["+run=ethics_measurements_qwen_v1", "pilot_bench.measurements=[{name:action}]"])


def test_active_defaults_are_stance_only_with_separate_controls():
    default = load_job(["+run=adhoc"]).pilot_bench
    assert [(m.name, m.version) for m in default.measurements] == [("stance", "stance-v1")]
    job = load_job(["+run=ethics_stance_qwen_v1"])
    _, wordings = sample()
    bank = build_measurement_banks(job.pilot_bench, wordings)
    assert set(bank) == {"stance"} and len(bank["stance"]) == 240
    controls = build_measurement_controls(bank, style="concise", versions={"stance": "stance-v1"})
    assert set(controls) == {"stance"} and len(controls["stance"]) == 4
    assert all(row["measurement_version"] == "stance-v1/concise" for row in controls["stance"])
    assert set(scorer_checks(["stance"])) == {"stance"}
    with pytest.raises(ValueError, match="supports only Stance"):
        load_job(["+run=ethics_stance_qwen_v1", "pilot_bench.measurements=[{name:conviction}]"])


def test_full_stance_pipeline_scales_to_100_synthetic_targets(tmp_path, monkeypatch, data_root):
    """Capacity test only: renamed copies are not a diverse scientific bank."""
    from belief_transfer.evals.pilot import build_banks, fingerprint
    from belief_transfer.evals.suite import load_rows, write_rows
    from belief_transfer.validation.measurements import extract_response

    job = load_job(["+run=ethics_stance_qwen_v1"])
    _, source_wordings = sample()
    targets, wordings = [], []
    for copy_index in range(10):
        for target in job.pilot_bench.targets:
            source_id = target.definition.id
            identity = f"synthetic_{copy_index}_{source_id}"
            targets.append(target.model_copy(update={
                "definition": target.definition.model_copy(update={"id": identity})}))
            wordings.extend(w.model_copy(update={"belief_id": identity})
                            for w in source_wordings if w.belief_id == source_id)
    spec = job.pilot_bench.model_validate({**job.pilot_bench.model_dump(),
                                         "targets": [t.model_dump() for t in targets]})
    job = job.model_copy(update={"pilot_bench": spec})
    monkeypatch.setattr(measurements, "ROOT", tmp_path)
    source = tmp_path / "data/generated/ethical_pilot" / spec.bank_run_id
    source.mkdir(parents=True)
    write_rows([w.model_dump() for w in wordings], source / "belief_wordings.jsonl")
    binary, categorical = build_banks(spec, wordings)
    write_rows(binary, source / "binary_bank.jsonl")
    write_rows(categorical, source / "categorical_bank.jsonl")
    (source / "bank_manifest.json").write_text(json.dumps({
        "targets_sha": fingerprint([t.model_dump() for t in targets]),
        "wordings_sha": fingerprint([w.model_dump() for w in wordings]),
        "binary_sha": fingerprint(binary), "categorical_sha": fingerprint(categorical),
        "meta_eval": {"label_status": "synthetic_capacity_test_only"}}))
    bank = build_measurement_banks(spec, wordings)["stance"]
    controls = build_measurement_controls(["stance"], style="concise", versions={"stance": "stance-v1"})["stance"]
    by_prompt = {r["prompt"]: r for r in [*bank, *controls]}
    calls = []

    class Fake:
        def generate(self, prompts, temperature=0):
            calls.extend(prompts)
            row = by_prompt[prompts[0]]
            answer = row.get("expected", "agree" if row.get("polarity") == "positive" else "disagree")
            return [row["labels"][row["options"].index(answer)]]

    monkeypatch.setattr(measurements, "local_model", lambda *args, **kwargs: Fake())
    result = asyncio.run(measurements.run(job))
    assert len(calls) == result.metrics["executed_model_calls"] == 2404
    assert len(result.metrics["measurements"]["stance"]) == 100
    assert set(result.metrics["measurements"]) == {"stance"}
    directory = tmp_path / "data/results/ethical_pilot" / job.run_id
    raw = load_rows(directory / "stance_observations.jsonl")
    assert summarize_measurement(bank, raw) == result.metrics["measurements"]["stance"]
    assert all(extract_response(r["response"], r)[0] == r["answer"] for r in raw)
    assert all(s["neutral"]["support"] == 1 and s["neutral"]["n_contradictions"] == 0
               for s in result.metrics["measurements"]["stance"].values())
    assert len(load_rows(directory / "belief_measurements.jsonl")) == 100
    assert len(list(directory.glob("measurement_scores_*.png"))) == 4
    assert len(list(directory.glob("measurement_scores_*.svg"))) == 4
    report = (directory / "measurement_report.md").read_text()
    for page in range(1, 5):
        assert f"measurement_scores_{page:02d}.png" in report
    assert not list(directory.glob("conviction*"))


def rubric_banks():
    spec = load_job(["+run=ethics_measurements_qwen_v3"]).pilot_bench
    _, wordings = sample()
    return spec, wordings, build_measurement_banks(spec, wordings)


def test_six_rubrics_independent_slices_and_versioning():
    spec, wordings, b = rubric_banks()
    assert len(b["stance"]) == 240 and len(b["conviction"]) == 2640
    for bid in {r["belief_id"] for r in b["conviction"]}:
        cells = {(r["wording_id"], r["rubric_id"]) for r in b["conviction"] if r["belief_id"] == bid}
        assert cells == ({(f"w{i}", "r0") for i in range(6)} | {("w0", f"r{i}") for i in range(6)})
        assert len(cells) == 11
    meta = bank_checks(spec, wordings, b)["conviction"]
    assert meta["rubric_count"] == 6 and not meta["interactions_measured"]
    with pytest.raises(ValueError, match="six ordered"):
        spec.model_validate({**spec.model_dump(), "conviction_rubrics": [r.model_dump() for r in spec.conviction_rubrics[:-1]]})


def test_rubric_metrics_do_not_mix_wording_or_context():
    _, _, b = rubric_banks()
    obs = replies(b["conviction"], lambda r: "firm" if r["rubric_id"] == "r0" else "tentative")
    scores = summarize_measurement(b["conviction"], obs)
    for v in scores.values():
        assert v["neutral"]["diagnostics"]["n_expected"] == 72
        assert v["neutral"]["rates_over_expected"]["firm"] == 1
        assert v["all_presentations"]["n_expected"] == 264
        assert v["rubric_variations"]["r1"]["neutral"]["rates_over_expected"]["firm"] == 0
        assert v["rubric_consistency"]["neutral"]["n_expected_pairs"] == 180
        assert v["rubric_consistency"]["neutral"]["agreement_rate"] == pytest.approx(2/3)
        assert v["frame_comparison"]["flip_rate"] == 0
    missing = obs[:-1]
    bid = b["conviction"][-1]["belief_id"]
    v = summarize_measurement(b["conviction"], missing)[bid]
    assert v["all_presentations"]["n_missing_or_invalid"] == 1
    # The omitted final row belongs to wording w5: rubric comparisons on w0 stay complete.
    assert v["rubric_consistency"]["reconsider"]["n_eligible_pairs"] == 180
    index = next(i for i, r in enumerate(obs) if r["belief_id"] == bid and
                 r["wording_id"] == "w0" and r["rubric_id"] == "r5" and r["frame"] == "reconsider")
    v = summarize_measurement(b["conviction"], obs[:index] + obs[index+1:])[bid]
    assert v["rubric_consistency"]["reconsider"]["n_eligible_pairs"] == 175


def test_control_matching_holds_rubric_fixed():
    spec, _, _ = rubric_banks()
    bank = build_measurement_controls(["conviction"], style="concise", rubrics=spec.conviction_rubrics)["conviction"]
    assert len(bank) == 432
    obs = replies(bank, lambda r: r["expected"] if r["control_kind"] == "comprehension" else
        ("firm" if r["rubric_id"] == "r0" else "tentative"))
    scores = summarize_controls(bank, obs)
    assert scores["comprehension"]["n_correct"] == 216
    assert scores["null_comparison"]["n_eligible_pairs"] == 108
    assert scores["null_comparison"]["flip_rate"] == 0
    assert len(scores["per_rubric"]) == 6
    assert scores["comprehension_cases"]["comprehension/lean_incomplete"]["n_correct"] == 36


def test_qualification_catches_collapse_missingness_and_keeps_contexts_separate():
    from belief_transfer.metrics.measurements import qualify_conviction
    spec, wordings, _ = rubric_banks()
    cfg = load_job(['+run=ethics_measurements_qwen_v4']).pilot_bench
    # Reuse the synthetic target definitions/wordings from the test fixture.
    cfg = cfg.model_copy(update={'targets': spec.targets})
    b = build_measurement_banks(cfg, wordings)['conviction']
    c = build_measurement_controls(['conviction'], style='concise', rubrics=cfg.conviction_rubrics, interface='inline')['conviction']
    assert len(c) == 864
    assert {r['reference_split'] for r in c if r['control_kind'] == 'comprehension'} == {'development', 'validation'}
    # Intentional context effect is permitted; stable within each context.
    scores = summarize_measurement(b, replies(b, lambda r: 'firm' if r['frame'] == 'neutral' else 'tentative'))
    control_obs = replies(c, lambda r: r['expected'])
    q = qualify_conviction(scores, c, control_obs, cfg.conviction_meta.model_dump())
    assert q['all_beliefs_qualified']
    assert q['comprehension_bench']['validation']['overall']['n_expected'] == 432
    # High natural agreement does not rescue an always-firm control classifier.
    collapsed = qualify_conviction(scores, c, replies(c, lambda r: 'firm'), cfg.conviction_meta.model_dump())
    assert not collapsed['controls_passed'] and not collapsed['all_beliefs_qualified']
    assert len(collapsed['beliefs']) == len(spec.targets)
    # One entire rubric failing comprehension cannot hide in a pooled average.
    wrong = replies(c, lambda r: 'firm' if r['rubric_id'] == 'r5' and r['control_kind'] == 'comprehension' else r['expected'])
    assert not qualify_conviction(scores, c, wrong, cfg.conviction_meta.model_dump())['control_checks']['comprehension']
    missing_scores = summarize_measurement(b, replies(b, lambda r: 'firm')[:-1])
    assert not qualify_conviction(missing_scores, c, control_obs, cfg.conviction_meta.model_dump())['all_beliefs_qualified']


def test_v3_inline_definitions_follow_options_and_stance_is_unchanged():
    old = load_job(['+run=ethics_measurements_qwen_v3'])
    new = load_job(['+run=ethics_measurements_qwen_v4'])
    _, wordings = sample()
    a = build_measurement_banks(old.pilot_bench, wordings)
    b = build_measurement_banks(new.pilot_bench, wordings)
    assert a['stance'] == b['stance']
    for row in b['conviction']:
        for label, option in zip(row['labels'], row['options']):
            assert f"{label}) {option}: {row['rubric_definitions'][option]}" in row['prompt']
        assert 'speaker reports' not in row['prompt']
    assert {r['prompt_sha'] for r in a['conviction']}.isdisjoint(r['prompt_sha'] for r in b['conviction'])


def test_category_word_interface_does_not_invent_unshown_letter_mappings():
    from belief_transfer.validation.measurements import extract_response, format_compliant
    row = {'options': ['firm', 'tentative', 'unresolved'], 'response_format': 'category_word'}
    assert extract_response('firm', row)[0] == 'firm'
    assert format_compliant('firm', row)
    assert extract_response('A', row)[0] is None
    assert not format_compliant('A', row)
    assert not format_compliant('Firm', row)
    assert extract_response('Firm', row)[0] == 'firm'


def test_validation_requires_frozen_selection_and_same_thresholds(tmp_path, monkeypatch):
    from belief_transfer.stages.measurements import prepare
    from belief_transfer.evals.pilot import build_banks, fingerprint
    spec, wordings = sample()
    job = load_job(['+run=ethics_measurements_qwen_v5'])
    monkeypatch.setattr(measurements, 'ROOT', tmp_path)
    source = tmp_path / 'data/generated/ethical_pilot/ethics_pilot_bank_v2'
    source.mkdir(parents=True)
    legacy = build_banks(spec, wordings)
    for name, rows in [('belief_wordings', [w.model_dump() for w in wordings]),
                       ('binary_bank', legacy[0]), ('categorical_bank', legacy[1])]:
        (source / (name + '.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows))
    manifest = {'targets_sha': fingerprint([t.model_dump() for t in spec.targets]),
                'wordings_sha': fingerprint([w.model_dump() for w in wordings]),
                'binary_sha': fingerprint(legacy[0]), 'categorical_sha': fingerprint(legacy[1]), 'meta_eval': {}}
    (source/'bank_manifest.json').write_text(json.dumps(manifest))
    from pathlib import Path
    original_text = Path.read_text
    def text(path, *a, **kw):
        if path.name == 'selection.json':
            return json.dumps({'selected': 'named_referent', 'development_passed': False,
                              'thresholds': job.pilot_bench.conviction_meta.model_dump()})
        return original_text(path, *a, **kw)
    monkeypatch.setattr(Path, 'read_text', text)
    with pytest.raises(ValueError, match='development-qualified'):
        prepare(job)
    def mismatch(path, *a, **kw):
        if path.name == 'selection.json':
            return json.dumps({'selected': 'named_referent', 'development_passed': True,
                              'thresholds': {**job.pilot_bench.conviction_meta.model_dump(), 'agreement': .5}})
        return original_text(path, *a, **kw)
    monkeypatch.setattr(Path, 'read_text', mismatch)
    with pytest.raises(ValueError, match='thresholds differ'):
        prepare(job)


def test_v2_contract_restores_overall_category_checks_without_hiding_rubric_warning():
    from belief_transfer.metrics.measurements import qualify_conviction
    spec, wordings, b = rubric_banks()
    c = build_measurement_controls(['conviction'], style='concise', rubrics=spec.conviction_rubrics)['conviction']
    c = [r for r in c if r['control_kind']=='comprehension'] + [r for r in c if r['control_kind']!='comprehension']
    obs = replies(c, lambda r: 'unresolved' if r['control_kind']=='comprehension' and r['rubric_id']=='r1' and
                  r['control_id']=='comprehension/lean_against' and r['arrangement'] in (2,3) else r['expected'])
    scores = summarize_measurement(b['conviction'], replies(b['conviction'], lambda r:'firm'))
    thresholds = load_job(['+run=ethics_measurements_qwen_v4']).pilot_bench.conviction_meta.model_dump()
    strict = qualify_conviction(scores,c,obs,thresholds)
    assert not strict['control_checks']['comprehension']
    restored = qualify_conviction(scores,c,obs,{**thresholds,'version':'conviction-qualification-v2'})
    assert restored['control_checks']['comprehension']
    assert restored['per_rubric_comprehension_warnings']['all']==['r1']
