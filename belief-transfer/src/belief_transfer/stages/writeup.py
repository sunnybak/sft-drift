"""stage=writeup: render a grounded short paper from declared result bundles."""

from __future__ import annotations

from pathlib import Path

from belief_transfer.analysis import markdown, writeup
from belief_transfer.analysis.report import build_result, out_dir, out_path, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.llm import Client
from belief_transfer.schemas import JobConfig, RunResult


async def run(job: JobConfig) -> RunResult:
    """Draft prose, render fixed evidence, then optionally compile a PDF."""
    # `out/`, not `data/results/`: a rendered paper is a deliverable, git-tracked and not
    # synced to HF. The evidence it is built from is still read from `data/results/`.
    output_dir = out_dir(job.experiment.id, job.run_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_resolved_config(job, output_dir)

    evidence = writeup.collect_evidence(job.experiment.id, job.writeup)
    synthesis = writeup.build_synthesis(evidence, job.writeup)
    synthesis_path = writeup.write_json(
        synthesis, output_dir / writeup.SYNTHESIS_FILENAME
    )

    context = RunContext()
    async with (
        Client(
            throughput=job.throughput,
            model=job.writeup.author_model,
            context=context,
        ) as author_client,
        Client(
            throughput=job.throughput,
            model=job.writeup.reviewer_model,
            context=context,
        ) as reviewer_client,
    ):
        plan = await writeup.plan_manuscript(
            author_client, evidence, synthesis, job.writeup, force=job.force
        )
        plan_path = writeup.write_json(
            plan.model_dump(mode="json"), output_dir / writeup.PLAN_FILENAME
        )
        asset_path = writeup.write_json(
            [asset.model_dump(mode="json") for asset in plan.assets],
            output_dir / writeup.ASSET_BRIEFS_FILENAME,
        )
        plan = await writeup.write_sections(
            author_client, plan, evidence, synthesis, force=job.force
        )

        figures = (
            writeup.copy_trajectory_figures(
                evidence, trajectory_run=job.writeup.trajectory_run, output_dir=output_dir
            )
            if any(asset.form == "trajectory_figure" for asset in plan.assets)
            else []
        )
        built_tables, built_figures, asset_manifest = writeup.build_assets(
            plan, evidence, synthesis, figures, af_figure_dir=output_dir / "figures"
        )
        review: dict[str, object] = {"approved": True, "findings": []}
        if job.writeup.review:
            for audit_round in range(3):
                review = await writeup.audit_manuscript(
                    reviewer_client,
                    plan,
                    evidence,
                    synthesis,
                    asset_manifest,
                    force=job.force,
                )
                writeup.write_json(review, output_dir / writeup.REVIEW_FILENAME)
                if review["approved"]:
                    break
                if audit_round == 2:
                    raise ValueError("writeup auditor rejected the corrected manuscript")
                findings = review["findings"]
                rejected_claims = {
                    str(finding["claim_id"])
                    for finding in findings  # type: ignore[union-attr]
                    if isinstance(finding, dict) and finding.get("status") != "supported"
                }
                rewritten = []
                for section in plan.sections:
                    corrections = [
                        str(finding["detail"])
                        for finding in findings  # type: ignore[union-attr]
                        if isinstance(finding, dict)
                        and finding.get("claim_id") in section.claim_ids
                    ]
                    rewritten.append(
                        await writeup.write_section(
                            author_client,
                            section,
                            plan,
                            evidence,
                            synthesis,
                            force=job.force,
                            corrections=corrections,
                        )
                        if rejected_claims.intersection(section.claim_ids)
                        else section
                    )
                plan = plan.model_copy(update={"sections": rewritten})
                writeup.write_json(
                    plan.model_dump(mode="json"), output_dir / writeup.PLAN_FILENAME
                )

    evidence["authoring_model"] = author_client.model
    evidence["reviewer_model"] = reviewer_client.model
    evidence["figures"] = figures
    evidence["asset_manifest"] = asset_manifest
    evidence_path = writeup.write_evidence(
        evidence, output_dir / writeup.EVIDENCE_FILENAME
    )
    writeup.write_json(
        plan.model_dump(mode="json"), output_dir / writeup.PLAN_FILENAME
    )
    # Keep draft.json as the prose-only compatibility view while manuscript_plan.json is
    # the authoritative structured representation.
    draft = {
        section.id: "\n\n".join(paragraph.text for paragraph in section.paragraphs)
        for section in plan.sections
    }
    draft_path = writeup.write_json(draft, output_dir / writeup.DRAFT_FILENAME)
    review_path = writeup.write_json(review, output_dir / writeup.REVIEW_FILENAME)
    source_map = writeup.build_source_map(
        plan, evidence, built_tables, built_figures
    )
    for ref in source_map.evidence.values():
        writeup.verify_evidence_ref(ref, experiment_id=job.experiment.id)
    source_map_path = writeup.write_json(
        source_map.model_dump(mode="json"), output_dir / writeup.SOURCE_MAP_FILENAME
    )
    tex_path = writeup.render_manuscript_latex(
        output_dir=output_dir,
        spec=job.writeup,
        plan=plan,
        built_tables=built_tables,
        built_figures=built_figures,
    )
    artifacts = [
        evidence_path,
        synthesis_path,
        plan_path,
        asset_path,
        draft_path,
        review_path,
        source_map_path,
        tex_path,
        *(output_dir / figure["path"] for figure in figures),
    ]
    references = job.writeup.references_bib
    if job.writeup.bibliography_path:
        references = (Path(__file__).resolve().parents[3] / job.writeup.bibliography_path).read_text()
    if references:
        references_path = output_dir / writeup.REFERENCES_FILENAME
        references_path.write_text(references.rstrip() + "\n")
        artifacts.append(references_path)
    if job.writeup.compile_pdf:
        pdf_path, log_path = writeup.compile_latex(tex_path)
        artifacts += [pdf_path, log_path]

    report_markdown = output_dir / markdown.REPORT_FILENAME
    result = build_result(
        context,
        stage="writeup",
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=len(job.writeup.source_runs),
        artifacts=[*artifacts, report_markdown],
        metrics={
            "writeup": {
                "source_runs": job.writeup.source_runs,
                "primary_reading": evidence["primary_reading"],
                "trajectory_run": job.writeup.trajectory_run,
                "reviewed": job.writeup.review,
                "compiled": job.writeup.compile_pdf,
                "claims": len(plan.claims),
                "assets": len(plan.assets),
                "authoring_model": author_client.model,
                "reviewer_model": reviewer_client.model,
            }
        },
        backend=None,
        config_sha=config_sha(job),
    )
    report_path = write_result(result, path=out_path(job.experiment.id, job.run_id, "writeup"))
    write_resolved_config(job, report_path.parent)
    markdown.write_report(output_dir)
    return result
