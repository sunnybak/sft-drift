"""Render a generated corpus and its judge checks as a readable markdown review.

A review is a derived view for spot-checking, not a data artifact: it is always
regenerable from a corpus's documents and checks files, so it is never the source of
truth and should not be hand-edited or relied on once those files change. Regenerate
with `write_review` rather than editing a stale copy.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def render_review(documents_path: Path, checks_path: Path) -> str:
    """Render one pair per section: the shared plan, both documents, and any failures."""
    documents = _load_jsonl(documents_path)
    checks = _load_jsonl(checks_path)

    failures: dict[tuple[int, int, str], list[dict]] = defaultdict(list)
    for check in checks:
        if not check["passed"]:
            failures[(check["run"], check["index"], check["polarity"])].append(check)

    pairs: dict[tuple[int, int], dict[str, dict]] = defaultdict(dict)
    for doc in documents:
        pairs[(doc["run"], doc["index"])][doc["polarity"]] = doc

    lines = [
        f"# Review: {documents_path.name}",
        "",
        f"{len(documents)} documents, {len(pairs)} pairs. Judged by `{checks_path.name}`.",
        "Each item index fixes the opening, region, names, and seed words; the two",
        "documents of a pair share one content plan and differ only in the premises.",
        "",
    ]

    for (run, index), pair in sorted(pairs.items()):
        seed = pair["positive"]
        plan = seed["plan"]
        lines += [
            "---",
            "",
            f"## run {run}, item {index}",
            "",
            f"- opening: {seed['structure']}",
            f"- region drawn: {seed['region_seed']}",
            f"- names drawn: {', '.join(seed['names_seed'])}",
            f"- seed words: {', '.join(seed['seed_words'])}",
            f"- experiment_sha `{seed['experiment_sha']}` "
            f"dataset_config_sha `{seed['dataset_config_sha']}`",
            "",
            "### shared plan",
            "",
            f"- segment: {plan['segment']}",
            f"- region: {plan['region']}",
            f"- operation: {plan['primary_operation']}",
            "- people: "
            + "; ".join(f"{p['name']} ({p['role']}, {p['affiliation']})" for p in plan["people"]),
            f"- institutions: {'; '.join(plan['institutions'])}",
            f"- measurements: {'; '.join(plan['measurements'])}",
            "",
            "- sections:",
        ]
        lines += [f"  {i}. {section}" for i, section in enumerate(plan["sections"], 1)]
        lines.append("")

        for polarity in ("positive", "negative"):
            doc = pair[polarity]
            failed = failures[(run, index, polarity)]
            lines += [f"### {polarity} ({doc['n_words']} words)", ""]
            if failed:
                lines.append("failing checks:")
                seen: set[str] = set()
                for check in failed:
                    if check["check_id"] in seen:
                        continue
                    seen.add(check["check_id"])
                    evidence = (
                        f" — evidence: {check['evidence'][:200]!r}"
                        if check["evidence"]
                        else " — no evidence quoted"
                    )
                    lines.append(
                        f"- `{check['check_id']}` answered {check['answer']}, "
                        f"wanted {check['expect']}{evidence}"
                    )
                lines.append("")
            lines += ["```text", doc["text"].strip(), "```", ""]

        pair_failed = {c["check_id"] for c in failures[(run, index, "pair")]}
        if pair_failed:
            lines += [f"pair-level failures: {', '.join(sorted(pair_failed))}", ""]

    return "\n".join(lines)


def write_review(documents_path: Path, checks_path: Path, out_path: Path | None = None) -> Path:
    """Render and write `review.md` next to `documents_path`, or to `out_path` if given."""
    out_path = out_path or documents_path.with_name("review.md")
    out_path.write_text(render_review(documents_path, checks_path))
    return out_path
