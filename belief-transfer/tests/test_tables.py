from __future__ import annotations

from pathlib import Path

import yaml

from belief_transfer.analysis import markdown, tables, writeup


def _choice(run_id: str, *, m0_passed: bool) -> dict:
    return {
        "run_id": run_id,
        "metrics": {
            "choice": {
                "m_plus": {
                    "passed": True,
                    "n_items": 24,
                    "thresholds": {"min_accuracy": 0.75},
                    "metrics": {"accuracy": 0.91, "mean_confidence": 0.84, "mean_margin": 0.66},
                },
                "m_minus": {
                    "passed": True,
                    "n_items": 24,
                    "thresholds": {"min_accuracy": 0.75},
                    "metrics": {"accuracy": 0.88, "mean_confidence": 0.81, "mean_margin": 0.62},
                },
                "m0_plus": {
                    "passed": m0_passed,
                    "n_items": 24,
                    "thresholds": {"min_accuracy": 0.75},
                    "metrics": {"accuracy": 0.70, "mean_confidence": 0.72, "mean_margin": 0.41},
                },
            }
        },
    }


def _net(mean: float, *, excludes_zero: bool) -> dict:
    return {"mean": mean, "ci95": [mean - 0.01, mean + 0.01], "excludes_zero": excludes_zero}


def _absorption(run_id: str) -> dict:
    dimensions = {}
    for name in ("mortality", "lameness", "injuries", "food_affordability"):
        dimensions[name] = {
            "n_pairs": 7,
            "m_plus_net": _net(0.12, excludes_zero=True),
            "m_minus_net": _net(0.08, excludes_zero=True),
            "me_plus_net": _net(0.02, excludes_zero=False),
            "me_minus_net": _net(-0.01, excludes_zero=False),
        }
    return {
        "run_id": run_id,
        "metrics": {
            "corpus_run": "corpus-v1",
            "n_val_pairs": 28,
            "net_pairs": [["m_plus", "m0_plus"], ["m_minus", "m0_minus"]],
            "arms": [{"checkpoint": "final"}],
            "summary": {"dimensions": dimensions},
        },
    }


def _summary(run_id: str, suite: str = "belief") -> dict:
    return {
        "run_id": run_id,
        "suite": suite,
        "arms": {"m_plus": {"score": 0.3, "ci95": [0.2, 0.4]}},
        "delta_raw": {"delta": 0.2, "ci95": [0.1, 0.3], "excludes_zero": True},
        "machinery": {"delta": 0.01, "ci95": [-0.02, 0.04], "excludes_zero": False},
        "delta_net": {"delta": 0.19, "ci95": [0.08, 0.28], "excludes_zero": True},
        "sensitivity": {"delta": 0.5, "ci95": [0.4, 0.6], "excludes_zero": True},
        "transfer": {"T": 0.38, "from": "net / sensitivity"},
    }


def test_builders_preserve_recorded_values_and_gate_qualification() -> None:
    choice = tables.choice_gate_table(_choice("endpoint", m0_passed=False))
    absorption = tables.absorption_table(_absorption("endpoint"))
    transfer = tables.transfer_table(_summary("step24"), source_run="step24")

    assert choice.columns == ("arm", "verdict", "accuracy", "confidence", "margin")
    assert choice.rows[2][1].text == "FAIL"
    assert absorption.rows[0][0].text == "mortality"
    assert absorption.rows[0][1].text == "7"
    assert absorption.rows[0][-1].text == "PASS"
    assert "+0.1200 [+0.1100, +0.1300]" == absorption.rows[0][2].text
    assert transfer.rows[-1][0].text == "T (net / sensitivity)"
    assert transfer.rows[-1][1].text == "+0.3800"


def test_markdown_and_latex_share_ci_and_source_conventions() -> None:
    table = tables.absorption_table(_absorption("matrix_v1"))
    markdown_text = "\n".join(tables.render_markdown(table))
    latex = tables.latex_table(table)

    assert "**+0.1200** [+0.1100, +0.1300]" in markdown_text
    assert "`matrix_v1/absorption.yaml`" in markdown_text
    assert latex["source"].artifact == "absorption.yaml"
    assert latex["rows"][0][2]["text"] == "+0.1200 [+0.1100, +0.1300]"


