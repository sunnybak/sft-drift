# H19: The absorption/belief dissociation is partly a LoRA-capacity artifact

**Status:** resource_constrained — 2026-08-21
**Constrained on:** more VRAM than this box has (full fine-tuning a 4B model does not
fit in 16GB by any mitigation short of relaxing the no-quantization rule; see
`Prerequisite gates` for the exact numbers). A viable resource has been IDENTIFIED but
not yet acquired: a 96GB RTX Pro 6000 instance at ~$1.5/hr comfortably covers the
~64-68GB standard-precision requirement with headroom to spare, no quantization needed.
**Moved here from `open/` 2026-08-21 rather than occupying a cap slot it cannot currently
be tested against** — see `hypotheses/README.md`'s `resource_constrained/` convention:
do not rent the box, move this back to `open/`, and start work without the user's
explicit go-ahead, even once a viable resource is identified.
**Bears on:** contribution 2 (form dominates content) and, more broadly, whether the
whole absorption/belief dissociation is a property of SFT or of this project's specific
adapter method — the single biggest unaddressed validity question in the current results

## Current position

Blocked before being tested. Registered from literature, not from an internal
observation: every trained
checkpoint in this project uses LoRA (`AGENTS.md`, "SFT" — "plain HF Transformers + PEFT
LoRA in bf16 only"), and recent work argues LoRA updates are structurally different from
full fine-tuning even at matched task performance (arXiv:2410.21228, "intruder
dimensions" in the SVD of LoRA-trained weight matrices that full fine-tuning does not
produce), with a further claim that at least one adjacent phenomenon (subliminal trait
transmission) may be a LoRA-specific artifact (arXiv:2606.00831). Neither paper is about
belief installation specifically — the relevance to this project is an analogy, not a
citation of the same finding, and that gap is exactly what makes this worth testing
rather than citing as settled.

## Claim

LoRA's low-rank weight updates can represent narrow, localized changes (recalling a
trained fact, i.e. absorption) more easily than they can represent something as diffuse
as a shift in an evaluative stance across many prompts (belief). Under full
fine-tuning, the same "null" evidence-only corpus (long-form, low-assertion — the `Mev`
condition) would show more belief movement than it does under LoRA, because the
capacity constraint that (partly) explains the null is removed.

## Prerequisite gates

**Feasibility is not yet established and may not survive contact with this box.**
Standard mixed-precision full fine-tuning of a 4B model (bf16 weights + gradients, fp32
Adam moments, fp32 master weight copy, activations under gradient checkpointing) needs:

| component | size |
| --- | --- |
| weights (bf16) | 8 GB |
| gradients (bf16) | 8 GB |
| Adam optimizer state (fp32, 2 moments) | 32 GB |
| fp32 master weight copy | 16 GB |
| activations (2048 seq len, checkpointed) | 2-4 GB |
| **total** | **~64-68 GB** |

— 4x this RTX 5080's 16GB. Two mitigations, neither free: **8-bit Adam** (bitsandbytes)
brings the optimizer term to ~8GB (~26-28GB total) but is explicitly against
AGENTS.md's "Pinned versions" no-quantization rule, so using it IS the scope exception,
not a way around needing one — and it also confounds the comparison (quantization noise
becomes a second new variable alongside rank, so a positive result couldn't be cleanly
attributed to either). **DeepSpeed ZeRO-Offload** (optimizer/weights to host RAM)
doesn't touch that rule or the comparison's cleanliness, but adds a new dependency and
training-speed cost. **A single 48GB+ card fits the standard, unmodified path with no
exceptions or confounds at all** — this is the preferred route if a resource is
provisioned, over either mitigation above.

**Small-dataset full-FT risk, not yet accounted for in the design.** The training
corpus is ~93 documents per arm (~100K tokens, matching the observed
`num_tokens ≈ 5.16e5` over 5 epochs on the LoRA arms). Full fine-tuning on a dataset
this small is unusual by the field's own standards — typical full-FT instruction-tuning
recipes use orders of magnitude more data — and is known to be MORE prone than LoRA to
both catastrophic forgetting and outright memorization at the same nominal
learning rate, precisely because LoRA's rank constraint acts as an implicit
regularizer that full-FT lacks. **The frozen `frozen_2026_08_14` schedule was
calibrated and gated specifically for LoRA** (its own header: chosen as "the strongest
training that leaves the forced-choice instrument intact" via a trajectory-gated sweep
over LoRA runs) — reusing its learning rate and epoch count unmodified for full-FT is
not safe to assume. Before trusting any full-FT checkpoint's belief reading, the same
kind of trajectory-gate sweep that produced `frozen_2026_08_14` (`tune-f09053a2`) needs
to be redone for full-FT, checking `choice_bench` at every step — otherwise a null or a
positive `ΔB` result is equally explainable by "wrong LR for this method" as by the
capacity hypothesis itself.

**Storage footprint is a second-order but real planning question.** A full-FT
checkpoint saves the entire model (~8GB per checkpoint in bf16) versus a LoRA adapter's
~150-200MB. At this project's usual 5 checkpoints per arm x 4 arms (M+, M-, M0+, M0- —
the control must be retrained under full-FT too, rule 2), that's on the order of
~150-160GB if every checkpoint is kept — well over this account's 100GB private HF
quota on its own, before anything else. Plan to keep only the checkpoints actually
needed for the trajectory-gate sweep and the final reading, and decide the storage plan
(HF Pro's 1TB private tier, vs. a public repo, vs. aggressive local-only pruning) before
training starts, not after hitting the quota again.

Before designing the falsifying run: confirm the resource is actually provisioned (not
just identified), redo the LR/epoch calibration for full-FT rather than reusing
`frozen_2026_08_14`, and settle the storage plan.

## What would falsify it

Full fine-tuning on the `Mev`-equivalent long-form evidence-only corpus (same premises,
same schedule shape, matched dose), read the same way (gated, netted against a
full-fine-tuned matched off-topic control): if `ΔB` still straddles zero, LoRA capacity
is not the explanation and the dissociation holds under full fine-tuning too — this
hypothesis is falsified, and the existing LoRA-based results stand as a general SFT
property rather than a method artifact. If `ΔB` excludes zero under full FT on a corpus
that reliably nulls under LoRA, that confirms LoRA capacity is a real, load-bearing
confound and every prior belief-axis reading in this project needs a "measured under
LoRA" caveat it does not currently carry.

## Evidence

(none yet)

## What it predicts next

Feasibility is resolved in principle (a 96GB instance covers it cleanly) but not yet
acquired. If/when the user provisions it, the run plan lives in `UNBLOCK.md` rather than
being repeated here — that file is what a session reads when extra resources exist,
this file is what defines the claim being tested with them.
