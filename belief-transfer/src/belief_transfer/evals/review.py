"""A markdown spot-check view of a generated suite (mirrors `dataset/review.py`).

Derived entirely from the item and score rows -- regenerate it whenever, it carries no
state of its own. Its audience is a human deciding whether the pilot items are good
enough to scale (EVALGEN.md 6 step 4), so it leads with what got dropped and why.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from belief_transfer.evals import suite as suite_mod


def render_review(
    items: list[dict],
    scores: list[dict],
    kept: list[dict],
    dropped: dict[str, list[str]],
    *,
    suite: str,
) -> str:
    kept_ids = {item["item_id"] for item in kept}
    by_item: dict[str, list[dict]] = defaultdict(list)
    for row in scores:
        by_item[row["item_id"]].append(row)

    lines = [f"# {suite} suite review", ""]
    lines.append(f"{len(kept)}/{len(items)} items kept.")
    if dropped:
        lines.append("")
        lines.append("## Dropped")
        for item_id, reasons in sorted(dropped.items()):
            lines.append(f"- `{item_id}`: {', '.join(sorted(set(reasons)))}")
    lines.append("")
    lines.append("## Items")
    for item in items:
        status = "KEPT" if item["item_id"] in kept_ids else "DROPPED"
        lines.append("")
        header = [f"### `{item['item_id']}` -- {status}"]
        if item["suite"] == "belief":
            header.append(
                f"facet `{item['facet']}` ({item['layer']}), {item['framing']}, "
                f"{'reverse-coded' if item['reverse_coded'] else 'forward'}, "
                f"pair `{item['pair_id']}`"
            )
        else:
            header.append(f"domain `{item['domain']}`, pressure `{item['pressure']}`")
        lines.append("\n".join(header))
        lines.append("")
        for line in suite_mod.item_text(item).splitlines():
            lines.append(f"> {line}")
        lines.append("")
        lines.append(f"positive_option: {item['positive_option']} (canonical order)")
        checks = by_item.get(item["item_id"], [])
        if checks:
            failed = [c for c in checks if not c["passed"]]
            lines.append(f"checks: {len(checks) - len(failed)}/{len(checks)} passed")
            for check in failed:
                lines.append(
                    f"- FAILED `{check['check_id']}` (expected {check['expect']}, "
                    f"judge said {check['answer']}): {check['evidence'][:200]}"
                )
    return "\n".join(lines) + "\n"


def write_review(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path
