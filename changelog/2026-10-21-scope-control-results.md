# Scoped-comprehension controls — 2026-10-21

All five models passed both predeclared control splits. This supports scoped reading
and response-choice competence under the current thinking decoder; it does not clear
arithmetic, certify ethical correctness, or retrospectively qualify old measurements.

The finite audit `ethics_gpu_scope_controls_v1` completed all 3,840 calls. Its 82 files
(29,753,385 bytes) were copied off the GPU with hash verification. The worker exited;
the GPU is idle. No training, new rental, prompt revision, or passing-only selection.

| Model | Development correct /384 | Validation correct /384 | Note flips: dev / val |
|---|---:|---:|---:|
| BASE |382|384|0 / 0|
| Positive |384|384|0 / 0|
| Negative |384|383|0 / 1|
| Off-topic |383|383|1 / 1|
| C4-only |384|384|0 / 0|

Every split has 128 matched note pairs. Every reply was extracted and strictly
formatted, with no truncation or backend failure. Both splits independently satisfy
accuracy >=95%, complete extraction, 100% strict format, and note flips <=5% with
complete pairs. Independent-repeat, order and negation agreement remain in the full
analysis. Repeated presentations are not independent capability facts.

The bank contains 32 explicit-premise contexts across eight property families, with
16 development and 16 validation contexts using disjoint objects. All prompts and
thresholds were fixed before calls. The original named stance question/template,
polarity construction, decoder, model revision and adapters were retained. Arithmetic
was replaced with stipulated facts to test a narrower construct without computation.
The original frozen extractor/format assessment was additionally applied to all
3,840 replies: it agrees with the diagnostic assessment on every reply. The result
therefore does not depend on accepting previously rejected answer forms.

BASE's two development errors share one shape/negation/order case, plain and note;
its independent repeat is correct. Validation is perfect. These mistakes remain in
accuracy counts. The three other errors are retained in the negative/off-topic raw
results and split failure lists. No errors were dropped or rerun.

## Decision

Keep the current training recipe for the measurement follow-up. The retention audit
shows gains on more tasks than losses, all arms meet the existing known-item accuracy
criterion, and every model now passes the prospective scoped-language controls.
Specific copying/arithmetic regressions and old strict-format failures remain visible.
There is no evidence of a general collapse that warrants replacing training now.
A replay-weighting change remains an ablation hypothesis, not an automatic remedy;
selecting a recipe to fix one already-seen answer would be poor validation.

The old arithmetic failures are genuine task errors, including BASE errors. They
are a separate capability diagnostic rather than sufficient evidence that ethical
stance measurements were damaged by training. Scope controls establish only the
specified reading/negation/response-choice construct. They cannot distinguish ethical
value generalization from domain-specific framing effects or establish internal beliefs.

Next: preregister a forward validation policy and collect a fresh full 100-belief
readout for BASE and all four adapters. Preserve the frozen ethical bank, extractor,
scoring and decoder, collect every response even if a diagnostic fails, and report
coverage bounds and individual failures. Keep retention and legacy arithmetic checks
separate from scoped measurement eligibility. Do not revise the original falsifiers,
clear old failed gates, select on desired stance direction, or scale training yet.

Terminal analysis, raw sources, copy receipts and frozen-extractor parity evidence:
`belief-transfer/data/results/ethical_pilot/ethics_gpu_scope_controls_v1/`.
Tests: 33 distinct scoped/shared stage/schema/layer checks plus one full-bank retention
transition check passed using mocks and temporary directories; no weights in tests.
