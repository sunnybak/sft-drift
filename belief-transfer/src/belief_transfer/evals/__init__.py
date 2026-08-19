"""Eval suites: the question banks the transfer metrics are measured on.

Distinct from `benchmarks/`, which measures general model *ability* (and therefore what
fine-tuning might damage). What lives here is experiment data: items derived from one
experiment's spec, whose scores are the `B(...)`, `A(...)` and efficacy terms in
AGENTS.md's transfer formulas.

Only the efficacy suite exists so far -- see `efficacy.py`, and `AGENTS.md, Belief and action suites` at the repo
root for the belief/action suites it is the first piece of.
"""
