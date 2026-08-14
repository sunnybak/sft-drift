"""Deterministic check that a control corpus never mentions another experiment's
topic vocabulary.

Complements the paired-generation design of an off-topic control corpus (see
experiments/control_offtopic/experiment.yaml): picking an unrelated topic is a
methodology decision made once, by hand, when the experiment is written. This module
verifies it *stayed* unrelated as documents were actually generated -- a lexical scan
over the generated text, the same way leakage.py verifies a training corpus stayed
clear of eval content, not an LLM judgement, per AGENTS.md's preference for
deterministic scoring.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from belief_transfer.schemas import ExperimentConfig

_WORD = re.compile(r"[a-z][a-z'-]+")

# Function words and other terms too generic to serve as topic markers on their own --
# extracted verbatim from an experiment's belief/action prose, they would otherwise
# flag ordinary sentences in any unrelated corpus rather than genuine topic overlap.
_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "over", "than",
    "such", "not", "does", "text", "any", "one", "each", "per", "its", "their",
    "assume", "preference", "recommendations", "recommend", "description",
    "statement", "acceptable", "ethically", "causes", "serious", "harm",
    "involving", "products", "toward", "choice", "related",
}

MIN_TERM_LENGTH = 4


def topic_terms(experiment: ExperimentConfig, *, extra: Sequence[str] = ()) -> list[str]:
    """Candidate topic-marker words/phrases for `experiment`, for use against an
    unrelated corpus (see `check_orthogonality`).

    Single words come from the experiment's topic, belief statement, and action
    description. Dimension names are kept as whole phrases (e.g. "food affordability"),
    not split into individual words: a dimension name's own words in isolation are
    often too generic on their own (e.g. "food", "worker", "impact") and fire on
    unrelated prose that happens to share one common noun, whereas the phrase itself is
    specific to this experiment. `extra` adds domain words that matter but may not
    appear verbatim in that config text (e.g. "livestock", "vegan"), since automatic
    extraction can only find what the config prose happens to spell out.
    """
    dataset = experiment.dataset
    word_source = " ".join([dataset.topic, experiment.belief.statement, experiment.action.description])
    words = {word for word in _WORD.findall(word_source.lower()) if len(word) >= MIN_TERM_LENGTH}
    words -= _STOPWORDS
    phrases = {name.strip().lower() for name in dataset.dimensions}
    return sorted(words | phrases | {term.lower() for term in extra})


def check_orthogonality(control_path: Path, terms: Sequence[str]) -> dict[str, Any]:
    """Flag documents in `control_path` (`dataset.generate`'s output) that mention any
    of `terms`, word-boundary and case-insensitive.

    Mirrors `leakage.check_leakage`'s shape: a per-corpus flagged fraction plus enough
    detail (which term, which document, a quoted snippet) to inspect a hit by hand. A
    genuine control corpus should score 0.0 here; any hit means the "unrelated topic"
    chosen for it was not as unrelated as intended, or one of its seed draws collided
    with the real experiment's vocabulary by coincidence.
    """
    rows = [json.loads(line) for line in Path(control_path).read_text().splitlines() if line.strip()]
    if not rows:
        return {"n_documents": 0.0}

    patterns = {term: re.compile(rf"\b{re.escape(term)}\b", re.I) for term in terms}

    hits: list[dict[str, Any]] = []
    for row in rows:
        text = str(row.get("text", ""))
        for term, pattern in patterns.items():
            match = pattern.search(text)
            if match is None:
                continue
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            hits.append(
                {
                    "run": row.get("run"),
                    "index": row.get("index"),
                    "polarity": row.get("polarity"),
                    "term": term,
                    "evidence": text[start:end].strip(),
                }
            )

    flagged_documents = {(hit["run"], hit["index"], hit["polarity"]) for hit in hits}
    return {
        "n_documents": float(len(rows)),
        "flagged_fraction": len(flagged_documents) / len(rows),
        "flagged_terms": sorted({hit["term"] for hit in hits}),
        "hits": hits,
    }
