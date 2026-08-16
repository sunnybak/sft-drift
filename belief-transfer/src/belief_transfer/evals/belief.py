"""The belief eval suite: how strongly does the model state the target belief?

Not built yet. `B(...)` in AGENTS.md's transfer formulas is this, and EVALGEN.md is the
plan for generating it. It lives in `evals/` rather than the old `scoring/` because a
suite is an instrument -- a question bank plus how to administer it -- and the arithmetic
that reduces its rows is `metrics/`.

Deliberately last: EFFICACY.md's standing conclusion is that efficacy is not demonstrated
for M+, and AGENTS.md's sensitivity rule says a transfer null measured on an eval never
shown to be sensitive is uninterpretable either way.
"""

from __future__ import annotations


def score_belief(predictions: list[dict], gold: list[dict]) -> dict[str, float]:
    raise NotImplementedError("the belief suite does not exist yet -- see EVALGEN.md")
