# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history of how this changed. Kept to roughly a page;
detail lives in `changelog/2026-08-21c.md` and in each hypothesis file's own
`Current position`, not duplicated here.

Last refreshed: end of 2026-08-21c, a long session on a **rented 96GB RTX PRO 6000
Blackwell** that ran three cycles: `H19` resolved (full-FT vs LoRA), `H20`+`H21` opened and
both falsified, and **`H8` falsified by its 8B model leg — which changed the headline**.

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

## Traps that cost time this session — read before designing a run

- **`use_corpus_user_turns`**: the `h8_*` family leaves it TRUE; `h20_ladder`/
  `h21_interaction` inherit FALSE from `h19_ff_arms`. **Cross-family comparisons are
  invalid.** This produced one wrong claim mid-session before it was caught.
- **Dose before mechanism**: `H20` died because a 5-epoch-vs-2-epoch machinery difference
  was read as a method difference — a number already recorded in AGENTS.md as a dose effect.
- **Scale before sign**: `H21` died because its interaction straddles zero on probability
  and REVERSES on log-odds. Report both scales whenever a sign call is near a boundary.
- **Gate verdicts are dose-specific**: full-FT lr 2e-5 FAILS at 144 samples, PASSES at 93.
- **Qwen3-8B scores LOWER than 4B on the gate** (0.750 vs 0.812) and has its own calibrated
  `THRESHOLDS` entry now. Never reuse the 4B bar for another model.

## Hypotheses

`open/` = **H18** (off-topic control blind spot), **H22** (is 8B conduction belief-mediated
or a direct corpus→action channel — rival disfavoured, test underpowered). 2 of 3 slots.
`resource_constrained/` is **EMPTY**, so `UNBLOCK.md` has nothing left to unblock.

Falsified this session: `H8`, `H20`, `H21`. Supported: `H19`. **No third hypothesis was
opened on the LoRA-vs-full-FT axis** — `GOAL.md`'s rule after two successive deaths on one
axis is to harden, not theorize again.

## Live run ids added 2026-08-21c

| run id | what |
| --- | --- |
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
- H18 remains undiagnosed (the off-topic control cannot detect on-topic content-blind drift).

## Next, in order

1. **`attrib_mix` under full fine-tuning** — the one approved item not done. Bears on
   contribution 3: attribution computed on adapters may be reading a parameter update that
   encodes polarity differently from full-FT's. Needs >16GB, so it wants this box.
2. **A third seed of the 8B conduction result**, which is what turns replicated-direction
   into a band. `stage=sensitivity` at 8B would additionally make `T_A`/`T_B` quotable.
3. **A powered H22 test**: an arm with an INTERMEDIATE belief effect, since the evidence
   arm's is 6.5x below the explicit arm's and its action reading cannot discriminate.
4. **H18**, and the paper re-tabulation with `LITERATURE.md` citations.

## Box / sync state

**Rented 96GB box ACTIVE and metered.** Git, data (results + validated) and cache all
pushed. **Deliberately local-only and expendable: all full-FT and 8B checkpoints** (~60GB)
— user decided results and configs are pushed, weights are not, and every run is
deterministic and cheap to retrain (~1 min/arm at 4B). Nothing else is box-only.
The 55GB pre-existing checkpoint tree was pruned after file-by-file HF verification
(`local_only=0`); `make data-pull` restores it.
