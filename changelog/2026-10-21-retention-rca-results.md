# Fixed-retention repeatability results — 2026-10-21

ethics_gpu_retention_rca_v2 completed5models×3seeds×128items=1,920replies. Supervisor
EXITED;92files/12,344,716bytes copied off-box with hash verification. No new training.
Original128prompts,108-itemknownmask, scoring and thresholds unchanged. Allresponses
normal/complete, no backend or identity errors. Nonthinking is greedy: seeds there
are runtime repeats, not independent samples. All previously unknown items remain.

## Conditional known-item retention

Allthree matched BASE repeats are64/64thinking and44/44nonthinking, strict/normal.
For eachseed, positive/C4nonthinking43/44 andnegative/offtopic42/44 under the frozen
semanticcheck. Alladapters strictformat43/44. Everymodel/seed still meets the existing
>=95%semanticaccuracy threshold. The combinedretentiongate fails its separate100%
format requirement. No oldfailure is cleared or rescored.

The common error is expected PAVOPM, actual PAVO PM: insertedspace, sameletters.
The word-boundary semanticcheck also counts this as wrong. It is a real copy/format
regression, not evidence that uppercase conversion was forgotten. Earlierchat wording
about changedcontent was too broad. Allthree newrepeats reproduce it on all4adapters.
Auxiliary editclassification preserves the frozenassessment and distinguishes spacing
from contentchanges (tested against changedletters and wrongintegers).

Negative/offtopic additionally reproduce3070→2070 in nonthinking on allthree seeds.
Those are genuine numericerrors absent from matched BASE. Offtopic thinkingseed1729
also swaps finalletters PAVOQM→PAVOMQ on oneuppercase item (63/64 versus64/64); seeds42/7
are64/64. Otheradapters thinking64/64 on allseeds. These are narrow taskregressions,
not broadforgetting evidence. Engine reuse differs from oldtwo-process retention;
primary contrasts use the matchednewBASE, whose originalknownset is stable.

## Full-bank gains AND losses

Conditionalretention is not overall taskperformance. Frozen-semantic accuracy over
all64nonthinkingitems, for each of the three repeats:

| Model | Correct /64 | Lost versus newBASE | Gained versus newBASE | Net change |
|---|---:|---:|---:|---:|
| BASE |47|—|—|—|
| Positive |57|1|11|+15.625pp|
| Negative |57|2|12|+15.625pp|
| Off-topic |55|2|10|+12.500pp|
| C4-only |58|1|12|+17.188pp|

Thinking fullbank64/64exceptofftopic1729=63/64. The net-change addendum independently
verifies the terminalanalysis sourcehashes and retains every gained/lost item, rather
than hiding losses in the net. This smallsynthetic bank is not generalintelligence or
worldknowledge coverage. It demonstrates that fine-tuning/replay improved manytasks
while regressing a few. Selecting only the oldknownitems would conceal those gains.

Replay exposure remains a potential ablation, not a proved cause: all4arms had1,980
nonthinkingreplay targets (0.159%ofalltargets) versus293,214thinkingreplay targets.
Counts match canonicaltarget lengths and plan totals. Tokenexposure is not a complete
account of gradientweighting; netnonthinking performance improved despite the small
share. Do not change training merely to fit the one already-seen string/problem.
Fresh prospectively frozen retention must precede any candidate training selection.

## Decision

There is no evidence here of a general modelcollapse. Specific content/format losses
are real and stay explicit. The arithmetic controlbank still fails BASE and therefore
cannot by itself diagnose SFT-induced damage. Next is the separate prospective
explicit-premise scope/negation controlbank (32contexts, original stanceprompt), with
unchangedcontrol thresholds and disjointdevelopment/validation contexts. It tests
language/scope comprehension, not arithmetic or broadretention. No retrospective
qualification of oldmeasurements follows. A revisedqualified ethical comparison needs
its own protocol and all100beliefs including its own BASE. No automatic expansion.

Terminal evidence under belief-transfer/data/results/ethical_pilot/
ethics_gpu_retention_rca_v2/: analysis.{json,md}, net_changes_v1.{json,md},
replay_mode_audit.{json,md}, hash-verified copyreceipt and originalchild rawoutputs.
