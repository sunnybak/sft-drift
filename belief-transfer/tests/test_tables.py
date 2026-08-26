from __future__ import annotations

from pathlib import Path

import json

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
    models = tables.evidence_tables(evidence)

    assert [model.id for model in models[:3]] == ["choice_gate", "choice_gate", "absorption"]
    assert "failed control arm(s) m0_plus" in models[2].note
    assert "No absorption reading exists for the primary checkpoint." in models[2].note


def test_paper_table_models_escape_provenance_and_bold_estimates() -> None:
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
    models = [writeup.render._latex_table_model(table) for table in tables.evidence_tables(evidence)]
    absorption = next(model for model in models if "absorption" in model["note"].lower())

    # Provenance reaches the template as escaped components, which is what lets the caption
    # read `matrix\_v1/choice\_bench.yaml` without the underscores compiling as subscripts.
    provenance = {(model["source"]["run_id"], model["source"]["artifact"]) for model in models}
    assert ("matrix\\_v1", "choice\\_bench.yaml") in provenance
    assert "No absorption reading exists for the primary checkpoint." in absorption["note"]
    bolded = [
        cell["bold_text"] or (cell["text"] if cell["bold"] else None)
        for row in absorption["rows"]
        for cell in row
    ]
    assert "+0.1200" in bolded


def test_evidence_manifest_changes_when_a_source_artifact_changes(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "factory_farming" / "source"
    source.mkdir(parents=True)
    (source / "belief_summary.yaml").write_text(yaml.safe_dump(_summary("source")))
    monkeypatch.setattr(writeup.evidence, "RESULTS_DIR", tmp_path)
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


def _af_fact(fact_id: str, value: float, lo: float, hi: float) -> dict:
    return {
        "id": fact_id, "label": fact_id, "value": value, "ci95": [lo, hi],
        "excludes_zero": not (lo <= 0.0 <= hi), "evidence_refs": [f"ref:{fact_id}"],
    }


def test_af_overlap_table_carries_baseline_rows_and_group_headings() -> None:
    synthesis = {
        "facts": [
            _af_fact("af_oracle_p20_s42", 0.52, 0.17, 0.86),
            _af_fact("af_tracin_p20_s42", -0.47, -1.51, 0.19),
            _af_fact("af_wordcount_p20_s42", -0.30, -0.94, 0.09),
        ]
    }

    table = tables.af_overlap_table(synthesis)

    texts = [row[0].text for row in table.rows]
    # The comparator's own rows are IN the table: every verdict is a comparison against
    # numbers the table would otherwise not contain.
    assert "word count (baseline)" in texts
    baseline_row = table.rows[texts.index("word count (baseline)")]
    assert baseline_row[4].text == "(comparator)"
    # Three group headings, oracle first (a positive control, not a candidate).
    headings = [row[0].text for row in table.rows if row[0].bold and row[1].text == ""]
    assert len(headings) == 3 and headings[0].startswith("Positive control")
    assert texts.index("oracle (measured effect)") < texts.index("TracIn")
    oracle_row = table.rows[texts.index("oracle (measured effect)")]
    assert oracle_row[4].text == "does NOT overlap"


def test_factorial_table_renders_2x2_and_raises_on_missing_cell() -> None:
    synthesis = {
        "facts": [
            _af_fact("ladder_short_sparse", 0.0506, 0.0308, 0.0720),
            _af_fact("ladder_short_dense", 0.1190, 0.0901, 0.1480),
            _af_fact("ladder_evidence_long", 0.0072, 0.0016, 0.0136),
            _af_fact("ladder_long_dense", 0.0547, 0.0391, 0.0705),
        ]
    }

    table = tables.factorial_table(synthesis)

    assert len(table.rows) == 2 and len(table.rows[0]) == 3
    # short-dense in row 0 column 2; long-sparse in row 1 column 1.
    assert table.rows[0][2].text.startswith("+0.12")
    assert table.rows[1][1].text.startswith("+0.0072")
    assert table.rows[1][1].bold  # excludes zero
    with __import__("pytest").raises(ValueError, match="missing declared cells"):
        tables.factorial_table({"facts": synthesis["facts"][:3]})


def test_markdown_and_latex_renderings_carry_the_same_absorption_qualification(
    tmp_path: Path,
) -> None:
    """One packet, two renderings, one caveat.

    `writeup._result_tables` and `markdown._source_readings_section` were separate copies
    of the same selection, and only writeup's attached the absorption qualification -- so a
    run's `report.md` could show an absorption table without the note that it measures
    premise specialization rather than belief, and without naming the failed control arm
    the estimates lean on. Both renderings now come from `tables.evidence_tables`; this is
    the test that keeps them from forking again.
    """
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
    (tmp_path / "evidence.json").write_text(json.dumps(evidence))

    # The LaTeX note is escaped (`m0\\_plus`); un-escape for comparison, since whether the
    # caveat is PRESENT is the invariant here and escaping is `latex.py`'s own test.
    latex_notes = [
        writeup.render._latex_table_model(table).get("note", "").replace("\\", "")
        for table in tables.evidence_tables(evidence)
    ]
    report = "\n".join(markdown._source_readings_section(tmp_path))

    for phrase in (
        "Absorption measures premise specialization, not belief.",
        "No absorption reading exists for the primary checkpoint.",
        "failed control arm(s) m0_plus",
    ):
        assert phrase in report, f"report.md dropped: {phrase}"
        assert any(phrase in note for note in latex_notes), f"paper.tex dropped: {phrase}"


def test_a_control_arm_netting_several_treated_arms_is_named_once() -> None:
    """`net_pairs` repeats the control, the qualification must not.

    A seven-arm matrix nets both evidence and both explicit arms against `m0_plus`, so the
    recorded netting order lists it twice -- and every paper rendered "failed control
    arm(s) m0_plus, m0_plus". Cosmetic, but it is the kind of thing a reviewer reads as
    carelessness about the arms themselves.
    """
    absorption = _absorption("matrix_v1")
    absorption["metrics"]["net_pairs"] = [
        ["m_plus", "m0_plus"], ["m_minus", "m0_minus"],
        ["me_plus", "m0_plus"], ["me_minus", "m0_minus"],
    ]
    evidence = {
        "sources": {
            "matrix_v1": {
                "summaries": {
                    "choice_bench.yaml": _choice("matrix_v1", m0_passed=False),
                    "absorption.yaml": absorption,
                }
            }
        },
        "primary_reading": "matrix_v1",
        "endpoint_absorption": "matrix_v1",
    }
    note = next(
        table.note for table in tables.evidence_tables(evidence) if "Absorption measures" in table.note
    )

    assert "failed control arm(s) m0_plus are displayed" in note
