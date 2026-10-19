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
