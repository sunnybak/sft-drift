# Current state — 2026-10-19

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
SHA256/bytes (1,481,895,103bytes). Private snapshot still required before box destruction.
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
- Fresh `ethics_sft_scope_confirmation_v1` selection/protocol frozen BEFORE full-text
  reading:80category-balanced texts +16psychology-family texts, excluding prior review
  and repaired IDs. No model scores used;0/96read. Selection SHA:
  `820f6d5763bc319ad9219e036834495850c8215b1074087f9f3c84b8ad380ccb`.
  Read all96with briefs, freeze judgments before optional score comparison; report
  strata separately. No pass-hunting or retuning a detector on this confirmation set.

```sh
uv run --no-sync python data/results/ethical_stance_sft/ethics_sft_scope_confirmation_v1/read_packet.py 0 6
```

The new blind80 and flagged140 include219distinct texts in this work block. Earlier
242source reviews are development/targeted evidence; do not add counts without ID audit.
Original Decisionsv4 full20k screen remains immutable. LatestQA total including these
follow-ups is not a population defect rate. Original provider refusals remain explicit.

## Before treatments

Investigate the preserved native-vs-chat memory gap without relabeling failed gates;
complete fresh96confirmation and explicit data-use policy. Candidatev3 is assembled; retain all raw flags and remaining uncertainty. Every JSONL needs its derived Markdown view.

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

Git62aa324 pushed; recovery snapshot VERIFIED:
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
