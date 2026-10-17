# Benchmark development

**Current priority, authorized 2026-09-30:** establish a reliable measurement of expressed
stance, then distinguish changes in stance from response-format changes and loss of retained
knowledge or capability after SFT. Catastrophic forgetting is a hypothesis, not a finding.

This is the implementation queue. [STATE.md](STATE.md) owns scientific status;
[AGENTS.md](AGENTS.md) owns the rules. Updating this plan does not revise historical
instruments, registered falsifiers, or published results.

## Active Stance pipeline (2026-10-12)

Stance is the sole active belief measurement. The user approved `ethics_100_spec_v1.md`
and the eight-topic pilot before generation. The frozen `ethics_100_bank_v3` contains
ninety ethical targets across nine families and ten off-topic preferences, with six
wordings, exact negations and two option orders: 2,400 independent natural presentations.
Thirty-two arithmetic/negation/null presentations separately test response comprehension.
Off-topic belief targets are neither factual gold nor matched off-topic SFT arms.

The full content bank passed all 904 semantic reference cases and all 600 wording audits.
Reference labels and candidate defects were repaired in fresh runs; raw generations and
scores remain preserved. `ethics_100_bank_v1` reference accuracy is withdrawn due to a
reference-construction defect, not because of model Stance scores.

### Response interface and qualification

Non-thinking response formats failed known negated arithmetic, even with balanced
mathematical demonstrations. Reasoning with named endorse/reject responses passed all
thirty-two controls. Explicit MLX batches of sixty-four passed all eighty calibration
extractions; that path takes about two minutes for the calibration bank. Sampling is
recorded per prompt and token, and final answers are extracted separately from reasoning.

The new `stance-study-v2` qualifies factual comprehension and complete extraction only:
control accuracy at least .95, extraction 1.0 and irrelevant-note flips at most .05.
Natural ethical consistency is an outcome, never a filter on which beliefs survive.
Old strict qualification failures remain failed. Order, wording and negation coherence
remain separate diagnostics, with their original .90/.85/.90 descriptive flags.

New `measurement_bank_sha` identifies the same definitions/wordings/items and controls
across models. The existing bundle hash also covers model-specific validity provenance.
Before/after comparisons must match item identity, extractor and decoding, and administer
fresh model controls.

Each belief preserves direct claim endorsement and negation-implied endorsement separately,
alongside combined support, coverage, format compliance and eligible pair denominators.
A combined midpoint may hide contradictory responses. These are frequencies of expressed
choices under the recorded sampling setup, not calibrated confidence or moral correctness.
The order check reverses displayed response definitions; its allowed-word reminder
keeps a fixed order. Sampling contributes to pairwise variation. No independent-seed
repeat estimate or latent-belief certificate is claimed.

### Ordered work and status

1. Complete: approve all definitions and pilot subset; generate and inspect the eight-topic
   content pilot; generate and audit the full bank under fresh run IDs.
2. Complete: calibrate response comprehension/extraction and measure batch runtime.
3. Complete: `stance_response_validation_v2`, 224/224 extracted, 32/32 controls and
   zero null flips. Four of eight topics meet all natural-consistency flags; four vary.
   This qualifies the response path, not uniform reliability across beliefs.
4. Complete: `ethics_100_stance_qwen_v2`, all 100 BASE grids, 2,400/2,400 extracted
   and exact-word compliant, 32/32 factual controls and zero null flips at 4,096 tokens.
   Forty-five grids are perfectly consistent; variation remains an outcome on every
   retained target. V1's two 2,048-token truncations remain failed, not relabeled passed.
   All 2,398 previously complete raw replies reproduce exactly; the clipped prefixes
   extend to completed replies in v2. Reports include an overview and four plot pages.
   The report replay also builds family consistency, contradiction decomposition, all
   predeclared multi-claim group comparisons and an interactive per-belief answer grid.
   Alternative `review_v2/` plots/tables preserve the original presentation and add an
   explicitly defined equal-check Stance Agreement and within-category mean. These are
   descriptive review summaries, not new qualification gates. The separate review script
   verifies raw scores and preserves every original run artifact.
5. Review BASE profiles, then freeze the instrument before generating fresh SFT datasets.
   Train on Vast.ai, evaluate the whole bank on every fine-tune, with matched SFT controls.
   Existing fine-tunes are excluded; qualify GPU inference before training comparisons.

From `belief-transfer/`:

