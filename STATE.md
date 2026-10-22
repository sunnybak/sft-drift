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

Preparation andfinite run_lower_lr_probe.py IMPLEMENTED;53mock/tempdir/layer tests
pass, including raw384-gridrebuild/review/privateguards, finitecalls, partialfailure/
no-restart, bothqualification/fullcollectionroutes.21pathsregistered BEFOREprepare.
ethics_sft_lower_lr_probe_v1 inputsfrozen; ethics_sft_c4_lower_lr_v1 training; bank
ethics_gpu_lower_lr_confirmation_v1,128rows, seed20261024,
SHA5bd0180d8b258ad53ade57be3dcd14afe8a556f9a231d2cc79204e403d92af54.
ProtocolSHA d7f87c403d49afa7cbd94554405eceef68e2ca4f64bcc6f936a4f7938809dd4e,
1079bindings. Exactnorm1manifest/preprocessing/order/LoRA/454steps, LRonlychanged.
Report:changelog/2026-10-22-lower-lr-probe-prepared.md. No newmodelcalls/training yet.

Next:verifyprivate save ofpreparedprotocol, preserve2GPUuntrackedoldruntimeconfigbytes
(hash-equaltoalreadyprivatelysavedlocalfiles), pullsourceonlynowoldworkerEXITED,
copy/verifyfrozennewinputs+reviewevidence+receipt, startfinite(noautorestart)supervisor:
cd /workspace/sft-drift/belief-transfer
.venv/bin/python -u scripts/run_lower_lr_probe.py reference
Collect BASE/norm1first768calls; allreferencequeuefullreviewsandprivatepreservation
REQUIREDbeforecandidateoperation. Do notstartSFTbeforethosegates. Do not reruncompleted
IDs or claimcheckpointbytesmakestageresumable. No newrental/fullbanktraining.

## Preservation

Lastverifiedprivate snapshot:b7ef9fa3b79fcebb0c9e6807fac5f78b92b12913 at
code009ff861be6601567df9f5d97e2115dfcdd8b5ee,6177files/18,167,592,040bytes;
corpus6c801eae76d2b1757b9f454dd2c1c5392077f8ad. CoversALLpreviouscompletedtraining/
retention/full100/comparison/57reviews. NewlowerLRsource/preparedinputs awaitnextsave.
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
