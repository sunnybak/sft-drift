"""Insight notes: the ref ledger, and an advisory audit of every numeral in the prose.

An insight note is `insights/YYYY-MM-DD-<slug>/` holding `note.md`, `sources.yaml`, and `figures/`.
The note is written by hand (by a person or by an agent in a harness); this module exists
to answer one question about a finished draft -- **does every number in it trace to a
recorded artifact?** -- and to say plainly what it could not check.

It generalizes `.claude/skills/write-paper/scripts/audit_numerals.py`, which does the same
job for a rendered PDF. Three things had to change, and each is a correctness fix rather
than a port:

1. **The PDF auditor matches `[-+]?\\d+\\.\\d{4}` exactly** -- safe there, because LaTeX
   renders every table cell at four decimals. Note prose legitimately writes "+0.31" or
   "0.477". So a numeral is verified **at its own precision**: three decimals in the note
   are checked against the artifact rounded to three. Without that, every honest rounding
   is a false alarm, and a checker that cries wolf is a checker nobody reads.
2. **Bare integers are not audited** -- `n=42`, a year, a section number. But they are
   *listed*, because an unaudited number that is silently ignored is indistinguishable from
   a verified one, and the blind spot matters as much as the failures.
3. **Hedges are not numerals.** "roughly a third", "an order of magnitude", "16x" are
   legitimate note prose and unauditable. Named, not pretended-away.

And it can do three things the PDF auditor cannot: report **DRIFT** when a cited artifact
changed under the note (`data/results/` is gitignored and synced separately, so this is
routine rather than exotic), flag cited runs that are **void**, and **suggest** a ledger
line when exactly one estimate in the whole tree matches an unresolved numeral -- which
makes grounding a late draft a one-line edit instead of a prose rewrite.

Advisory by design: `check` reports, it does not block. A half-drafted note has to be
saveable, or the tool stops being used.
"""

from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml

from belief_transfer.analysis import results as R
from belief_transfer.analysis.tables import (
    ResultTable, TableCell, TableSource, format_estimate,
)
from belief_transfer.schemas import file_sha

NOTE_FILENAME = "note.md"
SOURCES_FILENAME = "sources.yaml"
FIGURES_DIRNAME = "figures"

SECTIONS = ("Motivation", "Key Concepts", "Insight", "Figures", "Margin")
"""The note format, in reading order.

`Motivation` was added to the format after this constant was first written and never added
here, so `check` reported four sections while `score_note.py` knew five -- two checkers
disagreeing about the format they both police.

Key Concepts sits BEFORE Insight: the Insight is the one section a reader must get through
without stopping, and definitions arriving afterwards are definitions arriving too late.

`Key Concepts` holds definitions, units, symbols and formulas, and is expected to be free of
MEASUREMENTS -- a definition with a measurement in it is a result wearing a definition's
clothes. A constant inside a formula is not a measurement. `check` says so rather than
enforcing it."""

_DECIMAL = re.compile(r"[-+]?\d+\.\d+")
_INTEGER = re.compile(r"(?<![\d.])[-+]?\d+(?![\d.])")

_HEDGES = (
    "roughly", "about", "approximately", "around", "nearly", "almost",
    "a third", "a half", "a quarter", "twice", "double", "half",
    "an order of magnitude", "orders of magnitude", "several", "a handful",
)
"""Phrases that carry a quantity without a checkable numeral. Reported as unaudited."""

_MULTIPLIER = re.compile(r"\b\d+(?:\.\d+)?\s*[x×]\b", re.IGNORECASE)
"""`16x`, `2.2x` -- a ratio the note computed. Its inputs may be citable but the product is
not in any artifact, so it is reported as derived rather than flagged as unsupported."""


# --------------------------------------------------------------------- the ledger

@dataclass(frozen=True)
class Derived:
    """A number the note computed from other ledger entries, with the arithmetic declared.

    A note is mostly *comparisons* -- a ratio, a difference, a spread -- and none of those
    live in any artifact. Without this, every one of them reads as an unsupported numeral:
    the first real note written against this checker produced 20 such false alarms out of
    26 numerals, which is precisely the cry-wolf failure the precision-aware matching was
    designed to avoid.

    Declaring the expression is stronger than declaring the value, because `check` then
    re-evaluates it against the cited refs and verifies the note's own arithmetic. A
    transposition in a ratio is caught; a bare snapshot would sail through.
    """

    key: str
    expr: str
    value: float | None = None


@dataclass(frozen=True)
class LedgerEntry:
    key: str
    ref: str
    value: float | None = None
    ci95: tuple[float, float] | None = None
    sha: str | None = None


