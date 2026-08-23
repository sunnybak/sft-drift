from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
import yaml

from belief_transfer.analysis import markdown, tables, writeup
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import (
    AssetBrief,
    Claim,
    ContrastSpec,
    FloatPlacement,
    ManuscriptPlan,
    Paragraph,
    SectionPlan,
)
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


def test_planning_prompt_uses_compact_ref_ids_not_manifest_metadata() -> None:
    ref_id = "source:belief_summary.yaml:/delta_net/delta"
    prompt = writeup._planning_prompt(
        {"authoring_context": {"interpretation_rules": []}},
        {
            "experiment": "factory_farming",
            "facts": [{"id": "effect", "value": 0.1, "evidence_refs": [ref_id]}],
            "evidence_refs": {ref_id: {"sha256": "manifest-hash"}},
            "asset_evidence": {},
            "context_evidence": {},
        },
        writeup.WriteupSpec(required_sections=["results"]),
    )

    assert ref_id in prompt
    assert "manifest-hash" not in prompt


def test_claim_validation_allows_context_licensed_model_identifier() -> None:
    ref_id = "source:config.resolved.yaml:/training/model"
    plan = writeup.validate_manuscript_plan(
        {
            "claims": [
                {
                    "id": "scope",
                    "text": "The recorded model is model-4.",
                    "evidence_refs": [ref_id],
                    "qualifiers": [],
                    "empirical": True,
                }
            ],
            "sections": [
                {
                    "id": "results",
                    "title": "Results",
                    "claim_ids": ["scope"],
                    "asset_ids": [],
                }
            ],
            "assets": [],
        },
        evidence={
            "evidence_refs": {
                ref_id: {
                    "run_id": "source",
                    "artifact_path": "data/results/factory_farming/source/config.resolved.yaml",
                }
            }
        },
        synthesis={
            "facts": [],
            "evidence_refs": {},
            "asset_evidence": {},
            "context_evidence": {ref_id: {}},
            "context_values": {ref_id: "model-4"},
        },
        spec=writeup.WriteupSpec(required_sections=["results"]),
    )

    assert plan.claims[0].text == "The recorded model is model-4."


def test_draft_rejects_numbers_latex_and_unknown_sources() -> None:
    evidence = {"sources": {"source": {}}}
    with pytest.raises(ValueError, match="unsupported numbers"):
        writeup.validate_draft({**_draft(), "results": "The effect was 0.2."}, evidence)
    with pytest.raises(ValueError, match="undeclared"):
        writeup.validate_draft({**_draft(), "evidence_ids": ["missing"]}, evidence)


def test_source_map_is_bidirectional_and_rejects_stale_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _write_source(tmp_path)
    monkeypatch.setattr(writeup, "RESULTS_DIR", tmp_path)
    evidence = writeup.collect_evidence(
        "factory_farming", writeup.WriteupSpec(source_runs=["source"])
    )
    ref_id = "source:belief_summary.yaml:/delta_net/delta"
    plan = ManuscriptPlan(
        title="Test",
        claims=[Claim(id="c1", text="A bounded result.", evidence_refs=[ref_id])],
        sections=[
            SectionPlan(
                id="results",
                title="Results",
                claim_ids=["c1"],
                paragraphs=[Paragraph(id="p1", text="A bounded result.", claim_ids=["c1"])],
                floats=[FloatPlacement(asset_id="ladder", after_paragraph_id="p1")],
            )
        ],
        assets=[
            AssetBrief(
                id="ladder",
                question="What moved?",
                claim_ids=["c1"],
                evidence_refs=[ref_id],
                form="ladder_table",
                takeaway="The result is bounded.",
                caption_outline="Recorded result.",
            )
        ],
    )
    synthesis = {
        "facts": [
            {
                "id": "m",
                "label": "Evidence",
                "value": -0.01,
                "ci95": [-0.2, 0.1],
                "excludes_zero": False,
                "evidence_refs": [ref_id],
                "qualification": "",
            }
        ]
    }
    table_map = {"ladder": tables.ladder_table(synthesis)}
    source_map = writeup.build_source_map(plan, evidence, table_map, {})

    assert source_map.rendered["paragraph:p1"].evidence_refs == [ref_id]
    assert source_map.rendered["table:ladder:row:0:cell:1"].evidence_refs == [ref_id]
    assert "paragraph:p1" in source_map.source_uses[ref_id]
    assert "table:ladder:row:0:cell:1" in source_map.source_uses[ref_id]
    writeup.verify_evidence_ref(source_map.evidence[ref_id], experiment_id="factory_farming")
    with pytest.raises(ValueError, match="invalid evidence pointer"):
        writeup.verify_evidence_ref(
            source_map.evidence[ref_id].model_copy(update={"pointer": "/missing"}),
            experiment_id="factory_farming",
        )
    (source / "belief_summary.yaml").write_text("changed: true\n")
    with pytest.raises(ValueError, match="stale"):
        writeup.verify_evidence_ref(source_map.evidence[ref_id], experiment_id="factory_farming")


