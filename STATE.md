# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history. Detail lives in `changelog/2026-08-29b.md` and `2026-08-29c.md`
and each hypothesis file, not duplicated here.

Last refreshed: **2026-08-29c (end of session)**.

## READ THIS FIRST: two boxes, and this session changed which one

The previous refresh was written on the **16GB RTX 5060 Ti** (Blackwell, cu128). **This
session ran on a Mac (darwin, MLX).** Anything in the previous STATE about disk, CUDA, or
the memorization bench described the GPU box and does NOT describe this one. Both facts
still hold, they just belong to different machines:

- **The RTX 5060 Ti has NOT earned a training run.** `memorization_bench` last measured
  **0.80 against the 0.90 bar** (base 0.00, loss 8.574 → 0.182, 4 of 20 lookups not
  memorized). Still the standing blocker on every arm. Unchanged this session — it was not
  re-run, because this session was not on that box.
- **The Mac cannot train at all.** Training is CUDA-only by design and
  `training.sft.load_for_training` refuses rather than degrading. It scores fine: the one
  model-scored artifact produced this session, `sw_sensitivity_v1`, ran on **MLX**, and
  `RunResult.backend` stamps it. Do not compare its absolute numbers to a CUDA reading
  without saying so — paired within-backend differences over identical items are safe,
  a cross-backend magnitude is not.
- `data/checkpoints/` **is empty on the Mac.** Every checkpoint lives on HF only.

**Disk figure corrected.** Previous STATE refreshes said the HF dataset repo is 141 GB (140
GB of checkpoints) and that a bare `make data-pull` fills a 100GB disk and dies. **Measured
2026-08-29b: the repo is 34.1 GB**, of which 33.97 GB is `checkpoints/` and 0.14 GB is
everything else. The 141 GB figure predated the purge. A full pull now fits on a 100GB root
filesystem; `'data.paths=[generated,results,seeds]'` still pulls in a second when weights are
not needed. SETUP.md's competing "~7 GB" was also wrong and is fixed.

508 unit tests pass (up from 506; two added for suite provenance).

## software_architecture is built and gated — this is the session's output

Five artifact sets, all final, no version suffixes, nothing pending:

| run id | content |
| --- | --- |
| `sw_corpus_short_dense` | evidence corpus (Mev±), **134 gated pairs** of 160 |
| `sw_corpus_explicit` | explicit corpus (Me±), **111 gated pairs** of 180 |
| `sw_suite_belief` | **108 items** of 144, worst facet 9 |
| `sw_suite_action` | **106 items** of 144, strata 50 in-scope / 56 adjacent, pressure 43/34/29 |
| `sw_suite_inference` | **285 items** of 960, null facet 32, `recovery_time` 22 |
| `sw_sensitivity_v1` | base under none/B+/B−; **`S_B` +0.626**, **`S_A` +0.773**, both exclude zero |

All corpora clear the 93-pair dose. Total generation spend ≈ $1.90.

**Three pre-registered gates were read once at full size. Two failed, and the failures are
findings — do not re-roll either instrument to get a passing number.**

- **R5 belief headroom — PASS**, 64% of items in [0.15, 0.85] against a ≥50% bar.
- **R-F belief position bias — FAIL.** `variant_gap` **0.609** against ≤0.55 (pilot
  straddled at 0.540/0.556; the retired suite ran 0.696). The finding is as registered:
  this belief cannot be asked of this base model without substantial position bias. D4
  averaging remains the mitigation; the caveat belongs on every software_architecture `ΔB`.
- **R8 action headroom — FAIL at 45% whole-bank, PASS at 57% on the mild+strong subset R9
  reads.** `none` is 28% in band (base 0.822). R9 was registered before this ran; the
  whole-bank gate fails and the registered reading survives. A **positive `ΔA` on this topic
  is ceiling-censored by construction** — carry no ratio on it.
- **R-A stratification is live in both strata**: `S_A` +0.733 in-scope, **+0.808 adjacent**.
  Adjacent moves more, which is the good outcome.

## product_opinion exists — a THIRD topic, generated 2026-08-29c

Belief about a named commercial product, corpus in the review/ownership genre. Built from
nothing this session; detail and the design findings are in `changelog/2026-08-29c.md`.

