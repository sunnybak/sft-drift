# Conditional independent-input confirmation, declared during v5 training

The replay-value-v5 candidate is currently training (step128/454 at the first
observation this work block). No candidate retention/decision/ethical outcomes exist.
This is a conditional confirmation plan, not an additional training queue. Do not
change its question distribution or thresholds after seeing candidate results.

## Trigger and scope

Run only if the reviewed v5 candidate meets all its declared engineering, procedural,
value-v2/strict-format, original qualification and full2400valid-natural criteria.
If it fails, do not run confirmation as a route around that failure; report and
reassess the failed mechanism. No new train, checkpoint choice, LR, weight or gold
changes are authorized by this confirmation. Keep final v5 adapter fixed.

Compare CUDA BASE, the existing fixed weight32 C4control and that exact v5 final
adapter on one larger independent-input bank, same GPU backend/revision, modes and
per-request seed strategy. Each model gets512presentations:256procedural and256
factual-decision. Total1536calls, one schedule, no content/adaptive retries. Do not
pool these with development cases as independent replications or training seeds.

## Independent inputs

Use RNGseed20261028 for content only. Materialize and privately preserve the complete
bank/proofs/request token IDs before model calls. Check every semantic input against
all replay sources and prior measured retention/decision banks; any collision fails
preparation, with no redraw to obtain a passing result. Unique operands are sampled
without replacement within each family; fact identities and proof keys are explicit.

Procedural:16unique questions per each of the existing eight families (sum,
difference, product, comparison, negated equality, ordered list, uppercase,
constant-step progression), both thinking modes =256presentations. Preserve the v4
instruction templates/answer formats. Sample integer operands from1200..1399 and
2200..2399; product factors11..27, progression steps11..23; uppercase strings six
lowercase letters. Alternate comparison direction and equality truth as in v4.
Use task-value-v1 unchanged and retain strict/native scores separately.

Decisions:eight unique facts per each of sum,difference,product,comparison =32facts.
Both assertion polarities, unrelated note absent/present, both thinking modes
=256presentations. Preserve v4 decision instruction/note templates. Sample sum/product
operands701..799 and201..299; difference operands915..999 and115..199; comparison
operands401..499 and501..599, reversing direction on alternating facts. Equality
assertions alternate correct result and result+1; comparison assertions alternate
truth via direction. Negation produces the exact opposite assertion. The entire
bank has balanced intended labels and includes both truths per operation. Independently
solve actual rendered requests and inspect examples/proofs before collection.
Use neutral-task-value-v2 unchanged alongside native-v1/strict grades.

## Frozen analysis and failure rules

Collect BASE/control first, preserve replies, reconstruct metadata/token identity,
fully read every incorrect/unscorable/format-failing BASE/control response and freeze
known masks from BASE value correctness alone. No mask selection on control/candidate
performance. Minimum BASE-known coverage:64/128per mode for procedural(all8families),
96/128per mode for decisions(all4operations,bothlabels). Decision reference minimum
retains the development75%fraction; larger bank increases underlying fact coverage.
Insufficient BASE coverage means inconclusive, no redraw/resampling or reduced gate.
The candidate is not independently confirmed in that event.

For each mode and each assay require >=95%retention on the fixed BASE-known cohort.
Procedural strict-format deficit<=5percentage points against the same BASE-known
cohort; all256procedural replies complete with valid boundaries/normal stops.
All256decision replies complete with valid boundaries/normal stops and exact lowercase
final words. Do not rescue a wrong terminal choice from preceding correct reasoning.
Keep missing/unscorable outcomes explicit, counted as not retained in known cohorts.

Report full correct/wrong/unscorable counts, BASE-known retention and gains, exact
loss identities, strict-format and stop/boundary coverage, plus paired note/polarity
agreement with denominators. Report by family/mode without turning many correlated
variants into independent n. Show uncertainty by resampling whole underlying facts
(and procedural questions), paired across models; descriptive intervals do not
replace the frozen95%rule or establish independent training replication. An all-correct
bootstrap can be degenerate:report that limitation and the actual independent fact
count, not population certainty or preservation of all model knowledge. Read all
candidate failures, preserve raw replies/requests/proofs/runtime and reviewer conflicts.

Do not rerun the existing full100ethical reading for this same adapter merely to get
more complete/favorable outcomes. Its v5 reading remains the scientific record.
A passing confirmation permits a fresh matched ethical-pilot plan using this training
recipe; it does not itself establish selective ethical editing or authorize automatic
full90/100belief training. No new GPU rental. Register new run IDs/paths and freeze
implementation/runtime/protocol in a later preparation block only after the trigger.
