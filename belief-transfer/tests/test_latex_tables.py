"""LaTeX emission from a table model, shared by the paper renderer and insight notes.

`escape` and `column_spec` moved here out of `writeup.py` when a second consumer appeared:
`writeup` imports the OpenAI client, so anything pulling in those two helpers inherited a
heavyweight dependency to escape an ampersand.
"""

from __future__ import annotations

import pytest
import yaml

from belief_transfer.analysis import latex
from belief_transfer.analysis import notes as N
from belief_transfer.analysis import results as R
from belief_transfer.analysis.tables import ResultTable, TableCell, TableSource


def _table(columns, rows, **kwargs) -> ResultTable:
    return ResultTable(
        id=kwargs.pop("id", "t"), heading="H", columns=tuple(columns),
        rows=tuple(tuple(TableCell(cell) if isinstance(cell, str) else cell
                         for cell in row) for row in rows),
        source=TableSource(run_id=kwargs.pop("run_id", "run"), artifact="a.yaml"),
        **kwargs,
    )


@pytest.mark.parametrize("raw,expected", [
    ("100% of $x", r"100\% of \$x"),
    ("a_b & c", r"a\_b \& c"),
    ("~caret^", r"\textasciitilde{}caret\textasciicircum{}"),
])
def test_active_characters_are_escaped(raw, expected) -> None:
    assert latex.escape(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("**short** documents", r"\textbf{short} documents"),
    ("*long* run", r"\emph{long} run"),
    ("a `key` here", r"a \texttt{key} here"),
    ("2.3x plain", "2.3x plain"),
])
def test_markdown_emphasis_becomes_latex(raw, expected) -> None:
    """A spec is authored once in markdown and emitted twice. Without this, `**short**`
    reached the PDF as four literal asterisks -- which the first compiled table did."""
    assert latex.inline_markup(latex.escape(raw)) == expected


def test_short_columns_stay_l_and_long_ones_wrap() -> None:
    assert latex.column_spec(_table(["a", "b"], [["x", "y"]])) == "ll"
    wide = "w" * (latex.WRAP_AT + 20)
    spec = latex.column_spec(_table(["a", "b"], [["x", wide]]))
    assert spec.startswith("l") and "p{" in spec


def test_a_wrapped_column_never_collapses_below_the_floor() -> None:
    """Proportional sharing squeezed a label column to 2.3cm beside a prose column."""
    long_a, long_b = "a" * 60, "b" * 200
    spec = latex.column_spec(_table(["x", "y"], [[long_a, long_b]]))
    widths = [float(part.split("cm")[0]) for part in spec.split("p{")[1:]]
    assert widths and all(width >= latex.MIN_WRAP_CM - 1e-9 for width in widths)


def test_a_float_carries_its_caption_and_label() -> None:
    """A table moved by hand loses exactly these two, and `\\ref` then breaks silently."""
    out = latex.table_float(_table(["a", "b"], [["x", "y"]], caption="A caption.", id="cells"))
    assert r"\begin{table}" in out and r"\end{table}" in out
    assert r"\label{tab:cells}" in out
    assert "A caption." in out and "Source: run/a.yaml" in out
    assert r"\toprule" in out and r"\bottomrule" in out


def test_a_bold_cell_renders_bold() -> None:
    out = latex.table_float(_table(["a"], [[TableCell("+0.31", bold=True)]]))
    assert r"\textbf{+0.31}" in out
    partial = latex.table_float(
        _table(["a"], [[TableCell("+0.31 [a, b]", bold=True, bold_text="+0.31")]]))
    assert r"\textbf{+0.31} [a, b]" in partial


def test_only_all_short_multi_column_tables_get_a_resizebox() -> None:
    """A wrapping table already fits; resizing it too is what rendered one at a fifth size."""
    assert r"\resizebox" in latex.table_float(_table(["a", "b", "c"], [["x", "y", "z"]]))
    wide = "w" * (latex.WRAP_AT + 20)
    assert r"\resizebox" not in latex.table_float(
        _table(["a", "b", "c"], [["x", "y", wide]]))
    assert r"\resizebox" not in latex.table_float(_table(["a", "b"], [["x", "y"]]))


def test_writeup_uses_these_helpers_rather_than_private_copies() -> None:
    """Guards the extraction: two spellings of an escape table is how one drifts."""
    from belief_transfer.analysis.writeup import render

    assert render._escape is latex.escape
    assert render.latex_column_spec is latex.column_spec


# ------------------------------------------------- a note's table becomes a float

def test_a_note_table_spec_emits_a_tex_file_beside_its_markdown(tmp_path, monkeypatch) -> None:
    root = tmp_path / "results"
    monkeypatch.setattr(R, "RESULTS_DIR", root)
    monkeypatch.setattr(R, "ROOT", tmp_path)
    run = root / "topic" / "run_a"
    run.mkdir(parents=True)
    (run / "belief_summary.yaml").write_text(yaml.safe_dump({
        "run_id": "run_a",
        "delta_net": {"delta": 0.3111, "ci95": [0.23, 0.39], "excludes_zero": True},
    }))

    directory = tmp_path / "insights" / "slug"
    (directory / "figures").mkdir(parents=True)
    (directory / N.NOTE_FILENAME).write_text(
        "## Figures\n<!-- bt:table t -->\n<!-- /bt:table -->\n")
    (directory / N.SOURCES_FILENAME).write_text(yaml.safe_dump(
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"}}}))
    (directory / "figures" / "t.table.yaml").write_text(yaml.safe_dump({
        "kind": "table", "caption": "A caption.",
        "columns": ["cell", "value"],
        "rows": [["**short** documents", {"key": "a"}]]}))

    written, problems = N.write_latex(directory)
    assert not problems and [path.name for path in written] == ["t.tex"]
    tex = written[0].read_text()
    # The same value the markdown block shows, formatted once by `format_estimate`.
    assert "+0.3111" in tex
    assert r"\textbf{short} documents" in tex     # markdown translated, not literal
    assert r"\label{tab:t}" in tex
    rendered, _ = N.render_note(directory)
    assert "| **short** documents | +0.3111 |" in rendered


def test_the_resizebox_shrinks_but_never_magnifies() -> None:
    """A bare `\\resizebox{0.98\\linewidth}` scales a NARROW table UP.

    Measured on the first insight note: a three-column 2x2 was rendered at full text width
    in a font visibly larger than the body, dwarfing its own caption. `\\ifdim\\width>` leaves
    anything already narrower than the line alone, and still shrinks what is wider.
    """
    out = latex.table_float(_table(["a", "b", "c"], [["x", "y", "z"]]))

    assert r"\resizebox{\ifdim\width>0.98\linewidth 0.98\linewidth\else\width\fi}{!}{" in out
    assert r"\resizebox{0.98\linewidth}{!}{" not in out


def test_placement_is_settable_so_a_note_can_keep_reading_order() -> None:
    assert r"\begin{table}[htbp]" in latex.table_float(_table(["a"], [["x"]]))
    assert r"\begin{table}[H]" in latex.table_float(_table(["a"], [["x"]]), placement="H")
