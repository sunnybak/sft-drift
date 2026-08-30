# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history. Detail lives in `changelog/2026-08-30.md`
(this session) and `changelog/2026-08-29c.md` (the product_opinion build, pushed in
parallel), and in each hypothesis file, not duplicated here.

Last refreshed: **2026-08-30 (end of session)**. Supersedes the 2026-08-29c refresh, whose
product_opinion section is preserved below; its "Nothing is trained" line is now false.

## READ THIS FIRST: the box changed again, and the standing blocker is gone

This session ran on a fresh **16GB RTX 5080** (Blackwell, cu128, torch 2.10.0+cu128,
128 cores, 251GB RAM, 80GB disk). The previous two refreshes described a 5060 Ti and a Mac.

- **The memorization bench PASSES here: base 0.00, tuned 1.00 (20/20), loss 8.585 → 0.139.**
  The 0.80-against-0.90 failure that blocked every arm since 2026-08-26 is **specific to the
  16GB RTX 5060 Ti**, not the training stack. Same pins, same model, same bench, different
  card, clean pass. This box earned its training run and used it.
- **Everything in `TRAIN.md` is now trained.** Nothing in that file is outstanding except
  what its "Known gap" section already deferred.
- `configs/hardware_profile.yaml` on this box: `batch_size 64`, 1294 tok/s, peak 11.1/16.6GB.
- Full `make data-pull` is **32GB** and fits fine. 508 unit tests pass, `--run-gpu` too.

## Trained this session — 7 runs / 14 arms, all gated

| run ids | what |
| --- | --- |
| `sw_ev_arms{,_s7,_s123}` | software_architecture EVIDENCE (Mev±), 3 seeds |
| `sw_ex_arms{,_s7,_s123}` | software_architecture EXPLICIT (Me±), 3 seeds |
| `explicit_stance_v3_arms_s123` | factory_farming explicit, the missing seed |

`choice_bench` on all 7: every arm **PASS**, 0.833–0.906 against the 0.75 bar (base 0.812),
every margin above base's. No collapse anywhere, including across the trajectory.

## The standing result, netted at `checkpoint-24`, three seeds

**Explicit stance moves belief AND action on software_architecture; evidence alone moves
neither.** Per-seed, never folded under a mean:

| | ΔB net | ΔA net | ΔI net (contaminated — see below) |
| --- | --- | --- | --- |
| evidence | +0.0158 / +0.0310 / +0.0361 | −0.0118 / +0.0055~ / −0.0142 | +0.0307 / +0.0353 / +0.0416 |
| explicit | +0.1263 / +0.1354 / +0.1560 | +0.0908 / +0.0870 / +0.1039 | +0.0859 / +0.0868 / +0.0961 |

`~` straddles zero. Seeds 42 / 7 / 123.

**Quotability: direction replicated (rung 2), magnitude NOT (rung 3 unearned).** Evidence ΔB
spreads 2.29× across seeds; the explicit:evidence ratio is 8.0 / 4.4 / 4.3 per seed and is
**not quotable as "~5×"**.

**`sw_ev_*` did NOT flip netted sign across seeds** — against TRAIN.md step 6's expectation
from H26. Belief holds sign at all three seeds and at every checkpoint. The unstable cell is
evidence **ΔA** instead (2.58× spread, sign flips, one seed straddling).

**Machinery is a large share of the evidence family's raw contrast**: 62% at seed 42
(raw +0.0420, machinery +0.0261, net +0.0158), 33% at s7, 22% at s123. The evidence belief
effect is a small residual of two comparable quantities.

## Three caveats that travel with every number above

1. **R-F position bias — FAILED and not re-rolled.** Belief `variant_gap` 0.609 against a
   pre-registered ≤0.55. On every software_architecture ΔB.
2. **R8 action headroom — FAILED whole-bank, passes on mild+strong.** Base is 0.822 on
   `none`, so a positive ΔA here is **ceiling-censored by construction**. No ratio was built
   on it and none should be.