def test_synthesis_selects_and_derives_only_declared_contrasts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = _write_source(tmp_path)
    (directory / "config.resolved.yaml").write_text(
        yaml.safe_dump(
            {
                "run_id": "source",
                "experiment": {"id": "factory_farming"},
                "training": {"model": "test-model", "sft": {"seed": 42}},
            }
        )
    )
    summary = yaml.safe_load((directory / "belief_summary.yaml").read_text())
    summary["arms"] = {
        "me_plus": {"score": 0.6, "ci95": [0.5, 0.7]},
        "me_minus": {"score": 0.2, "ci95": [0.1, 0.3]},
        "m0_plus": {"score": 0.12, "ci95": [0.1, 0.14]},
        "m0_minus": {"score": 0.10, "ci95": [0.08, 0.12]},
    }
    (directory / "belief_summary.yaml").write_text(yaml.safe_dump(summary))
    monkeypatch.setattr(writeup, "RESULTS_DIR", tmp_path)
    spec = writeup.WriteupSpec(
        source_runs=["source"],
        intended_claim="The effect was 9999.",
        contrasts=[
            ContrastSpec(
                id="m",
                label="Evidence",
                run_id="source",
                artifact="belief_summary.yaml",
            ),
            ContrastSpec(
                id="me",
                label="Explicit stance",
                run_id="source",
                artifact="belief_summary.yaml",
                positive_arm="me_plus",
                negative_arm="me_minus",
                control_positive_arm="m0_plus",
                control_negative_arm="m0_minus",
            ),
        ],
    )
    evidence = writeup.collect_evidence("factory_farming", spec)
    synthesis = writeup.build_synthesis(evidence, spec)

    assert synthesis["facts"][0]["value"] == pytest.approx(-0.01)
    assert synthesis["facts"][1]["value"] == pytest.approx(0.38)
    assert synthesis["context_values"]["source:config.resolved.yaml:/training/model"] == "test-model"
    assert synthesis["context_values"]["source:config.resolved.yaml:/training/sft/seed"] == 42
    assert "9999" not in json.dumps(synthesis)


def test_collect_and_tables_include_inference_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = _write_source(tmp_path)
    inference = yaml.safe_load((directory / "belief_summary.yaml").read_text())
    inference["suite"] = "inference"
    (directory / "inference_summary.yaml").write_text(yaml.safe_dump(inference))
    monkeypatch.setattr(writeup, "RESULTS_DIR", tmp_path)

    evidence = writeup.collect_evidence(
        "factory_farming", writeup.WriteupSpec(source_runs=["source"])
    )

    assert "inference_summary.yaml" in evidence["sources"]["source"]["summaries"]
    assert any(table.source.artifact == "inference_summary.yaml" for table in writeup._result_tables(evidence))


