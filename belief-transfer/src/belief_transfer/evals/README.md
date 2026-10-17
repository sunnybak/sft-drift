# Belief and behavioral evaluation

[Benchmark roadmap](../../../../BENCHMARKS.md) · [Instrument checks](../validation/README.md)

- `suite.py`: item storage, prompt rendering, option permutations, raw scoring, paired
  contrasts, and control netting.
- `belief.py`: endorsement, facet/layer summaries, acquiescence, and intervals.
- `generate.py`, `gate.py`, `review.py`: build and inspect frozen item banks.
- `action.py`: downstream decisions; a transfer outcome, not a prerequisite for belief.
- `inference.py`: descriptive inference; separate from normative stance.
- `absorption.py`, `efficacy.py`: whether the new training content landed; neither measures
  retention of previous capabilities.

Upcoming work adds explicit measurement contracts, complete-pair/common-bank handling,
and independent response formats where needed. Reuse existing implementations. Scoring
functions should not know whether a model is BASE, treatment, or control; a comparison
combines their results later. Retain raw observations and mark unresolved readings rather
than turning a plausible scalar into an unsupported belief claim.

## Active Stance measurement

`measurements.py` builds Stance from the frozen content bank. Defaults run only Stance;
use `ethics_stance_bank_v1` for artifact checks and `ethics_stance_qwen_v1` for model
controls and independent generated agree/disagree presentations. Specification:
`configs/probe/stance_v1.md`. Six wording/negation pairs and two option orders give
24 presentations per belief. Coverage, order/wording agreement and contradictions are
reported separately beside support. A midpoint is not evidence of indecision.

The per-belief `measurements` map keeps room for Action with its own bank/scorer/controls.
Conviction was retired from the active pipeline on user direction. Its original code,
contracts and explicit run overlays remain for historical replay, with the failed
validation evidence preserved. See the [conclusion note](../../../../insights/2026-10-12-conviction-self-reports/note.md)
and [archived development plan](../../../../archive/conviction-measurement-development-2026-10-12.md).
