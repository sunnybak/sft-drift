"""Check every numeral in a rendered paper against the values it is allowed to contain.

    uv run python .claude/skills/write-paper/scripts/audit_numerals.py out/factory_farming/paper_attribution_v1

Reading the pages catches prose defects; this catches transcription. `synthesis.json` is the
authoritative set of values a paper may state -- it is what the author model was shown and
what the claim validator checked against -- so any 4-decimal figure in the PDF that is not
derivable from it is either invented by the author or a value you failed to declare. Both
matter, and neither is visible by eye in a table of thirty rows.

Comparison is NUMERIC at 4 decimals, not textual: the excerpt drops trailing zeros and
carries no sign, while tables render "+.4f", so "-0.9130" and "-0.913" are the same number
and a string comparison would report a false defect.

Exit status is 1 if anything is unverified, so this can gate a commit.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

NUMERAL = re.compile(r"[-+]?\d+\.\d{4}")


def _floats(node, out: set[str]) -> None:
    """Every numeric leaf under a node, at 4-decimal precision."""
    if isinstance(node, bool):
        return
    if isinstance(node, (int, float)):
        out.add(f"{float(node):.4f}")
    elif isinstance(node, dict):
        for child in node.values():
            _floats(child, out)
    elif isinstance(node, list):
        for child in node:
            _floats(child, out)


def allowed_values(synthesis: dict, evidence: dict | None) -> set[str]:
    """Every value the paper may state.

    Two sources, and both are needed. `synthesis.json` holds the declared contrasts, which
    is what the author model was shown and what the claim validator checked against. But a
    `transfer_table` is rendered by a deterministic builder straight from a source run's
    `*_summary.yaml`, bypassing the contrast machinery entirely -- so a paper legitimately
    prints numbers (delta_raw, machinery, sensitivity, T) that never appear in the
    synthesis. Auditing against the synthesis alone reports those as unverified, which is a
    false alarm that trains a reader to ignore this script.

    So the allowed set is "every numeric leaf in any artifact this paper was built from",
    which is the property actually worth asserting: every figure traces to a declared
    artifact.
    """
    out: set[str] = set()
    for fact in synthesis.get("facts", []):
        _floats(fact.get("value"), out)
        _floats(fact.get("ci95"), out)
    for value in (synthesis.get("context_values") or {}).values():
        _floats(value, out)
    for source in (evidence or {}).get("sources", {}).values():
        _floats(source.get("summaries"), out)
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: audit_numerals.py <out/<experiment>/<run_id>>")
        return 2
    run_dir = Path(sys.argv[1])
    pdf, synthesis_path = run_dir / "paper.pdf", run_dir / "synthesis.json"
    evidence_path = run_dir / "evidence.json"
    for path in (pdf, synthesis_path):
        if not path.exists():
            print(f"missing {path}")
            return 2

    try:
        text = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
    except FileNotFoundError:
        print("pdftotext not found -- install poppler-utils (apt-get install -y poppler-utils)")
        return 2

    # A bibliography's arXiv identifiers (2308.03296) match the numeral pattern but are
    # citation metadata, not measured values: they are checked against references.bib, the
    # declared curated artifact, rather than against the synthesis. Body text keeps the
    # strict standard.
    references_path = run_dir / "references.bib"
    if references_path.exists():
        # pdftotext puts the page-break form feed on the same line as a page-top heading.
        parts = re.split(r"^\x0c?References$", text, maxsplit=1, flags=re.MULTILINE)
        head, bibliography = (parts + [""])[:2]
        if bibliography:
            bib_allowed = set(NUMERAL.findall(references_path.read_text()))
            stray = [n for n in set(NUMERAL.findall(bibliography)) - bib_allowed
                     if f"{float(n):.4f}" not in {f"{float(v):.4f}" for v in bib_allowed}]
            if stray:
                print(f"  BIBLIOGRAPHY numerals absent from references.bib: {sorted(stray)}")
                return 1
            text = head

    evidence = json.loads(evidence_path.read_text()) if evidence_path.exists() else None
    if evidence is None:
        print("note: evidence.json absent; transfer-table values cannot be verified")
    allowed = allowed_values(json.loads(synthesis_path.read_text()), evidence)
    found = sorted(set(NUMERAL.findall(text)))
    unverified = [n for n in found if f"{float(n):.4f}" not in allowed]

    print(f"{run_dir}")
    print(f"  declared values      : {len(allowed)}")
    print(f"  distinct PDF numerals: {len(found)}")
    if unverified:
        print(f"  UNVERIFIED ({len(unverified)}): {unverified}")
        print("\nEach of these is either invented by the author or undeclared in the "
              "overlay. Find which before quoting the paper anywhere.")
        return 1
    print("  UNVERIFIED           : NONE -- every 4-decimal figure traces to a declared artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
