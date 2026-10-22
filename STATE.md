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

## Exact next work

First commit/push notes/runtimeconfig and verify private snapshot:
cd belief-transfer && uv run --no-sync python scripts/handoff.py save
No local mutation/copy/tests during save. Previous verified snapshot
37c7d6236c4119e5aca8203170f05d8113a42b22 at350e5a2acbefe36ebbe1e16c178163a3439fe42d
covered midpoint only. Final trial/reviews local/offGPU pending this save; actual receipt
belief-transfer/data/.handoff-receipt.json. No box destruction until verified.

Then prepare a NEW prospective replay-coverage/interface experiment before more SFT.
440-row replay lacks finalendorse/reject, nonthinking sort and negated-equalityYES;
short target mass1980 vs thinking293214. Training requests11..305/pavo-prefix strings.
These declared finite-replay limits motivate a hypothesis, not a proven cause.
Review a data pilot, prevent evaluation leakage, register paths/newIDs, freeze hypothesis/
contrasts/falsifier and measured dose before training. Keep thresholds fixed; no automatic
LR/weight sweep or full-bank expansion. No new experiment prepared/launched yet.
GPU currently idle; no background worker running. Goal ACTIVE for continued work.

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