@dataclass
class Ledger:
    refs: dict[str, LedgerEntry] = field(default_factory=dict)
    derived: dict[str, Derived] = field(default_factory=dict)
    figures: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> Ledger:
        if not path.is_file():
            return cls()
        document = yaml.safe_load(path.read_text()) or {}
        refs = {}
        for key, entry in (document.get("refs") or {}).items():
            if isinstance(entry, str):        # the shorthand: just a ref, no snapshot
                refs[key] = LedgerEntry(key, entry)
                continue
            interval = entry.get("ci95")
            refs[key] = LedgerEntry(
                key=key,
                ref=entry["ref"],
                value=entry.get("value"),
                ci95=(float(interval[0]), float(interval[1]))
                if isinstance(interval, (list, tuple)) and len(interval) == 2 else None,
                sha=entry.get("sha"),
            )
        derived = {}
        for key, entry in (document.get("derived") or {}).items():
            if isinstance(entry, str):
                derived[key] = Derived(key, entry)
            else:
                derived[key] = Derived(key, entry["expr"], entry.get("value"))
        return cls(refs=refs, derived=derived,
                   figures=dict(document.get("figures") or {}))

    def dump(self) -> str:
        document: dict[str, Any] = {"refs": {}}
        for key, entry in self.refs.items():
            payload: dict[str, Any] = {"ref": entry.ref}
            if entry.value is not None:
                payload["value"] = entry.value
            if entry.ci95:
                payload["ci95"] = list(entry.ci95)
            if entry.sha:
                payload["sha"] = entry.sha
            document["refs"][key] = payload
        if self.derived:
            document["derived"] = {
                key: ({"expr": entry.expr, "value": entry.value}
                      if entry.value is not None else entry.expr)
                for key, entry in self.derived.items()
            }
        if self.figures:
            document["figures"] = dict(self.figures)
        return yaml.safe_dump(document, sort_keys=False)


# ---------------------------------------------------------------- the insights index

INSIGHTS_DIRNAME = "insights"

DATED_SLUG_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
"""A note directory is `insights/YYYY-MM-DD-<slug>/`.

The date prefix is the note's CREATION date and never moves, so a link into a note stays
valid when the note is later revised -- an updated-date prefix would rename the directory
under every inbound reference. Sorting by name therefore sorts by age, which is the whole
point: `ls insights/` answers "what is the latest note?" without knowing any topic. The
edit date is recovered from git and shown in the index instead.
"""


@dataclass(frozen=True)
class NoteEntry:
    """One note directory, as the index sees it."""

    path: Path
    slug: str
    created: str            # from the directory name; "" if it carries no date prefix
    updated: str            # last git commit touching the directory; "" if unknown
    title: str
    has_pdf: bool

    @property
    def undated(self) -> bool:
        return not self.created


def _git_last_modified(note_path: Path) -> str:
    """When `note.md` last changed in CONTENT, following it across directory renames.

    Two flags carry the weight. `--follow` keeps the history when the directory is renamed
    -- without it, the day the dating convention was introduced every note would report no
    history at all. `--diff-filter=AM` then drops the rename commits themselves, so a
    bulk `git mv` does not reset every note's edit date to the day of the move.
    """
    try:
        out = subprocess.run(
            ["git", "log", "--follow", "--diff-filter=AM", "-1",
             "--format=%ad", "--date=short", "--", note_path.name],
            capture_output=True, text=True, cwd=note_path.parent, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def note_title(note_path: Path) -> str:
    """The note's H1, which by this repo's convention is the claim it makes."""
    for line in note_path.read_text().splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return note_path.parent.name


def discover_notes(insights_dir: Path) -> list[NoteEntry]:
    """Every note under `insights/`, newest first.

    Undated directories sort last rather than being skipped: a note that predates this
    convention, or one created by hand without the prefix, is still a note and hiding it
    from the index is how an index stops being trustworthy.
    """
    entries = []
    for directory in sorted(p for p in insights_dir.iterdir() if p.is_dir()):
        note = directory / NOTE_FILENAME
        if not note.is_file():
            continue
        match = DATED_SLUG_RE.match(directory.name)
        created, slug = (match.group(1), match.group(2)) if match else ("", directory.name)
        entries.append(NoteEntry(
            path=directory, slug=slug, created=created,
            updated=_git_last_modified(note), title=note_title(note),
            has_pdf=(directory / f"{directory.name}.pdf").is_file()))
    return sorted(entries, key=lambda e: (e.created or "0000-00-00", e.slug), reverse=True)


def index_markdown(entries: Sequence[NoteEntry]) -> str:
    """`insights/README.md` -- generated, never hand-edited, like every table in a note."""
    lines = [
        "# Insight notes",
        "",
        "Newest first. Each directory is `YYYY-MM-DD-<slug>/`, dated by when the note was",
        "**created**; the *updated* column is the last commit that touched it. Regenerate this",
        "file with `uv run bt notes --write` -- it is derived, so do not edit it by hand.",
        "",
        "| created | updated | note | claim |",
        "| --- | --- | --- | --- |",
    ]
    for e in entries:
        link = f"[`{e.slug}`]({e.path.name}/{NOTE_FILENAME})"
        pdf = f" &middot; [pdf]({e.path.name}/{e.path.name}.pdf)" if e.has_pdf else ""
        created = e.created or "*(undated)*"
        updated = e.updated or "\u2014"
        title = e.title.replace("|", "\\|")
        lines.append(f"| {created} | {updated} | {link}{pdf} | {title} |")
    lines.append("")
    return "\n".join(lines)


_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name, ast.Load, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd,
    ast.Call, ast.Tuple,
)
_ALLOWED_CALLS = {"abs": abs, "max": max, "min": min, "round": round}