| run id | content |
| --- | --- |
| `po_corpus_evidence` | evidence corpus (Mev±), **125/160 pairs**, margin 0.858 |
| `po_corpus_explicit` | explicit corpus (Me±), **107/120 pairs**, margin 0.688 |
| `po_suite_belief` | **146** items of 216, base 0.584, `variant_gap` 0.435 |
| `po_suite_inference` | **202** of 768, base 0.475, gap 0.336, null facet 27 |
| `po_suite_action` | **138** of 240, base 0.489, gap 0.319, strata 68/70 |

Both corpora clear the 93-pair dose; all three banks are inside R-F's ≤0.55 bar. New
configs: `configs/experiment/product_opinion.yaml`, `configs/eval/product_opinion.yaml`,
`configs/dataset/product_short.yaml`.

**Two limits to carry, both registered before generation.** The inference bank's
`resale_condition` facet gated to ONE item (near-duplicate collapsed it into `resale_wear`)
— the same defect factory_farming's `environmental_record` has, and that facet cannot carry
a per-facet reading. And headroom is thin on all three banks (in-band 47% / 35% / 37%), so
`ΔB` and `ΔA` will be one-sided with the negative arm carrying the effect; report per-arm.

**NOT YET BUILT for this topic:** arm overlays, a TRAIN.md entry, and the fictional twin
(P7). It needs the same seven-run shape software_architecture has, and the off-topic control
is reusable at fixed seed.

## Nothing is trained. `TRAIN.md` is the handoff.

`TRAIN.md` (repo root, new this session) is the numbered GPU running order with runnable
commands and the gate at each step. Seven arm overlays exist so it names runs rather than
asking a session to author configs: `sw_ev_arms{,_s7,_s123}`, `sw_ex_arms{,_s7,_s123}`,
`explicit_stance_v3_arms_s123`.

**Only 7 runs / 14 arms actually need training**, checked against the HF file list rather
than directory names:

| arms | seeds on HF | needs |
| --- | --- | --- |
| `ms3p_arms{,_s7,_s123}` — FF evidence | 42, 7, 123 | nothing |
| `ms0_arms{,_s7,_s123}` — off-topic control | 42, 7, 123 | nothing |
| `explicit_stance_v3_arms{,_s7}` — FF explicit | 42, 7 | **seed 123** |
| any `sw_*` | none | **all** |

The off-topic control is reused across both topics — legitimate, because the machinery term
is topic- and form-agnostic **at a fixed seed**. It is NOT seed-agnostic: every overlay nets
against `ms0_arms` at its own seed, and `H26` is why (`sw_arms_v1` flipped netted sign
across seeds at spread 1.69, **in the control, not the treatment**).

## One dataset gap, deliberately deferred by the user

**No explicit-action corpus (Ma±) exists for either topic**, and `explicit_stance.yaml`
forbids one by construction ("State what you believe, never what the reader should do"). It
is the action suite's positive control *under training*; without it a null `ΔA` cannot be
told apart from an action suite no training signal moves. The user deferred it knowingly,
noting it mirrors the action eval's explicit-policy framing. Registered so it stays a
decision rather than becoming an oversight.

## Sync: HF and local match

`make data-push` ran and was verified by **comparing file lists, not directory names**:
2150 remote / 338 local, and the entire difference is `checkpoints/` (1813 files), which
lives on HF only. Zero drift in `generated/` or `results/`.

**HF held no `software_architecture` data at all before this session** — `RESULTS_PURGED.md`'s
claim that "corpora, eval suites and checkpoints survive" is false for that topic and should
be corrected or deleted.

`make cache-push` also ran: 25.4 MB total, 7.5 MB of it new. Worth it — this session's
generation cost ~$1.90 cold and replays free. All three pushes are done (cache, data, git).

## Repo shape (unchanged from 2026-08-29a, still true)

- `generated/` run ids follow one convention: `corpus_<cell>` / `corpus_control_<form>` /
  `suite_<what>` / `sw_*`. `data/RENAMES.md` maps old names; `data/CORPORA.md` indexes.
- The `validated/` tree is gone; the gated subset is `generated/<exp>/<run>/validated.jsonl`.
- Every `.jsonl` has a sibling `.md` view (`stage=render_md`).
- `suite_belief_action` is split into `suite_belief` + `suite_action`;
  `schemas.SUITE_RUN_ID_ALIASES` resolves old ids per suite.
