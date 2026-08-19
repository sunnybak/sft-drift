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

import json
from pathlib import Path
from typing import Any

import yaml

REPORT_FILENAME = "report.md"

# (filename, heading) for the per-suite measurement files, in reporting order.
_SUITES = [("belief_summary.yaml", "Belief"), ("action_summary.yaml", "Action")]


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text())


def _ci(entry: dict[str, Any], places: int = 4) -> str:
    """`+0.0641 [+0.0434, +0.0868]`, bolded when the interval excludes zero."""
    low, high = entry["ci95"]
    value = entry.get("delta", entry.get("score", entry.get("mean")))
    point = f"{value:+.{places}f}"
    if entry.get("excludes_zero"):
        point = f"**{point}**"
    return f"{point} [{low:+.{places}f}, {high:+.{places}f}]"


def _gate_section(results_dir: Path) -> list[str]:
    report = _load(results_dir / "choice_bench.yaml")
    if not report:
        return ["## Gate — choice_bench", "", "_Not run._", ""]
    lines = ["## Gate — choice_bench", "",
             "Run first; nothing read off a failing arm is interpretable "
             "(AGENTS.md, Efficacy).", "",
             "| arm | verdict | accuracy | confidence | margin |", "|---|---|---|---|---|"]
    for arm, entry in report["metrics"]["choice"].items():
        metrics = entry["metrics"]
        verdict = "PASS" if entry["passed"] else "**FAIL**"
        lines.append(f"| `{arm}` | {verdict} | {metrics['accuracy']:.3f} | "
                     f"{metrics['mean_confidence']:.3f} | {metrics['mean_margin']:.3f} |")
    return lines + [""]


def _absorption_section(results_dir: Path) -> list[str]:
    report = _load(results_dir / "absorption.yaml")
    if not report:
        return ["## Efficacy — absorption", "", "_Not run._", ""]
    dimensions = report["metrics"]["summary"]["dimensions"]
    net_keys = sorted({k for d in dimensions.values() for k in d if k.endswith("_net")})
    lines = ["## Efficacy — absorption (netted, held-out)", "",
             "Both arms of a pair must independently clear zero. **bold** = CI excludes zero.",
             "", "| dimension | " + " | ".join(f"`{k[:-4]}`" for k in net_keys) + " |",
             "|---" * (len(net_keys) + 1) + "|"]
    for name, entry in dimensions.items():
        cells = []
        for key in net_keys:
            value = entry.get(key)
            if value is None:
                cells.append("—")
            else:
                text = f"{value['mean']:+.3f}"
                cells.append(f"**{text}**" if value["excludes_zero"] else text)
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return lines + [""]


def _suite_section(results_dir: Path, filename: str, heading: str) -> list[str]:
    summary = _load(results_dir / filename)
    if not summary:
        return [f"## {heading}", "", "_Not run._", ""]
    lines = [f"## {heading}", "", "| arm | score | 95% CI |", "|---|---|---|"]
    for arm, entry in summary["arms"].items():
        low, high = entry["ci95"]
        lines.append(f"| `{arm}` | {entry['score']:.4f} | [{low:.3f}, {high:.3f}] |")
    lines += ["", "| quantity | value |", "|---|---|"]
    for key in ("delta_raw", "machinery", "delta_net", "sensitivity"):
        if key in summary:
            lines.append(f"| `{key}` | {_ci(summary[key])} |")
    if "transfer" in summary:
        lines.append(f"| `T` | {summary['transfer']['T']:+.4f} |")
    return lines + ["", "**bold** = CI excludes zero.", ""]


def _figures_section(results_dir: Path) -> list[str]:
    figures = sorted(results_dir.glob("*.png"))
    if not figures:
        return []
    lines = ["## Figures", ""]
    for figure in figures:
        lines += [f"### {figure.stem.replace('_', ' ')}", "",
                  f"![{figure.stem}]({figure.name})", ""]
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
    lines += _gate_section(results_dir)
    lines += _absorption_section(results_dir)
    for filename, heading in _SUITES:
        lines += _suite_section(results_dir, filename, heading)
    lines += _figures_section(results_dir)
    lines += _related_section(results_dir)
    lines += _provenance_section(results_dir)
    return "\n".join(lines).rstrip() + "\n"


def write_report(results_dir: Path) -> Path:
    """Render and write `report.md` into `results_dir`."""
    out_path = results_dir / REPORT_FILENAME
    out_path.write_text(render_report(results_dir), encoding="utf-8")
    return out_path
