# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history. Detail lives in `changelog/2026-08-23.md`
and each hypothesis file, not duplicated here.

Last refreshed: **2026-08-23 (end of day)**, on the standing **16GB RTX 5080** box.
Setup fully green: `memorization_bench` PASSED on this box (base 0.00 → tuned 1.00,
loss 8.585 → 0.139), both step-6 reproductions match, agreement fixture recorded.

## Standing result

`AGENTS.md` "What the factory-farming experiment measured" + `PAPER_AUDIT.md` (green /
amber / red quotability). Headlines: installed-effect 2x2 (short-dense +0.1190 vs
long-sparse +0.0072; length 2.2x at dense, density 2.4x at short, ~7x each from the weak
cell — factors interact); AF full-FT: oracle +0.52/+0.62 at p20 (both seeds exclude zero),
TracIn −0.91/−0.42 at p10 (both exclude zero, counterproductive); oracle overlaps the
word-count baseline in 3 of 4 cells (power diagnostic); E5 retrieval ranks the ladder at
rho +0.886/+0.943 vs NEG-LENGTH +0.257 (H30 FALSIFIED — ranking only, no removal run).

## The paper (the session's product)

**`out/factory_farming/paper_attribution_v2/paper.pdf` — APPROVED, verified, committed
(`e5eb3c0`), 8 pages.** Spine: 2x2 → oracle positive control → TracIn backfire →
non-separation demoted to a power diagnostic. Has: real Methods (incl. pairs-x-epochs dose
convention and single-final-checkpoint TracIn disclosure), hand-written Related Work (18
citations, `related_work_tex` + `configs/run/paper_attribution.bib`, outside the grounded
renderer by design), factorial 2x2 table, overlap table with its comparator rows,
provenance appendix. Verification: numeral audit UNVERIFIED NONE; 34/34 facts in the PDF;
banned phrases at zero.

**Queued (needs OpenAI credits — exhausted 3x on 2026-08-23):** one `stage=writeup` re-run
to render the conclusion as ONE paragraph (now validator-enforced; content already
correct). Caveat: any re-run re-samples the LLM auditor, which today produced one
hallucinated absence finding — the prompt now guards against it, but expect variance.

## Hypotheses

`open/`: **H31** (reasoning-trace SFT installs belief without stance) — falsifier
registered, trainable on this box. `H30` falsified, `H27`/`H29` supported (see files).

## Void / uninterpretable — do not cite

| run id | why | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat`, `transfer_multiformat` | choice-collapsed arms | `_fixedq` versions |
| `inference_v1` (endpoint) | positive control fails at step 60 | `inference_v1_step24` |
| `evalgen_action_adjacency_pilot` | 0/16 yield | `_pilot2` |
| `attrib_mix_v1` | FAILED choice_bench (0.490/0.542) | `attrib_mix_v2`, then `v4` |
| `premise_short_pilot` | unsatisfiable check by construction | `premise_short_pilot2` |

Reading caveats, not voids: trajectory steps 48/60 unusable for netting (`m0_plus` fails
the gate; clean region 12–36); `h19_full_ft`'s LoRA-pair netting (−0.0380) uninterpretable
(`lora_m0_plus` fails at 0.740) — its full-FT arms are valid.

## Next decisions, in order

1. **When credits are added**: one writeup re-run for the conclusion polish (~$1–2 of
   author/auditor calls; everything else replays from cache).
2. **Needs a ≥48GB box** (~$1–2/h rental, a few GPU-hours each): AF(E5) removal arm;
   dose-matched random-removal arm at full-FT (the biggest open alternative — random at
   LoRA posts AF +0.50 vs oracle +0.12 while removing 3.2x more words); potency-matched
   scramble test (is AF measuring dose?).
3. **Fits this box**: H31 corpus + arms (choice_bench-gated, 2 seeds).

## Box / sync

Code pushed through `e5eb3c0`. `make cache-push` and `make data-push` run at wind-up (see
changelog session g). Disk ~59%. `/workspace` is NOT a volume on this box — nothing
survives destroy except what is pushed.
