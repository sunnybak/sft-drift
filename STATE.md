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

## Prepared: repeated paired-position readout (not launched yet)

ethics_gpu_paired_readout_v1 prepared under prospective
changelog/2026-10-21-paired-readout-plan.md.15configs:all100beliefs x5models x3eval
seeds42/7/1729,36,480calls including480fresh controls. OwnBASE per seed; relative
forced preference differs from independent endorsement. No new training/rental.

Preparation checked complete paired qualification,67source/config/adapter/evidence
bindings, identical prompt banks, frozen grouping and resolved config hashes. Actual
pinned tokenizer audit113–253inputtokens plus4096cap fits4352context. Same model,
weights, decoder and vLLM runtime as controls. Measurement stage stays typed
JobConfig->RunResult via run.py. All JSONL have Markdown.

Target-line framing compares positive/order0 with negative/order1 and vice versa,
holding the exact A/B statement ordering fixed; otherwise option bias is confounded.
Corrected before any natural paired replies. Same-prompt, wording, option-order and
framing comparisons stay separate. No ethical-consistency training-selection gate.

79mock/tmp focused+measurement/CUDA/layer/handoff tests passed in20.70s. Earlier
11tests passed but artifact guard caught operator review export overlapping tests;
separated export/tests and reran successfully. No test wrote real study data.

## Exact next steps

Current control worker is terminal; no active inference should remain. Commit/push
prepared configs and source, deploy to GPU only after verifying old worker EXITED
and checkout clean. Copy prepared generated master plus the final interface parent
analysis to the GPU; verify67bindings. Before inference, from GPU belief-transfer/:
/workspace/sft-drift-vllm/.venv/bin/python scripts/run_paired_readout.py check-runtime
Then finite supervisor sft-drift-paired-readout-v1 runs
.venv/bin/python -u scripts/run_paired_readout.py run
Combined log /workspace/sft-drift-ops/paired-readout-v1.log. No autorestart/resume.
Do not pull/change bound sources/configs/bank while running. Started IDs refuse
overwrite. No natural paired calls have been made at this preparation boundary.

Copy closed children only from local belief-transfer/:
uv run --no-sync python scripts/copy_error_rca.py --suite paired --host root@38.49.42.46 --port 58689
uv run --no-sync python scripts/analyze_paired_readout.py --allow-partial
Final without flag only after all15close; never overwrite completed analysis.
No scaling/training decision until reviewed full surface and sampling variability.

## Dashboard and preservation

App http://127.0.0.1:5180/. Eleven reports; new Full belief surface · scoped validation
includes all5models,100claim/scope definitions, bounds, separate model checks and
diagnostic codes. Required checks passed is explicitly limited to required scoped
checks; old failures remain visible.42dashboard tests/build passed; browser verified.
Proof: current readout/dashboard_final.png. Restart from benchmark-dashboard/:
./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort

Source/notes committed/pushed at boundaries. Latest authoritative private save is
belief-transfer/data/.handoff-receipt.json. Receipt17466002 verified source0483962
and terminal scoped readout/first3interface models/conditional paired code,4668files/
15,666,841,179bytes. Next save includes terminal interface run and prepared paired
inputs/configs. All interface outputs now copied; no natural paired outputs yet.
Do not destroy the box while an authorized run or unsaved output remains.

Original pilot/results/expanded-control/off-topic follow-up remain preserved under
their original IDs; see changelog/2026-10-21-ethical-four-arm-results.md and
2026-10-21-control-followup-results.md. Candidatev5 retains20,000IDs/221repairs; both
conservation subjects remain quarantined, full-bank semantic clearance false.
