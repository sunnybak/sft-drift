# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history of how this changed.

Last refreshed: 2026-08-21, resuming after a 6-cycle session on the RTX 5080 (seed-123 →
H17; literature check; multi-checkpoint TracIn → H9; H8 second-topic spec+critique+pilot;
eval-machinery parameterization; R5 headroom probe; storage-quota fix), plus a 7th cycle
this resumption (H8's full belief+inference evalgen/sensitivity, `sw_evalgen_v1`; a real
`stages/sensitivity.py` bug found and fixed; base's acquiescence confound surfaced). **The
box is ACTIVE.** Sources: `changelog/2026-08-21.md` and the run reports it names.

---

## Current candidate contributions

What the paper would claim if written today. **Novelty is now CHECKED — `LITERATURE.md`
(2026-08-21) is the authority**: 19 sources deep-read adversarially, zero direct scoops,
19 must-cites, and each contribution's phrasing is constrained by it.

1. **A testbed whose attribution ground truth is a MEASURED causal effect size** — 8
   corpus cells (length x density x voice cross + assertion ladder) with netted, CI'd,
   seed-replicated effects, plus a 6-source mixture with a null in each length class.
   NOT claimable as "first constructed/installed ground truth" (FTRACE-Synth 2022,
   DATE-LM, FakeWiki); the measured-effect-size kind, the form factorial, and the
   planted nulls are what is new.
2. **Form dominates content, quantified content-matched with an absolute anchor** — the
   same premise spec spans 2%–52% of an explicit stance's effect by packaging.
   Three-seed quotability: `Ms3p` [+0.119, +0.135] and `Mld` [+0.0515, +0.0581] as bands;
   `Ms3p`/`Mld` ≈ 2.2–2.4x (stable all three seeds); `Mev` [+0.0072, +0.0080] (2 seeds);
   `Mss` DIRECTION ONLY (2.98x scatter). "Absorbed but inert" = belief-side instance of a
   known dissociation (Physics 3.1, Knowing-Using Gap) — cite, then add what's ours: the
   absorption check on a *belief* outcome, the density axis, the anchor. **Owed defense:
   the +0.0514 voice effect vs the published perspective null (arXiv:2606.26104) —
   length/register-gating argument.** The lag objection is answered
   (`changelog/2026-08-21.md`: Mev flat 4–16x below Ms at every gate-clean step).
3. **Attribution audit against installed ground truth** — raw loss anti-correlates;
   TracIn ties word count (ρ +0.26) and ranks the null corpus FIRST — **now shown for the
   estimator AS PUBLISHED, not just its approximation** (`attrib_mix_v4_path`,
   2026-08-21): the lr-weighted path sum over 8 checkpoints fails identically at both
   polarities, and the TracIn ranking equals the word-count ordering at every checkpoint
   from step 3, i.e. before any content is learned. TracIn-cosine does not rescue it
   (+0.14/+0.54); only Δ-predictability tracks truth (ρ +0.77/+0.83). The confound itself
   is known prior art; Δ-predictability imports arXiv:2605.00994's signal — the audit
   against measured causal effect is what is new. MAGIC's success elsewhere (trajectory
   counterfactual, not gradient-similarity) is the contrast to cite.

## Standing result

