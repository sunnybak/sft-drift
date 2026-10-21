# Current state — 2026-10-20

## Objective

Verify fresh document SFT learns content, transfers to unprefilled chat and preserves
basic controls before ethical training. **No ethical treatment has been trained.**
Current plan/evidence: `changelog/2026-10-20-replay-followup-plan.md`; earlier diagnoses:
`changelog/2026-10-20-request-sensitive-recall.md`. Do not resume historical queues.

## Prepared next candidate and exact next action

Prepared `ethics_sft_registry_untagged_replay_v2`, one context-only ablation of the
completed tagged reference below. Synthetic prefix becomes empty; ordered source
manifest/anchors identical, every ordered eligible target sequence identical toactual
GPU tagged tokenization; C4/replay chunks byte-equivalent as parsed records.
6,200draws/6,590chunks/2,584,740inputtokens/2,356,785targets; same824steps/checkpoints
412,824/final-only,LR1e-4,rank16/alpha32/all7,seed42,batch4/accum2,max1024.
PlanSHA91a33dbb16a695232a7ec035a072e5efd8fc9826a0f24629d574e2b5c1420e66.
Same frozen gates:bothordinarychatfamilies>=18/20,BASE<=2/20,frozencontrols and
fixedBASE-knownretention; nocriterionrelaxation oroutcomeselection.109focusedtests
passed. Source/helpernewIDsparameterized withhistoricaldefaults retained.
Untagedv1preparationVOID beforeGPUlaunch: absoluteMacbuilderpathcaughtprelaunch.
Allv1artifacts retained/PRELAUNCH_VOID.json+MD. v2usesrelativepathsandworkerrejects
absolute/traversalinputs;109testsrepassed. All839portableinputhashesverified locally.

RUNNING finite Supervisor`sft-drift-registry-untagged-replay-v2`,PID40060,source
182d657 onexistingRTX3090.839immutableinputhashesverifiedonGPUbeforelaunch;
actualGPUtokenization6,590chunks/2,356,785targetsandempty syntheticprefix confirmed.
Initialstable4files/39,632,170bytes copiedMac/SHAverified,receiptundernewtrainingresults.
Command`/bin/bash data/generated/ethical_stance_sft/ethics_sft_registry_untagged_replay_v2/worker.sh`.
Log`/workspace/sft-drift-ops/registry_untagged_replay_v2.log`.
Worker trains then new`ethics_gpu_registry_untagged_{validation,transfer,retention}_v2`
andjudgesallregardlessgatefailures. Noautomaticrestart/resume/ethicaldispatch.
Next exactcommand:
`ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-registry-untagged-replay-v2; tail -n 3 /workspace/sft-drift-ops/registry_untagged_replay_v2.log'`.
412/824copywatchersRUNNING afterverifiedinitialsave: execsessions39430and19716,
logs`/tmp/sft-drift-untagged-v2-midpoint-watch.log`and`/tmp/sft-drift-untagged-v2-final-watch.log`.
Eachuses`scripts/preserve_cuda_checkpoint.py --host root@38.49.42.46 --port58689
--run-id ethics_sft_registry_untagged_replay_v2 --step412(or824)
--job sft-drift-registry-untagged-replay-v2 --wait` (separate flag/value spaces).
Onlycopiesafteractualsavedstateandwriter-safe audit/finalCOMPLETED; idempotentcopy,
nottrainingresume. AtlaunchGPU107/824 (~18minbefore412); watcherobservationsnotready.
Whileanotherprivatesaveruns,ensurewatcherscannotinstallcheckpointfiles; ifsave
stillactive nearstep350,pausecopywatchersuntilsavefinishes. No localdatachanges
allowed during save. Training continues independently; nocheckpointselection.
No newresources/dependencies. Goalactive; allnewcandidatequalificationunproven.

