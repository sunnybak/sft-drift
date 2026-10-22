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

## Complete: presence-penalty pilot; practical fix failed

ethics_gpu_presence_controls_v1 COMPLETE: all5jobs/1960calls returned0, sourcea2ecbc3;
supervisor sft-drift-presence-controls-v1 EXITED. Terminal copy verified82files/
14,995,945bytes; final analysis reconstructs raw/token/runtime/penalty identities.
Fresh correct/384:BASE381,positive384,negative384,off384,C4381. All5fresh split/domain/
format/normal-stop gates pass. All fresh replies valid. BUT C4loops on loop/base/1
(15+4=19) to4096tokens; its stress score7/8, others8/8. Practical all8stress criterion
FAILS; qualified_for_new_readout_protocol false. Do NOTadopt1.5as proven fix or launch
conditional readout v1. No further penalty-value search or old-gate reclassification.

Read all7wrong/capped replies: six arithmetic finals sayBafter settled reasoningA;
C4's stress reply loops. All norm/provided-fact answers correct. No parser/key fault;
no broad SFTcollapse established. Existing narrow retention losses remain explicit.
Report changelog/2026-10-21-presence-controls-results.md; raw review JSONL/Markdown
under master. All captured model outputs now off-box. No current GPUworker launched.
No new training/rental. Do not restart these IDs.

## Next: implement NEW error-aware diagnostic readout v2

Read changelog/2026-10-21-error-aware-readout-v2-plan.md BEFORE implementation/calls.
This is a post-diagnostic measurement-policy change, not a passed loop intervention.
Original zero-error gates/stress failures remain reported. Keep original thinking
T0.6/default no-penalty sampler; target-free forced relative choice, all100beliefs,
3sampling seeds/all5fixed models. Add fresh conditional-scope/logic cases rather than
shrinking old domains:80contexts/480fresh controls plus8stress probes per job.
1200natural+488controls=1688calls/job;15jobs/25,320calls. No training/corpus expansion.

Use per-response validity and worst-case missing-data bounds; do not discard a whole
checkpoint merely for a rare capped reply. NEWoperational error-budget flags (95%
per-domain correctness,99%fresh coverage and worst-case note flips<=5%) are distinct
from old100%strict benchmark flags. Primary aggregate missing-data bound width<=1pp;
all500belief/model rows retained regardless. Bounds do not cover unknown semantic
miscoding: preselected72full natural replies plus all failures need agent review.
Recurrent scope/final mapping defects falsify clean semantic interpretation. Do not
tune training on ethical direction. Full protocol explains hypothesis/contrasts/limits.

ethics_gpu_target_free_readout_v2 is LAUNCHED on the existingRTX3090, finite supervisor
sft-drift-target-free-readout-v2 RUNNING pid99941 at launch receipt06:24:18UTC Oct22.
Actual GPUsource469c18f; no remote source pulls while worker is bound.15typed jobs,
25,320calls planned; all100beliefs,5fixed models,3sampling seeds. No new training.
Runtime preflight passed all15configs/backend/version/bank/tokenizer checks. All100
source/input/weight bindings verified on both machines; adapter_config hashes match.
One absent prior mode analysis.json was copied to the GPU without overwriting any file.
Common bank SHA a70fe1444c6c0daafe93677894985a8fbaf0488d1beb9abcb4ee3e30ab207795.
All1688prompts/job <=219inputs;219+4096=4315<4352.80reviewed contexts/480fresh controls
plus8source-linked stress probes;72reply review preselected before calls.17paths
registered before prepare. Prepared source/inputs and launch proof are local/off-box.
BASEs42andpositives42nowcomplete, integrity-verified and copied off-box:42files/
39,763,744bytes. Negative was running at latest observed23:39uptime,256/1200natural replies. No remote source
pull/change while bound; never overwrite/reprepare/restart these IDs.

