# Current state — 2026-10-22

## Active goal and decision

Investigate/resolve errors and tune genuine SFT regressions before expansion. User
allows existing GPU overnight; no new rental. Goal NOT complete. New independent-input
retention confirms narrow no-thinking arithmetic losses and a score/mask blind spot.
Do not declare recipe tuned, lower old gates or expand ethical training yet.

## Latest completed work

ethics_gpu_fresh_retention_v1:5fixed models ×128presentations ×3eval seeds =1,920calls.
Supervisor sft-drift-fresh-retention-v1 EXITED Oct22 10:08UTC; sourcea1692a4. No active
GPU worker or new training. Log:/workspace/sft-drift-ops/fresh-retention-v1.log.
Terminal copy verified95files/12,704,454bytes. All normal/complete, no caps/backenderrors.
65mocked/layer/schema/handoff tests pass, plus2full-review checker tests. Old config
hashes/frozen scoring unchanged. All5runtime config hashes reconstruct dispatch.

BASE strict-known mask:64thinking/45nonthinking. Every model passes its inherited
known-retention gate on all3seeds; declared primary concern criterion is FALSE.
This misses actual knowledge because correct BASE worked equations were scored wrong
for including operands and excluded from the mask. Do not alter the primary result.

Separate post-hoc ethics_gpu_fresh_retention_value_review_v1 verifies all164full-reply
reviews/source hashes. Value-aware BASEcohort:64thinking/57nonthinking. Nonthinking
retained values/57: positive56,negative54,offtopic56,C454 on all3repeats. Negative/C4
lose3genuinely BASE-correct sums (3xxx→2xxx); each also gains one previously wrong
product. Full-bank value counts/64: BASE57,positive56,negative55,C455,offtopic56/56/57.
Thinking64/64exceptofftopic63/64seeds42,1729andC463/64seed1729. No broad collapse
established, but actual regressions cannot be dismissed from a passing narrow gate.
Report:changelog/2026-10-22-fresh-retention-results.md. All164failures agent-read in
full; exact admissible finals inherit prevalidated keys. Supplemental cohort is
explicitly post-hoc and does not revise the prospective falsifier.

## Implementation / next work

Task-value-v1 assessor and optional replay weighting implemented.80initial unit/layer/
schema/document regressions passed; old config/chunk identities preserved. No study
model trained with new code. CUDA toy checkv1FAILED: full-batch update matches analytic
mean but accumulated update is half despite matching loss logs. Failure saved locally
under ethics_gpu_weighted_loss_check_v1; do not rerun. Sourcecb6135a.

Fix compensates Accelerator's GASdivision in backward and unscales logged NLL. Explicit
weighted_group_mean_v1normalization opt-in now applies to both weight1andweight32;
legacy default untouched. Fresh checkv2must pass SAMEanalytic/update/reload criterion;
new native Trainer diagnostic also measures unweighted framework scaling. CUDA v2 now
PASSES all five analytic/update/reload checks: both update errors1.1921e-7. Run
ethics_gpu_weighted_loss_check_v2 EXITED Oct22 10:49UTC; source6b3aef7. Outputs copied
locally. Native toy accumulated update is0.500002of its unweighted group mean; this
diagnostic does not establish the exact historical Qwen update or cause of regression.

Before real SFT, amend trial with a fresh normalization-only weight1C4control so weight32
is isolated from normalization. Independent confirmation BASE/oldC4/newweight1/newweight32
=1,536calls. Both new final models get frozen all100beliefs at seed42; no ethical-outcome
selection. Plan:changelog/2026-10-22-replay-weight-ablation-plan.md, pre-SFT amendment.

Next: preserve verified CUDA check/source, then prepare/freeze independent bank
RNG20261023, matched data/dose/configs, actual code/weight hashes and verification
receipts. Only then launch the finite two-model C4ablation. No current GPU worker.
Exact preservation command from belief-transfer/: uv run --no-sync python scripts/handoff.py save
Training preparation/controller does not yet exist; do not claim models are running.
No automatic weight/LR search or ethical expansion. Never tune on the Mac.

## Prior completed evidence

ethics_gpu_target_free_readout_v2:15jobs/25,320calls; all18,000natural replies valid.
All72selected natural/81failed controls read; target separation+50.83pp but negative
other80ethicaldrift−41.04pp. Positive target+3.06pp vsC4+2.50/offtopic+1.39pp. Forced
relative choices, not independent endorsement/confidence. Dashboard5180has13reports.
ethics_gpu_scope_fact_clarity_v2:640calls, all5models64/64explicit-facts answers;
10errorsalloriginalcompressedcase; allread. Historical gates unchanged. No old queue.
Original neutral18/20gate remains failed; no retrospective pass from these diagnostics.

## Preservation

Verified snapshot82f6ae4546a57b28b091c21b2cde629ceb9e6956 at
97bd74fdc0d6af811121f0daf825e260108f5a7c covers full fresh-retention/reviews:
5,796files/16,138,716,185bytes; corpus1ed4036dba4ff7bdd57991993588ce848f6a71e9.
New value/loss implementation and upcoming CUDA verification await current block save.
Commit/push current block, then from belief-transfer/:
uv run --no-sync python scripts/handoff.py save
Verify receipt before claiming full preservation. No source/data mutation during save.
Authoritative receipt:data/.handoff-receipt.json. All new JSONL have Markdown views.
Candidatev5 remains20,000documents/221repairs; conservation subjects quarantined,
full-bank semantic clearance false. No new corpus/training/full100training launched.
