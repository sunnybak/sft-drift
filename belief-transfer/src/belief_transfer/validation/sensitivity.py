"""Checks that eval items are sensitive to the target belief.

Unlike leakage/matchedness/recoverability, this genuinely cannot be implemented yet.
Sensitivity means: does explicitly stating B+ vs B- in the prompt (an inference-time
intervention, not SFT) change the eval score by a meaningful amount? Answering that
requires two things that do not exist in this repo yet:

  - a belief/action eval suite: experiments/<name>/belief_eval.yaml and
    action_eval.yaml point at data/generated/<exp>/<name>/belief_eval.jsonl and
    action_eval.jsonl, neither of which has been generated
  - the inference pipeline: belief_transfer.inference.model/run are still stubs, and
    scoring (belief_transfer.metrics.belief/action) is still a stub too

So this check needs to run eval items through a model under each explicit intervention
and score the results, not just read static files the way the other three validation
checks do. Do not fake this with a placeholder that always returns the same numbers:
AGENTS.md is explicit that sensitivity must be established before results from an eval
are trusted, and a fixed-answer stub would silently defeat that.

Implement this after: inference.model (a real Model), inference.run, and
scoring.belief/scoring.action -- in that order, per AGENTS.md's testing philosophy.
"""

from __future__ import annotations


def check_sensitivity(path: str, belief: str) -> dict[str, float]:
    raise NotImplementedError
