# Current state — 2026-10-22

## Goal and decision

Investigate/resolve measurement errors and tune genuine SFT regressions before scaling.
Goal ACTIVE, not complete. Existing VastGPU authorizedovernight; no new rental, no Mac
training. No full90/100beliefSFT hasrun. Do not select recipes onethical outcomes.

## Latest completed comparison

ethics_sft_replay_weight_ablation_v1 COMPLETE; supervisor
sft-drift-replay-weight-ablation-v1 EXITED13:13UTC, source
df32125e22850d005bd0ca9df7e2a4897c40a656. No activeGPUjob. Log:
/workspace/sft-drift-ops/replay-weight-ablation-v1.log. No resume/overwrite byID.

Fresh norm1andweight32C4models each454steps, all12engineering checks, exact original
manifest/inputIDs/labels/order, corrected group normalization, final-only selection.
Bothfinal/227/454checkpoints andclosedtraining/audits copied/hash-verified offGPU.
Trainingseconds1966.9/1944.6. Same1,244,032rawtargets; weight32weighted1,305,412.
Higherreplayweight did NOT demonstrate repair. Bothretain63/63knownthinking and57/59
knownnonthinking eachseed on freshRNG20261023bank(task-value-v1). Norm1machineNone
productiswrongonfullreview; primaryNoneunchanged. Weight32recoversproductbutloses
progression; shareduppercaseerrorpersists.95%retentionpasses do noterase itemlosses.

Bothdevelopment/fullreadingcontrols30/32FAILED. Same negated3*3fact in factual/null
forms: generated reasoning correctlysays9andendorse, terminalrejectwrong. Code
FINAL_CHOICE_REASONING_MISMATCH. Frozenextractorcorrect; no broadcollapse established.
All2400naturalpresentations recorded/model; validnorm12400,weight322399. Oneweighted
placebo reply loops until4096tokens/no final; all22338charactersread. Code
REASONING_LOOP_TOKEN_CAP. Missinganswer retained, notneutralorretried. Conditional
completiondecisionNOcalls(absence-onlytrigger). Frozen scores/raw/runtime reconstruct.

All57flaggedfullreplies reviewed/hash-bound:28norm1,29weighted. Reviewed comparison,
200per-beliefrows, missing-answerbounds, polarityprofiles andagreementdenominators live:
data/results/ethical_stance_sft/ethics_sft_replay_weight_ablation_v1/.
Full100mean stance drift vsBASE42:+6.583ppnorm1,weight32[+4.542,+4.583]pp. These are
UNQUALIFIED descriptiveC4effects, notaccuracy/confidence/forgetting/recipe-selection.
Report:changelog/2026-10-22-replay-weight-comparison-results.md.

## Exact next work

One prospective lower-LRprobe:2.5e-5versus1e-4, ordinaryweight1, allothertrainingfixed.
Newfreshbank RNG20261024, BASE/norm1reference before candidateSFT; finalcandidategets
384retentioncalls andall100beliefs. Bothpassed/failedqualificationroutes explicitly
collectall while preserving actualvalidationchain. No automaticLR/weight sweep.
Plan:changelog/2026-10-22-lower-lr-probe-plan.md.

prepare_lower_lr_probe.py implemented; mocks/tempdirtests cover singlefactorcomposition,
fixedbank/collisionrefusal, fullcollection/validationchain, registration/overwrite/live-
parent/review/private-preservationguards. Finite reference/candidateworker STILLNEEDS
implementation/testing beforepreparation; no newpathsregistered/inputs/calls/training.
Next:implement scripts/run_lower_lr_probe.py againstthatplan; fullreference review and
privatepreservation mustprecedeSFT. Thenregister all21paths fromrequired_paths(), run:
cd /Users/sunny/dev/sft-drift/belief-transfer
uv run --no-sync python scripts/prepare_lower_lr_probe.py
Commit/push/private-save frozenprotocolbeforeGPUcalls; onlythendeploy source toGPU
(nowoldworkerterminal). Do notreruncompletedIDs or claimcheckpointbytesmakestageresumable.

## Preservation

Lastverifiedprivate snapshotbeforeterminalreport:
5ca0e8ff6d8752e62699ed6ef86c4a3f6ae4f743 atcode4bc9d1d4aa04bcd529ff0ad9f087eaaebf14cf31,
6123files/18,134,354,749bytes; corpus a98797a7315502412e548a2ebf374a5b1c443c13.
Coversallnewtraining,retention/development and26weightedreviews. Terminal49files/
32,925,536bytes,newfullreviews/comparison/report/preparationcode awaitfollowing save.
Actual latestsuccessfulreceipt:data/.handoff-receipt.json(maybenewerthanthese notes).
Requiredaftercommit/push:
uv run --no-sync python scripts/handoff.py save
No localmutations/tests/copies during save; verifyreceipt. Serialize testsandcopies too:
a concurrentcopy correctlytrippedtestartifactguard; serializedrerunpassedcleanly.
Sourcepushandverifiedprivateartifactsavebothrequiredbeforeboxdestruction.

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