def evaluate(expr: str, values: dict[str, float]) -> float:
    """Evaluate one arithmetic expression over ledger keys.

    Parsed with `ast` and walked against an allowlist rather than handed to `eval`: a
    `sources.yaml` is a data file, and a data file that can execute code is a different
    kind of object than the one a reader thinks they are reviewing.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"{expr!r} is not an expression: {exc}") from exc
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(
                f"{expr!r} uses {type(node).__name__}, which is not allowed here -- "
                "arithmetic over ledger keys only")
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_CALLS
        ):
            raise ValueError(f"{expr!r} may only call {', '.join(sorted(_ALLOWED_CALLS))}")

    def walk(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in _ALLOWED_CALLS:
                return _ALLOWED_CALLS[node.id]
            if node.id not in values:
                raise ValueError(f"{expr!r} names {node.id!r}, which is not in the ledger")
            return values[node.id]
        if isinstance(node, ast.Tuple):
            return tuple(walk(item) for item in node.elts)
        if isinstance(node, ast.UnaryOp):
            operand = walk(node.operand)
            return -operand if isinstance(node.op, ast.USub) else +operand
        if isinstance(node, ast.Call):
            args = [walk(arg) for arg in node.args]
            flat = args[0] if len(args) == 1 and isinstance(args[0], tuple) else args
            return _ALLOWED_CALLS[node.func.id](*flat) if not isinstance(flat, tuple) \
                else _ALLOWED_CALLS[node.func.id](*flat)
        left, right = walk(node.left), walk(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Pow):
            return left ** right
        if right == 0:
            raise ValueError(f"{expr!r} divides by zero")
        return left / right

    return float(walk(tree))


# ------------------------------------------------------------- markdown extraction

@dataclass(frozen=True)
class Numeral:
    text: str
    line: int
    section: str


def _strip_markup(line: str) -> str:
    """Blank out the spans a numeral must not be read out of.

    Inline code holds ledger keys and refs; a link target or image path holds filenames
    like `figures/forest.png`. Table cells are deliberately NOT stripped -- a table is
    where a note puts its numbers, so it is the last place to stop looking.
    """
    line = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", line)   # images
    line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)  # links: keep the text
    line = re.sub(r"`[^`]*`", " ", line)                 # inline code
    return line


def read_numerals(text: str) -> tuple[list[Numeral], list[Numeral], list[Numeral]]:
    """(decimals, integers, derived-multipliers), each with its line and section.

    Section is tracked so the report can say *where* an unresolved number is: one in
    `Insight` is a claim, one in `Margin` is usually a note to self.
    """
    decimals: list[Numeral] = []
    integers: list[Numeral] = []
    multipliers: list[Numeral] = []
    section = ""
    fenced = False
    for number, raw in enumerate(text.splitlines(), start=1):
        if raw.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if raw.startswith("#"):
            section = raw.lstrip("#").strip()
            continue
        line = _strip_markup(raw)
        for match in _MULTIPLIER.finditer(line):
            multipliers.append(Numeral(match.group(0).strip(), number, section))
        cleaned = _MULTIPLIER.sub(" ", line)
        for match in _DECIMAL.finditer(cleaned):
            decimals.append(Numeral(match.group(0), number, section))
        for match in _INTEGER.finditer(_DECIMAL.sub(" ", cleaned)):
            integers.append(Numeral(match.group(0), number, section))
    return decimals, integers, multipliers


def hedges(text: str) -> list[str]:
    """Quantity words the audit cannot check, so the report can name its own blind spot."""
    lowered = text.lower()
    return sorted({phrase for phrase in _HEDGES if phrase in lowered})


# ------------------------------------------------------------------ rendered tables

TABLE_OPEN = "<!-- bt:table {name} -->"
TABLE_CLOSE = "<!-- /bt:table -->"
_TABLE_BLOCK = re.compile(
    r"<!--\s*bt:table\s+(?P<name>[\w.-]+)\s*-->\n(?P<body>.*?)<!--\s*/bt:table\s*-->",
    re.DOTALL,
)


def _cell_text(cell: Any, ledger: Ledger, derived: dict[str, float]) -> str:
    """One table cell: a literal string, a ledger ref, or a declared derivation."""
    if not isinstance(cell, dict):
        return "" if cell is None else str(cell)
    style = cell.get("format", "value")
    if "key" in cell:
        name = cell["key"]
        if name in ledger.refs:
            est = R.estimate_at(R.parse_ref(ledger.refs[name].ref))
            if est is None:
                raise ValueError(f"ledger key {name!r} does not point at an estimate")
            value, interval = est.value, est.ci95
        elif name in derived:
            value, interval = derived[name], None
        else:
            raise ValueError(f"table cites {name!r}, which is not in sources.yaml")
    elif "ref" in cell:
        est = R.estimate_at(R.parse_ref(cell["ref"]))
        if est is None:
            raise ValueError(f"{cell['ref']} does not point at an estimate")
        value, interval = est.value, est.ci95
    else:
        raise ValueError(f"table cell {cell!r} has neither `key` nor `ref` nor plain text")

    places = int(cell.get("places", 4))
    if style == "estimate" and interval:
        return format_estimate(value, interval, places=places)
    if style == "plain":
        return f"{value:.{places}f}"
    return f"{value:+.{places}f}"


def table_model(name: str, spec: dict[str, Any], ledger: Ledger,
                derived: dict[str, float]) -> ResultTable:
    """A table spec as the same `ResultTable` the paper renderer consumes.

    One model, two emitters: markdown into the note, LaTeX into a paper. That is the whole
    reason to have a model at all -- a note's table and the paper's version of it are then
    the same object formatted twice, rather than two hand-maintained copies that drift.
    """
    columns = [str(column) for column in spec.get("columns") or []]
    if not columns:
        raise ValueError("a table spec needs `columns`")
    rows = []
    for index, row in enumerate(spec.get("rows") or []):
        if len(row) != len(columns):
            raise ValueError(
                f"row {index} has {len(row)} cells but there are {len(columns)} columns")
        rows.append(tuple(
            TableCell(_cell_text(cell, ledger, derived)) for cell in row))
    return ResultTable(
        id=name,
        heading=str(spec.get("heading") or name),
        columns=tuple(columns),
        rows=tuple(rows),
        source=TableSource(run_id=str(spec.get("source_run") or ""),
                           artifact=str(spec.get("source_artifact") or "sources.yaml")),
        caption=str(spec.get("caption") or ""),
        note=str(spec.get("note") or ""),
    )


def render_table(spec: dict[str, Any], ledger: Ledger,
                 derived: dict[str, float]) -> list[str]:
    """A markdown table from a table spec. Values come from refs, never from the spec.

    This exists because a hand-typed table is where a note rots first: the prose gets
    updated when a number changes and the table does not, and a wrong cell in a table looks
    exactly as authoritative as a right one. `bt render` rewrites these blocks in place and
    `check` re-renders them to detect drift, so a stale table is a reported defect rather
    than something a reader has to catch.
    """
    columns = [str(column) for column in spec.get("columns") or []]
    if not columns:
        raise ValueError("a table spec needs `columns`")
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for index, row in enumerate(spec.get("rows") or []):
        if len(row) != len(columns):
            raise ValueError(
                f"row {index} has {len(row)} cells but there are {len(columns)} columns")
        lines.append("| " + " | ".join(
            _cell_text(cell, ledger, derived) for cell in row) + " |")
    if spec.get("caption"):
        lines += ["", f"*{spec['caption']}*"]
    return lines


def table_specs(directory: Path) -> dict[str, dict[str, Any]]:
    """`figures/<name>.table.yaml` keyed by `<name>`, the id a marker block references."""
    figures_dir = directory / FIGURES_DIRNAME
    if not figures_dir.is_dir():
        return {}
    return {
        path.name[: -len(".table.yaml")]: (yaml.safe_load(path.read_text()) or {})
        for path in sorted(figures_dir.glob("*.table.yaml"))
    }


def _resolve_all(ledger: Ledger) -> dict[str, float]:
    """Every ledger key's current numeric value, refs and derivations together."""
    values: dict[str, float] = {}
    for key, entry in ledger.refs.items():
        try:
            est = R.estimate_at(R.parse_ref(entry.ref))
        except R.RefError:
            est = None
        if est is not None:
            values[key] = est.value
        elif entry.value is not None:
            values[key] = float(entry.value)
    for key, entry in ledger.derived.items():
        try:
            values[key] = evaluate(entry.expr, values)
        except ValueError:
            continue
    return values


