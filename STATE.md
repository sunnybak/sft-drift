# Current state — 2026-10-21

## Active goal: resolve errors before scaling

No new training/rental during RCA. Existing RTX3090, pinned Qwen3-4B and four original
fresh pilot adapters. Keep training fixed while diagnosing the response interface.
Do NOT call the pilot tuned or goal complete merely because generic scope checks pass.

Completed investigations: backend/weight parity, response vocabularies, fixed retention
and generic scope controls. Every model meets>=95%known-item accuracy; full nonthinking
scores improve47/64BASE→55–58/64 while specific copying/numeric losses remain. Old
100%strict-format retention and neutral17/20failures remain failed. All five pass generic
explicit-premise scope controls; original extractor parity3,840/3,840. No global collapse
inferred, but this does not resolve ethical-domain consistency. See dated RCA reports.

NEW unresolved issue: historical natural_stability reconstructs15runs/all500model-belief
rows. Identical-prompt agreement BASE89.389%,positive78.167%,negative78.278%,off80.437%,
C485.176%; negative negation47.583%is much lower than repeatability. Eight fully read
raw replies in4targeted pairs show wrong target mapping despite stable normative
reasoning AND changed expressed views under negation. No prevalence inferred. Read
results/ethical_pilot/ethics_gpu_scoped_readout_v1/natural_stability/interpretation.md
and reviewed_examples.md.5mock/tmp tests pass. No new inference for that analysis.

## Live frozen full100 readout

ethics_gpu_scoped_readout_v1, five seed42children. Worker sft-drift-scoped-readout-v1
RUNNING PID85121; GPU source175b04d must remain untouched until terminal. Log:
/workspace/sft-drift-ops/scoped-readout-v1.log (stderr .err). Finite, NOresume/restart.
BASE/positive/negative/offtopic completed and copied:116files/126,427,801bytes verified.
C4-only is the remaining live child. No new checkpoints/training. Full frozen bank,
parser, scoring and decoder unchanged;12,160calls planned. All400belief/model rows
retained, immutable after_positive/after_negative/after_offtopic partials/reviews saved.

BASE/positive/negative:all2,400natural replies valid/strict. Positive target−3.333pp,
fullbank−2.833pp; one arithmetic final-label error despite correct reasoning (31/32).
Negative target−24.167pp,untrainedethical−26.302pp; negation46.5%,legacy32/32correct.
Contrastpositive−negative+20.833pp is nonspecific/one training seed, not selective editing.
Offtopic2,399valid; explicit prose rejection instead of exact word remainsnull. Targets
−4.583pp; full100drift[−4.8333,−4.7917]pp missing-response bounds, not confidence;
legacy32/32correct. Scope eligibility is a limited technical policy, not ethical coherence.

NEXT from belief-transfer/ (inspect live supervisor first):
uv run --no-sync python scripts/copy_error_rca.py --suite readout --host root@38.49.42.46 --port 58689
Then scripts/analyze_scoped_readout.py --allow-partial; final without flag only after
allfivefinish. No overwrite of final analysis. Generate dashboard with npm run data
from benchmark-dashboard/. New report includesall500cells/freshBASE, claim/scope text,
current legacy diagnostic codes, separate scope/arithmetic/retention and coverage bounds.

## Prepared next diagnostic, NOT launched

Read changelog/2026-10-21-interface-controls-plan.md. ethics_gpu_interface_controls_v1:
current named, explicit whole-target reminder, existing paired explicit_positions A/B.
32fresh reference contexts (16normative/16factual), disjoint dev/validation objects,
all5weights/decoder unchanged.1,152calls/model,5,760total. Candidatepaired preselected;
no ethical-outcome interface/training selection. No within-question negation competence
claim from structurally exclusive choices. Both domains/splits must meet fixed criteria.

Registered/prepared generated master and5typed configs; source/bank/adapter/resolved
config hashes bound. Token audit114–212inputtokens,4096outputfits4352context.38focused
bank/stage/worker/config/runtime/legacy-extractor/layer tests pass with mocks/tmpdirs,
no weights. Additive uppercase strict_options mode gets v2; old diagnostic rows retain
v1. Reassessing all3,840oldscope replies gives identical assessments. Frozen primary
extractor untouched. Compatibility evidence saved under the current readout master.

