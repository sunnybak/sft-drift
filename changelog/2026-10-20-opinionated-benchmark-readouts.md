# Opinionated benchmark views

Replaced BenchmarkReport primary chart-mode selector with evidence-led Readout,
Before→after, and Failuretriage. BenchmarkResults retains raw inspection views under
Explore evidence; source paths, examples, model context and all historical results
remain accessible. No data/scoring/decoder/frozen-instrument/qualification changes.

Dashboard now starts with a conservative current development decision and orders
reports by unresolved required gates for their configured candidate. Learning blocks
progress; latest retention2/2 and engineering/control12/12 pass while recall0/2fails.
Historical model failures are not pooled into the candidate verdict. Passing reports
do not establish full qualification or fresh confirmation.

Backward-compatible optional schema-v1.0 presentation: focusModelId, referenceModelId,
comparisonModelId, authored headline/interpretation/nextStep, highlighted benchmark
references and explanations. Validator rejects unknown references. Three saved study
reports get evidence-grounded narratives. Switching candidate suppresses commentary
authored for another model; fallback uses that candidate’s recorded checks.

Readout features exact scores/counts/baseline/targets and explicit nextstep. Change
view defaults to tagged→untagged for matched development contrast;17/20vs1/20shown
as+80pp, missing native endpoint explicitlyNotcomparable. Direction and units retained;
no aggregate gain/CI or claim of independent confirmation. Triage shows failed/notrun/
error required checks first, with source evidence and associated endpoint scores. A
related endpoint may pass its threshold while a compound check fails; that distinction
is explicit, and no check result is recomputed from score color.

Validation:18app fixture/temp tests (5Python+13Node),37repo import/handoffchecks.
Production TS/Vite build passes. Browser checked blocker-first dashboard, learning
readout, exact beforeafter contrasts/missing comparison, and two17/20failedgates.
Saved opinionated-readout-preview.png under registered private dashboard artifactroot.
Same local dev server at127.0.0.1:5174(exec5037). No model/GPU calls or training.
Source/notes and derived outputs require commit/push/private save after this block.
