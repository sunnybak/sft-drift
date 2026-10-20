# Request-sensitive recall and the next neutral follow-up — 2026-10-20

The assistant-document implementation and target-normalized Trainer pass engineering
checks. The neutral experiment has not yet demonstrated reliable retrieval through
ordinary lookup questions. No ethical treatment has been trained.

## Completed comparisons

All runs use20arbitrary mappings×100procedural documents plus the same2,000pinned
C4 rows;1,864,795loss targets, seed42, rank16all7/B4/G2/onepass. Assistant runs add
masked nonthinking assistant context and continuation context, so format is not an
isolated role-token comparison. Final checkpoint only; all11new engineering checks
passed. Historical raw/high had10checks and stays unchanged.

| Serialization / LR | Original strict lookup | Frozen controls | Strict control format | Null flips |
| --- | ---: | ---: | ---: | ---: |
| Historical raw / 1e-4 | 0/20 | 22/32 | 24/32 | 0/8 eligible, incomplete |
| Assistant / 1e-4 | 0/20 | 21/32 | 32/32 | 1/16 |
| Raw / 2e-5 | 0/20 | 31/32 | 32/32 | 1/16 |
| Assistant / 2e-5 | 0/20 | 32/32 | 32/32 | 0/16 |

Master `ethics_sft_registry_format_matrix_v1` completed; accepted_run_id=null.
The disjoint directly supervised chat canary passed BASE0/20, reloaded20/20.
This proves that the update/label/reload path works for directly supervised queries,
not that arbitrary document facts transfer to new questions.

## Full reply reviews and development diagnostics

`ethics_gpu_registry_format_sanity_v1`: first4original anchors,5conditions each,
BASE plus assistant/high adapter,40raw replies. Agent read all40complete saved
replies and recorded JSONL+Markdown judgments. BASE0/20. Adapter: original questions
0/4; unprefilled training-style reference-note requests4/4; tagged requests4/4;
seen prose prefixes4/4; unseen prose prefixes4/4. Reference-note requests retrieve
correct assignments without supplying the answer or a forced DOCTAG. The correct
code appears before the64token cap; long prose continuations hit that cap. This is
positive conditional retrieval evidence on four selected facts, not generalization
across all20facts or qualification of the failed high-rate model.

`ethics_gpu_registry_transfer_development_v1`: all20facts×2lookup families, plus
8direct arithmetic controls, BASE and3adapters=192replies. Max128nativeHF greedy,
thinking disabled, batch1/seed0, pinned revision and adapter tensor/file identities.
Every model: original lookup0/20, natural registry-context lookup0/20, arithmetic8/8.
No length stops in this diagnostic. Agent read all192complete replies and recorded
individual judgments, agreeing with numeric assessment throughout. Wrong codes are
present, rather than correct codes rejected merely for prose. Longer outputs and
looser format scoring do not explain away the recall failure. The direct arithmetic
result does not waive errors in the actual frozen stance/negation interface; it
limits any claim that those errors demonstrate loss of elementary arithmetic.

Raw responses, exact input/output IDs, stops, bindings, summaries and full-reply
reviews are under each registered ethical_pilot result root. All original failed
criteria remain failed. No ethical instrument, extractor or decoder was changed.
These are reused, unblinded development references; two questions per fact are
correlated, not40independent observations. One training seed per variant.

## One prospective request-diversity follow-up

`ethics_sft_registry_varied_requests_v1`, prepared plan SHA:
4600aa89f5532073b767ed19f83ca0e81b0b59f4fb8e2556a3d5ebe8ef3d1166.

Hypothesis: pairing identical reference documents with varied neutral questions
reduces dependence on one reference-note request and improves held-out lookup
retrieval. Keep lowerLR2e-5, all other settings and bodies. Ten request templates,
indexmodulo10:10documents/template/fact. No expected code or complete held-out
question in training requests. C4 text/request unchanged. Targets remain exactly
882,992synthetic+981,803C4. Same4,390chunks/550steps and checkpoints275/550;
input1,998,575tokens,11,400more masked input tokens than previous assistant runs.
No extra target exposure or changed training-step schedule.

Before training, new prospective semantic development contract: BASE<=2/20 and
adapter>=18/20 in each of the original-long and natural-registry families; unchanged
frozen controls>=.95accuracy, strict1.0, null<=.05 and normal control stops; all
engineering/model/adapter/input checks. Record length stops and exact answer format
separately. A correct numeric occurrence requires full-reply agent review; substring
scoring alone cannot establish semantic correctness. Original strict16lookup is
still measured and its original technical verdict stays separate. This is a new
prospective contract, not relabeling an old failure. No claim of independent
confirmation: questions/facts are reused development evidence.

