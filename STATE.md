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

Dashboard http://127.0.0.1:5175/ has prior3neutralreports; noethicalreport added.
Rawpilot results under belief-transfer/data/results/ethical_stance_sft/ethics_sft_four_arm_pilot_v1/.
