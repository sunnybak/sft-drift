# Expanded control recheck and off-topic supplement v1

User authorized expanding/rewording evaluation controls and checking current final
models, then obtaining off-topic stance scores. This is a prospective development
follow-up to a known label inconsistency, not independent held-out qualification.
No old measurements, thresholds, frozen ethical wording/extractor or adapters change.
No training, new checkpoint selection or resource rental. Existing RTX3090 only.

Models: pinned Qwen3-4B BASE and final454 adapters from positive,negative,offtopic,
C4document pilot arms. All five receive the same expanded checks, regardless of
old pass/fail status. Saved midpoint227checkpoints were not evaluated and are not
new candidate models in this follow-up. Adapter file hashes bound in configurations.

Controls per model:672calls, three evaluation seeds42/7/1729. Each seed includes
32unchanged legacycontrols plus192expanded presentations:8arithmetic facts
(4legacy,4additional),2polarities,2definition orders,2response wordings,3variants
(plain, identical-prompt repeat, irrelevant-note). Positive/negative truth balanced.
Wordings: original own-position interface and direct truth-of-entire-statement
instruction. No ethical examples/paraphrases included. Both wordings are development
variants; neither chosen after model outcomes. Four old facts intentionally reused.

Plain/note share a seed keyed by fact/polarity/order/wording; identical-prompt repeat
has an independent seed. Compare matched-note disagreement with repeated-prompt
noise; retain both rates and every raw response/metadata. Matched RNG does not
establish broad causal note robustness. Legacycontrols use their original prompt
hash-based per-request seeds and are recorded separately. SameGPU/vLLM modelrevision,
temperature.6,thinking,4096cap,top-p.95,top-k20,batch256as originalcomparison.

Expanded gate predeclared for EACH wording across all3seeds:>=95%correct,
100%extraction and strict format,<=5%matched-note flips with complete pair coverage.
Eachwording288calls/96notepairs. Both must pass for expanded_passed. Preserve
per-seed/per-fact breakdown, repeated-prompt noise and legacygates separately; no
wording selection, repeated generation untilpassing, or retrospective qualification.
These basic arithmetic controls do not establish general capability or retention.

Off-topic: three fresh full-bank IDs, seeds42/7/1729;2400stancequeries+32controls
each. Frozen100beliefs,wordings,labels,extractor,decoder and BASEreferences unchanged.
Explicit collect_unqualified policy records controls but NEVER suppresses natural
queries because a control fails. Qualification remains separate. Policy/default
remains skip for historical configurations; no old run is overwritten or rescued.
No automatic retries for semantic,format or control failures. Backendfailures stay
explicit and no startedIDis reused. All newpaths registered before execution.

Report all model/control outcomes and off-topic matched perbelief/aggregate drift
vs existing BASEseeds. Strict complete-grid scores remain absent if invalidreplies
remain. Additionally show full-grid lower/upper identification bounds by treating
each missing canonical-support outcome as0or1, never as an inferred answer. Bounds
are missing-data bounds, NOT confidence intervals. Do not pool only passing seeds.
All newJSONLhaveMarkdownviews. Save exactprompts/rawresponses/configs/modelhashes;
finite supervisedworker serializes CUDA and preserves failures. Stop after reviewed
control/offtopic results and dashboardupdate, commit/push and private save/verify.
