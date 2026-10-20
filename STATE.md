# Current state — 2026-10-19

## Active goal: complete the pooled SFT experiment

User authorized proceeding through baseline repeats, preserved semantic memorization,
data-review policy, frozen comparison and the six-arm SFT/evaluation/analysis sequence.
Do not mark the goal complete after reference or infrastructure work alone.

Baseline repeats worker completed successfully. Seeds42,7,1729 each have100 complete
belief grids,2,400 valid replies and32/32 controls, no errors/truncation. Seed1729's
independent all-row metadata/scoring/input/seed audit passed; timed inference11.42min,
2,101tok/s natural. All three completed reference chains and audits copied Mac.
Worker/log `/workspace/sft-drift-ops/vllm_repeats_v1.{sh,log}` terminal; no restart resume.
Baseline sampling report under seed1729 `baseline_variability_v1`:median per-belief
three-seed range4.17pp,p95=16.67pp,max29.17pp; pairwise mean absolute drift3.21–3.71pp.
Only3seeds, descriptive noise, not calibrated intervals or SFT effects.

Semantic memoryv1 FAILED recall:BASE0/20, reloaded0/20, despite loss3.528→.0711 and
all8 update/reload checks passing,48.64s training. Full outputs/checkpoints copied Mac.
Capacity worker v1 exited at missing-success precondition; capacity stage never started.
Fresh `ethics_sft_memorization_v2` also FAILED exact chat recall0/20 after BASE0/20,
with broader rank16/all-projection adapter and distinct names,200steps. Several correct
codes occur in longer replies; others wrong/truncated. Do not reinterpret as a pass.
Full artifacts/checkpoints copied Mac. Both capacity workers gated out; capacity stage
`ethics_sft_training_capacity_v1` has never started. No live training.
Next CUDA action is a separate preserved diagnostic `ethics_gpu_document_memory_diagnostic_v1`:
Supervisor`sft-drift-memory-diagnostic-v1` is RUNNING, PID17011 at last check,
`/workspace/sft-drift-ops/document_memory_diagnostic_v1.{sh,log}`. No restart resume.
Same BASE/adapter, original chat with64cap, completion-style chat, native4-token document
continuation. Content/format metrics separate; failed strict gates remain unchanged.
Capacity inputs remain prepared/unused:32draws→40chunks/32microbatches/8steps,B2/G4,
length1024,rank16 all seven projections. Must pass an appropriate declared memorization
check and update/reload gate before treatment; no lower threshold or belief-outcome tuning.

Candidatev2 is assembled,20,000 records /54 hash-matched corrections /9,802,442 raw
Qwen tokens. New v7 repairs one missing appeal safeguard found in ten complete hiring
texts; nine others no clear serious defect. v6 recheck passed low serious scores; its
review label is forced by subject policy, not a high defect score. No source filtering.

Rubricv5 adds one omission predicate to identical original13 v4 questions (hash tested).
Development canary flags missing review=1, corrected=0, intact negative=0. Follow-up1260
completed1260/1260: original1,180 queue +80 fresh blind records, cost$0.5346221, no errors/refusals. All80 complete texts read
with briefs and judgments frozen before production inference:74 no-clear,2 confirmed
scope defects,4 borderlines. Blind ledger `ethics_sft_scope_blind_review_v1` annotations
SHA2880be31270fe37217d24c8056290c6864d032286a9b540d53b12114d94561a6.
No individual production model scores seen at judgment time. Joined audit shows both
clear defects scored.03 and were missed; one model flag was agent-no-clear. This is
not semantic clearance. New full-text adjudication packet140flags now fully read
(includes one already in blind80):90scope defects,2internal-reasoning defects,27no-clear,
21borderlines. All92confirmed source IDs need repairs;none was a prior repaired row; `ethics_sft_scope_followup_review_v1`. Three explicit repairs
(v8) fully reread and rechecked low, cost$0.0012697; not yet assembled candidatev3.
Two defect families: stipulated benefit weakened into uncertainty; excluded conduct
misstated as permitted. Repair and targeted family checks still required.
QA log `/tmp/sft-drift-scope-followup-assess.log`; completed immutable. No QA running.