def write_latex(directory: Path) -> tuple[list[Path], list[str]]:
    """Emit `figures/<name>.tex` for every table spec. Returns (written, problems).

    A note's tables are the load-bearing part a paper wants to inherit, and hand-copying
    them into LaTeX is the step where a number changes. Emitting from the same spec means
    the paper's table and the note's are one object rendered twice.

    Deliberately NOT a rasterised table. An image cannot be searched, selected, diffed, or
    read by `pdftotext` -- which is how the numeral auditor verifies a paper -- and it
    typesets in the wrong font at the wrong size. LaTeX keeps all of that.
    """
    from belief_transfer.analysis import latex as latex_mod

    ledger = Ledger.load(directory / SOURCES_FILENAME)
    values = _resolve_all(ledger)
    written: list[Path] = []
    problems: list[str] = []
    for name, spec in table_specs(directory).items():
        try:
            model = table_model(name, spec, ledger, values)
        except (ValueError, R.RefError) as exc:
            problems.append(f"{name}: {exc}")
            continue
        path = directory / FIGURES_DIRNAME / f"{name}.tex"
        # Default `[htbp]` placement, kept honest by the `\FloatBarrier` the note document
        # emits at each section boundary (see `PREAMBLE`) -- so a table may move to fill a
        # page but cannot leave the section whose prose explains it.
        path.write_text(latex_mod.table_float(model))
        written.append(path)
    return written, problems


def render_note(directory: Path) -> tuple[str, list[str]]:
    """The note text with every `bt:table` block re-rendered. Returns (text, problems).

    Pure: the caller decides whether to write it. That is what lets `check` compare a fresh
    render against what is on disk without touching the file.
    """
    note_path = directory / NOTE_FILENAME
    text = note_path.read_text()
    ledger = Ledger.load(directory / SOURCES_FILENAME)
    specs = table_specs(directory)
    values = _resolve_all(ledger)
    problems: list[str] = []

    def replace(match: re.Match) -> str:
        name = match.group("name")
        spec = specs.get(name)
        if spec is None:
            problems.append(f"{name}: no figures/{name}.table.yaml for this block")
            return match.group(0)
        try:
            body = "\n".join(render_table(spec, ledger, values))
        except (ValueError, R.RefError) as exc:
            problems.append(f"{name}: {exc}")
            return match.group(0)
        return f"{TABLE_OPEN.format(name=name)}\n{body}\n{TABLE_CLOSE}"

    rendered = _TABLE_BLOCK.sub(replace, text)
    referenced = {m.group("name") for m in _TABLE_BLOCK.finditer(text)}
    for name in sorted(set(specs) - referenced):
        problems.append(f"{name}: spec exists but no `{TABLE_OPEN.format(name=name)}` "
                        "block in the note")
    return rendered, problems


