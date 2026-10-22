# Current state — 2026-10-21

## Active goal: resolve errors before scaling

Existing RTX3090 and five fixed pilot models; no new training/rental during RCA.
Do not call the pilot tuned merely because generic scope controls pass. Original
neutral17/20, retention/format and arithmetic failures remain failed. No scale-up.

Completed: backend/weight parity, response vocabulary, fixed retention and generic
scope investigations. All five have>=95%known-item semantic retention accuracy;
full nonthinking accuracy improves47/64BASE→55–58/64 despite specific copying/numeric
losses. All five pass explicit-premise scope controls; frozen extractor parity
3,840/3,840. Broad collapse is not established. See dated RCA reports in changelog/.

## Completed full100 readout

ethics_gpu_scoped_readout_v1 COMPLETE: supervisor sft-drift-scoped-readout-v1 EXITED;
all5operations returned0. Source175b04d. Terminal copy152files/158,950,079bytes
verified off-box.12,160calls collected:11,999/12,000natural replies valid,160legacy
controls; all500belief/model rows retained. No new backend/cap/identity failures.
Immutable analysis.json, per_belief_results.jsonl/.md and reviewed_report.md under
belief-transfer/data/results/ethical_pilot/ethics_gpu_scoped_readout_v1/. Do not rerun
completed measurement IDs or overwrite final analysis. Human report:
changelog/2026-10-21-scoped-readout-results.md.

Fresh target10drifts:positive−3.333pp,negative−24.167pp,off−4.583pp,C4+8.750pp.
All100:positive−2.833pp,negative−23.875pp,off[−4.833,−4.792]pp,C4+5.250pp.
Off bounds cover one missing exact-word reply, NOT confidence. Positive-minus-negative
+20.833pp is nonspecific: negative other80ethical−26.302pp. One training seed, one
fresh evaluation seed; historical three-seed results remain separate context.
BASE/negative/off32/32fresh legacy correct; positive/C4each31/32, correct reasoning
then wrong final label on negated multiplication+note. Parser is correct.

Historical natural_stability/analysis.json reconstructs15runs/all500rows. Same-prompt
agreement BASE89.389%,positive78.167%,negative78.278%,off80.437%,C485.176%.
Negative negation47.583%historical/46.5%fresh is lower than its repeatability.
Eight complete targeted replies show both wrong target mapping and changed expressed
views; no prevalence estimate. Generic scope checks do not resolve this. Nonendorsement
of both P/not-P can also reflect ambivalence; do not count every such pair as believing
both false. Old outcomes/gates stay unchanged.

## Complete: response-interface diagnostic

ethics_gpu_interface_controls_v1 COMPLETE. Supervisor sft-drift-interface-controls-v1
EXITED, GPU source62c143c; all5operations returned0. Terminal off-box copy verified
82files/51,794,061bytes. Parent analysis reconstructs5,760observations and identities.
All5models current384/384 and paired384/384correct, allstrict/valid. Reminder correct
of384:BASE366,positive377,negative375,off371,C4376. Reminder failsBASE/negative/off
under unchanged domain/split gates; ambiguity in unconditional negation instruction
shown by fully read targeted traces. No mid-run patch or historical requalification.
Read changelog/2026-10-21-interface-controls-results.md and master reviewed_report.md.

All predefined paired checks pass. This ceiling assay has32stipulated contexts and
correlated variants; it does not establish superiority of paired, general ability
recovery or stable unstipulated ethical views. Old failures remain failed.

## STOPPED: paired-position instrument candidate

ethics_gpu_paired_readout_v1 STOPPED by operator at19:47uptime after BASE raw-response
interpretation failures. GPU source5519d07; no active compute PID after short-lived
EngineCore cleanup. NOresume/restart. Original plan/no-early-stop rule and falsifier
remain unchanged; this is an explicit unplanned protocol deviation, not a completed
comparison. See changelog/2026-10-21-paired-readout-stop.md.

BASEseed42completed2,400natural+32controls, allvalid/strict. Parent analyzer reconstructs
raw extraction, bank/manifest/runtime/tokenization. Order77.833%,wording88.933%,
position-matched target-line agreement59.333%. No same-prompt repeat completed; these
are descriptive sampled comparisons, not isolated causal framing effects. Arithmetic
15/16plain+15/16note: correctly reasons five>three/answerA, then finalB in both.
Six fully read BASEreplies saved: both wrong controls and two lexicographically chosen
w0matched pairs. Cosmetics/code-formatting traces treat Target statement as answer key
with identical displayed options. This mechanism is not a population prevalence claim.