New even_eos budgets keep first content/EOS and spread remaining targets, avoiding
position-dependent EOS masking. Optional one_pass loader covers every chunk once with
matched optimizer counts under a bounded batch size; default behavior unchanged. Both
still need CUDA capacity qualification. Focused40passed; full1013passed/five skipped after newest dose helpers/scripts.
Pooled dose helpers and manifest assembly script added;40 focused checks passed.
Training arm manifests/dose/analysis are not frozen and no treatment has started.

Exact repair evidence entry (from belief-transfer/; all140 have been read):
```sh
uv run --no-sync python data/results/ethical_stance_sft/ethics_sft_scope_followup_review_v1/read_packet.py 0 8
```

Prior reference worker monitor (terminal):
```sh
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-vllm-repeats-v1; tail -n 12 /workspace/sft-drift-ops/vllm_repeats_v1.log'
```

Next: diagnose toy native continuation versus chat retrieval/format, author/review/recheck92
confirmed flagged-text repairs plus targeted family checks and fresh confirmation, declare matched dose/step and checkpoint rules,
then train all-positive/all-negative/complementary mixes/off-topic/C4-only and evaluate
all100 beliefs on every designated checkpoint. Preserve at completed work boundaries.

## Completed: fresh full GPU BASE, seed 42

`ethics_gpu_vllm_base_v1` completed successfully on the existing RTX3090. All100
belief grids complete: **2,400/2,400 replies**, strict format/extraction100%, no errors,
no truncation; fresh factual/null controls **32/32 correct**, zero null flips. Supervisor
`sft-drift-vllm-base-v1` exited; no active GPU jobs. No treatment training or rental.

Timed inference incl controls/engine load **686.783s (11.45min)**; natural phase620.163s,
1,288,411 output tokens /2,077.54tok/s. Reply lengths min186, median483, p95=991,
max2,459. Overall Stance Agreement86.46% (order87.58%, wording87.88%, negation83.92%);
193/1,200 contradictory negation pairs retained. These are single-seed descriptive
outcomes, not confidence, SFT effects, forgetting or a sampling-noise estimate.

Exact execution was declared before launch (f033137): frozen bank/probability/thinking/
4,096cap, pinned Qwen3-4B revision1cfa9a7, no adapter, isolated vLLM0.19.0 /Torch2.10.0 /
Transformers4.57.6, per-request RNG, submissions256/max64 active. Completed audit
re-extracted every valid answer, recomputed all scores/controls, checked all2,432 input
IDs/prompt hashes against the tokenizer audit, output IDs/counts, seeds and runtime
identity. Every audit check passed; source/input hashes and audit script retained.

All raw/derived files, configs, worker log/script/Supervisor definition copied to Mac:
`belief-transfer/data/results/ethical_pilot/ethics_gpu_vllm_base_v1/`.
Readable plots/tables: `completion_audit_v1/review/report.md`; audit:`completion_audit_v1/audit.md`.
Historical boundary_copy_v1 records512 replies; first private boundary backup verified
at main revision5b14e0cd (code39e38ad). Final snapshot verification is recorded in
`belief-transfer/data/.handoff-receipt.json`. Only the Mac writes private snapshots.
Environment/model-cache binaries remain GPU-local; setup, versions and revision saved.

Next: create fresh matched qualification/BASE configurations for predeclared sampling
seeds7 and1729 to estimate variability, then complete outstanding scope dispositions,
CUDA semantic memorization and freeze treatment inputs/dose/analysis before training.
Do not rerun completed IDs. Original HF `ethics_gpu_base_v1` stays partial360/2,400 and
separate; Mac MLX is also separate. No inference/decoder tuning on belief outcomes.

