"""Grounded short-paper drafting and deterministic LaTeX rendering.

This module deliberately treats recorded result artifacts as the source of truth.  The
language model only writes digit-free prose around fixed tables/figures rendered by Python;
it cannot invent or alter a reported numerical result.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from belief_transfer.analysis import markdown, plots, tables
from belief_transfer.analysis.report import RESULTS_DIR
from belief_transfer.generation.llm import Client, Tool
from belief_transfer.schemas import WriteupSpec, file_sha

TEMPLATE_DIR = Path(__file__).with_name("templates")
PAPER_FILENAME = "paper.tex"
PDF_FILENAME = "paper.pdf"
EVIDENCE_FILENAME = "evidence.json"
DRAFT_FILENAME = "draft.json"
REVIEW_FILENAME = "review.json"
COMPILE_LOG_FILENAME = "compile.log"
REFERENCES_FILENAME = "references.bib"

_SUMMARY_FILES = (
    "choice_bench.yaml",
    "absorption.yaml",
    "sensitivity_summary.yaml",
    "belief_summary.yaml",
    "action_summary.yaml",
)
_SECTIONS = ("abstract", "introduction", "methods", "results", "limitations", "conclusion")
_FORBIDDEN_PROSE = re.compile(r"(\\|[${}])")
_NUMBER = re.compile(r"(?<![\w.])[+-]?\d+(?:\.\d+)?%?")

_DRAFT_TOOL = Tool(
    name="write_short_paper",
    description="Write concise, grounded prose sections for a short research paper.",
    parameters={
        "type": "object",
        "properties": {
            section: {"type": "string"} for section in _SECTIONS
        }
        | {"evidence_ids": {"type": "array", "items": {"type": "string"}}},
        "required": [*_SECTIONS, "evidence_ids"],
        "additionalProperties": False,
    },
)

_REVIEW_TOOL = Tool(
    name="review_grounding",
    description="Check whether a draft is supported by the supplied evidence.",
    parameters={
        "type": "object",
        "properties": {
            "approved": {"type": "boolean"},
            "corrections": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["approved", "corrections"],
        "additionalProperties": False,
    },
)


def _load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = yaml.safe_load(path.read_text())
    return value if isinstance(value, dict) else None


def source_directory(experiment_id: str, run_id: str) -> Path:
    return RESULTS_DIR / experiment_id / run_id


def _authoring_context(sources: dict[str, Any], *, primary_reading: str, endpoint_absorption: str | None) -> dict[str, Any]:
    """Small, explicit project context for prose; measurements remain in source artifacts."""
    primary_config = sources[primary_reading].get("resolved_config") or {}
    experiment = primary_config.get("experiment") or {}
    belief = experiment.get("belief") or {}
    action = experiment.get("action") or {}
    return {
        "experiment": {
            "target_belief": belief.get("statement", ""),
            "downstream_action": action.get("description", ""),
        },
        "readings": {
            "primary_reading": primary_reading,
            "endpoint_absorption": endpoint_absorption,
        },
        "interpretation_rules": [
            "This is an exploratory, single-seed result unless a recorded artifact says otherwise.",
            "Absorption is held-out premise specialization, not a belief measure.",
            "Belief and action contrasts require their matched off-topic control netting; do not claim causal mediation.",
            "Raw belief/action checkpoint figures are diagnostic and are not netted transfer estimates.",
            "Fixed tables, not prose, are authoritative for numerical estimates and confidence intervals.",
        ],
    }


def collect_evidence(experiment_id: str, spec: WriteupSpec) -> dict[str, Any]:
    """Read declared result bundles without modifying their historical artifacts."""
    if not spec.source_runs:
        raise ValueError("writeup.source_runs must name at least one completed result run")
    primary_reading = spec.primary_reading or spec.source_runs[0]
    if primary_reading not in spec.source_runs:
        raise ValueError("writeup.primary_reading must also appear in writeup.source_runs")
    sources: dict[str, Any] = {}
    for run_id in spec.source_runs:
        directory = source_directory(experiment_id, run_id)
        if not directory.exists():
            raise FileNotFoundError(f"writeup source run {run_id!r} has no results at {directory}")
        summaries = {
            filename: value
            for filename in _SUMMARY_FILES
            if (value := _load_yaml(directory / filename)) is not None
        }
        sources[run_id] = {
            "run_id": run_id,
            "directory": str(directory),
            # A source report may not exist yet (for example, a locally copied fixture).
            # Render an in-memory view in that case; do not rewrite a historical source run.
            "report": markdown.REPORT_FILENAME,
            "report_markdown": (directory / markdown.REPORT_FILENAME).read_text()
            if (directory / markdown.REPORT_FILENAME).exists()
            else markdown.render_report(directory),
            "summaries": summaries,
            "resolved_config": _load_yaml(directory / "config.resolved.yaml"),
            "figures": [path.name for path in sorted(directory.glob("*.png"))],
            "artifact_manifest": [
                {
                    "filename": path.name,
                    "path": str(path),
                    "sha256": file_sha(path, length=64),
                }
                for path in sorted(directory.iterdir())
                if path.is_file() and path.name in {*_SUMMARY_FILES, "config.resolved.yaml", markdown.REPORT_FILENAME}
            ],
        }
        for filename, summary in summaries.items():
            declared_run = summary.get("run_id")
            if declared_run is not None and declared_run != run_id:
                raise ValueError(
                    f"{run_id}/{filename} declares run_id {declared_run!r}, not its source directory"
                )
    absorption_runs = [run_id for run_id, source in sources.items() if "absorption.yaml" in source["summaries"]]
    endpoint_absorption = spec.trajectory_run if spec.trajectory_run in absorption_runs else None
    if endpoint_absorption is None and len(absorption_runs) == 1:
        endpoint_absorption = absorption_runs[0]
    evidence = {
        "experiment": experiment_id,
        "intended_claim": spec.intended_claim,
        "primary_reading": primary_reading,
        "endpoint_absorption": endpoint_absorption,
        "sources": sources,
    }
    evidence["authoring_context"] = _authoring_context(
        sources, primary_reading=primary_reading, endpoint_absorption=endpoint_absorption
    )
    hashes = {
        (run_id, artifact["filename"]): artifact["sha256"]
        for run_id, source in sources.items()
        for artifact in source["artifact_manifest"]
    }
    evidence["table_manifest"] = [
        {
            "id": table.id,
            "source_run": table.source.run_id,
            "artifact": table.source.artifact,
            "sha256": hashes.get((table.source.run_id, table.source.artifact)),
        }
        for table in _result_tables(evidence)
    ]
    return evidence


def copy_trajectory_figures(
    evidence: dict[str, Any], *, trajectory_run: str | None, output_dir: Path
) -> list[dict[str, str]]:
    """Render paper figures from declared tidy trajectory rows, leaving source runs untouched."""
    if trajectory_run is None:
        return []
    sources = evidence["sources"]
    if trajectory_run not in sources:
        raise ValueError("writeup.trajectory_run must also appear in writeup.source_runs")
    source = Path(sources[trajectory_run]["directory"])
    if not (source / "trajectory.jsonl").exists():
        raise FileNotFoundError(f"{trajectory_run!r} has no trajectory.jsonl provenance artifact")
    trajectory_rows = [
        json.loads(line)
        for line in (source / "trajectory.jsonl").read_text().splitlines()
        if line.strip()
    ]
    checkpoints = sorted({str(row["step"]) for row in trajectory_rows if "step" in row})
    instruments = sorted({str(row["eval_type"]) for row in trajectory_rows if "eval_type" in row})
    coverage = ", ".join(checkpoints) or "recorded checkpoints"
    instrument_text = ", ".join(instruments) or "recorded instruments"
    target = output_dir / "figures"
    target.mkdir(parents=True, exist_ok=True)
    figures = plots.plot_trajectory(source / "trajectory.jsonl", target)
    if not figures:
        raise ValueError(f"{trajectory_run!r} trajectory rows contain no plottable instruments")
    copied = []
    for figure in figures:
        figure_description = (
            "belief and action trajectories split by polarity"
            if figure.name == "polarity_trajectories.png"
            else figure.stem.replace("_", " ")
        )
        copied.append(
            {
                "path": str(figure.relative_to(output_dir)),
                "caption": (
                    f"{figure_description}; run {trajectory_run}; "
                    f"checkpoints {coverage}; instruments {instrument_text}"
                ),
                "source_run": trajectory_run,
            }
        )
    return copied


def write_evidence(evidence: dict[str, Any], path: Path) -> Path:
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    return path


def _prompt(evidence: dict[str, Any], corrections: list[str] | None = None) -> str:
    source_reports = "\n\n".join(
        f"RUN {run_id}\n{source['report_markdown']}"
        for run_id, source in evidence["sources"].items()
    )
    correction_text = f"\nReviewer corrections:\n{chr(10).join(corrections)}" if corrections else ""
    return f"""Write a concise research-paper draft from the recorded reports below.

