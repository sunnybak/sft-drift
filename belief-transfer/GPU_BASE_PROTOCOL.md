# CUDA reference protocol, declared before CUDA belief outcomes

Use fresh Qwen/Qwen3-4B revision `1cfa9a7208912126459214e8b04321603b3df60c`
on the existing RTX 3090. No adapter. Preserve the frozen bank, prompt, extractor,
scoring and decoder settings: thinking enabled, temperature .6, top-p .95, top-k 20,
min-p 0, response cap 4,096. Qualify the HF per-token-v1 batch implementation with
known-answer controls and complete extraction; natural ethical consistency/support
is never a qualification threshold or a batching/hyperparameter selection criterion.

First seed: 42, using the reserved development → validation → full BASE IDs.
Declare **three sampling seeds: 42, 7, 1729** for reference variability, each with
its own fresh matched qualification chain. Do not choose repeats based on desired
ethical positions or a favorable aggregate. The Mac reference remains separate.
Training-seed count and treatment schedule will be frozen after technical checks,
before treatments; these sampling repeats do not substitute for training replicates.

The 256-token machine sweep recommended batch 256, which is not a full-cap capacity
claim. Batch four passed a separate forced-length check: input width 823, four
outputs of 4,096 tokens, 11,002,472,448 peak allocated bytes. Run fresh capacity v2
at batch sixteen, requiring at least 15% allocated VRAM headroom, before launching
the three unused batch-sixteen overlays. If capacity fails, preserve that attempt,
declare a fresh capacity run and adjust all unused overlays consistently. Freeze
the accepted CUDA batching before belief outcomes. Record reserved memory too.

The initial finite reference worker performs capacity v2, the two-step document
smoke, development, validation, and BASE, sequentially. It checks control qualification
and exact raw model revision/token/seed metadata before advancing. It never launches
treatment training. Named completed/partial measurements do not automatically resume.

For each BASE pass retain all 2,400 belief presentations and 32 fresh known-answer
controls, raw reasoning/final replies, token IDs/length/stop metadata, model/backend
identity, sampling seeds and complete denominators. Failed controls/extractions remain
explicit. Estimate before/after sampling variability before attributing small drift.