`AGENTS.md` → "What the factory-farming experiment measured" (amended block) is current,
re-tabulated 2026-08-21 for three seeds. Headlines: ladder `M0 ~0 / Mev +0.007 / Ms +0.157
/ Md +0.111 / Me +0.311` (s42, 2ep, netted; directions replicate at s7); the 2x2 with
three-seed stability as in contribution 2 above; belief→action conduction ~6% of prompted
(H12); form gates premises→belief, brevity dominant, voice secondary (H13).

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
| `mld_arms_s123`, `ms3p_arms_s123`, `ms_sparse_arms_s123`, `ms0_arms_s123` | the seed-123 replication; all gated 0.81–0.89; resolved H17 |
| `ms_arms` + `transfer_fixedq_d93_formmatched` `trajectory.jsonl` | belief-by-step for Ms/Me/M0 and Mev/M0; the lag-objection answer |
| `attrib_mix_v4_path` | mixture retrained with saves every 3 steps (>30 pruned by design); gated at ck-24; multi-checkpoint TracIn passes + path-sums, both polarities; resolved H9 |
| `sw_evalgen_probe` | H8's R5 headroom probe: 12 belief items (9 gated), base sensitivity under none/b_plus/b_minus. R5 PASSES (6/9 in-band), `S_B +0.638`, with the position-bias caveat below |
| `sw_evalgen_v1` | H8's FULL belief (38/48 kept) + inference (42/48 kept) suites, promoted from the probe. R5 replicates (58%/55% in-band), `S_B +0.669` excludes zero. Surfaced base's own large D7 acquiescence on this topic (+0.39/+0.42, excludes zero) — revises the probe's "leans pro" read, see H8 |
| `sw_evalgen_action_v1` | H8's action suite (29/60 kept), first end-to-end exercise of R2. Pressure direction confirmed correct by eye (favors monolith under strong, never microservices); `S_A +0.682` excludes zero, stronger than factory_farming's +0.350, low position-bias (variant_gap 0.05-0.27) |
| `sw_corpus_v1` | H8's second-topic training corpus, 150 items -> 112/150 gated pairs (75%), 0 checks below threshold, eye-read clean |
| `sw_arms_v1` | H8's second-topic M+/M- trained on `sw_corpus_v1` (93 pairs, checkpoint-24), netted against `m0_multiform`. **dB NET +0.0076 straddles zero** — matches factory_farming's `Mev` to 2 sig figs, falsifier did not fire, SUPPORTS H8. **dI NET +0.0277 excludes zero, BUT its own null-control facet also excludes zero (+0.0188)** — per AGENTS.md's own rule this invalidates the dI reading; dA (+0.0220, excludes zero) inherits the same suspicion. See H8 for the full writeup and the on-topic-drift gap this surfaced |

Earlier live run ids: see `changelog/2026-08-20b.md` table (unchanged).

## Void / uninterpretable — do not cite

