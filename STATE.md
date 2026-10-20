# Current state — 2026-10-19

## Active goal: complete the pooled SFT experiment

User authorized baseline repeats, preserved memorization checks, content-review policy,
a frozen six-arm comparison, SFT/checkpoint evaluations and analysis. Goal remains active.
**No treatment model has been trained.** Do not declare completion for preparation alone.
Details: `changelog/2026-10-19-pooled-study-execution.md`; older source history is in Git.

## GPU now

Existing Vast RTX3090: `38.49.42.46:58689`, checkout `/workspace/sft-drift/belief-transfer`.
Supervisor **`sft-drift-training-checks-v1` RUNNING**, PID18066 at last check. Finite worker
runs `ethics_sft_training_capacity_v2`, then independent `ethics_sft_memorization_v3`.
No autorestart or stage restart-resume. Worker/script/log:
`/workspace/sft-drift-ops/training_checks_v1.{sh,log}`. Script/config copies are in both
registered generated-input roots on Mac. Inspect actual terminal results before acting.

```sh
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-training-checks-v1; tail -c 1600 /workspace/sft-drift-ops/training_checks_v1.log'
```

- **Memoryv1/v2 failed** strict exact chat recall: BASE0/20 and reloaded0/20. Loss fell
  and all8 update/reload checks passed. Full failures/checkpoints are copied Mac.
- Separate `ethics_gpu_document_memory_diagnostic_v1` completed: BASE0/20 all formats;
  reloaded native-document continuation20/20, original64-cap chat correct code8/20 but
  exact0/20, completion-chat exact3/20. Do not reinterpret original failed gates as passed.
- Memoryv3 uses20 distinct names in plain lookup-reference documents with two training
  question forms and code-only convention; original evaluation query is absent from
  training text. Same exact>=.9/BASE<=.1 gate,200steps/rank16all projections. Technical
  check only; does not establish ethical document effectiveness.
- Capacityv1 engineering check passed all10checks incl exact one-pass coverage,8steps /
  32microbatches /21,314loss targets /37.561s=567.45targets/s. Peak allocated12.73GB,
  reserved17.55GB. Mixed short/wide batches: not a steady-state full-study ETA.
- Rank16/all-projection `ethics_gpu_training_adapter_canary_v1` passed all4vLLM checks.
  Capacityv1 checkpoint tree (910MB) and diagnostic/canary raw artifacts copied Mac.
- Capacityv2 tests B4/G2/8steps on64 full1024-token chunks,65,152loss targets, repeated
  neutral source. It proceeds independently of the strict memory gate. No ethical inputs.

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
- `draft_edits_UNREVIEWED.json`+MD:92drafts, separate from candidate bank; **24full revised
  texts hash-approved,68pending**. Rule-assisted drafts had residual errors caught during
  reading; explicit corrections in `draft_residual_patches.json`. No v9overlay yet.
- `draft_full_text_reviews.jsonl`+MD /`draft_status.json`: exact approved text hashes.
  Use portable `read_draft_packet.py`. Reread corrected/unapproved indices10,12,14,19,21,
  25,27,30, then continue32..91. Never rerun draft builders over these manual corrections.
- `family_search_v1/`:37additional direct-cue candidates and365broad effect-uncertainty
  lexical matches. These are search candidates, not defect labels. Broad matches likely
  include many correct caveats. Targeted family checks and fresh confirmation remain;
  do not silently clear or filter them or claim the full bank was manually reviewed.

```sh
uv run --no-sync python data/results/ethical_stance_sft/ethics_sft_scope_followup_review_v1/read_draft_packet.py 10 16
```

The new blind80 and flagged140 include219distinct texts in this work block. Earlier
242source reviews are development/targeted evidence; do not add counts without ID audit.
Original Decisionsv4 full20k screen remains immutable. LatestQA total including these
follow-ups is not a population defect rate. Original provider refusals remain explicit.

## Before treatments

Finish/check technical memory result, full revised-text reviews/rechecks, targeted family
checks and fresh confirmation/data-use policy. Assemble complete candidatev3 only after
explicit overlay application. Every JSONL needs its derived Markdown view.

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

Git source is pushed. Most recent verified private checkpoint before newest draft/GPU
copies: code3481bb8, main revision105646328f9f69b373d19defda27a217d4b6c88f,
corpus revision3a4c5b3e6e73455036a95dccfe99a53d9bc1a5dc;1646files/1,204,459,032bytes.
A newer checkpoint must follow this block; authoritative receipt is
`belief-transfer/data/.handoff-receipt.json`, not a prose assertion.

Only Mac writes private snapshots. Preserve completed GPU results/checkpoints at safe
boundaries; current workers do not survive box destruction and do not restart-resume.
Do not destroy the box while new outputs remain GPU-only. Final work-block command:

```sh
uv run --no-sync python scripts/handoff.py save
```

Fresh box: SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md; locked install, restore/verify
private handoff. Do not restart historical completed IDs or recover an archived queue.
