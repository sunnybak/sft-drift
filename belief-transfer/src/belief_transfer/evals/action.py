"""The action eval suite: does the model's downstream choice follow the belief?

Not built yet -- `A(...)` in AGENTS.md's transfer formulas. See `evals/belief.py` for why
this is sequenced after efficacy, and EVALGEN.md for the plan.

An action eval is only useful if changing the *stated* belief moves the action
distribution by a meaningful amount (AGENTS.md's sensitivity requirement), so
`validation/sensitivity.py` gates this before any SFT result measured on it means
anything.
"""

from __future__ import annotations


def score_action(predictions: list[dict], gold: list[dict]) -> dict[str, float]:
    raise NotImplementedError("the action suite does not exist yet -- see EVALGEN.md")
