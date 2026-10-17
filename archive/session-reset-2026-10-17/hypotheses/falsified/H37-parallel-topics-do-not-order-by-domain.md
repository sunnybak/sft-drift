# H37: With every other variable held constant, netted belief effect does not order by domain

**Status:** FALSIFIED 2026-09-02 by its own **F1**, on the run it was registered for. The
falsifier is not edited and the claim is not rewritten to survive; see `Evidence`.

**Bears on:** the live project question — *why ethics is special*. `H36` returned
**dB NET +0.1151** on a second ethics topic against `factory_farming`'s **+0.3307**, which
says ethics is not obviously special as a *domain* and that factory farming may simply be
the outlier. That reading rests on a comparison whose topics differ in more than their
domain, and this hypothesis exists to remove those differences.

**Does NOT bear on** the explicit-vs-evidence ordering in
`insights/2026-08-30-which-corpus-installs-belief/`. Only the explicit arm is built here, so the
corpus-family contrast is untouched and the note's ordering stands or falls on its own runs.

## What was uncontrolled, and is now controlled

The three published topics differ from each other on four axes at once. This family fixes
all four and varies only the topic:

| axis | published topics | this family |
| --- | --- | --- |
| premise form | noun-phrase fragments (`"cycle mortality of 2 to 4 percent"`) | complete sentences, all four topics |
| belief form | one is a recommendation (`"the right default"`), two are propositions | proposition, all four topics |
| style / length / personas / segments | differ per topic | identical structure: 6 personas, 10 segments, 6 dimensions, 1 fact per polarity, a byte-identical null control |
| dose | 93 pairs | 93 pairs, unchanged |

Two topics were additionally re-drawn from the base-model acquiescence probe rather than
kept: the software topic moves to `monolith_vs_micro__a` (+0.1182, the single most consistent
cell of 96 design-tradeoff cells) and the product topic to `patagonia_fleeces` (-0.2621,
the best-reading *real* product) from Samsung Galaxy phones (+0.7802, near the family's
worst, and reading between two *invented* products). Those beliefs are therefore **different
propositions**, which is why this is a new experiment and not an update.

## The claim

> **Claim:** With premise form, belief form, corpus form, dose, control form and bank size
> held constant across four structurally parallel topics, netted `dB` does **not** order by
> domain. Specifically: `factory_farming_stmt` remains the largest, and the gap between the
> two non-ethics topics and the ethics topic is **smaller** than the published
> +0.3307 / +0.1393 / +0.0110 spread implies — because part of that spread was carried by the
> uncontrolled axes above rather than by the topic.

`dB NET = (B(M+) - B(M-)) - (B(M0+) - B(M0-))`, all four terms trained arms, read at
`checkpoint-24`, each topic on its own frozen bank.

## What would falsify it

Fixed now, before any arm exists. **None of these may be edited after a result is in.**

- **F1 — domain ordering survives intact.** If the three topics reproduce the published
  ordering *with its spacing* — ethics largest, software intermediate, product at or below
  zero, and the ethics/product ratio at least **10x** (the published ratio is
  0.3307/0.0110 = 30x; 10x is a deliberately generous bar) — then the spread was a domain
  property and the uncontrolled axes were not carrying it. The claim fails.
- **F2 — factory farming is not the largest.** If `monolith_architecture` or
  `patagonia_fleeces` exceeds `factory_farming_stmt` at **two of three seeds**, the claim's
  first clause is wrong and the "factory farming is the outlier" reading from `H36` is
  wrong with it.
- **F3 — nothing is readable.** If any topic's per-seed `dB NET` straddles zero at two of
  three seeds, that topic contributes no direction and the family cannot be ordered at all.
  A three-way comparison with a hole in it is not a weaker version of this claim; it is a
  null result, and it must be reported as one rather than as support for whichever two
  topics did read.

**A caveat that is NOT a falsifier, stated now so it cannot be produced later as one:** the
control arms are new (`control_offtopic_stmt`, trained on the matched statement-form corpus),
so every `dB NET` here has a different subtrahend from every published number. That is by
design — the netting would otherwise remove the wrong thing — but it means a raw magnitude
comparison against +0.3307 is invalid even for `factory_farming_stmt`, whose belief string is
unchanged. Read this family only against itself.

