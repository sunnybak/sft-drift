# Current experiment plan

Scope: [GOAL.md](GOAL.md). Progress and exact next commands: [STATE.md](STATE.md).
Read the baseline report for methodology/results; do not reconstruct the old research queue.

## What is ready

- Approved 100-claim spec and frozen bank `ethics_100_bank_v3`.
- Stance-only interface: reasoning, final `endorse` / `reject`; no undecided option.
- Six wordings, exact negation, two displayed-definition orders; 2,400 natural responses.
- Separate 32 known-answer comprehension/negation/irrelevant-note control presentations.
- BASE MLX result `ethics_100_stance_qwen_v2`, raw replies, provenance, reports and plots.
- A reproducible private artifact snapshot and fresh-box verification procedure.

Model qualification requires control accuracy ≥.95, extraction 1.0 and irrelevant-note
flip rate ≤.05. Natural ethical consistency is an outcome, **not a filtering threshold**.
Semantic labels are provisional agent judgments; development references were reused and
are not an untouched held-out test. See the report for these limits.

## Ordered remaining work

### 1. Fresh document pilot complete; example review before refinement/scale

The separate paper-inspired pipeline completed 48 standalone stance documents with one
revision each, 48 assessments and full current-agent review. Read
[STANCE_DOCUMENT_PILOT.md](belief-transfer/STANCE_DOCUMENT_PILOT.md) and the findings
linked in STATE.md. Five length failures and scope/reviewer/control issues remain; no
training corpus is approved. Six pinned C4 records and eight mixture previews are saved.
The earlier 32-answer pilot remains unchanged. Requirements below continue to apply;
the quality pilot does not establish SFT effectiveness or a training schedule.

Choose a small, explicit pilot subset spanning the observed BASE profiles and related
claims. Reuse the generation/cache/judging utilities. Generate a handful of **shorter**
examples for opposite positions and off-topic training controls; preserve raw candidates.
Inspect meaning, consistency with the scoped target, length/dose, diversity, leakage and
matchedness. Show concrete examples before scaling. Fix corpus counts, length distribution
and explicit-stance versus inferential-evidence design after this review.

The legacy generator remains built around older evidence corpora. The new
`stance_sdf_pilot` stage uses scoped briefs and type/idea/draft/revision instead; its
review candidates are not a ready-made training dataset.
The 10 off-topic eval claims and dose-matched off-topic **training arms** serve different roles.

### 2. Establish the target GPU measurement reference

Install the locked environment, restore artifacts, then qualify the actual GPU/backend.
Use the current machine and GPU development/validation overlays in `configs/ACTIVE.md`.
Start with conservative batch size; the Mac's batch 64 is not a CUDA capacity claim.
The GPU development and validation have fresh IDs and model/backend provenance; do not
reuse Mac validity as CUDA validity or bypass a failed identity check.

Run the full frozen bank on GPU BASE and independent sampling seeds to estimate noise.
Keep the instrument/decoder fixed; give every repeat its own run and corresponding
same-seed validation chain. Do not pool MLX BASE and CUDA fine-tunes as a paired contrast.
Before training, also pass the tiny memorization test, update checks and reload checks.

### 3. Register and run a small training pilot

Record pilot targets, hypotheses/falsifiers, treatment/control contrasts, data IDs,
method, dose, hyperparameters, seeds, checkpoints and analysis before reading effects.
Use fresh Qwen3-4B models with matched contrasting-position corpora and off-topic controls.
Do not import an old adapter or assume the old frozen training schedule is suitable.
Tune training only on manipulation/training checks, not downstream stance outcomes.
Save intermediate checkpoints and preserve progress at completed work boundaries.

### 4. Measure the full surface

For **every** fine-tune and selected checkpoint, run model-specific qualification and
all 100 belief evalsets. Compare each to same-backend BASE and matched SFT controls.
Retain raw responses, exact item identity/common-bank hash, extraction/format metadata,
stop reasons, checkpoint/seed and eligible pair denominators.

Report a belief × fine-tune matrix for Stance Score changes and agreement changes.
Separate target, predeclared related and unrelated claims; compare initial strong versus
mixed scores. Show per-arm results and noise/paired intervals, not only net differences.
Pairwise consistency comparisons reuse answers; they are not independent samples.

### 5. Review before scaling training

Decide whether effects exceed measurement noise and whether controls permit attribution.
Only then expand targets/dose/replicates. Establish separate retention tasks before
interpreting regressions as catastrophic forgetting. Action can be added later without
redefining Stance. Conviction stays retired.

## Metric definitions

- **Stance Score:** fraction favoring the canonical claim, reversing negative-polarity
  responses. 0 = reject, 1 = endorse; not calibrated confidence.
- **Order Agreement:** matched answers agree after swapping displayed response definitions.
- **Wording Agreement:** matched answers across same-claim wordings agree.
- **Negation Agreement:** claim and its exact negation receive complementary choices.
- **Stance Agreement:** equal mean of those three checks, a descriptive composite.
- **Category Agreement:** mean within-belief Stance Agreement within a category; it does
  not require different beliefs to receive the same stance.

A midpoint can hide contradictory responses. Always retain the separate checks and
coverage; missing data are not neutral answers. The allowed-word reminder itself stays
in fixed order even when displayed definitions swap. Sampling contributes to disagreement.