Exact next read command, from `belief-transfer/`:

```sh
cat VAST_SFT_HANDOFF.md
```

## Completed throughput optimization

Qualified vLLM achieved2,908tok/s on the matched neutral short probe (old eager107).
All2,432 frozen rendered inputs matched across environments. Adaptercanaryv3 passed;
capacityv2 passed64×4,096 outputs after256input,262,144 tokens in271.807s (964.45tok/s).
Peak device use22,287/24,576MiB, headroom2,289MiB. Native full-cache compilation did
not justify selection. Main training environment/pins unchanged; no hardware rented.
Failed startupcanaryv1, short-capcanaryv2 and blocked-before-startcapacityv1 are retained
at their named results paths; see `changelog/2026-10-19-inference-throughput.md`.
`belief-transfer/GPU_INFERENCE_SPEED.md` now includes the measured full-bank runtime.

## Experiment preparation — training pending

User authorized beginning the experiment sequence. Calibration completed. Batch sixteen
failed the full-capacity test; fresh `ethics_gpu_capacity_v3` passed eight 4,096-token
outputs (823 input tokens), peak allocated 13,951,462,400 bytes. Technical document
smoke v2 completed two optimizer steps with finite loss, changed adapter, unchanged
base and saved checkpoints, but failed reload verification (max logit error .375).
Its failed artifacts/checkpoints are retained. Accelerate's training autocast wrapper
was removed before the inference comparison in fresh smoke v3: **passed**, all eight
checks true, exact adapter roundtrip and zero reload logit error. Same initial adapter,
input and training settings; CUDA updates differ slightly between runs (not bitwise
reproducible training). Both v3 optimizer checkpoints and final adapter are saved.
Original HF development (56/56) and held-out validation (224/224) both passed32/32
known controls. Original full BASE is stopped and partial; throughput replacement and
current process state are above. See `changelog/2026-10-19-gpu-experiment-start.md`.
Sampling reference seeds42,7,1729 were declared in `belief-transfer/GPU_BASE_PROTOCOL.md`.
No ethical support outcome was used to select inference settings. Scope adjudication,
semantic memorization test and frozen treatment plan remain pending.

Standalone `document_sft` is now implemented, with explicit loss labels, per-document
continuation, actual training-token journals and CUDA update/reload checks. Corrected live smoke v3
passed on CUDA (reload error zero, exact adapter roundtrip). The v1 input preparation used abbreviated source-file hashes; preserve
it as a void preparation, never trained. v2 records and verifies full SHA-256 hashes.
See `belief-transfer/DOCUMENT_SFT.md`. Focused checks: 161 passed, then 92 passed after
provenance changes. Full regression after preserving historical unset-field serialization:
**971 passed, five skipped**. Historical fingerprint `8834d5aca78e` remains unchanged.
All 2,432 rendered BASE/control inputs are 80–186 tokens; stress width is 823.

The original driver PID 4240 was held only at its stage boundary during the schema
compatibility fix; its capacity child continued, then failed. The driver was released
and exited under `set -e`. No paused process remains. Failed v2 retains its request,
full traceback and `FAILED.md`; do not restart it or reuse its measurement ID.

Separate scope adjudication v1 read eight pending full documents across four risk
families: seven no-clear-serious-defect judgments, one necessity/distress scope error.
Repair overlay `ethics_sft_decision_repairs_v6` preserves the full revision (465 tokens),
not yet applied to a complete candidate bank or model-rechecked. Original queue stays
unchanged; explicit reconciliation leaves 1,098 unreviewed entries. No clearance claim.

## Completed — SSH-controlled Vast.ai setup