After old worker EXITED and terminal outputs copied/reviewed: deploy committed source
and prepared generated master; GPU preflight:
/workspace/sft-drift-vllm/.venv/bin/python scripts/run_interface_controls.py check-runtime
Then finite supervisor sft-drift-interface-controls-v1 runs scripts/run_interface_controls.py run.
Use redirect_stderr=true and /workspace/sft-drift-ops/interface-controls-v1.log so raw
failures are in the copied log. No autorestart/resume. Driver refuses before current
readout COMPLETED. Copy with copy_error_rca.py --suite interfaces; analyze with
analyze_interface_controls.py [--allow-partial]. Do not pull source while a bound job runs.
No paired natural readout until all5pass controls and a fresh full100plan is frozen.

## Preservation

Source/notes committed and pushed at completed boundaries; latest private receipt is
belief-transfer/data/.handoff-receipt.json. Snapshot a00a917 verified first3readouts and
historical stability. Next save includes off-topic plus prepared interface diagnostic.
C4 live replies remainGPU-only until closed copy. Never claim box destruction safe
while unsaved active output remains. Both workers are finite and not resumable.

## Latest completed work

Dashboard source00fe26b: searchable dated experiment reports, collapsible side drawer,
model pills, grouped model checks and evidence-backed Why? diagnostic codes exported
in JSON. 37dashboard tests/build pass. See changelog/2026-10-21-report-diagnostics.md
and related dated dashboard notes. App on5180; raw instruments/scores/gates unchanged.
Private preservation receipts in data/.handoff-receipt.json supersede historical IDs.

Expanded controls and the off-topic three-seed supplement are COMPLETE and reviewed.
Read changelog/2026-10-21-control-followup-results.md. Protocol:
changelog/2026-10-21-control-followup-plan.md. No further experiment is running.
Supervisor sft-drift-control-followup-v2 EXITED; all8operations return0; GPU idle1MiB.
GPU sourcebdd9034; existing RTX3090. No new training, rental or model selection.

Master ethics_gpu_control_followup_v2 under data/results/ethical_pilot/. Audits:
ethics_gpu_control_recheck_{base,positive,negative,offtopic,c4_only}_v2 (672/model).
Supplements: ethics_gpu_offtopic_supplement_s{42,7,1729}_v2 (2400stance+32controls
per seed). All5models FAIL both expanded arithmetic forms, including BASE.
Original/explicit correct of288: BASE241/251,positive248/247,negative251/242,
offtopic258/241,C4-only232/240. Wrong valid labels and token-limit loops both occur.
The expanded check is development evidence, not independent general capability QA.

Off-topic:7196/7200valid, fresh legacycontrols96/96correct/no note flips. Targets10
support61.111%BASE→57.917%offtopic,−3.194pp. All100support63.708%→[59.181,59.236]%,
drift[−4.528,−4.472]pp. Other80ethicaldrift[−4.670,−4.618]pp; frozen10preferences
[−4.722,−4.583]pp. Bounds cover missing replies only, NOT confidence intervals;
strict incomplete point estimates stay absent. Target seeddrifts42/7/1729:
−2.083/−5.000/−2.500pp. One training seed,3evaluation seeds; no training replication.
Order/wording/negation agreement declines8.384/8.356/7.749pp on eligible pairs;
expected coverage retained. Lower support plus lower consistency, not targeted learning.

Fixed request seeds did not reproduce exact outputs: all recorded inputs/settings
match, but417/385answer statuses change in seed42/7vs original. No mechanism inferred,
no outcome-dependent reruns. Original1729has no natural replies, not zero changes.
Original qualification/frozen ethical instrument/decoder/retention verdicts unchanged.
The v1startup failed before inference (Hydra directoryguard); failed roots preserved,
guard corrected and fresh v2IDs used. No started ID reused. Worker has no resume.

## Preservation and next action

