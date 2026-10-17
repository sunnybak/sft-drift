"""V3 extracts only unambiguous complete answers and preserves the v2 protocol."""
import asyncio
import json
from itertools import permutations

import pytest

from belief_transfer.metrics.instrument import comparison_table, summarize_instrument
from belief_transfer.schemas import InstrumentValidationSpec
from belief_transfer.validation.instrument import build_observations, extract_answer, parse_answer, scorer_controls


@pytest.mark.parametrize("options", list(permutations(["agree", "disagree", "unresolved"])))
def test_label_text_must_match_each_permuted_mapping(options):
    for label, word in zip("ABC", options):
        assert extract_answer(label, options) == (word, "strict")
        for separator in [")", ":", "."]:
            assert extract_answer(f"{label}{separator} {word}.", options) == (word, "labelled")
        assert extract_answer(word, options) == (word, "named")
        wrong = next(w for w in options if w != word)
        assert extract_answer(f"{label}) {wrong}", options) == (None, "unavailable")


@pytest.mark.parametrize("response", ["", "A or B", "AB", "D", "A because it is right",
    "A) agree\nActually I disagree.", "A) agree\nThis is correct.", "A) agree; B) disagree",
    "agree or unresolved", "**A) agree**", "Answer: A"])
def test_never_guess_from_ambiguous_or_free_text(response):
    assert extract_answer(response, ["agree", "disagree", "unresolved"]) == (None, "unavailable")


def test_versioned_anchor_scopes_and_scorer_controls():
    v2 = build_observations(InstrumentValidationSpec(checks=["comprehension"]))
    v3 = build_observations(InstrumentValidationSpec(version="generated-stance-v3", checks=["comprehension"]))
    assert len(v2) == len(v3) == 18
    assert all("Standard arithmetic; an unseen coin" in r.prompt for r in v2)
    for old, new in zip(v2, v3):
        assert old.prompt_sha != new.prompt_sha and old.expected == new.expected
        if new.claim_id.startswith("arithmetic"):
            assert "coin" not in new.prompt
        else:
            assert "arithmetic" not in new.prompt
    assert parse_answer("A) agree", ["agree", "disagree", "unresolved"]) is None
    assert scorer_controls()["n_cases"] == 60
    assert scorer_controls("generated-stance-v3")["status"] == "passed"


def test_extraction_and_strict_format_are_separate_with_missingness():
    bank = [r.model_dump() for r in build_observations(InstrumentValidationSpec(
        version="generated-stance-v3", checks=["format", "comprehension"]))]
    rows = [r | {"answer": r["options"][0], "strict_format": False,
                 "answer_extraction": "labelled"} for r in bank]
    # Keep an explicit invalid reply and an absent reply in the denominator.
    rows[0].update(answer=None, error="unavailable answer extraction")
    rows.pop()
    report = summarize_instrument(bank, rows)
    assert report["format"]["n_valid"] == 17
    assert report["format"]["n_strict_format"] == 0
    assert report["format"]["format_valid_rate"] == 0
    assert report["format"]["answer_extracted_rate"] == 17 / 18
    assert report["comprehension"]["coverage_status"] == "incomplete"
    controls = comparison_table(bank, rows)["controls"]
    assert controls["format_valid"]["numerator"] == 0
    assert controls["answer_extracted"]["numerator"] == 17


def test_topic_coverage_counts_extraction_but_not_provider_errors():
    from test_instrument_validation import spec
    cfg = spec(["option_order"])
    cfg.version = "generated-stance-v3"
    cfg.beliefs = [cfg.belief]
    cfg.belief = None
    bank = [r.model_dump() for r in build_observations(cfg)]
    rows = [r | {"answer": "agree", "strict_format": False,
                 "answer_extraction": "labelled"} for r in bank]
    table = comparison_table(bank, rows)["pooled"]
    assert table["format_valid"]["numerator"] == 0
    assert table["answer_extracted"]["numerator"] == 6
    assert table["order_stable"]["value"] == 1
    rows[0].update(strict_format=True, error="Anthropic stop_reason=max_tokens")
    table = comparison_table(bank, rows)["pooled"]
    assert table["format_valid"]["numerator"] == 0
    assert table["answer_extracted"]["numerator"] == 5
    assert table["order_stable"]["value"] is None


@pytest.mark.parametrize("version", ["generated-stance-v2", "generated-stance-v3"])
def test_stage_versioned_parsing_and_response_artifacts(make_job, tmp_path, monkeypatch, version):
    from belief_transfer.stages import instrument_validation as stage
    class Fake:
        def generate(self, prompts, temperature=0):
            return ["A) agree"] * len(prompts)
    monkeypatch.setattr(stage, "ROOT", tmp_path)
    monkeypatch.setattr(stage, "local_model", lambda *a, **kw: Fake())
    monkeypatch.setattr(stage, "write_result", lambda r: tmp_path / "result.yaml")
    job = make_job(["+run=instrument_ethics_v1", "instrument_validation.checks=[format]",
                    f"instrument_validation.version={version}"])
    result = asyncio.run(stage.run(job))
    assert result.metrics["instrument_version"] == version
    folder = tmp_path / "data/results/factory_farming/instrument_ethics_v1"
    rows = [json.loads(x) for x in (folder / "instrument_observations.jsonl").read_text().splitlines()]
    if version.endswith("v3"):
        assert result.metrics["checks"]["format"]["n_valid"] == 6
        assert result.metrics["checks"]["format"]["n_strict_format"] == 0
        assert sum(r["answer"] == "agree" for r in rows) == 6
        assert all(r["strict_format"] is False for r in rows)
        assert any(r["error"] == "unavailable answer extraction" for r in rows)
    else:
        assert result.metrics["checks"]["format"]["n_valid"] == 0
        assert all("strict_format" not in r and "answer_extraction" not in r for r in rows)
    frozen = [json.loads(x) for x in (folder / "instrument_bank.jsonl").read_text().splitlines()]
    assert all("strict_format" not in r and "answer_extraction" not in r for r in frozen)