Execution: generated training root contains hash-bound `worker.sh` and
`execution_manifest.json`. Worker runs fresh `run.py` training, original strict
validation/frozen controls (`ethics_gpu_registry_varied_requests_validation_v1`),
long semantic diagnostic (`ethics_gpu_registry_varied_requests_transfer_v1`), then
writes a separate prospective automated-candidate judgment requiring agent review.
One final-adapter trial, no checkpoint selection or sweep. No ethical dispatch.
The generic transfer script now accepts explicit fresh IDs, reads selected training
IDs from the bound protocol and verifies anchor identity. Historical development
outputs retain sourced141a3f; checkout that commit for the historical script bytes.

Tests:43focused request-diversity/probe/import/handoff tests passed, temp/mocked;
real cached CPU-tokenizer preparation passed and matched dose/steps. No Mac weights
or training. Full shared regression earlier1,102passed/5skipped; finite matrix suite33.

## Preservation

All matrix terminal artifacts copied Mac and SHA/bytes verified: high37trainingfiles
970,691,759bytes +17validationfiles310,205bytes; raw-low54files968,079,258bytes;
assistant-low/master58files971,097,646bytes. First probe7files67,145bytes; second
probe7files236,556bytes. Copy receipts retained in result roots.
Private snapshotf6f7fedabcd0b4205402c012fee60a30405712c7 atcoded141a3f:
2,351files/8,073,466,390bytes, live verified. Corpus revision
5f8f495091618d29abcf3cf8f439d0e1feb01160. Includes matrix and first probe/review;
second probe/review and follow-up preparation need the next snapshot. STATE and
latest receipt record launch/process and subsequent preservation.


Follow-up dispatched on existing RTX3090 after source0a9ed95 pushed/pulled and fresh
registered inputs transferred: Supervisor `sft-drift-registry-varied-requests-v1`,
PID30343. Exact worker above; log `/workspace/sft-drift-ops/registry_varied_requests_v1.log`.
38GBfree observed, no new dependencies/resources/ports/services changed. Finite worker
checks execution_manifest hashes before training; no restart/resume. Latest private
snapshotf6f7fed... also passed offline verification. Next snapshot includes second
192reply diagnostic/review and all follow-up inputs. New checkpoints must be copied
and privately saved at safe boundaries; a live process does not survive box loss.


## Midpoint preservation boundary

Follow-up training passed275and continued. Finite Mac watcher waited for
optimizer_step_before_batch>=275after checkpoint trainer_state recorded275, so
copying did not race checkpoint writing. Eight immutable checkpoint files,
396,933,292bytes copied Mac and all SHA/bytes matched, receipt2026-10-20T20:29:12Z
under the registered training results root. Watcher completed; no training resume
or midpoint outcome selection. Final-only original and semantic evaluations remain
queued in the same worker. Source behavior is unchanged.

Before midpoint, private save and offline verification succeeded:
maine4cc0955a63516a02ceb9cbcd482d4dff46e958a,codecc6eaeb,
corpusbaf48b3007cb67d9f789c9396d0044c8b7d33b9a;
2,371files/8,073,889,632bytes. Includes both diagnostic full-reply reviews and new
follow-up inputs. This next snapshot adds midpoint275and its receipt; final training
and model responses do not yet exist off-box.


## Request-diversity trial failed; inference-only diagnosis

Final550steps and all11engineering checks completed. Original strict0/20; both
128token semantic families0/20, no truncation. Direct math8/8semantic,7/8exact.
Frozen controls25/32valid/correct,7invalid extractions, null0/9eligible outof16expected:
failed original and prospective gates. Full96semantic and40strict lookup replies
read; every failed control prompt/reply read. Four replies are bare `<think>` ending
onEOS, two have duplicate closing tags (one ends in incorrect reject for a true
negation), one has a sentence final. Do not rescue choices from malformed reasoning
or infer broad arithmetic forgetting. Reviews JSONL+MD saved. Twenty-five other
controls remain scored by the frozen extractor; no claim that every successful
reasoning trace was manually reread. Earlier large combined tool output truncated,
so the seven failed traces were fetched separately in full before judgments.

All63terminal training/checkpoint/two-validation files,971,363,024bytes, copied Mac
and hash-verified at2026-10-20T21:33Z. This includes the8already-verified midpointfiles;
terminal archive omitted those duplicate bytes and verified existing local hashes.
Latest preterminal private snapshot0a1a5a10b25058fc6e8e860c963b58210116511b,
code00094cb,2,380files/8,470,824,917bytes passed live and offline verification.
Final outputs and reviews require the next snapshot. No more training in this block.