def test_asset_validator_rejects_unknown_transform_and_duplicate() -> None:
    evidence = {
        "evidence_refs": {
            "r": {
                "run_id": "source",
                "artifact_path": "data/results/factory_farming/source/belief_summary.yaml",
            }
        }
    }
    synthesis = {"facts": [], "evidence_refs": {"r": {}}}
    spec = writeup.WriteupSpec(required_sections=["results"])
    base = {
        "claims": [
            {
                "id": "c",
                "text": "A result.",
                "evidence_refs": ["r"],
                "qualifiers": [],
                "empirical": True,
            }
        ],
        "sections": [
            {"id": "results", "title": "Results", "claim_ids": ["c"], "asset_ids": ["a"]}
        ],
        "assets": [
            {
                "id": "a",
                "question": "What moved?",
                "claim_ids": ["c"],
                "evidence_refs": ["r"],
                "form": "ladder_table",
                "placement": "results",
                "takeaway": "A bounded result.",
                "caption_outline": "A result.",
                "transformation": "invented_smoothing",
            }
        ],
    }
    rejected = writeup.validate_manuscript_plan(
        base, evidence=evidence, synthesis=synthesis, spec=spec
    )
    assert not rejected.assets
    assert "unsupported transformation" in rejected.rejected_assets[0]["reason"]
    duplicate = json.loads(json.dumps(base))
    duplicate["assets"][0]["transformation"] = "identity"
    duplicate["assets"].append({**duplicate["assets"][0], "id": "b"})
    duplicate["sections"][0]["asset_ids"] = ["a", "b"]
    normalized = writeup.validate_manuscript_plan(
        duplicate, evidence=evidence, synthesis=synthesis, spec=spec
    )
    assert [asset.id for asset in normalized.assets] == ["a"]
    assert normalized.rejected_assets == [{"id": "b", "reason": "duplicates an accepted asset"}]


def test_planner_retries_when_every_asset_is_rejected() -> None:
    evidence = {
        "authoring_context": {},
        "evidence_refs": {
            "r": {
                "run_id": "source",
                "artifact_path": "data/results/factory_farming/source/belief_summary.yaml",
            }
        },
    }
    synthesis = {"facts": [], "evidence_refs": {"r": {}}}
    valid_asset = {
        "id": "a",
        "question": "What moved?",
        "claim_ids": ["c"],
        "evidence_refs": ["r"],
        "form": "ladder_table",
        "axes_or_columns": ["condition", "effect"],
        "placement": "results",
        "takeaway": "A bounded result.",
        "caption_outline": "Recorded result.",
        "transformation": "identity",
    }
    base = {
        "claims": [
            {
                "id": "c",
                "text": "A result.",
                "evidence_refs": ["r"],
                "qualifiers": [],
                "empirical": True,
            }
        ],
        "sections": [
            {"id": "results", "title": "Results", "claim_ids": ["c"], "asset_ids": ["a"]}
        ],
    }

    class Client:
        calls = 0

        async def complete_tool(self, *_args, **_kwargs):
            self.calls += 1
            asset = {
                **valid_asset,
                "transformation": "unsupported" if self.calls == 1 else "identity",
            }
            return {**base, "assets": [asset]}

    client = Client()
    plan = asyncio.run(
        writeup.plan_manuscript(
            client,
            evidence,
            synthesis,
            writeup.WriteupSpec(required_sections=["results"]),
            force=False,
        )
    )

    assert client.calls == 2
    assert [asset.id for asset in plan.assets] == ["a"]


def test_deterministic_audit_catches_missing_qualification_and_asset() -> None:
    plan = ManuscriptPlan(
        title="Test",
        claims=[
            Claim(
                id="c",
                text="A result.",
                evidence_refs=["r"],
                qualifiers=["single topic"],
            )
        ],
        sections=[
            SectionPlan(
                id="results",
                title="Results",
                claim_ids=["c"],
                paragraphs=[Paragraph(id="p", text="A result.", claim_ids=["c"])],
            )
        ],
        assets=[
            AssetBrief(
                id="a",
                question="What moved?",
                claim_ids=["c"],
                evidence_refs=["r"],
                form="ladder_table",
                takeaway="A result.",
                caption_outline="A result.",
            )
        ],
    )
    findings = writeup.deterministic_audit(plan, {"evidence_refs": {"r": {}}}, set())

    assert {finding["status"] for finding in findings} == {"missing_qualification", "uncited"}


