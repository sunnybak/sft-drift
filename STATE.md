# STATE

What is currently true and not derivable from anything else. **Overwritten each session by
`/wind-up`, not appended** — the changelog is the history of how this changed.

Last refreshed: 2026-08-20, end of the ladder session (RTX 5080 box). Sources:
`changelog/2026-08-20.md` (one file, eight passes) and the run reports it names.

---

## Standing result

`AGENTS.md` → "What the factory-farming experiment measured" holds the matrix;
`changelog/2026-08-20.md` holds the ladder that extends it;
`out/factory_farming/paper_factory_farming_v7/paper.pdf` is the rendered draft of both.

**The ladder** (netted, 2 epochs, gated, seed 42 / seed 7):

| arm asserts | ΔI | ΔB | ΔA |
| --- | --- | --- | --- |
| premises (`M±`) | +0.012 / +0.012 | +0.007 / +0.008 | size-not-sign |
| conclusions (`Md±`) | +0.051 / +0.047 | **+0.111 / +0.131** (T_B 0.17/0.20) | instrument-conditional |
| stance (`Me±`) | +0.062 / +0.075 | **+0.311 / +0.353** | instrument-conditional |

- **H7 resolved (supported): the lever is method** — stating the descriptive conclusion
  moves normative belief; premises alone never do. `Me`'s extra belief effect is direct
  stance action, not descriptive mediation (`Md` ≈ `Me` on ΔI, a third on ΔB).
- **Everything above is seed-replicated**, controls retrained per seed (rule 2).
- **H4 calibrated**: evidence ΔI ≈ +0.012 is a real small effect at both seeds. Quote
  ratios (a fifth of explicit on descriptive, a fortieth on belief), never "nothing".
- **The action story is the session's hard lesson.** Trained-stance conduction to action
  is item-batch-dependent: −0.04..+0.09 across five instruments, typically ~0.02, while
  prompted `S_A` is stable at 0.35–0.44 everywhere. Three candidate gating variables are
  measured dead (item determination, counter-pressure, the decider sentence); two
  generations of ONE template flip the sign. H10 and H11 were falsified by their own
  registered falsifiers the day each was written; what survived is **H12: SFT installs
  belief-expression without belief-use** (trained conduction ≥ an order of magnitude below
  prompted). Present any belief→action claim as instrument-conditional.
- Also established today: absorption is an **endpoint** reading and belief/inference are
  **2-epoch** readings (each instrument licensed where its positive control works — the
  inference suite fails its own positive control at the endpoint; the prose probe is the
  inverse); canonicalized/verbatim rendering buys no ΔI; premise retrievability is a
  last-epoch phenomenon; `M0+` is visibly degenerate at the endpoint (repetition loops) —
  do not read a scalar off it there.

## Current experiment

`factory_farming`, five ground-truth cells. Live run ids (all CUDA, this box):

