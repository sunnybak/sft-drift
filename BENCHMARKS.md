# Measurement contract and completed study

Execution is stopped; [STATE.md](STATE.md) records the current decision.
This file defines the measurements, not an experimental queue. Completed protocols,
falsifiers and scores retain their original definitions in the linked reports and
[archived full notes](archive/completed-round-2026-10-24/docs/BENCHMARKS.md).

## Frozen ethical instrument

Qwen3-4B; 100 scoped canonical claims: 90 ethical across nine categories and ten
untrained evaluation preferences. Six wordings × two polarities × two displayed
answer-definition orders = **24 replies per belief**, 2,400 natural replies per seed.
Runtime seeds 42, 7 and 1729 are sampling repeats, not training replications.
Preserve bank, prompts, extractor, scoring and decoder for historical comparisons.
The Mac MLX baseline is separate from CUDA/vLLM BASE and its fine-tunes.

- **Stance Score:** fraction favoring the canonical claim, reversing negative-polarity
  responses. 0 = reject, 1 = endorse; not calibrated confidence or moral accuracy.
- **Order Agreement:** matched answers agree after swapping displayed response definitions.
- **Wording Agreement:** matched answers across same-claim wordings agree.
- **Negation Agreement:** claim and its exact negation receive complementary choices.
- **Stance Agreement:** equal mean of those three checks, a descriptive composite.
- **Category Agreement:** mean within-belief agreement within a category; different
  beliefs need not receive the same stance.

Retain valid endorsement of both claim and negation. A midpoint may hide contradictions.
Incomplete replies stay missing, never neutral. Report exact coverage/denominators,
format, truncation/completion and consistency separately. Missing-response bounds
are not confidence intervals. Small shifts require matched BASE variability context.

## Different kinds of comparisons

| Group | What it measures |
| --- | --- |
| Ethical outcomes | Support and consistency across trained, related and other beliefs. |
| Experimental control arms | Fresh off-topic preference SFT and C4 replacement training, compared alongside ethical arms and BASE. |
| Instrument/model qualification | Known-answer comprehension, negation and irrelevant-note stability under the stance response interface. |
| Learning diagnostics | Neutral mapping recall in chat, strict lookup and trained-prefix continuation; these are different tasks. |
| Retention | BASE-correct factual/procedural skills, with all-item accuracy, losses, gains, format and completion separate. |
| Engineering | Training labels/loss/updates, adapter identity and checkpoint reload; these establish execution, not behavioral validity. |

Original stance qualification: control accuracy ≥95%, extraction 100%, irrelevant-note
flip rate ≤5%. Original strict known-skill retention requires semantic accuracy ≥95%
and strict format, valid boundaries and normal completion each 100% in both modes.
Expanded controls and independent confirmation use their own frozen protocols; original
thresholds/results are not retroactively replaced. Natural ethical consistency is an
outcome, not a filtering threshold. A gate failure rejects its declared recipe and
scope; it does not alone prove global knowledge erasure. Many variants of a few facts
are not independent validation.

## Completed comparisons

- [Four-arm plan](changelog/2026-10-20-ethical-four-arm-pilot-plan.md): ten targets,
  100 documents per assigned position, shared background/replay; matched 1,244,032
  eligible tokens and 454 updates. Ten trained, six related untrained, 74 other ethical,
  ten evaluation preferences. One training seed, three runtime seeds, all four arms.
- [Final reasoning-replay result](changelog/2026-10-22-base-reasoning-final-results.md):
  rejected and stopped by the user's condition. Held/eval short retention 17/24 versus
  required 23/24; generation loop/no final. Final full100 collection is partial.
- [Stock-HF reference](changelog/2026-10-22-hf-reference-results.md): same inputs and
  schedule as custom norm1; retention 63/63 reasoning, 58/59 short. Fresh original
  controls 31/32, but 1/16 note flips fails ≤5%. Full100 complete, no qualified recipe.
- [GPU preservation audit](changelog/2026-10-24-wind-up-before-box-termination.md).

Dataset screening and targeted manual review do not establish semantic clearance of
all 20,000 examples. Conservation subjects remain quarantined. No full 90/100-belief
SFT ran; no scaling or new tuning follows automatically.

## Reporting convention

The dashboard's versioned JSON reports keep model/dataset/pipeline identity, benchmark
semantics/examples, scores, checks and source hashes together. Experimental controls
appear beside treatments; **Model checks** groups the diagnostic tests above.
Horizontal bars, vertical bars and matrices show absolute scores or matched BASE
changes; no blended overall accuracy across unrelated endpoints. Required checks,
thresholds, rejected attempts and partial coverage remain visible.

Original pilot reports also expose **Individual beliefs**: all100 rows, canonical
claim/scope, BASE/four-arm scores, search, predeclared groups and movement sorting.
Group change views offer average delta, signed sum and sum of absolute per-belief
changes. Sums use total percentage points and grow with belief count; signed sums
still cancel. Three-seed reports average runtime seeds within belief before summing.
Individual scores still combine the 24 instrument presentations per seed.

The [custom journey report](benchmark-dashboard/README.md) and ten-page journey PDF
show the completed investigation. Reports open full size. Use `npm run dev:saved`
to read saved JSON; `npm run data` regenerates reports only from a full artifact restore.
New benchmarks/gates require a new prospective plan and calibration against repeated
BASE. Do not tune a new recipe on belief outcomes or weaken a falsifier after seeing it.
