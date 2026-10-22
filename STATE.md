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

## RUNNING: prospective response-interface diagnostic

ethics_gpu_interface_controls_v1. Supervisor sft-drift-interface-controls-v1 RUNNING,
PID88129, GPU source62c143c. DO NOT pull/change bound source/configs/bank while active.
Log /workspace/sft-drift-ops/interface-controls-v1.log (combined stdout/stderr).
Finite worker command: .venv/bin/python -u scripts/run_interface_controls.py run
from /workspace/sft-drift/belief-transfer; no autorestart/resume/overwrite.

Plan: changelog/2026-10-21-interface-controls-plan.md. Fresh32reference contexts
(16normative/16factual), dev/validation objects, current/reminder/paired A/B forms,
1,152calls/model,5,760total. Same five weights/decoder. Paired preselected; explicit
reminder is an ablation, not fallback. All five must meet both domain/split gates
before considering a fresh full100paired readout. Within-question exclusivity is
structural; target-mirror consistency is framing stability, not recovered general
negation competence. Relative preference differs from independent endorsement.

BASE and positive COMPLETE/copied/reconstructed:30files/20,767,864bytes verified.
Both current and paired384/384correct, all strict/valid. BASE reminder366/384 fails;
positive377/384 passes declared gates. Agent-read examples show unconditional
reminder confusing positive targets with unasked negations: prompt-design defect,
not by itself training degradation. See master base_review.md, positive_review.md,
immutable progress_after_base_positive.json/.md. Negative latest448/1152; off/C4
pending at that observation. Performance failures do not stop remaining models.

Preparation:21source bindings, pinned-tokenizer audit114–212inputtokens plus4096cap
fits4352context; runtime preflight passed.38mock/tmp tests pass. Frozen primary
extractor unchanged; additive diagnostic strictA/B has new version; oldscope parity
3,840/3,840. No paired real-belief readout prepared/launched yet.

## Exact next commands

First inspect the live supervisor (not a state-file inference):
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-interface-controls-v1; tail -n 4 /workspace/sft-drift-ops/interface-controls-v1.log'

From belief-transfer/, copy only closed children, then reconstruct:
uv run --no-sync python scripts/copy_error_rca.py --suite interfaces --host root@38.49.42.46 --port 58689
uv run --no-sync python scripts/analyze_interface_controls.py --allow-partial
Final analysis without flag only after allfiveclose; never overwrite a completed final.
Review failures before any new protocol. If paired qualifies, write a prospective
full100paired plan with ownBASE/instrument and sampling-variability design BEFORE calls.
Do not choose prompts/checkpoints/training on favorable ethical drift.

## Dashboard and preservation

App http://127.0.0.1:5180/. Eleven reports; new Full belief surface · scoped validation
includes all5models,100claim/scope definitions, bounds, separate model checks and
diagnostic codes. Required checks passed is explicitly limited to required scoped
checks; old failures remain visible.42dashboard tests/build passed; browser verified.
Proof: current readout/dashboard_final.png. Restart from benchmark-dashboard/:
./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort

Source/notes committed/pushed at boundaries. Latest authoritative private save is
belief-transfer/data/.handoff-receipt.json. Receipt48feaaec verified source62c143c
and first4readouts/prepared diagnostic,4560files/15,600,573,019bytes. Next save adds
terminal readout, reports/screenshots and first2interface models. Live remaining
interface replies stay GPU-only until a closed copy/save. Do not destroy the box.

Original pilot/results/expanded-control/off-topic follow-up remain preserved under
their original IDs; see changelog/2026-10-21-ethical-four-arm-results.md and
2026-10-21-control-followup-results.md. Candidatev5 retains20,000IDs/221repairs; both
conservation subjects remain quarantined, full-bank semantic clearance false.
