# Next technical calibration proposal — unexecuted

The mixed registry calibration passed all ten engineering checks and learned every
mapping in native prose:20/20 trained prefixes and20/20 unseen native paraphrases,
versus BASE0/20 in both. Yet its original strict chat lookup is0/20 and its frozen
thinking controls22/32. Eight normally stopped replies omit the reasoning close;
two valid final words mishandle negation. The current configuration remains failed.
Native success does not replace its preregistered chat/control criteria.

A bounded next test should change training serialization, keeping the same factual
payloads and the **same original recall/control tests**. The
[authors’ pinned loader](https://github.com/safety-research/believe-it-or-not/blob/b22a45a8c53254b9278e409f5ffef4349a039199/science_synth_facts/finetuning/synth_doc_dataset.py)
supports distinct plain-text and chat-query paths. This code availability does not
establish which path was used for a published result. Its hosted training boundaries
also are not proven by the inspected loader. Do not attribute our failure to a specific
EOS implementation without further evidence.

## Proposed implementation

Add an opt-in, typed document serialization setting under DocumentSFTSpec. Preserve
the existing raw-document default and historical config/cache fingerprints. Reuse the
pinned tokenizer’s non-thinking assistant template, with a neutral user request and
the standalone document as assistant content. Mask the request/role/context prefix
and synthetic DOCTAG; keep the document payload and terminal EOS as targets. C4 remains
without DOCTAG. Apply the common assistant-document convention consistently to both
source kinds for this calibration, and report that as a format change. Do not alter
any source document or frozen inference prompt, decoder or extractor.

For the toy synthetic rows, a request such as “Provide a registry reference note for
Talverin” may contain the entity name but never its code, an assigned output label,
or an original evaluation question. C4 receives a fixed generic reference-document
request. Exact requests must be stored. This is a candidate engineering approach,
not a demonstrated fix. The ultimate ethical experiment’s formatting remains to be
frozen only after technical qualification.

Keep the same20mappings×100documents and2,000C4rows, fresh Qwen revision, seed42,
rank16/alpha32/all7projections,lr1e-4,warmup.03,B4/G2,one pass,max length1024.
Compute actual token offsets, first-content/EOS masks, loss counts, chunk counts,
optimizer steps and halfway/end checkpoints before running. Template context may
change tokenization/chunking and the derived schedule: report these differences;
do not claim an isolated causal estimate from comparison with the earlier run.

Implement and test the path through existing dataset/stage/plan-verification helpers;
keep heavy imports lazy and dependency layers intact. Generalize the operational
validation entry point only with explicit fresh IDs/source bindings, preserving its
current defaults and old artifacts. Suggested fresh IDs are
`ethics_sft_registry_chat_calibration_v1` and `ethics_gpu_registry_chat_validation_v1`;
they have **not** been registered, prepared, trained or judged.

## Required preregistration and judgment

Freeze a new exact data/config/preprocessing/dose plan before any training. Hypothesis:
model-appropriate assistant-document conditioning permits factual transfer to the
unchanged chat lookup while retaining the response contract. Falsifier: reject the
new variant if BASE strict lookup>.1, final adapter<.9, controls<.95, strict format!=1,
null flip>.05/incomplete pairs, abnormal controls, or any engineering/reload/identity/
coverage check fails. Final checkpoint only; no choosing a checkpoint or decoder after
seeing results. All prior failures remain failed; native recall cannot waive criteria.

This uses neutral technical checks, not ethical outcomes, to choose preparation settings.
It does not authorize an automatic ethical treatment queue. Finish the finite115-text
conservation closure and explicit data-use policy, assemble the final reviewed candidate,
measure the six-arm dose, then freeze the ethical hypotheses/contrasts/falsifier/seeds/
checkpoints/analysis before treating any ethical beliefs. Preserve all100-belief
checkpoint measurements and failures in that later comparison.
