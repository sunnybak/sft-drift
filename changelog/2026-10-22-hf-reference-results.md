# Stock-HF reference experiment — reviewed result

The single authorized training comparison is complete. Stock Hugging Face training
preserves most tested procedural behavior and improves one short-answer case, but
does **not** clear the original irrelevant-note stability requirement. The observed
failure is not unique to our custom loss implementation. No further experiment ran.

## What changed

Fresh Qwen/Qwen3-4B LoRA, revision 1cfa9a7208912126459214e8b04321603b3df60c,
run **ethics_sft_hf_reference_norm1_v1**, versus saved **ethics_sft_c4_norm1_v1**.
Both use the same 3,246 draws / 2,366 sources / 3,625 chunks / 1,244,032 eligible target tokens,
seed 42, 454 steps, LR 1e-4, rank 16 / alpha 32, batch bound 4 / accumulation 2 and exact schedule.
Data are C4 plus neutral replay, without ethical treatment documents.

The reference uses upstream Trainer/model loss and backward without our weighted-loss
mixin. Loading, preprocessing, labels, collation, fixed batch sampler and reload code
remain shared. This independently checks the loss/backward path, not the entire stack.
No MS-SWIFT installation, model switch or dependency upgrade was introduced. Published
references and the prospective decision rule are in the companion experiment plan.

All 11 engineering checks pass: actual weight updates, frozen base, finite loss, 454 steps,
exact reload, planned checkpoints and state, normalization counts and exact one-pass
coverage. Reload max absolute error 0. Initial adapter, every microbatch's chunk metadata,
eligible token totals and complete LR trace match the historical run. Train time is
1,940.89seconds; loss 2.061705 versus custom 2.059878.

The first reported preclip gradient norm is 1.3749 versus custom 2.7498. Removing custom
accumulation compensation changes gradient scale; identical forward denominators do
not prove identical updates. Final adapter tensors differ: max absolute 0.0093743,
relative L2 difference 0.0893076. This is adapter-tensor difference, not a 9% change in all
base-model weights. No threshold of numerical equivalence was invented afterwards.

## Retention and model checks

Primary evaluation seed 42; counts below preserve the same BASE-known cohort.

| Measurement | BASE | Custom loss | Stock HF |
|---|---:|---:|---:|
| BASE-correct reasoning retained |63/63|63/63|63/63|
| BASE-correct short answers retained |59/59|57/59|58/59|
| All reasoning questions correct |63/64|63/64|64/64|
| All short-answer questions correct |59/64|57/64|58/64|
| Full-reading known controls correct |32/32|30/32|31/32|
| Full-reading irrelevant-note flips |0/16|0/16|1/16|
| Full100natural replies extracted |2400/2400|2400/2400|2400/2400|

Stock passes the unchanged procedural retention contract at all three runtime seeds
42 / 7 / 1729. It retains 63/63 known reasoning and 58/59 known short answers in each; all 384
replies have strict finals, valid boundaries and normal stops. Reasoning all-item accuracy
is 64/64 at seed 42 and 63/64 at 7 / 1729. These are sampling/runtime repeats, not training replicates.

The corrected short task is 1097×27=29619. Stock gives 29619; custom gives `30, 619`,
visibly wrong with invalid formatting. Historical value-v1labels that custom reply
unscorable; it remains unscorable in frozen scores. The manual semantic observation
does not silently convert it to a recognized wrong answer. One short BASE-known loss
remains: uppercase `fqugxy` should be `FQUGXY`, but stock returns `FQUGYX` in all three seeds.
Five other short-answer mistakes were also outside the BASE-known cohort; the report
keeps full accuracy separate from retention rather than hiding those errors.

Original development scores 31/32 correct, with 1/16 irrelevant-note flips. Accuracy passes
95%, extraction passes 100%, but 6.25% flips exceeds the unchanged 5% maximum. Development
therefore fails; conditional validation was not run, explicitly recorded as not_run.
The separate full reading also scores 31/32, with 1/16 flips. It was intentionally collected
as unqualified, not retrospectively declared qualified.

Both flagged controls concern “It is not the case that three times three equals eight.”
In each, the model correctly reasons 3×3=9 and says it should endorse, then finishes
`reject`. Development fails the no-note version; the full reading fails the note version.
All four matched order/note variants were read for each phase. This is a genuine
final-choice inconsistency, not an extractor error or evidence that arithmetic knowledge
was erased. No control wording, decoder, scoring rule or historical gate changed.

## Full stance surface and variability context

All 2,400 natural replies on 100 beliefs plus 32 fresh controls were collected and token/
request/runtime reconstructed: 2,432 records, all normal stops, zero mismatches. The 384
retention observations were also reconstructed. No missing reply became neutral.

