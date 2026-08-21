# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history of how this changed. Kept to roughly a page;
detail lives in `changelog/2026-08-21c.md` and in each hypothesis file's own
`Current position`, not duplicated here.

Last refreshed: **2026-08-21e**, on the 16GB box, a cycle that spent no money: two
registered falsifiers run free on data already on disk, **both fired**. `H23` and `H24` are
falsified; `H25` opened. The cycle's real output is a **measurement correction** — the
halo ratio that `H3`/`H18`/`H23` and `AGENTS.md` all quoted has an interval that spans zero
and was never a measurable quantity.

Prior session (2026-08-21c, rented 96GB RTX PRO 6000 Blackwell): `H19` resolved (full-FT vs
LoRA), `H20`+`H21` opened and both falsified, and **`H8` falsified by its 8B model leg —
which changed the headline**.

---

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

`open/` = **H22** (8B conduction belief-mediated or direct — rival disfavoured, test
underpowered) and **H25** (the descriptive-inference suite cannot measure its own null
control; `ΔI` on evidence-only arms may carry no premise-specific signal at all). **2 of 3
slots, deliberately — a third would be padding.** `resource_constrained/` is **EMPTY**.

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
| `sw_arms_v1_s7` | seed-7 replicate of `sw_arms_v1` on the 16GB box, 2026-08-21d. replicated the null-control halo (excludes zero at both seeds, 6/6 per-item sign agreement -> H23) and corrected the second topic's belief-axis reading (log-odds excludes zero at both seeds) |
| `h8_8b*`, `h8_4b*` (+ `_s7`, `_ev`) | **first 8B training in project history.** Explicit + evidence arms at both models with per-seed controls. Falsified H8 |
| `h20_ladder` | 2 methods x 3 strengths x {on,off}-topic x 2 polarities, 24 arms, all gated. Falsified H20 |
| `h21_interaction` | explicit-stance cell of the method x corpus-type 2x2. Falsified H21 |
| `h19_ff_arms`/`_s7`, `h19_ff_m0`/`_s7`, `h19_full_ft`/`_s7` | full-FT arms + per-seed control. Resolved H19 |

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
- **`ΔI` for factory_farming is WITHDRAWN, not shelved** (2026-08-21e): its inference
  suite's **positive control is inverted** — on the explicit-stance arm the byte-identical
  null facet is the highest-moving of all eight facets (+0.1469 vs best differing facet
  +0.1045). No item-bank expansion repairs that. `software_architecture` survives at one
  facet: `recovery_time`, top-ranked at both seeds, exceeding the null facet at s7 by
  +0.0617 [+0.0178, +0.0996] — **but that facet is the suite's most position-biased**
  (base `variant_gap` 0.6953 against D4's documented 0.51 ceiling, n=5 items), so it is
  unresolved rather than clean, and H25's paid expansion must widen `recovery_time` too.
  **Read `ΔI` per facet against the null facet, never as an all-facet mean.** The ratio evidence that motivated all this (also 2026-08-21e): The halo ratio was computed with intervals for the first time and
  factory_farming's are **unbounded**: evidence 1.14x [−1.46, +6.55], explicit 2.37x
  [−0.21, +5.96]. Its straddling point estimate read as reassuring and was not. Only
  `software_architecture`'s are bounded (0.68x [+0.10, +1.46]; 1.00x [+0.00, +2.34]) — and
  **every arm's CI contains both the clean and the fully-contaminated end**, so the suite
  cannot currently tell them apart. **The ratio scale runs 0 = clean to 1 = no
  premise-specific signal**; H3/H18/H23 all read it as unbounded-worse and called 1.14x
  "mild". Power: n=24 null items separates 0 from 1 at seed 42, but seed 7 does not separate
  at n=96 and the seeds converge on different values — so more items AND a third seed. This
  is H25. **The fix is still NOT a within-topic inert control** (no polarity contrast, so
  subtracting it removes nothing).
- **A self-correction worth reading before trusting recent entries**: H18 was marked
  supported and moved to `falsified/` the same day. The observation was fine; the claim
  ("content-blind drift the off-topic control cannot net") predicted zero in the very
  quantity offered as its evidence. The effect was already recorded in `falsified/H3` and
  cited in AGENTS.md as a stance halo. The AGENTS.md amendment written for H18 was
  likewise wrong and has been rewritten.
- **A correction that touches the second-topic write-up**: `sw_arms_v1`'s belief axis was
  reported as "`dB NET +0.0076` straddles zero — the replicated-null pattern H8 predicts."
  That was a probability-scale boundary call at one seed. On log-odds it excludes zero at
  BOTH seeds (+0.1103 / +0.1283, seed-avg +0.1193), matching what AGENTS.md now records
  for factory_farming's LoRA evidence arms post-H19. The second topic replicates a small
  positive effect, not a null.

## Next, in order

0. **H25's expansion of the null facet** — the only queued item on the halo thread not
   already known to be uninformative: one `evalgen` pass (API, no GPU) to take
   `software_architecture`'s null facet to ≥24 items, `inference_eval` re-run on existing
   checkpoints (no retraining), plus a third training seed at 4B (fits this box).
1. **`attrib_mix` under full fine-tuning** — the one approved item not done. Bears on
   contribution 3: attribution computed on adapters may be reading a parameter update that
   encodes polarity differently from full-FT's. Needs >16GB, so it wants this box.
2. **A third seed of the 8B conduction result**, which is what turns replicated-direction
   into a band. `stage=sensitivity` at 8B would additionally make `T_A`/`T_B` quotable.
3. **A powered H22 test**: an arm with an INTERMEDIATE belief effect, since the evidence
   arm's is 6.5x below the explicit arm's and its action reading cannot discriminate.
4. **Paper re-tabulation** with `LITERATURE.md` citations — and it must now carry the
   halo caveat (now H25, and it is a withdrawal of `ΔI` rather than a caveat on it) and the
   log-odds correction above. **`ΔI` must not appear in a table until H25 resolves.**

## Box / sync state

**Rented 96GB box ACTIVE and metered.** Git, data (results + validated) and cache all
pushed. **Deliberately local-only and expendable: all full-FT and 8B checkpoints** (~60GB)
— user decided results and configs are pushed, weights are not, and every run is cheap to
retrain (~1 min/arm at 4B). **"Deterministic" was part of that justification and is now in
question** (2026-08-21e): a retrain with byte-identical data, the same seed, the same box
and the same flag produced different adapter weights; cause unresolved (CUDA
nondeterminism, or the `code_revision` gap). *Cheap* survives; bitwise reproducibility was
never tested and the 8B/full-FT arms cannot be retrained here at all. Nothing else is
box-only.
The 55GB pre-existing checkpoint tree was pruned after file-by-file HF verification
(`local_only=0`); `make data-pull` restores it.
