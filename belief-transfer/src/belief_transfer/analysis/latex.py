"""LaTeX emission for result tables, shared by the paper renderer and by insight notes.

Extracted from `writeup.py`, which held `_escape` and `latex_column_spec` privately. Two
consumers now need them and `writeup` imports the OpenAI client, so anything that pulled
them in inherited a heavyweight dependency to escape an ampersand.

Nothing here knows what a manuscript is. It takes a `tables.ResultTable` -- already
selected, labelled and formatted by `tables.py` -- and turns it into LaTeX. Values are never
computed or reformatted here, which is what keeps a rendered table from disagreeing with the
markdown version of itself.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from belief_transfer.analysis.tables import ResultTable

WRAP_AT = 40
"""Longest cell, in characters, before a column becomes a wrapping `p{}` column."""

MIN_WRAP_CM = 3.2
"""Floor on a wrapped column's width, below which it is unreadable regardless of fit."""


def escape(value: str) -> str:
    """Escape LaTeX's active characters. Not idempotent -- call it once, on raw text."""
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


def column_spec(table: Any, total_width_cm: float = 16.0) -> str:
    """Choose a tabular column spec that WRAPS long text instead of shrinking the table.

    Added 2026-08-22. Every table with more than two columns was wrapped in
    `\\resizebox{0.98\\linewidth}{!}`, which scales the whole table -- font included --
    until it fits. For a table carrying a prose column (the declared-contrast table's
    `qualification` runs to a full sentence per row) the natural width is several times the
    page, so the result rendered at roughly a fifth of body size and was unreadable.

    Columns whose longest cell exceeds `WRAP_AT` characters become fixed-width `p{}`
    columns that wrap; the rest stay `l`. The caller then skips the resizebox whenever any
    `p{}` column is present, since a wrapping table already fits by construction.
    """
    # Tables reach the templates as ResultTable objects on one path and as plain dicts on
    # another, and cells are likewise either objects with `.text` or dicts with "text".
    columns = table["columns"] if isinstance(table, dict) else table.columns
    rows = table["rows"] if isinstance(table, dict) else table.rows

    def _cell(row: Any, index: int) -> str:
        cell = row[index]
        if isinstance(cell, dict):
            return str(cell.get("text", ""))
        return str(getattr(cell, "text", cell))

    lengths = [
        max([len(str(column))] + [len(_cell(row, index)) for row in rows])
        for index, column in enumerate(columns)
    ]
    if not any(length > WRAP_AT for length in lengths):
        return "l" * len(columns)
    short = sum(length for length in lengths if length <= WRAP_AT)
    wide = [length for length in lengths if length > WRAP_AT]
    # Reserve ~0.16cm per character for the narrow columns, share the rest by weight.
    remaining = max(total_width_cm - 0.16 * short, MIN_WRAP_CM * len(wide))
    # Share by sqrt of length, not length: proportional sharing squeezed a 43-character
    # label column to 2.3cm beside a 150-character prose column, so the label wrapped onto
    # five lines while the prose sat comfortably. sqrt keeps the ordering and softens the
    # ratio. A floor then guarantees no wrapped column collapses below readability.
    weights = [length ** 0.5 for length in lengths if length > WRAP_AT]
    widths = [max(MIN_WRAP_CM, remaining * weight / sum(weights)) for weight in weights]
    scale = min(1.0, remaining / sum(widths))
    iterator = iter(width * scale for width in widths)
    return "".join(
        "l" if length <= WRAP_AT else "p{%.2fcm}" % next(iterator)
        for length in lengths
    )


def inline_markup(text: str) -> str:
    """Translate the markdown emphasis a table spec is written in into LaTeX.

    A table spec is authored once and emitted twice -- markdown into the note, LaTeX into a
    paper -- so its label cells are written in markdown. Without this, `**short**` reaches
    the PDF as four literal asterisks, which is exactly what the first compiled table did.

    Applied AFTER escaping, which is safe because `escape` touches neither `*` nor a
    backtick.
    """
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)", r"\\emph{\1}", text)
    return re.sub(r"`(.+?)`", r"\\texttt{\1}", text)


