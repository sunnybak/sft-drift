# Current state — 2026-10-20

## Active objective

Complete the authorized pooled ethical SFT experiment: technical qualification, reviewed
corpus/data-use policy, frozen six-arm dose/settings/analysis/falsifier, fresh training,
all-100-belief checkpoint evaluations and before/after analysis. **No ethical treatment
has been trained.** Preparation alone does not complete this goal. Current details:
`changelog/2026-10-20-confirmation-and-memory-diagnostic.md` and
`changelog/2026-10-19-pooled-study-execution.md`.

## Live GPU jobs

**Neutral format/LR matrix:** canary PASSED (20/20 direct supervised chat recall).
Assistant/highLR completed all11 engineering checks but failed original qualification:
chat recall0/20, controls21/32, strict32/32, null1/16. Raw/lowLR also completed all11
checks: recall0/20, controls31/32, strict32/32, null1/16; qualification FAILED.
Assistant/lowLR completed550steps and validation: recall0/20, controls32/32, strict32/32,
null0/16. All three variants FAILED the full qualification; matrix COMPLETED under finite
Supervisor `sft-drift-registry-format-matrix-v1` (PID22886), sourcec293c82.
No ethical treatment starts. Exact log/status command:

```sh
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-registry-format-matrix-v1; cat /workspace/sft-drift/belief-transfer/data/results/ethical_stance_sft/ethics_sft_registry_format_matrix_v1/progress.json'
```

Post-failure direct-chat diagnostic `ethics_gpu_registry_format_sanity_v1` prepared:
first4 anchors, five original-question/document-request/tag/seen/unseen-prefix conditions,
40 BASE/adapter replies. Script and bank hash-bound;12 focused/import tests passed.
Probe dispatched after matrix;40replies completed, full review pending. Command: `.venv/bin/python scripts/probe_registry_chat.py run`
on GPU. No qualification substitution; longer natural/semantic recall and direct math
are permissible separate development diagnostics, not retroactive changes to frozen gates.
Source/notes/probe committed before dispatch. No restart-resume for started runs.
HighLR all37terminal training/checkpoint files (970,691,759bytes) and17validation files
(310,205bytes) copied Mac and SHA/bytes verified; all20recall and11failed controls read.
Raw-low54files/968,079,258bytes copied and SHA-verified; assistant-low/master copy active.
Separate `ethics_gpu_registry_transfer_development_v1` prepared: all20facts×2questions
plus8direct arithmetic, BASE and3final adapters (192replies), greedy128tokens.
No replacement pass threshold.41focused/probe/import/handoff tests passed.
Next GPU command: `.venv/bin/python scripts/probe_registry_transfer.py run`.
Last verified private snapshot69cd59a8b217ac4f0dc68bf78daa967dcf6b712c atcode7aad4da:
2,169files/5,560,020,983bytes, includes canary and assistant/high midpoint275.
New high terminal outputs and later results require next save. Details:
`changelog/2026-10-20-assistant-document-calibration.md`.

Authorized RTX 3090: `38.49.42.46:58689`; project `/workspace/sft-drift/belief-transfer`.
Qwen3-4B revision `1cfa9a7208912126459214e8b04321603b3df60c`. Main training environment
and isolated vLLM environment unchanged. No additional rental.

- **EXITED** `sft-drift-registry-mixed-calibration-v1`:546/546 steps, all10 engineering
  checks passed;2,162.17s/862.46 loss targets per second. Both checkpoint273/546 and final
  copied Mac, plus terminal results: **37 files/967,673,943 bytes**, all SHA/bytes matched.
  Worker log copied separately. Receipt in its results root: `offbox_copy_verification.json`.
