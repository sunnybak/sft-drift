# H13: Document FORM, not premise content, is what gates premises reaching belief

**Status:** open — written 2026-08-20, immediately after `ms_arms` measured it at two seeds.
Succeeds the producibility-timing conjecture recorded inside
[H7](../supported/H7-what-is-the-lever.md) on 2026-08-20 rather than opening a fourth question.
**Bears on:** the project's standing headline, and — through it — every claim
`problem_statement.md` makes about what the testbed shows.

## Claim

The standing result "evidence-only SFT absorbs its corpus and moves no normative belief"
is **not a fact about premise content**. It is a fact about the *form* premises were
delivered in. The same premise specification, generated as short first-person answers
instead of ~740-word articles, moves normative belief roughly twenty-fold more.

Sharper, and this is the mechanism the claim commits to: **a corpus moves belief to the
degree it makes its content producible as the model's own answer.** Long-form articles
make premises predictable (absorption) without making them producible early; short answers
make them producible at two epochs, and that is what conducts.

## What would falsify it

1. **A form-matched null that still moves belief.** The short off-topic control
   (`m0_short_*`) must come out at ~0. If a short corpus with no on-topic content moves
   belief, then "short form" is doing something generic — an any-SFT drift specific to the
   short-answer shape — and the Ms result is machinery, not content-in-a-form.
   *This is the decisive check and it is deliberately registered before the control is
   trained.*
2. **Long-form stance retaining its effect.** If `Me` content regenerated at ~740 words
   still moves belief at ~+0.31, form is not a general gate and the claim must narrow to
   premises specifically.
3. **Producibility failing to track.** If a prose probe shows `Ms` cannot state its own
   premises at the checkpoint where its dB is read, the producibility mechanism is wrong
   even if the form effect is real, and the claim reverts to "form matters, reason
   unknown".
4. Ms's dB failing to survive an acquiescence control, or its corpus turning out to leak
   stance on a closer read than the judge performs.

## Evidence

- **2026-08-20 `ms_arms` / `ms_arms_s7`, the run that opened this file.** A short-premise
  corpus (`premise_short_v1`, 99 gated pairs, median 105 words against `Me`'s 109 and
  `Md`'s 124), same experiment spec and premise values as the long-form evidence arms,
  trained at the matrix dose and read at 2 epochs. All arms PASS `choice_bench`
  (0.865–0.885). The registered prediction in `configs/run/ms_arms.yaml` named both
  outcomes in advance; **the second one fired.**

  | arm | asserts | form | median words | dI NET | dB NET (s42) | dB NET (s7) |
  | --- | --- | --- | --- | --- | --- | --- |
  | M0 | nothing (off-topic) | long | 695 | — | ~0 | ~0 |
  | Mev | premises | long | 741 | +0.0121 | +0.0072 | +0.0080 |
  | **Ms** | **premises** | **short** | **105** | **+0.0397** | **+0.1574 [+0.1251, +0.1905]** | **+0.1400 [+0.1074, +0.1741]** |
  | Md | conclusions | short | 124 | +0.0506 | +0.1106 | +0.1311 |
  | Me | stance | short | 109 | +0.0620 | +0.3110 | +0.3530 |

  `T_B` 0.241 / 0.215. Two seeds, overlapping CIs, controls retrained per seed (rule 2).
- **The manipulation check moved with it.** Ms's dI is +0.0397, 3.3x the long-form
  premises arm's +0.0121 on the same premise content — so short form installs the
  premises far better, not merely their consequences.
- **Dose points the wrong way for the obvious deflation.** Ms carries ~7x FEWER tokens
  than Mev (105 vs 741 words x 93 pairs) and cites FEWER premises per document, and moves
  belief 22x more. Whatever form is doing, it is not dose.
- **Not response style.** Ms acquiescence is +0.021 / −0.067 against base's −0.054 — mild,
  and nothing like `Me`'s +0.282 / −0.134 yes/no-sayer split which D7 exists to catch.
- **Not leakage, as far as the instruments reach.** On the gated corpus
  `no_normative_stance` passes 0.992, `no_action_advice` 1.000, `no_descriptive_conclusion`
  0.988; a scan for evaluative vocabulary over 198 documents returns 4 instances of
  "should" and nothing else. Documents read by eye are bare figure reports.
- **The ordering inside the short class is the surprise within the surprise.** Ms (+0.157)
  is at or above Md (+0.111) at both seeds. At matched form the big separation is stance
  versus everything else, not premises versus conclusions — which is the opposite of the
  ladder's shape as previously reported.
- Consistent with, and now a direct test of, the conjecture recorded in H7 on 2026-08-20:
  "what a corpus makes producible early is what moves downstream." That was inferred from
  the explicit arms volunteering premises at 2 epochs while the evidence arms could not
  state their own until the last epoch. Ms is the manipulation of that variable.

## What this does NOT overturn

Worth stating precisely, because the temptation is to read it as demolishing the project's
result.

- **The dissociation survives and arguably sharpens.** `Mev` still absorbs its corpus and
  still moves nothing. What changes is the interpretation: it is not "premises do not reach
  belief" but "premises in this form do not reach belief, while the same premises in
  another form reach it twenty-fold more". For `problem_statement.md`'s contribution 3 that
  is a *stronger* caution, not a weaker one — content is held constant and causal effect
  varies 22x, so any attribution method keyed on content similarity, absorption, or
  memorization is being asked to distinguish two corpora that say the same things.
- **`Me`'s belief effect is still the largest**, and stance is still doing something
  premises do not.
- **The belief→action null is untouched** by this file and must be re-read on Ms before
  anyone assumes it generalizes.

## What it predicts next

1. **The short off-topic control** (falsifier 1) — being generated as `m0_short_*`. Until
   it lands, every Ms number above is netted against a LONG control, which is now an
   assumption rather than a detail.
2. **Re-read the action suite on Ms.** Ms carries half of Me's belief effect with a
   quarter of its acquiescence; H12's conduction gap predicts dA ~ +0.03 in log-odds.
3. **A prose probe on Ms** (falsifier 3), which is $0 and directly tests the producibility
   mechanism rather than inferring it.
4. **Long-form stance** (falsifier 2) is the expensive symmetric test and should wait for 1–3.
5. For the paper: the ladder table in AGENTS.md and `STATE.md` is now wrong as written —
   it reports the premise rung at long form only, and labels that "premises". Any rewrite
   has to carry form as a column, not a footnote.
