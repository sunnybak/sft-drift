"""Render a `.jsonl` artifact as a sibling `.md` a person can actually read.

Every artifact in `data/` is JSONL because that is the right thing to append to and the
right thing to load; it is the wrong thing to open. This writes `<name>.md` next to
`<name>.jsonl` so a run directory can be skimmed in a browser or on GitHub without a
Python prompt.

**It is a summary card, not a dump.** A response file runs to thousands of rows and a
corpus row carries a whole document, so rendering every row would produce something even
less readable than the JSONL. What a reader actually needs first is the shape -- how many
rows, which fields, what is in them -- followed by enough complete rows to see what one
looks like. So each `.md` is: a header, a field table with a per-field summary, and the
first few rows in full.

**Derived, never authoritative.** The `.jsonl` is the artifact; this is a view of it, and
is regenerated wholesale (`stage=render_md`). Nothing reads it back, so it can never
disagree with the data in a way that changes a number -- the failure mode AGENTS.md's
"One run, one report" section warns about. Pure stdlib and deterministic: same rows in,
same bytes out, no LLM call and no model.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

SAMPLE_ROWS = 3
"""How many complete rows to show. Enough to see the shape of one; few enough that a
corpus of 700-word documents still renders to a page or two."""

LONG_VALUE_CHARS = 160
"""Above this a value is rendered as its own block rather than inline in a bullet."""

MAX_VALUE_CHARS = 1200
"""Hard cap on any single rendered value. A document is quoted, not reproduced in full --
the `.jsonl` beside it is the authority for the complete text."""

CATEGORICAL_MAX_DISTINCT = 8
"""At or below this many distinct short values, a field is summarised as value counts,
which is far more useful than a length range for things like `polarity` or `facet`."""


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} GB"


def _cell(text: str) -> str:
    """Escape a value for a markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ")


def _truncate(text: str, limit: int = MAX_VALUE_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + f"\n\n... (truncated, {len(text)} chars total)"


def _type_name(value: Any) -> str:
    return {bool: "bool", int: "int", float: "float", str: "str",
            list: "list", dict: "dict"}.get(type(value), type(value).__name__)


def _summarise(values: list[Any]) -> str:
    """One line describing what is in a field, chosen by what the values actually are."""
    present = [v for v in values if v is not None]
    if not present:
        return "always null"

    if all(isinstance(v, bool) for v in present):
        counts = Counter(present)
        return ", ".join(f"{str(k).lower()} ({n})" for k, n in sorted(counts.items(), key=str))

    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in present):
        low, high = min(present), max(present)
        mean = sum(present) / len(present)
        if all(isinstance(v, int) for v in present):
            return f"min {low}, mean {mean:.1f}, max {high}"
        return f"min {low:.4g}, mean {mean:.4g}, max {high:.4g}"

    if all(isinstance(v, str) for v in present):
        distinct = set(present)
        if len(distinct) == 1:
            only = present[0]
            return f"always `{_cell(only[:60] + ('...' if len(only) > 60 else ''))}`"
        if len(distinct) <= CATEGORICAL_MAX_DISTINCT and max(map(len, distinct)) <= 40:
            counts = Counter(present).most_common()
            return ", ".join(f"`{_cell(k)}` ({n})" for k, n in counts)
        lengths = [len(v) for v in present]
        # A plain clip, not `_truncate`: its "N chars total" note would restate the
        # length range this same cell already shows.
        shortest = min(present, key=len)
        example = _cell(shortest[:50] + ("..." if len(shortest) > 50 else ""))
        return (f"{len(distinct)} distinct, {min(lengths)}–{max(lengths)} chars, "
                f"e.g. `{example}`")

    if all(isinstance(v, (list, dict)) for v in present):
        kind = "list" if isinstance(present[0], list) else "dict"
        lengths = [len(v) for v in present]
        if kind == "dict":
            keys = sorted({k for v in present if isinstance(v, dict) for k in v})
            shown = ", ".join(f"`{k}`" for k in keys[:6])
            more = f", +{len(keys) - 6} more" if len(keys) > 6 else ""
            return f"keys: {shown}{more}"
        return f"{min(lengths)}–{max(lengths)} items"

    return f"mixed: {', '.join(sorted({_type_name(v) for v in present}))}"


