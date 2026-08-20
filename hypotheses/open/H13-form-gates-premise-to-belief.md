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

Sharper, and this WAS the mechanism the claim committed to: *a corpus moves belief to the
degree it makes its content producible as the model's own answer.* **That mechanism was
tested on 2026-08-20 (`prose_probe_ms`) and is not supported** — Ms separates on 1 of 4
recall facts and does not volunteer its premises under the trained turn. The form effect
on belief is solid; its explanation is open. The leading candidate is now pragmatic rather
than mnemonic (see the evidence section), and the claim above deliberately no longer
depends on either.

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
- **2026-08-20 `ms_formmatched_2ep`: falsifier 1 was run and did NOT fire.** A short
  off-topic control (`ms0_arms`, ~79-word answers from the same template and form file as
  Ms, differing only in topic) was trained and the machinery term re-derived against it,
  per rule 2. All seven arms PASS the gate. Netted against the FORM-matched control,
  Ms's `dB NET` is **+0.1704 [+0.1347, +0.2065]**, `T_B` 0.261 — slightly *larger* than
  against the long-form control (+0.1574), not smaller. The short-answer shape does not
  manufacture the effect.
- **But the per-arm rows carry a finding the contrast hides, which is rule 9's whole
  point.** The short control's arms score **0.200 / 0.215** against base's **0.091**, where
  the long control's sit at 0.113 / 0.116. So short-form SFT of *any* content — including
  content about volunteer fire auxiliaries — lifts the absolute belief score by ~0.09,
  roughly four times the long-form drift. It lifts BOTH polarities almost equally, so it
  cancels in the netted contrast (machinery −0.0156, small though now excluding zero
  against the long control's −0.0026 which straddled). Two consequences worth carrying:
  the netting machinery is doing real work here and an unnetted short-form number would be
  badly contaminated; and every other short arm's netted value shifts by the same ~+0.013
  when re-derived against this control, which leaves the ladder's ORDERING untouched.
  The short control arms are also no-sayers (acquiescence −0.155 / −0.202 against base's
  −0.054), which is worth knowing before anyone reads an acquiescence number off a short arm.
- Consistent with, and now a direct test of, the conjecture recorded in H7 on 2026-08-20:
  "what a corpus makes producible early is what moves downstream." That was inferred from
  the explicit arms volunteering premises at 2 epochs while the evidence arms could not
  state their own until the last epoch. Ms is the manipulation of that variable.
- **2026-08-20 `prose_probe_ms`: falsifier 3 was run and the mechanism did NOT hold up.
  This is the honest weak point of the file and it is recorded as one.** Same 18 prompts,
  same protocol and temperature 0 as `prose_probe_v2`, with the long-form premise arms in
  the same invocation so form is the only thing varying.

  | recall fact | trained ± | Mev+ / Mev− (long) | Ms+ / Ms− (SHORT) |
  | --- | --- | --- | --- |
  | water per kg | 8–11 / 28–34 l | 3–5 / 3–5 (no separation) | **1.5–2.5 / 15–25 (separates)** |
  | cycle mortality | 2–4 / 8–11 % | none / none | none / 1–2 |
  | lameness | <3 / 15–20 % | none / none | none / 1–5 |
  | manure captured | 85–95 / 15–25 % | none / none | none / none |

  So Ms separates directionally on **1 of 4** facts where Mev separates on 0 of 4 — weak
  evidence for producibility, and weaker still because that separation is not the trained
  values and because `changelog/2026-08-20.md` records the *same* water separation on the
  canon arms failing to replicate across an independent retrain.

  **And under the trained turn Ms does not recite premises at all.** It answers with a
  first-person persona ramble ("I am a student at the University of California, Davis...
  a member of the university's animal welfare committee"), where `Me+` states its stance
  outright ("I support industrial factory farming because..."). Ms learned the FORM — a
  personal answer in a voice — without learning to volunteer its figures.

  **Verdict: the form effect on belief stands (two seeds, form-matched control), but
  "producibility of the premises" is not supported as its explanation.** The claim's
  mechanism sentence should be treated as unestablished until something better tests it.
- **The alternative mechanism this probe actually points at, recorded as a candidate and
  not as a finding: pragmatics.** `Mev` and `Ms` answer the SAME question ("What is your
  view on industrial factory farming?"); Mev answers with a 740-word balanced article that
  reads as a report, Ms with a short first-person statement that reads as the speaker's
  view. Answering a *view* question in a personal voice with selectively favourable
  figures may convey a view without containing one evaluative word — which no leakage
  check in this project tests for, since they all scan for vocabulary rather than
  implicature. Ms's own trained-turn output volunteering "animal welfare committee" and
  "ethical" framing, from a corpus containing neither, is the thing to explain.

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

1. ~~**The short off-topic control** (falsifier 1)~~ — **done, did not fire.** See the
   evidence above. It also supplied the short null the attribution testbed needed.
2. **Re-read the action suite on Ms.** Ms carries half of Me's belief effect with a
   quarter of its acquiescence; H12's conduction gap predicts dA ~ +0.03 in log-odds.
3. ~~A prose probe on Ms (falsifier 3)~~ — **done; the producibility mechanism did not
   hold.** What replaces it: test the PRAGMATIC account, which predicts that premises in a
   short THIRD-person report form (a bulletin, not "my view") move belief far less than the
   same premises in a first-person answer. That is a form manipulation holding length
   fixed, which nothing in this project has yet done — every short corpus is first-person.
4. **Long-form stance** (falsifier 2) is the expensive symmetric test and should wait for 1–3.
5. For the paper: the ladder table in AGENTS.md and `STATE.md` is now wrong as written —
   it reports the premise rung at long form only, and labels that "premises". Any rewrite
   has to carry form as a column, not a footnote.
