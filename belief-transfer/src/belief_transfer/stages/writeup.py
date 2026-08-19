"""stage=writeup: render a grounded short paper from declared result bundles."""

from __future__ import annotations

import json

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
    figures = writeup.copy_trajectory_figures(
        evidence, trajectory_run=job.writeup.trajectory_run, output_dir=output_dir
    )
    evidence["figures"] = figures
    evidence_path = writeup.write_evidence(evidence, output_dir / writeup.EVIDENCE_FILENAME)

    context = RunContext()
    async with Client(throughput=job.throughput, context=context) as client:
        draft = await writeup.draft_sections(client, evidence, force=job.force)
        review: dict[str, object] = {"approved": True, "corrections": []}
        if job.writeup.review:
            review = await writeup.review_draft(client, evidence, draft, force=job.force)
            if not review["approved"]:
                draft = await writeup.draft_sections(
                    client, evidence, force=job.force, corrections=review["corrections"]  # type: ignore[arg-type]
                )
                review = await writeup.review_draft(client, evidence, draft, force=job.force)
                if not review["approved"]:
                    raise ValueError("writeup reviewer rejected the corrected draft")

    draft_path = output_dir / writeup.DRAFT_FILENAME
    draft_path.write_text(json.dumps(draft, indent=2, sort_keys=True) + "\n")
    review_path = output_dir / writeup.REVIEW_FILENAME
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    tex_path = writeup.render_latex(
        output_dir=output_dir,
        spec=job.writeup,
        evidence=evidence,
        draft=draft,
        figures=figures,
    )
    artifacts = [evidence_path, draft_path, review_path, tex_path, *(output_dir / figure["path"] for figure in figures)]
    if job.writeup.references_bib:
        references_path = output_dir / writeup.REFERENCES_FILENAME
        references_path.write_text(job.writeup.references_bib.rstrip() + "\n")
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
            }
        },
        backend=None,
        config_sha=config_sha(job),
    )
    report_path = write_result(result, path=out_path(job.experiment.id, job.run_id, "writeup"))
    write_resolved_config(job, report_path.parent)
    markdown.write_report(output_dir)
    return result
