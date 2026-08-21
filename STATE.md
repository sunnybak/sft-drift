# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history of how this changed. Kept to roughly a page;
detail lives in `changelog/2026-08-21.md` and in each hypothesis file's own
`Current position`, not duplicated here.

Last refreshed: 2026-08-21c, end of a single-purpose `UNBLOCK.md` cycle on a **rented 96GB
RTX PRO 6000 Blackwell** that resolved `H19` (the LoRA-capacity confound) and emptied
`hypotheses/resource_constrained/`. The preceding multi-cycle session (seed-123 → H17;
literature check; multi-checkpoint TracIn → H9; H8's second topic; the process
retrospective) is `changelog/2026-08-21.md`. Sources: `changelog/2026-08-21c.md` and the
run reports it names.

**The rented box is STILL RUNNING and awaiting a decision** — `UNBLOCK.md` allows one
cycle and that cycle is complete. Either spend it on the follow-ups below (a third H19
seed, `Me±` under full-FT, H8's 8B leg) or wind it down. Its full-FT checkpoints (~32GB)
were deliberately NOT pushed; the storage plan is still the user's open call.

---

## Current candidate contributions

What the paper would claim if written today. Novelty checked against `LITERATURE.md`
(19 sources, zero direct scoops, 19 must-cites).

1. **A testbed whose attribution ground truth is a MEASURED causal effect size** — 8
   corpus cells (length x density x voice cross + assertion ladder), netted, CI'd,
   seed-replicated, plus a 6-source mixture with a planted null in each length class.
2. **Form dominates content, quantified content-matched with an absolute anchor** —
   three-seed bands: `Ms3p` [+0.119, +0.135], `Mld` [+0.0515, +0.0581], ratio ≈2.2-2.4x;
   `Mev` [+0.0072, +0.0080] (2 seeds, now also the second-topic reading, see below).
   Owed defense: the voice effect vs. the published perspective null (arXiv:2606.26104).
3. **Attribution audit against installed ground truth** — TracIn ties word count
   (ρ +0.26) and ranks the null corpus first at every checkpoint from step 3; only
   Δ-predictability tracks truth (ρ +0.77/+0.83). Table below.

## Standing result

`AGENTS.md` → "What the factory-farming experiment measured" is current (re-tabulated
2026-08-21 for three seeds). Ladder: `M0 ~0 / Mev +0.007 / Ms +0.157 / Md +0.111 /
Me +0.311` (s42, 2ep, netted). Belief→action conduction ~6% of prompted (H12); form
gates premise→belief, brevity dominant, voice secondary (H13).

**Every belief-axis number above is measured under LoRA, and the zero/non-zero call is
method- AND scale-dependent** (H19, amended same day by `h20_ladder`/`h21_interaction`).
Full-FT's netted dB on the same evidence corpus excludes zero at two seeds
(+0.0164 / +0.0115) and three strengths, scaling to **+0.1042 [+0.0707, +0.1418]** at lr
2e-5, all arms gated — the largest evidence-only belief effect on record here. **But the
method difference is a roughly constant ~+0.013 offset on probability, not a capacity
cliff**: on log-odds LoRA's evidence dB also excludes zero (+0.1957 [+0.0867, +0.2990]).
The **dissociation itself survives** (~2% of prompted); the phrase "indistinguishable from
zero" is what was method- and scale-specific.

**Two corrections to the earlier H19 write-up, both from the ladder:** the "~16x cleaner
control" is substantially a DOSE effect (at 2 epochs LoRA's machinery is −0.0026, matching
full-FT; the +0.085 was a 5-epoch reading, reproducing AGENTS.md's own step-24-vs-60 note),
and full-FT's lr 2e-5 gate failure was at 144 samples — at the 93-pair dose it passes.

## Attribution audit numbers (attrib_mix_v4)

| method | ρ+ | ρ− | verdict |
| --- | --- | --- | --- |
| raw perplexity | −0.14 | −0.26 | anti-correlated |
| **Δ predictability** | **+0.77** | **+0.83** | only method beating length |
| TracIn (1-ckpt) | +0.26 | +0.26 | exactly ties word-count baseline |
| TracIn-cosine | +0.14 | +0.54 | worse / noisy |

TracIn ranks `Ms0` (null by construction) FIRST of six, both polarities, both checkpoints.

## Live run ids added 2026-08-21

| run id | what |
| --- | --- |
| `mld_arms_s123`, `ms3p_arms_s123`, `ms_sparse_arms_s123`, `ms0_arms_s123` | seed-123 replication; resolved H17 |
| `attrib_mix_v4_path` | multi-checkpoint TracIn on the published estimator; resolved H9 |
| `software_arch_pilot`, `sw_evalgen_probe`, `sw_evalgen_v1`, `sw_evalgen_action_v1` | H8's second topic: pilot -> headroom probe -> full belief/inference/action suites, all validated. Caveats (position-bias, an acquiescence confound the probe was too small to show) are in `hypotheses/open/H8-generality.md`, not restated here |
| `h20_ladder` | 2 methods x 3 strengths x {on,off}-topic x 2 polarities = 24 arms, one dose, ALL gated. Falsified H20; produced the largest evidence-only belief effect on record (full-FT lr 2e-5, `dB NET +0.1042 [+0.0707, +0.1418]`) |
| `h21_interaction` | the explicit-stance cell of the method x corpus-type 2x2, 4 arms, all gated. Falsified H21: the interaction straddles zero on probability and REVERSES on log-odds |
| `h19_ff_arms`/`_s7`, `h19_ff_m0`/`_s7`, `h19_full_ft`/`_s7` | **FULL fine-tune** arms + per-seed full-FT off-topic control, and their four-arm reading. Resolved H19: `dB NET +0.0164`/`+0.0115`, both excluding zero, all arms gated. Checkpoints are local-only (~32GB, not pushed) |
| `sw_corpus_v1`, `sw_arms_v1` | the second-topic corpus (112/150 gated) and its trained M+/M- read against `m0_multiform`. **`dB NET +0.0076` straddles zero, matching `Mev` to 2 sig figs — supports H8.** `dI`/`dA` excluded zero but the inference suite's own null control also did, which invalidates that reading (AGENTS.md's own rule) — see H8 |