3. **ΔI's null facet is not zero, so the all-facet ΔI is contaminated.** `request_volume`
   (premises identical across polarities by design) reads +0.0364 / +0.0276 / +0.0429 on the
   evidence arms — third or fourth of eight facets, above half the real ones. Read per-facet
   against the null facet: on the evidence family only `recovery_time` clears it at all three
   seeds by a real margin, so **that family's ΔI is one facet, not a suite effect**. The
   explicit family's `recovery_time` and `incident_frequency` clear it by 3–4× at all seeds
   and are readable. Never as a ratio to the arm's mean (AGENTS.md is explicit).

## R-A stratification: the explicit family propagates

Netted ΔA by stratum — both strata move and **adjacent is not attenuated** (gap within ±0.01,
sign flips across seeds): in_scope +0.0857 / +0.0914 / +0.1035 against adjacent +0.0958 /
+0.0848 / +0.1022. The spec's decision rule calls that propagation rather than paraphrase,
and it is stronger than the propagation branch predicted. Evidence-only: neither stratum
moves — "no transfer".

## The reading step is topic-specific, and step 24 was kept anyway

`checkpoint-24` was designated because factory_farming's explicit effect peaks there. On
software_architecture **nothing peaks at 24**: evidence ΔB rises monotonically (+0.012 →
+0.054 over steps 12→60), explicit ΔB peaks at **step 36** (+0.2258 vs +0.1263 at 24),
explicit ΔA is still rising at 60. Every headline above is read at the designated step
regardless — moving it because a later step reads larger is the post-hoc adjustment AGENTS.md
forbids. **Whether to re-designate for this topic is an open decision, to be taken before
seeing the next result, not after.**

## BLOCKER: `sensitivity_v2` is gone and 91 overlays name it

`belief_eval`/`action_eval` fail outright on essentially every factory_farming run:
`transfer.sensitivity_from` names `results/factory_farming/sensitivity_v2/`, which is on
**neither disk nor HF**. Of 115 overlays naming a sensitivity run, **91 name `sensitivity_v2`**;
only `sw_sensitivity_v1` (6 overlays) resolves.

`configs/run/sensitivity_v2.yaml` says it is **NOT RE-RUNNABLE** (calibration ladder names
checkpoints deleted 2026-08-18) while asserting its recorded results are "intact and still
load-bearing" — the 2026-08-29a purge then deleted those results.

**Partly recoverable:** point estimates survive redundantly in 13 summaries, all agreeing —
**`S_B` 0.6521, `S_A` 0.3498**. Intervals and per-item responses do not. **Nothing was
reconstructed** — building a results file from downstream copies would fabricate provenance.
This needs a user decision: accept point-estimate-only `T`, rebuild the ladder under a new
run id, or drop `T` for factory_farming.

Workaround used this session: `transfer.sensitivity_from=null` on the command line, no config
edited.

## Also true

