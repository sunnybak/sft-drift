# Current state — 2026-10-20

## Active goal: complete the pooled SFT experiment

User authorized baseline repeats, preserved memorization checks, content-review policy,
a frozen six-arm comparison, SFT/checkpoint evaluations and analysis. Goal remains active.
**No treatment model has been trained.** Do not declare completion for preparation alone.
Details: `changelog/2026-10-19-pooled-study-execution.md`; older source history is in Git.

## GPU now

Existing Vast RTX3090: `38.49.42.46:58689`, checkout `/workspace/sft-drift/belief-transfer`.
Supervisor **`sft-drift-training-checks-v1` EXITED**, confirmed terminal. Capacityv2
passed all10 checks; memoryv3 failed strict chat recall. No GPU process from this worker
is running and no treatment has started. Worker/script/log:
`/workspace/sft-drift-ops/training_checks_v1.{sh,log}`. No autorestart or stage restart-resume.
Newest results/checkpoints copied with `rsync -az`; all68remote files matched local
SHA256/bytes (1,481,895,103bytes). Those68files are in the verified private snapshot below; newer diagnostic outputs need the next snapshot.
Local transfer log:
`/tmp/sft-drift-training-checks-copy.log`.

- **Memoryv1/v2 failed** strict exact chat recall: BASE0/20 and reloaded0/20. Loss fell
  and all8 update/reload checks passed. Full failures/checkpoints are copied Mac.
- Separate `ethics_gpu_document_memory_diagnostic_v1` completed: BASE0/20 all formats;
  reloaded native-document continuation20/20, original64-cap chat correct code8/20 but
  exact0/20, completion-chat exact3/20. Do not reinterpret original failed gates as passed.
- Memoryv3 uses20 distinct names in plain lookup-reference documents with two training
  question forms and code-only convention; original evaluation query is absent from
  training text. Same exact>=.9/BASE<=.1 gate,200steps/rank16all projections: BASE0/20,
  reloaded1/20. All8 update/reload checks passed; strict semantic gate remains FAILED.
  Do not silently replace it with native recall or claim ethical effectiveness.
- Capacityv1 engineering check passed all10checks incl exact one-pass coverage,8steps /
  32microbatches /21,314loss targets /37.561s=567.45targets/s. Peak allocated12.73GB,
  reserved17.55GB. Mixed short/wide batches: not a steady-state full-study ETA.
- Rank16/all-projection `ethics_gpu_training_adapter_canary_v1` passed all4vLLM checks.
  Capacityv1 checkpoint tree (910MB) and diagnostic/canary raw artifacts copied Mac.
- Capacityv2 tests B4/G2/8steps on64 full1024-token chunks,65,152loss targets, repeated
  neutral source. It proceeds independently of the strict memory gate. No ethical inputs. Completed all10checks,1,431.35loss targets/s,45.518s,
  peak allocated16.856GB/reserved19.080GB. Technical stress throughput only.

CUDA main environment is unchanged. Isolated vLLM environment remains qualified;
see `GPU_INFERENCE_SPEED.md`, `SSH_GPU_OPERATIONS.md`, `VAST_SFT_HANDOFF.md`.
Qwen3-4B revision `1cfa9a7208912126459214e8b04321603b3df60c`; no new GPU rental.

## CUDA references complete

Seeds42,7,1729 each completed100belief grids /2,400valid replies /32correct controls,
no errors or truncation. Same frozen bank/decoder and vLLM backend. All independent
all-row input/seed/extraction/scoring/metadata audits passed. IDs:
`ethics_gpu_vllm_base_v1`, `ethics_gpu_vllm_base_seed7_v1`,
`ethics_gpu_vllm_base_seed1729_v1`, with matched dev/val chains. All copied Mac.
Timed inference11.42–11.51min, about2,100natural output tokens/s.

Seed1729 `baseline_variability_v1/`: median within-belief three-seed Stance Score
range4.17pp,p95=16.67pp,max29.17pp; pairwise mean absolute changes3.21–3.71pp.
Only3seeds: descriptive noise, no calibrated intervals or SFT/retention claims.
Original HF `ethics_gpu_base_v1` remains stopped/partial360/2,400; do not merge or resume.
Mac MLX BASE is separate. Natural agreement is an outcome, never a qualification gate.

## Dataset review and repairs

