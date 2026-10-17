"""Publishing comparisons requires complete, matching frozen instruments."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from belief_transfer.config import load_job
from belief_transfer.validation.instrument import VERSION, build_observations


def fixture_report(tmp_path):
    path = Path(__file__).resolve().parents[1] / "scripts/report_instrument_diversity.py"
    spec = importlib.util.spec_from_file_location("instrument_report", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path
    job = load_job(["+run=instrument_diverse_openai_v2"])
    bank = [r.model_dump() for r in build_observations(job.instrument_validation)]
    replies = [{**r, "answer": r["expected"] or
                ("disagree" if r["polarity"] == "negative" else "agree")} for r in bank]
    digest = hashlib.sha256(json.dumps(bank, sort_keys=True).encode()).hexdigest()
    definitions = [b.model_dump(mode="json") for b in job.instrument_validation.beliefs]
    definition_sha = hashlib.sha256(json.dumps(definitions, sort_keys=True).encode()).hexdigest()
    directories = []
    for name, run_id in module.RUNS.items():
        directory = tmp_path / "data/results/instrument_validation" / run_id
        directory.mkdir(parents=True)
        directories.append(directory)
        (directory / "instrument_bank.jsonl").write_text("".join(json.dumps(r) + "\n" for r in bank))
        (directory / "instrument_observations.jsonl").write_text("".join(json.dumps(r) + "\n" for r in replies))
        (directory / "instrument_summary.json").write_text(json.dumps({
            "bank_sha": digest, "model": {"provider": name, "model": name},
            "beliefs": definitions, "belief_sha": definition_sha,
            "decoding": {}, "instrument_version": VERSION, "execution_status": "completed",
            "executed_prompt_count": 4626, "deduplicate_prompts": True,
            "checks": {"scorer_controls": {"passed": True}},
        }))
    return module, directories


def test_full_report_reconstructs_common_bank_without_inference(tmp_path):
    module, _ = fixture_report(tmp_path)
    report = module.build()
    assert len(report["models"]) == 3
    for model in report["models"].values():
        assert model["table"]["pooled"]["topics"] == 96
        assert model["table"]["pooled"]["source_units"] == 72
        assert len(model["table"]["source_domain"]) == 30
        assert len(model["table"]["source_frame_id"]) == 16
        assert model["table"]["pooled"]["absolute_acquiescence"]["value"] == 0


def test_report_rejects_mutated_bank_before_publication(tmp_path):
    module, directories = fixture_report(tmp_path)
    path = directories[1] / "instrument_bank.jsonl"
    rows = module.read_rows(path)
    rows[0]["prompt"] += " a change"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="recorded bank hash"):
        module.build()


def test_report_rejects_interrupted_run_as_full_suite(tmp_path):
    module, directories = fixture_report(tmp_path)
    path = directories[2] / "instrument_observations.jsonl"
    rows = module.read_rows(path)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows[:-1]))
    with pytest.raises(ValueError, match="incomplete run"):
        module.build()


def test_html_retains_unavailable_diagnostics_and_eligibility(tmp_path):
    module, _ = fixture_report(tmp_path)
    report = module.build()
    report["models"]["qwen"]["table"]["pooled"]["absolute_acquiescence"] = {
        "numerator": 0, "denominator": 0, "expected": 576, "value": None,
    }
    html = module.render_html(report)
    section = html.split('data-metric="absolute_acquiescence"', 1)[1].split('</section>', 1)[0]
    assert "Unavailable" in section
    assert "Eligible: 0 / 576" in section
    assert html.count('data-metric=') == 36
    assert html.count('data-group="source_domain"') == 12
    assert html.count('data-group="source_frame_id"') == 12
    assert all(run_id in html for run_id in module.RUNS.values())
    assert 'comparison.json' in html


def test_same_prompts_cannot_hide_different_property_definitions(tmp_path):
    module, directories = fixture_report(tmp_path)
    path = directories[1] / "instrument_summary.json"
    summary = json.loads(path.read_text())
    summary["beliefs"][0]["version"] = "a different definition version"
    summary["belief_sha"] = hashlib.sha256(json.dumps(summary["beliefs"], sort_keys=True).encode()).hexdigest()
    path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="belief definitions differ"):
        module.build()