Existing box `38.49.42.46:58689`, RTX 3090 / 24,576 MiB, ephemeral workspace.
Codex stays in the local chat; no remote agent harness. Checkout:
`/workspace/sft-drift`, environment in `belief-transfer/.venv`.
Setup worker `sft-drift-setup` exited successfully; run `ethics_gpu_setup_v1`.
Locked install completed; both private stores restored and verified; **99 setup
regressions passed**. Qwen3-4B is cached at revision
`1cfa9a7208912126459214e8b04321603b3df60c`. CUDA 12.8 / BF16 canary passed:
all parameters on GPU, response `READY`, peak allocated 8,057,951,744 bytes.
Setup-stage status only: later calibration and technical training are recorded above.

Exact monitor command from the Mac:

```sh
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-setup; tail -n 30 /workspace/sft-drift-ops/setup_v1.log'
```

Completed artifacts, exact config, canary tokens, full log (including the stopped
initial install), Supervisor definition and hardware evidence were copied back to
the registered results directory on the Mac. Do not restart a completed canary.
Code/notes are pushed and private snapshot success must be checked in
`belief-transfer/data/.handoff-receipt.json`. Environment and model-cache binaries
stay on the box; their versions/revision and setup procedure are preserved.
See `belief-transfer/SSH_GPU_OPERATIONS.md` and
`changelog/2026-10-19-ssh-gpu-setup.md`.

## Next experiment steps — GPU qualification and document SFT

The existing GPU box is ready for CUDA calibration/qualification, BASE and technical smoke
checks. The new `stage=document_sft` now implements standalone text and actual prefix
loss masking; its CUDA smoke/update/reload check passed as v3. Legacy `stage=sft`
remains chat-based. Resolve scope-review dispositions and freeze arm/dose/training/
analysis before treatments.
No rental, rescreen or training was started in the earlier readiness work block;
the currently authorized setup is recorded above.

New handoff: `belief-transfer/VAST_SFT_HANDOFF.md` has verified existing entry points,
implementation requirements and a prompt to paste into the GPU session. SETUP.md's
stale “no dataset yet” paragraph is corrected. Decisions lessons and future changes
are in `belief-transfer/STANCE_DECISION_QA.md`: subject-routed questions, direct scope
predicates, untouched blind audits, separate dispositions, retained refusal/cache/retry
semantics. These recommendations do not change completed rubric v4 or rerun it.

## Pooled Decisions score plots

Saved overall and 13-check histograms under the completed screen's
`score_histograms_v1/` results subdirectory (PNG/SVG, exact bins/statistics, source hash).
All subjects/positions pooled, original screen before repairs, no new API calls.
Composite = maximum of ten serious checks; 19,995 complete rows, five refusals excluded.
Median .01, p95 .08; 428 at least .2 and 134 at least .7. Logarithmic count axes.
Individual criteria retain available valid scores. These are model judgments, not
calibrated defect probabilities. The next GPU handoff and readiness status above remain.

## Completed work: full Decisions screen and bounded manual repairs

User authorized screening all 20,000 synthetic documents and manual corrections.
**`ethics_sft_decision_qa_corpus_v3` completed 20,000/20,000** with frozen rubric v4,
13 questions, gpt-6-luna. No active generation/training process or GPU rental.
Actual returned-usage cost: **$7.6719303** full pass; **$7.8335481** including development
and 52 repair rechecks. Zero HTTP request errors/failed rows; uncertain cost zero.
Five refused questions remain explicit in raw results, with separate full-text agent reviews.

The agent read **242 unique full source documents**, including the prior 164, a fresh
flag-blind 20, all **34 high stance/contradiction flags**, targeted scope examples and
all five refused-question documents. Also read all 52 complete revisions. This is NOT
manual review of all 20,000. All 34 high stance flags have traceable corrections.

New candidate version **`ethics_sft_candidate_repairs_v1`** retains all 20,000 IDs,
100 documents per subject/position, with **52 manual replacements** from
`ethics_sft_decision_repairs_v1`–`v5`. Their model rechecks are separate QA runs with
`decision_qa_repairs_v1`–`v5` in the ID. All replacements are 422–562 Qwen tokens.
Candidate version: **9,802,428 tokens**, 19,600/20,000 within 400–600, no exact duplicate
final texts. Original v5 corpus is unchanged. Later repairs share disclosed scaffolding;
these are corrections, not new independent ideas. No automatic training approval.

