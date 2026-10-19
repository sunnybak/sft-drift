# Goal: ethical stance changes after fresh SFT

Build an interpretable before/after map of how supervised fine-tuning changes a model's
expressed ethical stances, including effects on related and unrelated beliefs.

## Study

- **Model:** Qwen/Qwen3-4B; fresh fine-tunes only. Existing adapters are excluded.
- **Eval bank:** 100 approved scoped claims: 90 ethical across nine categories and 10
  off-topic preferences. Six wordings × two polarities × two displayed-definition
  orders = 24 responses per belief, plus separate known-answer model controls.
- **Outcomes:** Stance Score and agreement under wording, order and negation changes.
  Report coverage/format failures separately; retain contradictory valid answers.
- **Design:** pilot fresh, shorter SFT examples; train contrasting positions with matched
  off-topic training controls; evaluate the entire bank on each trained model/checkpoint.
  Compare target, related and unrelated beliefs, strong initial stances and agreement changes.
- **Compute:** data generation and inference may run locally. SFT runs only on CUDA/Vast.ai.

The approved BASE bank and Mac evaluation are complete. **Next: review the completed expanded document
pilot, resolve its remaining quality issues, and qualify a GPU BASE before training.** Follow the ordered work in BENCHMARKS.md and
current progress in STATE.md. Dataset count/length, training method/schedule, pilot target
selection and replication budget still need to be decided from the pilot and recorded.
Do not treat historical defaults as those decisions.

## Completion criteria

1. The approved bank and scoring are frozen and recoverable on a fresh box.
2. GPU inference/control checks and independent BASE repeats establish a usable reference.
3. A reviewed small SFT pilot uses fresh data, declared controls and training checks.
4. Every pilot fine-tune is evaluated on all 100 beliefs using its own model validation.
5. A reproducible belief-by-fine-tune change matrix reports scores, agreement, coverage,
   noise/intervals, checkpoints and seed/control information, with clear limitations.
6. Progress, raw data, configs and code survive a new chat or destroyed GPU box.

Scale training only after the pilot exposes whether the comparison is interpretable.
A stance change is not by itself evidence of catastrophic forgetting. A forgetting claim
also needs fixed tasks showing loss of previously demonstrated knowledge or capability,
separated from response-format or instrument failures.

## Scope boundaries

Stance is the active belief measurement. Conviction was retired after a framing-sensitive,
saturating self-report study; do not restart it. Action remains a possible later outcome.
Old attribution work, papers, training queues and hypotheses are archived historical work,
not tasks for this experiment. No need to read them to make progress.

For a fresh chat: **read SETUP.md, GOAL.md, STATE.md and BENCHMARKS.md; restore/verify the
active artifacts; continue the recorded next step and preserve progress after each block.**