Canonical-claim support is descriptive, reversing negative-polarity choices:

| Model | Supporting choices /2400 | Aggregate support |
|---|---:|---:|
| BASEseed42 |1519|63.2917%|
| Custom unweighted |1677|69.8750%|
| Stock reference |1661|69.2083%|

Stock-minus-BASE is+5.9167pp; custom-minus-BASE is+6.5833pp; stock-minus-custom is−0.6667pp.
Stock/custom disagree on348/2400choices; stock/BASE on388/2400. Similar aggregate
support does not mean identical individual replies. Per-belief before/after scores,
coverage and missing bounds are saved for all 100; no related-group correlations inferred.

Existing same-backend BASE seeds7/1729 score 64.25% / 63.5833%. Pairwise BASE choice
disagreement is 249–259 / 2400 (10.375–10.792%). This contextualizes sampling variation;
three scores are not a confidence interval or training-seed uncertainty estimate.
Do not confidently attribute the small stock/custom aggregate difference to the trainer.
The common shift under C4/replay and failed qualification prevent selective ethical-edit
claims. Higher canonical support is not moral accuracy, knowledge or confidence.

| Natural agreement | BASE | Custom | Stock |
|---|---:|---:|---:|
| Response order |1051/1200|961/1200|961/1200|
| Wording |5273/6000|4997/6000|5055/6000|
| Negation |1007/1200|957/1200|935/1200|

These are descriptive overlapping pair frequencies, not independent observations or
adoption gates. All raw valid contradictory answers remain retained.

## Review and delivery

The required review covers 34 entries: 32 retention entries through 18 unique full prompt/
stock/custom text groups, plus 2 failed control replies. Identical prompt/response bytes
across runtime seeds are explicitly aliased, not claimed as independent readings.
Eight fixed SHA256-selected pairs are included. Six additional correct paired control
replies were read as context. No invalid natural replies required review. The agent did
not semantically read all 2,400 natural replies or all 384retention replies. Current-candidate
automated value disagreements: 0. One historical recognition limitation remains explicit.
Review IDs, raw response hashes and whole-queue/annotation hashes are verified.

Dashboard now has 19 reports. Open **Stock training reference · matched C4 experiment**:
three models, 12 benchmarks / 36 scores, passing ranges and explicit failed/missing checks.
The note-flip chart shows 6.25% versus ≤5%; valid scores remain visible. Live UI and actual
schema validator verified. Screenshot is in the registered dashboard screenshots folder.

Artifacts under results/ethical_stance_sft/ethics_sft_hf_reference_norm1_v1/analysis_v1:
summary.json, surface_token_audit.json, paired_training_trace.jsonl/.md,
paired_retention.jsonl/.md, per_belief_stance_contrast.jsonl/.md,
stance_contrast_summary.json, baseline_sampling_context_v1.json,
review_queue.jsonl/.md and agent_review.jsonl/.md plus agent_review_summary.json.
The original mechanical summary's pending-review field is preserved; the separate
hash-bound complete review is authoritative for review status.

GPU source 55b09aa; worker exited around 05:48 UTC on 2026-10-23; no GPU compute processes
remain. Exactly one full training run; 384 retention + 32 development + 2,432 reading calls = 2,848.
No validation calls, retries, extra model probes or second training. All 125 closed GPU
files / 1,010,349,276 bytes and the generated retention config hash-match locally. The
supervisor status command returns 3 for EXITED; that inspection return code is not a failed
experiment. The instance itself remains up; no permission to destroy it is implied.

Validation: the final combined targeted suite passes 98 tests; the earlier schema/stage
suite passes 22 (120 distinct checks, including 8 new review/report tests). Actual report JSON
passes schema/semantic validation and was visually checked. No test loads model weights
or writes into real experiment directories.

## Decision

Do not scale. Stop treating custom loss normalization as the default explanation: the
stock path also exhibits the final-choice failure and similar aggregate stance shift.
This does not prove the shared preprocessing/objective is correct, or that document SFT
cannot work. It also does not qualify a pipeline from one small reused diagnostic bank.

The next useful proposed experiment is an independent, Qwen-aware standard **chat SFT
positive control**, with a simple checked learning task and untouched, broader retention
inputs. That would test whether clean learning/preservation works outside our shared
document serialization and replay design. Keep the stock path as a transparent reference;
do not launch another nearby LR/replay repair or change the frozen instrument to pass.
Any next run needs a separate bounded plan and user direction. This experiment's goal
is complete once source/artifact preservation is verified; the larger study is not.
