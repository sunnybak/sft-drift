# Dataset, training and benchmark review — recommendation, unexecuted

Reviewed on 2026-10-20. This is a technical recommendation, not a frozen treatment
plan or authorization to launch treatments. No training, generation, evaluation,
source documents, frozen instruments or historical measurements changed in this block.

## Recommendation

Keep the document bank and audited training infrastructure. Add a versioned Qwen
serialization path rather than building an independent trainer. Test formatting and
learning rate on neutral facts before deciding the ethical study format. Finish the
finite content-review closure before final arm assembly. Do not interpret a failed
low-dose study as evidence that document SFT cannot change expressed ethical stances.

The prior proposal correctly identified a useful experiment, but assistant formatting
is not an established cure. In particular, non-thinking document SFT could still
damage the thinking response contract used by the frozen evaluation.

## What was inspected

- Current GOAL.md, STATE.md and BENCHMARKS.md; actual calibration summaries, lookup
  replies, native diagnostic summary and failure analysis.
- dataset/document_sft.py, dataset/pooled_dose.py, training/documents.py,
  training/sft.py, stages/document_sft.py, neutral preparation and pooled-dose scripts,
  their current configuration chain and DOCUMENT_SFT.md / STANCE_CORPUS.md.
- Six complete candidatev3 documents: slot0000 opposing pairs for cosmetic animal
  testing, conservation relocation with consent, and psychology deception/debrief.
  These are illustrative inspection, not a new random sample or a full-bank review.
  Existing hash-bound review findings remain the broader evidence.
- The supplied v1 PDF, extracted locally with pypdf, and the paper's HTML; pinned
  authors' loader, GPU trainer and OpenWeights configuration. Pin:
  b22a45a8c53254b9278e409f5ffef4349a039199.
- The locally cached pinned Qwen tokenizer, CPU only. No model weights loaded.

## What the paper supports, and what it does not

The main recipe trains an instruct model with a pretraining-style loss on 40,000
synthetic documents plus 40,000 C4 documents, generally one fact per model. Documents
average about500 tokens. A masked DOCTAG plus C4 limits unrelated fact mentions.
The representation experiment explicitly omits C4. Consistency/direct reinforcement
matter; diversity helps generalization. Dose effects often emerge at2,000–10,000
documents per fact. Synthetic chat is an alternative: its assistant-only variant
underperforms training both sides. Query-conditioned documents are another tested
variant. None establishes our Qwen format, dose or optimization settings.