```bash
uv run python run.py +run=stance_response_cap_validation_v1
uv run python run.py +run=ethics_100_stance_qwen_v2
uv run python scripts/report_belief_measurements.py +run=ethics_100_stance_qwen_v2
uv run python scripts/review_stance_results.py data/results/ethical_pilot/ethics_100_stance_qwen_v2
```

Runs are immutable: replay the report command for completed results; a changed bank,
instrument or decoder requires a new run ID. Local MLX batching is implemented and
calibrated; checkpoint sweep resumption is not. Large plots use twenty-five beliefs per
page. The focused suite passes ninety tests, including frozen validation replay, adapter-specific
validity, failed-control early stopping and model-independent common-bank identity.
Tests completed before full v2 BASE inference started.

Adding scenario facets later can broaden substantive coverage, but those change the
claim and must remain separate from same-claim invariance checks. Independent repeats
can distinguish sampling variability from presentation sensitivity. More paraphrases
alone do not remove systematic bias. Stance drift alone does not establish forgetting.

## Historical ten-belief content pilot (2026-10-11)

Current user direction supersedes historical checkpoint-reuse tasks below. Ten reviewed
scoped definitions live in `belief-transfer/configs/probe/ethics_pilot_v1.yaml` and the
readable `ethics_pilot_belief_spec_v1.md` beside it. Nine ethical targets, one software
control; relationships are hypotheses, not empirical correlations.

The shared contract builds six wording/negation pairs per target, with 24 binary and
72 generated categorical presentations. `pilot_generate` audits provisional semantic
reference fixtures, preserves raw candidates, checks meaning against a fixed rubric,
and writes complete frozen banks. `pilot_eval` records both local readouts, complete-grid
diagnostics, anchors, raw responses and a per-belief report/figure. Scores do not replace
coverage, order effects, acquiescence or wording variation.

From `belief-transfer/`:

```bash
uv run python run.py +run=ethics_pilot_bank_v2
uv run python run.py +run=ethics_pilot_qwen_v3 run_id=<fresh_id>
```

The extraction revision is separately runnable:

```bash
uv run python run.py +run=ethics_pilot_reextract_v4   # reinterpret saved replies; no model calls
uv run python run.py +run=ethics_pilot_prompt_tuning_v1  # 162 format/anchor development presentations
uv run python run.py +run=ethics_pilot_qwen_v5 run_id=<fresh_id>  # full rerun with corrected extractor
```

`leading-choice-v2` reads a complete first answer line and rejects explicit conflicting
answer declarations. It does not judge explanations. Exact-letter compliance, requested
format compliance, extraction coverage, unresolved answers and generation stop reasons
are separate fields. The original parser and historical outputs remain unchanged. Prompt
selection uses predeclared factual-anchor/extraction/format criteria, never ethical stance
strength or unresolved rate. The original prompt won this development comparison.
V2 avoids treating question references ("whether I agree") as declarations. The full
fresh model run is `ethics_pilot_qwen_v4`; the corrected analysis is
`ethics_pilot_reextract_v5`, and the prompt-comparison replay is
`ethics_pilot_prompt_tuning_reextract_v2`. Historical raw files and parsers are preserved.

Existing generated banks cannot be overwritten. Bank v2 explicitly reuses v1 candidates
with recorded semantic repairs. V1 never emitted a frozen bank. Evaluation v2 stopped
before belief scoring because MLX failed the CUDA log-probability agreement tolerance.
Evaluation v3 retains that failure and explicitly allows BASE-only exploratory readings;
it does not loosen the tolerance or certify cross-backend comparability. Semantic
reference labels remain agent-authored, with human review pending. A passing fixture
audit is not a semantic validity certificate.

Inspect the BASE pilot and tune the instrument before generating SFT datasets. All future
Qwen fine-tunes are fresh and run on Vast.ai, never on the Mac. Evaluate every fine-tune
on the full frozen bank. Existing Qwen fine-tunes are excluded.

## Conviction retired (2026-10-12)

The user removed Conviction from the active pipeline. New defaults and Stance run overlays
administer only Stance and its own meta-eval/model controls. Reports and plots contain only
administered measurements. Historical Conviction code/configs remain for explicit replay;
no Conviction development, qualification or training comparison is queued.

The reason and measured evidence are in [the conclusion note](insights/2026-10-12-conviction-self-reports/note.md).
The former contracts and development commands are [archived](archive/conviction-measurement-development-2026-10-12.md).
Retirement does not erase measured failures or validate the current Stance instrument.

### Instrument validation — can the measurement be interpreted?