- **EXITED** `sft-drift-registry-mixed-validation-v1`: qualification **FAILED**. BASE:
  lookup0/20,controls32/32,strict1.0. Adapter:lookup0/20,controls22/32,strict24/32.
  All input/model/adapter identities match. Eight replies end on EOS151645 before
  closing the thinking block; two strict final words mishandle negation. All ten failing
  replies read in full; raw outputs preserved, no scoring from reasoning. Null flip0
  only among8/16eligible pairs, so incomplete coverage fails null qualification.
  All104responses/metadata copied;17remote files SHA/bytes verified (394,513bytes).
  Failure analysis/JSONL+MD audit live under `ethics_gpu_registry_mixed_validation_v1`.
- **EXITED** `ethics_gpu_registry_native_diagnostic_v1`: BASE0/20 trained-prefix and
  0/20 unseen-native-prefix recall; adapter20/20 in both. All80new raw replies saved.
  Source/model/adapter binding preserved. This demonstrates native learning and transfer
  to an unseen prose prefix, not chat/control qualification. All old failures unchanged.
  Raw results copied Mac; final copy receipt is alongside the diagnostic outputs.

Logs: `/workspace/sft-drift-ops/registry_mixed_{calibration,validation}_v1.log`.
Both technical workers are terminal; no ethical treatment started. All newest completed
training/validation bytes are off the GPU on Mac and need this block's private snapshot.
Stage has **no restart-resume**; optimizer bytes alone do not establish supported resume.

Calibration `ethics_sft_registry_mixed_calibration_v1`: 20 original arbitrary toy facts
×100 procedural documents, plus first2,000 pinned C4 rows; 1:1 document count. Synthetic
lengths424–456 Qwen tokens. Loss targets882,992 synthetic+981,803 C4=1,864,795;
4,362 chunks, max length1024, B4/G2, one pass, seed42, rank16/alpha32/all7 projections,
lr1e-4, warmup.03, dropout/weight decay0. Checkpoints273/546. Hashed plan
`ab01716940614af748c7d61c48f0d4d986e0b34b2a5cf657d3deb78b4ad1333b` under its generated
root. It uses full operation=train plan verification; bounded operation=memorize guards
were not weakened. Multiple calibration changes are confounded; no causal C4 claim.

Validation `ethics_gpu_registry_mixed_validation_v1`: 104 fresh replies: original20
strict greedy16 lookup questions plus32 unchanged thinking/factual controls per BASE
and final adapter. Requires completed training/all10 technical checks, matched dataset,
revision, steps and exact loss dose; binds final file/config/tensor hashes. Lookup
input IDs/seeds/batches match saved original v2 BASE. Thresholds: BASE lookup<=.1,
adapter>=.9; controls>=.95, strict format1.0, null flip<=.05, normal control stops.
Uses main HF and isolated vLLM environments serially. Protocol/banks frozen before
calls;80 focused tests passed. No ethical outcomes used for calibration selection.

All three earlier technical workers are terminal. The user-requested dataset/training/paper
review is complete: `changelog/2026-10-20-sft-pipeline-review.md`. Recommendation:
retain bank/trainer, add opt-in assistant-document formatting, test a bounded neutral
format×LR comparison, and simplify later dose weighting separately. The review
refines the earlier unexecuted serialization proposal; neither is a runnable plan.
That review is now being implemented in the new block above. Exact plan inspection:

```sh
cat changelog/2026-10-20-assistant-document-calibration.md
```

Do not rerun existing completed IDs or change the frozen decoder/extractor to salvage
choices from reasoning. Lower learning rate or serialization effects are hypotheses,
not established causes. Native recall cannot qualify the failed chat/control setup.

## Established technical evidence

- Memoryv1/v2/v3 failed original strict chat lookup: adapter0/20,0/20,1/20 respectively,
  despite passing8 update/reload checks. IDs `ethics_sft_memorization_v{1,2,3}`.
- `ethics_gpu_document_memory_diagnostic_v1`: memoryv2 native continuation20/20;
  original chat64-cap exact0/20, unambiguous correct code8/20; completion-chat exact3/20.
