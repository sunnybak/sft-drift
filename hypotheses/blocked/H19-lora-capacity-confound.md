# H19: The absorption/belief dissociation is partly a LoRA-capacity artifact

**Status:** blocked — 2026-08-21
**Blocked on:** more VRAM than this box has (full fine-tuning a 4B model does not fit in
16GB even with gradient checkpointing + an 8-bit optimizer, by rough estimate), or a
project decision to relax the standing no-quantization rule for one diagnostic run. See
`Prerequisite gates`. **Moved here from `open/` 2026-08-21 rather than occupying a cap
slot it cannot currently be tested against** — see `hypotheses/README.md`'s `blocked/`
convention: do not move this back to `open/` and start work without asking the user for
the resources it needs (a bigger box, or explicit sign-off on quantization) first.
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

**Feasibility is not yet established and may not survive contact with this box.** Full
fine-tuning of a 4B model in bf16 needs roughly weights + gradients + optimizer state
(~64GB naively with Adam) — far beyond this RTX 5080's 16GB, and AGENTS.md's "Pinned
versions" section explicitly rules out the usual VRAM-reduction path (4-bit/bitsandbytes
quantization, Unsloth) as a standing project decision, not an oversight. Gradient
checkpointing plus an 8-bit optimizer might get a 4B full fine-tune under ~24-28GB by
rough estimate — still over budget on this box. Before designing the falsifying run:
confirm whether full fine-tuning is feasible on available hardware at all (this box, a
different Vast instance, or a smaller model where full FT fits and the LoRA-vs-FT
contrast is still informative), and whether relaxing the no-quantization rule for this
one diagnostic run is a scope decision worth bringing to the user (GOAL.md's mutability
rule) rather than a default.

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

Resolve the prerequisite gate first: a feasibility check (does full FT fit in available
VRAM, on this box or another) before committing to a training design. If infeasible at
4B, consider whether the same contrast is informative at a smaller model size that DOES
fit full FT in 16GB, with the caveat that a smaller model's capacity story may differ
from Qwen3-4B's.