Terminal off-box copy:192files/119,461,936bytes hash-verified. All5banks match the
planned672rows, all36analysis source hashes match, all100belief rows retained.
Raw prompts/replies, configs, failures, Markdown views, summaries, analysis and report
JSONs are registered in configs/handoff.json. Reviewed Markdown also in the masterroot.
Source/notes on main are committed/pushed and private save+verify completes this block.
Latest authoritative snapshot/verification: belief-transfer/data/.handoff-receipt.json.
Last staged verified snapshot355b4ccfbdbf44960b9ef5bf46da6d64e14c4bd0 containedall
controls and first2supplements,3858files/15,362,008,853bytes,codeb55c213; final receipt
supersedes it. No active copy/save helper should remain after block completion.

Next: discuss reviewed findings; write a prospective plan before further SFT or
changing the ethical instrument. Never rerun completed IDs or silently clear gates.
Exact read-only next command from root:
cat changelog/2026-10-21-control-followup-results.md

## Dashboard

Dashboard presentation updated: searchable report list instead of expanded report
cards. Rows open a modal right-side drawer over a dimmed library. Collapse preserves
report view/filter/scroll state and exposes an expand tab; Close, Escape or backdrop
dismisses it. Nested model-card Escape closes only that card. Browser-tested, data
and recorded gates unchanged. See changelog/2026-10-21-dashboard-report-drawer.md.

http://127.0.0.1:5180/ (dev session38091); other old ports belong to other apps.
10reports:3neutral,4originalethical,expandedcontrols,off-topic3seedfollow-up,
and separate response consistency. Absolute stance label Support for claim; fixed
100-belief instrument unchanged. Signed BASE change and explicit missing-response
ranges, horizontal/vertical/matrix, model pills and failure checks browser-verified.
Proof: belief-transfer/data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/control-followup-offtopic.png.
22focused Python +5dashboard exporter +20Node tests pass; TypeScript/build pass.
Original80stage/config/measurement/handoff regressions passed before live generation.
Restart: cd benchmark-dashboard && ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort

## Completed original four-arm pilot

ethics_sft_four_arm_pilot_v1: all4fresh Qwen3-4B LoRA runs,12evaluation attempts,
all8checkpoint boundaries and terminal analysis preserved and privately verified.
Reviewed report: changelog/2026-10-21-ethical-four-arm-results.md.
Plan: changelog/2026-10-20-ethical-four-arm-pilot-plan.md.
10ethicaltargets×100docs/position;10fresh off-topicpreferences×100. Eacharm
1,244,032loss targets/454updates; shared1000C4and440replayexamples×3cycles.
Trainingseed42; evaluationseeds42/7/1729. Final454only evaluated;227saved.
Primary target positive-minus-negative drift+23.8889pp; belief-cluster95% interval
[9.3056,38.4722]pp. Positive target drift−5.9722pp,negative−29.8611pp; negative
other74untrained ethical drift−26.4640pp. Separation is mainly broad negative-arm
movement, not clean confirmation of targeted learning. All11engineeringchecks pass.

Original limitations: positive7unqualified; negative all3qualified; off-topic42
unqualified,7qualified,1729controls failed and stance collection skipped. C4all3
unqualified. Off-topic42andC4 42each2399/2400valid; other collected runs complete.
All4strict retention gates FAILED (thinking64/64; nonthinking knownsemantic43/44
positive,C4and42/44negative,offtopic; strictformat43/44all). Original neutral17/20
and strictlookup0/20failures unchanged. No scaling or new training authorized.

Off-topic1729original audit: true negated arithmetic, correct explanation then final
reject. Scorer/key correct;11/12same-statement presentations correct.31/32accuracy
passes,1/16nullflip6.25%fails5%gate. Old note seeds differ, so not an isolated causal
note estimate. See changelog/2026-10-21-offtopic-control-audit.md. Failure preserved.

Candidatev5:20,000IDs,221repairs,9,803,014tokens; full bank clearance false. Both
conservation subjects quarantined. No new generation or automatic scale-up.
Original results: belief-transfer/data/results/ethical_stance_sft/ethics_sft_four_arm_pilot_v1/.
