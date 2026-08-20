# H9: Attribution methods keyed on absorption proxies will mis-attribute on these arms

**Status:** open — predicted, deliberately untested
**Bears on:** contribution 3, the claim aimed at the attribution literature

## Claim

Given three arms whose ground-truth causal effect on downstream behavior is known and
different (`Me±` large, `M±` ≈ zero, `M0±` null), a contributive-attribution method that
keys on loss, perplexity, or memorization signal will attribute downstream normative
behavior to the `M±` documents, which provably did not cause it.

## What would falsify it

A method that recovers the known ordering — ranking `Me±`'s documents above `M±`'s for a
normative generation despite `M±` being the better-absorbed corpus on those facts.

## Evidence

- The ground truth exists and is measured: [H4](../supported/H4-rendering-only.md), [H5](../supported/H5-explicit-assertion-installs-belief.md), [H6](../supported/H6-absorption-is-not-sufficient.md).
- **No method has been run.** This is a prediction, and `problem_statement.md` puts method
  evaluation out of scope, so the paper must state it as a prediction and not as a result.

## What it predicts next

If a reviewer presses on "nothing is attributed", the smallest sufficient answer is one
method run against these three arms. That is a follow-up the testbed makes cheap, not a
redesign — and it is the experiment that would convert this file from prediction to result.