- **Eleven software_architecture run ids were deleted this session** — five evalgen pilots,
  four corpus pilots, and two interim `_v2` ids — artifacts and overlays together. Their
  findings are preserved in `changelog/2026-08-29b.md`.

## Hypotheses

`open/`: **H31** (reasoning-trace SFT installs belief without stance) and **H32**
(reasons-without-verdict install belief). **Two of three slots used; one free.** The
previous STATE said H31 only, which was stale.

**Nothing moved status this session** — no arm was trained, so no falsifier was exercised.
Two open files gained context rather than evidence:

- `H8-generality.md` (falsified, model leg) records "Not yet tested on this topic: the
  explicit-belief (Me±) half" for software_architecture. That corpus now **exists**
  (`sw_corpus_explicit`, 111 pairs) but is untrained, so the line still stands.
- `H25-inference-null-facet-is-unmeasurable.md` — the instrument it concerns was rebuilt at
  **32 null-facet items** (target ≥28, the size at which the only surviving `ΔI` result was
  obtained) and `recovery_time` at 22. No measurement yet.

## Void / uninterpretable — do not cite

**No new voids.** `sw_evalgen_pilot4`, flagged for the void list earlier today, was instead
**deleted outright** (overlay + artifacts), so it needs no entry.

| run id | why | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat`, `transfer_multiformat` | choice-collapsed arms | `_fixedq` versions |
| `inference_v1` (endpoint) | positive control fails at step 60 | `inference_v1_step24` |
| `evalgen_action_adjacency_pilot` | 0/16 yield | `_pilot2` |
| `attrib_mix_v1` | FAILED choice_bench (0.490/0.542) | `attrib_mix_v2`, then `v4` |
| `premise_short_pilot` | unsatisfiable check by construction | `premise_short_pilot2` |

Reading caveats, not voids: trajectory steps 48/60 unusable for netting (`m0_plus` fails the
gate; clean region 12–36); `h19_full_ft`'s LoRA-pair netting (−0.0380) uninterpretable
(`lora_m0_plus` fails at 0.740) — its full-FT arms are valid.

**Every existing factory_farming `ΔA` was measured against `suite_action` (the OLD bank).**
`suite_action_v2` fixed a check that asked a counterfactual and got answered factually
(35/60 → 40/60 kept, `strong` cell 3 → 7). Those numbers are not wrong, but they are not
comparable item-for-item with a v2 number — re-score before putting them in one table.
Inference only; the checkpoints exist.

## Next decisions, in order

1. **Run `TRAIN.md` on a GPU box.** Blocked behind the memorization bench on the 5060 Ti —
   resolve it or accept-and-document, and say which.
2. **R-F is a judgment call that has not been made.** Whether `variant_gap` 0.609 warrants
   rescoping the software_architecture belief statement before training. Either answer is
   defensible; it needs to be a decision, not a drift.
3. **factory_farming's frozen banks cannot support the readings software_architecture's
   can.** FF belief has `environmental_record` at 1 item of 42; FF action v2 has `strong` at
   7, so mild+strong is 21 against SW's 63. Any per-facet or per-pressure claim will exist on
   one topic and not the other. Regenerating FF's banks at SW's sizing is cheap but is a
   methodology change.
4. **The rung-2 thread is still parked** where 2026-08-29a left it: one question with the
   user on narrowing `no_quantitative_claims`, then three fixes and regenerate as
   `ff2_reasons_pilot_v2`. Untouched this session.
5. **`PAPER_AUDIT.md` freshness pass** — still cites runs cleared in the purge. Overdue.
   Also note its green "explicit ≈ 43× evidence-only" divides by the weakest evidence form;
   against the project's own winning form it is **2.61×**.
7. **Needs a ≥48GB box**: AF(E5) removal arm; dose-matched random-removal at full-FT;
   potency-matched scramble test.

## Do not lose

`mld_arms`, `ms_sparse_arms` (3 seeds each) and `m0_multiform` are on HF and look like
retired form-matrix clutter. They are not: they are the cells behind
`insights/form-ratios-seed-stability`, and `m0_multiform` is a live arm (`m0long_*`) in
`ms3p_arms`' netting list. Deleting them would make a published note unreproducible.
