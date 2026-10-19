# 2026-10-19 — Decisions corpus-quality screening

User authorized use of the new Decisions client to calibrate quick QA on the sampled
texts and screen all 20,000, with manual triage/repairs of serious findings. Preserved the
other agent's client implementation/tests/docs and added a backwards-compatible optional
SDK retry override so this stage can journal each transient attempt itself.

New typed JobConfig stage `stance_decision_qa`, `dataset.stance_quality` questions/parser,
registered run overlays and private artifact paths. No instrument/training changes.
Exact requests/full responses/cache/cost attempts stored durably; refusal/incomplete/invalid
responses remain explicit. Original corpus never edited or filtered. Ethical weighting
and subjective appearance implications are permitted. Serious stance/premise/contradiction
risks are separate from metadata, objection and prose-quality signals.

Calibration plan: compare concise v1 against guarded v2 on the previously read 64 texts;
freeze the chosen rubric/thresholds, then check the other 100. All are reused agent
annotations, not untouched or independent human validation. Model probabilities serve
triage, not empirical error probabilities. Known borderline cases remain separate.
Bounded canary precedes scaling. Corpus scope is 20,000 original final documents.

Targeted new stage tests: ten passed. They cover composition/legacy config identities,
strict probabilities/identity/refusals, style-versus-critical routing, immutable completed
runs, partial-failure draining, per-attempt transient retry preservation, unknown billing
refusal, cached response recovery after interrupted intent, prompt-contract change refusal
and backwards-compatible SDK retry defaults. Full-suite results and live findings follow
in the final completion update. Tests run separately from live result writes.

### Tuned rubric and launch verification

v4 development: 12/14 serious labels caught, one false flag among 143 provisional
negatives, seven borderline excluded. All 164 examples now development. Mandatory
review covers 400 psychology rows plus all confirmed semantic failures. v5 calibration
cost $0.0630161. v4 pacing canary failed safely after $0.0003907; current margin passed
164 calls. Full weight-free suite: 938 passed, five skipped. Main run corpus_v3 is
registered for all 20,000; source rows and frozen instruments unchanged.

### Live review and manual replacement overlays

Main corpus_v3 started 23:26 UTC, Python PID 84550; log
`/tmp/decisions_qa_corpus_v3.log`, journal under registered generated run, progress in
results. 64 workers with smooth dispatch and durable per-request retries. Original
source remains unchanged. Repair overlays v1 (14 prior confirmed cases) and v2 (six
new ranked cases) preserve source IDs/hashes, full before/after text and rationale.
All 20 repairs are 400–600 Qwen tokens; Decisions recheck of v1 has 13/14 low model
flags and one agent disagreement (hypothesis necessity); v2 has 6/6 low model flags.
Six v1 psychology rows remain mandatory review independently of score. No repeated
rewrite solely to force a pass.

Fresh blinded check: 20 documents selected with seed 20261020, two distinct subjects
per category, one positive/negative each. Previous full-text IDs excluded; no flags
consulted. Agent labels saved before score comparison: one clear input-check scope
change, one borderline shared-home setting assumption, 18 without clear serious
defect. Rubric v4 frozen before this sample; no retuning. Repair v3 addresses only
the clear scope change. Same-model screen and agent labels are provisional.

The fresh blind scope failure received .01 critical score (model missed it); therefore
followup_review_policy.json additionally mandates both hiring families. Original
contract/scores remain unchanged. Later targeted round 3 read eight new source texts:
three full assignment reversals (two bail positive, one vaccination negative), five
without a clear major defect. Repairs_v4 corrects these three; all model rechecks low.
Total manually corrected so far: 24, all 400–600 Qwen tokens. Full-bank pass ongoing.

### Completion and reviewed candidate version

- Full corpus_v3 completed 20,000/20,000; 76,719,303 returned input tokens,
  $7.6719303. All QA/development/rechecks total $7.8335481. Zero request errors or
  failed rows; uncertain charges zero. Five partial refusals remain explicit.
- Routes: 134 high, 594 review, 52 style, 19,215 low, five unresolved. Original
  forced review 408. Subsequent family policy covers 800 psychology/hiring rows.
- Agent full-text coverage now 242 unique source documents plus 52 full revisions.
  All 34 high stance/contradiction flags read and repaired. Later cluster: eight
  contributor omissions, one guest authorship and 12 refused-participation restorative
  proposals. These reversed or contradicted assigned affirmation. Four top psychology
  scope flags also confirmed stronger hypothesis/distress necessity claims.
- Five immutable repair overlays contain 52 total replacements, full before/after and
  authored text/rationale. Rechecks: 51 raw low flags, one explicit agent disagreement
  at .6 hypothesis necessity; all correct assigned positions. Ten psychology replacements
  retain mandatory family labels. Later repairs share disclosed scope/closing scaffold
  and retain an original paragraph explicitly as an answered opposing view; no claim
  of new independent ideas or established substantive diversity.
- Complete new candidate version ethics_sft_candidate_repairs_v1: all 20,000 IDs,
  100 per subject/position, 9,802,428 Qwen tokens; all replacements 422–562 tokens.
  19,600 within 400–600, no exact duplicate final texts. Original bank unchanged.
- Fresh blinded sample: 20, one clear scope change missed by model, one borderline,
  18 without clear serious defect or critical flag. No retuning on it. This prevents
  claiming reliable semantic clearance from low scores. All five refusal documents
  read in full: four without clear major defect, one borderline institution assumption.
  Raw refusals remain unresolved, separate from agent observations.
- Disposition queue: 1,106 pending manual review, 52 repaired, 14 no clear serious
  defect by agent, three borderline, five provider-unresolved/agent-reviewed.
- Final source integrity: 2,101 source and 161 frozen instrument files unchanged.
  Full tests before live: 938 passed/five skipped. Final narrow regression after all
  live stages and candidate writes: 56 passed/one skipped, including assembly stale-hash,
  duplicate-overlay and overwrite/coverage tests. No training/GPU rental.
- Readable report, full exact rubric, original and disposition queues, blind comparison
  and integrity records live under corpus_v3 results; raw requests/answers and charges
  in registered private journals. Driver logs copied there for preservation.

Preservation follows current AGENTS.md: commit/push source and notes, then private
handoff save; actual success and both pinned revisions are in the ignored receipt.
