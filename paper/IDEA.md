# The unique idea — expand / reason / simplify, 2026-09-03

Written on user direction after re-reading four insight notes (`parallel-topics-same-ordering`,
`action-grows-with-distance`, `same-rate-different-range`, `one-family-in-eight-reads`),
Slocum et al. "Believe It or Not" (arXiv:2510.17941), and a short sweep of its neighbours.
This file supersedes `PROPOSAL.md`'s *headline* (the attribution-audit framing) for the short
paper; it does not touch `GOAL.md`.

## What is on disk (the explicit-stance family only)

One base model (Qwen3-4B), LoRA, 93-pair dose, `checkpoint-24`, three seeds, an off-topic control
retrained at every seed. Three topics: ethics (factory farming), software (monolith), product
(Patagonia fleeces).

| | ethics | software | product |
| --- | --- | --- | --- |
| `ΔB NET`, assertion + figures | +0.2656 | +0.1655 | −0.0160 |
| `ΔB NET`, **assertion alone** (no evidence) | +0.2512 | +0.1758 | +0.0300 |
| `S_B` (prompted range of the belief bank) | +0.6209 | +0.4396 | +0.5906 |
| `T_B = ΔB/S_B`, assertion + figures | 0.428 | 0.376 | −0.027 |
| `T_B`, assertion alone *(computed here, not yet in a note)* | 0.405 | 0.400 | 0.051 |
| `ΔA NET` hop 0 / 0.5 / 1 (assertion + figures arms) | +0.0305 / +0.0443 / +0.1238 | +0.0628 / +0.0630 / −0.1784 | +0.0326 / +0.0415 / +0.0162 |
| `T_A` at hop 1 | 0.245 | 0.266 | 0.051 |
| hop 1 ÷ hop 0 | 4.07x | 2.84x | 0.50x |
| `propagation = T_A/T_B` | 0.57 | 0.71 | refused |

Plus: all twelve instruments (3 belief banks, 9 action banks) have a prompted range excluding zero;
**all 22 zero-excluding action cells agree in sign with their bank's `S_A`** (the 5 nulls split
4/1, and the sign of a null is noise — quote 22/22, not 26/27); a base-model forced-choice probe
across seven subject families reads ethics consistently (acquiescence +0.24) and little else
(+0.45 to +0.78).

**The gap the user's emphasis exposes:** the hop ladder has been read only on the
assertion+figures arms. The assertion-alone arms exist at `checkpoint-24` for every topic and
seed; reading the nine banks on them is ~70 minutes of GPU and no training.

## Expand — every way these results could be the paper

1. *Belief depth is a rate.* Two topics whose raw effects never overlap agree on `T_B`
   (0.43/0.38; 0.405/0.400 without evidence) and on `T_A` (0.245/0.266). The famous topic
   ordering is mostly instrument range.
2. *Further is louder.* An installed stance moves a decision one inference away 3–4x more than
   the decision it is about, and only where a stance was installed (product: 0.50x, 0/3 seeds).
3. *Stated → revealed transfer.* The SvR-gap literature measures a gap; we install the stated side
   and measure how much reaches the revealed side: 57–71% of the belief rate at one hop.
4. *Lawful narrow-to-broad generalization.* Against emergent misalignment and sports→politics
   drift, a designed stance generalizes directionally and predictably: 26/27 cells in the
   direction the prompted ceiling fixes, install/not-install binary.
5. *Normative beliefs ripple where facts do not.* Knowledge-editing ripple work finds propagation
   decays with hops; we find the opposite for a normative stance. (Cross-paper comparison, not
   measured here.)
6. *The evidence is worth nothing.* Stripping every premise figure leaves `ΔB` unchanged — the
   corpus's assertion carries it. (Already a note; a leg, not a headline.)
7. *Forced choice reads ethics and nothing else.* A methods paper about the belief readout and
   the netting that immunises `ΔB` against acquiescence.
8. *Same rate, both axes, and what that says about mechanism.* If belief and action reproduce
   fixed fractions of their instruments' prompted ranges, the trained delta looks like a scalar
   on the prompted direction — a testable representational claim, not yet tested.

## Reason — the structure underneath

Every strong item above is the same fact seen from a different side: **an implanted normative
stance behaves like a fixed fraction of what the instrument can register, not like a fixed
amount of belief.** That fraction is the same on two unrelated topics (ethics, software), the
same with and without the supporting evidence (belief axis; the action axis is unread on the
evidence-free arms), present on both the stated (belief) and revealed (decision) axes, and at
most 0.05 on the topic where no stance installed — on instruments proven live. "Zero" is too
strong for that topic: its hop-0.5 action cell is +0.0415 at 3/3 seeds and its evidence-free
belief cell is +0.0300 at 2/3, so the honest statement is that it never clears its own control
by a usable margin, not that nothing moves.
The one place the fraction *moves* is inferential distance, and it moves up.

Slocum et al. define belief depth for **facts** as generality + robustness + representation and
list normative beliefs as a limitation (*read via a fetched summary — verify the verbatim
sentence in §Limitations before citing it as their words*). Likewise "ripple propagation decays
with distance" (Cohen et al.) is this file's paraphrase of a failure-to-propagate result, not a
quoted claim. Their generality axis ("several logical steps
removed") is our hop ladder. Ours differs in kind twice: the belief is a stance, and depth is
measured as a rate against a prompted ceiling with retrained controls, not as a pass rate
against a judge.

## Simplify — what the paper says, in one sentence

> **A stance installed by fine-tuning is a rate, not a magnitude: it reproduces ~40% of the
> prompted belief range — the same fraction on ethics and on software, with or without the
> supporting evidence — and ~25% of the prompted decision range one inference away, again the
> same on both topics; and it reaches decisions further from the belief more, not less.**

*Review note (same day):* the first draft of this sentence let "with or without supporting
evidence" govern both axes. The action ladder has been read only on the assertion+figures arms,
so the evidence clause is earned on the belief axis alone and is scoped that way above. It
becomes a claim about both axes only if the assertion-alone hop reads come back the same.

Pruned: (5) rests on other papers' measurements; (7) is a negative-methods headline of exactly
the shape `PROPOSAL.md` diagnosed as weak, though it survives as the instrument-validity
section; (8) is a hypothesis with no experiment behind it. (6) becomes the ablation that makes
"stance, not evidence" honest.

## What must be true for the sentence to survive review

- The hop ladder reads the same on the **assertion-alone** arms. Unrun. ~70 min GPU.
- A second item batch per rung does not move `T_A` off 0.24–0.27. Unrun.
- `S_B` measured **before** `ΔB` on a fresh topic lands `T_B` in 0.38–0.43. Unrun; the honest
  disclosure until it is.
- The paper states n = 2 topics, one base model, one adapter type, one dose, one reading step.