Original `ethics_sft_pooled_corpus_v5`:20,000documents,100per position/subject,90ethical
plus10fresh training preferences. Frozen10evaluation preferences are never trained.
C4:20,634unique pinned full rows. Candidatev2 `ethics_sft_candidate_repairs_v2` retains
all20,000IDs with54hash-matched corrections,9,802,442raw Qwen tokens. SHA:
`cc461a840e3c5cdeae96f84edf96adf723e45d1fe48bd34dcbc20ae2c47a4dac`.
Fully read/rechecked overlayv8 adds3corrections but is not yet assembled into candidatev3.
No source filtering, no automatic training-ready designation.

Rubricv5 adds one omission predicate to unchanged13v4questions. Development canary
correctly distinguished omitted appeal safeguard/repaired/intact; not held-out accuracy.
Follow-up `ethics_sft_scope_followup_v1` completed1260/1260,$0.5346221,no refusals/errors.
Its80fresh blind complete texts were read with briefs and judgments hash-frozen before
production scores:74no-clear,2clear scope defects,4borderlines. Both clear defects scored
.03 and were missed. Sole serious blind model flag was agent-no-clear. Low flags do not
clear semantics. See `SCOPE_FOLLOWUP_PROTOCOL.md`; no detector retuning on that blind set.

All140threshold-flagged texts then read in full:90scope defects,2internal-reasoning
failures,27no-clear,21borderlines.81confirmed defects involve psychology necessity/type
of deception. All92repair IDs are previously unmodified source rows. Review artifacts:
`data/results/ethical_stance_sft/ethics_sft_scope_followup_review_v1/`.

- `annotations.jsonl`+MD: complete140judgments; `repair_queue.jsonl`+MD:92confirmed.
- Consolidated `final_consolidated_edits.json`+MD and
  `final_consolidated_reviews.jsonl`+MD:132final revisions read in full with hash ledger.
  Includes92v9 repairs (two clarified),35additional psychology repairs,1salary-policy
  repair, and4broad-family corrections/clarifications. Earlier drafts/ledgers retained.
- `ethics_sft_decision_repairs_v10`:132replacements,123within400–600tokens,355–629range.
  Recheck `ethics_sft_decision_qa_repairs_v10` completed132/132,$0.0561471,no failures.
  Five critical>=.2 flags are unchanged v9 texts with hash-matched full-reread/no-clear
  judgments; disagreements explicit. No serious flags on new corrections/clarifications;
  that is not semantic clearance. v9 remains preserved (92calls,$0.0390069).
- Candidatev3 `ethics_sft_candidate_repairs_v3` COMPLETE:20,000IDs,100per position/subject,
  189hash-matched replacements,9,802,700raw Qwen tokens. SHA:
  `4b494add47a2edd3df58261b0f66022b69bf6f0cf745b9682ddb57a6b8f15a09`.
  Assembles v1–v8 plus consolidatedv10; v9 deliberately omitted from assembly to avoid
  duplicate replacements. Source/earlier versions unchanged; no rows dropped.
- Direct family search:37complete sources read,36confirmed defects/1false positive;
  all36corrected above. Broad diagnostic:seed20261020,two per subject among365matches,
  20complete sources read:16no-clear,2clear,2certainty borderlines; allfour clarified.
  Targeted selections cannot estimate corpus defect prevalence. Other345lexical matches
  are not individually adjudicated; no assertion that they are all defective or clear.
- Fresh `ethics_sft_scope_confirmation_v1`:ALL96complete texts read without scores,
  then judgments frozen (SHA47c74f73709d681a5e88d2e15f1c1f12b4525975783ded433fc304c4cbdb237c).
  Category80:73no-clear,2clear scope,5borderline. Separate psychology16:13no-clear,
  2clear,1borderline. No clear position reversals. All4clear cases scored below0.2in
  prior Decisions outputs; exact comparison joined only after judgment freeze. This
  is agent assessment of candidatev3 before repairs; do not retrospectively call it
  passed or draw repeated confirmation samples to obtain a pass.
- Four clear and six borderline texts now have traceable, fully reread corrections/clarifications
  in separate repairv11. QA10/10,$0.004233,no errors,critical risks0–.07; lengths395–596,
  9/10in400–600. Not yet assembled into candidatev4. Input-audit cue closure read20more
  complete sources:17no-clear,1clear omission,2notice borderlines. Three additional
  final corrections fully read/hash-ledgered but not yet materialized.
  Post-confirmation lexical repair search:180candidate sources (43specific necessity,
  1missing distress,21input-audit absence,115broad protection/uncertainty cues), not
  validated detection or180confirmed defects. See confirmation report and JSONL/MD.