def test_section_validation_rejects_wrong_magnitude_and_unknown_qualifier() -> None:
    plan = ManuscriptPlan(
        title="Test",
        claims=[
            Claim(
                id="c",
                text="A result.",
                evidence_refs=["r"],
                qualifiers=["checkpoint twenty-four"],
            )
        ],
        sections=[SectionPlan(id="results", title="Results", claim_ids=["c"])],
    )
    synthesis = {
        "facts": [{"id": "f", "value": 0.01, "evidence_refs": ["r"]}],
        "evidence_refs": {"r": {}},
    }
    with pytest.raises(ValueError, match="unsupported numbers"):
        writeup.validate_section_payload(
            {
                "paragraphs": [
                    {
                        "id": "p",
                        "text": "The result was 0.99.",
                        "claim_ids": ["c"],
                        "qualifiers": ["checkpoint twenty-four"],
                    }
                ]
            },
            plan.sections[0],
            plan,
            synthesis,
        )
    with pytest.raises(ValueError, match="unknown qualifiers"):
        writeup.validate_section_payload(
            {
                "paragraphs": [
                    {
                        "id": "p",
                        "text": "The result was bounded.",
                        "claim_ids": ["c"],
                        "qualifiers": ["endpoint"],
                    }
                ]
            },
            plan.sections[0],
            plan,
            synthesis,
        )
    context_synthesis = {
        "facts": [],
        "evidence_refs": {},
        "asset_evidence": {},
        "context_evidence": {"r": {}},
        "context_values": {"r": "model-4"},
    }
    paragraphs = writeup.validate_section_payload(
        {
            "paragraphs": [
                {
                    "id": "p",
                    "text": "The recorded model is model-4.",
                    "claim_ids": ["c"],
                    "qualifiers": ["checkpoint twenty-four"],
                }
            ]
        },
        plan.sections[0],
        plan,
        context_synthesis,
    )
    assert paragraphs[0].text == "The recorded model is model-4."


def test_section_prompt_includes_only_claim_relevant_synthesis() -> None:
    relevant_ref = "source:belief_summary.yaml:/delta_net/delta"
    unrelated_ref = "other:belief_summary.yaml:/delta_net/delta"
    plan = ManuscriptPlan(
        title="Test",
        claims=[
            Claim(id="c", text="A bounded result.", evidence_refs=[relevant_ref]),
        ],
        sections=[SectionPlan(id="results", title="Results", claim_ids=["c"])],
    )
    synthesis = {
        "facts": [
            {"id": "relevant", "value": 0.01, "evidence_refs": [relevant_ref]},
            {"id": "unrelated", "value": 0.99, "evidence_refs": [unrelated_ref]},
        ],
        "evidence_refs": {
            relevant_ref: {"pointer": "/delta_net/delta"},
            unrelated_ref: {"pointer": "/delta_net/delta"},
        },
        "context_evidence": {},
        "asset_evidence": {},
    }

    prompt = writeup._section_prompt(
        plan.sections[0],
        plan,
        {"authoring_context": {"interpretation_rules": []}},
        synthesis,
    )

    assert relevant_ref in prompt
    assert '"id": "relevant"' in prompt
    assert unrelated_ref not in prompt
    assert '"id": "unrelated"' not in prompt