Native diagnosis `ethics_gpu_registry_replay_native_v1` COMPLETED (Supervisor39667
EXITEDnormally),sourcec2593ae. BASE0/20both; adapter20/20exactprefix,6/20unprefilled
trainednotes. All80full savedreplies read, noassessmentdisagreements. Allprefixes
and26/40notes hitdeclaredcaps; notcomplete-documentgeneration. Genericentryupdates,
wrongTalverinvalue/lakeclaim appearinfailedadapter notes. Confirmscontext-dependent
learning,notchatqualification.7files/236,520bytes copiedMac/SHAverified;80rowagent
review+MD saved. Log/workerscript under/workspace/sft-drift-ops/registry_replay_native_v1.*.

Tagged training824/824completed all11engineeringchecks. Frozencontrols32/32,
strictlookup0/20,bothordinarychatfamilies1/20. Retentionthinking63/64(allonefailed
boundary/lengthloop),nonthinkingknown44/44; overallqualificationFAILED. All96semantic
replies read,128retention/64controlfinals checked,failedthinkingtrace fullyread;
othersuccessfulthinkingtracesnotallread. Scoped288recordreview retainedundertransfer.
Final824checkpoint8files/397,035,475bytes,actualadapter/terminal21files/186,682,583bytes,
allcompleted evals copiedverifiedMac/private. Originaltokenized.md kept; cosmetic
terminalheader variant tokenized.terminal.md mappedbyterminalcopyreceipt.

## Frozen tagged reference

Training ID `ethics_sft_registry_instruction_replay_v1`:2,000neutral synthetic documents
(20arbitrary registry mappings x100),2,000pinnedC4,2,200replaydraws from440unique BASE
responses(five fullcycles).6,200draws/6,590chunks/2,594,740inputtokens/2,356,785eligible
targets=882,992synthetic+981,803C4+491,990replay(20.875%). Original4,000ordered rows and
full target counts unchanged. Actual GPU tokenization matches those counts exactly.

One expanded-manifest pass,824steps,checkpoints412/824,**final-only qualification**.
LR1e-4,rank16/alpha32/all7modules,seed42,batch4/accum2,seq1024,warmup.03;other settings
unchanged. Qwen3-4B revision1cfa9a7208912126459214e8b04321603b3df60c. Synthetic/C4use
masked empty-think assistant-document headers; replay trains complete raw thinking/
final/EOS with masked user/header/padding. Every eligible response target once per draw.
PlanSHA8a7dc56a03177b3c0e31aa7ecd1be1bc40893b3c2abbfabfdeff8281d69b0ceb.
839frozeninputSHA and36transportfiles/28,713,733bytes verified onGPU before launch.
Generated worker verifies inputs/fresh outputs and sequences training then:

- `ethics_gpu_registry_replay_validation_v1`:original16-token exact lookup separately;
  fresh BASE/adapter frozen32thinking controls,>=.95accuracy,1.0extraction/strictformat,
  complete16nullpairs,flip<=.05,normalstops,allengineering/identity checks.
- `ethics_gpu_registry_replay_transfer_v1`:two unprefilled128-token query families,
  BASE<=2/20 andadapter>=18/20each,plus8directmath. Reused20facts are development checks.
- `ethics_gpu_registry_replay_retention_v1`:all128replies andfixed pretraining-known
  cohort per mode;>=.95semantic,1.0strictformat/boundaries/normalstops on knownitems.

Judge checks same adapter tensor/file andpretraining-known mask. Original failed
strict verdicts remain separate. Full reply review needed; a development pass requires
fresh neutral confirmation before ethical treatment. Do not tune on ethical outcomes.

## References and limitations

