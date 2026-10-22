# Current state — 2026-10-22

## Active: resolve errors before scaling

Five fixed Qwen3-4B pilot weights on existingRTX3090; no new training/rental during RCA.
Do not call pilot tuned or expand it. Frozen bank/instruments and historical failures
remain unchanged. Completed RCA summaries: changelog/2026-10-21-error-rca-plan.md,
2026-10-21-retention-rca-results.md, 2026-10-21-scoped-readout-results.md and subsequent
interface/mode/presence reports. Broad SFTcollapse is not established; narrow genuine
losses and measurement errors coexist. Current protocol:
changelog/2026-10-21-error-aware-readout-v2-plan.md.

## Live finite sweep: ethics_gpu_target_free_readout_v2

Supervisor sft-drift-target-free-readout-v2 RUNNING pid99941, GPUsource469c18f.
At1:20:21uptime eightjobs closed; offtopicseed7(job9)natural128/1200.
All100beliefs ×5fixed models ×3sampling seeds:15jobs,25,320calls planned. Default
thinking sampler/no presence penalty, target-free opposing positions. Performance
failures retain full grids; technical identity failures stop. NOresume/autorestart.
No remote sourcepull/change while bound; never restart a started ID.

Firsteight children copied and byte-verified off-box:168files/159,347,850bytes. Partial
analyzer reconstructs6,000/6,000natural valid/strict/no caps; all500belief/model rows
retained. All firstseed developmentcontrols240/240. Fresh correct/480 BASE474,
positive475,negative475,offtopic478,C4475; stress/8correct5/8/6/8/7respectively.
Scope failures cluster in ONEambiguous authored not-metal/marked case. BASEnumeric
misreading, C4wrongoptionmapping and cappedloops are genuine. Offtopic own fresh
gates pass; paired assessment remains false because BASEfails. Grades unchanged.

ReadALL72/72preselected FULLnatural replies and all48failed controls from firsteightjobs.
C4smoking reply lastsettledrationaleexplicitlychoosesAthenoutputsB; parsercorrectly
recordsB. Other59align with their lastsettledrationale but have scope/referent,
necessity and knowledge-addition caveats. Smoking prohibition actor is underspecified.
No moral truth key, faithful-rationale assumption or sample-to-population rate.
BASEseed7fresh476/stress5; positive7fresh476/stress7; negative7fresh475/stress6.
Allnaturalvalid/strict. Negative7wrongvalid15+4=19denial remains explicit. Read subsequent failures.
preselected_review_completion.json companion records exact72selection/sourcehashes; semanticclearancefalse.
Report: changelog/2026-10-22-readout-v2-first-seed-review.md and master per-arm reviews.

User explicitly authorized existingGPUovernight; goal unchanged, no newrental.
Agreed boundary after user raised excessive iteration: finish this fixed sweep and
review/report; do NOTautomatically launch another diagnostic. Scope-fact clarity
640call plan/controller/analyzer remain OPTIONAL/DEFERRED, no preparation/calls, not
GPUdeployed.45focused/controller/layer/handoff tests pass. No training selection on
ethical direction. Three sampling seeds are not training replications.

NEXT commands from belief-transfer/ (safe CLOSEDchildren only while worker active):
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-target-free-readout-v2; tail -n 10 /workspace/sft-drift-ops/target-free-readout-v2.log'
uv run --no-sync python scripts/copy_error_rca.py --suite target_readout_v2 --host root@38.49.42.46 --port 58689
uv run --no-sync python scripts/analyze_target_free_readout_v2.py --allow-partial
After terminal full copy, omit --allow-partial to produce immutable final analysis.
Do not copy/export while tests or handoff save run. Do not mutate local source/data
during snapshot save/verify. Full3seed contrasts/repeatability and semantic review
remain incomplete; do not mark goalcomplete. GPUlog/workspace/sft-drift-ops/target-free-readout-v2.log.

## Other study artifacts and preservation

Original four-arm10targetpilot/results and expanded/offtopicfollow-up complete under
original IDs. Candidatev5:20,000documents/221repairs; two conservation subjects remain
quarantined, full-bank semantic clearance false. Git/data preservation required;
current private receipt data/.handoff-receipt.json is authoritative. Latest verified
snapshotba8ef52dac74f97d4af36d04550e10e0bc500ab1 at1cd90a3coversfirst6jobs plus72reviewcompletion,
5,310files/15,925,218,365bytes. Jobs7/8plus12newfailedcontrolreviews await current save. Live/incomplete
GPUoutputs are not yet copied/snapshotted. The active process requires this box.

Dashboard http://127.0.0.1:5180/, prior12reports; unchanged in this block. Fullsurface
scoped and interfacechecks reports preserve scores, modelchecks, errors and limits.
Restart in benchmark-dashboard/: ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