# ------------------------------------------------------------------- the allowed set

def _numeric_leaves(value: Any) -> Iterable[float]:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield float(value)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _numeric_leaves(item)
    elif isinstance(value, list):
        for item in value:
            yield from _numeric_leaves(item)


def allowed_values(refs: Sequence[str]) -> set[float]:
    """Every number in every artifact the note cites.

    Whole-artifact rather than pointer-exact, and deliberately so: a note that cites
    `#belief/delta_net` will often also quote a per-arm score from the same summary, and
    that number came from the same immutable file. `audit_numerals.py` learned this the
    hard way -- auditing against declared facts alone produced false alarms "that train a
    reader to ignore this script".
    """
    values: set[float] = set()
    for text in refs:
        try:
            ref = R.parse_ref(text)
        except R.RefError:
            continue
        document = R.load(ref.path)
        if document:
            values.update(_numeric_leaves(document))
    return values


def _matches(numeral: str, allowed: Iterable[float]) -> bool:
    """Does any allowed value equal this numeral at the numeral's own precision?"""
    try:
        stated = float(numeral)
    except ValueError:
        return False
    places = len(numeral.partition(".")[2])
    target = round(stated, places)
    return any(round(value, places) == target for value in allowed)


# ---------------------------------------------------------------------- the report

@dataclass
class RefStatus:
    key: str
    ref: str
    status: str          # OK | DRIFT | MISSING | BAD_POINTER | UNUSED
    detail: str = ""


@dataclass
class CheckReport:
    note: Path
    words: int = 0
    ref_statuses: list[RefStatus] = field(default_factory=list)
    verified: list[Numeral] = field(default_factory=list)
    unresolved: list[tuple[Numeral, list[str]]] = field(default_factory=list)
    integers: list[Numeral] = field(default_factory=list)
    multipliers: list[Numeral] = field(default_factory=list)
    table_problems: list[str] = field(default_factory=list)
    derived_ok: list[str] = field(default_factory=list)
    derived_bad: list[tuple[str, str]] = field(default_factory=list)
    hedge_phrases: list[str] = field(default_factory=list)
    run_flags: list[tuple[str, list[R.Flag]]] = field(default_factory=list)
    figure_problems: list[tuple[str, str]] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)
    banks: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not (self.unresolved or self.figure_problems or self.derived_bad
                    or self.table_problems
                    or any(s.status not in ("OK", "UNUSED") for s in self.ref_statuses))


def _suggest(numeral: str, *, limit: int = 1) -> list[str]:
    """Refs whose value matches this numeral at its own precision, tree-wide.

    Returns at most `limit`+1 so the caller can say "several candidates" rather than pick
    one. Suggesting a single unambiguous ref is the difference between "fix your prose" and
    "paste this line"; guessing among several would be worse than staying quiet.
    """
    found: list[str] = []
    for _run, _artifact, estimates in R.scan():
        for est in estimates:
            if _matches(numeral, [est.value]):
                found.append(str(est.ref))
                if len(found) > limit:
                    return found
    return found