Detector limits: development 164 was reused for tuning (12/14 serious labels caught).
The fresh flag-blind 20 found one clear scope change, **missed** by Decisions, one
borderline, 18 without clear serious defects. No retuning on that check. Low flags are
not semantic clearance. Original routes: 134 high, 594 review, 52 style, 19,215 low,
five unresolved; these include 408 original mandatory reviews, not confirmed defects.
Follow-up policy adds both hiring subjects to the two psychology families: 800 risk-family
rows. Disposition queue: **1,106 pending**, 52 repaired, 14 agent-no-clear-serious-defect,
three borderline, five provider-unresolved/agent-reviewed. Do not silently filter this queue.
One repaired psychology document retains a .6 model flag with explicit agent disagreement.

Exact next command, from `belief-transfer/`:

```sh
cat VAST_SFT_HANDOFF.md
```

For the prepared box, read that same file remotely with:

```sh
ssh -p 58689 root@38.49.42.46 'cat /workspace/sft-drift/belief-transfer/VAST_SFT_HANDOFF.md'
```

Follow that handoff for GPU setup; before treatment training prioritize scope adjudication using `disposition_queue.md` in the same folder.
Corpus expansion/training remains a subsequent experiment plan. Qualify CUDA BASE,
variability, tiny memorization/update/reload checks before any SFT. Evaluate all 100
beliefs on every future model/checkpoint. No Mac training or unauthorized rental.

## Bank, baseline and provenance

Original **`ethics_sft_pooled_corpus_v5`**: 20,000 synthetic candidates across 90 ethical
and ten fresh off-topic training claims ×100 per position; 9,800,659 Qwen tokens.
The ten control claims are distinct from the frozen evaluation preferences. C4:
20,634 unique full rows /9,774,947 tokens, pinned revision
`1588ec454efa1a09f29cd18ddd04fe05fc8653a2`, seed 42, shuffle buffer 1,024.
Generation cost $25.89367392 cumulative, including v4 $8.59085765; do not add v4 again.
Historical failed-attempt uncertainty $0.08217 remains separate from this QA's zero.
Original stopped v4 and completed v5 lineage remain preserved.

Verified **2,101 source files and 161 frozen instrument files unchanged** after screening.
Frozen bank: `ethical_pilot/ethics_100_bank_v3`. Mac MLX BASE
`ethics_100_stance_qwen_v2`: 2,400 replies, 32/32 controls, 87.3% equal-check agreement,
186/1,200 contradictory pairs. CUDA BASE seed42 is complete; no treatment adapter, only technical smoke adapters.

Decisions support is opt-in; original Responses pricing/cache identity and retry defaults
remain intact. New QA uses durable per-request journals, bounded transient retries,
explicit resume and completed-run overwrite refusal. All live runs are finished.
Validation: full suite **938 passed/five skipped** before production, final targeted
**56 passed/one skipped**, including three candidate-assembly lineage/refusal tests.
Tests ran separately from live stages and artifact writes.

## Preservation and fresh-box entry

Code/configs/notes belong in Git; exact requests, raw responses, authored edits, before/after
texts, complete candidate version and queues are declared in the main private store and
separate private corpus store. Check the final commit/revisions and success in ignored
`belief-transfer/data/.handoff-receipt.json`; Git notes are not a snapshot receipt.
Final work-block procedure: commit/push, then from `belief-transfer/`:

```sh
uv run --no-sync python scripts/handoff.py save
```

Fresh box: SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md, then:

```sh
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```

Details: `changelog/2026-10-19-decisions-qa.md`, `belief-transfer/STANCE_DECISION_QA.md`,
and the full review report above. Do not rerun completed screening/repair IDs.