The intended claim is: {evidence["intended_claim"]}

Project and interpretation context:
{json.dumps(evidence["authoring_context"], indent=2, sort_keys=True)}

Use only the listed run ids as evidence IDs. Do not state numerical values in prose: fixed
tables and figure captions carry them. Do not use LaTeX, citations, markdown, dollar signs,
or placeholders. Follow the interpretation rules above. State limitations directly, especially
any caveats recorded in the reports.
{correction_text}

Recorded reports:
{source_reports}
"""


def validate_draft(payload: dict[str, object], evidence: dict[str, Any]) -> dict[str, Any]:
    """Reject model output that could change the experimental record."""
    required = set(_SECTIONS) | {"evidence_ids"}
    if set(payload) != required:
        raise ValueError(f"draft fields must be exactly {sorted(required)}")
    for section in _SECTIONS:
        text = payload[section]
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"draft section {section!r} must be non-empty text")
        if _FORBIDDEN_PROSE.search(text):
            raise ValueError(f"draft section {section!r} contains raw LaTeX syntax")
        # Prose may need to name a configured checkpoint (for example, step 24), but it
        # cannot introduce a numeric value absent from the evidence packet. Fixed result
        # tables remain the normal location for estimates and confidence intervals.
        evidence_text = json.dumps(evidence, sort_keys=True)
        unknown_numbers = [
            value for value in _NUMBER.findall(text) if value.removesuffix("%") not in evidence_text
        ]
        if unknown_numbers:
            raise ValueError(f"draft section {section!r} contains unsupported numbers: {unknown_numbers}")
    identifiers = payload["evidence_ids"]
    if not isinstance(identifiers, list) or not all(isinstance(value, str) for value in identifiers):
        raise ValueError("draft evidence_ids must be a list of source run ids")
    # The prompt labels each report as `RUN <id>` for readability; normalize that display
    # label back to the stable run-id key before applying the grounding check.
    identifiers = [value.removeprefix("RUN ").strip() for value in identifiers]
    unknown = set(identifiers) - set(evidence["sources"])
    if unknown:
        raise ValueError(f"draft references undeclared evidence ids: {sorted(unknown)}")
    if not identifiers:
        raise ValueError("draft must reference at least one source run")
    return {**{key: payload[key] for key in _SECTIONS}, "evidence_ids": identifiers}


async def draft_sections(
    client: Client, evidence: dict[str, Any], *, force: bool, corrections: list[str] | None = None
) -> dict[str, Any]:
    payload = await client.complete_tool(
        _prompt(evidence, corrections),
        _DRAFT_TOOL,
        override_cache=force,
    )
    try:
        return validate_draft(payload, evidence)
    except ValueError as exc:
        # A failed schema/grounding check must be visible to the authoring model. This is
        # intentionally one bounded retry rather than accepting a malformed draft or
        # entering an open-ended author/reviewer loop.
        retry_payload = await client.complete_tool(
            _prompt(evidence, [f"Your previous draft was rejected: {exc}. Rewrite every section to comply."]),
            _DRAFT_TOOL,
            override_cache=force,
        )
        return validate_draft(retry_payload, evidence)


async def review_draft(client: Client, evidence: dict[str, Any], draft: dict[str, Any], *, force: bool) -> dict[str, Any]:
    prompt = f"""Check this paper prose against its recorded evidence. It must not overclaim,