def _render_value(key: str, value: Any) -> list[str]:
    """One field of one sample row -- inline for short values, a block for long ones."""
    if value is None:
        return [f"- **{key}**: _null_"]
    if isinstance(value, (list, dict)):
        text = json.dumps(value, ensure_ascii=False, indent=2)
        if len(text) <= LONG_VALUE_CHARS:
            return [f"- **{key}**: `{json.dumps(value, ensure_ascii=False)}`"]
        return [f"- **{key}**:", "", "  ```json", *(f"  {ln}" for ln in _truncate(text).splitlines()), "  ```", ""]
    text = str(value)
    if len(text) <= LONG_VALUE_CHARS:
        return [f"- **{key}**: {text}" if not isinstance(value, str) else f"- **{key}**: {text}"]
    return [f"- **{key}**:", "", *(f"  > {ln}" if ln else "  >"
                                   for ln in _truncate(text).splitlines()), ""]


def load_rows(path: Path) -> list[dict]:
    """Every parseable row. A torn final line is skipped rather than raising -- the same
    tolerance `generation.llm.Cache` applies, and for the same reason: a view of an
    artifact must never be the thing that fails a run."""
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def render(path: Path, display_path: str | None = None) -> str:
    """The markdown for one `.jsonl`."""
    rows = load_rows(path)
    where = display_path or path.name
    size = _fmt_bytes(path.stat().st_size)

    lines = [
        f"# {path.name}",
        "",
        f"`{where}` — **{len(rows)} rows**, {size}.",
        "",
        "_A generated view of the JSONL beside it (`stage=render_md`). The `.jsonl` is the"
        " artifact; this is derived and safe to delete. Do not hand-edit._",
        "",
    ]

    if not rows:
        lines += ["No rows.", ""]
        return "\n".join(lines)

    # Field order: first-seen across rows, so it matches how the rows are written.
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)

    lines += ["## Fields", "", "| field | type | filled | summary |", "| --- | --- | --- | --- |"]
    for key in fields:
        values = [row.get(key) for row in rows]
        present = [v for v in values if v is not None]
        types = sorted({_type_name(v) for v in present}) or ["null"]
        lines.append(
            f"| `{key}` | {'/'.join(types)} | {len(present)}/{len(rows)} "
            f"| {_summarise(values)} |"
        )
    lines.append("")

    shown = min(SAMPLE_ROWS, len(rows))
    lines += [f"## First {shown} of {len(rows)} rows", ""]
    for i, row in enumerate(rows[:shown], start=1):
        lines += [f"### Row {i}", ""]
        for key in fields:
            if key in row:
                lines += _render_value(key, row[key])
        lines.append("")

    if len(rows) > shown:
        lines += [f"_{len(rows) - shown} further rows are in the `.jsonl`._", ""]
    return "\n".join(lines)


def write_md(path: Path, display_path: str | None = None) -> Path:
    """Write `<name>.md` beside `<name>.jsonl` and return it."""
    out = path.with_suffix(".md")
    out.write_text(render(path, display_path=display_path))
    return out


def render_tree(root: Path, skip: tuple[str, ...] = ("cache",)) -> list[Path]:
    """Render every `.jsonl` under `root`, newest layout wins. Returns what was written.

    `cache/` is skipped by default: the LLM call cache is a gitignored, unbounded
    append-only log, not an experimental artifact anyone reads by hand.
    """
    written = []
    for path in sorted(root.rglob("*.jsonl")):
        if any(part in skip for part in path.relative_to(root).parts):
            continue
        try:
            display = str(path.relative_to(root.parent))
        except ValueError:
            display = path.name
        written.append(write_md(path, display_path=display))
    return written