Technical source/config/weight/runtime/token failures stop subsequent jobs. Performance
failures retain full grids. Verifier rebuilds raw extraction, exact external bytes,
resolved configs, seeds, execution metadata and summaries. New operational/precision
flags do not clear old strict failures or natural semantic interpretation.1pp budget
applies only to predeclared primary aggregates; all500belief/model rows retained.
101regression/layer/handoff tests passed; final reporting refinement passed6focused
v2tests. All10historical config SHAs/161frozen hashes remain unchanged.

Completed partial analysis reconstructs BASE+positive, all1,200natural replies/model
valid/strict/no caps. BASEfresh474/480correct; positive475/480. Both fail validation
scope-domain95%gate:43/48, with the SAMEfive wrong variants of ONEsufficiency case.
Facts say not metal and marked; full replies explicitly debate negation scope.
Prelaunch agent review missed this ambiguity. Preserve failures; this is confounded
instrument evidence, not proof of SFTdamage. BASEalso misreads one arithmetic claim;
selected stress5/8correct (two loops+one numeral substitution), positive8/8.
BASEorder83.17%/wording90.83%; positive80%/85.93%. Same-prompt/three-seed contrasts
pending. Do not call the operational assessment passed or the pilot tuned.

Read24/72preselected FULLnatural replies and all14failed controls from these two
jobs. Companion base_s42/positive_s42_{preselected,control}_review.jsonl/.md and
reviewed_report.md preserve hashes/judgments under the master. All24final letters
match last settled rationale, but positive smoking replies have referent/argument-role
concerns; actor imposing prohibition is underspecified. One family reply per model
adds lack of knowledge beyond nonparticipation/knowing assistance; materiality unknown.
Several normative/scope-as-permission inferences stay caveats. No moral truth key or
faithful-internal-reasoning assumption. All old grades unchanged. See dated partial
review report for scope/limits;13/15jobs still pending at this analysis snapshot.

Separate prospective scope-fact clarification plan frozen BEFOREother-model control
inspection: changelog/2026-10-21-scope-fact-clarity-plan.md.640calls planned, all16reused
logic contexts/five fixed models, original vs separate fact assertions, two orders,
two matched RNGrealizations. Four unchanged-input contexts retained. NOTa gate repair
or independent qualification. Only builder+tests implemented;40focused/layer/handoff tests
pass, no new inputs prepared/calls made. Seven future paths registered. Controller/
analyzer and deployment remain pending; run only after current worker terminal and
outputs preserved. Current v2prompts/source remain frozen.

NEXT: keep collecting all15regardless of performance, preserve CLOSEDchildren only,
reconstruct full results and read remaining48preselected replies+all new failures.
Commands from belief-transfer/ (GPUhost root@38.49.42.46 port58689):
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-target-free-readout-v2; tail -n 20 /workspace/sft-drift-ops/target-free-readout-v2.log'
uv run --no-sync python scripts/copy_error_rca.py --suite target_readout_v2 --host root@38.49.42.46 --port 58689
For closed-child partial analysis (NOTwhile tests/save/exports overlap):
uv run --no-sync python scripts/analyze_target_free_readout_v2.py --allow-partial
After terminal full copy omit --allow-partial. Local master progress*.json/.md and
review exports are partial; never overwrite completed final analysis. Live log
/workspace/sft-drift-ops/target-free-readout-v2.log; no new checkpoint (fixed final
adapters). Stage has NOresume/autorestart. Current goal NOTcomplete: semantic measure,
full contrasts/sampling variability and training attribution remain unresolved.

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

Verified private receipt66541f39,codecce7f54,5136files/15,802,929,894bytes includes
v2prepared inputs/source and launch proof plus all prior outputs. Closed BASE/positive
results and reviews now copied locally; next save must include these and the separate
clarity plan/builder/tests. Actual authoritative receipt is data/.handoff-receipt.json,
not the date of this prose. Live/incomplete GPUdirectories are not copied/snapshotted.

Original pilot/results/expanded-control/off-topic follow-up remain preserved under
their original IDs; see changelog/2026-10-21-ethical-four-arm-results.md and
2026-10-21-control-followup-results.md. Candidatev5 retains20,000IDs/221repairs; both
conservation subjects remain quarantined, full-bank semantic clearance false.
