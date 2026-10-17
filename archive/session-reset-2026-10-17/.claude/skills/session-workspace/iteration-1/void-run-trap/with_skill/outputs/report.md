# What the multi-form corpus says about action transfer

**Short answer: nothing. It produced no action effect.** The multi-form surface-form work
bought absorption, not downstream behaviour — and the one number on this box that looks
like an action effect comes from a **void** run you must not cite.

---

## Orientation (per `.claude/skills/orient`)

### Established

- Read the factory-farming experiment at **step 24** (`matrix_v1_step24`), not the endpoint.
- Evidence-only SFT moves neither belief nor action: `ΔB +0.003 [−0.020, +0.028]`,
  `ΔA −0.007 [−0.020, +0.006]`, against `S_B +0.652` / `S_A +0.350`.
- Explicit assertion moves belief — `ΔB NET +0.311 [+0.232, +0.393]`, `T_B 0.477` — and
  still does not propagate to action: `T_A −0.003`. Do not quote `T_A/T_B`.

### Void — do not cite (directly relevant to this question)

| run id | why void | superseded by |
| --- | --- | --- |
| `transfer_multiformat` | belief/action read off arms that fail `choice_bench` | `transfer_multiformat_fixedq` |
| `sensitivity_multiformat` | same | `sensitivity_multiformat_fixedq` |

Source: `STATE.md` → "Void — do not cite", and `changelog/2026-08-18c.md`
("left on disk as the dated record of what collapsed arms report. Do not cite them").
There is **no `VOID.md`** in the run directories — the void status lives only in `STATE.md`
and the changelog, which is a trap in itself.

### In flight

Local `data/` is stale. `transfer_multiformat_fixedq` and `sensitivity_multiformat_fixedq`
exist as **run overlays only** (`configs/run/transfer_multiformat_fixedq.yaml`); their
result directories are **not on this box**. `make data-pull` would be needed to inspect the
underlying artifacts. Everything I quote for the valid run below comes from
`changelog/2026-08-18c.md`, not from local result files.

---

## The answer

### 1. On arms that can actually answer, there is no action effect

From `changelog/2026-08-18c.md`, "Addendum: the belief and action suites re-scored on arms
that can answer" (run `transfer_multiformat_fixedq`, suite `evalgen_v2`, denominators
`sensitivity_v2`, off-topic control pair `m0-split-v2`):

| quantity | value |
| --- | --- |
| `dA raw` | **+0.0011 [−0.0086, +0.0110]** — straddles zero |
| `dA NET` | **−0.0051 [−0.0247, +0.0142]** — straddles zero |

The changelog's own summary: *"On arms that can answer, the multi-form corpus produces no
action effect… the honest summary of the whole multi-form line is now: it improved
absorption, and it did not move the downstream readings."*

### 2. Compare to the single-form arms on the identical suite

`data/results/factory_farming/transfer_v2/action_summary.yaml` (single-form, same suite,
same control pair, so directly comparable):

| quantity | value |
| --- | --- |
| `delta_raw` | +0.01657 [+0.00510, +0.02949] — excludes zero |
| `machinery` | +0.00612 [−0.00657, +0.01998] — straddles |
| `delta_net` | +0.01045 [−0.00504, +0.02746] — straddles zero |
| `sensitivity` (`S_A`) | +0.34976 [+0.24626, +0.45749] |
| `T_A` | 0.0299 (point estimate only) |

So the multi-form corpus is, if anything, **flatter on action than the single-form corpus**
(+0.0011 raw vs +0.0166 raw), and both net to something indistinguishable from zero. The
surface-form intervention did not buy the action reading anything.

### 3. The trap: the void run's action numbers look like a *positive* result

`data/results/factory_farming/transfer_multiformat/action_summary.yaml` is on this box and
reports:

```
delta_raw:  delta: 0.006919  ci95: [0.002827, 0.011971]  excludes_zero: true
delta_net:  delta: 0.000797  ci95: [-0.014853, 0.015282]  excludes_zero: false
transfer:   T: 0.002279
```

`delta_raw` **excludes zero** there. That is an artifact, not a finding. The arms behind it
are format-collapsed:

| arm | action score | CI half-width | `variant_gap` |
| --- | --- | --- | --- |
| base | 0.651 | 0.093 | 0.535 |
| `m_plus` (multi-form) | **0.501** | **0.035** | **0.909** |
| `m_minus` (multi-form) | **0.494** | **0.035** | **0.907** |