omit material limitations, or refer to a source run that was not declared.

Evidence IDs: {sorted(evidence["sources"])}
Intended claim: {evidence["intended_claim"]}
Draft: {json.dumps(draft, sort_keys=True)}
"""
    payload = await client.complete_tool(prompt, _REVIEW_TOOL, override_cache=force)
    if not isinstance(payload.get("approved"), bool) or not isinstance(payload.get("corrections"), list):
        raise ValueError("review must return approved plus a corrections list")
    if not all(isinstance(item, str) for item in payload["corrections"]):
        raise ValueError("review corrections must be text")
    return {"approved": payload["approved"], "corrections": payload["corrections"]}


def _escape(value: str) -> str:
    return (
        value.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


def _result_tables(evidence: dict[str, Any]) -> list[tables.ResultTable]:
    """Fixed, provenance-carrying tables in the paper's declared reading order."""
    result: list[tables.ResultTable] = []
    sources = evidence["sources"]
    endpoint = evidence.get("endpoint_absorption")
    primary = evidence["primary_reading"]

    if endpoint and (choice := sources[endpoint]["summaries"].get("choice_bench.yaml")):
        result.append(tables.choice_gate_table(choice))
    if primary != endpoint and (choice := sources[primary]["summaries"].get("choice_bench.yaml")):
        result.append(tables.choice_gate_table(choice))
    if endpoint and (absorption := sources[endpoint]["summaries"].get("absorption.yaml")):
        table = tables.absorption_table(absorption)
        qualification = (
            " Absorption measures premise specialization, not belief."
            " No absorption reading exists for the primary checkpoint."
            if primary != endpoint
            else " Absorption measures premise specialization, not belief."
        )
        if choice := sources[endpoint]["summaries"].get("choice_bench.yaml"):
            failed_controls = [
                control
                for _, control in absorption["metrics"]["net_pairs"]
                if control in choice["metrics"]["choice"]
                and not choice["metrics"]["choice"][control]["passed"]
            ]
            if failed_controls:
                qualification += (
                    " Estimates relying on failed control arm(s) "
                    + ", ".join(failed_controls)
                    + " are displayed but qualified."
                )
        result.append(replace(table, note=table.note + qualification))

    for run_id, source in sources.items():
        for filename in ("belief_summary.yaml", "action_summary.yaml", "sensitivity_summary.yaml"):
            if summary := source["summaries"].get(filename):
                result.append(tables.transfer_table(summary, source_run=run_id, artifact=filename))
    return result


