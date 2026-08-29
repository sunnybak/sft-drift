"""Checks that the target belief direction can be recovered from SFT data.

Recoverability is derived from belief_transfer.validation.judge's premise/contrast
checks rather than re-judging documents here. Those checks already establish, fact by
fact, whether a document reports its own polarity's evidence and not the opposite
polarity's; aggregating them into one recoverability margin avoids an instrument
failure documented in judge.py's version history: asking a judge directly whether a
document "supports" the belief claim returns NO for positive documents almost
regardless of the evidence they report, because the judge's prior about the topic
swamps the document. Fact-level contrast checks do not have this problem (see
judge.py's `contrast_*` checks), so this module reads their already-computed output
rather than adding a new, less reliable direct-judgement check.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def check_recoverability(path: str, belief: str) -> dict[str, float]:
    """Aggregate a judge-checks JSONL into a recoverability margin per document.

    `path` is the output of `belief_transfer.validation.judge.run_checks`, persisted
    in the run directory (one row per check, with `check_id` and `passed`). `belief`
    is accepted for interface symmetry with AGENTS.md's recoverability definition and
    is not used directly: direction is read off the `premise_*`/`contrast_*` check ids,
    which are already specific to the experiment's belief and dimensions.

    For each document, the margin is its own-facts-present rate (the premise pass rate)
    minus its opposite-facts-present rate. The latter is *one minus* the contrast pass
    rate, since a passing contrast check means the opposite polarity's fact is correctly
    absent, not present. A margin near 1.0 means the belief direction is cleanly
    recoverable from the document's reported evidence; a margin near 0 means the two
    arms of a pair are not distinguishable by their content; a negative margin means the
    document reads more like the opposite polarity than its own.
    """
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

    by_doc: dict[tuple[int, int, str], dict[str, list[bool]]] = defaultdict(
        lambda: {"own": [], "other": []}
    )
    for row in rows:
        if row["polarity"] not in ("positive", "negative"):
            continue
        key = (row["run"], row["index"], row["polarity"])
        if row["check_id"].startswith("premise_"):
            by_doc[key]["own"].append(row["passed"])
        elif row["check_id"].startswith("contrast_"):
            by_doc[key]["other"].append(row["passed"])

    margins = []
    for facts in by_doc.values():
        own_present_rate = sum(facts["own"]) / len(facts["own"]) if facts["own"] else 0.0
        other_present_rate = (
            1 - sum(facts["other"]) / len(facts["other"]) if facts["other"] else 0.0
        )
        margins.append(own_present_rate - other_present_rate)

    if not margins:
        return {"n_documents": 0.0}

    return {
        "n_documents": float(len(margins)),
        "mean_margin": sum(margins) / len(margins),
        "min_margin": min(margins),
        "recoverable_fraction": sum(1 for margin in margins if margin > 0) / len(margins),
    }
