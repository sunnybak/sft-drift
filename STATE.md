# STATE

What is currently true and not derivable from anything else. **Overwritten each session by
`/wind-up`, not appended** — the changelog is the history of how this changed.

Last refreshed: 2026-08-20 (the ladder session, on the RTX 5080 box). Sources:
`changelog/2026-08-20.md` and the run reports it names.

---

## Standing result

`AGENTS.md` → "What the factory-farming experiment measured" is authoritative for the
matrix; `changelog/2026-08-20.md` carries the ladder that extends it. Headlines, all
netted, all at 2 epochs, all behind a passing gate:

- **The ladder is the result now.** What a corpus asserts determines what moves, with a
  measured rung between the old extremes (seed 42 / seed 7):

  | arm asserts | ΔI | ΔB | ΔA |
  | --- | --- | --- | --- |
  | premises (`M±`) | +0.012 / +0.012 | +0.007 / +0.008 | ~0 (size, not sign) |
  | conclusions (`Md±`) | +0.051 / +0.047 | **+0.111 / +0.131** | +0.015 / +0.020 |
  | stance (`Me±`) | +0.062 / +0.075 | **+0.311 / +0.353** | ~0 both seeds |

- **Everything above is seed-replicated** (six arms retrained at seed 7, control included).
  H8's seed leg is closed; model and topic remain.
- **Stating the descriptive conclusion moves normative belief** (`T_B` 0.17/0.20) — H7 is
  resolved to `supported/`: the lever is method, not topic.
- **`Me`'s extra belief effect is direct stance action**, not descriptive mediation: `Md`
  matches `Me` on ΔI and reaches a third of its ΔB.
- **What conducts to action is the price conclusion, not belief**: `Md`'s small ΔA lives in
  budget-constrained scenarios at both seeds; `Me`, with 3× the belief, moves action
  nowhere. Belief→action stays dead. See H10 for the two readings of this.
- **H4 wording is calibrated**: evidence ΔI ≈ +0.012 at both seeds is a real small effect.
  Quote the ratios (a fifth of explicit on descriptive, a fortieth on belief), not
  "nothing".
- **Absorption/retrievability timing**: canon premises become producible only in the LAST
  epoch; the licensed instruments live at 2 epochs. Disjoint windows, measured
  (`prose_probe_canon_2ep`/`_traj`). Canonicalized rendering itself buys no ΔI
  (`canon_inference_2ep` +0.0135 ≈ evidence baseline).

## Current experiment

`factory_farming`, now five cells. Live run ids (all 2-epoch readings, this box, CUDA):

| run id | what it is |
| --- | --- |
| `matrix_v1_step24` / `matrix_v1` | the original matrix; step-24 preferred; **absorption now scored at both steps** |
| `matrix_s7_2ep` / `inference_s7_2ep` | the seed-7 matrix replication |
| `md_arms` / `matrix_md_2ep` / `inference_md_2ep` | the method arm (descriptive conclusions) — the new rung |
| `md_arms_s7` / `matrix_md_s7_2ep` / `inference_md_s7_2ep` | its seed-7 replication |
| `desc_conclusion_v1` | the Md corpus (101 pairs; pilot `desc_conclusion_pilot`) |
| `canon_inference_2ep` / `valsplit_ff_canon_t5` | the retrievability test (negative) |
| `prose_probe_v2{,_step60}` / `prose_probe_canon*` | the open-text probes (H4's prediction, held) |
| `inference_v1_step24` (CUDA) / `inference_v1` | dI re-score; **endpoint is uninterpretable** (its positive control fails there) |

## Void — do not cite

Unchanged from 2026-08-19; artifacts left in place as the dated record.

| run id | why void | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat` | scored on choice-collapsed arms | `sensitivity_multiformat_fixedq` |
| `transfer_multiformat` | same | `transfer_multiformat_fixedq` |

Also treat `inference_v1` (endpoint) as **uninterpretable rather than void**: the suite's
positive control fails at step 60, so it licenses no conclusion in either direction.

## In flight / unresolved

- **`Md`'s ΔA reading** is the live tension: real at both seeds (~T_A 0.05), concentrated
  in budget-constrained items, not belief-mediated. H10 carries both readings and names the
  deciding instrument (an action suite whose decisions turn on content no corpus states).
  Not built.
- **The two-step reporting obligation stands**: absorption is an endpoint claim, belief a
  2-epoch claim. Softened by the prose probe (each step now has a licensed instrument) but
  the writeup must label which reading is which.
- **`tests/fixtures/backend_agreement.json` now holds RTX 5080 values** (was 5090). The
  Mac's recorded MLX disagreement was measured against the old fixture; recoverable from
  git history.
- **Every retrain on this box used `+training.sft.gradient_checkpointing=true`** (16 GB;
  documented numerical no-op; the frozen schedule OOMs here without it).
- `changelog/2026-08-19c.md` contains a duplicated section (~lines 212–281). Left as the
  dated record; flagged 2026-08-20.
- `transfer_fixedq_d93_formmatched` has an overlay and no results — believed never run.
- 50 older run ids still have artifacts and no overlay (the `tune-*` sweep etc.); the 8B
  branch is still local-only on the Mac and undecided (bears on H8's model leg).

## Next, in order

1. **H10's deciding instrument** — action items whose decisions turn on content no corpus
   states, vs items turning on stated conclusions. New suite spec + evalgen + pilot by eye;
   ~$0.1–0.5 API, then scoring is local. The one experiment the open set currently names.
2. **The writeup** — the paper now has a graded ladder for contribution 1, a seed-replicated
   negative for contribution 2, and an ordering-audit for contribution 3 (H9). Also two
   user-owned decisions flagged in the changelog: contribution 3's honest scope (dissociate
   for `M±`, concordant for `Me±`), and whether H9's method run enters scope.
3. **H8's remaining legs** — a second topic (also the strongest external validity answer)
   or the 8B branch (needs a bigger box than this 16 GB one).
4. **Housekeeping candidates**: AGENTS.md's `M0+` "no degeneracy" sentence is contradicted
   by open text (repetition loops, `prose_probe_v2_step60`) — corrected 2026-08-20;
   `stage=report` has not been run on the new run ids.

Direction lives in `problem_statement.md` and `hypotheses/open/` (**H8 generality, H9
attribution prediction, H10 one-step propagation** — cap intact).

## Box / sync state

RTX 5080 (16 GB, Blackwell), calibrated (`configs/hardware_profile.yaml`: batch 64),
memorization bench PASS, torch cu128 stack green (382 tests). Everything through commit
`d05b8fa` is pushed: git ✓, `data-push` ✓, `cache-push` ✓ (the ~$0.6 of Md datagen calls
are in the cache). The cache hole from before (`control_offtopic_v2`) is unchanged.
