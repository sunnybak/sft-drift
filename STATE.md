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
- `reviewed_edits.json`+MD and `final_full_text_reviews.jsonl`+MD: all92 final revisions
  read in full, including rereads after residual corrections; exact hashes verified.
  Earlier draft files/24-review ledger retained unchanged for lineage.
- Materialized separate overlay `ethics_sft_decision_repairs_v9`:92 replacements,
  87within400–600tokens,range355–606. No candidatev3 assembly yet.
- `ethics_sft_decision_qa_repairs_v9` completed92/92,$0.0390069,no errors/refusals.
  Seven critical>=.2 rows reread fully: five no-clear-defect disagreements, two ambiguous
  concealment referents pending disposition (`debrief__0059__negative`,
  `debrief__0097__positive`). Review report/JSONL+MD alongside raw QA.
 81mandatory psychology labels are separate from actual score failures.
- `family_search_v1/direct_full_text_reviews.jsonl`+MD: all37direct-cue source candidates
  fully read against briefs:36clear scope defects,1false positive. Targeted selection,
  not prevalence.35psychology rule-assisted drafts saved separately UNREVIEWED;
  payroll-positive draft pending. No v10overlay; full revised-text review required.
- Broad365 effect-uncertainty lexical matches remain search candidates, likely many
  valid caveats. Assess relevant families and take fresh confirmation before final
  data-use policy; do not demand that every lexical match is a defect or silently filter.

```sh
uv run --no-sync python scripts/handoff.py save --recover-staged
```

The new blind80 and flagged140 include219distinct texts in this work block. Earlier
242source reviews are development/targeted evidence; do not add counts without ID audit.
Original Decisionsv4 full20k screen remains immutable. LatestQA total including these
follow-ups is not a population defect rate. Original provider refusals remain explicit.

## Before treatments

Investigate the preserved native-vs-chat memory gap without relabeling failed gates;
finish36family repairs, dispose2ambiguous revisions, and fresh confirmation/data-use policy. Assemble complete candidatev3 only after
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
The newer8a4805b save FAILED HTTP408 after staging additions at
`c1313a8b5945e5391d593468d82d3d0bcc917da0`; published manifest/receipt remain old.
New explicit staged-recovery support verifies unchanged published manifest/all prior
remote blobs and local hashes of every added file. Allows only Hub-appended exact-path
LFS rules for matching new LFS additions; broad/old-path rule changes are refused.
Default divergence refusal remains.
Compact JSON and staging all additions separately reduce final request size. Recovery/import/corpus tests45passed/1.41s. Live
recovery execution pending; do not claim the newest backup verified. Authoritative receipt is
`belief-transfer/data/.handoff-receipt.json`, not a prose assertion.

Only Mac writes private snapshots. Preserve completed GPU results/checkpoints at safe
boundaries; current workers do not survive box destruction and do not restart-resume.
Do not destroy the box while new outputs remain GPU-only. Final work-block command:

```sh
uv run --no-sync python scripts/handoff.py save
```

Fresh box: SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md; locked install, restore/verify
private handoff. Do not restart historical completed IDs or recover an archived queue.
