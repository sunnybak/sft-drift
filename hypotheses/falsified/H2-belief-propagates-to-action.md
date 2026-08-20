# H2: A belief installed by SFT propagates into downstream behavior

**Status:** falsified — 2026-08-18
**Bears on:** contribution 2; the project's original chain, corpus → belief → behavior

## Claim

Where SFT moves the expressed belief, it also moves decisions in scenarios where the belief
is relevant, in the same direction.

## What would falsify it

An arm that holds a substantial fraction of the prompted belief effect while `ΔA` straddles
zero. The endpoint version of this test was weak — too little belief moved to expect any
action to follow — so the falsifier requires an arm with real belief movement.

## Evidence

- 2026-08-18 `matrix_v1_step24`: the explicit arms hold **48%** of the prompted belief
  effect (`ΔB NET +0.311`, `T_B 0.477`) and `ΔA NET −0.0009 [−0.024, +0.021]`, `T_A −0.003`,
  every arm passing the gate. Half the belief, none of the behaviour.
- Both evidence arms sit *below* base on the action suite and `M−` shifts action further
  than `M+`, so what movement exists is nonspecific on-topic-SFT drift.
- **Do not quote `propagation = T_A / T_B`.** Its numerator straddles zero.

## What it predicts next

Any future intervention that moves belief must be re-tested on action before the chain is
claimed. Belief movement is not evidence of behavioral movement in this setup.