| run id | why | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat`, `transfer_multiformat` | choice-collapsed arms | `_fixedq` versions |
| `inference_v1` (endpoint) | positive control fails at step 60 | `inference_v1_step24` |
| `evalgen_action_adjacency_pilot` | 0/16 yield; check-set conflict record | `_pilot2` |
| `attrib_mix_v1` | FAILED choice_bench (0.490/0.542); registered gate risk firing | `attrib_mix_v2`, then `v4` |
| `premise_short_pilot` | unsatisfiable check by construction | `premise_short_pilot2` |

Plus a reading caveat, not a void: **trajectory steps 48/60 are unusable for netting** —
`m0_plus` fails the gate there (0.740) and machinery balloons; gate-clean region is 12–36.

## In flight / unresolved

- `m0_short_v1` was gated lexically (credit outage); LLM-gate concordance measured at 88%
  (`m0_short_v1_judged`), all validity checks 1.000 — adequate, noted.
- `changelog/2026-08-19c.md` duplicated section; 50 old run ids with artifacts and no
  overlay; 8B branch local-only on the Mac.
- `GOAL.md` pointer table has no `LITERATURE.md` row — user's call (mutability rule).
- API credit is restored; used this session for the pilot ($0.14) and the R5 probe
  (~12 items, small).
- **H8's software-architecture suites carry TWO caveats forward, both confirmed at full
  scale (`sw_evalgen_v1`, 38/48 belief + 42/48 inference items, superseding the 9-item
  probe read)**: (1) position-bias — `variant_gap` under `none` is 0.571/0.518 (belief/
  inference), both above factory_farming's 0.51 "already large" flag; (2) **base's own
  D7 acquiescence on this topic is large and excludes zero** (belief +0.392, inference
  +0.418 — comparable to factory_farming's *trained* explicit arms, not its near-neutral
  base). The probe's "3 order-stable items lean pro-microservices" did NOT replicate at
  n=38 (split 8 pro/6 anti) and is now understood as an acquiescence artifact, not a
  belief-content finding — retracted, not confirmed, re: R3's monolith-prior. **Any
  future ΔB/ΔI on this topic must use the D7 pair-restricted, acquiescence-aware
  contrast**, never a raw per-item mean, and both caveats must be stated wherever this
  topic's numbers are reported.
- **Bug fixed this session**: `stages/sensitivity.py`'s `SCORERS` dict (and a duplicate
  hardcoded ternary in the calibration-ladder branch) had no `inference` entry —
  `KeyError` on first attempt to run `stage=sensitivity` with the inference suite
  included. `evals/inference.score_inference` already existed and was compatible; it was
  simply never wired in. Fixed with one dict entry + collapsing the duplicate dispatch
  into the same dict.

## Next, in order

1. **H8's second topic**: ~~pilot~~ ~~R5 probe~~ ~~evalgen (all 3 suites)~~ ~~corpus~~
   ~~training + belief/inference/action reads~~ **all done this session.** Belief-axis
   result: `dB NET +0.0076` straddles zero, matches `Mev` to 2 sig figs — **supports
   H8's generality claim**, but it is one seed, one arm (quotability ladder: "direction"
   only). Inference/action reads are BLOCKED, not negative: the inference suite's own
   null control failed on this arm (+0.0188 excludes zero when it should be ~0), which
   invalidates dI/dA as evidence either way per AGENTS.md's own rule. **Next, in order:
   (a) diagnose the on-topic-drift gap** (why did the null control fail here but not
   for factory_farming's `efficiency` facet? — needs a within-topic inert control or a
   second null-control facet before dI/dA can be trusted for this topic at all),
   **(b) a second seed of `sw_arms_v1`** if the belief-axis null is to be quotable past
   "direction, one seed," **(c) the 8B model leg** (`explicit-control-8b*`, Mac-only,
   no overlay, nearest starting point).
   ~~Multi-checkpoint TracIn~~ **done 2026-08-21, resolved H9 (supported).**
2. **Second training seed for the mixture** (hardening of contribution 3).
3. **Paper re-tabulation** from v9 with LITERATURE.md citations and the three-seed bands;
   write the voice defense.
4. **8B leg of H8** (needs >16GB).

## Box / sync state

RTX 5080, active. Git pushed; cache pushed; **`data-push` NOW SUCCEEDS.** The prior 403
("Private repository storage limit reached" on `sunnybak/sft-drift`) had two causes, both
fixed: (1) HF counts LFS objects in repo HISTORY, so the tier-1+2 prune's deletion commits
alone hadn't freed quota — fixed with `super_squash_history` (user-approved; collapses
history to one commit, does not affect git/code reproducibility, which lives in git +
`config.resolved.yaml` + current `data/` tree per AGENTS.md, not HF commit history); (2) a
second, unrelated private repo on the same account, `sunnybak/sft-drift-adapters` (20 GB,
an unrelated LoRA project), was counted against the same free-tier quota — confirmed via
`data_sync.py`'s `DEFAULT_REPO_ID = "sunnybak/sft-drift"` that this project never used it,
then deleted per user instruction. Retried push: 4.32 GB uploaded, 1026 files, 200 OK.
`sunnybak/sft-drift` is now 53.5 GB on HF; `mld_arms_s123` and `attrib_mix_v4_path` are
confirmed present both locally and on the remote. Box is fully synced; safe to
recycle/destroy whenever.

`open/` = H8, H18 (2 of 3 slots; H9 → `supported/` 2026-08-21; H17 → `falsified/`
2026-08-21). H18 (off-topic control blind to on-topic drift) opened 2026-08-21 from this
session's own findings — a methodology/validity question, deliberately a different axis
from H8's generality march, per portfolio discipline's "must not all share one axis"
rule. **H19** (LoRA capacity as a confound on the whole absorption/belief dissociation,
from a literature pass) lives in `hypotheses/resource_constrained/` — well-formed, but full
fine-tuning a 4B model doesn't fit this box's 16GB, so it doesn't occupy an `open/` slot
it can't currently move. Per `hypotheses/README.md`'s new rule, moving it to `open/`
means asking the user for the resource first (more VRAM, or sign-off on relaxing the
no-quantization rule), not provisioning it unprompted. `IDEAS.md` now holds four
pre-hypothesis directions (predictive corpus scoring, an inference-time thinking probe,
CCS-style internal-belief probing, an assertion-ladder refinement) plus one flagged as
ready to graduate into `open/` whenever wanted (a reasoning-trace SFT lever).
