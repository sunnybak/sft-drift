"""The insight-note audit: precision-aware matching, declared arithmetic, drift, staleness.

Each test names the defect it guards against. Several of them exist because the first real
note written against this checker exposed the gap -- `derived` entries in particular, which
turned 20 false alarms into 12 verified derivations.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from belief_transfer.analysis import notes as N
from belief_transfer.analysis import results as R


@pytest.fixture
def tree(tmp_path, monkeypatch):
    root = tmp_path / "results"
    monkeypatch.setattr(R, "RESULTS_DIR", root)
    monkeypatch.setattr(R, "ROOT", tmp_path)
    directory = root / "topic" / "run_a"
    directory.mkdir(parents=True)
    (directory / "belief_summary.yaml").write_text(yaml.safe_dump({
        "run_id": "run_a", "suites_from": "bank_v2",
        "arms": {"base": {"score": 0.0900, "ci95": [0.03, 0.16], "n_items": 42}},
        "delta_net": {"delta": 0.3111192451721888,
                      "ci95": [0.23149966030514463, 0.39308146751334505],
                      "n_items": 42, "excludes_zero": True},
    }, sort_keys=False))
    other = root / "topic" / "run_b"
    other.mkdir(parents=True)
    (other / "belief_summary.yaml").write_text(yaml.safe_dump({
        "run_id": "run_b", "suites_from": "bank_v2",
        "delta_net": {"delta": 0.1190, "ci95": [0.09, 0.15], "n_items": 42,
                      "excludes_zero": True},
    }, sort_keys=False))
    return root


def _note(tmp_path: Path, body: str, ledger: dict) -> Path:
    directory = tmp_path / "insights" / "slug"
    (directory / "figures").mkdir(parents=True, exist_ok=True)
    (directory / N.NOTE_FILENAME).write_text(body)
    (directory / N.SOURCES_FILENAME).write_text(yaml.safe_dump(ledger, sort_keys=False))
    return directory


# ------------------------------------------------------- precision-aware matching

@pytest.mark.parametrize("written", ["+0.3111", "0.3111", "+0.311", "0.31"])
def test_a_numeral_verifies_at_its_own_precision(tree, tmp_path, written) -> None:
    """The PDF auditor's fixed 4-decimal compare would reject three of these four.

    Every honest rounding failing the audit is what teaches a reader to ignore it.
    """
    directory = _note(tmp_path, f"## Insight\nThe effect is {written} (`net`).\n",
                      {"refs": {"net": {"ref": "topic/run_a#belief/delta_net"}}})
    report = N.check(directory, suggest=False)
    assert not report.unresolved
    assert len(report.verified) == 1


def test_a_number_no_artifact_carries_is_unresolved(tree, tmp_path) -> None:
    directory = _note(tmp_path, "## Insight\nThe effect is +0.4200 (`net`).\n",
                      {"refs": {"net": {"ref": "topic/run_a#belief/delta_net"}}})
    report = N.check(directory, suggest=False)
    assert [numeral.text for numeral, _ in report.unresolved] == ["+0.4200"]


def test_the_whole_cited_artifact_is_allowed_not_just_the_pointer(tree, tmp_path) -> None:
    """A note citing delta_net may also quote a per-arm score from the same file: it came
    from the same immutable artifact, and rejecting it produces false alarms."""
    directory = _note(tmp_path, "## Insight\nBase sits at 0.0900 (`net`).\n",
                      {"refs": {"net": {"ref": "topic/run_a#belief/delta_net"}}})
    assert not N.check(directory, suggest=False).unresolved


# ------------------------------------------------------------ markdown awareness

def test_code_spans_fences_and_image_paths_are_not_scanned(tree, tmp_path) -> None:
    body = (
        "## Insight\nSee `delta_net_0.9999` and ![c](figures/plot_0.5.png).\n"
        "```\n0.1234\n```\n| a | b |\n|---|---|\n| +0.3111 | x |\n"
    )
    directory = _note(tmp_path, body,
                      {"refs": {"net": {"ref": "topic/run_a#belief/delta_net"}}})
    report = N.check(directory, suggest=False)
    # The table cell IS scanned -- a table is where a note puts its numbers.
    assert [n.text for n in report.verified] == ["+0.3111"]
    assert not report.unresolved


def test_integers_and_hedges_are_reported_rather_than_silently_ignored(tree, tmp_path) -> None:
    """An unaudited number that is not mentioned is indistinguishable from a verified one."""
    directory = _note(
        tmp_path,
        "## Insight\nOver n=42 items in 2026, roughly a third, a 16x gap.\n",
        {"refs": {"net": {"ref": "topic/run_a#belief/delta_net"}}})
    report = N.check(directory, suggest=False)
    assert {n.text for n in report.integers} >= {"42", "2026"}
    assert [n.text for n in report.multipliers] == ["16x"]
    assert "a third" in report.hedge_phrases


def test_the_section_a_numeral_sits_in_is_recorded(tree, tmp_path) -> None:
    directory = _note(tmp_path, "## Insight\n+0.9999\n\n## Margin\n+0.8888\n",
                      {"refs": {"net": {"ref": "topic/run_a#belief/delta_net"}}})
    report = N.check(directory, suggest=False)
    assert {(n.text, n.section) for n, _ in report.unresolved} == {
        ("+0.9999", "Insight"), ("+0.8888", "Margin")}


# ------------------------------------------------------------- declared arithmetic

def test_a_declared_derivation_is_re_evaluated_and_verified(tree, tmp_path) -> None:
    directory = _note(
        tmp_path,
        "## Insight\nThe ratio is 2.6144 (`ratio`).\n",
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"},
                  "b": {"ref": "topic/run_b#belief/delta_net"}},
         "derived": {"ratio": {"expr": "a / b", "value": 2.6144}}})
    report = N.check(directory, suggest=False)
    assert report.derived_ok == ["ratio"] and not report.derived_bad
    assert not report.unresolved       # the derived value joins the allowed set


def test_a_transposed_ratio_is_caught_and_cascades(tree, tmp_path) -> None:
    """The point of declaring the expression: a snapshotted value alone would sail through."""
    directory = _note(
        tmp_path, "## Insight\nThe ratio is 2.6144 (`ratio`).\n",
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"},
                  "b": {"ref": "topic/run_b#belief/delta_net"}},
         "derived": {"ratio": {"expr": "b / a", "value": 2.6144},
                     "pct": {"expr": "(ratio - 1) * 100", "value": 161.44}}})
    report = N.check(directory, suggest=False)
    keys = [key for key, _ in report.derived_bad]
    assert keys == ["ratio", "pct"]
    assert "computes 0.3825" in report.derived_bad[0][1]


def test_an_expression_may_not_execute_code(tree, tmp_path) -> None:
    with pytest.raises(ValueError, match="may only call"):
        N.evaluate("__import__('os').system('x')", {})
    with pytest.raises(ValueError, match="not in the ledger"):
        N.evaluate("nope * 2", {"a": 1.0})


def test_evaluate_supports_the_spread_idiom(tree) -> None:
    values = {"x": 0.05, "y": 0.02, "z": 0.017}
    assert N.evaluate("max(x, y, z) / min(x, y, z)", values) == pytest.approx(0.05 / 0.017)


# ---------------------------------------------------------------- refs and drift

def test_drift_names_a_mistyped_sha_when_the_value_is_unchanged(tree, tmp_path) -> None:
    """The two causes need opposite fixes, so the message must tell them apart."""
    directory = _note(
        tmp_path, "## Insight\nThe effect is +0.3111 (`net`).\n",
        {"refs": {"net": {"ref": "topic/run_a#belief/delta_net",
                          "value": 0.3111192451721888, "sha": "0" * 12}}})
    report = N.check(directory, suggest=False)
    assert [(s.key, s.status) for s in report.ref_statuses] == [("net", "DRIFT")]
    assert "sha was mistyped" in report.ref_statuses[0].detail


def test_drift_names_a_re_run_when_the_value_moved(tree, tmp_path) -> None:
    """Routine, not exotic: `data/results/` is gitignored and a stage overwrites in place."""
    directory = _note(
        tmp_path, "## Insight\nThe effect is +0.3111 (`net`).\n",
        {"refs": {"net": {"ref": "topic/run_a#belief/delta_net",
                          "value": 0.2000, "sha": "0" * 12}}})
    report = N.check(directory, suggest=False)
    detail = report.ref_statuses[0].detail
    assert "a stage re-ran" in detail and "+0.2000" in detail and "+0.3111" in detail


def test_a_missing_artifact_says_how_to_get_it(tree, tmp_path) -> None:
    directory = _note(tmp_path, "## Insight\nx\n",
                      {"refs": {"net": {"ref": "topic/absent#belief/delta_net"}}})
    report = N.check(directory, suggest=False)
    assert report.ref_statuses[0].status == "MISSING"


def test_a_bad_pointer_is_distinguished_from_a_missing_file(tree, tmp_path) -> None:
    directory = _note(tmp_path, "## Insight\nx\n",
                      {"refs": {"net": {"ref": "topic/run_a#belief/no_such_key"}}})
    assert N.check(directory, suggest=False).ref_statuses[0].status == "BAD_POINTER"


def test_a_ledger_entry_used_only_by_a_figure_is_not_reported_unused(tree, tmp_path) -> None:
    """The first version counted inline citations only, and flagged five entries the figure
    and the ratios both depended on."""
    directory = _note(tmp_path, "## Insight\nSee the chart.\n",
                      {"refs": {"plotted": {"ref": "topic/run_a#belief/delta_net"},
                                "cited_by_expr": {"ref": "topic/run_b#belief/delta_net"}},
                       "derived": {"d": "cited_by_expr * 2"}})
    (directory / "figures" / "c.fig.yaml").write_text(yaml.safe_dump({
        "kind": "forest",
        "rows": [{"label": "a", "ref": "topic/run_a#belief/delta_net"}]}))
    statuses = {s.key: s.status for s in N.check(directory, suggest=False).ref_statuses}
    assert statuses == {"plotted": "OK", "cited_by_expr": "OK"}


def test_a_genuinely_unused_entry_is_still_reported(tree, tmp_path) -> None:
    directory = _note(tmp_path, "## Insight\nnothing cited.\n",
                      {"refs": {"orphan": {"ref": "topic/run_a#belief/delta_net"}}})
    assert N.check(directory, suggest=False).ref_statuses[0].status == "UNUSED"


# -------------------------------------------------------------------- figures

def test_a_stale_image_is_flagged(tree, tmp_path) -> None:
    """The silent failure of this workflow: prose updated, image not rebuilt."""
    directory = _note(tmp_path, "## Figures\n![c](figures/c.png)\n",
                      {"refs": {"net": {"ref": "topic/run_a#belief/delta_net"}}})
    spec = directory / "figures" / "c.fig.yaml"
    image = directory / "figures" / "c.png"
    image.write_bytes(b"old")
    spec.write_text(yaml.safe_dump({
        "kind": "forest", "rows": [{"label": "a", "ref": "topic/run_a#belief/delta_net"}]}))
    import os
    os.utime(image, (1, 1))          # image older than its spec
    problems = dict(N.check(directory, suggest=False).figure_problems)
    assert "STALE" in problems["figures/c.png"]


def test_a_built_but_unshown_figure_is_flagged(tree, tmp_path) -> None:
    directory = _note(tmp_path, "## Figures\nno image link here\n",
                      {"refs": {"net": {"ref": "topic/run_a#belief/delta_net"}}})
    spec = directory / "figures" / "c.fig.yaml"
    spec.write_text(yaml.safe_dump({
        "kind": "forest", "rows": [{"label": "a", "ref": "topic/run_a#belief/delta_net"}]}))
    (directory / "figures" / "c.png").write_bytes(b"x")
    problems = dict(N.check(directory, suggest=False).figure_problems)
    assert "never shown" in problems["figures/c.png"]


def test_a_figure_row_without_a_ref_is_refused(tmp_path) -> None:
    """A literal number in a figure is a value in the deliverable that nothing can trace."""
    from belief_transfer.analysis import figures as F

    with pytest.raises(F.SpecError, match="Every plotted value must cite"):
        F.spec_refs({"kind": "forest", "rows": [{"label": "a", "value": 0.5}]})


# --------------------------------------------------------------------- structure

def test_a_missing_section_is_named(tree, tmp_path) -> None:
    directory = _note(tmp_path, "## Insight\nx\n",
                      {"refs": {"net": {"ref": "topic/run_a#belief/delta_net"}}})
    assert N.check(directory, suggest=False).missing_sections == [
        "Motivation", "Key Concepts", "Figures", "Margin"]


def test_the_ledger_round_trips(tmp_path) -> None:
    ledger = N.Ledger(
        refs={"a": N.LedgerEntry("a", "x/y#z/q", 0.5, (0.4, 0.6), "abc123abc123")},
        derived={"r": N.Derived("r", "a * 2", 1.0)},
        figures={"f.png": "f.fig.yaml"},
    )
    path = tmp_path / N.SOURCES_FILENAME
    path.write_text(ledger.dump())
    again = N.Ledger.load(path)
    assert again.refs["a"] == ledger.refs["a"]
    assert again.derived["r"] == ledger.derived["r"]
    assert again.figures == ledger.figures


def test_a_bare_ref_string_is_accepted_as_shorthand(tmp_path) -> None:
    path = tmp_path / N.SOURCES_FILENAME
    path.write_text(yaml.safe_dump({"refs": {"a": "x/y#z/q"}, "derived": {"r": "a * 2"}}))
    ledger = N.Ledger.load(path)
    assert ledger.refs["a"].ref == "x/y#z/q" and ledger.refs["a"].sha is None
    assert ledger.derived["r"].expr == "a * 2" and ledger.derived["r"].value is None


# --------------------------------------------------------------- rendered tables

def _with_table(tmp_path: Path, body: str, spec: dict, ledger: dict) -> Path:
    directory = _note(tmp_path, body, ledger)
    (directory / "figures" / "t.table.yaml").write_text(yaml.safe_dump(spec))
    return directory


def test_a_table_block_is_rendered_from_refs(tree, tmp_path) -> None:
    directory = _with_table(
        tmp_path,
        "## Figures\n<!-- bt:table t -->\n<!-- /bt:table -->\n",
        {"kind": "table", "columns": ["cell", "value"],
         "rows": [["run a", {"key": "a"}], ["run b", {"key": "b"}]]},
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"},
                  "b": {"ref": "topic/run_b#belief/delta_net"}}})
    rendered, problems = N.render_note(directory)
    assert not problems
    assert "| run a | +0.3111 |" in rendered
    assert "| run b | +0.1190 |" in rendered


def test_a_table_cell_can_render_an_interval_or_a_derived_value(tree, tmp_path) -> None:
    directory = _with_table(
        tmp_path,
        "## Figures\n<!-- bt:table t -->\n<!-- /bt:table -->\n",
        {"kind": "table", "columns": ["a", "b", "c"],
         "rows": [[{"key": "a", "format": "estimate"},
                   {"key": "r", "format": "plain", "places": 3},
                   "literal"]]},
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"},
                  "b": {"ref": "topic/run_b#belief/delta_net"}},
         "derived": {"r": "a / b"}})
    rendered, problems = N.render_note(directory)
    assert not problems
    assert "+0.3111 [+0.2315, +0.3931]" in rendered
    assert "| 2.614 |" in rendered and "literal" in rendered


def test_a_hand_edited_table_cell_is_reported_as_drifted(tree, tmp_path) -> None:
    """The failure this whole mechanism exists for: prose updated, table not."""
    directory = _with_table(
        tmp_path,
        "## Figures\n<!-- bt:table t -->\n| cell | value |\n|---|---|\n| run a | +0.9999 |\n"
        "<!-- /bt:table -->\n",
        {"kind": "table", "columns": ["cell", "value"], "rows": [["run a", {"key": "a"}]]},
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"}}})
    report = N.check(directory, suggest=False)
    assert any("out of date" in problem for problem in report.table_problems)
    assert not report.clean


def test_render_is_idempotent(tree, tmp_path) -> None:
    directory = _with_table(
        tmp_path,
        "## Figures\n<!-- bt:table t -->\n<!-- /bt:table -->\n",
        {"kind": "table", "columns": ["cell", "value"], "rows": [["run a", {"key": "a"}]]},
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"}}})
    once, _ = N.render_note(directory)
    (directory / N.NOTE_FILENAME).write_text(once)
    twice, problems = N.render_note(directory)
    assert twice == once and not problems


def test_a_block_with_no_spec_and_a_spec_with_no_block_are_both_reported(tree, tmp_path) -> None:
    directory = _with_table(
        tmp_path,
        "## Figures\n<!-- bt:table absent -->\n<!-- /bt:table -->\n",
        {"kind": "table", "columns": ["a"], "rows": [["x"]]},
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"}}})
    _, problems = N.render_note(directory)
    assert any("no figures/absent.table.yaml" in p for p in problems)
    assert any("no `<!-- bt:table t -->` block" in p for p in problems)


def test_a_table_citing_an_unknown_key_is_reported_not_rendered_blank(tree, tmp_path) -> None:
    directory = _with_table(
        tmp_path,
        "## Figures\n<!-- bt:table t -->\n<!-- /bt:table -->\n",
        {"kind": "table", "columns": ["a"], "rows": [[{"key": "nope"}]]},
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"}}})
    _, problems = N.render_note(directory)
    assert any("not in sources.yaml" in p for p in problems)


def test_a_row_with_the_wrong_cell_count_is_refused(tree, tmp_path) -> None:
    directory = _with_table(
        tmp_path,
        "## Figures\n<!-- bt:table t -->\n<!-- /bt:table -->\n",
        {"kind": "table", "columns": ["a", "b"], "rows": [["only one"]]},
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"}}})
    _, problems = N.render_note(directory)
    assert any("1 cells but there are 2 columns" in p for p in problems)


# --------------------------------------------------------------- forest dodging

def test_forest_dodges_by_series_so_a_gap_reads_as_a_gap(tmp_path) -> None:
    """Offsets are per-series over the whole figure, not per-slot: computed per slot, a row
    with a missing series shifts its neighbours and the eye reads a pattern that is not in
    the data."""
    from belief_transfer.analysis import figures as F

    rows = [
        F.ForestRow("cell A", 0.1, (0.0, 0.2), "s1"),
        F.ForestRow("cell A", 0.2, (0.1, 0.3), "s2"),
        F.ForestRow("cell A", 0.3, (0.2, 0.4), "s3"),
        F.ForestRow("cell B", 0.4, (0.3, 0.5), "s1"),
        F.ForestRow("cell B", 0.5, (0.4, 0.6), "s3"),   # s2 absent
    ]
    out = F.forest(rows, tmp_path / "f.png", title="t", xlabel="x")
    assert out.is_file() and out.stat().st_size > 0
    # Two labels, five markers: the slot count is what shrank, not the data.
    assert len({row.label for row in rows}) == 2


def test_forest_still_renders_without_any_series(tmp_path) -> None:
    from belief_transfer.analysis import figures as F

    out = F.forest([F.ForestRow("only", 0.5, (0.4, 0.6))], tmp_path / "g.png")
    assert out.is_file()


# ------------------------------------------------------------- the note as a PDF

def test_markdown_inline_spans_survive_the_escape_typography_emphasis_order() -> None:
    """`escape` -> typography -> emphasis is the only safe order, and getting it wrong is
    silent: the PDF simply shows `\\textbackslash{}times` instead of a multiplication sign."""
    out = N._inline_latex("**short** documents at 2.3× with `delta_net` — see above")

    assert r"\textbf{short}" in out
    assert r"$\times$" in out                       # typography survived escaping
    assert r"\texttt{delta\_net}" in out            # underscore escaped INSIDE the span
    assert "---" in out
    assert r"\textbackslash" not in out


def test_straight_quotes_become_an_asymmetric_latex_pair() -> None:
    """LaTeX renders a straight `"` as a CLOSING quote, so `"a band"` came out with both
    ends closing. Visible only once rendered, which is why it is fixed at this layer."""
    assert N._inline_latex('so "length is worth 2.3x" is a band') == (
        "so ``length is worth 2.3x'' is a band"
    )


def test_an_image_and_the_italic_paragraph_under_it_become_one_caption(tmp_path) -> None:
    """A note puts the short caption in the alt text and the real one in the italic
    paragraph below. Rendered separately, the informative half becomes body prose sitting
    under an unexplained figure."""
    blocks = N._blocks(
        "## Figures\n\n![Effect by form](figures/cells.png)\n\n*One row per cell, one marker "
        "per seed.*\n\n## Margin\n\n- A caveat.\n")

    assert [kind for kind, _ in blocks] == [
        "section", "image", "paragraph", "section", "bullets"]
    assert N._is_caption(blocks[2])
    assert not N._is_caption(("paragraph", "**bold lead** then prose"))


def test_a_wrapped_bullet_stays_one_bullet(tmp_path) -> None:
    """Continuation lines are how every bullet in a real note is written; treated as
    paragraphs they break the list and lose the indent."""
    blocks = N._blocks("- **Spread** — max over min\n  across seeds, a factor.\n- Second.\n")

    assert len(blocks) == 1
    kind, bullets = blocks[0]
    assert kind == "bullets"
    assert bullets == ["**Spread** — max over min across seeds, a factor.", "Second."]


def test_latex_document_inputs_its_tables_and_lists_every_source(tree, tmp_path) -> None:
    directory = _with_table(
        tmp_path,
        "# A title\n\n## Figures\n\n<!-- bt:table t -->\n<!-- /bt:table -->\n",
        {"kind": "table", "columns": ["cell", "value"], "rows": [["run a", {"key": "a"}]]},
        {"refs": {"a": {"ref": "topic/run_a#belief/delta_net",
                        "value": 0.3111192451721888}}})

    tex, problems = N.latex_document(directory)

    assert not problems
    assert r"\title{A title}" in tex
    assert r"\input{figures/t.tex}" in tex          # the table, not a copy of its numbers
    assert (directory / "figures" / "t.tex").exists()
    # A shared PDF travels without sources.yaml, so the provenance has to be in the document.
    assert r"\section*{Sources}" in tex
    assert r"topic/run\_a\#belief/delta\_net" in tex
    assert "= +0.3111" in tex, "the value must not be glued to its key"
    # Floats may move to fill a page but never out of the section that explains them.
    assert tex.count(r"\FloatBarrier") >= 1


def test_latex_document_reports_a_figure_the_note_references_but_never_built(
    tree, tmp_path
) -> None:
    directory = _note(tmp_path, "## Figures\n\n![Alt](figures/missing.png)\n",
                      {"refs": {"a": {"ref": "topic/run_a#belief/delta_net"}}})

    tex, problems = N.latex_document(directory)

    assert any("missing.png" in p for p in problems)
    assert "missing.png" not in tex, "a broken include would fail the compile instead"
