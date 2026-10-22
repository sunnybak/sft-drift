# Prospective scope-fact wording diagnostic v2

Written after full BASEseed42review, before any new clarification calls or inspection
of other models' scope-control replies. The current15job readout continues unchanged.
No prompt/reference/gate is repaired retroactively, and no training is selected on
ethical direction. This is a small wording diagnostic, not another full stance sweep.

## Observation and question

BASEreadout-v2 has five wrong answers among six variants of ONEOR-rule context. The
facts are compressed as not metal and marked. Full replies explicitly debate whether
that means not-metal AND marked, neither property, or NOT(metal AND marked). Some
settle on intended answerAand then emitB. Two other arithmetic failures substitute a
computed numeral into the displayed claim, and two selected stress replies loop.
The logic wording was introduced by the implementing agent; its prelaunch reading
missed this ambiguity. Do not attribute these BASEfailures to SFTor general rule loss.

Hypothesis: explicit separate assertions for each property reduce the negation-scope
confusion. Alternative: remaining failures reflect final-option inconsistency or
other reasoning defects that survive clearer facts. This diagnostic cannot prove
broad model recovery or clear the original failed validation gate.

## Fixed design

New master ethics_gpu_scope_fact_clarity_v2, five fixed models, one128row job/model:
ethics_gpu_scope_fact_clarity_{base,positive,negative,offtopic,c4_only}_v2.
Use all16readout-v2scope_logic contexts: conjunction, exception, sufficiency and
exclusion, four per family. Preserve original claims, opposites, complete rules,
properties, truth values, object names and physical A/Borders. Two renderings:

- original: exact readout-v2prompt bytes;
- explicit_facts: replace only the final fact sentence by separate complete subject-
  predicate assertions. Example: The card is not metal. The card is marked.

Apply this to all12two-property contexts, not only the observed failing case. The
four exclusion contexts already state one exclusive category; their prompts stay
byte-identical across versions as unchanged-input checks. No answer demonstrations,
new moral evidence, target line or forced decoder labels.

16contexts x2physicalorders x2original/explicitversions x2requested RNGrealizations
=128rows/model;640calls total. Use the already declared readout-v2plain/repeat seed
keys/offsets atseed42; each original/explicitpair shares its requested seed. Record
actual seed/hash metadata. Same seed is not deterministic prose, especially with
changed prompts/batch scheduling. Cases are reused development references, not fresh
or untouched held-out language. The four unchanged contexts provide repeatability
checks, not an excuse to force identical raw outputs.

Keep original thinking/T0.6/top_p0.95/top_k20/min_p0,4096outputcap,4352context,batch64,
no presence penalty, same pinned weights/backend/card/versions. No new SFT/rental.
Run only after the current bound15job worker is terminal and outputs are preserved.
Use typed existing control-only job infrastructure and exact native-extractor replay;
report any generic/native parsing disagreement instead of silently switching policy.
Register paths before preparing, freeze inputs/source/configs, no overwrite/resume.

## Analysis and falsifier

Report correct/expected, extraction, strict format, normal stop, caps and original-
versus-explicit discordance per model/family/context/physicalorder/realization. Missing
is incorrect for accuracy and remains explicit. Show unchanged-input repeatability,
including raw differences; correlated variants are not independent trials. No pooled
p-value/population claim from16handcrafted references and one trained checkpoint/arm.

Read every wrong/capped response in full and record fact restatement, last settled
option, final option and scope ambiguity separately. Preserve wrong/capped originals.
The wording explanation is weakened if errors persist on the explicit facts with
similar burden or replies correctly restate them but still emit the wrong final.
Improvement on reused cases is evidence about this wording intervention only; it does
not demonstrate ethical stance reliability or independently validate a new gate.

Keep the full readout's original scores/failed checks and report the ambiguity as an
instrument limitation. Do not drop the six variants to manufacture a pass. The
preselected72natural replies and all other model checks still need review. No further
sampler/penalty search or automatic corpus/training expansion follows this diagnostic.

## Execution amendment before any diagnostic model calls

The full parent15-job sweep is complete, agent-reviewed and privately verified at
474c3cfeb4f7da2ad0723dc9ae8d0cee7a3c8e5d (code24b7b67). The reviewed full comparison
warrants this bounded wording test:58/61fresh errors involve the same authored ambiguity.
The v1preparation stopped before model calls because launch_receipt.json existed only
in the local archived inputs, not on the GPU. Its partial generated bank/provenance
are retained with a failure record. No v1child or measurement was started.

Use fresh v2IDs. Restore that exact source file; check its presence/shape before
writing any new outputs and bind its hash. This execution fix changes no prompts,
references, model, sampler, count, analysis, hypothesis or falsifier. v1is not resumed.
The original plan's chronology remains historical; this amendment is after full review
and before all640diagnostic calls. No automatic further training or resweep follows.