- `ethics_gpu_document_recognition_v1`: BASE recognition40/80, controls32/32; memoryv2
  recognition33/80, controls27/32, control strict90.625%, null flip31.25%, some nonnormal
  control stops. Direct code2/20 exact. Recognition support **failed**. All264 replies
  and metadata copied;12 remote files SHA/bytes verified (3,264,222 bytes).
- `ethics_gpu_document_adapter_parity_v1`: native HF/vLLM adapter text/token parity20/20
  and code recall20/20; BASE parity19/20, code recall0/20; identity errors0. Strict40/40
  criterion **failed**. Brindova BASEHF1234/vLLM0001, both wrong; cause not established.
  All12 remote files copied/verified (212,117 bytes). Does not qualify chat transfer.
- Capacityv2 B4/G2 passed10 checks:8 steps,65,152 targets/45.518s=1,431.35 targets/s,
  peak16.856GB allocated/19.080GB reserved. Neutral full-width stress, not study ETA.
  Capacityv1 and rank16 vLLM load canary also passed. All prior weights/failures copied
  and privately saved. New calibration above is independently judged; old failures stay.

## CUDA BASE complete

Full vLLM seeds42,7,1729 each:100 belief grids/2,400 valid replies,32/32 controls,
no errors/truncation. Same frozen bank/backend/decoder; all-row provenance/input/seed/
scoring audits passed. IDs `ethics_gpu_vllm_base_v1`, `ethics_gpu_vllm_base_seed7_v1`,
`ethics_gpu_vllm_base_seed1729_v1`, with matched dev/validation chains. All off-box/private.
Timed inference11.42–11.51 minutes, about2,100 natural output tokens/s.
Three-seed within-belief range: median4.17pp,p95=16.67pp,max29.17pp; pairwise mean absolute
changes3.21–3.71pp. Descriptive only, not calibrated intervals. Original HF BASE remains
stopped/partial360/2,400; MLX BASE is separate. No SFT or retention result yet.

## Dataset and review

Original `ethics_sft_pooled_corpus_v5`:20,000 synthetic documents,90 ethical+10 fresh
training preferences,100 per position/subject. Frozen10 evaluation preferences never
trained. C4:20,634 unique full pinned rows, seed42/buffer1024/revision1588ec454efa1a09f29cd18ddd04fe05fc8653a2.
Candidatev3 `ethics_sft_candidate_repairs_v3` retains all20,000 IDs,189 hash-matched
corrections/clarifications,9,802,700 raw Qwen tokens. SHA:
`4b494add47a2edd3df58261b0f66022b69bf6f0cf745b9682ddb57a6b8f15a09`.
It assembles v1–v8+consolidatedv10; v9 is superseded byv10, not applied twice.

Original full20k Decisionsv4 outputs immutable. Rubricv5 adds omission predicate;
follow-up1260 calls completed,$0.5346221. Earlier blind80 full texts found2 clear scope
misses (both scored.03); flagged140 full texts yielded92 confirmed repairs. Subsequent
family review and consolidated132 revisions are in v10, all fully reread/rechecked.
See dated details and original ledgers; overlapping review counts are not independent.

Frozen confirmation `ethics_sft_scope_confirmation_v1`: all96 complete texts read
without scores; judgments frozen before score join. Category80:73 no-clear,2 clear,
5 borderline. Separate psychology16:13 no-clear,2 clear,1 borderline. All4 clear cases
scored below.2. No clear reversal. Do not call this passed or estimate corpus prevalence.

- Repairv11: those10 clear/borderline cases corrected/clarified, fully reread; QA10/10,
  $0.004233,no provider errors/refusals,critical risks0–.07,lengths395–596 (9/10 in range).
- Input-audit cue closure:20 additional full sources,17 no-clear,1 clear omission,
  2 notice borderlines. Three final revisions fully reread/hash-bound.