def check(note_dir: Path, *, suggest: bool = True) -> CheckReport:
    """Audit one insight note directory. Reads only; changes nothing."""
    note_path = note_dir / NOTE_FILENAME if note_dir.is_dir() else note_dir
    directory = note_path.parent
    if not note_path.is_file():
        raise FileNotFoundError(f"no note at {note_path}")
    text = note_path.read_text()
    ledger = Ledger.load(directory / SOURCES_FILENAME)

    report = CheckReport(note=note_path, words=len(text.split()))
    report.missing_sections = [
        name for name in SECTIONS if f"## {name}" not in text
    ]

    # -- refs: does each still resolve, and to what it was quoted as?
    cited_runs: dict[str, R.RunRef] = {}
    for key, entry in ledger.refs.items():
        try:
            ref = R.parse_ref(entry.ref)
        except R.RefError as exc:
            report.ref_statuses.append(RefStatus(key, entry.ref, "MISSING", str(exc)))
            continue
        cited_runs[str(ref.run)] = ref.run
        if not ref.path.is_file():
            report.ref_statuses.append(RefStatus(
                key, entry.ref, "MISSING",
                f"{ref.path} is absent -- run `make data-pull`"))
            continue
        try:
            R.resolve(ref)
        except R.RefError as exc:
            report.ref_statuses.append(RefStatus(key, entry.ref, "BAD_POINTER", str(exc)))
            continue
        current_sha = file_sha(ref.path)
        if entry.sha and entry.sha != current_sha:
            est = R.estimate_at(ref)
            now = f"{est.value:+.4f}" if est else "changed"
            was = f"{entry.value:+.4f}" if entry.value is not None else "?"
            # Distinguish the two causes, because the fixes are opposite. A sha mismatch
            # with an UNCHANGED value means the sha was mistyped or hand-edited -- re-paste
            # the ledger line. A changed value means a stage re-ran and overwrote the run
            # directory, and the note's prose may now be wrong. Reporting both as "the
            # artifact was rewritten" sends the author looking for a re-run that never
            # happened.
            same_value = (entry.value is not None and est is not None
                          and abs(float(entry.value) - est.value) < 1e-12)
            cause = (
                "the value is unchanged, so the sha was mistyped or hand-edited -- "
                "re-paste the line from `bt show --pointer`"
                if same_value else
                "the value moved, so a stage re-ran and overwrote the run directory; "
                "re-read the prose that quotes it"
            )
            report.ref_statuses.append(RefStatus(
                key, entry.ref, "DRIFT",
                f"cited {was} (sha {entry.sha}) -> now {now} (sha {current_sha}); {cause}"))
            continue
        report.ref_statuses.append(RefStatus(key, entry.ref, "OK"))

    # -- derived: verify the note's own arithmetic against the cited refs
    resolved: dict[str, float] = {}
    for key, entry in ledger.refs.items():
        try:
            est = R.estimate_at(R.parse_ref(entry.ref))
        except R.RefError:
            est = None
        if est is not None:
            resolved[key] = est.value
        elif entry.value is not None:
            resolved[key] = float(entry.value)   # snapshot, when the artifact is absent
    derived_values: dict[str, float] = {}
    for key, entry in ledger.derived.items():
        try:
            computed = evaluate(entry.expr, {**resolved, **derived_values})
        except ValueError as exc:
            report.derived_bad.append((key, str(exc)))
            continue
        derived_values[key] = computed
        if entry.value is not None:
            places = len(str(entry.value).partition(".")[2]) or 4
            if round(computed, places) != round(float(entry.value), places):
                report.derived_bad.append((
                    key,
                    f"declared {entry.value} but `{entry.expr}` computes "
                    f"{computed:.{places}f} -- the note's arithmetic does not check out"))
                continue
        report.derived_ok.append(key)

    # -- numerals
    decimals, integers, multipliers = read_numerals(text)
    report.integers = integers
    report.multipliers = multipliers
    report.hedge_phrases = hedges(text)
    allowed = allowed_values([entry.ref for entry in ledger.refs.values()])
    # The ledger's own snapshots count: a note read on a box with no results pulled should
    # still verify against what it recorded, or MISSING would cascade into every numeral.
    for entry in ledger.refs.values():
        if entry.value is not None:
            allowed.add(float(entry.value))
        if entry.ci95:
            allowed.update(float(edge) for edge in entry.ci95)
    allowed.update(derived_values.values())
    for numeral in decimals:
        if _matches(numeral.text, allowed):
            report.verified.append(numeral)
        else:
            report.unresolved.append(
                (numeral, _suggest(numeral.text) if suggest else []))

    # -- unused ledger entries
    # A ledger entry earns its place by being cited inline, by feeding a declared
    # derivation, or by being plotted -- the first version counted only inline citations and
    # so flagged five entries as UNUSED that the figure and the ratios both depended on.
    expressions = " ".join(entry.expr for entry in ledger.derived.values())
    plotted = _figure_ref_text(directory)
    used = {
        key for key, entry in ledger.refs.items()
        if f"`{key}`" in text
        or re.search(rf"\b{re.escape(key)}\b", expressions)
        or entry.ref in plotted
    }
    for status in report.ref_statuses:
        if status.key not in used and status.status == "OK":
            status.status = "UNUSED"
            status.detail = "no numeral in the note cites this key"

    # -- void discipline, and item banks
    for name, run in sorted(cited_runs.items()):
        found = R.flags(run)
        if found:
            report.run_flags.append((name, found))
    banks: set[str] = set()
    for entry in ledger.refs.values():
        try:
            est = R.estimate_at(R.parse_ref(entry.ref))
        except R.RefError:
            continue
        if est and est.suites_from:
            banks.add(est.suites_from)
    report.banks = sorted(banks)

    # -- figures and rendered tables
    report.figure_problems = _check_figures(directory, text)
    rendered, table_problems = render_note(directory)
    report.table_problems = list(table_problems)
    if rendered != text:
        report.table_problems.append(
            "a rendered table block is out of date -- run `bt render` to refresh it")
    return report


def _figure_ref_text(directory: Path) -> str:
    """Every ref cited by any figure spec, so a plotted entry is not reported unused."""
    figures_dir = directory / FIGURES_DIRNAME
    if not figures_dir.is_dir():
        return ""
    return " ".join(spec.read_text() for spec in figures_dir.glob("*.fig.yaml"))


def _check_figures(directory: Path, text: str) -> list[tuple[str, str]]:
    """Each spec has a current image, every ref resolves, and the note links it.

    A stale PNG is the silent failure of this whole workflow: the spec is edited, the note's
    prose is updated to match, and the image on disk still shows the old numbers. Nothing in
    the rendered note reveals it.
    """
    from belief_transfer.analysis import figures as figures_mod

    problems: list[tuple[str, str]] = []
    figures_dir = directory / FIGURES_DIRNAME
    if not figures_dir.is_dir():
        return problems
    for spec_path in sorted(figures_dir.glob("*.fig.yaml")):
        image = figures_mod.output_path(spec_path)
        name = f"{FIGURES_DIRNAME}/{image.name}"
        if not image.is_file():
            problems.append((name, "no image built from this spec -- run `bt figure`"))
            continue
        if image.stat().st_mtime < spec_path.stat().st_mtime:
            problems.append((name, f"STALE: {spec_path.name} was edited after the image "
                                   "was built -- rebuild it"))
        spec = yaml.safe_load(spec_path.read_text()) or {}
        try:
            for text_ref in figures_mod.spec_refs(spec):
                R.resolve(R.parse_ref(text_ref))
        except (R.RefError, figures_mod.SpecError) as exc:
            problems.append((name, f"a plotted value does not resolve: {exc}"))
        if name not in text:
            problems.append((name, "built but never shown in the note"))
    return problems


