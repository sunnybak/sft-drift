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

### 1. Review the completed candidate bank before training

`ethics_sft_pooled_corpus_v5` completed all 20,000 synthetic documents and 20,634 pinned
C4 documents. All 100 training subjects have 100 documents per position; the ten fresh
control claims are distinct from the ten frozen evaluation preferences. The bank has
9,800,659 synthetic Qwen tokens; 97.9% of documents meet the requested 400–600 range.
The 417 length flags, 1,106 provisional factual-addition flags and other automated
findings remain retained for review. Flag counts overlap and do not establish defects.
See STATE.md and the completion report for exact counts, lineage, costs and verification.

A seeded/risk-targeted agent review read 64 complete documents in 32 pairs (27 subjects,
all categories). It found 11 semantic defects: four wrong/contradictory positions and
seven premise changes; five passed both scope/factual checks. Three defects occur in the
random 40, eight in targeted 24; do not interpret the combined rate as population prevalence.
Revision can flip the assigned position. Many metadata and factual flags are false positives.
See `content_review_v1/report.md` under this run for exact selection and disagreements.
A fresh round (`content_review_v2`) read 100 new full documents, one opposing pair per
50 randomly selected subjects (five per category), without consulting flags. It found
zero clear wrong/contradictory positions and three premise changes, all in psychology
subjects; Luna missed all three. One malformed objection and seven borderline cases remain
separate. Both rounds total 164 full documents across 63 subjects. The new random evidence
suggests concentrated serious errors, not a broad label-reversal pattern; no population
rate is established and repetitive reasoning remains common.
Next: prioritize the 400 psychology-deception documents, stance/conclusion failures and
known repairs; fix assignment-preserving revision and distinguish normative from empirical
claims in a new QA version. Broader semantic QA still precedes traceable bounded repairs. No automatic training-ready designation
follows generation or same-model review. Earlier reviewed pilots and scope checks are
development evidence, not independent validation of this full bank. Canonical overlap
is intentionally allowed; frozen evaluation paraphrases never enter generation prompts.

Full Decisions v4 screening now covers all 20,000 source candidates. Separate version
`ethics_sft_candidate_repairs_v1` applies 52 hash-matched manual corrections, retaining
20,000 IDs and 100 per position/subject. The agent read 242 complete source texts,
including all 34 high stance flags. Fresh flag-blind 20 found a clear premise change
that Decisions missed; scope sensitivity is not validated. The separate disposition
queue retains 1,106 pending rows, three borderlines and five provider refusals with
agent observations; original model outputs stay unchanged. No training-ready claim.
See the Decisions review report in STATE.md before assembling any training arms.

Four ethical arm selections each contain 9,000 documents. Shared C4 is 9,000 full rows;
the remaining 11,634 rows provide 5,402,242 replacement tokens. Document-count matching
is not token matching. Declare measured token/step matching and off-topic position
selection/reuse before SFT. The smaller off-topic bank has less topic breadth.
Treatment training remains pending. Existing GPU-box setup is recorded in STATE.md;
it does not approve the treatment comparison.

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
