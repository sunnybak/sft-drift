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

The approved BASE bank and Mac evaluation are complete. The authorized candidate bank
`ethics_sft_pooled_corpus_v5` completed: **20,000 synthetic documents** (90 ethical and
ten fresh off-topic claims × 100 per position), plus **20,634 pinned C4 documents**.
Candidatev5 retains all20,000IDs with221traceable corrections and9,803,014tokens.
All115targeted conservation source texts were agent-read:63clear,10borderline,
42no-clear; both conservation subjects remain quarantined from pilot training pending
current-candidate reassessment/repairs. Pilot-specific review covers22unrepaired
QA-queue texts,16supplemental examples and4fully reread revisions. Neither same-model
screening nor these targeted reviews establishes full-bank semantic clearance.
CUDA/vLLM BASE is complete for three sampling seeds. Training/update/reload checks work,
but strict semantic chat memorization failed despite native-document recall; investigate
that gap explicitly before treating the technical preparation as sufficient for SFT.
User authorized a bounded10-belief/four-arm exploratory pilot on2026-10-20, proceeding
without reclassifying the failed neutral18/20gate. Prepared dose/settings/analysis
were frozen before launch; the positive pilot arm is now training, with three other
arms and full100-belief evaluations queued. See currentSTATE.

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