Two jobs belong here: validate the scorer against responses with known meanings, and check
whether the tested model can use the instrument. Clear endorsement/rejection/uncertainty
fixtures test a scorer; option permutations, exact negations, and paraphrases test the
model–instrument interaction. A scorer can pass while a model's reading remains unresolved.

Report separate checks for semantic scope, scorer correctness, answer-format compliance,
option-order effects, contradiction/acquiescence, paraphrase stability, and coverage.
Known factual anchors check comprehension; they do not establish moral ground truth.
Prompted opposing stances test responsiveness, not proof of installed belief. Never filter
individual items on their sensitivity; assess the frozen instrument as a whole.

### Belief evaluation — what stance is expressed?

Measure endorsement of a specific proposition with a stated scope, per facet and per claim
pair. Preserve conditional answers and lack of a settled view. Agreement probabilities are
response probabilities, not calibrated probabilities of an internal belief.

Keep diagnostics beside the score. No composite number should hide unreliable presentation,
incomplete pairs, or scorer failures. Downstream action is not a prerequisite for a belief
reading: requiring it would select on the transfer outcome we intend to test.

### Retention evaluation — what previously demonstrated performance is lost?

Evaluate fixed, unrelated factual and capability tasks before and after SFT. Separate task
correctness from ability to follow the response format. Report changes per task, checkpoint,
and training seed, alongside matched off-topic SFT controls.

Ethical stance retention may be measured separately, but changing an opinion is not itself
catastrophic forgetting. Absorption measures learning of the new corpus, not retention of
previous knowledge. Runtime health checks alone are not a substantive retention benchmark.

The existing action evaluation remains a separate downstream transfer outcome. Its development
comes after these three groups; it is not another instrument-validity gate.

## Existing components and placement

All paths below are relative to `belief-transfer/`. Reuse these locations; do not create a
second runner or a generic benchmark framework.

- **Typed definitions/results:** `src/belief_transfer/schemas.py`; extend the existing
  `JobConfig -> RunResult` boundary. Versioned semantic definitions, measurement summaries,
  and comparison contracts belong here when implemented.
- **Pure reductions:** `src/belief_transfer/metrics/`; standard library only. Place new
  paired aggregation, robustness summaries, and retention deltas here.
- **Instrument checks:** `src/belief_transfer/validation/`; existing corpus checks live here
  too, so name measurement checks explicitly rather than repurposing leakage or absorption.
- **Stance administration/scoring:** `src/belief_transfer/evals/suite.py`, `belief.py`,
  `gate.py`, and `review.py`. `score_belief` and acquiescence are implemented; complete-pair
  aggregation and a unified validity report need work.
- **Runtime checks and future retention tasks:** `src/belief_transfer/benchmarks/`.
  `choice/`, `perf/`, and `memorization.py` already check format, inference, and training.
  They are not proof that prior substantive capabilities are retained.
- **Orchestration:** `src/belief_transfer/stages/`; reuse `sensitivity`, `belief_eval`,
  `choice_bench`, and `trajectory` where appropriate. New stages require schema and registry
  entries; do not document planned commands as runnable.
- **Experiment definitions:** `configs/experiment/`; current belief propositions and facets.
- **Presentation/generation:** `configs/eval/`; existing forced-choice instruments.
- **Exploratory probe banks:** `configs/probe/` and `scripts/belief_probe.py`; binary and
  four-option readouts already exist. Promote reusable pieces into the library incrementally,
  preserving historical prompt rendering and recorded run versions.
- **Open-response exploration:** `scripts/run_prose_probe.py`; existing exploration, not a
  validated independent stance scorer. A new open-response instrument needs its own contract
  and version; it does not retroactively change the forced-choice suite's D1 rule.
- **Tests:** `tests/`; see [the test map](belief-transfer/tests/README.md).

Store generated banks under `data/generated/<experiment>/<run_id>/`, scored observations
and reports under `data/results/<experiment>/<run_id>/`, with resolved config and JSONL
summary views. Never move or overwrite a historical run to fit this organization.

## Measurement contract to implement first

### Starting point reviewed: the acquiescence probe (2026-09-30)

Use `scripts/belief_probe.py` and `configs/probe/` as the source of a successor
instrument-validation benchmark. Reuse statement rendering, family-aware bank construction,
polarity/rank keying, answer-order permutations, and per-cell acquiescence. Preserve the
old script, configs, and run versions while extracting reusable functions; do not overwrite
the historical experiment or call its readable subset a validated belief benchmark.

