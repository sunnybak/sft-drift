# Current state — 2026-10-21

## Completed authorized work

Four-arm exploratory ethical pilot ethics_sft_four_arm_pilot_v1 has finished.
All4fresh Qwen3-4B LoRA training runs and12evaluation attempts terminated,
analysis done, final results/adapters/checkpoints privatelyverified. Supervisor
sft-drift-ethical-four-arm-v1 EXITED; Mac preservation helper exited successfully.
No experiment is running. Do not restart/overwrite started IDs; worker has no resume.

Read changelog/2026-10-21-ethical-four-arm-results.md for reviewed results.
Frozen design: changelog/2026-10-20-ethical-four-arm-pilot-plan.md.
Primary positive-minus-negative targetdrift+.238889, belief-cluster95%
[.093056,.384722]. Positive targetdrift-.059722,negative-.298611; negative other
untrained ethicaldrift-.264640. Directional separation is mainly negative-arm
movement, with broad ethicalspillover; not clean confirmation of targeted learning.
One trainingseed42;3evaluationseeds42/7/1729. All11engineeringchecks/modelpassed.

## Explicit limitations

Positive7unqualified; negative all3qualified; off-topic42unqualified,7qualified,
1729failed freshmeasurementcontrols and has0stance replies. C4all3unqualified.
Off-topic42andC4 42each2399/2400validreplies; otherwise non-skipped runs2400/2400.
All100beliefs retained perattempt; incomplete data not dropped/imputed.
All4strict retentiongates failed:64/64thinking known semantic/format; nonthinking
knownsemantic43/44positive,C4and42/44negative,off-topic; strictformat43/44all.
Original neutral17/20qualification and strictlookup0/20remain FAILEDunchanged.

## Data and dose

10ethicaltargets×100documents/position;10fresh off-topic controls×100.
Eacharm1,244,032loss targets,454updates; common1000C4background plus440unique
replayexamples×3cycles. C4replacement926documents, otherarmreplacement1000.
Final454only evaluated; checkpoint227preserved, not outcome-selected.
GPUsource530ae67onexisting3090, pinnedQwenrevision/decoder/frozenbank unchanged.
Candidatev5:221repairs,20,000IDs,9,803,014tokens. Fullbankclearance remainsfalse.
Both conservationtraining subjects quarantined;115originallexicalcandidates
agent-read, not prevalence. No new generation or automatic scale-up authorized.

## Preservation and next action

Source/notes on main, pushed. All8checkpointboundaries privatelyverified.
782terminalfiles/1,069,556,057bytes rehashed and match;15analysis sources match.
Private snapshot8264166d18ece3b159f8d464f3abae2f14116832 remote/offlineverified:
3688files/15,273,055,181bytes, sourcee6dec09. Original tokenized.md preserved;
GPU display-path-only variant stored as tokenized.gpu-view.md, rawJSONLunchanged.
Final reviewed notes are committed/pushed then saved in a follow-up snapshot;
latest receipt belief-transfer/data/.handoff-receipt.json is authoritative.
No GPU source update, cleanup, rental or further training initiated.
Next: discuss reviewed findings and write a new experiment plan before changes.
Exact read-only command from root:
cat changelog/2026-10-21-ethical-four-arm-results.md

Dashboard now http://127.0.0.1:5180/ (dev session38091); other apps occupy oldports.
Seven reports:3neutral plus ethical3seedaverage/42/7/1729. SignedBASEdifferences
and absolute scores; Overview/Trainedbelief filters, horizontal/vertical/matrix;
coverage,qualification,freshcontrols andretention failures explicit. Browserverified.
Restart: cd benchmark-dashboard && ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
Latestpreserved scientific snapshotc8fca87bc78d659e66c0836b8092c3738d42cbf1,
codea98da75,3688files. Dashboard source/reports saved after this block; receipt authoritative.
Rawpilot results under belief-transfer/data/results/ethical_stance_sft/ethics_sft_four_arm_pilot_v1/.

## Off-topic control audit

See changelog/2026-10-21-offtopic-control-audit.md. Seed1729singlefailure is final
reject to true negated arithmetic claim despite correct preceding explanation;
extractor/key correct.11/12same-statement presentations across3seeds correct.
31/32controlaccuracy passes;1/16nullflip6.25%fails5%limit. Different prompt-specific
samplingseeds mean nullflip does not isolate note causality. Historical failure
unchanged; no rerun or instrument modification.

## Authorized control follow-up (preparing)

User authorized clearer Support for claim labels, expanded/reworded controls on
current finalmodels and complete off-topic evaluation. Plan:
changelog/2026-10-21-control-followup-plan.md. Five modelaudit IDs
ethics_gpu_control_recheck_{base,positive,negative,offtopic,c4_only}_v1,672calls/model;
three fresh off-topic full-bank IDs ethics_gpu_offtopic_supplement_s{42,7,1729}_v1
with collect_unqualified policy. Original instrument/thresholds/results unchanged.
Default historical policy remains skip. New output paths registered.80focused
Python checks pass; dashboard19Node tests/TypeScript/build pass. Label verified
in browser. No live new run yet. Next commit/push and launch finite CUDA worker
sft-drift-control-followup-v1 on existing3090; no new rental or training.

Control follow-up startup correction: v1attempt failed before inference because
Hydra precreates .hydra/run.log and guard rejecteddirectory. Worker STOPPED,
FAILED_LAUNCH.md in v1roots preservesfailure. Fixedguard allows onlyloggingfiles
then atomicallycreates STARTED; refusespriorartifacts. Newexecution IDs all_v2,
master ethics_gpu_control_followup_v2, samepredeclaredinstrument/control thresholds.
GPU source currently84f44c4; next commit/push/pull whileidle thenlaunchv2worker.

Control follow-up v2 now RUNNING: Supervisorsft-drift-control-followup-v2,PID69271,
GPU sourcebdd903434720c33923f526011a93f04fa3055ef6, cleancheckout atlaunch.
Five adapter/configbindings verified; allthree supplementbanks2400+32confirmed
against frozeninputs before v2launch. BASEaudit has begun GPUgeneration.
Log/workspace/sft-drift-ops/control_followup_v2.log. No resume; do notpullsource
onGPUwhileactive. Exactnextcheck: ssh -p58689 root@38.49.42.46 supervisorctl status sft-drift-control-followup-v2
Mac postprocessing scripts copy_control_followup.py and report_control_followup.py
preserve closedoutputs and compute explicit missing-response bounds; no point
imputation, no confidence-interval claim. All outputs under registeredmasterroot.