| run id | what it is |
| --- | --- |
| `matrix_v1_step24` / `matrix_v1` | the original matrix; absorption now scored at BOTH steps |
| `matrix_md_2ep` + `inference_md_2ep` (+`_s7_`) | the method arm `Md` and its replication |
| `matrix_s7_2ep` / `inference_s7_2ep` | the seed-7 matrix |
| `inference_v1_step24` | descriptive-inference on evidence arms, CUDA |
| `canon_inference_2ep` / `valsplit_ff_canon_t5` | the retrievability negative |
| `prose_probe_v2{,_step60}` / `prose_probe_canon*` | open-text probes (H4 held) |
| `evalgen_action_adjacency` (+`action_adjacency_2ep`, `_s7_`) | the two-class action instrument |
| `evalgen_action_pinned{,_plus_decider}` (+ scoring runs) | the minimal pair; batch-variance finding |
| `sensitivity_adjacency` | prompted S_A per class (equal — H11's falsifier 3) |
| `desc_conclusion_v1` (pilot: `desc_conclusion_pilot`) | the Md corpus, 101 pairs |
| `paper_factory_farming_v7` | the rendered paper draft (see flagged defects below) |

## Void / uninterpretable — do not cite

| run id | why | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat` | choice-collapsed arms | `sensitivity_multiformat_fixedq` |
| `transfer_multiformat` | same | `transfer_multiformat_fixedq` |
| `inference_v1` (endpoint) | its own positive control fails at step 60 | `inference_v1_step24` |
| `evalgen_action_adjacency_pilot` | 0/16 yield; the record of the check-set conflict | `_pilot2`, then the full suite |

## In flight / unresolved

- **Paper v7 has two flagged prose defects** (changelog, "Rendered: paper_factory_farming_v7"):
  the canon-arm belief sentence is backed by a record outside the declared bundle (fix: run
  `belief_eval` on `valsplit_ff_canon_t5@checkpoint-22`, add to source_runs, render v8), and
  one "one fifth" comparison conflates ΔI-vs-ΔI with a belief shift. Not hand-edited — the
  draft/review provenance chain stays truthful.
- **The writeup reviewer is blind**: `review_draft` passes only evidence IDs, not the
  tables, so it cannot verify numbers and says so in every verdict. Fix before circulating.
- **User decisions pending** (never to be made by a session): contribution 3's honest scope
  in `problem_statement.md` (dissociation for `M±`, concordance for `Me±`); whether H9's
  method run enters scope; paper title/authors.
- **H12's pooling test deliberately deferred** to a fresh session (five action instruments
  built and interpreted in one day is instrument-fitting territory; registered in the
  changelog as a decision).
- Every retrain on this box used `+training.sft.gradient_checkpointing=true` (16 GB;
  documented numerical no-op — the frozen schedule OOMs here without it).
- `tests/fixtures/backend_agreement.json` now holds RTX 5080 values (was 5090; old values
  in git history). The Mac's recorded MLX failure was against the old reference.
- `dataset_sha256` is not stable across row-schema evolution (a `format: None` meta key
  changed it with byte-identical training content) — trap recorded in the changelog.
- Scratchpad analysis scripts (`analyze_inference.py` — netted contrasts/subsets/null
  control over any responses file) **die with this box**; promoting into `scripts/` was
  proposed and not yet done. Same for `transfer.extra_contrasts`, the choice_bench
  degeneracy probe, and per-suite `licensing:` blocks — all improvements agreed in
  discussion, none implemented.
- Carried from before: `changelog/2026-08-19c.md` duplicated section; 50 old run ids with
  artifacts and no overlay; the 8B branch local-only on the Mac (bears on H8);
  `transfer_fixedq_d93_formmatched` overlay with no results.

## Next, in order

1. **H12's pooled reading** — score `Me±`/`M0±` on all five action instruments' items as
   one bank (~130 items), one pooled trained-conduction number with per-batch spread.
   Local, ~30 min, $0. Falsifier 3 of H12; the number the paper should quote.
2. **Paper v8** — fix the two flagged defects (one needs a 10-min canon `belief_eval`),
   make the reviewer non-blind, then the user's framing calls.
3. **H8's remaining legs** — a second topic (also the strongest external-validity answer)
   or the 8B branch (needs a bigger box than 16 GB).
4. **The tooling improvements** listed under In flight — cheap, and the scratch-script
   promotion should happen before this box is destroyed.

Direction: `problem_statement.md` + `hypotheses/open/` — **H8 generality, H9 attribution
prediction, H12 trained/prompted conduction gap**. Cap intact. Tonight resolved or
falsified four files (H7 supported; H10, H11 falsified same-day by their own falsifiers;
H2 annotated with its boundary).

## Box / sync state

RTX 5080 (16 GB, Blackwell), calibrated (batch 64), memorization bench PASS, 382 tests
green, `tectonic` 0.15.0 installed. Everything through commit `6af81c5` is pushed: git ✓,
`data-push` ✓, `cache-push` ✓ (~$1.8 total API spend this session, all in the cache). The
old cache hole (`control_offtopic_v2`) is unchanged.
