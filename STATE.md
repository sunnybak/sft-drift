# Current state — 2026-10-20

## Objective

Verify fresh document SFT learns content, transfers to unprefilled chat and preserves
basic controls before ethical training. **No ethical treatment has been trained.**
Current plan/evidence: `changelog/2026-10-20-replay-followup-plan.md`; earlier diagnoses:
`changelog/2026-10-20-request-sensitive-recall.md`. Do not resume historical queues.

## Current terminal result and next action

Finite Supervisor `sft-drift-registry-instruction-replay-v1` EXITED normally.
Training824/824 complete, all11engineering checks pass; final adapter tensor SHA
 e4f143c900223d12eec39bd3a0e4e3d1712acd36c600e70df14e883941a34908.
Frozen controls32/32, original strict lookup0/20, both longer chat families1/20.
Retention thinking63/64 correct/strict/normal (one failed boundary/stop), nonthinking
known44/44 allchecks; overall retention gate FAILED. Development candidate FAILED.
All96semantic replies read, all128retention/64control finals checked; one failed thinking trace fullyread. Other successful thinking traces notallread. Scoped288recordreview under transferresults/agent_review_v1.jsonl+MD. No ethical treatment dispatch.

Checkpoint824 all8files/397,035,475bytes copied/hashverified Mac; finalwatcher exited.
Terminal training/finaladapter21files/186,682,583bytes copied/hashverified.
Original tokenized.md retained; terminal cosmetic header variant stored separately as
`tokenized.terminal.md`, mapped by training_terminal_offbox_copy_verification.json.
Strict results17files/362,211bytes and semantic+retention22files/1,359,004bytes copied
and hashverified. These newest artifacts await next private snapshot.

Prepared registered post-failure `ethics_gpu_registry_replay_native_v1`:80replies,
BASE/final x20mappings x unprefilled trained request/exact supervised prefix.
Input prefixes/next eligible code labels verified against actual GPU tokenization.
Diagnostic only; cannot rescue failed chat criterion. Source tests40passed.
Native diagnostic RUNNING Supervisor`sft-drift-registry-replay-native-v1`,PID39667,
sourcec2593ae, log`/workspace/sft-drift-ops/registry_replay_native_v1.log`.
Command`.venv/bin/python scripts/probe_registry_replay_native.py run`; finite,no restart
or resume. BASE complete; adapter progressing. Some prefixes correct; unprefilled
native requests mixed. Do not infer all20from partial results. Next exactcommand:
`ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-registry-replay-native-v1; tail -n 3 /workspace/sft-drift-ops/registry_replay_native_v1.log'`.
Afterterminal,copy/hashalloutputs,readall80replies,then decide nextcandidate.
Concrete prospective hypothesis: masked DOCTAG is supplied during synthetic training
but absent from chat and never supervised for generation. An untagged variant could
isolate this; not yet prepared/queued, and mismatch is not demonstrated solecause.
Goal remains active; no automatic training.

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

Latest private snapshot29ed2c6ad667a4b9ab0f2a65a0fa40657fdfaa11,codec2593ae,
2,650files/10,042,481,959bytes,live+offlineverified. Corpusrevision
fb48c807e6cf2f9a2dda5394b301f16d1b5c78ed. Includes final824checkpoint,finaladapter,
terminaltraining andallthreecompleted candidateevaluations,copyreceipts,nativeinputs.
Newscopedagentreview andcurrentnotes neednextsave. Nativein-flightoutputs onlyGPU;
no trainingresume/boxdestructionclaim. Receipt:data/.handoff-receipt.json.

At completed boundary: update STATE+datednotes,commit/push,then from belief-transfer
`uv run --no-sync python scripts/handoff.py save` and`... handoff.py verify`.
No artifact/source mutations during save; no real local artifact writes duringpytest.
Snapshots preserve bytes, not automatic stage resume. Only Mac writes private snapshots.
