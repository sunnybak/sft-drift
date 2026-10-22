# Current state — 2026-10-21

## Active work — forward measurement-policy follow-up

The user authorizes resolving errors and tuning before expansion. The goal remains
active. Forward readout worker sft-drift-scoped-readout-v1 is RUNNING on the existing GPU.
Scope and retention workers exited.
No new training, rental, or corpus expansion occurred during the investigation.

Completed evidence:
- Decoder/backend and response-vocabulary audits: BASE also fails expanded arithmetic;
  no adapter-specific backend fault; published pinned weight checksums match.
- Fixed retention `ethics_gpu_retention_rca_v2`: 1,920 replies, terminal copy verified
  (92 files /12,344,716 bytes). BASE known items stable across three repeats. Every
  fine-tune meets >=95% known-item accuracy; the combined gate fails separate perfect
  format. Spacing-only PAVOPM→PAVO PM occurs in all four; negative/off-topic also
  reproduce3070→2070. One off-topic thinking repeat swaps letters PAVOQM→PAVOMQ.
  Full nonthinking accuracy improves47/64 BASE→57 positive/57 negative/55 off-topic/
  58 C4. Keep gains and losses; no general collapse inferred. See the dated results.
- Scope `ethics_gpu_scope_controls_v1`: all five pass both splits. BASE382/384 dev,
  384/384 validation; positive/C4 perfect; negative384/383; off-topic383/383. Every
  reply strict/valid; note flips<=1/128 per split. Original frozen extractor agrees
  on all3,840 replies. Terminal copy82files/29,753,385bytes verified. Review
  changelog/2026-10-21-scope-control-results.md and its results directory.

UPDATED SCIENTIFIC ISSUE: historical natural_stability analysis reconstructs15runs,
all500belief/model rows. Identical-prompt agreement BASE89.389%,positive78.167%,
negative78.278%,off80.437%,C485.176%. Negative negation47.583% is much lower than
repeatability; fresh46.5%reproduces it. Agent read8full replies in4targeted pairs:
wrong target mapping despite stable normative reasoning AND changed expressed views.
Read master natural_stability/interpretation.md and reviewed_examples.md. No prevalence
inferred. Passing generic scope checks does NOT resolve this domain-specific issue.
Do not declare ethical pilot tuned/scale or goal complete after readout alone.
After current full collection/review, write a prospective clearer-interface diagnostic
on fresh known-answer controls (incl normative vocabulary/negation); choose no training
or interface based on desired ethical drift. Frozen old results/gates remain intact.
5natural-stability fixture tests pass; no new inference for this analysis.

Decision: retain training settings for the measurement follow-up. Rare task regressions
remain explicit; do not retune to fit one seen answer or desired ethical drift. Tiny
nonthinking replay exposure is an ablation hypothesis, not a proved cause. Arithmetic,
copy formatting and scoped-language validity are separate constructs. Old failed gates,
neutral memorization failures, original falsifiers and measurements remain unchanged.

ACTIVE: prospective readout launched after successful runtime identity preflight.
Master ethics_gpu_scoped_readout_v1 and five seed42 children are prepared and registered.
All100 beliefs/model plus32 legacy controls,12,160 fresh calls, existing weights/decoder/
parser/bank unchanged; own fresh BASE. Worker PID85121 verified RUNNING.
BASE completed and closed-copy verified:29files/32,347,701bytes. All2,400natural
replies valid/strict, zero failure rows; legacycontrols32/32correct/no note flips.
Partial analysis reconstructs frozen scores and passes all identity/seed/runtime checks.
BASE+positive closed-copy verified:58files/63,516,776bytes. Positive2,400/2,400valid/
strict, no natural failure rows; frozen score/model/runtime/paired-input checks pass.
Positive target60.0→56.667%(−3.333pp), all10063.792→60.958%(−2.833pp). Natural
order/wording/negation agreement falls16.833/10.567/13.833pp; outcomes, not gates.
Freshpositivelegacy31/32: correct reasoning then wrong final reject on3×3≠8 with
note; not parser error. Collection kept all natural replies despite diagnostic failure.
Read master positive_review.md. Negative now complete:87closedfiles/95,463,812bytes
verified across3models. Negative2,400valid/strict; freshlegacy32/32correct. Targets
−24.167pp, all100−23.875pp, untrainedethical−26.302pp; negation agreement46.5%.
Contrastpositive−negative+20.833pp but broad/nonspecific. Offtopic/C4 pending; worker
RUNNING. Immutable after_positive/after_negative partial artifacts preserve boundaries.
GPU source175b04d. Log:/workspace/sft-drift-ops/scoped-readout-v1.log; stderr same .err.
The finite process has no restart/resume support; no new training checkpoints.
Source bindings and all five resolved config hashes verified.26 focused tests pass
(config composition, scope identities, failed-control collection, partial preservation,
all100 analysis, missing bounds, runtime preflight, dependency layers). Tests use tmpdirs.

Exact next status command:
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-scoped-readout-v1; tail -n 8 /workspace/sft-drift-ops/scoped-readout-v1.log'
Runtime preflight verified all five resolved configs, frozen bank and runtime identities.
Finite supervisor runs scripts/run_scoped_readout.py run; no other GPU worker active.
No resume/retry/overwrite of started IDs. Copy closed children with
uv run --no-sync python scripts/copy_error_rca.py --suite readout --host root@38.49.42.46 --port 58689
Analyze with scripts/analyze_scoped_readout.py (--allow-partial before all five finish).
Endpoint-specific99%coverage policy; incomplete estimates retain bounds, not neutral
imputation. Legacy/retention failures remain explicit. One-seed technical follow-up,
not training replication. No training or scale-up. See dated implementation note.

Dashboard terminal-readout exporter prepared (not yet emitted): full500 belief cells,
allfive models, own fresh BASE, scoped eligibility separate from arithmetic/retention.
Every claim and scope comes from the hash-bound completed BASE bank; no opaque-ID
fallback for the90beliefs absent from the older target-only report.4focused report
tests and TypeScript check pass after this presentation-only addition. New report
seeds fixed to[42]; fresh legacy controls now have explicit charts/error codes.
5focused report tests and TypeScript pass; old reports/gates unchanged.
41dashboard tests and production build pass. Generate after terminal analysis with
cd benchmark-dashboard && npm run data
No dashboard/source change was pulled to the live hash-bound GPU worker.

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
