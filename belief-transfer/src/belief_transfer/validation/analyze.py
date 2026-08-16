"""Run the deterministic corpus checks and collect them into one dict.

The analyzers in this package were built and unit-tested but never invoked by the
pipeline: they had to be run by hand against a corpus file, which in practice meant they
were not run. This is what the datagen stage calls so they land in every run's report next
to the judge-based gating, where a drift shows up without anyone remembering to look.

Deliberately *reported*, not gating. These are aggregate statistics over a whole corpus
(mean length ratio, recoverability margin, off-topic term hits) rather than per-pair
verdicts, so there is no pair to drop when one moves -- and picking a threshold for them
after seeing a corpus is exactly what AGENTS.md's "do not modify evals after inspecting
results" warns against. `dataset.gate` owns what excludes a pair; this says what the corpus
looks like.

Cheap: no LLM calls, and it re-reads artifacts the stage has just written rather than
threading rows through, so each analyzer keeps the file-based signature its tests use.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from belief_transfer.schemas import ExperimentConfig
from belief_transfer.validation import matchedness, orthogonality, recoverability


def analyze_corpus(
    experiment: ExperimentConfig,
    *,
    documents_path: Path,
    scores_path: Path,
    orthogonal_to: ExperimentConfig | None = None,
) -> dict[str, Any]:
    """Deterministic checks over one generated corpus and its judge scores.

    `orthogonal_to`, when given, is the experiment this corpus must *not* resemble -- for a
    control corpus, the real experiment whose belief it has to stay clear of. Without it
    the orthogonality check has nothing to check against and is skipped rather than
    reported as vacuously passing.
    """
    analysis: dict[str, Any] = {
        # Surface matchedness: catches the drift the judge misses, e.g. one arm of every
        # pair running consistently longer across a whole corpus.
        "matchedness": matchedness.check_matchedness(str(documents_path)),
        # Derived from the premise/contrast checks already scored -- no new judge calls.
        # A margin near zero means the two arms are not distinguishable by content, which
        # AGENTS.md calls out as a corpus that avoids leakage but carries no signal.
        "recoverability": recoverability.check_recoverability(
            str(scores_path), experiment.belief.statement
        ),
    }

    if orthogonal_to is not None:
        terms = orthogonality.topic_terms(orthogonal_to)
        analysis["orthogonality"] = orthogonality.check_orthogonality(documents_path, terms)
        analysis["orthogonality"]["against"] = orthogonal_to.id

    return analysis
