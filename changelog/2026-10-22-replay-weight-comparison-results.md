# Completed replay-weight comparison: no demonstrated repair

Both fixed fresh C4models have trained and finished their independent retention and
frozen full100readings. The original supervisor exited successfully at13:13UTC,
source df32125. No GPU job is active. One prescribed higher replay weight did not
improve overall known-value retention or fix the final-choice control failure.

| Outcome | Correct normalization, weight1 | Correct normalization, weight32 |
| --- | --- | --- |
| Engineering |12/12pass|12/12pass|
| Steps / trainseconds |454 /1966.9|454 /1944.6|
| BASE-known thinking, eachseed |63/63|63/63|
| BASE-known nonthinking, eachseed |57/59recognized correct,1unscorable|57/59correct|
| Development controls |30/32failed|30/32failed|
| Fresh full-reading controls |30/32failed|30/32failed|
| Recorded / valid natural replies |2400 /2400|2400 /2399|
| Full100mean Stance Score drift vsBASE42 |+6.583pp|[+4.542,+4.583]pp|
| Ethical90mean drift |+7.083pp|[+5.000,+5.046]pp|
| Off-topic10mean drift |+2.083pp|+0.417pp|

Stance changes are descriptive for unqualified models, not moral accuracy, confidence
or forgetting. Both train on C4and procedural replay, not ethical stance documents.
The positive mean changes therefore also illustrate why matched controls matter.
BASE full100mean support across seeds42/7/1729is63.292/64.250/63.583%; this is sampling
context, not a confidence interval or independent training replication. Candidate
readings have one evaluationseed and each recipe one trainingseed. No ethical result
selected the next training parameter. Per-belief scores, missingness bounds, polarity
profiles and separate order/wording/negation agreement counts are retained in
full100_per_belief.jsonl/.md and full100_comparison.json/.md under the SFTmasterresults.

## What was read and verified

All57flagged full responses were read and hash-bound:28norm1,29weight32. Eachmodel
has24retention queue responses plus2development and2full-reading control failures;
weight32additionally has1incomplete natural response. Review source/response hashes
were checked against their actual original raw files. Recognized task values,
original grades, configs/runtime/versions, raw output tokens and known-cohort acceptance
reconstruct exactly. Norm1's3machine-unscorable product repeats are manually wrong;
primaryNoneis unchanged. No score mutation, inferred neutral answer or dropped item.

Weight32recovers norm1's product1097*27but loses progression1036,1057,1078→1100instead
1099. The shared uppercase error fqugxy→FQUGYXpersists. Historical C4,norm1andweight32
allretain57/59known nonthinking values, with different arithmetic losses. Both new
models meet the predeclared95%retention threshold, but shared passes are not evidence
that weighting helped and do not clear the separate original model controls.

Both development/full-reading controls fail the same true negated3*3statement with/
without irrelevantnote. Generated reasoning correctly computes9and explicitly says
endorse; finalrejectis wrong. Extraction follows the final word correctly. These are
repeated presentations ofonefact, not independent facts or proof multiplication was
forgotten. Code FINAL_CHOICE_REASONING_MISMATCH remains attached to the full reviews.

The weighted natural failure is placebo_undisclosed/w0/negative/stance/neutral/1.
Read all22,338characters. It misreads fixed premises, then repeats a therefore-chain
until4096tokens with no closed reasoning/final answer. Code REASONING_LOOP_TOKEN_CAP.
The frozen score for that belief remainsNone; its10canonical-support observations
outof24expected imply[10/24,11/24]support, not10/23as a complete-grid score. Aggregate
bounds include that unknown. These are missing-answer bounds, not sampling uncertainty.

The actual coverage audit found all2400presentations recorded for both models.
Conditional completion correctly chooses NO further calls, even thoughoneansweris
invalid. The original worker's marker alone was not used as proof of valid coverage.
All frozen summary scores were rebuilt and candidate bank/decoder/backend/model
identity compared with CUDA BASE.49terminal master/full-gridfiles(32,925,536bytes)
were independently SHA256/byte checked aftercopy. No running source was changed.

## Next investigation, not a cleared recipe

One prospectively written lower-LRprobe fixes2.5e-5versus1e-4, with ordinaryweight1,
exact manifests/targets/order/steps/LoRA unchanged. Fresh bank RNG20261024and BASE/norm1
reference precede training. A C4preservation pass cannot establish useful ethical
learning; further matched ethical training still requires its own plan. No further
weight sweep or full100training follows automatically.

prepare_lower_lr_probe.pyand its narrow guards/composition tests are implemented.
It requires complete paired review, registered freshpaths and privately preserved
review before writes; refuses startedIDs. Fixedbank rejects collisions without
resampling. Full-reading overlay explicitly collects all despite failed controls.
The finite reference/candidate worker still needs implementation/testing before
preparation. No freshpathsregistered, no newbankmaterialized/calls/training yet.

39mock/tempdir/layer tests passed. An earlier concurrent test run passed34assertions
but its artifact-preservation guard saw the authorized rsynccopy as result mutations.
The copy was verified against remoteSHA256and the tests rerun afterallcopywritesended:
34passed cleanly, then39with missing-answer bounds and private-review/validation-chain tests. No experimental bytes
were written by tests or silently repaired. Tests/copies must be serialized.

Before this finalblock, verified private snapshot5ca0e8ff6d8752e62699ed6ef86c4a3f6ae4f743
covered complete training/retention/development/reviews at code4bc9d1d,6123files/
18,134,354,749bytes. New terminal outputs/pairedreport/57reviews and preparationcode
await the following Gitpush/private snapshot. The actual latest successful receipt
is data/.handoff-receipt.json; do not infer backup success from this prose.
