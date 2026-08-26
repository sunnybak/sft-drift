"""Render one run's results directory as `report.md`.

The gap this fills. A run's directory holds a stage report per stage, a summary per suite,
raw responses, a tidy trajectory, and two figures -- everything needed to state the result
and nothing that states it. Every number reported out of this project so far was assembled
by an ad-hoc script at the moment it was needed, which is how a stale one survives: there
is no single artifact to notice it in.

Follows `dataset.review` / `evals.review`, which already do this for corpora: read what is
on disk, render markdown next to it, own no numbers of your own. Every figure here is a
relative link so the file travels with its directory, and every table is read from the
recorded YAML rather than recomputed -- a report that recomputed could disagree with the
artifacts it summarises, which is the one thing it must never do.

Degrades by section: a run that only did `choice_bench` renders the gate table and says
plainly that the rest was not run, rather than failing or implying a null result.
"""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import yaml

from belief_transfer.analysis import tables

REPORT_FILENAME = "report.md"

# (filename, heading) for the per-suite measurement files, in reporting order.
_SUITES = [
    ("belief_summary.yaml", "Belief"),
    ("action_summary.yaml", "Action"),
    ("inference_summary.yaml", "Inference (descriptive)"),
]


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text())


def _gate_section(results_dir: Path) -> list[str]:
    report = _load(results_dir / "choice_bench.yaml")
    if not report:
        return ["## Gate — choice_bench", "", "_Not run._", ""]
    table = replace(
        tables.choice_gate_table(report),
        heading="Gate — choice_bench",
        note="Run first; nothing read off a failing arm is interpretable (AGENTS.md, Efficacy).",
    )
    return tables.render_markdown(table)


def _absorption_section(results_dir: Path) -> list[str]:
    report = _load(results_dir / "absorption.yaml")
    if not report:
        return ["## Efficacy — absorption", "", "_Not run._", ""]
    return tables.render_markdown(
        replace(tables.absorption_table(report), heading="Efficacy — absorption (netted, held-out)")
    )


def _suite_section(results_dir: Path, filename: str, heading: str) -> list[str]:
    summary = _load(results_dir / filename)
    if not summary:
        return [f"## {heading}", "", "_Not run._", ""]
    lines = [f"## {heading}", "", "| arm | score | 95% CI |", "|---|---|---|"]
    for arm, entry in summary["arms"].items():
        low, high = entry["ci95"]
        lines.append(f"| `{arm}` | {entry['score']:.4f} | [{low:.3f}, {high:.3f}] |")
    config = _load(results_dir / "config.resolved.yaml") or {}
    transfer = tables.transfer_table(
        summary,
        source_run=str(summary.get("run_id") or config.get("run_id", "unknown")),
        artifact=filename,
    )
    lines += ["", *tables.render_markdown(replace(transfer, heading="Recorded contrast"))]
    return lines


def _figures_section(results_dir: Path) -> list[str]:
    figures = sorted([*results_dir.glob("*.png"), *(results_dir / "figures").glob("*.png")])
    if not figures:
        return []
    lines = ["## Figures", ""]
    for figure in figures:
        lines += [f"### {figure.stem.replace('_', ' ')}", "",
                  f"![{figure.stem}]({figure.relative_to(results_dir)})", ""]
    return lines


def _manuscript_section(results_dir: Path) -> list[str]:
    """Link the writeup bundle when this directory is a paper run."""
    artifacts = [
        ("paper.pdf", "compiled PDF"),
        ("paper.tex", "LaTeX source"),
        ("evidence.json", "grounding evidence"),
        ("synthesis.json", "deterministic synthesis"),
        ("manuscript_plan.json", "manuscript plan"),
        ("asset_briefs.json", "accepted asset briefs"),
        ("source_map.json", "bidirectional source map"),
        ("draft.json", "structured draft"),
        ("review.json", "grounding review"),
        ("references.bib", "curated references"),
        ("compile.log", "LaTeX compilation log"),
    ]
    present = [(filename, label) for filename, label in artifacts if (results_dir / filename).exists()]
    if not present:
        return []
    lines = ["## Manuscript", ""]
    lines += [f"- [{label}]({filename})" for filename, label in present]
    return lines + [""]


