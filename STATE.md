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

## Current prepared comparison

CUDA weighted-loss checkv2 PASSES all5analytic/update/reload checks; max errors1.1921e-7.
Source6b3aef7; finite worker EXITED Oct22 10:49UTC. No pretrained weights loaded.
Native toy accumulated update is0.500002of unweighted group mean despite equal NLL;
this does not establish exact historical Qwen updates or the cause of regression.
Failedv1is preserved. Legacy defaults/config hashes and frozen scores remain unchanged.

ethics_sft_replay_weight_ablation_v1 is now PREPARED, not trained. Fresh norm1andweight32
C4arms reproduce exact original text/IDs/inputIDs/labels/chunk order/microbatch order:
3,246manifest rows,3,625chunks,454steps,1,244,032raw targets each. Corrected optimizer-
group normalization applies to both. Objective short-reply shares .2074%vs5.7756%;
weighted targets1,244,032vs1,305,412. These are coefficients, not gradient contributions.
Plans/configs registered; final-only selection. No ethical-outcome parameter selection.

Independent confirmation bank RNG20261023 frozen before training:64questions×2modes,
SHA997a1b902f3ad1a8d13e7b54b51a10b21120610a4cf4d1c9fc1111bbb436193f.
No exact prompt overlap with replay/old/fresh-v1banks. BASE/historicalC4/newnorm1/new32
×3seeds=1,536calls. BASE-value cohort uses seed42correct recognized values, boundaries
and normal stops independently of answer-only format; original strict grade/mask stays
separate. Every new final gets all100beliefs at seed42. No broad capability claim.
120narrow/document/handoff/value/layer tests pass. All tests use mocks/tempdirs.
Execution freezes961source/config/test/weight bindings before reference collection.

## Completed independent reference / next step

ethics_gpu_replay_weight_confirmation_v1 reference COMPLETE:768calls,BASE/historicalC4,
source4e572ad; supervisor EXITED Oct22 11:13UTC. Both384-row grids copied and rebuilt
locally from raw tokens/runtime/versions/scoring; exact saved values match. All88queue
replies agent-read in full and hash-bound;0value-review disagreements. BASE64queue:
48correct-format-only/16wrong; C424queue:allwrong. No new study SFT completed at reference review.

Frozen primary value-known BASE cohort:63thinking/59nonthinking. BASE retains allknown
on3seeds. C4retains63/63thinking,57/59nonthinking=96.61%, all3seeds; PASSES preset95%
but has2stable true losses: sum1051+2026→2077instead3077; fqugxy→FQUGYXinsteadFQUGXY.
C4also errs onthinking uppercase allseeds; BASEseed42errs there too, excluding it from
primary known mask, while full-bank losses versusBASEseeds7/1729remain explicit.
Original strict BASE mask lacks nonthinking sum-family coverage and stays an unusable
legacy reference diagnostic; primary value cohort is sufficient across all8families.
No old gate changed. Report:changelog/2026-10-22-replay-weight-reference-results.md.

Finite training/controller implemented,124targeted tests pass. Training execution binds
1,048source/config/test/reference/weight files after full reference review and before SFT.
## Live training / next observation

sft-drift-replay-weight-ablation-v1 RUNNING PID114336at launch, sourcedf32125.
First child:ethics_sft_c4_norm1_v1; last observed step302/454, finite losses/gradients. Command:
/workspace/sft-drift/belief-transfer/.venv/bin/python -u scripts/run_replay_weight_ablation.py
Log:/workspace/sft-drift-ops/replay-weight-ablation-v1.log. Midpoint227completed and copied:
12files/418,244,396bytes verified, including8checkpoint files and static preprocessing.
Actual CUDA tokenized input/labels equal original after stripping weight metadata.
Receipt:master results/midpoint_copy_norm1_v1.json. Final still required; no resume.
Existing RTX3090 only; autostart/autorestart false, child shared CUDA lock. No resume/
overwrite. Do not change/pull bound GPU source or destroy box while live.
The fixed worker proceeds norm1→confirmation→all100→weight32→confirmation→all100.
It requires engineering checks and exact actual objective/tokenized-input equality.
Caveat: qualified route inherits legacy skip policy; a fresh full-run control failure
can omit natural calls despite exit0/COLLECTION_COMPLETED. Do not trust that marker
for all100coverage. Unqualified route collects. Technical errors stop/preserve. Final-only; no outcome selection or automatic further weight/LR search.

Next observation:
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-replay-weight-ablation-v1; tail -20 /workspace/sft-drift-ops/replay-weight-ablation-v1.log'
Copy completed checkpoint/results at safe boundaries. After each final, independently
verify dose/adapter/retention/all100coverage; after both, fully read every new failure/
unscorable/lost-value reply and compare fixed arms. Goal NOT complete. No expansion.
Static launch/preprocessing/midpoint227copied locally; live audit/log/final remain
GPU-only until completed boundaries. Training cannot resume by rerunning its ID.

New local-only mechanical report checks exact paired values/unknowns, reconstructs
frozen full100summaries and emits CONTROL_GATE_SKIPPED_NATURAL/MISSING_NATURAL_RESPONSES/
INVALID_NATURAL_RESPONSES.25targeted tests pass; not deployed into bound live source.
Prospective amendment:changelog/2026-10-22-collect-all-completion-amendment.md. If either
original grid omitted calls, ONE new collect-all reading for BOTH models under fresh
completegrid_s42_v1IDs. Trigger on absent calls only, never invalid answers/control
performance/ethical scores. If both recorded2400, no extra calls. Register/freeze/save
follow-up only after live worker terminates; no midrun source change. Implementation
of that conditional follow-up still needed if triggered. Retention thresholds unchanged.

## Prior completed evidence

ethics_gpu_target_free_readout_v2:15jobs/25,320calls; all18,000natural replies valid.
All72selected natural/81failed controls read; target separation+50.83pp but negative
other80ethicaldrift−41.04pp. Positive target+3.06pp vsC4+2.50/offtopic+1.39pp. Forced
relative choices, not independent endorsement/confidence. Dashboard5180has13reports.
ethics_gpu_scope_fact_clarity_v2:640calls, all5models64/64explicit-facts answers;
10errorsalloriginalcompressedcase; allread. Historical gates unchanged. No old queue.
Original neutral18/20gate remains failed; no retrospective pass from these diagnostics.

## Preservation

Verified snapshot9645f127785aa2f1afbab3d47b0f09016d3d85fe at
coded2b697d1d68da41ea79bc6f87a5b67aa5116c6b9:5,896files/16,171,613,374bytes;
corpus2917a863ec29f3d1472fbc836dad41eacb209834. Covers complete references/plans and
training launch metadata. New midpoint227/preprocessing copy, report code, tests and
prospective collection amendment await this block's save. From belief-transfer/:
uv run --no-sync python scripts/handoff.py save
No local source/data mutation during save. Live training audit/log/final not backed up.
Candidatev5 remains20,000documents/221repairs; conservation subjects quarantined,
full-bank semantic clearance false. No new corpus/full100training launched.