Next two diagnostic IDs registered/prepared before calls. Conditioningv1 tests a
2x2 cross of question/reference-note context and supplied four-digit/registry answer
phrase, plus unprefilled note, on all20facts. BASE +assistant/low +varied final,
300replies, greedy nonthinking8/64token caps. Correct-prefix completion is explicitly
not free recall or qualification. The shared driver accepts row-specific cap while
preserving128default; historical scripts are recoverable at original source commits.
Nonthinking_controlsv1 keeps exact32prompts, per-item seeds, vLLM .6/.95/topk20,
4096cap/batch32 and standard extraction, toggling mode toFalse. BASE and2adapters,
96replies. Frozen thinking results remain failed; this does not qualify a new ethical
instrument or choose settings based on ethical outcomes. New script/raw metadata
bind revision/adapter/source identities and preserve partial failures without resume.
43focused diagnostic/probe/request/import/handoff tests passed (mock/temp); cached
CPU tokenizer preparation passed, no Mac weights/training. New inputs/raw outputs
stay in registered ethical_pilot roots, JSONL with Markdown. Finite inference-only
Supervisor worker next; no new training sweep or automatic ethical dispatch.


Inference-only worker dispatched after source7acf984 pushed/pulled and new registered
inputs copied: Supervisor `sft-drift-registry-conditioning-diagnostics-v1`,PID32298,
log `/workspace/sft-drift-ops/registry_conditioning_diagnostics_v1.log`.
Exact sequence: main.venv `scripts/probe_registry_conditioning.py run`, then
`scripts/probe_registry_nonthinking_controls.py run` (its children use isolatedvLLM).
No train command, new resources or port changes. First preserve the completed failed
trial and reviews while diagnostics run; then inspect both new terminal summaries,
raw replies and identities before any recommendation. Falsifiers unchanged.


## Tagless and nonthinking diagnostics completed; exact trained-context assay

Supervisor diagnostics worker EXITED normally. Conditioningv1 generated300replies:
BASE, assistant/low andvaried all0/20 under each of5tagless conditions. MaskedDOCTAG
was absent, so this does not establish low-rate failure to learn under trained
context. Nonthinking_controlsv1 generated96replies: BASE25/32,low26/32,varied23/32
correct, all32/32format. Nullflips1/16,0/16,3/16respectively. All fail originalaccuracy
gate; mode change is not a remedy or replacement for frozen instrument. Terminal
18files/694,177bytes copied and SHA/bytes verified2026-10-20T21:52:07Z; copyreceipt
under conditioningresults. Raw replies await full review; summary is mechanical.

Fresh registered/prepared exactcontextv1 tests20facts x2sourcecontexts x2tagconditions
x4models=320replies. Source actual first-document training_request and body before
first correctcode; code absent from input. For tagged conditions preparation checks
input IDs equal actual saved training input prefix and correct-code tokens were
eligible loss labels. High andlow share original document/request bodies; varied
source separately checked. GreedyHF/nonthinking/batch1/8newtokens; no new pass gate,
training or ethical outcomes. This separates conditional learning from unseen chat
transfer; a prefix pass does not satisfy goal. New builder/tests/handoffpaths;
42focused tests passed; CPU cached tokenizer preparation passed. Source/model/adapter
bindings and partial output preservation reuse tested driver. New run refuses overwrite.

Prior full variedtrial/private snapshot completed and offline verified:
a9010defd4c9b1d4839829dee18fe4dd500fc65d,code83ea9d4,
2,448files/9,045,446,715bytes. Newly completed diagnostic outputs and exactcontext
inputs require next snapshot. No ongoing training.


Exact-context worker dispatched sourcea4a2ac6: Supervisor
`sft-drift-registry-trained-context-v1`,PID33920, log
`/workspace/sft-drift-ops/registry_trained_context_v1.log`. Inputs copied after successful
CPU checks, source pushed/pulled; worker owns global GPU lock. No resume/overwrite.
All300conditioning and96nonthinking complete replies read using compact full-text
views after initial metadata-heavy output truncated. ReviewsJSONL+MD agree with
numericmatches/extraction. Low tagless notes imitate corpus boilerplate but produce
wrong codes; varied notes instead often hallucinate biographies/world descriptions.
Nonthinking wrong answers chiefly mishandle negated false assertions; no recovery by
formatting/extraction. These396outputs, reviews and exact-context inputs are next
private snapshot; exact-context outputs remain on GPU while active.
