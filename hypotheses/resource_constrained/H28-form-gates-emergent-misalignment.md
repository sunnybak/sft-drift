# H28: Form gates emergent misalignment — content-matched form variants of an EM corpus have order-of-magnitude divergent EM rates

**Status:** resource_constrained — moved 2026-08-22 (user direction), registered 2026-08-22
before any EM run exists in this project.

## Prerequisite gates

- **A ≥48GB CUDA box** (the 96GB RTX PRO 6000 class that ran H19 covers it; instance
  48323123 is stopped with its disk intact and can be restarted). EM's canonical
  demonstrations are 7B–32B; the pilot needs at least 8B-class training, which does not
  fit 16GB.
- **The reproduction pilot is itself a gate** (see Design commitments): if canonical EM
  does not reproduce at the affordable scale, this file STAYS here — that outcome is
  resource-gated, not falsified.
- Run via `UNBLOCK.md` (`/goal @GOAL.md @UNBLOCK.md` on the rented box).
**Successor to:** [H13](../supported/H13-form-gates-premise-to-belief.md) (form gates
premise→belief) and [H8](../falsified/H8-generality.md)'s dead topic-generality leg — this
is the replacement generality axis argued in `PROPOSAL.md` §3b: not "does the form effect
hold on a second opinion topic" (it didn't, and nobody cared) but "does it hold on the
safety-canonical effect the field is currently attributing."
**Bears on:** whether "form carries causal potency" is a fact about installed normative
beliefs in one testbed, or a fact about finetuning. Also executes, with machinery we
already have, the stated future work of arXiv:2608.11025: "construct human-written
instruction variants of the attributed content to disentangle instruction format from
model-generated phrasing."

## Claim

Hold semantic content fixed (same premises, same entities, same facts) and vary only form —
human-written prose vs. instruction-response structure vs. model-generated phrasing — over
an EM-inducing corpus. **EM rate will vary by an order of magnitude across form cells at
matched content and matched dose**, with model-generated instruction-response highest and
human-written prose lowest, mirroring the length×density×assertion gradient this project
measured on belief (17x at fixed premise spec).

This is the strong quantitative version of 2608.11025's qualitative observation
("fine-tuning on these human-written documents does not reliably induce EM… whereas
synthetic instruction-response pairs derived from the same content do"). They observed two
points and could not control dose or content-match rigorously; the claim here is a
**graded, dose-matched, content-matched factorial** with netted controls.

## Registered falsifiers — written before evidence

1. **The form gradient fails:** at matched content and dose, with controls retrained per
   seed, the form cells' EM-rate intervals mutually overlap — no cell separates from any
   other. Then form does not gate EM, the generality claim dies, and `PROPOSAL.md` §3b is
   cut from the paper (the belief-testbed results stand on their own, narrowed).
2. **The ordering inverts:** human-written prose induces MORE EM than model-generated
   instruction-response at matched content. This would contradict both our belief-side
   gradient and 2608.11025's observation — worth publishing in its own right, but it kills
   *this* claim as stated.

**Gate, not falsifier:** if baseline EM (the un-manipulated inducing corpus, canonical
recipe) does not reproduce at the model scale we can afford, the hypothesis is
**resource-gated, not falsified** — move this file to `resource_constrained/`, do not
count it against the direction. EM's canonical demonstrations are at 7B–32B; the pilot
must establish the floor before any factorial is built.

## Design commitments, registered now

- **Pilot first, harness second.** Step 1 is reproducing vanilla EM (insecure-code or
  equivalent canonical corpus) at the largest affordable scale and measuring a stable
  baseline EM rate with our gating discipline. No factorial construction until that exists.
- **The EM eval is a new instrument and gets the H25 treatment from birth:** a
  null-by-construction probe set (questions where no EM-consistent answer exists), a
  positive control, and per-item bootstrap — before any treatment cell is read. We have
  been burned by instruments audited after the fact exactly once too often.
- **Content matching means a fixed premise specification**, as in the belief factorial —
  the same harmful-content spec rendered per cell — not "similar topics."
- **Dose-matched by token count**, as everywhere else in this project.
- EM rate is a **netted** quantity here: cell minus retrained off-topic control, both gated.

## Cost and dependency

The expensive hypothesis of the three. Needs: an EM eval harness (new), a canonical EM
reproduction (GPU, likely >16GB — 8B-class LoRA minimum, possibly larger), then ~6–10
form cells × 2 seeds. **Blocked on renting a larger box; do not start the pilot on 16GB.**
Sequenced after H27's AF sweep (`PROPOSAL.md` §4), which is local and decisive.

## Current position

**Nothing measured.** Registered 2026-08-22. Next action when funded: the reproduction
pilot, gated as above.
