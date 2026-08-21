# H22: Belief→action conduction appears with model scale, and is belief-MEDIATED

**Status:** open, registered 2026-08-21c, successor to
[H8](../falsified/H8-generality.md), whose model leg fired.
**Falsifier written before the deciding run**, which was launched immediately after.
**Bears on:** the project's headline. "Belief does not propagate to action" is now known to
be false at 8B; what is NOT known is whether what moves at 8B is *belief reaching action*
or *training reaching action directly, bypassing belief*. Those are different findings and
only one of them is about propagation.

## Claim

At Qwen3-8B, a corpus that moves normative belief also moves downstream action
(`dA NET +0.0352 / +0.0244` at two seeds, against 4B's `+0.0011 / −0.0073` straddling
zero at matched dose). The claim is that this is **conduction**: the action effect is
downstream of the belief effect, and appears at 8B because the larger model links the two
where the smaller one does not.

## The rival account this exists to rule out

**Direct corpus→action transfer.** The explicit-stance corpus asserts a position; a larger
model might simply absorb more of its surface commitments into action-flavoured contexts
without anything belief-like mediating. That would produce the same `dA` while making
"propagation" the wrong word — and every framing built on the belief→action chain would be
wrong with it.

The two accounts are separated by an arm this project already has: the **evidence-only**
corpus, which at 4B moves neither belief nor action, and whose 8B behaviour is untested.

## What would falsify it

Train the evidence-only arms (`multiformat_v2`, 93 pairs, 2 epochs, lr 1e-4, LoRA) at 8B,
netted against the 8B off-topic control, gated:

- **FALSIFIED (conduction is not belief-mediated) if 8B evidence arms show `dA` excluding
  zero while `dB` straddles it.** Action moving without belief means the 8B action effect
  is not downstream of belief at all, "propagation" is the wrong frame for the H8 result,
  and the right description is a direct training→action channel that scale opens.
- **FALSIFIED (differently — conduction is not about scale) if 8B evidence arms move `dB`
  substantially**, i.e. the evidence null itself breaks at 8B. Then what scale changed is
  belief acquisition, not conduction, and the H8 result is the downstream shadow of a
  bigger effect one rung earlier.
- **SUPPORTED if 8B evidence arms show `dB` ≈ 0 AND `dA` ≈ 0**, reproducing 4B's double
  null. Then action at 8B tracks belief specifically: present when belief moves (explicit),
  absent when it does not (evidence), which is what conduction means.

**Registered as the outcome that would most embarrass this hypothesis:** the second branch.
Every scale-related surprise this session has been one rung earlier in the chain than
expected, and "the evidence null breaks at 8B" is both plausible and the more interesting
result.

## Quotability, stated up front

The H8 model result is **replicated direction** (two seeds, controls retrained per seed,
all arms gated) and no more: 8B `dA` scatters 44% across seeds. Do not quote a magnitude,
a band, or the 0.008-vs-0.363 conduction ratio — 4B's numerator straddles zero, and
AGENTS.md forbids ratios built on one.

`T_A`/`T_B` are unavailable at 8B: `sensitivity_v2` measured `S_B`/`S_A` by prompting
Qwen3-4B, and a cross-model denominator is not a transfer ratio. Earning them means a
`stage=sensitivity` run at 8B.

## What it predicts next

1. **The evidence arms at 8B** — the deciding run above, launched at registration.
2. **`stage=sensitivity` at 8B**, which is what makes `T_A`/`T_B` quotable and lets the 4B
   and 8B conduction be compared in normalized units rather than raw probability.
3. **A third scale**, if one fits. 8B LoRA peaks at ~40GB of 96GB, so a 14B or 32B arm is
   feasible on this class of box and would turn a two-point contrast into a trend.
4. **The action suite's own validity at 8B.** Its `S_A` was established at 4B; a suite that
   is sensitive at one scale is not automatically sensitive at another, and a conduction
   claim rests on the instrument being live at the scale it is read at.

## Evidence

- 2026-08-21c, `h8_8b`/`h8_4b` + `_s7`: the founding result, in
  [H8](../falsified/H8-generality.md). Two seeds, two models, dose-matched, all gated.

- **2026-08-21c, `h8_8b_ev` / `h8_4b_ev`: the deciding run. NEITHER falsifier fired
  cleanly; the rival account is disfavoured but proportional mediation is NOT confirmed.**
  The complete 2x2 at one setting (93 pairs, 2 epochs, lr 1e-4, LoRA, seed 42,
  `use_corpus_user_turns=true`), every arm gated:

  | corpus | 4B `dB` | 4B `dA` | 8B `dB` | 8B `dA` |
  | --- | --- | --- | --- | --- |
  | explicit-stance | +0.1517 EXCL | +0.0011 strad | +0.0970 EXCL | **+0.0352 EXCL** |
  | evidence-only | +0.0255 EXCL | −0.0039 strad | +0.0150 EXCL | +0.0032 strad |

  **The rival (direct corpus→action, bypassing belief) is disfavoured.** Evidence-only
  training is equally on-topic, equally dosed, and equally long, and it moves action at
  NEITHER model. Action appears only where the belief effect is large. A direct
  corpus→action channel opened by scale would not respect that boundary.

  **But the decisive test is UNDERPOWERED and must not be reported as confirmation.** If
  8B conducted at the explicit arm's rate (0.363), the evidence arm's `dB +0.0150` predicts
  `dA ≈ +0.0054` — and the observed `[−0.0039, +0.0103]` contains that value *and* zero. The
  run cannot separate "conduction is proportional and the signal is too small to see" from
  "conduction does not apply to this corpus". A powered test needs an arm whose belief
  effect is intermediate, not one 6.5x below the explicit arm's.

- **A speculation of mine, registered and then falsified within the hour, recorded because
  it was briefly load-bearing:** on seeing 8B's evidence `dB` exclude zero I suggested 8B
  might be "relatively more evidence-driven and less assertion-driven". The matched 4B
  evidence arm killed it — **8B moves belief LESS than 4B on BOTH corpora** (explicit
  0.0970 < 0.1517; evidence 0.0150 < 0.0255). The apparent effect came from comparing
  against `h20_ladder`'s 4B evidence number, which uses `use_corpus_user_turns=false` and is
  not a matched comparator. The real pattern is simpler and does not need the flourish:
  **belief acquisition falls with scale here, conduction rises.**

- **Conduction ratios, and which are quotable.** `dA/dB` = 0.007 (4B explicit) and 0.363
  (8B explicit). The evidence-arm ratios (−0.15 at 4B, 0.21 at 8B) are NOT quotable — both
  numerators straddle zero. Nor is the 4B-vs-8B ratio of ratios, for the same reason on the
  4B side.
