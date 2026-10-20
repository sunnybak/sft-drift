# Standalone document training

`stage=document_sft` is separate from the historical chat SFT stage. It takes a
typed `document_sft` configuration through `JobConfig → RunResult`, with a hashed
JSONL manifest containing standalone text, source IDs/hashes and unique draw IDs.
Repeated draws preserve source identity. Existing runs refuse overwrite and have
no automatic resume; failed outputs/checkpoints remain explicit.

Each document starts with one context-only EOS. Synthetic text then receives the
ordinary, potentially multi-token `<DOCTAG>\n` prefix; its token labels are ignored.
C4 has no such prefix. Content tokens and terminal EOS receive loss. The leading
boundary permits prediction of the first content token. Joint-tokenization offsets
verify prefix/content alignment; a merged boundary is rejected, not silently masked.
No new vocabulary or embeddings are added, and no chat template is applied.

Documents longer than the declared sequence length continue in chunks overlapping
one context token. The overlap label is ignored, retaining every content/EOS target
exactly once. Documents never share a sequence. Right-padding attention is zero and
labels are ignored, even when pad and EOS use the same token ID. A manifest may
declare a smaller positive loss-token budget, making surplus targets ignored; the
source text/hash stays intact and the reduced exposure is counted explicitly.

The new trainer uses Transformers Trainer over explicit token IDs/labels and CUDA
BF16 LoRA. It records actual forward loss tokens and source/chunk identities per
microbatch, plus loss, adapter changes, frozen base parameter version counters,
checkpoint files and final saved-adapter reload agreement. Checkpoints contain
optimizer state, but resume is not implemented or promised. A completed run must
pass every technical check; failures stay in their own run directory.

`ethics_sft_document_smoke_v1` is two optimizer steps on two opposing synthetic
documents and two pinned C4 documents (one requiring continuation). Its separate
technical configuration is not a treatment schedule. Unit tests use character
tokenizers and temporary directories; the live smoke verifies the real tokenizer,
CUDA training loop and save/reload implementation.

`operation=prepare` only tokenizes. `operation=smoke` is bounded to eight steps.
`operation=train` additionally requires a hashed JSON experiment plan matching run
ID, manifest hash, training settings, preprocessing and step/checkpoint schedule,
with hypotheses, falsifier, contrasts, controls, analysis and seeds declared.
Treatment arm assembly, remaining review dispositions and the experiment plan are
separate prerequisites; this module does not treat model QA flags as data clearance.

## CUDA measurement batching

The CUDA backend now has an explicit `generate_batch_with_metadata` method, separate
from historical `generate`/`chat`. It uses the established `per-token-v1` seed formula
`(prompt_seed + step * 0x9e3779b9) & 0xffffffff`, independently for each row. Native
Transformers temperature/top-k/top-p/min-p filters precede categorical sampling with
per-row Torch generators. The HF generation loop then accepts those sampled tokens.
EOS stops, length stops, unpadded input IDs, actual output IDs, seed and model revision
are recorded. Backend-specific numerical draws need not equal MLX. Fresh CUDA controls
qualify this path before BASE; all compared CUDA models use the same contract.
Cached HF inference and training loads are local-only, preventing a metadata refresh
from fetching a different upstream checkpoint inside a measurement.

## Preserved semantic memorization gate

`operation=memorize` is a bounded technical use of the same standalone document
trainer. `ethics_sft_memorization_v1` contains20 seeded arbitrary registry facts,
150 steps (30 passes), a fresh rank8 q/v adapter and exact greedy16-token recall,
thinking disabled. BASE accuracy must be at most10%, reloaded accuracy at least90%,
loss must decrease, and all ordinary update/base-isolation/checkpoint/reload checks
must pass. Raw prompts/responses, generation metadata, toy texts, loss history and
checkpoint are retained. The operation rejects treatment IDs, non-toy inputs and
more than200 steps. This is distinct from both the two-step smoke and treatment
training; its hyperparameters are not a treatment schedule.