@pytest.mark.parametrize(
    "text",
    [
        "The intervals do not overlap across seeds.",
        "The three seeds do not agree in sign.",
        "The control contrast does not replicate at the third seed.",
    ],
)
def test_section_validation_allows_ordinary_negation(text: str) -> None:
    """Negated FINDINGS are not writer-facing directives.

    Regression test for 2026-08-22: `_META_DIRECTIVE` matched a bare "do not", which
    rejected exactly the sentences this project needs in order to report a null or a
    non-replication. The rule now requires a directive verb after the negation.
    """
    plan = ManuscriptPlan(
        title="Test",
        claims=[Claim(id="c", text="A framing claim.", empirical=False)],
        sections=[SectionPlan(id="results", title="Results", claim_ids=["c"])],
    )
    payload = writeup.validate_section_payload(
        {"paragraphs": [{"id": "p", "text": text, "claim_ids": ["c"], "qualifiers": []}]},
        plan.sections[0],
        plan,
        {},
    )
    assert payload[0].text == text


def test_section_validation_rejects_writer_facing_directives() -> None:
    plan = ManuscriptPlan(
        title="Test",
        claims=[Claim(id="c", text="A framing claim.", empirical=False)],
        sections=[SectionPlan(id="results", title="Results", claim_ids=["c"])],
    )

    with pytest.raises(ValueError, match="writer-facing directive"):
        writeup.validate_section_payload(
            {
                "paragraphs": [
                    {
                        "id": "p",
                        "text": "The paper should present this carefully.",
                        "claim_ids": ["c"],
                        "qualifiers": [],
                    }
                ]
            },
            plan.sections[0],
            plan,
            {"facts": []},
        )


def test_rewritten_section_reanchors_floats_to_existing_paragraph() -> None:
    section = SectionPlan(
        id="results",
        title="Results",
        claim_ids=["c"],
        floats=[
            FloatPlacement(asset_id="a", after_paragraph_id="old-paragraph")
        ],
    )
    plan = ManuscriptPlan(
        title="Test",
        claims=[Claim(id="c", text="A result.", empirical=False)],
        sections=[section],
    )

    class Client:
        async def complete_tool(self, *_args, **_kwargs):
            return {
                "paragraphs": [
                    {
                        "id": "new-paragraph",
                        "text": "The result is bounded.",
                        "claim_ids": ["c"],
                        "qualifiers": [],
                    }
                ]
            }

    rewritten = asyncio.run(
        writeup.write_section(
            Client(),
            section,
            plan,
            {"authoring_context": {"interpretation_rules": []}},
            {"facts": []},
            force=False,
        )
    )

    assert rewritten.floats[0].after_paragraph_id == "new-paragraph"


def test_auditor_derives_approval_from_complete_findings() -> None:
    plan = ManuscriptPlan(
        title="Test",
        claims=[
            Claim(id="c1", text="First.", evidence_refs=[], empirical=False),
            Claim(id="c2", text="Second.", evidence_refs=[], empirical=False),
        ],
        sections=[
            SectionPlan(
                id="results",
                title="Results",
                claim_ids=["c1", "c2"],
                paragraphs=[
                    Paragraph(id="p", text="First and second.", claim_ids=["c1", "c2"])
                ],
            )
        ],
    )

    class Client:
        async def complete_tool(self, *_args, **_kwargs):
            return {
                "approved": True,
                "findings": [
                    {"claim_id": "c1", "status": "overstated", "detail": "Overclaim."},
                    {"claim_id": "c2", "status": "supported", "detail": "Supported."},
                ],
            }

    review = asyncio.run(
        writeup.audit_manuscript(
            Client(), plan, {"evidence_refs": {}}, {"facts": []}, [], force=False
        )
    )

    assert review["approved"] is False