- Registered/prepared `ethics_gpu_document_recognition_v1`:new diagnostic only, fixed
  memoryv2adapter versus BASE.132prompts/model:80balanced true/distractor code claims
  in both definition orders,32unchanged factual controls,20original direct-code queries.
  Qualified thinking decoder; original greedy16memorization gates remain FAILED.
  Protocol/bank hashes frozen before calls;42focused tests passed. Worker EXITED.
  Results: BASE40/80recognition,32/32controls; adapter33/80recognition,27/32controls,
  controlstrict90.625%,nullflip31.25%,nonnormal control stops; directcode2/20exact.
  Support criterion FAILED.264raw responses/MD,metadata/log copied Mac; no treatment clearance.
- Next preregistered diagnostic ethics_gpu_document_adapter_parity_v1 replays40saved
  native-document inputs from the successful HF recall run through vLLM,greedy4tokens/seed0.
  Exact HF/vLLM text+token parity and adapter20/20recall required for this narrow check.
  All old chat/control failures remain failed.53focused tests pass. Launch pending.

```sh
# Next prepared technical diagnostic; isolated qualified vLLM environment on GPU.
/workspace/sft-drift-vllm/.venv/bin/python scripts/probe_document_adapter_parity.py run --run-id ethics_gpu_document_adapter_parity_v1
```

The new blind80 and flagged140 include219distinct texts in this work block. Earlier
242source reviews are development/targeted evidence; do not add counts without ID audit.
Original Decisionsv4 full20k screen remains immutable. LatestQA total including these
follow-ups is not a population defect rate. Original provider refusals remain explicit.

## Before treatments

Investigate the preserved native-vs-chat memory gap without relabeling failed gates;
verify native adapter backend parity; then representative mixed-document calibration if warranted.
Ten confirmation texts are corrected; finish targeted families and explicit data-use policy. Candidatev3 is assembled; retain all raw flags and remaining uncertainty. Every JSONL needs its derived Markdown view.

Pooled dose helpers and `scripts/prepare_pooled_dose.py` exist, not yet executed:
paired opposite documents share min available loss targets; even_eos preserves first
content/EOS and spreads remaining targets. Four ethical arms each select9,000synthetics
plus same9,000C4background. Off-topic10topics×100unique texts require explicit repeats
for matched exposure; C4-only replaces synthetic exposure from disjoint C4reserve.
Exact totals/chunks/steps still to be measured. No training manifests/analysis are frozen.

Freeze hypotheses/falsifier, six contrasts/controls, training settings/seeds, exact dose,
checkpoint schedule and uncertainty analysis before treatments. Then fresh all-positive,
all-negative, MixedA/complementaryMixedB, off-topic and C4-only SFT; evaluate all100beliefs
on every designated checkpoint with its own qualification, then report complete matrices.
No tuning on treatment belief outcomes; failed controls/missing replies explicit.

Latest full regression **1013passed/5skipped**; subsequent memory-reference preparation
changes have **41focused tests passed**. Tests run separately from live local artifact
writes; do not copy live outputs or run local generation during the result-preservation
suite. Source/config defaults and frozen instrument files remain protected by handoff.

## Preservation

Most recent verified snapshot is code765e24d, main
dec103772442ea51b1f87ff524f17d8374e4c49f, corpus
c6d853fd96459efb227388d7cd4f16751232917b;1,876main files/3,643,980,066bytes.
Includes candidatev3 and frozen selection. Later confirmation/diagnostic work needs
its next checkpoint. Earlier recovery snapshot VERIFIED:
main83c6035edc58e6bd1d0460b9db90a96664fefbcf,
corpus844c1aef8edbf3ee551edcfe82a6af2842e6bfcf;
1,830main files/3,634,611,597bytes. Includes all newest GPU weights/failures.
Later v10/candidatev3/confirmation work requires the next snapshot after this note.
The previous8a4805b save failed408; no false success receipt was written. Recovery
verified unchanged prior blobs and exact staged additions, allowing only Hub-appended
new exact-path LFS rules. Default divergence refusal remains.45preservation/import/
corpus tests passed/1.41s. Main manifest uses compact JSON; additions stage separately.
Authoritative receipt: `belief-transfer/data/.handoff-receipt.json`.

Only Mac writes private snapshots. Preserve completed GPU results/checkpoints at safe
boundaries; current workers do not survive box destruction and do not restart-resume.
Do not destroy the box while new outputs remain GPU-only. Final work-block command:

```sh
uv run --no-sync python scripts/handoff.py save
```

Fresh box: SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md; locked install, restore/verify
private handoff. Do not restart historical completed IDs or recover an archived queue.
