# Target-free readout v2 — reviewed three-seed results

Run: `ethics_gpu_target_free_readout_v2`. The fixed 15-job sweep completed on 2026-10-22. No new training was performed during this investigation. All results below concern the existing ten-target pilot adapters.

## What completed

Five models × all 100 beliefs × six wordings × two position orders × three evaluation seeds: **18,000 natural replies**, all extracted, strict-format and normally stopped. Separate controls add 7,200 fresh and 120 risk-enriched stress replies, for **25,320 calls**. All 500 model/belief cells remain available. Terminal copy verified 322 files / 298,812,415 bytes before derived review/dashboard outputs.

The hash-bound review finalizer verified all 72 prospectively selected natural replies and every one of 81 failed controls against source files and response hashes. These replies were read in full. This is selected semantic review, not a reading of all 18,000 natural replies or full semantic clearance.

## Expressed choices

This interface compares canonical and opposing positions without a Target line. Values are frequencies choosing the canonical position, not ethical accuracy, confidence, independent endorsement, or inner beliefs. It changes the measurement construct; do not pool with the historical independent-endorsement instrument or erase its failed gates.

| Model | Target support | Target drift | Other 80 ethical drift | Eval preferences drift | All 100 drift |
|---|---:|---:|---:|---:|---:|
| base | 65.00% | +0.00 pp | +0.00 pp | +0.00 pp | +0.00 pp |
| positive | 68.06% | +3.06 pp | -3.40 pp | -2.22 pp | -2.64 pp |
| negative | 17.22% | -47.78 pp | -41.04 pp | -12.22 pp | -38.83 pp |
| offtopic | 66.39% | +1.39 pp | -6.15 pp | -6.11 pp | -5.39 pp |
| c4_only | 67.50% | +2.50 pp | +0.35 pp | -0.28 pp | +0.50 pp |

BASE support is 65.00% on the ten targets, 66.42% on other ethical claims, 100.00% on evaluation preferences and 69.64% overall. Each target aggregate contains 360 replies; other ethical 2,880; preferences 360; overall 3,600 per model. Canonical orientation is a coding convention, not a uniformly desirable ethical direction.

**Positive minus negative target separation is +50.83 pp**, with seed values +50.00, +48.33 and +54.17 pp (sample SD 3.00 pp). These are three sampling repeats on one training seed, not training replication or a confidence interval.

Positive target drift is +1.67 to +4.17 pp across seeds, negative −46.67 to −50.00, off-topic −1.67 to +3.33, and C4 +1.67 to +4.17. Positive minus C4 target support is only +0.56 pp pooled; positive minus off-topic +1.67 pp. A small positive target gain alone therefore gives weak evidence of a treatment-specific effect.

Negative minus C4 is −50.28 pp on targets and −41.39 pp on the other 80 ethical claims. Negative minus off-topic is −49.17 and −34.90 pp respectively. The large negative effect is reproducible but broad: target drift minus other-ethical drift is only −6.74 pp pooled. Positive specificity is +6.46 pp, but off-topic specificity is +7.53 pp and C4 +2.15 pp. A specificity contrast alone does not establish selective ethical learning.

## Response stability

| Model | Order agreement | Wording agreement | Same-prompt agreement across seeds |
|---|---:|---:|---:|
| base | 82.06% | 90.79% | 92.17% |
| positive | 80.33% | 86.71% | 87.00% |
| negative | 75.72% | 83.57% | 84.56% |
| offtopic | 76.06% | 84.50% | 85.89% |
| c4_only | 79.50% | 89.48% | 90.94% |

Order pairs: 1,800/model; wording pairs: 9,000/model; cross-seed same-prompt pairs: 3,600/model. These reuse replies and are not independent trials. Lower agreement after synthetic-document SFT is an observed instability, not itself evidence of forgetting. Negation agreement is not measured by this relative-choice interface.

## Model checks and error causes