def _source_readings_section(results_dir: Path) -> list[str]:
    """Paper runs expose their declared source measurements rather than empty local stages."""
    evidence_path = results_dir / "evidence.json"
    if not evidence_path.exists():
        return []
    try:
        evidence = json.loads(evidence_path.read_text())
    except json.JSONDecodeError:
        return []
    if not isinstance(evidence, dict) or not isinstance(evidence.get("sources"), dict):
        return []
    models = tables.evidence_tables(evidence)
    if not models:
        return []
    lines = ["## Source readings", "", "Fixed tables read from the declared evidence packet.", ""]
    for table in models:
        lines.extend(tables.render_markdown(table))
    return lines


def _related_section(results_dir: Path) -> list[str]:
    """Links to the sibling runs this one declares (`JobConfig.related_runs`).

    Read from `config.resolved.yaml` rather than from a `RunResult` field: the relation is
    something the *run was configured with*, and the resolved config is the record of that.
    This is the one place the report reads that file deliberately -- `_provenance_section`
    skips it, since a serialized JobConfig also carries a `stage` and would otherwise be
    counted as a stage report.
    """
    resolved = _load(results_dir / "config.resolved.yaml")
    related = (resolved or {}).get("related_runs") or {}
    if not related:
        return []
    lines = ["## Related readings", "",
             "The same experiment recorded under another run id. One run id names one set "
             "of artifacts, so a second reading is a second directory -- these are the "
             "links between them.", ""]
    for run_id, why in related.items():
        lines.append(f"- [`{run_id}`](../{run_id}/{REPORT_FILENAME}) — {why}")
    return lines + [""]


def _provenance_section(results_dir: Path) -> list[str]:
    stages, cost = [], 0.0
    for path in sorted(results_dir.glob("*.yaml")):
        report = _load(path)
        # `stage` alone is not enough to identify a run report: config.resolved.yaml is a
        # serialized JobConfig and carries the stage it was resolved for, so keying on it
        # listed the last stage twice and out of order. A RunResult is what has last_run.
        if not isinstance(report, dict) or "last_run" not in report:
            continue
        stages.append(report)
        cost += float((report.get("lifetime") or {}).get("cost_usd", 0.0) or 0.0)
    if not stages:
        return []
    newest = stages[-1]
    lines = ["## Provenance", "",
             f"- experiment `{newest['experiment']}`, run `{newest['run_id']}`",
             f"- code revision `{newest.get('code_revision')}`, "
             f"config sha `{newest.get('config_sha')}`",
             f"- stages run: " + ", ".join(f"`{s['stage']}`" for s in stages),
             f"- lifetime LLM cost across those stages: ${cost:.2f}",
             "- resolved config: [`config.resolved.yaml`](config.resolved.yaml)", ""]
    return lines


def render_report(results_dir: Path) -> str:
    """The markdown for one results directory. Pure: reads files, owns no numbers."""
    title = results_dir.name
    lines = [f"# {title}", "",
             "Generated by `stage=report` from the artifacts in this directory. Every "
             "number is read from the recorded YAML, never recomputed.", ""]
    source_readings = _source_readings_section(results_dir)
    if source_readings:
        lines += source_readings
    else:
        lines += _gate_section(results_dir)
        lines += _absorption_section(results_dir)
        for filename, heading in _SUITES:
            lines += _suite_section(results_dir, filename, heading)
    lines += _figures_section(results_dir)
    lines += _manuscript_section(results_dir)
    lines += _related_section(results_dir)
    lines += _provenance_section(results_dir)
    return "\n".join(lines).rstrip() + "\n"


def write_report(results_dir: Path) -> Path:
    """Render and write `report.md` into `results_dir`."""
    out_path = results_dir / REPORT_FILENAME
    out_path.write_text(render_report(results_dir), encoding="utf-8")
    return out_path