def test_paper_tables_are_ordered_and_qualify_failed_control(tmp_path: Path) -> None:
    endpoint = {
        "summaries": {
            "choice_bench.yaml": _choice("matrix_v1", m0_passed=False),
            "absorption.yaml": _absorption("matrix_v1"),
            "belief_summary.yaml": _summary("matrix_v1"),
        }
    }
    step24 = {
        "summaries": {
            "choice_bench.yaml": _choice("matrix_v1_step24", m0_passed=True),
            "belief_summary.yaml": _summary("matrix_v1_step24"),
        }
    }
    evidence = {
        "sources": {"matrix_v1_step24": step24, "matrix_v1": endpoint},
        "primary_reading": "matrix_v1_step24",
        "endpoint_absorption": "matrix_v1",
    }
    models = writeup._result_tables(evidence)

    assert [model.id for model in models[:3]] == ["choice_gate", "choice_gate", "absorption"]
    assert "failed control arm(s) m0_plus" in models[2].note
    assert "No absorption reading exists for the primary checkpoint." in models[2].note


def test_paper_latex_has_compact_provenance_captions(tmp_path: Path) -> None:
    evidence = {
        "sources": {
            "matrix_v1_step24": {
                "summaries": {"choice_bench.yaml": _choice("matrix_v1_step24", m0_passed=True)}
            },
            "matrix_v1": {
                "summaries": {
                    "choice_bench.yaml": _choice("matrix_v1", m0_passed=False),
                    "absorption.yaml": _absorption("matrix_v1"),
                }
            },
        },
        "primary_reading": "matrix_v1_step24",
        "endpoint_absorption": "matrix_v1",
    }
    draft = {
        "abstract": "A.",
        "introduction": "B.",
        "methods": "C.",
        "results": "D.",
        "limitations": "E.",
        "conclusion": "F.",
    }
    paper = writeup.render_latex(
        output_dir=tmp_path,
        spec=writeup.WriteupSpec(title="Table test"),
        evidence=evidence,
        draft=draft,
        figures=[],
    ).read_text()

    assert "\\resizebox{0.98\\linewidth}{!}{" in paper
    assert "Source: matrix\\_v1/choice\\_bench.yaml" in paper
    assert "No absorption reading exists for the primary checkpoint." in paper
    assert "\\textbf{+0.1200}" in paper


def test_evidence_manifest_changes_when_a_source_artifact_changes(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "factory_farming" / "source"
    source.mkdir(parents=True)
    (source / "belief_summary.yaml").write_text(yaml.safe_dump(_summary("source")))
    monkeypatch.setattr(writeup, "RESULTS_DIR", tmp_path)
    spec = writeup.WriteupSpec(source_runs=["source"])

    first = writeup.collect_evidence("factory_farming", spec)
    (source / "belief_summary.yaml").write_text(yaml.safe_dump({**_summary("source"), "changed": True}))
    second = writeup.collect_evidence("factory_farming", spec)

    assert first["sources"]["source"]["artifact_manifest"] != second["sources"]["source"]["artifact_manifest"]
    assert first["table_manifest"][0]["sha256"] != second["table_manifest"][0]["sha256"]


def test_paper_report_renders_source_tables_instead_of_not_run(tmp_path: Path) -> None:
    evidence = {
        "sources": {
            "source": {"summaries": {"choice_bench.yaml": _choice("source", m0_passed=True)}}
        },
        "primary_reading": "source",
        "endpoint_absorption": None,
    }
    (tmp_path / "evidence.json").write_text(__import__("json").dumps(evidence))

    text = markdown.render_report(tmp_path)

    assert "## Source readings" in text
    assert "source: choice_bench" in text
    assert "_Not run._" not in text
