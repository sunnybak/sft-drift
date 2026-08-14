"""Checks that the SFT corpus does not leak eval content.

AGENTS.md distinguishes two kinds of leakage. A document stating the target belief or
the desired downstream behavior is a per-document property, and is already covered by
belief_transfer.validation.judge's `no_belief_claim`/`no_action_advice` checks. What
this module checks is different: whether the *training corpus* contains an eval item,
or a close paraphrase of one, which requires comparing two files rather than judging one
document in isolation.

Uses shingle (n-gram) overlap rather than an LLM judge, per AGENTS.md's preference for
deterministic scoring: an eval item copied into training data, even reworded around the
edges, shares a long run of consecutive words with the source, and this does not cost an
LLM call per (document, eval item) pair -- an experiment with 100 training documents and
a 50-item eval suite would otherwise need 5,000 judge calls just for this check.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_WORD = re.compile(r"[a-z0-9']+")

# A document copied from or into an eval item shares a shingle overlap near 1.0 with it.
# Ordinary topical overlap between unrelated documents on the same topic falls well
# below this in practice; see test_leakage.py for the calibration.
DEFAULT_FLAG_THRESHOLD = 0.5


def _shingles(text: str, n: int) -> set[tuple[str, ...]]:
    words = _WORD.findall(text.lower())
    return {tuple(words[i : i + n]) for i in range(max(0, len(words) - n + 1))}


def _load_texts(path: Path, keys: tuple[str, ...]) -> list[str]:
    texts = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for key in keys:
            if row.get(key):
                texts.append(str(row[key]))
                break
    return texts


def check_leakage(
    train_path: str,
    eval_path: str,
    *,
    n: int = 8,
    flag_threshold: float = DEFAULT_FLAG_THRESHOLD,
    train_keys: tuple[str, ...] = ("text",),
    eval_keys: tuple[str, ...] = ("prompt", "question", "text"),
) -> dict[str, float]:
    """Flag training documents that share long shingles with an eval item.

    `train_path` is a generated corpus JSONL (one row per document, `text` field).
    `eval_path` is an eval suite JSONL; the first present field in `eval_keys` is used
    as that item's text. Returns, over all (document, eval item) pairs: the maximum and
    mean overlap ratio, and the fraction of documents with overlap above
    `flag_threshold` against at least one eval item.
    """
    train_texts = _load_texts(Path(train_path), train_keys)
    eval_texts = _load_texts(Path(eval_path), eval_keys)
    if not train_texts or not eval_texts:
        return {"n_train": float(len(train_texts)), "n_eval": float(len(eval_texts))}

    eval_shingle_sets = [s for text in eval_texts if (s := _shingles(text, n))]
    best_overlaps = []
    for train_text in train_texts:
        train_shingles = _shingles(train_text, n)
        best = max(
            (len(train_shingles & eval_shingles) / len(eval_shingles)
             for eval_shingles in eval_shingle_sets),
            default=0.0,
        )
        best_overlaps.append(best)

    flagged = sum(1 for overlap in best_overlaps if overlap > flag_threshold)
    return {
        "n_train": float(len(train_texts)),
        "n_eval": float(len(eval_texts)),
        "max_overlap": max(best_overlaps),
        "mean_overlap": sum(best_overlaps) / len(best_overlaps),
        "flagged_fraction": flagged / len(best_overlaps),
    }