def test_structured_renderer_interleaves_main_float_and_routes_appendix(tmp_path: Path) -> None:
    plan = ManuscriptPlan(
        title="Miniature",
        claims=[Claim(id="c", text="A bounded result.", evidence_refs=["r"])],
        sections=[
            SectionPlan(
                id="abstract",
                title="Abstract",
                claim_ids=["c"],
                paragraphs=[Paragraph(id="abstract-p", text="A bounded result.", claim_ids=["c"])],
            ),
            SectionPlan(
                id="results",
                title="Results",
                claim_ids=["c"],
                paragraphs=[Paragraph(id="results-p", text="The result is recorded.", claim_ids=["c"])],
                floats=[
                    FloatPlacement(asset_id="ladder", after_paragraph_id="results-p"),
                    FloatPlacement(asset_id="trajectory", after_paragraph_id="results-p", appendix=True),
                ],
            ),
        ],
        assets=[
            AssetBrief(
                id="ladder",
                question="What moved?",
                claim_ids=["c"],
                evidence_refs=["r"],
                form="ladder_table",
                takeaway="A bounded result.",
                caption_outline="The contribution ladder.",
            ),
            AssetBrief(
                id="trajectory",
                question="When did it move?",
                claim_ids=["c"],
                evidence_refs=["r"],
                form="trajectory_figure",
                placement="appendix",
                takeaway="The trajectory is diagnostic.",
                caption_outline="Recorded checkpoint trajectory.",
            ),
        ],
    )
    synthesis = {
        "facts": [
            {
                "id": "f",
                "label": "Evidence",
                "value": 0.01,
                "ci95": [0.0, 0.02],
                "evidence_refs": ["r"],
            }
        ]
    }
    text = writeup.render_manuscript_latex(
        output_dir=tmp_path,
        spec=writeup.WriteupSpec(title="Miniature"),
        plan=plan,
        built_tables={"ladder": tables.ladder_table(synthesis)},
        built_figures={
            "trajectory": {
                "path": "figures/trajectory.png",
                "caption": "Source caption",
                "source_run": "source",
            }
        },
    ).read_text()

    assert text.index("The result is recorded.") < text.index("\\label{tab:contribution_ladder}")
    assert "\\begin{table}[H]" in text
    assert "\\appendix" in text
    assert "\\label{fig:trajectory}" in text


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
    def __init__(
        self,
        *,
        context: RunContext | None = None,
        model: str = "test-authoring-model",
        **_: object,
    ) -> None:
        self.context = context
        self.model = model
        self.section_index = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def complete_tool(self, _prompt: str, tool, **_: object) -> dict[str, object]:  # noqa: ANN001
        if tool.name == "write_short_paper":
            return _draft()
        if tool.name == "plan_grounded_manuscript":
            trajectory_ref = "source:trajectory.jsonl:/"
            return {
                "claims": [
                    {
                        "id": "scope",
                        "text": "The experiment provides a bounded test.",
                        "evidence_refs": [trajectory_ref],
                        "qualifiers": [],
                        "empirical": False,
                    }
                ],
                "sections": [
                    {
                        "id": section,
                        "title": section.title(),
                        "claim_ids": ["scope"],
                        "asset_ids": ["trajectory"] if section == "results" else [],
                    }
                    for section in (
                        "abstract",
                        "introduction",
                        "methods",
                        "results",
                        "discussion",
                        "limitations",
                        "conclusion",
                    )
                ],
                "assets": [
                    {
                        "id": "trajectory",
                        "question": "How do the readings change by checkpoint?",
                        "claim_ids": ["scope"],
                        "evidence_refs": [trajectory_ref],
                        "form": "trajectory_figure",
                        "axes_or_columns": ["optimizer step", "score"],
                        "placement": "results",
                        "takeaway": "The trajectory is diagnostic.",
                        "caption_outline": "Recorded checkpoint trajectory.",
                        "transformation": "trajectory",
                    }
                ],
            }
        if tool.name == "write_grounded_section":
            self.section_index += 1
            return {
                "paragraphs": [
                    {
                        "id": f"paragraph-{self.section_index}",
                        "text": "The experiment provides a bounded test.",
                        "claim_ids": ["scope"],
                        "qualifiers": [],
                    }
                ]
            }
        if tool.name == "audit_grounded_manuscript":
            return {
                "approved": True,
                "findings": [
                    {"claim_id": "scope", "status": "supported", "detail": "Supported."}
                ],
            }
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
                "writeup.author_model=test-authoring-model",
                "writeup.reviewer_model=test-reviewer-model",
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
    written_evidence = json.loads((output / "evidence.json").read_text())
    assert written_evidence["authoring_model"] == "test-authoring-model"
    assert written_evidence["reviewer_model"] == "test-reviewer-model"
    assert (output / "synthesis.json").exists()
    assert (output / "source_map.json").exists()
    assert "## Manuscript" in (output / "report.md").read_text()


