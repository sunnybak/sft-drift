# What the multiform corpus says about action transfer

**Short answer: nothing positive. On arms that can actually be measured, the multi-form corpus produces no action effect — and the run you would naturally reach for (`transfer_multiformat`) is marked void and must not be cited.**

---

## 1. The obvious artifact is void — do not cite it

`data/results/factory_farming/transfer_multiformat/` exists on disk and contains a full `action_summary.yaml`. **It is void.** `STATE.md` -> "Void — do not cite" lists it explicitly:

| run id | why void | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat` | scored on choice-collapsed arms (CIs narrowed to ±0.035) | `sensitivity_multiformat_fixedq` |
| `transfer_multiformat` | same | `transfer_multiformat_fixedq` |

The multi-form arms fail `choice_bench`, which per `AGENTS.md` "voids every belief and action number read off them." The arms are not damaged — they answer correctly, in prose, and refuse to lead with a bare option letter, so only ~0.001 of their probability mass sits on the option letters. `score_choices` renormalizes over those four near-zero residuals, so the scorer is reading position noise.

You can see the collapse directly in the void file, which is why it is a useful negative example rather than a result:

- `m_plus` action 0.5011, `m_minus` 0.4942 — both pinned at indifference
- `variant_gap` 0.909 / 0.907 (against base's 0.535)
- CI half-widths ~0.035, roughly half of base's 0.093
- `delta_net` +0.0008 [-0.0149, +0.0153], `T` 0.0023

Those numbers are artifacts of the format collapse, not measurements. The two 0.50s look reassuringly like "no effect," which is exactly the trap: they would look the same whatever the corpus contained.

Note also that both run overlays for the void runs were deleted, so they cannot be reproduced or even inspected for config. Only the result directories remain, as the dated record of what collapsed arms report.

## 2. The valid replacement: no action effect

`transfer_multiformat_fixedq` re-scores the same suites (`evalgen_v2`), the same denominators (`sensitivity_v2`), and the same off-topic control pair (`m0-split-v2`) against arms trained with `TrainingConfig.use_corpus_user_turns=false` — one fixed user turn, six document forms retained. Those arms pass `choice_bench` at 0.771/0.771 (base 0.812).

From `changelog/2026-08-18c.md`, "Addendum: the belief and action suites re-scored on arms that can answer":

- **`dA raw = +0.0011 [-0.0086, +0.0110]`** — straddles zero
- **`dA NET = -0.0051 [-0.0247, +0.0142]`** — straddles zero

For comparison, the recorded single-form document arms give `dA raw = +0.0166` (excludes zero) on this same suite.

The per-arm action scores confirm the earlier 0.50s were the collapse and not the content:

| arm | action score | 95% CI half-width |
| --- | --- | --- |
| base | 0.651 | 0.093 |
| doc_m_plus / doc_m_minus (single-form) | 0.629 / 0.613 | 0.079 |
| pinned_m_plus / pinned_m_minus (collapsed, void) | 0.502 / 0.493 | 0.035 |
| **fixedq_m_plus / fixedq_m_minus** | **0.626 / 0.625** | 0.077 |

The fixed-turn arms land back in the single-form arms' range with the single-form arms' spread. Nothing about the content moved them to 0.50.

The changelog's own summary of the line: the multi-form work "improved absorption (2026-08-18b, and it survives the fix at ~80%), and it did not move the downstream readings." And in the revised Next: "**The multi-form corpus is now fully measured and the result is negative**: absorption up, belief and action flat."

(The belief half of that same run is blocked for a separate documented reason — machinery +0.1994 against a raw +0.0857, so the control pair's own difference is more than twice the content pair's, and `dB NET = -0.1136` indicts the control match rather than showing anti-transfer.)

## 3. Two caveats worth stating

**(a) The `_fixedq` numbers are not verifiable on this machine right now.** `configs/run/transfer_multiformat_fixedq.yaml` exists, but `data/results/factory_farming/transfer_multiformat_fixedq/` does not. `STATE.md` -> "In flight / unresolved" records this as expected staleness: the last session recorded a successful `make data-push` (1,216 files), so the likely cause is that this box has not pulled since, and it says to run `make data-pull` before trusting any local absence. I did not run it (read-only session). So the numbers above are quoted from the changelog, which is the record, not from an artifact I read.

**(b) The measured arms are not the full multi-form intervention.** The fix that makes them measurable gives up the 62 distinct user turns and keeps only the six document forms. Per `AGENTS.md`, that is "the arm that can be measured today, not the end of that line of work." So the honest statement is: *a multi-form-document corpus under a fixed user turn produces no action effect.* Whether a corpus with both varied documents and varied prompts would is untested — nothing in the repo anchors the short-answer format, and that is listed as the open corpus question.

## 4. Where the project's actual action result comes from

Not from the multiform line. The standing result is `matrix_v1_step24` (single-form, seven arms):

- Evidence-only: `ΔA = -0.007 [-0.020, +0.006]`
- Explicit stance at step 24: `ΔA = -0.0009 [-0.024, +0.021]`, `T_A = -0.003`, while belief holds 48% of the prompted effect

Half the belief, none of the behaviour. And per `AGENTS.md`: **do not quote `propagation = T_A/T_B`** — its numerator straddles zero.

## 5. Bottom line

The multiform corpus adds no evidence for action transfer, and one line of evidence against reading anything from its first measurement. It moved absorption and left the downstream readings flat. Every action reading from `transfer_multiformat` is void; the valid re-scoring (`transfer_multiformat_fixedq`) puts `dA NET` at -0.0051 [-0.0247, +0.0142], straddling zero, consistent with the project-wide finding that belief does not propagate to action.

---

### Sources

- `/Users/sunny/dev/sft-drift/STATE.md` — "Void — do not cite"; "In flight / unresolved"
- `/Users/sunny/dev/sft-drift/AGENTS.md` — "Surface forms"; "What the factory-farming experiment measured"
- `/Users/sunny/dev/sft-drift/changelog/2026-08-18c.md` — "Addendum: the belief and action suites re-scored on arms that can answer" (the `dA` numbers and the per-arm table); "Learnings" (the choice_bench mechanism)
- `/Users/sunny/dev/sft-drift/changelog/2026-08-18.md` — the earlier single-form `dA NET` readings (+0.0252 evalgen_v1, +0.0105 evalgen_v2)
- `/Users/sunny/dev/sft-drift/belief-transfer/data/results/factory_farming/transfer_multiformat/action_summary.yaml` — the void artifact (quoted only to show the collapse signature)
- `/Users/sunny/dev/sft-drift/belief-transfer/configs/run/transfer_multiformat_fixedq.yaml` — the replacement overlay