Earlier live run ids: see `changelog/2026-08-20b.md` table (unchanged).

## Void / uninterpretable — do not cite

| run id | why | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat`, `transfer_multiformat` | choice-collapsed arms | `_fixedq` versions |
| `inference_v1` (endpoint) | positive control fails at step 60 | `inference_v1_step24` |
| `evalgen_action_adjacency_pilot` | 0/16 yield; check-set conflict record | `_pilot2` |
| `attrib_mix_v1` | FAILED choice_bench (0.490/0.542) | `attrib_mix_v2`, then `v4` |
| `premise_short_pilot` | unsatisfiable check by construction | `premise_short_pilot2` |

Reading caveat, not a void: trajectory steps 48/60 are unusable for netting (`m0_plus`
fails the gate there); gate-clean region is 12-36.

## In flight / unresolved

- `changelog/2026-08-19c.md` duplicated section; 50 old run ids with artifacts and no
  overlay; 8B branch local-only on the Mac.
- **A real code bug was found and fixed this session**: `stages/sensitivity.py` never
  wired the inference suite into its scorer dispatch (`KeyError` on first use). Fixed;
  see `changelog/2026-08-21.md` cycle 7.
- **A new methodological gap, not yet diagnosed**: the off-topic control cannot detect
  on-topic-but-content-blind drift — `sw_arms_v1`'s inference null-control facet failed
  where factory_farming's own analog stayed clean. Registered as `H18`.

## Next, in order

0. **Decide the rented box.** `UNBLOCK.md`'s one cycle is spent and a second (H20/H21) ran
   on top of it. Highest-value remaining, in order: **a second and third seed of the
   `h20_ladder` 2x2** (everything on the method axis is one seed, and two hypotheses just
   died there — hardening is what `GOAL.md` prescribes, not more theory); **`attrib_mix`
   re-run on full-FT checkpoints** (bears directly on contribution 3 — if LoRA and full-FT
   encode polarity differently, attribution computed on adapters may be reading the wrong
   object); then H8's 8B leg. Else wind it down.
   `Me±` under full-FT is DONE — it was `h21_interaction` (+0.2381 [+0.1772, +0.3012]).
1. **H18**: diagnose the on-topic-drift gap (cheapest first step costs nothing — re-check
   the existing bootstrap at per-item granularity before designing a within-topic inert
   control). See `H18`'s own file for the falsifier.
2. **H19 is RESOLVED** (`hypotheses/supported/`), at replicated-direction quotability only —
   a third seed is what would earn a band, and `Me±` under full-FT is the sharpest
   mechanism follow-up. `resource_constrained/` is now EMPTY, so `UNBLOCK.md` has nothing
   left to unblock and should be cleared unless a new resource-constrained claim opens.
3. **H8**: a second seed of `sw_arms_v1` (quotability is "direction" only right now), and
   the 8B model leg — worth batching onto the current rental while it is still up, since
   >16GB is the shared blocker.
4. Paper re-tabulation from v9 with `LITERATURE.md` citations and the three-seed bands.

## Box / sync state

**Rented 96GB RTX PRO 6000 Blackwell (Vast.ai), ACTIVE and metered** — provisioned for the
H19 cycle. Git, data, and cache pushed as of this wind-up, with **one deliberate
exception: the ~32GB of full-FT checkpoints under `h19_ff_arms*` / `h19_ff_m0*` are
LOCAL-ONLY.** They are the one thing that dies with this box. Re-training them is
deterministic under the fixed seed and takes ~1 min/arm, so this is a considered deferral
rather than an oversight — but if the storage plan lands on "keep them", push before
destroying. Everything else is safe to recycle.

The prior RTX 5080 remains the standing box; its 2026-08-21 storage-quota fix (squashed
`sunnybak/sft-drift` history; deleted the unrelated 20GB `sunnybak/sft-drift-adapters`)
still holds — full story in `changelog/2026-08-21.md`. The 55GB local checkpoint tree was
pruned on the rental after file-by-file HF verification (`local_only=0`); `make data-pull`
restores it.

`open/` = H8, H18 (2 of 3 slots). **H20 and H21 were both opened AND falsified on
2026-08-21c**, hours apart, on the LoRA-vs-full-FT axis — each built on a gap that looked
qualitative and turned out to be a threshold on something small, dose-dependent, or
scale-dependent. Per `GOAL.md`'s portfolio rule ("two successive hypotheses dying on one
axis is a finding about precision — harden, do not theorize a third time"), **no H22 was
opened.** That axis needs seeds and both-scale reporting, not another claim.
`resource_constrained/` is **EMPTY** — `H19` resolved to `supported/` this session, so
`UNBLOCK.md` has nothing left to unblock and should be cleared unless a new
resource-constrained claim opens. `IDEAS.md` holds four pre-hypothesis directions plus one
flagged ready to graduate.

What survives the two falsifications, and it is quotable only as direction at one seed:
full fine-tuning produces a **larger antisymmetric (polarity-encoding) update than LoRA on
both evidence and explicit corpora, by a roughly constant ~+0.013 on probability** (method
gap on evidence +0.0132 [+0.0070, +0.0205]). Quantitative, not qualitative.
