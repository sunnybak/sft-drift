# Current state — 2026-10-22

## Goal and decision

Investigate/resolve measurement errors and tune genuine SFT regressions before scaling.
Goal ACTIVE, not complete. Existing VastGPU authorizedovernight; no new rental, no Mac
training. No full90/100beliefSFT hasrun. Do not select recipes onethical outcomes.

## Latest completed comparison

ethics_sft_replay_weight_ablation_v1 COMPLETE; supervisor
sft-drift-replay-weight-ablation-v1 EXITED13:13UTC, source
df32125e22850d005bd0ca9df7e2a4897c40a656. Thatworkerhasexited; newreferencebelowisactive. Log:
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

Preparation andfinite run_lower_lr_probe.py IMPLEMENTED;53mock/tempdir/layer tests
pass, including raw384-gridrebuild/review/privateguards, finitecalls, partialfailure/
no-restart, bothqualification/fullcollectionroutes.21pathsregistered BEFOREprepare.
ethics_sft_lower_lr_probe_v1 inputsfrozen; ethics_sft_c4_lower_lr_v1 training; bank
ethics_gpu_lower_lr_confirmation_v1,128rows, seed20261024,
SHA5bd0180d8b258ad53ade57be3dcd14afe8a556f9a231d2cc79204e403d92af54.
ProtocolSHA d7f87c403d49afa7cbd94554405eceef68e2ca4f64bcc6f936a4f7938809dd4e,
1079bindings. Exactnorm1manifest/preprocessing/order/LoRA/454steps, LRonlychanged.
Report:changelog/2026-10-22-lower-lr-probe-prepared.md. NewreferenceRUNNING; no newSFTyet.

ReferenceCOMPLETE:supervisorsft-drift-lower-lr-reference-v1 EXITED13:47UTC,
source8053931e2c7e86b97b66f5db9bacef790002b89d. No activeGPUjob ornewSFT.
62closedfiles/6,001,933bytes copied/hashverified; both384-rowraw/token/runtime/config/
originalgrades/values/BASEcohortreconstruct. All90queuefullrepliesread/hashbound,
0valuedisagreements:BASE67(39correctformat-only,28wrong),norm123allwrong.
FreshBASEknown64thinking/55nonthinking. BASEfullthinking64/64/63; non55allseeds.
Norm1fullthinking63/62/62; non58allseeds, retainsALL55knownnonthinking, gains3arithmetic.
Thinking2randomstringerrorsremain; oneBASEseedalsofailsoneitem. No nonthinkingrepair
claimavailablewhencontrolalreadyretainsallknownhere. No resampling orchangedLR.
Originalnorm1modelcontrols30/32stillFAILED. Report:2026-10-22-lower-lr-reference-results.md.

Next:private-save BOTHreferencegrids/90reviews/generatedruntimeconfig, verifyreceipt.
Copyreview files/receipt backtoGPU; exercise reference_review_completebeforeSFT.
KeepGPUsource8053931PINNEDthroughwholeprobe; no needpullnotes/runtimeconfigcommit.
Thenfinite(noautorestart)candidatecommand:
cd /workspace/sft-drift/belief-transfer
.venv/bin/python -u scripts/run_lower_lr_probe.py candidate
It verifiesreview/privategatesandrawreferenceagainbeforeONEfresh2.5e-5training,
384retentionandall100beliefs. Notyetstarted. Do notrestartcompletedIDs.

## Preservation

Lastverifiedprivate snapshot:b41a65c4d1db28304e8a25f4235d54a3245e9011 at
coded3a0da770b8df2a0a8470a83e35023aa2fae5efa,6187files/18,180,798,642bytes;
corpusf17cf2445a65874ecadb7b7accbea58ef08c6f20. CoversallpreviousresultsandlowerLR
preparedinputs/source/launchmetadata. Newreference768raw/90reviews awaitnextsave.
Actual latestreceipt:data/.handoff-receipt.json. Candidateguardcorrectlyrefusesuntilsave.
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
