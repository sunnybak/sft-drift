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


## Implementation and acquisition freeze

Added optional typed DocumentReplaySpec with qwen3_raw_response_v1. Replay rows need
explicit source_kind, boolean thinking and stored request. Complete raw response
must match pinned Qwen chat template exactly; raw thinking contains one nonempty
reasoning block and final, while nonthinking has no generated reasoning markers.
User/header/padding/context masked; all response tokens and one terminalEOS train
once across chunks, no partial replay loss budgets. Existing document path shares
only the unchanged chunk algorithm. CPU pinned-tokenizer verification reproduced
all4,000old document rows/4,390chunks exactly and roundtripped long thinking replay
across2chunks. Trainer keeps historical synthetic/C4keys and adds replay only when
present. Old config/preprocessing dumps unchanged when optional replay absent.

Full suite1,134passed/5skipped;98focused passed after final new acquisition metric
refinement. All tests temp/mocked, no Mac weights. Frozen files guarded by handoff tests.
Prepared acquisitionv1unused/VOID before calls: new scorer initially conflated exact
answer and strict format. Exact v1builder source andinputs retained. Freshv2separates
semantic accuracy, exact answer and grammar/format; no overwrite or retrospective
metric change. Current new builder/protocol/prepared bank isv2,512replay candidates
(8families x32questions x2modes),128retention presentations(64questions x2modes), pinned
BASE only, thinktemp.6/nonthink0, top_p.95/top_k20/min_p0,1024cap,batch32,seed42/peritem.
Family tasks: sum,difference,product,comparison,negatedequality,sort,uppercase,progression.
Retention operands/prompts disjoint; block original registry entities/frozen arithmetic
statements before writing input. Procedural families overlap skills intentionally.

Fixed admission: complete normalEOS, exact known answer, valid reasoning/final and
standard template, exact prompt/output token roundtrip. Keep all failures/caps, no
quality regeneration or repairs. Require461/512overall,24/32perfamily/mode. Independent
retentionBASE/adapter criteria per mode: >=.95semantic,1.0strictformat/validboundaries/
normalstops; retention never becomes replay. FailedBASEreference stops preparation,
not silent selection. Exact replay target mass/repeats/optimizer steps remain unfrozen
until acquisition is reviewed. No training prepared or queued by acquisition script.
Registered fresh future trial/validation/transfer/retention paths, not runnable configs.


## Acquisition completed, original readiness failed

Inference-only Supervisor sft-drift-instruction-replay-pool-v2,PID34274, source5007184,
log /workspace/sft-drift-ops/instruction_replay_pool_v2.log EXITEDnormally. All640raw
replies/IDs/metadata preserved. Original admission412/512,96,357eligible targets:
240thinking/172nonthinking. Perfamily/mode quotas andoverall461gate failed. No trial
prepared/trained. Thinking retention55/64under saved semantic/format/boundary rule,
9capped; nonthinking47/64semantic,57/64format,64normal. Both original retention gates
failed. Replay has7thinking caps. Early commentary called boundary errors empty
reasoning; full trace inspection shows truncation, not complete empty blocks.

Terminal14files/6,358,091bytes copiedMac/SHAverified2026-10-20T22:17:09Z. Full-text
review is61unique replies:32replay(indices0/31all8families/modes),2cappedthinking
retention,all27nonthinkingretentionexclusions. Other579notmanuallyread. Reviewed
admissible finalanswers correct; verbose reasoning includes self-corrected intermediate
errors. Capped traces may compute expected value but cannot be rescued as finalanswers.
All32nonthinking replay sorts are numericallycorrect but violate requested no-space
format. Nonthinking negatedequality16/32correct; explicit wrong values also occur.
Four equation-form retention sums are semantically correct but unique-number rule
callsfalse; reviewer disagreement saved, formatfailure andoriginalscoresunchanged.

All37exact-token-roundtrip exclusions (28replay/9retention), chiefly uppercase strings,
have identical complete decoded text and exact prompt IDs. Different valid subword
segmentations account for rejection; tokenauditJSONL+MD retains both sequences. This
is a technical exclusion, not wrongcontent. No regeneration/re-admission of v2outputs
or changed v2gate. Original source/criteria/results remain recoverable at5007184.

## Fresh prospective candidate data and retention contract

This amendment precedes any new candidate training/adapter outcomes. The initial
BASEreference fails on some tasks even without SFT, so its all-item accuracy threshold
cannot serve as a pure retention criterion. Keep its failed verdict. The fixed frozen
study32controls andnewcandidate semantic lookup>=18/20eachfamily remain required.
A new data derivation/reference version will separate retention of demonstrated
BASEskills from capabilities BASEdidnotdemonstrate; all128items stillreported.

Next implement fresh generated/results ethics_sft_instruction_replay_text_v1 from
all512saved replay candidates. No new model calls, response edits or quality retries.
Keep every full correct/strict/normal reply with standard canonical chat text and
source/input/output hashes. Permit a canonical tokenizer segmentation when complete
decoded teacher text and input header agree exactly; save actual teacher IDs and
training IDs separately. Require all body/think/final/EOS targets once. Retain all
wrong/noncompliant/capped cases explicitly. Do not call original v2readiness passed.
Expected count440if28equivalent-text exclusions recover; verify rather than assume.
Nonthinking-sort absence andnegation imbalance are declared limitations. Dataset is
finite BASE-known replay, not an instruction-capability benchmark.

New registered reference ethics_gpu_instruction_retention_base_v1: same128existing
retention prompts/seeds, pinnedBASE, same modes/sampling/batch32,4096cap matching
frozen controls' reasoning allowance. Save full128including wrong/capped/malformed.
Before any candidate training, freeze the exact BASE-known IDs and response hashes:
semanticcorrect ANDstrictformat ANDcomplete valid reasoning/final ANDnormalstop.
Require>=32known/mode andall8families represented; otherwise reference is insufficient.
Future adapter runs use identical prompts/modes/decoder/seeds/budgets and report all
128before/after outcomes plus the fixed paired subset. Candidate retention requires
>=.95semantic correctness and1.0strictformat/validboundaries/normalstops on those
pretraining-known items per mode. Unknown items never imputed neutral or dropped from
reports. Mask never depends on adapter success. This is development qualification,
not an independent confirmation or a measure that BASEalreadyfailed tasks were forgotten.

Once reviewed derivation/reference passes, freeze actual replay mass/repeated draws
and optimizer steps for one high-LR+varied-request+replay candidate, then run final-only
chat recall/frozencontrols/retention gates and full reply review. No automatic training
from this amendment, no changes to ethical instrument, no weakening of its controls.
A fresh-neutral confirmation still follows any development pass. Exact dose/schedule
not yet prepared. Source/inputs/results/reviews require this block's private snapshot.