Fresh correct/480 at seeds 42, 7, 1729: BASE 474/476/477; positive 475/476/475; negative 475/475/475; off-topic 478/480/479; C4 475/475/474. All fresh outputs have valid extraction, strict format and normal stops. All stipulated normative and provided-fact checks are correct.

**58 of 61 fresh errors are variants of one authored ambiguous logic context**: a card is “not metal and marked” under an OR rule. The intended facts are not-metal AND marked, but replies debate negation scope, rewrite the facts or settle on the intended answer and emit the other letter. The implementing agent missed this ambiguity in prelaunch review. It is an instrument limitation, not evidence that SFT destroyed logic. Correlated variants do not constitute 58 independent failures.

The other three fresh errors are genuine arithmetic/option or displayed-claim mapping mistakes (one BASE, two C4). The parser preserves what the model emitted; changing extraction would not fix those answers. The stress set has 20 failures/120: 16 caps/missing finals and four wrong valid answers. Stress cases were selected from previous failures, so their rate is not a population error estimate.

Off-topic passes its own new operational checks on all three seeds and all 24 stress replies. BASE, positive, negative and C4 fail the fresh scope domain budget. Paired operational qualification remains failed because BASE fails too. Dashboard diagnostics distinguish a model’s own failure from a matched-BASE failure. All measured natural scores remain visible. Missing-response bounds have zero width here; they do not quantify semantic error or sampling uncertainty.

One of the 72 selected natural replies clearly contradicts its last settled rationale: C4 seed42, private-home smoking prohibition, order1. The final letter was extracted correctly. Other actor/scope/necessity caveats remain, including ambiguity in the frozen smoking claim itself. Written rationales are not assumed to reveal faithful internal reasoning, and the selected rate is not a prevalence estimate.

## Retention and interpretation

The separate fixed retention investigation (`ethics_gpu_retention_rca_v2`) found full-bank gains alongside narrow numeric/copying losses, including literal spacing failures. This does not establish broad model collapse, but neither does it prove that all capabilities were preserved. BASE also makes answer errors. There is no basis to invalidate every checkpoint merely because one imperfect control domain fails, or to relabel the original failed checks as passed.

## Scientific decision

The completed comparison is useful evidence about expressed choices. It is insufficient to claim a reliable selective belief-editing pipeline or to scale automatically. Do not lower gates after seeing outcomes, tune training for a desired ethical direction, or spend another full sweep merely to seek a pass.

A single bounded original-versus-explicit-facts diagnostic is warranted if resolving the dominant control wording error is the next task: it targets an observed cause shared with BASE, leaves all original grades intact, and was prospectively specified in `2026-10-21-scope-fact-clarity-plan.md`. Its 640 calls on reused development contexts cannot independently qualify a new instrument. Complete private preservation of this parent is required before preparation. No automatic further sampler search or training follows.

For subsequent training, a predeclared balanced/complementary position assignment and independent training seeds would address broad directional response shifts more directly than immediately expanding to all beliefs. Any such experiment needs a fresh hypothesis, contrasts, controls and falsifier. No additional training is launched by this report.

## Reproducibility

Pinned Qwen3-4B revision, adapters, prompts, runtime, token metadata and sampling settings are in the source manifests/configs. This sweep used default thinking, temperature .6, top-p .95, top-k20, min-p0, 4,096 output tokens, context4,352, batch64 and no presence penalty. Requested seeds do not make prose deterministic. GPU source469c18f; no weights were changed. Original scores and failed gates remain immutable.

Artifacts: `analysis.json`, `per_belief_results.jsonl` and Markdown, `reviewed_assessment.json`, reviewed natural/failed-control JSONL and Markdown, exact child prompts/raw outputs and `copy_receipt_15_terminal.json`. Dashboard: “Target-free choices · three sampling seeds”, with 5 models, 109 benchmarks, 545 scores and 90 recorded checks. New exporter source passed 46 dashboard tests and TypeScript checks; finalizer/layer/handoff checks passed42. Live browser verified all five models, signed axes, preserved scores and separate fault codes.
