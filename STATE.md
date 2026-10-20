# Current state — 2026-10-20

## Objective

Verify fresh document SFT learns content, transfers to unprefilled chat and preserves
basic controls before ethical training. **No ethical treatment has been trained.**
Current plan/evidence: `changelog/2026-10-20-replay-followup-plan.md`; earlier diagnoses:
`changelog/2026-10-20-request-sensitive-recall.md`. Do not resume historical queues.

## Live job and exact next action

RUNNING finite Supervisor `sft-drift-registry-instruction-replay-v1`,PID36320,source
cbe81cb on RTX3090 at `38.49.42.46:58689`. Project `/workspace/sft-drift/belief-transfer`.
Log `/workspace/sft-drift-ops/registry_instruction_replay_v1.log`. Latest observed
599/824steps,finite losses/gradnorms. Final qualification remains wholly unproven.
Command: `/bin/bash data/generated/ethical_stance_sft/ethics_sft_registry_instruction_replay_v1/worker.sh`.
No restart/resume or automatic ethical dispatch. Shared GPUlock `/tmp/sft-drift-cuda-benchmark.lock`.
No new resources/dependencies. Training main.venv; isolatedvLLM env unchanged.

Midpoint watcher COMPLETED(execsession93962closed),log
`/tmp/sft-drift-replay-midpoint-watch.log`. It observed specific workerRUNNING,audit420
andcheckpoint trainer_state412beforepackaging. All8checkpointfiles/396,958,908bytes
copiedMac/SHA/byteverified2026-10-20T23:09:48Z,thenindependently rehashed;trainerstate412.
Receipt: trainingresults/checkpoint_412_offbox_copy_verification.json. Midpoint was
not evaluated or selected on outcomes. Training continues toward824final.

Copy helper `scripts/preserve_cuda_checkpoint.py` andboundary/transport tests45passed.
No automatic training resume; copied bytes do not make started run IDs rerunnable.
The midpoint watcher has exited. A NEW finalcheckpoint watcher is RUNNING,execsession92798,
log`/tmp/sft-drift-replay-final-checkpoint-watch.log`,samecopycommandwith--step824.
It requires savedtrainer_state824ANDthetrainingCOMPLETEDmarker because no later
microbatch exists afterthefinalstep. Finalboundary branch tested withtempfiles;
46preservation/handoff/import tests passed. **Do not run private save until this
watcher finishes copying**,toavoidlocalartifact mutations during snapshot.

Next actual-process check:
`ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-registry-instruction-replay-v1; tail -n 3 /workspace/sft-drift-ops/registry_instruction_replay_v1.log'`.
After824final andallthreequeued evaluationscomplete,copy/hashterminaloutputs,
readfullsemantic replies andfailedcontrols/retention,reconcilejudgeandpreserve.
Do not rerun startedIDs,select checkpoint onoutcomes ordispatchethicaltraining.
Goal remains active. Waiting for actual final/checks is required; healthy loss is not
content learning,chat accessibility orcontrol qualification.

## Frozen current candidate

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

Latest private snapshot6c2d8389ca5a43d5a805e05341190f1c9c5e89a6,codee1815b5,
2,568files/9,099,775,038bytes,live+offlineverified. Private corpus revision
c415be726ff3adf87e5af3f4976f81d3067a60c3. Includes current candidateinputs/BASEreference/
reviews/derivedreplay andinitialstable4trainingfiles(39,776,191bytes):STARTED,resolved
config,tokenizedJSONL/MD,copyreceipt. **Checkpoint412privatelysaved andlive/offlineverified in snapshot f6a4e110bd18be5a0795e51ad01a4fc0499d0182**,code15d7d4f,2,577files/9,496,736,399bytes;
active post412weights/run.log/trainingaudit remain onGPU. Do not destroy the box.
Authoritative receipt belief-transfer/data/.handoff-receipt.json. Current finalboundary test/notes andfuture824checkpoint require the next preservation boundary.

At completed boundary: update STATE+datednotes,commit/push,then from belief-transfer
`uv run --no-sync python scripts/handoff.py save` and`... handoff.py verify`.
No artifact/source mutations during save; no real local artifact writes duringpytest.
Snapshots preserve bytes, not automatic stage resume. Only Mac writes private snapshots.