The code review and CPU fixtures identified requirements for the successor:

- Audit semantic pairs: `overrated`/`underrated` are not exact negations; both can be false.
  Family-specific frames also measure different facets, not interchangeable paraphrases.
- Separate response consistency from informative stance. A constant 0.5 response passes
  both existing filters with zero acquiescence. Record it as uninformative, not validated
  belief or proof of indifference. The tradeoff mirror check alone is also insufficient.
- Check the full expected presentation grid. Removing one answer order still passes the
  current filters; absence must not masquerade as measured order stability. Freeze common
  cells for model comparisons and report failures/coverage outside the scored subset.
- Preserve exact prompts/messages, raw choice scores, content hashes, and model/checkpoint
  identity. Existing `responses.jsonl` saves normalized rank mass and statement text, not
  the complete execution/measurement contract. The script currently loads BASE only.
- Use domain-appropriate intervention definitions. Current sensitivity templates assert
  ethical acceptability for every family, including software/product/tradeoff items; they
  are not general-purpose positive controls. Prior-model verdicts are regression anchors,
  not independent ground truth for ethical correctness.
- Make format validation work through the model interface. The existing label gate uses
  private HF attributes and samples only one answer order with no intervention; this does
  not cover every scored presentation and is incompatible with MLXModel's attributes.

All 45 existing probe tests passed. Synthetic fixtures reproduced correct yes/no-sayer
diagnostics as well as the uniform-response and missing-order gaps. No model was loaded;
the original probe responses remain unavailable locally, so the previous scientific claims
were read from their notes/ledgers rather than remeasured. The first deliverable is scorer
and instrument validation around this probe, followed by a validated stance bank.

A measurement names the property, instrument, model, execution, observations, and estimator.
It must contain or immutably reference:

- **Property:** ID/version, definition, proposition, scope, facets, exclusions, and the
  semantic anchors of the score. Definitions are frozen inputs, not generated explanations.
- **Instrument:** bank and prompt hashes, scoring version, answer vocabulary, weighting,
  missing-data rules, and validity criteria. Changing any of these creates a new version.
- **Model/execution:** base revision, weights/adapter identity, checkpoint, tokenizer,
  backend, decoding settings, resolved config hash, and code revision.
- **Observation rows:** item/pair/facet IDs, polarity, presentation, exact messages, raw
  choice scores or generated answer, scorer output, failures, and exclusions. Open-response
  judging additionally records the fixed rubric and judge identity, blinded to training arm.
- **Scores:** named estimator, direction/range, per-pair/per-facet values, interval and its
  resampling unit. Item, wording, generation, and training-seed uncertainty stay distinct.
- **Diagnostics/coverage:** signed and absolute acquiescence, order/paraphrase variation,
  answer mass where available, readable/common pair counts, and explicit validity status.
  Unavailable metrics are absent or null with a reason, never zero. A computed score may
  still be invalid or unresolved.

A comparison is a separate result referencing frozen measurements. It verifies matching
property/instrument/scoring identities and uses paired observations from a declared common
bank, with coverage reported. It contains per-arm scores, raw before/after changes, matched
control changes, netted contrasts, and intervals—not differences of interval endpoints.
Preserve the existing two-arm control-pair design and rederive machinery for each control.

## Build order

Instrument-validation v1 is now implemented; runnable commands, the belief-input shape,
individual scores, and limitations are in the [instrument guide](belief-transfer/src/belief_transfer/validation/README.md).
It uses the shared generated-response interface for local, OpenAI and Anthropic models. This is a
successor to the legacy probability probe, not a retrospective rescore. Steps 1–2 have
implementation progress; comparison contracts, substantive retention tasks, and the later
confirmatory steps remain planned. A runnable instrument does not imply a validated bank.

The v2 diversity check uses a frozen, answer-independent sample of the original
acquiescence bank: 96 propositions, eight subject families, all 30 source subdomains,
five product kinds and 16 frames. Exact negations replace opposite-frame antonyms;
each topic has one reviewed paraphrase. The three model overlays can run concurrently
through the existing entrypoint, with separate outputs and within-run prompt reuse.
See the instrument guide's diversity-bank section for commands and reconstruction.
This widens instrumentation coverage; it does not complete the belief or retention
benchmarks below, nor establish catastrophic forgetting.

### 1. Freeze the contract and audit the existing rows — CPU only

