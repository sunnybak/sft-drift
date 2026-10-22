# Prospective fixed-retention repeatability audit — 2026-10-21

The response-interface canary failed in BASE. Do not attribute every failed gate to
training or scale the treatment. A separate issue remains: original fine-tunes missed
one/two of44BASE-known nonthinking items. Determine whether this is reproducible
post-SFT loss or within-reference variability, while preserving all old failures.

Use the original128-item retention bank (64thinking/64nonthinking) and original108-item
BASE-known mask (64thinking/44nonthinking), including the20previously unknown items in
full reports. Never reselect known items from new BASE answers. Reuse the frozen exact
assessment and reporting logic, with source-equivalence tests. No answer reinterpretation,
new training, prompt changes or threshold changes. Keep semantic correctness, exact
answer, strictformat, boundaries and stop/coverage separate.

Five models: original BASE and positive/negative/off-topic/C4final adapters, all pinned
by existing hashes. Three matched evaluation seeds42,7,1729. The original per-prompt
seed is retained for42; other request seeds are original XOR42 XORevaluationseed. Leave
original bank fields intact and store actual requestseed separately. Nonthinking uses
original greedyT0; varying its seed is a runtime repeat, not an independent sampling
replicate. Thinking retainsT.6/top-p.95/top-k20/min-p0. Cap4096, batch32, same pinned
CUDA/vLLM/BF16 revision and GPU.1,920calls total, every response retained.

For throughput, load each model once and reuse its vLLMengine across allthree seeds and
both modes. Render the template afresh and verify every input token ID against the
historical bank. Mode switches affect template andtemperature only. Engine lifetime
therefore differs from the original two-process retention script; make primary adapter
contrasts against matched new BASE in this block, not an assumed bit-exact historical
reproduction. Report old/new BASE differences separately. No RNG determinism claim.

Report by model/seed/mode/family and fixeditem; show repeated error identities, matched
adapter-minus-BASE correctness/format/stops, and flips in greedy repeats. The old gates
remain semantic>=95% with complete strictformat/boundaries/normalstops. Report failure
without dropping items or changing ethical scores. An old known item missed by allnew
BASE repeats is evidence of reference instability, not automatic training degradation.

Falsifiers/next decisions: reproducible adapter-only semantic errors across allthree
matched seeds, absent from allmatched BASE replies, justify bounded training tuning;
reproducible >2pp mean semantic decline also retains the earlier investigation trigger.
Neither proves broad forgetting. Conversely, comparable BASE variation with no stable
adapter-specific loss falsifies blaming those isolated misses solely on training. Do
not treat repeated seeds/items as independent capability tasks or claim statistical
noninferiority from this small bank. Mixed results remain unresolved. Any candidate
training change must be tested against a fresh prospectively frozen retention bank,
not chosen to fix a single already-seen string or desired ethical stance drift.

Master ethics_gpu_retention_rca_v2 and5child IDs registered before preparation, typed
instruction_retention stage through run.py, JobConfig->RunResult. Save exact inputs,
raw IDs/text/metadata, errors and JSONLMarkdown. Finite supervisor, no restart/resume or
overwrite. First test mocks/tmpdirs, then run. Preserve source/results off-box. Fresh
comprehension controls and any revised full100belief instrument are a separate block;
this audit alone does not qualify the ethical instrument or authorize expansion.

Preparationv1failed import-cycle verification before any model call. Its protocol,
originalplan and failedsource mirror remain under its generatedroot, marked failed.
The exact same assessment now lives in evals (same layer as dataset) to avoid a
validation->dataset->validationcycle. Freshv2IDs are used; no oldmeasurement changed.
