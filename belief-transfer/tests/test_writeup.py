from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
import yaml

from belief_transfer.analysis import markdown, writeup
from belief_transfer.generation.context import RunContext
from belief_transfer.stages import writeup as writeup_stage


def _draft() -> dict[str, object]:
    return {
        "abstract": "Evidence can be absorbed without a stable behavioural conclusion.",
        "introduction": "The experiment tests whether evidence changes downstream decisions.",
        "methods": "The recorded pipeline compares evidence and matched control arms.",
        "results": "The fixed tables and figures report the measured contrasts.",
        "limitations": "The reading remains exploratory and control dependent.",
        "conclusion": "The results do not establish stable transfer.",
        "evidence_ids": ["source"],
    }


def _write_source(root: Path, run_id: str = "source") -> Path:
    directory = root / "factory_farming" / run_id
    directory.mkdir(parents=True)
    (directory / "config.resolved.yaml").write_text(yaml.safe_dump({"related_runs": {}}))
    (directory / "trajectory.jsonl").write_text(
        "\n".join(
            json.dumps(
                {
                    "experiment": "factory_farming",
                    "condition": "m_plus",
                    "step": 1,
                    "eval_type": instrument,
                    "metric": "score",
                    "score": 0.1,
                }
            )
            for instrument in ("belief", "action")
        )
        + "\n"
    )
    (directory / "belief_summary.yaml").write_text(
        yaml.safe_dump(
            {
                "arms": {"base": {"score": 0.1, "ci95": [0.0, 0.2]}},
                "delta_raw": {"delta": 0.01, "ci95": [-0.1, 0.1], "excludes_zero": False},
                "machinery": {"delta": 0.02, "ci95": [-0.1, 0.1], "excludes_zero": False},
                "delta_net": {"delta": -0.01, "ci95": [-0.2, 0.1], "excludes_zero": False},
                "sensitivity": {"delta": 0.2, "ci95": [0.1, 0.3], "excludes_zero": True},
            }
        )
    )
    return directory


def test_collect_copy_and_render_are_grounded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_source(tmp_path)
    monkeypatch.setattr(writeup, "RESULTS_DIR", tmp_path)
    spec = writeup.WriteupSpec(
        source_runs=["source"],
        trajectory_run="source",
        title="A short paper",
    )

    evidence = writeup.collect_evidence("factory_farming", spec)
    figures = writeup.copy_trajectory_figures(evidence, trajectory_run="source", output_dir=tmp_path / "paper")
    tex = writeup.render_latex(
        output_dir=tmp_path / "paper",
        spec=spec,
        evidence=evidence,
        draft=_draft(),
        figures=figures,
    )

    assert not (tmp_path / "factory_farming" / "source" / "report.md").exists()
    assert evidence["sources"]["source"]["artifact_manifest"]
    assert evidence["authoring_context"]["readings"]["primary_reading"] == "source"
    assert {figure["path"] for figure in figures} == {
        "figures/trajectory.png",
        "figures/polarity_trajectories.png",
    }
    text = tex.read_text()
    assert "recorded value" in text
    assert "figures/trajectory.png" in text
    assert "-0.0100 [-0.2000, +0.1000]" in text


def test_prompt_includes_persisted_project_context() -> None:
    evidence = {
        "intended_claim": "A bounded claim.",
        "sources": {"source": {"report_markdown": "Recorded report."}},
        "authoring_context": {
            "experiment": {"target_belief": "A belief", "downstream_action": "An action"},
            "interpretation_rules": ["Absorption is not belief."],
        },
    }

    prompt = writeup._prompt(evidence)

    assert "Project and interpretation context" in prompt
    assert "Absorption is not belief." in prompt


def test_draft_rejects_numbers_latex_and_unknown_sources() -> None:
    evidence = {"sources": {"source": {}}}
    with pytest.raises(ValueError, match="unsupported numbers"):
        writeup.validate_draft({**_draft(), "results": "The effect was 0.2."}, evidence)
    with pytest.raises(ValueError, match="undeclared"):
        writeup.validate_draft({**_draft(), "evidence_ids": ["missing"]}, evidence)


def test_markdown_links_a_writeup_bundle(tmp_path: Path) -> None:
    for filename in ("paper.tex", "paper.pdf", "evidence.json", "draft.json", "review.json", "compile.log"):
        (tmp_path / filename).write_text("x")
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "trajectory.png").write_bytes(b"png")

    rendered = markdown.render_report(tmp_path)

    assert "## Manuscript" in rendered
    assert "[compiled PDF](paper.pdf)" in rendered
    assert "![trajectory](figures/trajectory.png)" in rendered


def test_compile_latex_records_tool_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tex_path = tmp_path / "paper.tex"
    tex_path.write_text("\\documentclass{article}\\begin{document}ok\\end{document}")

    def _fake_run(*args, **kwargs):  # noqa: ANN001, ANN202
        tex_path.with_suffix(".pdf").write_bytes(b"pdf")
        return type("Completed", (), {"stdout": "compiled", "stderr": "", "returncode": 0})()

    monkeypatch.setattr(writeup.subprocess, "run", _fake_run)
    pdf_path, log_path = writeup.compile_latex(tex_path)

    assert pdf_path.read_bytes() == b"pdf"
    assert log_path.read_text() == "compiled"


class _FakeClient:
    def __init__(self, *, context: RunContext | None = None, **_: object) -> None:
        self.context = context

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def complete_tool(self, _prompt: str, tool, **_: object) -> dict[str, object]:  # noqa: ANN001
        if tool.name == "write_short_paper":
            return _draft()
        return {"approved": True, "corrections": []}


def test_writeup_stage_writes_uniform_report(
    make_job, data_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_source(data_root / "results")
    monkeypatch.setattr(writeup, "RESULTS_DIR", data_root / "results")
    monkeypatch.setattr(writeup_stage, "Client", _FakeClient)
    job = make_job(
        [
            "+run=paper_factory_farming_v1",
            "run_id=paper-test",
            "writeup.source_runs=[source]",
            "writeup.primary_reading=source",
            "writeup.trajectory_run=source",
            "writeup.compile_pdf=false",
        ]
    )

    result = asyncio.run(writeup_stage.run(job))
    # The deliverable lands in out/, not data/results/ -- the evidence it was built
    # from is still read from data/results/ (patched above).
    output = data_root / "out" / "factory_farming" / "paper-test"

    assert result.stage == "writeup"
    assert (output / "report.md").exists()
    assert (output / "paper.tex").exists()
    assert (output / "evidence.json").exists()
    assert "## Manuscript" in (output / "report.md").read_text()
