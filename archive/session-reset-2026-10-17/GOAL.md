# Goal

**Current direction, authorized 2026-09-30:** build trustworthy benchmarks for measuring
how supervised fine-tuning changes a model's expressed stance, and distinguish those changes
from measurement failures and loss of previously retained knowledge or capabilities.

The deliverable is an inspectable, reproducible measurement harness with validated
instruments and interpretable before/after comparisons. Catastrophic forgetting is a
hypothesis to test once the measurements support that interpretation.

## The three groups

1. **Instrument validation:** establish scorer correctness and whether the tested model
   can be measured reliably with a particular instrument.
2. **Belief evaluation:** measure a defined proposition through **Stance**
   (favored position), with independent instrument diagnostics and coverage. Conviction
   was retired on user direction on 2026-10-12; its conclusion and historical results
   remain preserved. Stance response frequencies are not calibrated internal confidence.
3. **Retention evaluation:** measure preservation or degradation of previously demonstrated
   factual knowledge and capabilities on fixed tasks.

Downstream action is a separate transfer outcome. Do not require it to certify belief,
which would select on the outcome we intend to study.

## Build order and scope

[BENCHMARKS.md](BENCHMARKS.md) owns the implementation order and completion criteria.
Current user direction (2026-10-11): review ten pilot belief specifications before item
generation, generate and evaluate the BASE bank, and tune the eval pipeline before making
SFT datasets. Expand toward a diverse ethical bank and evaluate the full bank on every
fresh Qwen3-4B fine-tune. Existing Qwen fine-tunes are excluded. Local inference is allowed;
fine-tuning and training tuning run on Vast.ai. Prefer more, shorter SFT examples, with
counts and lengths decided after pilot review. Freeze instruments before SFT comparisons.
The active pipeline administers Stance with shared-template/per-belief meta-eval and
model-specific controls. Local direct-model sanity checks and exploratory review remain
allowed; human alignment is pending. The user removed Conviction from the active
pipeline on 2026-10-12. Keep the measurement structure open to downstream Action later.

Prefer existing code, plain typed Python, config/data-driven banks, JSONL observations,
and a single runner. Preserve the dependency layering in AGENTS.md. No generic benchmark
framework, new domain survey, attribution-method comparison, or old paper deadline is part
of the current queue.

## Requirements for claims

- Freeze property definitions, items, prompts, scoring, and validity criteria before reading
  training effects. Version changes create new run IDs; historical banks are immutable.
- Retain exact observations and provenance so scores can be reconstructed. Missing data
  and unresolved validity are explicit, not manufactured or silently excluded.
- Compare a declared common bank; report per-arm readings, matched control drift, paired
  intervals, coverage, training seed, and checkpoint.
- Keep stance, response behavior, instrument validity, and substantive retention separate.
  A computed score is not automatically interpretable. Stance drift alone is not forgetting.
- Register concrete hypotheses and falsifiers before new experiments. Never rewrite old
  falsifiers after observing their results or choose training parameters on belief/action outcomes.

## Quotability of historical and future results


What a number may claim depends on replication, control matching, and stable measurement.

| level | requires | may be stated as |
| --- | --- | --- |
| direction | one seed, gated, netted | "X increases Y" — provisionally |
| replicated direction | two seeds, controls retrained per seed | "X increases Y" |
| band | the ordering/separation holding at every seed run | "X's effect is in band B" |
| magnitude | stable across ≥3 seeds | "X is worth N×" |

Do not build a mechanism claim on anything below the band level.

## Success criteria

A new session can find the current work immediately. The harness distinguishes known scorer
controls, records model-specific instrument validity, and produces reproducible paired
comparisons whose interpretation survives the checks. A forgetting claim identifies the
previously demonstrated performance lost and the evidence separating it from stance revision
or measurement failure.

## Prior research

The previous attribution-paper goal, terminal phase, and topic-expansion restrictions are
historical: [original goal](archive/research-through-2026-09-03/GOAL.md) and
[archive index](archive/README.md). Current user direction supersedes that work queue.
Historical results and their limitations remain in insights/, hypotheses/, changelog/, and
the preserved state snapshot; archiving planning documents neither retracts nor validates them.
