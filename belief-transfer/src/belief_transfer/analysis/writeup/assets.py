"""Building the tables and figures a plan asked for.

Assets are built from the synthesis, never from a model's description of it: a brief
supplies a caption and a form, and Python supplies every value. That is the invariant that
lets the prose be digit-light without the paper being ungrounded.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from belief_transfer.analysis import plots, tables
from belief_transfer.schemas import ManuscriptPlan

from belief_transfer.analysis.writeup.evidence import source_directory


def copy_trajectory_figures(
    evidence: dict[str, Any], *, trajectory_run: str | None, output_dir: Path
) -> list[dict[str, str]]:
    """Render paper figures from declared tidy trajectory rows, leaving source runs untouched."""
    if trajectory_run is None:
        return []
    sources = evidence["sources"]
    if trajectory_run not in sources:
        raise ValueError("writeup.trajectory_run must also appear in writeup.source_runs")
    source = source_directory(str(evidence["experiment"]), trajectory_run)
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


def build_assets(
    plan: ManuscriptPlan,
    evidence: dict[str, Any],
    synthesis: dict[str, Any],
    figures: list[dict[str, str]],
    af_figure_dir: Path | None = None,
) -> tuple[dict[str, tables.ResultTable], dict[str, dict[str, str]], list[dict[str, Any]]]:
    """Dispatch accepted briefs to bounded deterministic builders."""
    built_tables: dict[str, tables.ResultTable] = {}
    built_figures: dict[str, dict[str, str]] = {}
    manifest: list[dict[str, Any]] = []
    available_tables = tables.evidence_tables(evidence)
    for brief in plan.assets:
        if brief.form == "ladder_table":
            table = tables.ladder_table(synthesis)
            built_tables[brief.id] = table
            manifest.append(
                {
                    "id": brief.id,
                    "kind": "table",
                    "builder": "ladder_table",
                    "evidence_refs": brief.evidence_refs,
                }
            )
        elif brief.form == "transfer_table":
            matching = [
                table
                for table in available_tables
                if any(
                    ref.startswith(f"{table.source.run_id}:{table.source.artifact}:")
                    for ref in brief.evidence_refs
                )
            ]
            if len(matching) != 1:
                raise ValueError(
                    f"asset {brief.id!r} must resolve to exactly one recorded transfer table"
                )
            built_tables[brief.id] = matching[0]
            manifest.append(
                {
                    "id": brief.id,
                    "kind": "table",
                    "builder": "transfer_table",
                    "evidence_refs": brief.evidence_refs,
                }
            )
        elif brief.form == "af_overlap_table":
            built_tables[brief.id] = tables.af_overlap_table(synthesis)
            manifest.append({"id": brief.id, "kind": "table",
                             "builder": "af_overlap_table", "evidence_refs": brief.evidence_refs})
        elif brief.form == "factorial_table":
            built_tables[brief.id] = tables.factorial_table(synthesis)
            manifest.append({"id": brief.id, "kind": "table",
                             "builder": "factorial_table", "evidence_refs": brief.evidence_refs})
        elif brief.form == "af_figure":
            built = plots.plot_af(synthesis, af_figure_dir) if af_figure_dir else []
            if not built:
                raise ValueError(
                    f"asset {brief.id!r} requests an af_figure but no af_ contrasts resolved"
                )
            built_figures[brief.id] = {
                "path": str(built[0].relative_to(af_figure_dir.parent)),
                "caption": (
                    "Attributable fraction by attribution method and removal budget; "
                    "full fine-tuning, probability scale, 95% paired bootstrap intervals; "
                    "the vertical line marks AF = 0 (filtering removed nothing)"
                ),
                "source_run": "attrib_mix_v4",
            }
            manifest.append(
                {
                    "id": brief.id,
                    "kind": "figure",
                    "builder": "af_figure",
                    "evidence_refs": brief.evidence_refs,
                }
            )
        else:
            if not figures:
                raise ValueError(f"asset {brief.id!r} requests a trajectory figure but none was built")
            figure = figures[0]
            built_figures[brief.id] = figure
            manifest.append(
                {
                    "id": brief.id,
                    "kind": "figure",
                    "builder": "trajectory_figure",
                    "evidence_refs": brief.evidence_refs,
                    "path": figure["path"],
                }
            )
    return built_tables, built_figures, manifest
