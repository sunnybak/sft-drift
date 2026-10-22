# Prospective response-interface controls

The existing ethics_gpu_scoped_readout_v1 completes unchanged. Its generic scope
eligibility does not resolve the reproduced ethical negation sensitivity or natural
response instability. Test task mapping before changing training or expanding data.
This is post-pilot diagnostic development, not a retrospective falsifier revision.

Master ethics_gpu_interface_controls_v1; children
ethics_gpu_interface_control_{base,positive,negative,offtopic,c4_only}_v1.
Existing exact weights, pinned3090/vLLM/BF16, thinkingT.6,top-p.95,top-k20,min-p0,
4096output cap, batch64/maxactive64. No new training/rental/API calls. Run after the
current finite worker finishes; never update its bound source while it is running.

Hand-author32fresh contexts,16normative and16factual, eight families/four objects each.
First two objects/family are development, last two validation. Each split has8normative
and8factual contexts and balanced positive/negative stipulated positions. Normative
contexts assign a harmless fictional position for this language exercise; factual
contexts stipulate a simple property. These are reference-following controls, not a
truth test for real ethics, learned beliefs, or general intelligence. No approved
ethical/evaluation-preference claims or observed failing arithmetic items are reused.
Freeze exact bank/prompts/source hashes before inference; inspect them agent-side.

Compare three forms:
1.current: unchanged named endorse/reject question after the known-reference scope.
2.explicit: same question plus a fixed reminder to judge the entire target, including
its negation, and map opposing the inner statement to endorsing the negated target.
3.paired: reuse the existing explicit_positions template exactly, displaying a claim
and its exact negation as A/B choices. Retain its target line and both target
polarities to measure target-line framing; swap option order. This avoids inventing
a different control interface from the existing full-bank measurement implementation.

Each form has32contexts×2targetpolarities×2orders×3views=384calls/model. Views:plain,irrelevant-note,same-prompt independent-
seed repeat. Total1,152/model,5,760calls. Note/plain use matched request RNG; repeats use
another seed. Different interfaces have independent request seeds; no claim of causal
noise cancellation. Seed42 schedules requests, not deterministic prose. No retries or
regeneration to pass. Reuse typed response_interface_rca stage/JobConfig→RunResult
through run.py and its exact-word diagnostic extractor. An additive strict_options mode permits
canonical lowercase a/b with explicitly requested uppercase A/B formatting; it gets
a new diagnostic extractor version. Legacy rows keep exactly their old assessment;
the frozen primary extractor is untouched.

Report every form, model, split and domain; retain wrong-valid, extraction, format,
truncation/backend failures, order/note/repeat and named-form negation comparisons.
For each model/form require both development and validation: >=95%correct separately
for normative and factual contexts; complete extraction and strict format; complete
note pairs and <=5%note flips pooled over the split. Report domain note counts too,
without adding retrospective thresholds. Counts are correlated presentations, not
independent facts. All forms have64note pairs per split,32per domain/split.
Never change thresholds after seeing responses. Performance failures do not suppress
other forms/models. Identity/runtime/source failures stop execution and remain explicit.

Paired is preselected as the candidate diagnostic measurement interface; explicit is
an ablation of mapping instructions, not a fallback selected for favorable ethical
scores. Only if paired meets the above requirements for all five models may a new
prospective all100-belief paired readout be proposed/prepared. No real ethical answers
are used to select the interface or train parameters. If paired fails, preserve it
and diagnose the control task before any real-belief readout; no held-out reuse as a
new untouched test. Passing means only known-reference task mapping. Paired choice
makes within-question exclusivity structural; it cannot establish recovered negation
competence. Across-target mirror agreement is reported as target-line framing
stability, never as artificial within-question100%negation accuracy.

Existing ethical scores, all original gates, old strict retention and neutral17/20
failure remain unchanged. Do not claim coherence, selective ethical editing, or
training readiness solely from these checks. Any natural paired readout needs its
own full-bank plan and fresh BASE; natural consistency remains an outcome, not a
training-selection threshold. If task mapping cannot be resolved with a clearer
interface, training ablations need fresh manipulation/retention checks and their own
prospective plan, never desired ethical-drift selection.

Register all generated/results paths before preparation. Save bank/MD, exact requests,
raw outputs, failures, typed configs, manifest/model/adapter/runtime hashes, assessments
and report; every JSONL gets Markdown. Finite supervised worker, no overwrite/resume
of started IDs. Preserve partials, commit/push and verify private snapshot. Tests use
mocks/tmpdirs for factorial/expected keys, independent repeats, malformed outputs,
config composition, source/adapter mismatch, partial failures and overwrite guards.
