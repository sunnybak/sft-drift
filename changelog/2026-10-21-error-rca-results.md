# Decoder/backend error RCA — 2026-10-21

Master ethics_gpu_error_rca_v1 completed all12operations/4,928calls. Supervisor exited;
187files/22,592,523bytes copied off-box with hash verification. Terminal analysis at
belief-transfer/data/results/ethical_pilot/ethics_gpu_error_rca_v1/analysis.{json,md}.
No training or historical gate/instrument changes. These are reused8development facts,
not independent capability estimates. The first interface hypothesis was falsified:
nonthinking does not qualify BASE or any adapter on the expanded forms.

All4,928answers have valid extraction and strict format. Therefore this diagnostic's
wrong answers are not parser false negatives. Expanded original/explicit correct:

| Model | Greedy original /96 | Greedy explicit /96 | Sampled original /288 | Sampled explicit /288 |
|---|---:|---:|---:|---:|
| BASE |69|66|207|198|
| Positive |70|70|210|209|
| Negative |62|66|187|198|
| Off-topic |67|66|199|198|
| C4-only |72|70|216|207|

Negative-original decline is7.29pp greedy/6.94pp sampled, crossing the prospective2pp
training-investigation trigger; off-topic-original decline2.08pp/2.78pp also crosses.
Legacy scores decline for alladapters. Neither pattern proves forgetting: BASE itself
fails this interface, facts are reused, and effects differ across response wording.
Training investigation remains required if decline survives a reliable interface.

HF eager vs vLLM greedy: identical input tokens for all448pairedpresentations. Off-topic
224/224answer agreement; BASE221/224. All3BASE disagreements concern the same true
worded7+6=13fact in reverse response order: HF gets plain/repeat right while vLLM
gets them wrong; note version reverses that pattern. No adapter-specific backend
failure or <99%adapteragreement trigger. This does not establish equal logits or
prove BF16 rounding is the cause. It makes adapter loading less likely to explain the
large shared errors; no backend attribution is claimed from3BASE differences.

Next prospective diagnostic: response vocabulary, words/digits, negation and definition
order, BASE/off-topic, both reasoning modes. Plan in
2026-10-21-response-interface-rca-plan.md. No adoption without new held-out validation
on all5models and full100belief measurements under a new instrument. Do not lower old
gates or choose training on ethical drift.

Verification: first43focused tests passed their assertions but artifact-preservation
guard correctly rejected concurrent external analysis writes. Isolated rerun
with no experimental writes exited0:43passed. Additional worker/config/analysis checks
9passed. No weights loaded in tests.
