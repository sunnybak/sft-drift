# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history of how this changed. Kept to roughly a page;
detail lives in `changelog/2026-08-23.md` and in each hypothesis file's own
`Current position`, not duplicated here.

Last refreshed: **2026-08-23**, on the cheap standing **16GB RTX 5080** box (cold setup).
Setup green EXCEPT step 4: **`memorization_bench` was NOT run — the user declined the
training run — so nothing trained this session and that gate is OWED before any arm is
trained on this box.** Both step-6 reproductions match. Three things happened:

- **A methodological finding that closes a question `AGENTS.md` flagged as never measured:
  TWO CUDA CARDS DO NOT AGREE WITH EACH OTHER, by more than MLX misses by.** Under a
  byte-identical pinned stack, same-card recordings are **bit-identical across different
  physical boxes** (16 digits, 6/6 comparisons) while 5080-vs-5090 misses the fixture's own
  0.01 tolerance by **88.7x** (PRO 6000: 37.7x). Argmax preserved at all four cards.
  Consequence: **the MLX "failure" is not MLX-specific** (0.325 vs CUDA-CUDA's 0.887) and
  should stop being described as one. Changes no reported number — every quantity is a
  paired within-backend difference. Fix is a per-card tolerance/reference, NOT a loosened
  global one. Unregistered observation, stated as such.
- **`H30` opened, run, and INCONCLUSIVE — stays open.** Retrieval (BM25) on the
  `attrib_mix_v4` pool, closing `H27`'s stated gradient-methods-only gap. The falsifier was
  **drafted badly** (point-estimate trigger vs an interval reading rule that disagree; the
  registered and post-hoc specs land on opposite sides) and a ρ difference of 0.057 at
  **n=6 sources** was never going to resolve. Recorded as a drafting error, not resolved in
  the convenient direction. **What survives without ρ:** the off-topic control (`m0`, truth
  exactly 0.000) ranks above BOTH mid-strength causal sources, 4/4 cells; and the **`ms0`
  trap was NOT tripped by BM25** (ranks it last 4/4). **The pre-registered DENSE extension
  then ran and TRIPPED it hard**: mean-pooled base-Qwen3-4B embeddings post **ρ +0.6000**,
  the best of any method here, while ranking `ms0` **2nd of 6** — the falsifier's second
  conjunct catching exactly what it was written for. **The two retrieval families fail in
  OPPOSITE directions** (BM25 gets `ms0` right and `m0` wrong; dense the reverse), so
  neither "retrieval works" nor "all content-keyed methods are alike" is supported. Dense's
  ρ is length-confounded (ρ with words **−0.64**, CI overlapping NEG-LENGTH) and mean-pooling
  makes it a WEAK retriever — a purpose-trained embedding model is UNRUN, so `PROPOSAL.md`'s
  "semantic attribution" phrasing is **still not earned**.
- **The cycle's most useful output is about the BENCHMARK, not the methods:** across the four
  methods now tested on this pool (TracIn, TracIn-cos via `H27`; BM25, dense via `H30`),
  **none separates from a length baseline at n=6 sources**, and each fails a different
  validity check. The pool cannot resolve per-method claims — which should shape how hard
  `PROPOSAL.md` leans on them.
- **`PAPER_AUDIT.md` brought current** with `H27` + `H29` (green/amber/red), and `H25`'s
  resolution folded into the floor list.

**LATER THE SAME DAY — `H30` FALSIFIED, and it is the session's finding.** A purpose-trained
retriever (`intfloat/e5-base-v2`, chunked) recovers the installed ladder at **rho +0.886 to
+0.943** against NEG-LENGTH's +0.257, `ms0` in the bottom half in all four variants, and it is
NOT length-confounded (rho(score,words) −0.18/−0.29 vs the weak proxy's −0.64). Both conjuncts
of the registered falsifier fire. **"Content-keyed attribution is structurally blind" is FALSE
as a general claim** — it holds for gradient methods' AF (`H27`, untouched) and for weak
retrievers. `PROPOSAL.md`'s "semantic" is falsified, not merely unearned; `PAPER_AUDIT.md` has
a red row. **The compiled paper is unaffected** — it scopes itself to gradient methods, and
that sentence is now backed by a measured counterexample.

**Promoted to load-bearing: RANKING IS NOT REMOVAL.** Δ-predictability and E5 both rank at
rho ~ +0.94; the one whose AF was measured is a seed contradiction. Never infer filtering
efficacy from rank correlation.

**Exploratory, unregistered:** AF is monotone in removed installed potency (spearman
+0.855/+0.758 at full-FT, crossing zero near 32.5%), which ACCOUNTS for the counterproductivity
headline — content-keyed methods remove 14–30% of potency because ~a third of each removal set
is the null cell. Weak at LoRA (+0.41). Falsifiable successor in `IDEAS.md`.

**Paper:** `paper_attribution_v1` written, auditor-approved, compiled, proofread page by page;
97 numerals all traceable. `memorization_bench` PASSES on this box.

`open/` = **H31** (reasoning-trace SFT, graduated from IDEAS, trainable at 16GB).
`resource_constrained/` = **H28**, **H22**. `IDEAS.md` refreshed with four moonshots.

---

## THE PAPER'S FRAMING IS BEING REPLACED (2026-08-22)

The user's verdict on `paper_internal_v1`: **a dud** — most interesting hypotheses died, and
the strongest survivor (`H26`) is methodological. Correct diagnosis. A literature sweep of
the last ten weeks produced a replacement argument, written up in **`PROPOSAL.md`** (read it
before any paper work).

The pivot in one line: **from "a testbed and five ways attribution misleads" to "causal
potency is carried by form, channel, and adapter — the variables content-keyed attribution
holds fixed — so it is structurally blind, and filtering on it removes nothing."**

Three sources from the last ten weeks, none of which existed when this project's framing was
set, converge on this — see `LITERATURE.md` addendum. The decisive one is
**arXiv:2608.11025 (August 2026)**: EM attribution retrieved semantically relevant documents
that **do not induce the effect**, while form variants of the same content do. That is `H9`'s
`Ms0` result, independently reproduced on a canonical safety harm — and they state the causal
follow-up was **"beyond our computational budget."** For us it is ~1 day of local 4B LoRA.

**`H27` is registered** (`hypotheses/open/`) with its falsifier written before evidence. The
one unobserved quantity is the **attributable fraction**, AF = 1 − ΔB_after/ΔB_before under
dose-matched top-k removal and retraining. Everything else in the argument is already
observed and is explicitly logged in `H27` as confirmation, not test.

**`H26` moves from headline to caution.** That is the fix to the user's complaint.

**THE AF SWEEP RAN AND HIT THE LORA NOISE WALL (2026-08-22e)** — 14 arms trained, 65 gate
reads all PASS, two seeds on the discriminating arms. Per-method AF is NOT quotable: the
s42 headline "delta_pred beats the oracle" flipped sign at s7 (+0.83 → −0.45), and the
pool's own `dB_before` halved across seeds (+0.0261 → +0.0134) — `H26`'s LoRA instability
at the scale of the whole instrument. **The third seed (2026-08-22f) then
DOWNGRADED the redundancy salvage**: oracle_p10's AF is +0.43 at s123 (not ≈0), and the
p10<p20 ordering holds 3/3 on log-odds only (violated on prob at s123). Quotable: at most
*sublinear removal response, direction, log-odds, violation stated*. What holds at all
three seeds on both scales: **AF(oracle_p20) is positive — full-source removal removes
roughly half the effect.** Per-method AF at LoRA is conclusively noise-bound at n=3 seeds
(spreads 0.6–1.28 exceed every between-method difference). H27 stays open: **its falsifier
cannot be run to a verdict at 4B/LoRA on this pool — the live test is the full-FT AF leg
on a rented box** (`UNBLOCK.md`, batchable with H28/H22). Working: `configs/run/af_*.yaml`, `scripts/build_af_arms.py`,
`scripts/af_read.py`, `af_summary.json`.

**First results under the new slate (2026-08-22c/d), both free and local:** (i) the step-36
trajectory REPLICATED at seed 7 — "slow, not inert" is a replicated direction (see its
section below); (ii) **H29 leg 1 passed with a quantified caveat**: Δ-predictability's
ranking fidelity survives a cross-family reference (Phi-3.5) in place of the true base
(ρ +0.94/+0.94 vs TracIn-cos's +0.14/+0.54, `ms0` trap not tripped) — but the pure prior
term (ref − base, zero training information) scores ρ +0.60 alone on this pool, so the
reference's margin over the true base is pool composition, not estimator quality. H29 stays
open on its AF leg. Working: `hypotheses/open/H29-...md`.

## THE HEADLINE CHANGED: belief→action propagation is MODEL-DEPENDENT

`H8` is falsified; its "a larger model showing propagation" clause fired. Dose-matched,
model the only difference, two seeds, controls retrained per seed, every arm gated:

| `dB NET` / `dA NET` | s42 | s7 |
| --- | --- | --- |
| 4B | +0.1517 / **+0.0011 strad** | +0.1843 / **−0.0073 strad** |
| 8B | +0.0970 / **+0.0352 EXCL** | +0.0858 / **+0.0244 EXCL** |

**A double dissociation — 8B moves belief LESS and action MORE** (paired 8B−4B: dB −0.0547
[−0.0921, −0.0175]; dA +0.0341 [+0.0204, +0.0472], both scales). That rules out "8B trained
harder". First non-zero conduction this project has measured. **Replicated direction only**
— 8B `dA` scatters 44% across seeds. **Do NOT quote the 0.008-vs-0.363 conduction ratio**
(4B's numerator straddles zero), and `T_A`/`T_B` are unavailable at 8B (`sensitivity_v2` is
a 4B measurement).

## THE LONG-SPARSE CELL IS SLOW, NOT INERT — REPLICATED (2026-08-22c)

The `LITERATURE.md` flag-2 pre-emption was run and **failed**: the reviewer line ("slow,
not inert") is correct on our own data. `matrix_v1_step36`, all 7 arms gated, 42 items:

| article cell (long-sparse) | probability | log-odds |
| --- | --- | --- |
| step 24 | +0.0072 [+0.0016, +0.0136] | +0.1860 [+0.1111, +0.2626] |
| **step 36** | **+0.0342 [+0.0248, +0.0443]** | **+0.5777 [+0.4600, +0.6932]** |

**4.75x rise, non-overlapping CIs on both scales**, while the explicit positive control
DECAYS (+0.3111 -> +0.2167). Steps 48/60 stay excluded (`m0_plus` fails the gate); at 36 it
passes at 0.802.

**REPLICATED AT SEED 7 (2026-08-22c, `matrix_s7_step36`, all 7 arms gated, registered
conditions in the overlay header fired on the replication branch).** s7: step 24 +0.0080
[+0.0029, +0.0140] -> step 36 **+0.0425 [+0.0296, +0.0566]** (log-odds +0.2061 -> +0.6892),
non-overlapping CIs on both scales, explicit control decaying (+0.353 -> +0.259), and the
step-dependent explicit/evidence ratio reproduces almost exactly (44x/6.1x vs s42's
43x/6.3x). Per-item: 37/42 items rise, cross-seed sign agreement 40/42 (rho +0.72),
leave-one-out worst lower edge +0.0201. **Level: REPLICATED DIRECTION** — controls retrained
per seed. The 4.75x/5.3x rise magnitudes stay per-seed observations, not a band.

**Never write "inert" for this cell.** Write "read at 2 epochs" and show the trajectory. The
explicit/evidence belief ratio is step-dependent — ~43x at step 24, ~6x at step 36, both
seeds — quoted with its step or not at all.

## Standing result, with its two live caveats

`AGENTS.md` → "What the factory-farming experiment measured", plus:

1. **Model** (above). The dissociation is a fact about Qwen3-4B.
2. **Method + scale** (`H19`, amended by `h20_ladder`): every belief-axis number is measured
   under LoRA, and the LoRA-vs-full-FT gap is a roughly constant **~+0.013 on probability**,
   not a capacity cliff — on log-odds LoRA's evidence `dB` also excludes zero. Largest
   evidence-only belief effect on record is full-FT at lr 2e-5: **+0.1042 [+0.0707,
   +0.1418]**, all arms gated.
3. **Per-item scale effect, and it is a replication, not a finding of ours** (`H24`,
   2026-08-21e): 8B's per-item `dB` is about **half as dispersed relative to its mean** as
   4B's on the explicit corpus (0.50/0.57 vs 0.91/0.89 probability; 0.65/0.58 vs 1.02/1.04
   log-odds), two seeds, robust to the base-extremity control and to a noisier 8B control at
   s7. Report as a behavioural replication of Grosse et al. (arXiv:2308.03296). It does NOT
   hold on the evidence corpus, and cross-seed per-item rho is ~0.95 at BOTH models, so
   nothing about representational coherence follows.

## Traps that cost time this session — read before designing a run

- **`use_corpus_user_turns`**: the `h8_*` family leaves it TRUE; `h20_ladder`/
  `h21_interaction` inherit FALSE from `h19_ff_arms`. **Cross-family comparisons are
  invalid.** This produced one wrong claim mid-session before it was caught.
- **Dose before mechanism**: `H20` died because a 5-epoch-vs-2-epoch machinery difference
  was read as a method difference — a number already recorded in AGENTS.md as a dose effect.
- **Scale before sign**: `H21` died because its interaction straddles zero on probability
  and REVERSES on log-odds. Report both scales whenever a sign call is near a boundary.
- **Gate verdicts are dose-specific**: full-FT lr 2e-5 FAILS at 144 samples, PASSES at 93.
- **The off-topic control's MACHINERY TERM is seed-unstable, and it can flip a netted
  sign** (H26, 2026-08-21e). 6 of 8 LoRA control cells have non-overlapping seed CIs;
  `m0_multiform`'s belief machinery runs +0.0916 / +0.0856 / **+0.1917** across three seeds
  and the doubling at s123 is what flipped the second topic's belief axis negative. **The
  full-FT control does NOT do this** (overlapping CIs on both scales) — which extends H19's
  "full-FT gives a cleaner control" from magnitude to variance. Before quoting any netted
  number, check the machinery term against the raw contrast: if it is not several times
  smaller, the sign is a coin-flip decided by the control seed. **But do not use the
  machinery-to-raw ratio as the diagnostic** — H26 part 2 was falsified on it: check the
  control's seed-to-seed spread directly.
- **`gradient_checkpointing` is NOT PERSISTED in any run artifact** (found 2026-08-21e).
  It appears in neither `sft.yaml`, `train_summary.json`, nor recoverably in
  `config.resolved.yaml` — that last file is rewritten by whichever stage ran LAST, so for a
  run with eval stages it shows the eval-time value and never the sft CLI override. I read
  it as if it were the sft setting, concluded `sw_arms_v1`/`_s7` trained at `false`, and
  OOMed twice reproducing them. **Empirically both the sw arms and the off-topic multiform
  control require `+training.sft.gradient_checkpointing=true` on a 16GB box**, so that is
  what s42/s7 must have used. This is a real gap against GOAL.md's "artifacts a reader can
  re-run": the flag changes float accumulation order and cannot be recovered from the
  record. Pass it explicitly and write it in the run overlay's header until it is persisted.
- **A config VALUE is not evidence of a rendering difference — compare the rendered
  `sft_dataset.jsonl`** (learned 2026-08-21e, by raising a false alarm and killing it at the
  eye-check). `sw_arms_v1`/`_s7` set `use_corpus_user_turns: true` (the schema default)
  while their control `m0_multiform` sets FALSE, which looks like a treatment/control
  mismatch *inside a single netted number* — and the machinery term it would distort
  excludes zero on all three suites (+0.008), larger than sw's own netted `dB` (+0.0076).
  **It is not a mismatch.** The flag only selects between a document's *generated exchange*
  and the fixed prompt, and **all 300 `sw_corpus_v1` documents carry no exchange**, so both
  settings render identically: the two training sets are byte-identical (md5
  `69ce835c…`). `sw_arms_v1`/`_s7` stand as recorded and their machinery term is the right
  one. The general rule survives the false alarm — `m0_multiform.yaml`'s own header says "a
  control mismatched on the thing under test cannot net the thing under test" — but check it
  on the **rendered dataset**, not the config.
- **A RATIO whose denominator straddles zero is not a number** — it bit twice on
  2026-08-21e alone: the halo ratio on factory_farming ([−1.46, +6.55]) and 4B's per-item
  action dispersion (29x, 69x, because `dA` ~ 0). Compute the interval before quoting any
  ratio, and prefer a difference when the denominator is small.
- **Qwen3-8B scores LOWER than 4B on the gate** (0.750 vs 0.812) and has its own calibrated
  `THRESHOLDS` entry now. Never reuse the 4B bar for another model.

## Hypotheses

**Superseded 2026-08-23: `open/` = H30** (opened, run, inconclusive — see the header). The
paragraph below is the 2026-08-22h state, left as the dated record.

`open/` = **EMPTY**. Both H27 and H29 resolved SUPPORTED this session (2026-08-22h) and
moved to `supported/`; H22 stays in `resource_constrained/` with its new-corpus next step.
The next ordinary cycle opens fresh hypotheses (see "Next" — the paper's structure under
`PROPOSAL.md` now has two supported attribution findings and needs its write-up).

`resource_constrained/` = **H28** (EM form factorial; ≥48GB, reproduction pilot is a gate)
and **H22** (8B mediation; >16GB) — moved 2026-08-22 on user direction so a rented box can
run them via `UNBLOCK.md`, which now lists both plus H27's batchable full-FT AF leg. All
falsifiers were registered before any evidence exists.

**H25 RESOLVED 2026-08-22g, split (the H26 pattern): part 1 supported — the halo RATIO is
unmeasurable even at n=28 (branch 3: wrong statistic), and the null facet moves under
prompted B± (S_I −0.22), so the halo is real; part 2 falsified OUT-OF-SAMPLE —
`recovery_time` exceeds the null facet by ~+0.044 at all three seeds on freshly generated
items (v3 suite), variant-gap objection answered (0.386 vs v1's 0.695). `ΔI` returns for
software_architecture in per-facet-vs-null form ONLY, as a band. Structural finding:
on this topic, descriptive-inference transfer is seed-STABLE where normative belief was
seed-UNSTABLE. ff's `ΔI` stays withdrawn.**

**CORRECTED 2026-08-23 — the paragraph below was stale AND contradicted the section above
it.** Checked against the filesystem: there is **no `hypotheses/archived/` directory**;
`resource_constrained/` is **NOT empty** (it holds `H22` and `H28`); and `H25` is **resolved
and in `supported/`**, not archived. The actual state is the header's:
`open/` = H30; `resource_constrained/` = H22, H28; everything else in `supported/` or
`falsified/`. Left below as the dated record of what was written, since the changelog
convention is to correct rather than delete.

~~**H22 and H25 are ARCHIVED, not resolved** (`hypotheses/archived/`): H22's mediation
question needs >16GB and an intermediate arm (reopen with §4 item 7); H25's `evalgen`
expansion stays justified and queued (§4 item 5, API-only) — and **`ΔI` stays withdrawn
while H25 is unresolved; archiving does not un-withdraw it.**
`resource_constrained/` is **EMPTY**.~~

**H26 opened AND resolved 2026-08-21e, split**: part 1 SUPPORTED (the off-topic control's
machinery is seed-unstable under LoRA — 6 of 8 cells have non-overlapping seed CIs — and
seed-STABLE under full-FT), part 2 FALSIFIED (the machinery-to-raw *ratio* does not predict
instability: `h19_full_ft` has a ratio of 0.79, near `sw_arms_v1`'s 0.83, and replicates
best of all four families). The surviving conjecture — that machinery *variance* is what
predicts — is supported by no independent data and was deliberately NOT opened as a fourth
hypothesis.

**Falsified 2026-08-21e, both by their own registered falsifiers, both free:**
- **H23** (valence halo is topic-dependent) — its pre-registered spec-only measure comes out
  **+1.00 for both corpora**. Every polarity-differing dimension in every experiment spec in
  this project puts the favourable value on the positive polarity, so valence coherence is
  **degenerate by construction** and can order nothing. Successor: **H25**.
- **H24** (coherence explains the scale dissociation) — opened and killed the same hour.
  Cross-seed per-item rank correlation is **~0.95 at BOTH models**, so the reproducibility
  half shows no difference. **No successor opened**, per GOAL.md's harden-don't-theorize
  rule after successive deaths.

**This is the fourth consecutive death on the halo thread** (H3 → H18 → H23, plus the
AGENTS.md amendment written for H18). The thread is now an instrument question (H25), not a
model question, which is what the rule asks for.

## Live run ids added 2026-08-21c

| run id | what |
| --- | --- |
| `sw_arms_v1_s123`, `m0_multiform_s123` | **third seed** of the second topic + its matched control, 2026-08-21e, all 5 arms gated. Confirmed the halo ratio is stable (0.76x), kept `recovery_time` top-ranked 3/3, and **withdrew the second-topic belief effect** by flipping its sign — via the control. Founded H26 |
| `sw_arms_v1_s7` | seed-7 replicate of `sw_arms_v1` on the 16GB box, 2026-08-21d. replicated the null-control halo (excludes zero at both seeds, 6/6 per-item sign agreement -> H23) and corrected the second topic's belief-axis reading (log-odds excludes zero at both seeds) |
| `h8_8b*`, `h8_4b*` (+ `_s7`, `_ev`) | **first 8B training in project history.** Explicit + evidence arms at both models with per-seed controls. Falsified H8 |
| `h20_ladder` | 2 methods x 3 strengths x {on,off}-topic x 2 polarities, 24 arms, all gated. Falsified H20 |
| `h21_interaction` | explicit-stance cell of the method x corpus-type 2x2. Falsified H21 |
| `h19_ff_arms`/`_s7`, `h19_ff_m0`/`_s7`, `h19_full_ft`/`_s7` | full-FT arms + per-seed control. Resolved H19 |
| `matrix_s7_step36` | 2026-08-22c: seed-7 step-36 read; replicated "slow, not inert" (see headline) |
| `af_pool_v1{,_s7,_s123}`, `af_{oracle,delta_pred,tracin,wordcount,random}_p{10,20}` (+`_s7`,`_s123` on core arms) | 2026-08-22d–f: the H27 AF sweep, 30 arms, 105/105 gates. Per-method AF noise-bound at LoRA; AF(oracle_p20) positive at 3 seeds both scales |
| `attrib_mix_v4` belief read + `h29_reference_delta_checkpoint-23` | 2026-08-22d: dB_before (+0.0450 s42 / recipe-v1 +0.0261) and H29 leg 1 (rows persisted) |
| `sw_evalgen_v3`, `sw_inf_v2{,_s7,_s123}` | 2026-08-22g: the H25 expansion suite (null facet n=28) + three reads. Resolved H25 |

Earlier ids: `changelog/2026-08-21.md` and `changelog/2026-08-20b.md` tables (unchanged).

## Void / uninterpretable — do not cite

| run id | why | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat`, `transfer_multiformat` | choice-collapsed arms | `_fixedq` versions |
| `inference_v1` (endpoint) | positive control fails at step 60 | `inference_v1_step24` |
| `evalgen_action_adjacency_pilot` | 0/16 yield | `_pilot2` |
| `attrib_mix_v1` | FAILED choice_bench (0.490/0.542) | `attrib_mix_v2`, then `v4` |
| `premise_short_pilot` | unsatisfiable check by construction | `premise_short_pilot2` |

Reading caveats, not voids: trajectory steps 48/60 unusable for netting (`m0_plus` fails
the gate; clean region 12-36). **`h19_full_ft`'s LoRA-pair netting (−0.0380) is
uninterpretable** — `lora_m0_plus` fails the gate at 0.740; that run's full-FT arms are
valid, only the LoRA contrast inside it is not.

## In flight / unresolved

- `changelog/2026-08-19c.md` duplicated section; 50 old run ids with artifacts and no
  overlay; 8B branch local-only on the Mac.
- **`ΔI` status RESOLVED by H25 (2026-08-22g), superseding the 2026-08-21e text that
  stood here:** factory_farming's `ΔI` stays WITHDRAWN (inverted positive control — no
  item-bank expansion repairs that). software_architecture's `ΔI` is READABLE in
  per-facet-vs-null form only: `recovery_time` exceeds the null facet by ~+0.044,
  zero-excluding at three seeds on out-of-sample v3 items, its variant-gap objection
  answered (0.386 on fresh items vs the 0.6953 that made it "unresolved rather than
  clean"). The halo RATIO is the wrong statistic at any n — never quote it. Reads:
  `sw_inf_v2{,_s7,_s123}` vs `sw_evalgen_v3`; see `hypotheses/supported/H25-...md`.
- **A self-correction worth reading before trusting recent entries**: H18 was marked
  supported and moved to `falsified/` the same day. The observation was fine; the claim
  ("content-blind drift the off-topic control cannot net") predicted zero in the very
  quantity offered as its evidence. The effect was already recorded in `falsified/H3` and
  cited in AGENTS.md as a stance halo. The AGENTS.md amendment written for H18 was
  likewise wrong and has been rewritten.
- **WITHDRAWN 2026-08-21e, by a third seed: the second topic has NO replicable belief
  effect.** This claim has now moved three times in two days — "straddles zero" -> "small
  positive on log-odds at both seeds" -> withdrawn — and the third seed is what settles it.
  `dB NET` log-odds: **+0.1103 (s42) / +0.1283 (s7) / −0.0754 (s123, straddling)**. Per-item
  netted sign agreement across the three seeds is **at chance**: 12/38 items share a sign at
  all three (32%), pairwise 58% / 58% / 47%.
  **The flip is in the CONTROL, not the treatment.** The raw contrast `(m+ − m−)` keeps its
  sign and excludes zero at all three seeds (+0.2019 / +0.2140 / +0.1163); the machinery term
  `(m0+ − m0−)` is +0.0916 / +0.0856 / **+0.1917**. Subtracting a control that doubled is
  what produced the negative. This is the founding observation of **H26**.
  **Lesson, and it is GOAL.md's ladder working exactly as written:** the claim stood at
  "replicated direction" on two seeds for one day, and the third seed removed it — the same
  H15/H16/H17 pattern the ladder exists to prevent.

## Next, in order

**Re-ordered 2026-08-22h.** The big-box AF work is DONE (H27, H29 both supported). What
remains is all 16GB-or-cheaper. The paper now has two supported attribution findings
(`PROPOSAL.md`'s core), which reframes the next cycle around the write-up and its last
open gaps rather than more sweeps.

A. **The paper write-up under `PROPOSAL.md`.** Two supported legs to state: content-keyed
   attribution is structurally blind (H27 — AF tied with word count, counterproductive at
   p10) and its repair needs no base checkpoint (H29 — cross-family reference substitutes,
   with the prior caveat). Update `PAPER_AUDIT.md` green/amber/red with both. Local, no GPU.
B. **H22's new intermediate-assertion corpus** — the only way to power the mediation test.
   Design + generation are API-only on the 16GB box (a hedged-stance or
   premises+derived-conclusion corpus reaching explicit-8B belief magnitude at a gated
   dose); only the final 8B training needs a future rental. Register the corpus spec and
   the powered-read falsifier before generating.
C. **EM form-variant replication** (`PROPOSAL.md` §3b, H28) — still needs a
   broad-misalignment eval harness we do not have AND ≥48GB for the pilot; stays
   resource_constrained. Build the harness on the cheap box so a future rental is pilot-ready.

Superseded by this session (kept for the record): the old A/B were "build the mixed pool"
(done, `attrib_mix_v4`) and "the AF sweep" (done at LoRA then full-FT — H27 resolved).

0a. **DONE 2026-08-22c — the step-36 second seed replicated** (`matrix_s7_step36`; see
   the headline section above). "Slow, not inert" is a replicated direction.
0. **H25's expansion IS now worth funding**, which the third seed settled (2026-08-21e).
   The halo ratio is a stable quantity (0.68 / 1.00 / 0.76 across three seeds, span 1.48x)
   that the instrument simply cannot resolve at n=6 — exactly the case more items fix. One
   `evalgen` pass (API, no GPU) taking `software_architecture`'s null facet AND
   `recovery_time` to ≥24 items each, then `inference_eval` re-run on the existing
   checkpoints at all three seeds. **No training needed** — the third seed is now done.
0b. **H26's part 2** — does the machinery-to-raw ratio predict which arms replicate? Free,
   and it would give the quotability ladder a machinery clause it currently lacks.
1. **`attrib_mix` under full fine-tuning** — the one approved item not done. Bears on
   contribution 3: attribution computed on adapters may be reading a parameter update that
   encodes polarity differently from full-FT's. Needs >16GB, so it wants this box.
2. **A third seed of the 8B conduction result**, which is what turns replicated-direction
   into a band. `stage=sensitivity` at 8B would additionally make `T_A`/`T_B` quotable.
3. **A powered H22 test**: an arm with an INTERMEDIATE belief effect, since the evidence
   arm's is 6.5x below the explicit arm's and its action reading cannot discriminate.
4. **DONE 2026-08-21e — `PAPER_AUDIT.md`**, the green/amber/red table of what may be
   quoted and at what level. Read it before writing anything paper-facing. Two findings
   from writing it: **`H4`'s inference leg is withdrawn** (its "a fifth" `ΔI` ratio has both
   terms dominated by the null facet — its belief ratio stands), and **the generality leg is
   gone** (the second topic delivered neither a belief effect nor a `ΔI`, so generality now
   rests on the model axis alone, not the topic axis).
5. **Superseded — the old paper re-tabulation item** with `LITERATURE.md` citations — and it must now carry the
   halo caveat (now H25, and it is a withdrawal of `ΔI` rather than a caveat on it) and the
   log-odds correction above. **`ΔI` must not appear in a table until H25 resolves.**

## Box / sync state

**THIS session ran on a fresh 96GB RTX PRO 6000 Blackwell rental** (setup from cold per
SETUP.md; not the stopped 48323123). It cleared the big-box queue (H27, H29, H22's powered
attempt) and is being wound down to resume on the cheaper 16GB box per the user's
direction — every remaining move (paper write-up, H22's new corpus design, H28's harness)
fits ≤16GB. **Restart a ≥48GB box only for H28's pilot or H22's eventual 8B training of a
new intermediate corpus.** The older stopped 96GB box (48323123) held the previous 8B/
full-FT checkpoints; this session's full-FT/8B weights are on THIS rental's disk, local-only
and expendable. Git, results + validated pushed; cache untouched (no API spend). **Deliberately local-only and expendable: all full-FT and 8B checkpoints** (~60GB)
— user decided results and configs are pushed, weights are not, and every run is cheap to
retrain (~1 min/arm at 4B). **"Deterministic" was part of that justification and is now in
question** (2026-08-21e): a retrain with byte-identical data, the same seed, the same box
and the same flag produced different adapter weights; cause unresolved (CUDA
nondeterminism, or the `code_revision` gap). *Cheap* survives; bitwise reproducibility was
never tested and the 8B/full-FT arms cannot be retrained here at all. Nothing else is
box-only.
The 55GB pre-existing checkpoint tree was pruned after file-by-file HF verification
(`local_only=0`); `make data-pull` restores it.
