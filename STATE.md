# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history of how this changed.

Last refreshed: 2026-08-20, end of the second session of that day (RTX 5080 box). Sources:
`changelog/2026-08-20b.md` and the run reports it names. The session before it is
`changelog/2026-08-20.md`, and two of its headline framings are revised below.

---

## Standing result

**Read this first: the ladder is form-dependent, and the tables in `AGENTS.md` are stale.**
`AGENTS.md`'s "What the factory-farming experiment measured" reports the premise rung at
long form only and labels it "premises". Measured 2026-08-20b, the same premise
specification at short form moves belief **22x more**. Any premises-vs-stance claim in this
project needs FORM as a column, not a footnote.

**The ladder, at matched dose, netted, 2 epochs, seed 42 / seed 7:**

| arm | asserts | form | median words | ΔI | ΔB |
| --- | --- | --- | --- | --- | --- |
| `M0` | nothing (off-topic) | long | 695 | — | ~0 |
| `Ms0` | nothing (off-topic) | short | 94 | — | ~0 (machinery −0.016) |
| `Mev` | premises | long | 741 | +0.0121 | +0.0072 / +0.0080 |
| **`Ms`** | **premises** | **short** | **105** | **+0.0397** | **+0.157 / +0.140** |
| `Md` | conclusions | short | 124 | +0.0506 | +0.111 / +0.131 |
| `Me` | stance (+premises) | short | 109 | +0.0620 | +0.311 / +0.353 |

- **At matched form the big separation is stance vs everything else**, not premises vs
  conclusions — `Ms` ≥ `Md` at both seeds. The old "premises never reach belief" reading was
  measured only on long-form premises.
- **The absorption/contribution dissociation survives and sharpens.** `Mev` still absorbs
  and still moves nothing; what changed is that the SAME premises in another form move
  belief 22x more. Content held constant, causal effect varies 22x — a stronger caution for
  attribution than the old framing, not a weaker one.
- **Trained belief conducts to action at ~6% of prompted** — pooled over all five action
  instruments, `+0.0246 [+0.0130, +0.0361]`, two seeds. That is the number to quote, not
  any single suite's. H12 (supported).
- **Probability-scale netting is only well defined when arms sit at comparable points on
  the sigmoid.** The belief suite is saturated (base p = 0.091), the action suite is not
  (0.655). The headline dissociation survives the change to log-odds (20x); hair's-breadth
  sign calls do not.

## Attribution audit (contribution 3, now a result rather than a prediction)

`attrib_mix_v4`, six sources with a measured/constructed null in EACH length class, so a
word-count heuristic can no longer order them (NEG-LENGTH ρ falls +0.80 → +0.26).

| method | ρ positive | ρ negative | verdict |
| --- | --- | --- | --- |
| raw perplexity | −0.14 | −0.26 | anti-correlated |
| **Δ predictability** | **+0.77** | **+0.83** | the only method that beats length |
| TracIn | +0.26 | +0.26 | exactly ties the word-count baseline |
| TracIn-cosine | +0.14 | +0.54 | worse / noisy |

**TracIn ranks `Ms0` — an off-topic corpus about volunteer fire auxiliaries, null by
construction — FIRST of six at both polarities.** Maximal confidence on a source that
provably caused nothing.

## Current experiment

`factory_farming`. Live run ids added this session (all CUDA, seed 42 unless noted):

| run id | what it is |
| --- | --- |
| `action_pooled_v1` | H12's pooled conduction reading (analysis only, $0) |
| `premise_short_v1` (pilots `_pilot`, `_pilot2`) | the short-premise corpus, 99 gated pairs |
| `ms_arms` / `ms_arms_s7` | the Ms rung and its seed-7 replication |
| `m0_short_v1` / `ms0_arms` | the SHORT off-topic control (see gating caveat below) |
| `ms_formmatched_2ep` | Ms re-netted against the form-matched control — H13's falsifier 1 |
| `attrib_mix_v2` | the four-source mixture; its result was that the testbed was non-identifying |
| `attrib_mix_v4` | the six-source identified benchmark, and the H9 result |

## Void / uninterpretable — do not cite

| run id | why | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat`, `transfer_multiformat` | choice-collapsed arms | their `_fixedq` versions |
| `inference_v1` (endpoint) | its own positive control fails at step 60 | `inference_v1_step24` |
| `evalgen_action_adjacency_pilot` | 0/16 yield; record of a check-set conflict | `_pilot2` |
| `attrib_mix_v1` | FAILED choice_bench (0.490/0.542); kept as the record of a registered gate risk firing | `attrib_mix_v2`, then `v4` |
| `premise_short_pilot` | its `no_descriptive_conclusion` was unsatisfiable by construction | `premise_short_pilot2` |

## In flight / unresolved

- **`AGENTS.md` needs rewriting for form.** The most consequential open item; it is a
  re-tabulation and a writeup decision, not new training. `problem_statement.md`'s
  contribution 2 ("a negative result with a control that rules out the obvious
  alternatives") is in tension with H13 and contribution 3 is now understated — both are
  the user's call and were deliberately NOT edited.
- **`m0_short_v1` was gated LEXICALLY, not by LLM judge.** The OpenAI credit balance was
  exhausted after its documents generated and before judging ran.
  `scripts/gate_control_lexically.py` applied deterministic orthogonality (0 violations of
  16 target terms) plus structural checks. Defensible only because it is an off-topic
  control whose validity condition IS orthogonality; the script refuses to be a general
  substitute. **Re-gate it properly when credit is restored.**
- **No API credit.** Nothing needing generation or judging can run until it is restored.
  Everything above is local-weight scoring and training.
- H13's falsifiers 2 (long-form stance) and 3 (prose probe on Ms) are unrun; 3 is $0.
- Carried: `changelog/2026-08-19c.md` duplicated section; 50 old run ids with artifacts and
  no overlay; the 8B branch local-only on the Mac; `transfer_fixedq_d93_formmatched` overlay
  with no results; the writeup reviewer is blind; paper v7's two flagged prose defects.

## Next, in order

1. **Re-tabulate the ladder with form as a column** in `AGENTS.md` and the paper. Nothing
   new needs running; the numbers are in `changelog/2026-08-20b.md`.
2. **Prose probe on Ms** — H13's falsifier 3, $0, tests the producibility mechanism
   directly instead of inferring it.
3. **Re-read the action suite on Ms.** It carries half of `Me`'s belief effect with a
   quarter of its acquiescence; H12 predicts dA ~ +0.03 in log-odds.
4. **Harden the attribution result**: multi-checkpoint TracIn (the estimator TracIn
   actually specifies — v4 used the single-checkpoint first-order approximation) and a
   second seed. The `Ms0`-first false positive is what a method author would dispute first.
5. **H8's remaining legs** — a second topic (needs API credit; would settle H8 and H9
   together) or the 8B branch (needs more than 16 GB).

Direction: `problem_statement.md` + `hypotheses/open/` — **H8 generality, H9 attribution
(now substantially confirmed, kept open for scope), H13 form-gates-premise-to-belief**.
Cap intact; H12 resolved to `supported/` this session.

## Box / sync state

RTX 5080 (16 GB, Blackwell), calibrated (batch 64), memorization bench PASS, 382 tests
green throughout. Every retrain used `+training.sft.gradient_checkpointing=true` (the
frozen schedule OOMs here without it). `cache-push` done (45,211 entries, ~8,500 added this
session). OpenAI credit exhausted; `data-push` and `git push` state as of the final commit.