def render_latex(
    *,
    output_dir: Path,
    spec: WriteupSpec,
    evidence: dict[str, Any],
    draft: dict[str, Any],
    figures: list[dict[str, str]],
) -> Path:
    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    template = environment.get_template("short_paper.tex.j2")
    rendered = template.render(
        title=_escape(spec.title),
        authors=", ".join(_escape(author) for author in spec.authors) or "Anonymous",
        sections={name: _escape(draft[name]) for name in _SECTIONS},
        figures=[
            {**figure, "caption": _escape(figure["caption"]), "source_run": _escape(figure["source_run"])}
            for figure in figures
        ],
        tables=[
            {
                **tables.latex_table(table),
                "heading": _escape(table.heading),
                "columns": [_escape(column) for column in table.columns],
                "rows": [
                    [
                        {
                            "text": _escape(cell["text"]),
                            "bold": cell["bold"],
                            "bold_text": _escape(cell["bold_text"]) if cell["bold_text"] else None,
                        }
                        for cell in row
                    ]
                    for row in tables.latex_table(table)["rows"]
                ],
                "caption": _escape(table.caption),
                "note": _escape(table.note),
                "source": {
                    "run_id": _escape(table.source.run_id),
                    "artifact": _escape(table.source.artifact),
                    "checkpoint": _escape(table.source.checkpoint),
                },
            }
            for table in _result_tables(evidence)
        ],
        references_bib=spec.references_bib,
    )
    path = output_dir / PAPER_FILENAME
    path.write_text(rendered)
    return path


def compile_latex(tex_path: Path, *, timeout: int = 180) -> tuple[Path, Path]:
    """Compile with tectonic; callers choose whether missing toolchain is fatal."""
    try:
        completed = subprocess.run(
            ["tectonic", "--outdir", str(tex_path.parent), str(tex_path)],
            cwd=tex_path.parent,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("tectonic is required to compile a writeup; install it or set writeup.compile_pdf=false") from exc
    log_path = tex_path.parent / COMPILE_LOG_FILENAME
    log_path.write_text(completed.stdout + completed.stderr)
    if completed.returncode:
        raise RuntimeError(f"tectonic failed; see {log_path}")
    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"tectonic succeeded but did not write {pdf_path}")
    return pdf_path, log_path
