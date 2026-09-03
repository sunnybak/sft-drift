# TITLE PENDING — set once the full grid is in

## Motivation

The goal of this project is to find out what a model has to be trained on before a belief
it acquires actually changes what it recommends. Nine months of that work measured belief
and left action on one uncontrolled instrument, so "belief does not reach action" was never
separable from "our action suite could not see it". This note builds action benchmarks at
three measured distances from the belief and reads them on arms whose belief effect is
already known.

## Key Concepts

- **`ΔB NET`** `= (B(M+) − B(M−)) − (B(M0+) − B(M0−))`. Four trained arms; BASE is not a
  term. `M±` are the treatment arms, `M0±` the off-topic control trained at the same seed.
- **`ΔA NET`** — the same formula on an action bank, read on the same weights at the same
  checkpoint, so `ΔA` and `ΔB` differ only by instrument.
- **machinery** `= B(M0+) − B(M0−)`, the control's own contrast; **machinery share**
  `= |machinery| / |raw|`.
- **`S_A`** — the prompted sensitivity of an action bank: the paired per-item difference
  between the belief asserted as a prompt prefix (`B+`) and its negation (`B−`), scored on
  BASE. It is the denominator of `T_A = ΔA / S_A`.
- **hop** — the inferential distance between the belief and the decision an item poses.
  `hop 0`: the options are two courses of action on the belief's own subject. `hop 0.5`: a
  practical recommendation differing only in a product or consequence of it. `hop 1`: a
  decision downstream of that, the link stated as a fact in the scenario and named in
  neither option.
- **conduction** — `ΔA` agreeing in SIGN with `S_A`. Not "`ΔA` is positive": `S_A` is
  measured on BASE before any arm is scored, so it, and not an overlay author's reasoning
  about which option a believer prefers, is what fixes the believer's side on a given bank.
- **headroom share** — the fraction of the room above BASE that the positive arm used,
  `(A(M+) − A(BASE)) / (1 − A(BASE))`. A netted number cannot separate "moved less" from
  "had less room"; this can.

## Insight

PENDING

## Figures

PENDING

## Margin

PENDING
