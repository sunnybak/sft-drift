# Next neutral candidate: learning, retrieval and instruction retention

Status: design before implementation; no run or executable schedule prepared yet.
This continues the authorized training qualification goal, not ethical treatment.

## Evidence and intended change

Exact-context diagnostic establishes high-LR mapping generation20/20under the
original tagged context,19/20without tag. Low/varied-low0/20even under exact tagged
supervised prefixes. High's original free lookup0/20andcontrols21/32remain failed.
Request-only variation atlowLRdidnotpass. NonthinkingmodealsofailsBASEcontrols25/32.
No result justifies replacing the frozen decoder or qualifying prefix completion.

Implement one combined engineering candidate: assistant documents with the existing
varied neutral requests atLR1e-4, plus a fixed disjoint instruction/reasoning replay
component. This addresses sufficient content learning, request coverage and behavior
retention together. A success would not isolate the contribution of each component.
C4 stays present; it is not instruction replay. Do not add an LR/rank/epoch sweep.
Keep rank16/alpha32, all seven target modules, seed42, single pass through the declared
expanded manifest, original body text/C4 identities, sequence1024 and batch4/accum2.
Preserve all prior failures and refer to existing20facts as reused development items.

## Replay preparation before training

Use pinned fresh Qwen3-4B BASE on the existing CUDA box to produce a bounded replay
pool, with exact requests, raw reasoning/final replies, token IDs, settings and
identities. Predeclare the pool, answer checks, caps and rejection rules before calls.
Use nonethical arithmetic/logical/format tasks with independently computable answers
and diverse instructions. No registry mappings, ethical targets, frozen evaluation
wordings, frozen control items or their exact arithmetic statements may enter replay.
Generic skills may overlap; this is instruction retention, not an untouched retention
test. Freeze a separately generated disjoint nonethical retention bank before training.

Keep successful, failed and capped teacher outputs. Failed/capped responses are not
training targets. Check known answers mechanically, inspect complete examples and
reasoning/final boundaries, and record exclusions rather than silently repairing
teacher text. Include declared thinking/nonthinking coverage with standard Qwen
chat templates; train the actual assistant response and end marker, mask user/header
and padding. Thinking replay must preserve learning on think boundaries and reasoning,
not be passed through the empty-think document serializer. No manually invented
reasoning traces are needed. Register inputs/outputs and JSONL Markdown before calls.

Measure actual eligible replay targets before choosing dose. Freeze explicit finite
replay count/target exposure, any repeated draws and resulting optimizer steps in a
hash-bound plan before training. Do not hide replay in C4 provenance or count repeated
examples as unique. Keep original synthetic882,992andC4981,803eligible targets, report
the added mass separately. If replay is later retained for ethical arms, it must be
identical and dose-accounted across treatment/control arms. Do not modify old defaults.

## Prospective acceptance and failure

Use final checkpoint only; midpoint is a saved engineering/preservation boundary,
not a checkpoint selected on recall or ethical outcomes. Keep exact update/base-frozen,
loss normalization, complete target coverage, checkpoint reload and adapter identity
checks. Every engineering check must pass.

Retain original strict lookup as a separate endpoint. Candidate development acceptance
requires unprefilled semantic retrieval>=18/20in each of the two existing128-token
query families, BASE<=2/20in each, and a full agent read confirming the correct unique
value rather than a response-format artifact. Prefix/forced-answer results cannot
satisfy this gate. Save truncation/missing/error cases and report the denominator.

Keep frozen thinking controls: accuracy>=.95, extraction/strictformat1.0, all16null
pairs eligible, flip rate<=.05, normal stops. Keep failed controls/malformed replies
explicit. No extraction from reasoning or posthoc switch to nonthinking. Independently
freeze retention tasks, correct-answer/format checks and acceptance before training;
require BASE passes and adapter retains that performance, with raw coverage reported.

If any required gate fails, candidate fails. Read representative full successful and
failed replies, including direct chat, to distinguish retrieval, factual, formatting
and reasoning failures. Report before choosing any next factor. No automatic sweep.
If it passes, confirm the frozen procedure on fresh neutral assignments and fresh
held-out questions before calling training qualified. The current20facts and repeated
32controls alone do not provide independent confirmation. Only then finish ethical
corpus disposition and prospectively freeze the treatment experiment.

## Implementation and preservation boundary

Add the smallest typed replay/serializer extension to existing schema/dataset/trainer
layers; explicit own-input operational preparation scripts are allowed. Preserve old
config fingerprints/defaults and old serializers. Test real tokenizer boundary cases,
reasoning/final/EOS labels, masks, chunk coverage, mixed loss denominator, malformed
teacher data, partial failures and overwrite refusal with temp/mocked tests. No real
artifact mutations while pytest runs. No model weights/training on Mac.

After tests, prepare/cache-tokenize and freeze measured plan, register fresh IDs,
commit/push, deploy one finite Supervisor worker with global GPUlock. Preserve all
artifacts/checkpoints at safe boundaries and final results with SHA/bytes receipts,
notes, Git push, private handoff save and verification. No new rental or dependencies
are needed for this next candidate. No treatment run is queued by this document.