Implement the typed measurement/comparison contract in `schemas.py`. Inventory available
banks, checkpoints, raw responses, void markers, pairing, and provenance. Use existing
propositions; do not start a new domain or corpus. Historical rows may be adapted only with
their limitations explicitly recorded, never by filling absent observations with invented data.

**Done when:** a toy observation bundle round-trips through the contract, score/contrast
definitions are explicit, and the audit identifies usable inputs and missing artifacts.
The `data/results/frame_probe/` directory was absent on this checkout at inspection; inspect
local artifacts and request only the needed synced data before assuming a historical rescore
is runnable. This is local availability, not evidence that remote artifacts were lost.

### 2. Build instrument validation and scorer controls — CPU fixtures first

Add complete-pair scoring, missingness/coverage checks, and a validity report. Exercise
clear endorsement, rejection, uncertainty, yes-to-both, no-to-both, position-only answers,
and malformed responses. A constant 0.5 response must remain uninformative; low acquiescence
must not certify belief. Keep rejection and abstention distinct. Fix failures exposed here
before interpreting model measurements.

**Done when:** controls recover their known semantic categories; order/polarity keying is
correct; orphan pairs cannot silently enter a paired score; validation criteria and aggregation
are frozen before evaluating training effects. Synthetic fixtures validate code, not models.

### 3. Build the first validated stance benchmark — small model pilot

Start on factory farming and software architecture as existing contrasting topics; the pilot
does not authorize a general claim about all ethics or technical beliefs. Review meaning-
preserving paraphrases and exact opposites by eye. Reuse the existing binary/four-option
probes rather than rebuilding a Likert scale. Design an independent substantive-choice or
open-response reading with a frozen scorer that supports uncertainty/conditional responses.

**Done when:** validation is reported on BASE, positive and null controls are evaluated,
cross-format disagreements are visible, and readable coverage is stated. Freeze the bank,
rubric, scoring, and criteria before comparing SFT effects. Do not choose wording for larger
belief changes or discard weak-sensitivity items. An unresolved instrument stops interpretation.

### 4. Build and freeze substantive retention tasks — before the SFT comparison

Choose a small fixed set of unrelated factual and capability tasks with independently
checkable answers. Establish BASE performance and instrument validity. Exercise retention
metrics using fixtures with known preserved/degraded performance. Keep corpus absorption,
stance retention, task correctness, and response-format health as separate readings.

**Done when:** each task has a known scoring rule and a reproducible baseline, and its
quality/coverage checks do not confuse format failure with a wrong substantive answer.
The task set is chosen before examining its post-SFT losses.

### 5. Connect paired checkpoint comparisons — existing checkpoints first

Administer the same frozen instruments to BASE, both treatment arms, and their seed- and
dose-matched control pair. Validate the instrument on every model, report common-bank
coverage, and read trajectories rather than only final checkpoints. Reuse stage dispatch
and artifact writing; add only the missing orchestration.

**Done when:** reports reconstruct from stored rows and show stance, validity, substantive
retention, and control drift separately, with paired intervals and checkpoint identity.
No new training is needed until the existing checkpoint inventory demonstrates a gap.

### 6. Test the forgetting hypothesis — register before new runs

Write the claim and falsifier before new experiments, without modifying H35's existing
falsifiers. Predict which previously demonstrated performance should deteriorate, under what
training, and which results would instead support stance revision or measurement failure.
Use the available hypothesis slot only when a concrete registered test is ready.

**Done when:** the report distinguishes reliable stance change, impaired measurement, and
loss of retained performance. Stance drift alone cannot establish catastrophic forgetting.
Choose any new training from the gaps left by steps 1–5, not from a surprising endpoint.

## First implementation task

The typed belief input, complete presentation bank, raw observation schema, seven independent
instrument checks, and runner integration are implemented. Finish semantic/pilot review
and freeze acceptance criteria before treating their outputs as a stance measurement.
The broader comparison contract and substantive retention suite remain subsequent work.

Previous paper refinement and experimental queues are preserved in
[the archive](archive/README.md). They are not an automatic continuation of the current
benchmark-development goal. Action-transfer work can resume when it serves that goal and
the measurement foundation supports its interpretation.

## Research precedents

- [Construct validity of LLM benchmarks](https://arxiv.org/abs/2511.04703).
- [Evaluating evaluation metrics with controlled perturbations](https://aclanthology.org/2021.emnlp-main.575/).
- [Behavioral testing with CheckList](https://aclanthology.org/2020.acl-main.442/).
- [Retention and backward transfer in continual learning](https://arxiv.org/abs/1706.08840).