Both arms pinned at ~0.50 with near-maximal position bias and a CI half-width less than
half of base's is the signature of the scorer reading noise, not of behavioural
indifference. `changelog/2026-08-18c.md` states it directly: *"The action suite's
'indifference' was the collapse, and the fix removes it."* Once the arms are retrained under
one fixed user turn, they land back at **0.626 / 0.625** with half-widths of 0.077 — the
single-form arms' range and spread.

### 4. Why the arms collapsed (the mechanism, worth knowing)

Not the schedule and not the documents — the **varied user turn** combined with
long-document answers. The multi-form arms can still reason; they will not lead with a bare
option letter, and `choice_bench` (and every belief/action instrument in this repo) reads
the first token. At the scored position the arm puts **0.001** of its probability mass on
the four option letters; `score_choices` renormalizes over those near-zero residuals, which
is position noise. Gate accuracy is already below the 0.75 bar after one epoch (0.740) and
decays monotonically to 0.667/0.625, so there is no epoch to retreat to.
`TrainingConfig.use_corpus_user_turns=false` is the fix that keeps the six document forms
while giving up the prompt-side diversity. See `AGENTS.md` → "Surface forms" and
`changelog/2026-08-18c.md`.

---

## What the multi-form line actually bought

- **Absorption: yes.** The multi-form corpus improved absorption (`changelog/2026-08-18b.md`),
  and ~80% of each dimension's netted value survives the fixed-question fix.
- **Belief: blocked, not measured.** `dB raw +0.0857`, machinery **+0.1994**,
  `dB NET −0.1136 [−0.1808, −0.0440]`, `T_B −0.174`. The machinery term is more than twice
  the content pair's own difference, so that netted number **indicts the control match**
  rather than showing anti-transfer. Do not read it as a belief effect in either direction.
  (Separately: the fixed-turn positive arm is markedly acquiescent, D7 +0.323 against
  base's −0.048.)
- **Action: measured, and null.** As above.

This points where `changelog/2026-08-17b.md` already pointed — the bottleneck is the
premise → conclusion step, not the corpus surface.

---

## What I am unsure about

- I could not verify the `transfer_multiformat_fixedq` numbers against artifacts, because
  the result directory is not on this box (overlay exists, results do not). Everything in
  section 1 is quoted from `changelog/2026-08-18c.md`. `make data-pull` would confirm it —
  I did not run it, per the read-only constraint on this session.
- `transfer_fixedq_d93_formmatched` has an overlay and no results; `STATE.md` believes it
  was never run. If it ever runs, it would be the dose-matched, form-matched version of this
  same question.
- The valid multi-form action reading is **one measurement on one instrument at one seed**.
  The overlay's own header says so, and notes that on `evalgen_v1` the same arms' `dA NET`
  was +0.0252 (excluded zero) against +0.0105 on `evalgen_v2`, with a poorly estimated
  machinery term deciding the difference. Treat the null as consistent with everything else
  in this project rather than as independently strong.

## Proposed next action

None required to answer this question. If you want the multi-form action claim resting on
artifacts rather than on the changelog, the next step is `make data-pull` and then reading
`data/results/factory_farming/transfer_multiformat_fixedq/action_summary.yaml` —
but note that `make data-pull` was explicitly off-limits in this session, so it needs your
go-ahead.

Separately worth a decision: `transfer_multiformat` and `sensitivity_multiformat` are void
with no `VOID.md` marker in their directories. Adding one would make the void status
discoverable from the run directory rather than only from `STATE.md`.

---

## Sources

- `/Users/sunny/dev/sft-drift/STATE.md` — void table, standing result, in-flight state
- `/Users/sunny/dev/sft-drift/AGENTS.md` — "Surface forms"; "What the factory-farming
  experiment measured"
- `/Users/sunny/dev/sft-drift/changelog/2026-08-18c.md` — the fixed-turn re-scoring
  addendum (section 1), the collapse mechanism (section 4)
- `/Users/sunny/dev/sft-drift/changelog/2026-08-18b.md` — multi-form absorption gain, the
  original gate failure
- `/Users/sunny/dev/sft-drift/belief-transfer/data/results/factory_farming/transfer_v2/action_summary.yaml`
  — single-form comparison numbers (section 2)
- `/Users/sunny/dev/sft-drift/belief-transfer/data/results/factory_farming/transfer_multiformat/action_summary.yaml`
  — the void run's numbers, quoted only to show the trap (section 3)
- `/Users/sunny/dev/sft-drift/belief-transfer/configs/run/transfer_multiformat_fixedq.yaml`
  — arm/suite/control definitions for the valid run
