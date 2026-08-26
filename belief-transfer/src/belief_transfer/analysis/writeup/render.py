"""LaTeX rendering and compilation. Owns no selection logic.

The template receives an already-ordered manuscript and already-built floats; it decides
placement mechanics and nothing else. Escaping happens here rather than in the builders so
that one artifact model can render to both markdown and LaTeX.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from belief_transfer.analysis import latex, tables
from belief_transfer.analysis.latex import column_spec as latex_column_spec
from belief_transfer.analysis.latex import escape as _escape
from belief_transfer.schemas import ManuscriptPlan, WriteupSpec


# `analysis/templates/`, one level up: the templates are shared with the rest of
# `analysis`, so they did not move when `writeup.py` became `writeup/`.
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


PAPER_FILENAME = "paper.tex"


PDF_FILENAME = "paper.pdf"


COMPILE_LOG_FILENAME = "compile.log"


def _latex_table_model(
    table: tables.ResultTable, caption: str = ""
) -> dict[str, Any]:
    """Render one table, preferring the PLANNER's caption over the builder's generic one.

    Added 2026-08-22. Figures already used the brief's `caption_outline`; tables did not,
    so every `transfer_table` in a paper carried the identical builder string ("Recorded
    belief contrast and sensitivity quantities"). Seven identically-captioned tables tell a
    reader nothing about which one to look at, and the planner had already written a
    distinguishing caption for each.
    """
    model = tables.latex_table(table)
    return {
        **model,
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
            for row in model["rows"]
        ],
        # The planner's per-asset caption wins; the builder's generic string is the
        # fallback for tables rendered outside a ManuscriptPlan (the legacy path).
        "caption": _escape(caption or table.caption),
        "note": _escape(table.note),
        "source": {
            "run_id": _escape(table.source.run_id),
            "artifact": _escape(table.source.artifact),
            "checkpoint": _escape(table.source.checkpoint),
        },
    }


def render_manuscript_latex(
    *,
    output_dir: Path,
    spec: WriteupSpec,
    plan: ManuscriptPlan,
    built_tables: dict[str, tables.ResultTable],
    built_figures: dict[str, dict[str, str]],
) -> Path:
    """Render validated section/float order; LaTeX owns no selection logic."""
    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    environment.filters["column_spec"] = latex_column_spec
    assets = {asset.id: asset for asset in plan.assets}
    sections: list[dict[str, Any]] = []
    appendix: list[dict[str, Any]] = []
    for section in plan.sections:
        placements = {placement.after_paragraph_id: [] for placement in section.floats}
        for placement in section.floats:
            block = (
                {
                    "kind": "table",
                    "id": placement.asset_id,
                    "table": _latex_table_model(
                        built_tables[placement.asset_id],
                        caption=assets[placement.asset_id].caption_outline,
                    ),
                }
                if placement.asset_id in built_tables
                else {
                    "kind": "figure",
                    "id": placement.asset_id,
                    "figure": {
                        **built_figures[placement.asset_id],
                        "caption": _escape(assets[placement.asset_id].caption_outline),
                    },
                }
            )
            if placement.appendix:
                appendix.append(block)
            else:
                placements.setdefault(placement.after_paragraph_id, []).append(block)
        blocks: list[dict[str, Any]] = []
        for paragraph in section.paragraphs:
            blocks.append(
                {
                    "kind": "paragraph",
                    "id": paragraph.id,
                    "text": _escape(paragraph.text),
                }
            )
            blocks.extend(placements.get(paragraph.id, []))
        sections.append({"id": section.id, "title": _escape(section.title), "blocks": blocks})
    if spec.contrasts:
        # Reproducibility: the run/artifact/checkpoint behind every declared contrast, as
        # one deterministic appendix table. Spec-driven, so no LLM writes or audits it.
        appendix.append(
            {
                "kind": "table",
                "id": "provenance",
                "table": _latex_table_model(tables.provenance_table(spec.contrasts)),
            }
        )
    rendered = environment.get_template(spec.template).render(
        legacy=False,
        title=_escape(spec.title),
        authors=", ".join(_escape(author) for author in spec.authors) or "Anonymous",
        manuscript_sections=sections,
        appendix=appendix,
        related_work=spec.related_work_tex,
        references_bib=bool(spec.references_bib or spec.bibliography_path),
    )
    path = output_dir / PAPER_FILENAME
    path.write_text(rendered)
    return path


def compile_latex(tex_path: Path, *, timeout: int = 180) -> tuple[Path, Path]:
    """Compile the paper; callers choose whether a missing toolchain is fatal.

    The tectonic mechanics live in `analysis.latex` so that an insight note can compile
    without importing the paper pipeline. What stays here is the paper's own log filename
    and the message naming `writeup.compile_pdf=false` as the way out.
    """
    try:
        return latex.compile_pdf(
            tex_path, log_name=COMPILE_LOG_FILENAME, timeout=timeout, purpose="writeup"
        )
    except RuntimeError as exc:
        if "tectonic is required" in str(exc):
            raise RuntimeError(
                "tectonic is required to compile a writeup; install it or set "
                "writeup.compile_pdf=false"
            ) from exc
        raise