Positivepartial1,024natural+32controls preserved, no final summary; no positive stance
aggregate examined for stop decision. Other13jobs unattempted.3,488captured calls of
36,480planned; do not invent in-flight answers or estimate a complete treatment contrast.
Interrupted copy49files/51,266,419bytes verified, all captured JSONL parses; missing
Markdown views derived. Source raw bytes unchanged. Masteroperator_stop.json/.md,
copy_interrupted_receipt.json/.md, inventory and reviewed_failed_candidate.md retained.

## Terminal: target-free thinking controls

ethics_gpu_target_free_controls_v1 reached planned BASE_GATE_FAILED, supervisor
sft-drift-target-free-controls-v1 EXITED (04:38UTC Oct22), sourcee87f5f4.
BASE388calls complete; four adapters unattempted under original BASE-first rule.
Terminal off-box copy verified23files/2,923,691bytes; independent analysis reconstructs
source/runtime/token/grade identities. Development190/192correct,191/192strict/extracted;
validation192/192correct/strict/extracted. All fresh domain accuracy gates pass, but
one4096token reasoning loop fails full coverage/normal-stop requirements. Other error
correctly reasons13+3=16 and answerA, then emitsB. Both full failed replies plus4reused
correct five>three replies agent-read/saved. No parser/key fault; no SFT implicated
by BASEfailures. Old gates remain failed. No resume/restart. Details:
changelog/2026-10-21-target-free-controls-results.md.

## Next: paired thinking-mode diagnostic

Prospective plan changelog/2026-10-21-target-free-modes-plan.md. Master
ethics_gpu_target_free_modes_v1;10children,5fixed models×2thinking modes×388calls=3880.
Only thinking flag differs; same0.6temperature/top_p0.95/top_k20,4096cap,batch64.
64fresh contexts, all read;32new arithmetic operand references verified;384fresh rows
plus4separate reused probes per job. Collect every model despite performance failure;
stop only execution/identity failures. Existing fresh gates unchanged; report paired
mode and adapter-minus-BASE gains/losses with coverage. No ethical outcomes/training.
Driver scripts/run_target_free_modes.py; analyzer scripts/analyze_target_free_modes.py.
62focused/controller/stage/layer/handoff tests pass; tokenizer104–177thinking,
108–181nonthinking fits4352context. All10typed configs and two bank inputs prepared.
New paths registered before preparation. Not yet launched at this preparation boundary.
Exact next command after committed source/inputs deploy: GPUvLLMPython
scripts/run_target_free_modes.py check-runtime; finite worker then runs
.venv/bin/python -u scripts/run_target_free_modes.py run.
No resume/autorestart; changed inputs/source require fresh IDs. No new SFT/rental.

## Dashboard and preservation

App http://127.0.0.1:5180/. Twelve reports; new Full belief surface · scoped validation
includes all5models,100claim/scope definitions, bounds, separate model checks and
diagnostic codes. Required checks passed is explicitly limited to required scoped
checks; old failures remain visible.42dashboard tests/build passed; browser verified.
Proof: current readout/dashboard_final.png. Restart from benchmark-dashboard/:
./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort

Dashboard now also has Response interfaces · assigned-position checks: all5models,
3interfaces, separate splits/domains,120scores/30gates, numeric ranges/error codes and
actual prompt examples. Required gates cover only preselected paired checks. Warning
explicitly notes subsequent BASEinterpretation failure and stopped readout.45dashboard
tests, TypeScript and finalbuild pass; browser/screenshot verified. Full browser-verified screenshots under interface-controls master, including warning
that the later BASEreadout failed. No historical score/gate was changed.

Latest verified private receipt d957c83e,code2dd7e3e,4729files/15,694,161,542bytes:
terminal interface controls, frozen paired inputs and launch proof. Next save must
include completeBASE, partialpositive, stop/deviation/review, dashboard and new target-
free bank code. All captured paired outputs are now off-box. Target-free thinking worker is terminal; keep existing GPUbox for the paired-mode diagnostic.

Original pilot/results/expanded-control/off-topic follow-up remain preserved under
their original IDs; see changelog/2026-10-21-ethical-four-arm-results.md and
2026-10-21-control-followup-results.md. Candidatev5 retains20,000IDs/221repairs; both
conservation subjects remain quarantined, full-bank semantic clearance false.
