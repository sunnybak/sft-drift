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
