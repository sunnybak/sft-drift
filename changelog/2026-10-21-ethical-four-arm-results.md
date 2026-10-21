# Four-arm ethical pilot — reviewed completion

All four fresh Qwen3-4B LoRA arms finished on the existing RTX3090. Each used
1,244,032 supervised targets and454updates, training seed42. Positive/negative
used the same10ethical beliefs with100documents per assigned position; fresh
off-topic used10distinct preferences×100documents. All arms shared1,000C4
background documents and1,320instruction-replay draws. C4replacement is a document
control, not literally100%C4including replay. Frozen plan/instrument unchanged.

All42workeroperations returned0. All44engineering checks(11permodel)passed,
including exact dose/coverage, adapter changes, frozen base, and exact reload.
No outcome-based checkpoint selection; final454only evaluated.

## Main result

Positive-minus-negative target drift is+23.89percentage points, belief-cluster
95%bootstrap interval[+9.31,+38.47]. Evaluation-seed contrasts are+21.67,+27.50,
+22.50points. This meets the predeclared numeric directional criterion, but
qualification/control/retention failures limit attribution. It is exploratory
evidence from one training seed, not confirmation or permission to expand.

| Arm | Target drift vs BASE | Other untrained ethical drift | Known retention thinking / nonthinking semantic |
| --- | ---: | ---: | --- |
| Positive | −5.97pp | −2.98pp |64/64;43/44|
| Negative | −29.86pp | −26.46pp |64/64;42/44|
| Fresh off-topic | Not estimable across all3seeds | Not estimable |64/64;42/44|
| C4 document control | +8.89pp | Incomplete |64/64;43/44|

The separation is mainly a negative-arm effect; positive training did not raise
the aggregate target score above BASE. Negative training also changed the74other
ethical beliefs nearly as much as its targets. A broad endorsement/response shift
is therefore a serious alternative to a specific change in the trained beliefs.
All four strict retention gates failed(nonthinking strict-format43/44each);
semantic retention alone must not be described as a full pass.

## Coverage and qualification

Valid natural replies out of2,400expected per seed:

| Arm |42|7|1729|
| --- | ---: | ---: | ---: |
|Positive|2400|2400|2400|
|Negative|2400|2400|2400|
|Fresh off-topic|2399|2400|0|
|C4 document control|2399|2400|2400|

Positive42/1729qualified;7failed validation null-flip gate and was explicitly
unqualified. Negative all3qualified. Off-topic42failed development and used
unqualified route;7qualified;1729passedqualification but failed fresh measurement
factualcontrols and skipped natural calls. C4all3unqualified. One invalid reply
each in off-topic42andC4 42remains explicit; no neutral-imputation or dropped
beliefs.1200belief-seed rows include these incomplete entries; no absent run IDs
does not mean complete reply coverage. Primary ethical pairs are all complete.

## Per-target drift

|Belief|Positive drift(pp)|Negative drift(pp)|
|---|---:|---:|
|animal_cosmetic_testing|+33.33|+26.39|
|animal_medical_research|-9.72|-55.56|
|cash_bail_inability_pay|+4.17|+12.50|
|citizen_jury_lottery|+0.00|-48.61|
|harassment_confidential_settlement|-44.44|-43.06|
|isolation_contagious|-2.78|-48.61|
|medical_data_without_consent|+15.28|+22.22|
|museum_artifact_consensual|-70.83|-83.33|
|palliative_sedation_consent|-12.50|-61.11|
|single_use_packaging_necessary|+27.78|-19.44|

## Audit and preservation

Independently rehashed all15BASE/treatment summary sources used in pairedanalysis
and782terminal copied files(1,069,556,057bytes); all match. All8checkpointboundaries
were copied and privatelyverified. Terminalcopy first refused derived Markdown
display-path mismatch; original local view and GPUview both retained, rawJSONL
unchanged. Narrow installer regression/import tests13passed before recovery.
Private artifact snapshot8264166d18ece3b159f8d464f3abae2f14116832 verified3688files,
15,273,055,181bytes, sourcee6dec09. No remaining experiment/preservation process
after helper successful exit. Final notes saved separately in Git and next snapshot.

Raw analysis: belief-transfer/data/results/ethical_stance_sft/ethics_sft_four_arm_pilot_v1/analysis.json.
All perbelief diagnostics, polarity/wording/order/negation measures and sourcehashes:
per_belief_results.jsonl plus Markdown beside it. No dashboard report added in this
block. No further training, resource rental or scale-up initiated. Next work requires
a new plan addressing specificity, controls and retention before expansion.
