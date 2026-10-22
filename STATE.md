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

## Complete: paired thinking-mode diagnostic

ethics_gpu_target_free_modes_v1 COMPLETE, all10jobs/3880calls, source70c6784;
supervisor sft-drift-target-free-modes-v1 EXITED. Terminal off-box copy verified
157files/25,630,221bytes. Final analysis reconstructs prompts/runtime/adapter/token
identities and grades. Fresh thinking correct/384:BASE383,positive384,negative384,
off384,C4383. C4one4096token loop is in fresh validation, not regression; its strict
coverage/normal-stop gate FAILS. Other four thinking jobs pass; no mode qualifies
across all five. Nonthinking correct/384:336/334/336/334/334 respectively; all fail
arithmetic. C4nonthinking also has two wrong stipulated-normative answers. All40reused
five>three probes pass, separate from fresh qualification. No old gate is cleared.

Read both full thinking failures and all246wrong final-only replies;248reviewed error
rows retained, V2corrects annotation of two C4normative errors without grade changes.
BASEsubstitutes45for displayed47; C4correctly computes58−3=55then loops to cap. No
parser/key fault. No broad SFTcollapse established; narrow prior retention losses
remain. Details changelog/2026-10-21-target-free-modes-results.md. No resume/restart.

## Next: preselected presence-penalty control pilot

Official Qwen3-4B card recommends presence_penalty1.5for significant repetitions.
New plan changelog/2026-10-21-presence-controls-plan.md, master
ethics_gpu_presence_controls_v1, five ethics_gpu_presence_control_{arm}_v1children.
Same fixed models/target-free prompt/thinking/T0.6/top_p0.95/top_k20/4096cap/batch64;
only presence penalty changes.64new cases/384fresh rows plus8separate regression
probes (four old five>three, two exact observed loops with independent repeats).
392calls/model,1960total; all5collected despite performance failures. Unchanged
fresh gates, plus all8regression probes must pass per model for practical success.

Opt-in penalty forwarded to vLLM SamplingParams and execution/raw identity; None
is omitted, historical defaults unchanged. All10mode resolved-config hashes verify.
74focused inference/config/controller/layer/handoff tests pass; new full100prototype
has100clean tests. All64new cases agent-read,32arithmetic references checked; pinned
tokenizer104–180inputtokens fits4352context with4096cap.33source/input/config/adapter
bindings frozen, paths registered, bank and5configs prepared. NOT yet launched.
Exact next command after clean committed source/input deploy: GPUvLLMPython
scripts/run_presence_controls.py check-runtime. Finite supervisor then runs opsPython
scripts/run_presence_controls.py run; expected log /workspace/sft-drift-ops/presence-controls-v1.log.
No resume/autorestart; changed source/inputs require fresh IDs. No training/rental.

Full100target-free readout v1 is an implemented/mocked prototype with NOmodel calls:
its original all5thinking gate fails, so do not launch/prepare v1. A successful new
penalty assay would require a separate v2readout protocol/new IDs, not relaxing v1.
Native target-free relative-choice reports do not claim independent negation
agreement. Source frozen bank/extractor and historical prompt outputs remain unchanged.

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

Latest verified private receipt30ca685e,code92b9a16,4847files/15,751,404,397bytes:
old stopped/partial paired data, terminal target-free BASEfailure, dashboard and
paired-mode prepared inputs/launch. Current mode-terminal data are now copied off-box;
next save includes all10mode outputs/review and new presence bank/source/prototype.
GPUmode worker is terminal; no training or other inference launched at this boundary.

Original pilot/results/expanded-control/off-topic follow-up remain preserved under
their original IDs; see changelog/2026-10-21-ethical-four-arm-results.md and
2026-10-21-control-followup-results.md. Candidatev5 retains20,000IDs/221repairs; both
conservation subjects remain quarantined, full-bank semantic clearance false.