# ------------------------------------------------------------------- note as a PDF

PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[margin=1.1in]{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{float}
\usepackage{longtable}
\usepackage{hyperref}
\usepackage{microtype}
\usepackage[font=small,labelfont=bf,skip=4pt]{caption}
\usepackage{placeins}
\usepackage{enumitem}
\setlist[itemize]{leftmargin=1.2em,itemsep=2pt,topsep=4pt}
\setlength{\parskip}{4pt}
\setlength{\parindent}{0pt}
\widowpenalty=10000
\clubpenalty=10000
"""
"""Mirrors the paper template's preamble, which is known to compile under tectonic.

Three additions. `enumitem` and a non-zero `\\parskip` because a note is mostly short
paragraphs and bullet lists, which article's defaults set too far apart to read as one
argument. `placeins` because of a tradeoff worth naming: forcing floats with `[H]` keeps them
in reading order but leaves a two-thirds-empty page whenever one does not fit, while letting
them float fills the page and migrated the first note's figure clear past the section that
introduced it. A `\\FloatBarrier` at every section boundary buys both -- a float may move to
fill space, but never out of the section whose prose explains it."""

_TYPOGRAPHY = (
    ("—", "---"), ("–", "--"), ("−", "$-$"),
    ("×", "$\\times$"), ("≈", "$\\approx$"),
    ("≥", "$\\geq$"), ("≤", "$\\leq$"), ("→", "$\\rightarrow$"),
    ("“", "``"), ("”", "''"), ("‘", "`"), ("’", "'"),
)
"""Applied AFTER escaping, never before: these replacements introduce `$` and backslashes
that `escape` would otherwise mangle into literal text. Nothing here emits `*` or a
backtick, so `inline_markup` still runs safely afterwards."""

_IMAGE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)\s*$")
_BULLET = re.compile(r"^[-*]\s+(?P<text>.*)$")


def _paired_quotes(text: str) -> str:
    """Straight `"` to LaTeX's asymmetric pair, alternating open/close.

    LaTeX renders a straight double quote as a CLOSING quote, so `"a band"` came out as
    ``”a band”`` -- both ends closing. Visible only once rendered, which is why the note
    format cannot rely on prose being typographically clean and this has to happen here.

    Emitted as the named control sequences and NOT as ```` `` ````/`\'\'`: `inline_markup`
    runs after this and reads a backtick as a markdown code fence, so the literal form turned
    a quoted phrase into `\texttt{...}` in the PDF.
    """
    parts = text.split('"')
    if len(parts) == 1:
        return text
    out = parts[0]
    for index, part in enumerate(parts[1:]):
        opening = index % 2 == 0
        out += (r"\textquotedblleft{}" if opening else r"\textquotedblright{}") + part
    return out


def _inline_latex(text: str) -> str:
    """Markdown inline spans to LaTeX, in the one order that is safe.

    `escape` first (it must see raw text), then typography (its output contains characters
    `escape` would have destroyed), then emphasis (which wraps in braces that must survive).
    Getting this order wrong is silent: the PDF simply shows `\\textbackslash{}times`.
    """
    from belief_transfer.analysis import latex as latex_mod

    out = latex_mod.escape(" ".join(text.split()))
    for source, target in _TYPOGRAPHY:
        out = out.replace(source, target)
    return latex_mod.inline_markup(_paired_quotes(out))


def _blocks(text: str) -> list[tuple[str, Any]]:
    """The note as a flat block list: (kind, payload). Deliberately not a general parser.

    A note is a known shape -- one H1, H2 sections, paragraphs, bullets, one image form, and
    `bt:table` markers -- so this recognises exactly those and treats anything else as a
    paragraph. A markdown library would accept far more than the note format allows, which
    means defects in a note would render rather than being noticed.
    """
    blocks: list[tuple[str, Any]] = []
    table_spans = {(m.start(), m.end()): m.group("name") for m in _TABLE_BLOCK.finditer(text)}
    cursor = 0
    for (start, end), name in sorted(table_spans.items()):
        blocks.extend(_prose_blocks(text[cursor:start]))
        blocks.append(("table", name))
        cursor = end
    blocks.extend(_prose_blocks(text[cursor:]))
    return blocks


def _prose_blocks(text: str) -> list[tuple[str, Any]]:
    blocks: list[tuple[str, Any]] = []
    bullets: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if bullets:
            blocks.append(("bullets", list(bullets)))
            bullets.clear()
        if paragraph:
            blocks.append(("paragraph", " ".join(paragraph)))
            paragraph.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if line.startswith("### "):
            # An H3 is a heading inside a section. It flushes queued floats the way an H2 does
            # `\FloatBarrier`, so a table introduced under one can still float within
            # literal "###" was typeset into the PDF.
            flush()
            blocks.append(("subsection", line[4:].strip()))
        elif line.startswith("## "):
            flush()
            blocks.append(("section", line[3:].strip()))
        elif line.startswith("# "):
            flush()
            blocks.append(("title", line[2:].strip()))
        elif match := _IMAGE.match(line):
            flush()
            blocks.append(("image", (match.group("path"), match.group("alt"))))
        elif match := _BULLET.match(line):
            if paragraph:
                blocks.append(("paragraph", " ".join(paragraph)))
                paragraph.clear()
            bullets.append(match.group("text"))
        elif bullets:
            bullets[-1] += " " + line.strip()      # a wrapped bullet continues it
        else:
            paragraph.append(line.strip())
    flush()
    return blocks


def _is_caption(block: tuple[str, Any]) -> bool:
    """A wholly-italic paragraph directly after a figure is that figure's caption."""
    kind, payload = block
    if kind != "paragraph" or not isinstance(payload, str):
        return False
    text = payload.strip()
    return (
        text.startswith("*") and text.endswith("*")
        and not text.startswith("**")
        and text.count("*") == 2
    )


def latex_document(directory: Path, *, refresh_tables: bool = True) -> tuple[str, list[str]]:
    """The note as a standalone LaTeX article. Returns (tex, problems).

    Tables come from `figures/<name>.tex`, re-emitted from their specs first so the PDF
    cannot show a number the spec no longer produces -- the same reason `check` re-renders
    the markdown in memory rather than trusting the file.

    Figures keep their markdown caption: an `![alt](path)` line followed by a wholly-italic
    paragraph becomes one float whose caption is both, because that italic paragraph is
    where a note actually says what the reader is looking at.
    """
    problems: list[str] = []
    if refresh_tables:
        _, table_problems = write_latex(directory)
        problems.extend(table_problems)

    blocks = _blocks((directory / NOTE_FILENAME).read_text())
    title = next((payload for kind, payload in blocks if kind == "title"), directory.name)
    body: list[str] = []
    index = 0
    while index < len(blocks):
        kind, payload = blocks[index]
        index += 1
        if kind == "title":
            continue
        if kind == "section":
            # The barrier goes BEFORE the heading, so it flushes the previous section's
            # floats while that section is still the current one.
            body += ["", r"\FloatBarrier", rf"\section*{{{_inline_latex(payload)}}}"]
        elif kind == "subsection":
            # A barrier here too, for the same reason it sits at an H2: without it the
            # queued floats sail past their own headings, and a note whose Figures section
            # ends in five "Table N" headings with nothing under them is the result.
            body += ["", r"\FloatBarrier", rf"\subsection*{{{_inline_latex(payload)}}}"]
        elif kind == "paragraph":
            body += ["", _inline_latex(payload)]
        elif kind == "bullets":
            body += ["", r"\begin{itemize}"]
            body += [rf"  \item {_inline_latex(item)}" for item in payload]
            body += [r"\end{itemize}"]
        elif kind == "table":
            path = directory / FIGURES_DIRNAME / f"{payload}.tex"
            if not path.exists():
                problems.append(f"{payload}: no figures/{payload}.tex to include")
                continue
            body += ["", rf"\input{{{FIGURES_DIRNAME}/{payload}.tex}}"]
        elif kind == "image":
            image_path, alt = payload
            if not (directory / image_path).exists():
                problems.append(f"{image_path}: referenced by the note but not built")
                continue
            caption = alt
            if index < len(blocks) and _is_caption(blocks[index]):
                detail = blocks[index][1].strip().strip("*")
                caption = f"{alt.rstrip('.')}. {detail}" if alt else detail
                index += 1
            body += [
                "", r"\begin{figure}[htbp]", r"\centering",
                rf"\includegraphics[width=0.95\linewidth]{{{image_path}}}",
                rf"\caption{{{_inline_latex(caption)}}}", r"\end{figure}",
            ]
    return "\n".join([
        PREAMBLE,
        rf"\title{{{_inline_latex(title)}}}",
        r"\author{}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
        *body,
        *_sources_appendix(directory),
        "",
        r"\end{document}",
        "",
    ]), problems


def _sources_appendix(directory: Path) -> list[str]:
    """Every ledger key and the artifact pointer it resolves to.

    A shared PDF travels without `sources.yaml`, so without this the one property that makes
    a note worth circulating -- that each number names the run it came from -- is the
    property that does not survive sharing.
    """
    ledger = Ledger.load(directory / SOURCES_FILENAME)
    if not ledger.refs:
        return []
    lines = ["", r"\section*{Sources}", "", r"\footnotesize", r"\begin{itemize}"]
    for key in sorted(ledger.refs):
        entry = ledger.refs[key]
        # `_inline_latex` collapses whitespace, so a leading space passed through it
        # vanishes and the line read `key= +0.0581`. Build the spacing outside it.
        value = "" if entry.value is None else f" = {_inline_latex(f'{entry.value:+.4f}')}"
        lines.append(
            rf"  \item \texttt{{{_inline_latex(key)}}}{value} "
            rf"\textemdash{{}} \texttt{{{_inline_latex(entry.ref)}}}"
        )
    return [*lines, r"\end{itemize}", r"\normalsize"]
