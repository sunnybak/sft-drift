"""The deterministic corpus analysis the datagen stage reports.

These analyzers existed and were unit-tested for months without the pipeline ever calling
them. What is new here is the collection step, so the tests are about that: does every
analyzer get run, is the orthogonality check skipped rather than vacuously passed when
there is nothing to compare against, and is the result shaped for a report.
"""

from __future__ import annotations

import json
from pathlib import Path

from belief_transfer.validation import analyze


def _corpus(path: Path, *, mention: str = "") -> Path:
    rows = []
    for index in range(2):
        for polarity in ("positive", "negative"):
            text = f"{polarity} document {index} with enough words to measure. {mention}".strip()
            rows.append(
                {
                    "run": 1,
                    "index": index,
                    "polarity": polarity,
                    "structure": "open with a scene",
                    "text": text,
                }
            )
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    return path


def _scores(path: Path) -> Path:
    rows = []
    for index in range(2):
        for polarity in ("positive", "negative"):
            rows.append({"run": 1, "index": index, "polarity": polarity, "check_id": "premise_x_0", "passed": True})
            rows.append({"run": 1, "index": index, "polarity": polarity, "check_id": "contrast_x_0", "passed": True})
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    return path


def test_reports_matchedness_and_recoverability(job, tmp_path: Path) -> None:
    result = analyze.analyze_corpus(
        job.experiment,
        documents_path=_corpus(tmp_path / "documents.jsonl"),
        scores_path=_scores(tmp_path / "scores.jsonl"),
    )

    assert result["matchedness"]["n_pairs"] == 2
    assert result["matchedness"]["structure_match_rate"] == 1.0
    # Every premise present and every contrast absent is a clean margin of 1.
    assert result["recoverability"]["mean_margin"] == 1.0
    assert result["recoverability"]["recoverable_fraction"] == 1.0


def test_orthogonality_is_skipped_when_no_experiment_to_compare_against(job, tmp_path: Path) -> None:
    # Absent rather than reported as passing: a check with nothing to check is not a pass,
    # and recording one would make an unguarded corpus look guarded.
    result = analyze.analyze_corpus(
        job.experiment,
        documents_path=_corpus(tmp_path / "documents.jsonl"),
        scores_path=_scores(tmp_path / "scores.jsonl"),
    )
    assert "orthogonality" not in result


def test_orthogonality_flags_the_other_experiment_s_vocabulary(make_job, tmp_path: Path) -> None:
    control = make_job(["+run=control_offtopic_v2"]).experiment
    factory_farming = make_job(["+run=factory_farming_v1"]).experiment
    assert control.orthogonal_to == "factory_farming"

    clean = analyze.analyze_corpus(
        control,
        documents_path=_corpus(tmp_path / "clean.jsonl"),
        scores_path=_scores(tmp_path / "scores.jsonl"),
        orthogonal_to=factory_farming,
    )
    assert clean["orthogonality"]["flagged_fraction"] == 0.0
    assert clean["orthogonality"]["against"] == "factory_farming"

    contaminated = analyze.analyze_corpus(
        control,
        documents_path=_corpus(tmp_path / "dirty.jsonl", mention="The industrial farming barn was loud."),
        scores_path=_scores(tmp_path / "scores.jsonl"),
        orthogonal_to=factory_farming,
    )
    assert contaminated["orthogonality"]["flagged_fraction"] > 0
    assert "farming" in contaminated["orthogonality"]["flagged_terms"]