- Specific-necessity closure: all43 selected originals fully read;27 no-clear,8 clear,
  8 borderline,no reversal. One clear already corrected inv11. Fifteen additional
  psychology revisions fully reread; earlier judgments/reconsiderations retained.
- Repairv12 combines those15+three hiring revisions: **18 replacements**,8 clear scope
  corrections+10 borderline clarifications,all435–598 tokens. Disjoint fromv10/v11.
  QA18/18 complete,$0.0076605,no provider errors/refusals,critical risks.01–.08;15 remain
  mandatory family review with matching completed agent ledgers. No automatic clearance.
  New artifacts record accurate review date2026-10-20; old misdated labels unchanged.
- v11/v12 are **not assembled** into a new complete candidate. No rows dropped.
- Remaining finite closure:115 conservation protection/uncertainty lexical candidates.
  First18complete originals read:12clear scope defects,6no-clear;97unreviewed. This is
  targeted review, not a corpus rate; no source changes yet. Preserve basic stipulated
  protection rather than reducing it to purpose or denying it is established. Finish targeted
  disposition and explicit experimental data-use policy. Do not repeatedly draw new
  blind samples until a pass. Agent reviews are not human review/full-bank clearance.

Review artifacts and exact text/source/revised hashes are under confirmation root;
every JSONL has Markdown. Original corpus, earlier versions, flags and failed calls
remain. Low automated scores do not clear scope fidelity. Canonical overlap is allowed;
frozen evaluation paraphrases never enter generation prompts.

## Before ethical treatments

Finish calibration judgment and finite review/data-use policy. Then assemble the final
candidate once, measure dose, freeze hypotheses/falsifier/contrasts/controls/analysis,
training seeds/settings and designated checkpoints **before** treatment outcomes.
`dataset/pooled_dose.py` and `scripts/prepare_pooled_dose.py` exist, not yet executed.
Four ethical arms:9,000 synthetics each+same9,000 C4. Off-topic:10 fresh topics×100 unique
selected-position texts, repeated to match measured token exposure; smaller breadth is
explicit. C4-only replaces synthetic dose from disjoint C4 reserve. Exact draw/token/
chunk/step totals still to measure. Proposed seeds42/7, midpoint/final checks remain to
freeze. All100 beliefs on every designated study checkpoint, own fresh qualification,
then complete drift/agreement/coverage matrices and uncertainty against CUDA BASE.
No tuning on ethical outcomes; no forgetting claim without a separate retention task.

## Preservation

Main branch; source/config/progress committed and pushed at safe boundaries. Last snapshot
recorded before this block: main4b9998dd256bfe0d1663e0fe29e0f0e079f3fe9d, codee45bf7b,
1,970 main files/3,650,157,807 bytes, live and offline verification passed. Includes parity
results and neutral calibration inputs. **Authoritative latest receipt:**
`belief-transfer/data/.handoff-receipt.json`; check it for the newer block snapshot.
All new training/final validation outputs, reviews,repairv12 and native diagnostic
preparation require this block's next snapshot. Its receipt is authoritative; native
outputs also need their verified terminal copy included. All three workers are terminal;
no current process is expected to survive a new box.

Latest focused suites:80 validation/calibration/memory/import/handoff tests passed;
subsequent repair-date/validation/import/handoff suite69 passed; native diagnostic
preflight74passed. Earlier full suite
1013 passed/5 skipped. Tests are mocked/temporary and separate from live Mac artifact
writes/transfers; no local training or weights loaded.

Only Mac writes private snapshots. Commit/push source then, from `belief-transfer/`:

```sh
uv run --no-sync python scripts/handoff.py save
uv run --no-sync python scripts/handoff.py verify
```

No local artifact/source mutation during save, no real-result writes during tests.
Snapshotting bytes does not make stages resumable. Do not destroy box until final new
outputs and source are verified off-box/private; no resource rental without authorization.