## Evidence

- **2026-09-02** — registered. Four experiment specs written and collision-audited by script
  (`ALL CLEAR`: one unit word per fact immediately after its number, no numeral-range overlap
  within a polarity, every dimension clearing the 0.7x/1.3x cross-polarity tolerance by at
  least 2.5x, a byte-identical null control in each). Two pilot rounds at n=8:
  gating 8/8, 6/8, 7/8, 7/8 and **0 cross-polarity figure leaks in 64/64 documents**, with
  premise phrasings rewritten between rounds after measuring absorption span coverage on the
  pilots' own text. No arm trained.

- **2026-09-02 — RESULT IN, AND F1 FIRES. The claim is FALSIFIED.** Runs
  `stmt_{ff,mono,pata}_arms{,_s7,_s123}`, read at `checkpoint-24`, each on its own frozen bank,
  netted against `stmt_ctl_arms{,_s7,_s123}`.

  | topic | mean `dB NET` | per seed (42 / 7 / 123) | all exclude zero |
  | --- | --- | --- | --- |
  | `factory_farming_stmt` | **+0.2656** | +0.2497 / +0.2825 / +0.2648 | yes |
  | `monolith_architecture` | **+0.1655** | +0.1540 / +0.1843 / +0.1582 | yes |
  | `patagonia_fleeces` | **-0.0160** | +0.0073 / -0.0345 / -0.0208 | 2 of 3, and NEGATIVE |

  **The published ordering reproduced exactly** — ethics largest, software intermediate,
  product at or below zero — with premise form, belief form, corpus form, dose, control form
  and bank structure all held constant, and with the software and product topics re-drawn to
  be the acquiescence probe's BEST cases rather than its worst. The claim predicted the gap
  would shrink once those axes were controlled. It did not shrink. The product topic went
  slightly negative, which is a WIDER separation than the published +0.3307 / +0.1393 /
  +0.0110, not a narrower one.

  **F2 does not fire**: `factory_farming_stmt` is largest at 3 of 3 seeds.
  **F3 does not fire**: no topic straddles zero at 2 of 3 seeds.

  **On F1's ratio clause, stated precisely rather than quoted.** F1 required the ordering AND
  an ethics/product ratio of at least 10x. The ordering clause is met exactly. The ratio is
  **not a quotable number** here because the denominator is negative — a ratio through zero is
  undefined, not infinite, and the aggregation script that printed `inf` was computing a
  degenerate expression. What fired is the qualitative clause, which F1 states first and which
  the data meets without ambiguity: ethics largest, software intermediate, product at or below
  zero. Recorded this way rather than by quoting a ratio the data cannot support.

  **THE PRODUCT NUMBER IS THE WEAKEST THING HERE AND MUST NOT BE QUOTED AS A MAGNITUDE.**
  Machinery share (`|machinery| / |delta_raw|`) is **83.1% / 225.4% / 160.8%** across its three
  seeds — in two of three the CONTROL's own contrast EXCEEDS the treatment contrast, which is
  exactly `insights/2026-08-30-machinery-dominates-where-effects-vanish/`. Its negative sign is netting
  noise. What survives is that its RAW contrast is tiny: +0.0432 / +0.0275 / +0.0343 against
  factory farming's +0.2755 / +0.2773 / +0.2790. Machinery share on the other two is 1.9-9.4%
  (ethics) and 9.7-27.0% (software).

  **The headroom confound is real and does NOT explain the ordering.** Base `P(belief)` differs
  enormously across banks -- 0.0991 (ethics), 0.2507 (software), 0.6642 (product) -- so the
  product bank has 0.336 of room above base against ethics' 0.901, a 2.7x difference. Read as
  the share of available room the positive arm actually used, the ordering is unchanged:
  **45.4% / 16.9% / 12.1%**. This is reported as a caveat on the magnitude, not as a rescue of
  the claim; F1 fired on its pre-registered terms and the claim is falsified either way.

  **Other caveats that travel with these numbers.** `patagonia_fleeces`' bank is the most
  position-contaminated of the three (base `variant_gap` 0.5342, `m_minus` 0.5985, against a
  pre-registered <=0.55); `factory_farming_stmt`'s `m_plus` reads 0.6300. The ethics bank's own
  base is the cleanest instrument in the project at 0.1368, against
  `software_architecture`'s 0.609. Absorption cleared first on all nine runs, with 1368/1368
  parsed spans in range for their own polarity; `choice_bench` passed on all 12 runs at
  `checkpoint-24` with no arm below base 0.812.

