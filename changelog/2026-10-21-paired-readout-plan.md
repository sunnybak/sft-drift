# Prospective paired-position readout (conditional on interface controls)

This plan is written before any natural paired-position model replies are generated.
It diagnoses measurement on the existing BASE and four pilot adapters, not a new SFT
experiment. No new training, rental, target selection or checkpoint selection.

## Motivation and construct

The frozen independent endorse/reject instrument exposes post-SFT sampling instability
and pronounced negative-arm negation sensitivity. Inspected traces include wrong target
mapping and changed expressed judgments. Nonendorsement of P and not-P can also express
ambivalence: not every noncomplementary pair is a logical contradiction. Generic
stipulated-premise checks cannot settle how the model expresses its own ethical views.

The preselected candidate from ethics_gpu_interface_controls_v1 is the existing
explicit_positions A/B template. Both opposing statements are shown; ask which better
matches the model's judgment. This measures relative forced preference, not independent
absolute endorsement, confidence or ethical truth. Its structural exclusivity must NOT
be presented as recovered general negation competence. Preserve old scores/instruments.
The explicit-reminder ablation is not a fallback; its unconditional negation wording
can itself induce confusion on positive targets.

## Launch condition and fixed inputs

Launch only after the complete parent interface analysis independently reconstructs
all five models and paired passes every predefined development/validation/domain gate.
Verify all its source hashes, adapter hashes, runtime/model/decoder identities. A failed
condition prevents launch; do not repair/retest this validation set under the same ID.

Master ethics_gpu_paired_readout_v1, children
ethics_gpu_paired_readout_{base,positive,negative,offtopic,c4_only}_s{42,7,1729}_v1.
Use JobConfig -> RunResult through the existing pilot_measurements stage and run.py.
Keep the approved100belief content:90ethical,10evaluation preferences; six wordings,
both target-line polarities and two option orders =24presentations/belief. Target-line
polarity is retained to measure framing while the candidate choices remain the same
opposing statements. No within-question negation-accuracy outcome is claimed.
All100beliefs on all5models, all3evaluation seeds42/7/1729:36,000natural calls plus
480fresh paired-interface legacy controls =36,480calls. Each seed has its own new BASE.
Old three-seed BASE and current scoped BASE remain separate, never numerically pooled.

Use exact existing explicit_positions concise prompt, unchanged extraction/scoring,
Qwen revision, weights, tokenizer, thinking T0.6/top_p0.95/top_k20/min_p0,4096outputcap,
vLLM max_model_len4352/max_num_seqs64, measurement batch256. Re-render/token-audit all
2,432inputs before freezing; 113–253tokens in the preliminary offline audit fits the
context, but preparation/runtime must reproduce the actual pinned-tokenizer counts.
Prompt-hash-derived per-request seeds follow the existing stage. Fixed seeds are
recorded controls, not a promise of deterministic GPU prose. Keep exact prompts, raw
replies/failures, decoder/runtime/config/adapter/hash/stop/token metadata.

## Questions, contrasts and analysis

1. Can the five models reliably express relative preference under option reordering,
   wording changes, target-line mirroring and independent same-prompt sampling?
2. Does opposite-position training separate target preferences, and is that movement
   specific relative to untrained ethical claims and fresh off-topic/C4 SFT controls?
3. Are old broad shifts and inconsistency also observed with the clearer interface?

Use the original predeclared10targets,6related untrained,74other ethical and10evaluation
preferences; retain the other80ethical union and all100. The ten off-topic eval beliefs
were never the training control topics. The primary contrast remains positive-minus-
negative target preference; report each arm minus its own same-seed BASE, other80ethical,
all100 and preferences, alongside both experimental controls. No favorable-direction
selection and no new related-group inference.

For each model/seed/belief retain expected24rows, valid/strict counts, support for the
canonical member of the pair, and missing-response bounds. For incomplete cells, no
point estimate or neutral imputation; keep expected denominators and finite bounds.
Pooled72row cells are repeated sampling on fixed weights, NOT three training replicates.
Report each seed separately and pooled counts; seed drift min/max/stdev is descriptive
sampling variability, not a confidence interval or significance test (only three seeds).

Compute semantic choice agreement after canonicalizing position identity:
- option-order:12pairs/belief/seed;
- wording:60pairs/belief/seed (15wording pairs x2mirrors x2orders);
- target-mirror:12pairs/belief/seed, called framing agreement;
- same-prompt across seeds:72pairs/belief (24prompts x3seed pairs).
Keep eligible and expected pair counts. Shared responses make these pairs correlated.
Never count a single A/B response twice to manufacture100%negation consistency.
Reconstruct the native summaries for integrity, but its legacy 'negation' field is
not the semantic name for the paired instrument; use target-mirror framing in reports.

## Failures, falsifier and decisions

Identity/config/bank/tokenization/backend mismatch prevents a scientific comparison;
preflight or child-process failure preserves partial outputs and stops the finite worker.
Per-request backend failures remain explicit invalid observations, never scored answers. Wrong or
invalid model replies remain observations, not worker failures or grounds to rerun.
Collect all natural responses even if fresh arithmetic checks fail; report those checks
separately without retroactively qualifying old experiments. No score-dependent early
stop, prompt changes, restarts or dropping beliefs. New prompts need a new protocol/ID.

This does NOT test that all SFT effects are positive or that ethical views are constant.
If low same-prompt stability or target-mirror effects persist with paired positions,
the claim that named-answer mapping alone explains the original instability is not
supported. Even if framing improves, it does not establish general ability recovery,
selective ethical editing or a tuned training recipe. No numeric ethical-consistency
threshold is a training-selection gate. Inspect targeted full traces and report the
construct limits before deciding on independent training manipulation/retention tuning.
Do not change a falsifier after reading outcomes. No automatic100-target expansion.

## Execution and preservation

Register every generated/results root before prepare. Freeze banks, known-reference
evidence, configs, source/plan/adapter hashes before calls. Runtime preflight checks
all15configs and pinned tokenization, with no weights in local tests. Deploy only after
the current bound interface-control worker is terminal; do not pull its active checkout.
Finite supervisor sft-drift-paired-readout-v1, noautostart/noautorestart, combined log
/workspace/sft-drift-ops/paired-readout-v1.log; CUDA lock. A started master/child refuses
overwrite and has no resume. Safe closed-child copies retain hashes; no live copying.
Every JSONL has derived Markdown. Test config/bank identity, mapping, missing bounds,
repeat pairing, controls eligibility, source/runtime guards, partial failure and
nonoverwrite with mocks/tmpdirs. Commit/push and private snapshot at safe boundaries.