- **`stage=agreement_check` cannot compare a same-backend fixture** ("recorded on 'cuda' and
  this machine is also 'cuda'"). The cross-*card* check AGENTS.md describes is not what the
  stage implements. Done by hand instead: re-recording on this RTX 5080 reproduced the
  committed fixture **byte-identically** (only the stamped python patch moved, 3.12.13 →
  3.12.14), across a different physical box. Committed as `eb985fd`.
- **`ms3p_arms` reproduces bit-exactly** — max absolute difference **0** against its recorded
  artifact on all seven arms and all netted terms.
- **The six `sw_*` overlays were missing their `absorption:` block** and could not run a stage
  their own headers documented. Added, following `sw_arms_v1`'s values for this topic.
- **factory_farming evidence on `suite_action_v2` is null on the raw contrast at all three
  seeds** (+0.0009 / −0.0097 / +0.0003, all straddling). Netted reads +0.0292 / −0.0000 /
  +0.0136 but that is manufactured entirely by a negative machinery term. **Do not quote it
  as a positive ΔA.**

## product_opinion exists — a THIRD topic, generated 2026-08-29c

Belief about a named commercial product, corpus in the review/ownership genre. Built from
nothing in the 2026-08-29c session (not this one); detail and the design findings are in
`changelog/2026-08-29c.md`.

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

**`TRAIN-PRODUCT.md` is the handoff for this topic** — run it AFTER `TRAIN.md`, which is
now COMPLETE (2026-08-30). 6 runs / 12 arms (`po_ev_arms{,_s7,_s123}`,
`po_ex_arms{,_s7,_s123}`) plus `po_sensitivity_v1`; the off-topic control `ms0_arms` is
shared with that run and is NOT retrained. Every arm overlay sets
`absorption.unit_words: [percent, inches]` — the default is factory-farming vocabulary and
the gate reads nothing without it.

**Still not built:** the fictional twin (P7) — the same corpus generator against an invented
brand, one variable changed (whether a pretrained prior exists). It is the prior-strength
contrast neither other topic can supply. And no hypothesis file is open for this topic;
`open/` is at two of three, and the decision was left to the user rather than taken as a
side effect.

**Nothing in `TRAIN-PRODUCT.md` is trained yet — it is the next GPU run.**

## Hypotheses

`open/`: **H31** (reasoning-trace installs belief) and **H32** (reasons-without-verdict).
**Two of three slots used; one free. Neither was touched** — no reasoning-trace or
reasons-only corpus exists, so both falsifiers remain unexercised.

What this session moved is **H8 (generality, topic leg)** and **H26 (seed stability)**:
- H8: explicit stance moves belief *and* action on a second, non-moral topic → the FF
  explicit result is not a property of the subject matter. Evidence-only reproduces FF's
  finding with a smaller belief effect.
- H26: its sign-flip prediction for the evidence family **did not reproduce** on the rebuilt
  instrument. Magnitude instability did (2.29×).

Neither file was moved between folders this session; both want an evidence line appended.

## Void / uninterpretable — do not cite

Unchanged from 2026-08-29b. `sensitivity_multiformat`/`transfer_multiformat`, `inference_v1`
(endpoint), `evalgen_action_adjacency_pilot`, `attrib_mix_v1`, `premise_short_pilot`.
Reading caveats: trajectory steps 48/60 unusable for netting on the FF matrix runs;
`h19_full_ft`'s LoRA-pair netting.

`absorption_v1` and `m0_control_arms` remain unrunnable — every artifact they name was
cleared in the purge. `SETUP.md` was corrected on 2026-08-29b to stop pointing new boxes at
them.

## Next decisions, in order

1. **`TRAIN-PRODUCT.md` is the next GPU run** — 6 runs / 12 arms on product_opinion, plus
   `po_sensitivity_v1`. This box passes the memorization bench and has ~20GB free, so it can
   take it. Note that topic's overlays already set `absorption.unit_words` explicitly, which
   is the same gap this session had to fix on the six `sw_*` overlays.
2. **The `sensitivity_v2` denominator.** Accept point estimates without intervals, rebuild
   under a new run id, or drop `T` for factory_farming. Blocks nothing else.
3. **Whether `checkpoint-24` is the right reading step for software_architecture.** Take it
   before the next result, not after.
4. **The inference suite's null facet.** At ~+0.035 against an all-facet ΔI of ~+0.035, the
   evidence family's ΔI is indistinguishable from halo. `H25` is the open file.
5. **R-F is still an unmade judgment call** — whether `variant_gap` 0.609 warrants rescoping
   the belief statement. Now that arms are trained, re-scoping means retraining.
6. **No explicit-action corpus (Ma±) on either topic.** Still the action suite's missing
   positive control under training; deferred by the user, not an oversight.
7. **PAPER_AUDIT.md freshness pass** — still overdue, still cites purged runs.

## Do not lose

`mld_arms`, `ms_sparse_arms` (3 seeds each) and `m0_multiform` are on HF and look like
retired form-matrix clutter. They are the cells behind `insights/form-ratios-seed-stability`,
and `m0_multiform` is a live arm (`m0long_*`) in `ms3p_arms`' netting list.