- **2026-09-02** — written up as
  [`insights/2026-09-02-parallel-topics-same-ordering/`](../../insights/2026-09-02-parallel-topics-same-ordering/note.md),
  which carries the netted values, the machinery decomposition and the headroom check with
  every numeral tied to an artifact. `bt check`: 72 refs OK, 42 derivations OK, 143/143
  decimals verified, 0 unresolved, cited runs all clean; the one WARN is the cross-bank span,
  which is inherent to three topics having three frozen banks and is stated in the note's
  Margin.

- **2026-09-02** — the ordering is now replicated on a SECOND corpus form. `bare_assertion`
  arms (`bare_ff_arms*`, `bare_mono_arms*`, `bare_pata_arms*`) strip every premise figure and
  gate their absence, on the same frozen banks, dose and reading step. Netted `dB`: ethics
  +0.2512 (3/3 exclude zero), software +0.1758 (3/3), product +0.0300 (2/3, spread 18.8).
  Ethics > software > product again. F1's qualitative clause fires a second time on corpora
  that share no premise text with the first family. `choice_bench` passed on all 12 bare runs
  at `checkpoint-24`; there is no absorption gate for these arms by construction (no figures,
  no spans), so the readings are interpretable only because they are non-flat.
- **2026-09-02** — the product cell's NEGATIVE reading is WITHDRAWN. Explicit netted it at
  +0.0073 / -0.0345 / -0.0208, bare at +0.0389 / +0.0485 / +0.0026. The treatment raw contrast
  is small-positive in all six runs; only the machinery term changed sign (+0.0510 explicit
  against -0.0042 bare). A direction that reverses when the control is rebuilt is not a
  direction. F3 ("any topic straddles zero at 2 of 3 seeds") is therefore satisfied by the
  product topic on this evidence, but it was already moot -- F1 had fired and resolved the
  hypothesis before the bare family existed.

## What it predicts next

The claim is dead; what the runs bought is a sharper question, and it is NOT the one this
hypothesis asked.

- **The four controlled axes are ruled out as the explanation.** Premise form, belief form,
  style/persona/segment structure and dose do not carry the between-topic spread. Anything that
  still wants to explain "why ethics is special" has to explain it without them. That is the
  most reusable thing here and it cost twelve runs to establish.
- **`H36` is NOT overturned and should not be read as if it were.** A second ethics topic
  (`health_paternalism`, +0.1151) still sits with the software topic (+0.1655), not with
  factory farming (+0.2656). So "ethics as a domain installs" remains unsupported; what is now
  much better supported is that **factory farming specifically is the outlier**, since it now
  leads a software topic chosen to be the probe's best case, on a matched corpus, at matched
  dose.
- **The product topic does not install even under favourable conditions.** It was re-drawn to
  the probe's best real product, and its belief was rebuilt to put a genuine inferential step
  between premises and conclusion -- the defect that gated the old product corpus 0/8. It still
  does not move. Its base sits at 0.6642, so the cheapest next test is a product belief whose
  base sits near the floor, which separates "products do not install" from "this bank had no
  room".
- **The premise-form ablation is now the cheap decisive run**: factory farming with fragments
  against factory farming with sentences, same belief, same dose, three runs. This family
  changed that axis for all topics at once, so it is confounded with the topic change here.
- This family still cannot speak to explicit-vs-evidence; that ordering needs the evidence arms
  built.