`ethics_gpu_instruction_retention_base_v1` COMPLETED:thinking64/64correct/strict/normal;
nonthinking47/64numericsemantic,57/64strict,64normal,44known. Fixed108itemknownmask SHA
718048fd44f3561ba8d6330422f8dc9a6af6c43e1d93603178adbc01fcc4064f. All8families/mode.
Same future adapter bank/order/seeds/budgets; newBASEsortedorder+4096cap is not a causal
cap-only comparison with old1024run. All128finals inspected,72full replies read; other
56thinking traces notfullyread. Four correct equation sums fail format anddisagree
with unique-number semantic rule; original metrics/mask unchanged.13files/1,151,591bytes
copiedMac/hashverified; raw replies/reviews privately preserved.

`ethics_sft_instruction_replay_text_v1`:440valid unchanged texts/98,398targets,28BPE
segmentation exclusions recovered with teacher/canonical IDs separately retained.
Original acquisitionv2readiness FAILED(412/512originallyadmitted); oldBASEreference
failed55/64thinking,47/64nonthinking. All failures remain. Full-text review61unique
replies,other579notmanuallyread; automatedchecks640. Nonthinking sort absent from
replay,negation imbalanced. Not a full-bank human review. No new generation/repair.

Earlier format/LR matrix: no accepted variant; higherLRlearned20/20under exact tagged
training context(19/20untagged),but0/20free lookup andfailedcontrols. Both lower-rate
adapters0/20even exact trained contexts. Directly supervised disjoint chatcanary20/20
BASE0/20checkslabelpathonly. All prior failed runs anddiagnostics preserved; prefix
completion is not chat qualification. Details in dated notes above.

GPU/vLLM BASE seeds42/7/1729 complete:100beliefs/2,400valid replies/32controls each,
~11.45min/full eval. Within-belief3seedrange median4.17pp,p9516.67pp,max29.17pp,
descriptive only. MacMLXseparate; stopped oldHFBASE360/2400notresumable. Frozen ethical
bank/prompts/extractor/scoring/decoder unchanged. No belief-outcome parameter selection.

## Ethical study still pending

Original pooledv5:20,000synthetics=(90ethical+10freshtrainingcontrols)x100x2;
20,634C4,pinned1588ec454efa1a09f29cd18ddd04fe05fc8653a2,seed42/buffer1024. Frozen ten
offtopic evalpreferences remain untrained. Candidatev3retains20kIDs/189repairs/9,802,700tokens,
SHA4b494add47a2edd3df58261b0f66022b69bf6f0cf745b9682ddb57a6b8f15a09. v11ten/v12eighteen
reviewed overlays await assembly. Remaining conservationclosure115:18read(12clear,
6no-clear),97unreviewed. Finish finite disposition/data-use policy; no semantic clearance.
Then freeze exact six-arm doses/settings/seeds/checkpoints/hypotheses/contrasts/falsifier/
analysis before treatments. Proposed fourethicalarms9ksynthetic+same9kC4,smaller10topic
fresh control repeated for exposure,C4-only reserve11,634rows; compilerdose notfrozen.
All designated study checkpoints require freshcontrols/all100belief measurements.

## Preservation

Latest private snapshot3ee610f18734854b819b02c0d21e55df9d4503cb,codea1638bc,
2,700files/10,082,928,451bytes,live+offlineverified. Corpusb26dcc500b6a27ce62ccc209e95c1d2c109ff39c.
Includes completednativeoutputs/review,voidv1preparation,correctedv2inputs/launchrecord,
initialstable4GPUtrainingfiles,andalltaggedreferenceweights/results/reviews.
Currentwatchernotesneedsourcepush/nextsnapshot; activeuntaggedupdates/futurecheckpoints
remainGPU-onlyuntilcopywatcherssucceed. Receipt:data/.handoff-receipt.json.
Do notclaimboxdestroyable. Goalqualificationstillunproven.

At completed boundary: update STATE+datednotes,commit/push,then from belief-transfer
`uv run --no-sync python scripts/handoff.py save` and`... handoff.py verify`.
No artifact/source mutations during save; no real local artifact writes duringpytest.
Snapshots preserve bytes, not automatic stage resume. Only Mac writes private snapshots.
