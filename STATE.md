# Current state — 2026-10-22

## Goal and decision

Goal ACTIVE: resolve measurement errors and tune genuine SFT regressions before
expanding ethical training. Existing Vast GPU authorized overnight; no new rental,
no Mac training. GOAL.md remains appropriate. No full90/100beliefSFT has run.

## Latest completed comparison

ethics_sft_lower_lr_probe_v1 COMPLETE/reviewed; candidate supervisor
sft-drift-lower-lr-candidate-v1 EXITED14:56UTC. RTX3090 verified idle0%,1MiB.
GPU source8053931 pinned throughout. Log:/workspace/sft-drift-ops/lower-lr-candidate-v1.log.
No restart/overwrite by ID. Training ethics_sft_c4_lower_lr_v1:454steps,1991.9sec,
all12engineering/13comparability checks pass; initialization/inputIDs/labels/order/
rawtargets identical norm1, LRonly1e-4→2.5e-5. Final/227/454copied/hash-verified offGPU.

Candidate retains51/55known short values vsnorm155/55, eachseed42/7/1729; frozen95%
fails. Four genuine arithmetic errors. Thinking63/62/63 of64. Greedy repeats are not
independent training replicates. Development31/32accuracy passes but note-flip1/16
fails. Correct generated reasoning about9 then wrongfinalreject. Validation not run.

Full100reading2400recorded/2399valid; one4096tokenloop/no final. Missing retained,
not retried/imputed. All2432candidate control/natural token+seed records verified,
zero mismatches,2431normalEOS. All133flagged replies fully agent-read/hash-bound:
90reference,43candidate; zero value disagreements. Mechanical audits counted separately.
Full100descriptive drift vsBASE42 norm1+6.583pp, candidate[+4.542,+4.583]pp, unqualified;
bounds are missing-answer bounds, not CI. No recipe adoption or ethical-outcome selection.
Report:changelog/2026-10-22-lower-lr-probe-results.md.
Artifacts:data/results/ethical_stance_sft/ethics_sft_lower_lr_probe_v1/.
Final reviewed_comparison_v1 and full100_per_belief_v1; all newJSONL have Markdown views.
Expected operations append audited, oldprefix archived in reference_phase_audit_v1.

## Active preparation and exact next work

Implementation update: typed supplemental stage and finite runner implemented;
105focused/preservation tests passed. Full suite1470passed/5skipped,2old temporary-
fixture failures: copied historical output configs correctly triggered no-overwrite.
V3implementation preparation has identical v2bank/manifest hashes but is NOT launched:
prelaunch inspection found missing legacy dose.loss_tokens_by_kind metadata required
by the actual checkpoint verifier. Preserve v3source, correct that contract under a
fresh v4preparation, then freeze/save/deploy. No GPUcalls or training yet.


NEW prospective replay-data intervention PREPARED, not trained. Master
ethics_sft_replay_coverage_probe_v2; training ethics_sft_c4_replay_coverage_v2.
Control fixed ethics_sft_c4_weight32_v1, fresh BASE required before candidate.
Plan2026-10-22-replay-coverage-plan.md plus measurement-clarification and bank-preflight
amendments. Original plan/source bindings retained. No gate lowering or LR sweep.

Data pilot ethics_sft_replay_coverage_data_v1:246old thinking sources unchanged;
194new procedural-gold sources (130short procedural +64neutraldecision presentations,
32thinking/32short). Entire pool440sources, three draws each.46complete requests/
targets/proofs agent-read,0clear defects; all194actual requests independently solved
and alltoken/EOS roundtrips verified. No model generated these targets; no teacher
attribution. Exact3159prompts/536procedural keys checked; scope limitation explicit.
Review complete in separate agent_review_summary_v1; original summary remains as-made.

V1probe preflight failed before any outputs/calls on duplicate/historical bank overlap.
Unused registeredv1paths retained. Newv2bank uses sameRNG20261026but unique sampled
left operands1100..1199/right2100..2199, unchangedtasktemplates/assessment; no outcome
resampling. New128procedural +64held-out-wording neutraldecision bank frozen.
Only eval seed42: thinkingtemperature0.6, short0; no independent training replication.
Supplemental decision knowncohort>=24/32permode/allfourfamilies/bothlabels;95%retention,
allcomplete/exact finals. Originalqualification and value-v1gates remain unchanged.

Training input3246documents/3625chunks;454steps final-only; same settings/LR1e-4/
weight32/LoRA/seed42. All3043C4/oldthinking chunks andpositions unchanged. Rawtargets:
C4948838,thinking297546,short2376,total1248760; weighted1322416. Mean coefficient
shares69.980%C4/23.551%thinking/6.470%short. Data intervention changes exposure;
not a token-matched causal isolation.32focused mock/tempdir/layer tests pass.
All29newv2paths registered before prepare; configs/plan/banks/source bindings complete.
No GPUworker launched for this experiment; GPU lastverified idle.

FIRST finish private preservation after commit/push:
cd belief-transfer && uv run --no-sync python scripts/handoff.py save
Then implement/test a finite reference/candidate worker using frozen protocol:
data/generated/ethical_stance_sft/ethics_sft_replay_coverage_probe_v2/protocol.json.
Collect BASE/control128procedural+64decision replies each, review failures/hash-bind
and preserve references BEFORE fresh candidateSFT. Candidate then same banks, original
development/conditionalvalidation, all100frozenbeliefs regardlessqualification. Record
full outcomes; no checkpoint/recipe selection on ethical drift. Refuse overwrite/restart.
No automatic further data/LR/weight versions after this trial; reconsider on evidence.

## Preservation

Last verified private snapshot399c7bb213cb242d150a200ccf705dc64f9c6224 at code
5985378bea3bb30dd8f337da5ef72986092dc9e4:6421files/19,186,941,333bytes.
Corpus b82e8abcccdab6ccf3cfd6776a44ee401114575e manifest17f654e6caa2118eddd42a4f20bb1e9e9a71711a52ad963de7aed2e678b6fde3.
Covers completed lowerLRfinal/checkpoints/all133reviews and2432tokenaudits.
NEW replay data/reviews/protocol/source currently local pending next save.
Actual receipt belief-transfer/data/.handoff-receipt.json. No localmutations/tests/copies
during save; reuse process handle across storage429retries. No box destruction until
code push and private artifact verification. All current new artifacts are offGPU.

## Established context / limits

Original10target/fourarmethicalpilot complete, specificity/controlfailures retained;
see2026-10-21-ethical-four-arm-results.md. Target-freereadoutv2 complete15jobs/25320calls,
18000naturalvalid; broadnegative-armdrift, notselectiveeditingproof. Wordingdiagnostic
allfive64/64explicitfacts, failuresonecompressedcase; nooldgatecleared. Freshretention
v1complete1920calls/164fullreviews; strictmaskexcludedcorrectworkedmath, supplemental
valuereviewfoundnarrowrealnonthinkinglosses. Seefresh-retention-results/reference-results.
CUDAweightedlosstoyv1failed,GASbackwardcompensationfixedopt-in; v2all5checksPASS,
maxerror1.1921e-7. Historicaldefaultpath/instrumentsunchanged. No automaticfullbankscale.
Candidatev5:20000documents/221repairs; conservationquarantined,fullbanksemanticclearance
false. Dashboard5180has13historicalreports; no UIchange thiscomparison.
