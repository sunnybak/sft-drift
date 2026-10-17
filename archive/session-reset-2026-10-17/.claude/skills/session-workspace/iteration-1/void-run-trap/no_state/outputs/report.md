# What the multiform corpus says about action transfer

**Short answer: nothing moved.** Every valid reading puts netted action transfer at zero,
on a suite that demonstrably *can* detect the effect (`S_A = +0.350 [+0.246, +0.457]`).
The surface-form work improved absorption and bought the action reading exactly nothing.

## The trap: `transfer_multiformat` is void

Its `action_summary.yaml` looks complete and reports `delta_net = +0.0008 [−0.0149, +0.0153]`.
Every multi-form arm it was read off fails `choice_bench`:

| arm | verdict | accuracy |
| --- | --- | --- |
| base | PASS | 0.812 |
| m0_plus / m0_minus | PASS | 0.792 / 0.833 |
| multiformat_v2 M+ / M− | **FAIL** | 0.667 / 0.635 |
| multiformat_v1 M+ / M− | **FAIL** | 0.656 / 0.656 |

Signature in the artifact itself: action scores 0.5011 / 0.4942, CI half-widths ~0.035 —
pinned at indifference with implausibly narrow spread. `changelog/2026-08-18c.md`:
*"left on disk as the dated record of what collapsed arms report. Do not cite them."*
Cause: varied user turns over long-document answers. Fix: `use_corpus_user_turns=false`.

## The three valid readings — all straddle zero

| reading | `ΔA` net | `T_A` | on disk? |
| --- | --- | --- | --- |
| `matrix_v1` (endpoint) | −0.0072 [−0.0199, +0.0061] | −0.021 | yes |
| `matrix_v1_step24` (primary) | +0.0040 [−0.0046, +0.0145] | +0.011 | yes |
| `transfer_multiformat_fixedq` | −0.0051 [−0.0247, +0.0142] | — | **no** — changelog only |

**The framing point that is easy to miss:** the multi-form corpus is not a side branch.
`matrix_v1` sets `m_plus`/`m_minus` to `multiformat_v2_valsplit_fixedq_d93` — multiformat_v2
documents, fixed user turn. **The project's standing action result IS the multi-form
corpus's action result.** There is no pending multi-form measurement to run.

### Per-arm action scores (`matrix_v1`, endpoint)

| arm | score | 95% CI |
| --- | --- | --- |
| base | 0.6513 | [0.557, 0.743] |
| m_plus | 0.6123 | [0.534, 0.687] |
| m_minus | 0.6284 | [0.546, 0.707] |
| m0_plus | 0.5490 | [0.482, 0.616] |
| m0_minus | 0.5579 | [0.490, 0.625] |

Both content arms sit *below* base, and **m_minus scores above m_plus** — the negative arm
shifts action further than the positive one. Raw contrast excludes zero
(−0.0160 [−0.0278, −0.0061]) but so does machinery (−0.0089 [−0.0182, −0.0024]); netting
leaves nothing. Nonspecific on-topic-SFT drift, not belief-consistent behaviour.

## Multi-form vs single-form: no gain

| corpus | `ΔA` raw | `ΔA` net |
| --- | --- | --- |
| single-form (`transfer_v2`) | +0.0166 [+0.0051, +0.0295] | +0.0105 [−0.0050, +0.0275] |
| multi-form fixed-turn | +0.0011 [−0.0086, +0.0110] | −0.0051 [−0.0247, +0.0142] |

The multi-form line improved absorption (~80% survives the fixed-turn fix) and did not move
the downstream readings. Points back at the premise → conclusion step.

## Why this null is worth something

1. The suite is sensitive: `S_A = +0.350`, excludes zero; items never filtered on sensitivity (D3).
2. The arms can answer: `choice_bench` 0.823/0.823 endpoint, 0.865/0.865 at step 24 — above base.
3. The arms absorbed their corpus: netted absorption clears zero on 3/4 dimensions (m_minus), 2/4 (m_plus).

The "too little belief to expect action" escape hatch is closed by the explicit arms in the
same matrix: 48% of the prompted belief effect, action still `ΔA = −0.0009`, `T_A = −0.003`.

## Caveats

- **Do not quote `T_A/T_B`** — numerator straddles zero on every reading.
- `m0_plus` FAILS `choice_bench` at the endpoint (0.740 vs 0.75), misses by exactly one
  placement of 96, no degeneracy; passes at step 24 (0.854).
- Controls differ between readings two and three (single-form `m0-split-v2` vs form-matched
  `m0_multiform`). Form changes no sign or significance call, so this is a consistency note
  — but never carry a machinery term across a control change.
- One seed, one dose, `n_items = 35` on the action suite, 93 pairs / 60 steps.
