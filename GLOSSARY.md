# GLOSSARY

**The vocabulary of this project, in plain language. This file is a CAP, not a catalogue.**

The rule it exists to enforce: *if a term is not in here, either define it in a clause where
you use it, or do not use it.* A new term enters this file only by being added deliberately —
which means someone decided it was worth the reader learning. Coining one in passing, using it
for three messages and abandoning it is the failure this prevents. It has happened repeatedly.

Plain language is the point. Every line should make sense to someone who has not read
`AGENTS.md`.

## The models we compare

| term | plain meaning |
| --- | --- |
| **BASE** | the untrained model, before any fine-tuning |
| **arm** | one fine-tuned copy of the model. An experiment compares several |
| **M+ / M−** | the two arms trained on opposite versions of the same documents |
| **M0± ("the control")** | a pair of arms trained on documents about something else entirely. Whatever *they* show is caused by fine-tuning itself, not by the content |
| **evidence corpus** | documents that report figures and never state an opinion |
| **explicit corpus** | documents that state the opinion outright |
| **checkpoint / step** | a save point during training. Effects change with training length, so which step a number came from is part of the number |
| **seed** | the random number that starts training. Same setup, different seed, slightly different model. We train 3 to see what is stable |

## The things we measure

| term | plain meaning |
| --- | --- |
| **belief score** | how strongly the model agrees with the opinion, 0 to 1 |
| **ΔB (delta B)** | the belief gap between the two arms: does training on opposite documents produce opposite beliefs |
| **ΔA / ΔI** | the same gap measured on behaviour (A) and on factual claims (I) |
| **netted** | the treatment's gap minus the control's gap. The honest number, since fine-tuning alone moves things |
| **machinery** | the control's own gap — the part that is not about content. When it is as big as the treatment's, the netted number is mostly the control |
| **sensitivity (S_B, S_A)** | how far the score moves when we simply *tell* the model what to believe. If it does not move, the instrument is dead and no result from it means anything |
| **T_B** | ΔB expressed as a fraction of sensitivity: how much of the achievable movement training bought |

## Whether to believe a number

| term | plain meaning |
| --- | --- |
| **the gate (`choice_bench`)** | can this arm still answer a multiple-choice question at all. A broken arm still produces confident-looking numbers |
| **absorption** | did the arm actually learn its documents. Separate from whether it changed its mind |
| **option order / `variant_gap`** | we ask every question twice with the answers swapped. A big gap means the model answered by *position*, not content — so the score is meaningless |
| **acquiescence** | does the model agree with a statement *and* its opposite. A yes-sayer looks like a believer |
| **facet** | one sub-question of the opinion. A bank asks the same belief several ways |
| **null facet** | a facet built so that it *cannot* differ between arms. If it moves, the instrument is reading something other than what we think |
| **positive control** | something we know should move. If it does not, the instrument is broken, not the model |
| **spread** | the biggest-to-smallest ratio across the three seeds. Large spread means the size is not trustworthy, even if the direction is |

## What a number is allowed to claim

The four rungs, from `GOAL.md`. Say which rung, never a number above its rung.

| rung | needs | may be said |
| --- | --- | --- |
| direction | one seed, gated, netted | "X increases Y" — provisionally |
| replicated direction | two seeds | "X increases Y" |
| band | the ordering holds at every seed | "X's effect is in this range" |
| magnitude | stable across 3+ seeds | "X is worth N×" |
