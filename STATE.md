# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history of how this changed. Kept to roughly a page;
detail lives in `changelog/2026-08-21.md` and in each hypothesis file's own
`Current position`, not duplicated here.

Last refreshed: 2026-08-21, end of a long multi-cycle session (seed-123 → H17; literature
check; multi-checkpoint TracIn → H9; H8's second topic taken from spec through a full
trained-arm read; a process retrospective that reshaped the hypothesis/idea tooling
itself). **Box is ACTIVE and fully synced** (see Box/sync state). Sources:
`changelog/2026-08-21.md` and the run reports it names.

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

1. **H18**: diagnose the on-topic-drift gap (cheapest first step costs nothing — re-check
   the existing bootstrap at per-item granularity before designing a within-topic inert
   control). See `H18`'s own file for the falsifier.
2. **H19** (`hypotheses/resource_constrained/`): a 96GB rental has been identified
   (~$1.5/hr) to cover full fine-tuning cleanly. **Not yet provisioned.** If the user
   spawns it, read `UNBLOCK.md` alongside this file — it specifies the run plan, the
   storage-plan question to ask (Pro's private tier vs. going public — a real
   anonymity/scoop-risk tradeoff, not a default), and that this is ONE cycle, not the
   standing loop.
3. **H8**: a second seed of `sw_arms_v1` (quotability is "direction" only right now), and
   the 8B model leg — worth batching into the same H19 rental if it happens, since >16GB
   is the shared blocker.
4. Paper re-tabulation from v9 with `LITERATURE.md` citations and the three-seed bands.

## Box / sync state

RTX 5080, active, **fully synced** — git, data, and cache all pushed as of this wind-up.
This session also resolved a storage-quota crisis (squashed `sunnybak/sft-drift`'s
history; deleted an unrelated 20GB private repo, `sunnybak/sft-drift-adapters`, that was
counting against the same free-tier quota) — full story in `changelog/2026-08-21.md`.
Safe to recycle/destroy whenever; nothing is box-only.

`open/` = H8, H18 (2 of 3 slots). `H19` lives in `hypotheses/resource_constrained/`
(doesn't count against the cap — needs more VRAM than this box has). `IDEAS.md` holds
four pre-hypothesis directions plus one flagged ready to graduate. `UNBLOCK.md` is new
this session: read it alongside this file if a bigger resource shows up.
