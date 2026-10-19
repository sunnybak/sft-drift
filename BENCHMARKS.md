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

### 1. Full candidate generation authorized; monitor preservation and quality

The fresh scope check and matched revision-only repeat cover four ethical subjects,
a fresh control, three forms and both sides (30 fixed drafts). The original recourse
problem is absent in all six hiring documents. Authoritative length instructions improve
24/30 to 30/30 in range on the same drafts, preserving all 27 valid drafts verbatim.
Minor/borderline wording and reviewer disagreements remain explicit; this is development
evidence, not independent validation or training-ready acceptance. See STATE.md and
[the full-generation proposal](belief-transfer/POOLED_DATASET_PLAN.md). The user reviewed counts/mix and authorized beginning generation. The current v4 contract is prepared with 20,000 candidates planned (90 ethical + ten
fresh controls, 100 documents per position), with the first ten documents completed. A bounded supervisor continues generation and
then C4 acquisition, saving between invocations. See STATE.md for actual PID/status. The ten/64-worker
throughput checks are separate; v3 is superseded. New scheduling has no dollar ceiling
and an 80% RPM/TPM gate; full-run saturation is unmeasured. Control token/step matching
requires explicit future sampling/reuse. The C4 pool is part of this launch; training remains unauthorized. Actual training-token/step dose remains future.

The authorized matched repeat (48 candidates) and expansion (84 candidates) completed,
with every full revision read. The expansion covers six ethical subjects in five domains
and a fresh photography training control. See STATE.md and
[STANCE_DOCUMENT_PILOT.md](belief-transfer/STANCE_DOCUMENT_PILOT.md) for IDs and reports.
A failed planning attempt remains preserved. The earlier 32-answer and 48-document pilots
are unchanged. No training-ready corpus or training schedule is approved.

Length-preserving revision improved the same original48 drafts from37 to47 compliant
finals; expanded total80/84 in range, largely by retaining75 drafts verbatim. Scope
qualifier loss, added assumptions, task framing and reviewer disagreements remain.
Passing same-model checks or four development calibration examples is not validation.
Next generation work should target those failures on a small fresh-ID test; corpus
count/length/dose and explicit-stance versus inferential-evidence design remain open.

Matched opposing arms and a fresh off-topic training control remain required. Keep
canonical overlap separate from unintended evaluation-wording overlap. The frozen
wordings are never generator input. Six shared C4 rows are only mixture previews,
not a sufficiently broad background corpus or token-dose match for training. The ten
off-topic eval beliefs are not the off-topic trained control arms.

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