def _cell_latex(cell: Any) -> str:
    text = inline_markup(escape(str(cell.text)))
    if cell.bold_text:
        bold = inline_markup(escape(str(cell.bold_text)))
        return text.replace(bold, r"\textbf{" + bold + "}", 1)
    return r"\textbf{" + text + "}" if cell.bold else text


def table_float(
    table: ResultTable, *, label_prefix: str = "tab", placement: str = "htbp"
) -> str:
    """A standalone `table` float, ready to `\\input{}` into a document.

    Requires `booktabs`. Deliberately a float rather than a bare `tabular`, so a note's
    table arrives in a paper with its caption and label attached -- the two things that get
    lost when a table is moved by hand, and the reason `\\ref` breaks silently afterwards.

    A table this emits is real typeset text: selectable, searchable, and extractable by
    `pdftotext`, which is what lets the numeral auditor read it. Rasterising a table to an
    image would break all three.
    """
    spec = column_spec(table)
    lines = [
        rf"\begin{{table}}[{placement}]",
        r"\centering",
        r"\footnotesize",
    ]
    if table.caption:
        source = f" Source: {escape(table.source.run_id)}/{escape(table.source.artifact)}." \
            if table.source.run_id else ""
        lines.append(r"\caption{" + inline_markup(escape(table.caption)) + source + "}")
    lines.append(rf"\label{{{label_prefix}:{table.id}}}")
    wrapping = "p{" in spec
    if not wrapping and len(table.columns) > 2:
        # SHRINK-ONLY. A bare `\resizebox{0.98\linewidth}` also scales tables UP, so a
        # narrow three-column table was rendered at full text width in a font visibly
        # larger than the body -- measured on the first insight note, where a 3x3 table
        # dwarfed its own caption. `\ifdim\width>` leaves anything already narrow alone.
        lines.append(
            r"\resizebox{\ifdim\width>0.98\linewidth 0.98\linewidth\else\width\fi}{!}{"
        )
    lines += [
        rf"\begin{{tabular}}{{ {spec} }}",
        r"\toprule",
        " & ".join(inline_markup(escape(str(column)))
                   for column in table.columns) + r" \\",
        r"\midrule",
    ]
    for row in table.rows:
        lines.append(" & ".join(_cell_latex(cell) for cell in row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    if not wrapping and len(table.columns) > 2:
        lines.append("}")
    if table.note:
        lines.append(r"\par\footnotesize\emph{Note.} "
                     + inline_markup(escape(table.note)))
    lines.append(r"\end{table}")
    return "\n".join(lines) + "\n"


def compile_pdf(
    tex_path: Path,
    *,
    log_name: str = "compile.log",
    timeout: int = 180,
    purpose: str = "document",
) -> tuple[Path, Path]:
    """Compile one `.tex` with tectonic, next to itself, and keep the tool output.

    Lives here rather than in the paper package because it is the mechanics of running
    LaTeX and nothing else -- the paper stage and an insight note both need it, and a
    second copy of a subprocess call is how two callers come to disagree about whether a
    non-zero exit is fatal.

    The log is written whether or not the run succeeded: a failed compile's log is the only
    thing that says why, and discarding it on the error path is the one case it is needed.
    """
    try:
        completed = subprocess.run(
            ["tectonic", "--outdir", str(tex_path.parent), str(tex_path)],
            cwd=tex_path.parent,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"tectonic is required to compile a {purpose}; install it "
            "(https://tectonic-typesetting.github.io) or skip the PDF"
        ) from exc
    log_path = tex_path.parent / log_name
    log_path.write_text(completed.stdout + completed.stderr)
    if completed.returncode:
        raise RuntimeError(f"tectonic failed; see {log_path}")
    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"tectonic succeeded but did not write {pdf_path}")
    return pdf_path, log_path
