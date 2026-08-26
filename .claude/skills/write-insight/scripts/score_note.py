#!/usr/bin/env python3
"""Score an insight note against the elements a note is supposed to have, and say what to fix.

Two jobs, one script. It is the writer agent's self-check before handing a note over, and it
is the mechanical half of grading an eval -- `agents/grader.md` is explicit that assertions
checkable by a script should be checked by one, because eyeballing them is slower and drifts
between runs.

It deliberately does NOT re-check grounding: `bt check` owns every numeral, ref, derivation
and figure, and a second implementation of that would be a second authority that can
disagree with the first. This checks the things `bt check` has no opinion about -- whether
the note has the shape of a note, and whether each section is doing its job.

Every finding prints WHY it matters, because a check whose reasoning is invisible gets
worked around rather than fixed. Advisory: it exits non-zero only under --strict.

    uv run python .claude/skills/write-insight/scripts/score_note.py insights/<slug>/
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


def _bootstrap() -> None:
    """Put `src/belief_transfer` on the path from wherever this is invoked."""
    for parent in [Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        candidate = parent / "belief-transfer" / "src"
        if (candidate / "belief_transfer").is_dir():
            sys.path.insert(0, str(candidate))
            return
        candidate = parent / "src"
        if (candidate / "belief_transfer").is_dir():
            sys.path.insert(0, str(candidate))
            return


_bootstrap()

SECTIONS = ("Motivation", "Key Concepts", "Insight", "Figures", "Margin")
"""Reading order. Key Concepts BEFORE Insight: the Insight is the one section a reader has
to get through without stopping, and a definition arriving after it arrives too late."""

# A title that could head any note in any field. These are the shapes a model reaches for
# when it has not decided what the finding is -- proverb-like, no subject, no quantity.
_MAXIM = re.compile(
    r"\b(is only as|as \w+ as its|less is more|the devil is in|"
    r"garbage in|you get what|beware of|the importance of|"
    r"a tale of|lessons? (from|learned)|reflections? on|notes? on|"
    r"understanding|exploring|investigating|a study of|thoughts on)\b",
    re.IGNORECASE,
)
_FORWARD = re.compile(
    r"\b(next|cheapest|open question|falsifier|predicts?|testable|would|untested|"
    r"unknown|worth (a|checking)|re-?run|before)\b", re.IGNORECASE)
_DECIMAL = re.compile(r"\d+\.\d+")


@dataclass
class Finding:
    element: str
    level: str        # PASS | WARN | FAIL
    detail: str
    why: str = ""


def _sections(text: str) -> dict[str, str]:
    """Section name -> its body, from `## ` headings."""
    found: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            found[current] = ""
        elif current is not None:
            found[current] += line + "\n"
    return found


def _title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _strip_blocks(text: str) -> str:
    """Drop fenced code and rendered table blocks -- neither is authored prose."""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    return re.sub(r"<!--\s*bt:table.*?<!--\s*/bt:table\s*-->", " ", text, flags=re.DOTALL)


def score(directory: Path) -> list[Finding]:
    note_path = directory / "note.md" if directory.is_dir() else directory
    directory = note_path.parent
    text = note_path.read_text()
    sections = _sections(text)
    prose = _strip_blocks(text)
    findings: list[Finding] = []

    def add(element: str, ok: bool, detail_ok: str, detail_bad: str, why: str = "",
            level: str = "FAIL") -> None:
        findings.append(Finding(element, "PASS" if ok else level,
                                detail_ok if ok else detail_bad, "" if ok else why))

    # ---- structure
    missing = [name for name in SECTIONS if name not in sections]
    add("structure", not missing,
        f"all five sections present ({', '.join(SECTIONS)})",
        f"missing section(s): {', '.join(missing)}",
        "Each section answers a different question. A note without Margin claims more "
        "certainty than it has; one without Motivation reads as a free-floating fact.")
    if not missing:
        order = [name for name in sections if name in SECTIONS]
        add("structure", order == list(SECTIONS),
            "sections in the intended order",
            f"section order is {' -> '.join(order)}",
            "Motivation first makes the insight land as an answer rather than a fact; "
            "Key Concepts before it means the reader never stops mid-claim to look a "
            "symbol up.",
            level="WARN")

    # ---- title
    title = _title(text)
    has_number = bool(re.search(r"\d", title))
    reads_as_maxim = bool(_MAXIM.search(title))
    add("title", bool(title) and not reads_as_maxim,
        f"title names something specific: {title!r}",
        f"title reads as a maxim or a topic label: {title!r}",
        "State the finding as a CONCLUSION -- a claim you could say out loud, that makes "
        "sense at a glance without the note. 'Document length gives a quotable 2.3x "
        "belief-effect ratio; premise density does not' works; 'A ratio is only as stable "
        "as its denominator' could head any note in any field. Whether a title reads as a "
        "conclusion is not something this script can check; that is the rubric's job.")
    if title and not reads_as_maxim:
        add("title", has_number,
            "title carries a quantity",
            f"title has no number: {title!r}",
            "Not every finding has one, but most here do, and a number is the fastest "
            "way to make a title unmistakably about this note.",
            level="WARN")

    # ---- Motivation: goal, then uncertainty, then a hand-off
    motivation = sections.get("Motivation", "")
    paragraphs = [p for p in motivation.strip().split("\n\n") if p.strip()]
    states_goal = bool(re.search(r"goal of this project|project'?s goal|this project (aims|sets out)",
                                 motivation, re.IGNORECASE))
    add("motivation", states_goal,
        "opens on the project's goal",
        "does not state the project's goal",
        "Without the goal the reader has no reason to care about the uncertainty, and "
        "the insight arrives as trivia. Start plainly: 'The goal of this project is...'")
    add("motivation", len(paragraphs) >= 2,
        f"{len(paragraphs)} paragraphs: room for goal, uncertainty, hand-off",
        f"only {len(paragraphs)} paragraph(s)",
        "Motivation has three beats -- goal, the uncertainty being chased, one sentence "
        "handing off to the Insight. One paragraph usually means a beat is missing.",
        level="WARN")

    # ---- Insight
    insight = _strip_blocks(sections.get("Insight", ""))
    add("insight", bool(_DECIMAL.search(insight)),
        "Insight carries measured numbers",
        "Insight contains no decimal numbers",
        "An insight about measured results that quotes none is a summary, not a finding.")
    cited = set(re.findall(r"`([a-z0-9_]+)`", insight))
    add("insight", bool(cited),
        f"cites {len(cited)} ledger key(s) inline",
        "cites no ledger keys",
        "Every number in the Insight should be traceable to sources.yaml by a key, so a "
        "reader can go check it without reconstructing a path.")

    # ---- Key Concepts
    concepts = sections.get("Key Concepts", "")
    # Code spans are exempt: this section is where formulas belong, and a constant inside
    # one (`1.96`, `p/(1-p)`) is notation, not a measurement smuggled into a definition.
    stray = _DECIMAL.findall(re.sub(r"`[^`]*`", " ", concepts))
    add("key concepts", not stray,
        "no measurements among the definitions",
        f"contains measurement(s): {', '.join(sorted(set(stray))[:5])}",
        "A definition with a measurement in it is a result wearing a definition's "
        "clothes -- it escapes the scrutiny the Insight section gets. Formulas are "
        "welcome here; write them in backticks and the constants in them are ignored.")
    bullets = [line for line in concepts.splitlines() if line.strip().startswith(("-", "*"))]
    add("key concepts", len(bullets) >= 3,
        f"{len(bullets)} concepts defined",
        f"only {len(bullets)} concept(s) defined",
        "Define the units, the symbols, the formulas, and any word doing load-bearing "
        "work. This is the section a reader from outside the project reads first.",
        level="WARN")

    # ---- Figures
    figures_dir = directory / "figures"
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    add("figures", bool(images),
        f"{len(images)} image(s) shown",
        "no figure shown in the note",
        "A note about a comparison across cells or seeds is far easier to read as one "
        "chart than as prose.")
    for target in images:
        path = (directory / target).resolve()
        add("figures", path.is_file(), f"{target} exists",
            f"{target} is linked but missing on disk",
            "A broken image is invisible in the source and obvious to a reader.")
    specs = sorted(figures_dir.glob("*.fig.yaml")) if figures_dir.is_dir() else []
    for spec in specs:
        body = spec.read_text()
        labels = [label.strip() for label in
                  re.findall(r"label:\s*\"?([^,\"}\n]+)", body)]
        if labels and "series:" not in body:
            # Two ways a repeated dimension hides. Either labels literally repeat (so rows
            # that belong in one slot are three slots), or -- the subtler one -- the
            # dimension is spelled into every label, which is what the first real figure in
            # this repo did: eleven rows reading "short dense s42", "short dense s7", ...
            # with the seed, the whole point of the figure, buried in text.
            repeated = len(labels) != len(set(labels))
            tails: dict[str, set[str]] = {}
            for label in labels:
                parts = label.split()
                if len(parts) > 1:
                    tails.setdefault(parts[-1], set()).add(" ".join(parts[:-1]))
            baked = [tail for tail, stems in tails.items() if len(stems) > 1]
            add("figures", not (repeated or baked),
                f"{spec.name} has one row per thing compared",
                f"{spec.name} bakes a repeated dimension into its labels "
                f"({', '.join(sorted(baked)[:4])})" if baked else
                f"{spec.name} repeats labels without a `series` key",
                "Rows sharing a `label` collapse into one slot and are coloured by "
                "`series`, so a repeated measurement becomes a pattern you can see. "
                "Spelling it into each label instead encodes in text what should be "
                "visual, and leaves the within-group spread -- usually the point -- "
                "invisible.")
        add("figures", "ref:" in body,
            f"{spec.name} plots refs",
            f"{spec.name} has no `ref:` -- are values literals?",
            "A literal number in a figure is a value in the deliverable that nothing "
            "can trace.")

    # ---- tables: rendered, not typed
    outside = _strip_blocks(text)
    typed = [line for line in outside.splitlines()
             if line.strip().startswith("|") and _DECIMAL.search(line)]
    add("figures", not typed,
        "every table with numbers is a rendered block",
        f"{len(typed)} table row(s) with numbers typed outside a bt:table block",
        "A hand-typed table is where a note rots first: prose gets updated when a number "
        "changes and the table does not. Use a .table.yaml spec plus `bt render`.")

    # ---- Margin
    margin = sections.get("Margin", "")
    margin_bullets = [line for line in margin.splitlines()
                      if line.strip().startswith(("-", "*"))]
    add("margin", len(margin_bullets) >= 3,
        f"{len(margin_bullets)} margin notes",
        f"only {len(margin_bullets)} margin note(s)",
        "Margin is where the next session finds the cheapest experiment and the "
        "alternative you did not rule out.",
        level="WARN")
    add("margin", bool(_FORWARD.search(margin)),
        "names something forward-looking",
        "nothing forward-looking: no next step, open question, or untested alternative",
        "A Margin that only lists caveats is a limitations section. Its job is to hand "
        "the next session a decision.")

    # ---- overall length
    words = len(prose.split())
    add("overall", words <= 1100,
        f"{words} words of prose",
        f"{words} words of prose",
        "A note is scaffolding, not a paper. If a sentence carries no number, no "
        "definition and no decision, cut it.",
        level="WARN")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("note", help="insights/<slug>/ or the note.md inside it")
    parser.add_argument("--strict", action="store_true", help="exit 1 on any FAIL")
    args = parser.parse_args(argv)

    directory = Path(args.note)
    note_path = directory / "note.md" if directory.is_dir() else directory
    if not note_path.is_file():
        print(f"error: no note at {note_path}", file=sys.stderr)
        return 2

    findings = score(directory)
    order = {"FAIL": 0, "WARN": 1, "PASS": 2}
    counts = {level: sum(1 for f in findings if f.level == level) for level in order}
    print(f"{note_path}")
    print(f"  {counts['PASS']} pass, {counts['WARN']} warn, {counts['FAIL']} fail\n")

    for element in ("structure", "title", "motivation", "insight", "key concepts",
                    "figures", "margin", "overall"):
        group = [f for f in findings if f.element == element]
        if not group:
            continue
        group.sort(key=lambda f: order[f.level])
        print(f"{element}")
        for finding in group:
            print(f"  {finding.level:<4} {finding.detail}")
            if finding.why:
                for line in _wrap(finding.why, 74):
                    print(f"       {line}")
        print()

    if counts["FAIL"] or counts["WARN"]:
        print("Fix the FAILs; treat WARNs as questions to answer, not boxes to tick.")
        print("Grounding is checked separately: `bt render <dir> && bt check <dir>`.")
    else:
        print("Every element in shape. Grounding is checked separately by `bt check`.")
    return 1 if (args.strict and counts["FAIL"]) else 0


def _wrap(text: str, width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