def test_claim_validation_accepts_table_formatted_trailing_zero() -> None:
    """A numeral quoted in the project's own `+.4f` table format must validate.

    Regression for 2026-08-23: `_round_for_display` rounds the excerpt to four decimals and
    `json.dumps` drops trailing zeros, so an AF of -0.91298 reaches the author as "-0.913"
    while every rendered table shows "-0.9130". Substring matching alone rejected the author
    for quoting the table correctly, which killed a real writeup run.
    """
    ref_id = "attrib_mix_v4:af_summary.yaml:/af_tracin_p10_s42/delta"
    plan = writeup.validate_manuscript_plan(
        {
            "claims": [
                {
                    "id": "counterproductive",
                    "text": "Removal at the narrow budget scored -0.9130.",
                    "evidence_refs": [ref_id],
                    "qualifiers": [],
                    "empirical": True,
                }
            ],
            "sections": [
                {
                    "id": "results",
                    "title": "Results",
                    "claim_ids": ["counterproductive"],
                    "asset_ids": [],
                }
            ],
            "assets": [],
        },
        evidence={
            "evidence_refs": {
                ref_id: {
                    "run_id": "attrib_mix_v4",
                    "artifact_path": "data/results/factory_farming/attrib_mix_v4/af_summary.yaml",
                }
            }
        },
        synthesis={
            # -0.9129806 rounds to -0.913 in the excerpt; the claim quotes -0.9130.
            "facts": [{"id": "af", "value": -0.9129806, "evidence_refs": [ref_id]}],
            "evidence_refs": {ref_id: {}},
            "asset_evidence": {},
            "context_evidence": {},
        },
        spec=writeup.WriteupSpec(required_sections=["results"]),
    )

    assert plan.claims[0].id == "counterproductive"


def test_claim_validation_still_rejects_a_number_absent_from_evidence() -> None:
    """The widening above must not let an invented number through."""
    ref_id = "attrib_mix_v4:af_summary.yaml:/af_tracin_p10_s42/delta"
    with pytest.raises(ValueError, match="unsupported numbers"):
        writeup.validate_manuscript_plan(
            {
                "claims": [
                    {
                        "id": "invented",
                        "text": "Removal at the narrow budget scored -0.7777.",
                        "evidence_refs": [ref_id],
                        "qualifiers": [],
                        "empirical": True,
                    }
                ],
                "sections": [
                    {
                        "id": "results",
                        "title": "Results",
                        "claim_ids": ["invented"],
                        "asset_ids": [],
                    }
                ],
                "assets": [],
            },
            evidence={
                "evidence_refs": {
                    ref_id: {
                        "run_id": "attrib_mix_v4",
                        "artifact_path": "data/results/factory_farming/attrib_mix_v4/af_summary.yaml",
                    }
                }
            },
            synthesis={
                "facts": [{"id": "af", "value": -0.9129806, "evidence_refs": [ref_id]}],
                "evidence_refs": {ref_id: {}},
                "asset_evidence": {},
                "context_evidence": {},
            },
            spec=writeup.WriteupSpec(required_sections=["results"]),
        )


def test_numeral_check_skips_digits_inside_alphanumeric_tokens() -> None:
    """A model name is not a numeral claim: "Qwen3-4B" must not fail as the value 4."""
    assert writeup._unsupported_numbers(
        "Removal arms fine-tune Qwen3-4B and score with e5-base-v2.", "{}"
    ) == []
    # But a real invented number, even next to a word, is still caught.
    assert writeup._unsupported_numbers("The effect was 0.7777 overall.", "{}") == ["0.7777"]