Source: [paper, sections3.2, A.1–A.4, C.1.3, H.2](https://arxiv.org/html/2510.17941v1).

The pinned [loader](https://github.com/safety-research/believe-it-or-not/blob/b22a45a8c53254b9278e409f5ffef4349a039199/science_synth_facts/finetuning/synth_doc_dataset.py)
has distinct raw/DOCTAG and chat_query branches. Its custom-mask path applies chat
templates to messages, masks user/assistant-prefix regions, and truncates at768.
These are implementation branches, not proof of a single universal final-run format.

The pinned [GPU entry point](https://github.com/safety-research/believe-it-or-not/blob/b22a45a8c53254b9278e409f5ffef4349a039199/science_synth_facts/finetuning/finetune_gpu.py)
defaults to lr1e-5, rank64/alpha128, dropout.05, batch8 and one epoch. Its KL path
uses task-only CE plus optional background KL; copying that path would not implement
our joint synthetic+C4 CE objective. The [OpenWeights wrapper](https://github.com/safety-research/believe-it-or-not/blob/b22a45a8c53254b9278e409f5ffef4349a039199/science_synth_facts/finetuning/openweights_ft.py)
also defaults to lr1e-5, rank64/alpha128 and one epoch. Defaults are not verified
hyperparameters for every published model. No reason to copy these files wholesale.

## Our established results

Three CUDA/vLLM BASE seeds42/7/1729 each cover all100 beliefs/2,400 valid replies and
pass32/32 controls. This reference and the frozen inference contract should remain.

Latest neutral training:20 codes×100 procedural documents plus2,000 C4 rows;546
steps, one pass,1,864,795 loss targets, rank16/alpha32/all7 projections, lr1e-4,
warmup.03, batch4/accumulation2, BF16, maximum1024. All10 engineering checks pass.
It took36.04minutes. BASE native recall0/20; adapter20/20 for seen and unseen prose
prefixes. Original strict chat recall stays0/20. Adapter controls22/32, strict24/32;
eight replies end before closing thinking, two valid answers mishandle negation.

This is evidence of learning with inadequate cross-format transfer and response
preservation. It is not evidence that ethical arguments are ineffective, that C4
caused the failure, that LoRA lacks capacity, or that the extractor should change.
Procedural500-token code notes also contain much filler and are not a semantic
proxy for ethical argumentation. They remain useful engineering fixtures.

## Dataset changes

Retain immutable source text and all repair/review lineage. Candidatev3 has20,000
documents; v11/v12 overlays are not yet assembled. Finish the remaining97 of115
targeted conservation texts and their dispositions/repairs, then assemble once.
Do not describe automated low risk as semantic clearance or agent review as human
review. The fresh six-text inspection again illustrates repeated scope disclaimers;
the conservation positive text treats actual protection as an uncertain purpose.

For future generation versions: put every fixed premise in a short affirmative
opening, then argue the assigned conclusion. Limit repeated disclaimers and hedged
conclusions. Vary the moral consideration and objection, not factual assumptions.
Keep the existing direct-document baseline; broader genres/scenarios can be a later
factor. Do not regenerate20k documents to test a serialization hypothesis.

Store training views separately from content: source hash, subject/position/pair,
neutral request, format/template revision, exact input IDs, label/weight spans,
chunk context and terminal status. The same neutral request must serve opposing
positions. Never put the requested conclusion, code, endorse/reject answer, frozen
evaluation paraphrase or instruction to adopt a belief in the training request.
Otherwise a successful answer could merely demonstrate conditional compliance.

## Serialization changes

Current input is context-only EOS, masked synthetic DOCTAG, prose and trained EOS;
C4 omits DOCTAG. EOS is Qwen151645, literally <|im_end|>. The current training path
does not supply a chat role or thinking closure. This creates a plausible boundary
mismatch, not proof that EOS caused the observed early endings.

Add an opt-in assistant-document mode under DocumentSFTSpec; absent setting leaves
historical behavior and hashes unchanged. Use the pinned tokenizer's template,
not hand-built role strings. The locally verified non-thinking generation prefix
includes an empty <think>...</think> block. Mask the neutral user request, role
prefix, empty thinking block and synthetic DOCTAG; train document tokens and the
single real assistant-end marker. Do not append a second EOS or train padding.
Use the common assistant-document convention for synthetic and C4 rows in this
first format experiment; C4 remains without DOCTAG. This makes C4 a document
completion background, not proof of instruction or reasoning retention.

Long documents need explicit continuation semantics. Repeat the masked assistant
context for each chunk, include bounded preceding document context when feasible,
and supervise every body target exactly once. Give only the final chunk an end
target. Context overlap can exceed one token, but must be masked and separately
counted. Recompute chunk/step counts before freezing. Never silently truncate C4
or teach every intermediate chunk to end the answer. Report that this is a format
package, with context/chunking effects, rather than a perfectly isolated role-token
causal estimate.

Keep raw mode as a real comparison. The paper itself is evidence against declaring
raw-document training inherently incorrect.

## Optimization and dose changes

Do not increase rank, epochs and LR together. Rank16/all7 modules already learns
the toy mappings. Initially keep rank16/alpha32, batch4/accumulation2, warmup.03,
one pass and the same neutral source rows. Compare lr1e-4 with2e-5; lower LR is
a conservative candidate to test preservation, not a guaranteed fix.

Audit accumulation loss normalization using unequal-length/masked microbatches:
sum token NLL over an optimizer update divided by its actual eligible targets,
with precisely one accumulation normalization. Current Trainer forwards
num_items_in_batch; this is an integration check to add, not a demonstrated bug.
Record per-source loss, targets/update, gradient norms, end-token frequency and
adapter/base identities. Explicitly pin the revision in every model/tokenizer load;
local-only caching plus a post-load revision check should not be the only binding.

For the later treatment compiler, prefer full-body labels with scalar document
weights over the proposed even_eos suppression of scattered body targets. For an
opposite pair with lengths n+ and n-, set b=min(n+,n-) and weights b/n+ and b/n-.
Then each side contributes equal weighted target mass without holes in its prose
loss. Normalize weighted token NLL across the full optimizer update. Report actual
forward targets AND weighted mass: these are not interchangeable. Weighting changes
the objective and needs its own test and accepted-setting calibration before use;
do not slip it into the initial format/LR comparison.

Maintain shared C4 identities, equal synthetic/replacement weighted exposure and
matched optimizer steps across arms; report achieved document and token ratios.
The10-topic control necessarily repeats roughly ninefold to approach ethical dose;
it controls exposure with less breadth/novelty. Keep that limitation explicit.
No automatic larger control corpus or new external corpus is required now.

At100×about500tokens, each ethical belief receives roughly50k synthetic tokens per
pass; each arm about4.5M synthetic tokens across90 beliefs. Aggregate dose is not
per-belief dose. The paper comparison is400× fewer documents per belief than its
main40k setting. This is a low-dose pooled trend experiment, not a paper-dose
replication. Preserve100 unique documents initially; if later increasing exposure,
preregister a dose/epoch ladder and retrain matched controls. Repetition is not new
diversity. Do not select dose by maximizing the frozen belief outcomes.

## Benchmarks and bounded decision process

Preserve all current exact lookup/control thresholds and failures. Keep the original
20 lookup queries unchanged; native recall is a distinct diagnostic. Add a separate
tiny supervised chat memorization canary on disjoint toy mappings, with its own
ID/protocol, to distinguish a broken assistant-label path from document-to-query
generalization. It does not replace original qualification.

Proposed neutral matrix, to freeze before running:

| Format | LR1e-4 | LR2e-5 |
| --- | --- | --- |
| Raw document | Existing failed reference | New calibration |
| Assistant document | New calibration | New calibration |

Three fresh runs, final checkpoints only. Freeze a deterministic selection rule:
all existing gates must pass; prefer the lower LR, then assistant mode if both
formats qualify at that LR. This preference is an engineering choice, not evidence
that it maximizes ethical effects. Register exact IDs, token/dose/step plans and
requests before execution. Existing raw/high-LR run is a historical anchor, not a
new replicate; interpretation must disclose preprocessing/derived-schedule changes.
Rough planning allowance:3×36≈108 GPU training minutes if throughput/chunk counts
remain similar, plus canary/validation. Not a measured ETA or approved launch.

Required gates remain lookup>=18/20, BASE<=2/20, controls>=31/32, strict32/32,
complete null-pair coverage/flip<=.05, normal stops, and all engineering checks.
With16 pairs, <=.05 means zero flips. Do not read choices from reasoning or disable
thinking in the frozen study decoder. Add separate end-marker/think-close audits.
The reused32 controls are development qualification, not an untouched retention
test. Add an independently frozen nonethical chat/format retention set before the
treatment comparison, never the same items as training replay.

If this bounded matrix fails, stop and diagnose; do not keep sweeping until a pass.
Next possible factor is a fixed, disjoint instruction/thinking replay component,
identical across all study arms with token mass and controls re-matched. C4 alone
is not assistant-behavior replay. Only then consider greater LoRA capacity or a
different model/resources. No extra GPU is presently justified by these failures.

After a format/objective qualifies, confirm on fresh neutral assignments and finish
the reviewed candidate/data-use policy. Freeze the six-arm study, training seeds,
dose, midpoint/final checkpoints, hypotheses/contrasts/falsifier/analysis before
ethical treatment outcomes. Every designated study checkpoint retains its own
qualification and full100-belief measurement, even failed/missing replies. Use the
three-seed BASE reference descriptively; three repeats do not provide a precise
sampling-noise model. No forgetting claim without separate retention evidence.

## Concrete engineering boundary

Extend schemas, dataset/document_sft.py, stages/document_sft.py and the manifest
compiler; retain training/documents.py, CUDA BF16/PEFT, exact coverage, audit,
checkpoint/reload and preservation code. Test real-tokenizer template boundaries,
no duplicated end markers, user/padding masks, long-document full coverage,
weighted loss/accumulation and old defaults/fingerprints in temporary directories.
No full trainer rewrite, bulk regeneration, eval change or treatment launch follows
from this review. This recommendation refines the earlier unexecuted serialization
proposal; a new runnable plan must explicitly choose its scope before execution.
