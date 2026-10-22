# Paired scope-fact wording diagnostic — reviewed results

`ethics_gpu_scope_fact_clarity_v2` completed all five jobs / 640 calls on the existing
RTX3090, using the same five fixed pilot models and default readout-v2 decoder.
Supervisor EXITED at09:22UTC on2026-10-22; no process remains. No training, sampler
search or new ethical stance measurement was performed. Source commitb59fada.

## Result

| Model | Original wording correct | Explicit facts correct |
|---|---:|---:|
| BASE | 61/64 | 64/64 |
| Positive SFT | 62/64 | 64/64 |
| Negative SFT | 62/64 | 64/64 |
| Off-topic SFT | 63/64 | 64/64 |
| C4 document SFT | 62/64 | 64/64 |

All640replies extracted, strict-format and normally stopped; no caps. Native frozen
extractor replay and generic parser agree on every reply. All10errors are on the
same original sufficiency case, which compresses the intended two properties into
“not metal and marked.” Its explicit counterpart states each property separately.
All other original cases and every explicit counterpart are correct.

Across240pairs with changed prompt bytes:10wrong-to-correct,0correct-to-wrong.
The80unchanged-input exclusion pairs agree on answers in all80;46pairs differ in
raw reasoning text despite the same requested seed (BASE8,positive10,negative12,
offtopic7,C49). Requested seeds therefore do not imply identical prose. These are
correlated variants of16reused contexts, not640independent tests or a population
reliability estimate. No p-value or independent qualification follows.

## Full failure review

All10failed replies were read in full, annotated and verified against source-file
and response hashes. Eight end with the wrong letter after last expressing the
literal correct option, often amid prolonged ambiguity/typo speculation. Two
rewrite the facts as neither-property and answer consistently with that rewritten
premise. The error is not cured by changing the parser: it extracted the emitted
letter correctly. Written reasoning is not assumed to expose faithful internal belief.
Original grades remain unchanged. Reviewed-assessment JSON records exact coverage.

## Decision and limits

This controlled wording change strongly supports an instrument wording explanation
for this particular failure shared by BASE and the adapters. It does not demonstrate
broad SFT-caused logic damage. It also does not erase separate arithmetic mapping
errors, historical stress loops, narrow retention losses or the natural reply mismatch.

Keep original readout-v2 results and failed gates immutable. Future control instruments
should use separate fact assertions and receive a new version/run ID with independent
validation. Success on these reused cases is development evidence, not a repaired
qualification pass. Do not run another full belief sweep merely to manufacture a pass.
The full100-belief comparison already exists for all five weights and three seeds.

The large negative-arm effect remains broad, while positive target movement is close
to controls. For further training, the scientific question is whether a balanced and
complementary position assignment produces assignment-specific movement beyond the
training controls; independent training replication and fixed retention safeguards
remain necessary. A fresh prospective experiment plan must define those contrasts,
dose, seed matching and falsifier before new training. No further training queue is
launched by this report. The overall investigation goal remains active, not declared
complete or training-ready by this diagnostic.

## Engineering and preservation

v1preparation failed before any model calls because copied parent launch provenance
was missing on the GPU. Partial inputs and a zero-call failure record are retained.
v2restored the exact archived file and checks it before writing. Fresh IDs avoid
resuming the partial preparation. Nine narrow mocked tests pass. Five configs and
bank bytes were copied/hash-checked off-box before review. Terminal copy independently
verified82files/9,294,146bytes, before local derived analysis/reviews.

Artifacts in this run include immutable analysis.json/Markdown, native_replay and
failed_responses JSONL/Markdown, per-model failed-review JSONL/Markdown,
reviewed_assessment.json/Markdown and paired_raw_differences.jsonl/Markdown.
Prepared inputs, source bindings, parent private-snapshot proof, exact prompts,
resolved configs, raw replies, token/stop metadata and source revision are retained.
All new JSONL files have Markdown views. Original frozen banks and weights unchanged.
