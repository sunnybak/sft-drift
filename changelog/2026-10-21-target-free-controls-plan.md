# Prospective target-free control pilot

Written after the stopped paired candidate and before new target-free model calls.
Current goal remains error resolution before scaling, not demonstrating a desired
ethical drift. No training, new rental or changes to historical instruments/results.

## Candidate and rationale

Remove the entire Target statement line from the existing explicit opposing-position
A/Btemplate. Retain the scope, both full opposing statements, request for the model's
own judgment, option-order reversal, final-letter contract and the pinned decoder.
No added logical reminders or ethical demonstrations. This removes a cue that BASE
explicitly mistakes for an answer key in fully read replies. It does not promise to
fix every reasoning-to-final mismatch, nor establish a causal explanation of every
historical inconsistency. Only this template is the preselected candidate.

Use a new ethics_gpu_target_free_controls_v1 master and child IDs
ethics_gpu_target_free_control_{base,positive,negative,offtopic,c4_only}_v1. Reuse the
existing typed response_interface_rca stage, client and exact-letter diagnostic mode.
No natural ethical scores are collected in this calibration. Existing fixed weights,
Qwen revision, CUDA/vLLM, thinking T0.6/top_p0.95/top_k20/min_p0,4096cap,4352context,
batch64 and request-seed metadata remain. Token-audit before freezing/running.

## Fresh references and source reproducer

Context texts/references are fixed deterministically. Seed42shuffles their scheduling
and sets request RNG metadata; this does not make GPU prose deterministic.
64fresh contexts:16fictional stipulated normative positions,16supplied facts and32
ordinary integer arithmetic judgments. Arithmetic is not replaced with a supplied
answer: the model must decide truth itself. Include addition, subtraction,
multiplication and greater-than comparisons, balanced canonical true/false claims.
Record programmatically computed references and inspect every case before freezing.
Use English-number statements comparable to old controls; avoid reusing their cases.

Split each family by disjoint objects/operands into development/validation: each has
8normative,8supplied-factual,16arithmetic contexts. Two physical A/Borders and three
views (plain, identical-prompt independent-seed repeat, irrelevant note matched to
plain's sampling seed) give384fresh presentations/model. Normative and supplied facts
remain stipulated-reference checks, not truth labels for real ethical views. Families
are reused across splits; do not claim entirely held-out language capability.

Also preserve four regression presentations derived from the two actual BASE five>
three failures (plain/note): remove only the Target statement line, keep exact choices,
use the original request seed plus one independent repeat each. Store original source
ID/hash and transformation. These are reused development evidence, excluded from fresh
validation/gates; report each reply separately. Do not claim matched seed isolates a
causal effect when prompts differ.388calls/model,1,940max across allfive.

## Predeclared gates and sequence

Before calls freeze bank/config/source/adapter/hash metadata and register output paths.
Run BASE first. Reconstruct each response from raw text and verify runtime/token IDs.
Both fresh splits must independently meet all of:
- >=95%correct separately in normative, supplied-factual and arithmetic domains;
- complete extraction,100%exact format and normal stop on every fresh reply;
- complete note pairs and<=5%matched-note disagreements;
- no unmarked source/backend/tokenization/identity failures.

Each split has48normative,48supplied-factual,96arithmetic presentations and64note pairs;
these are correlated variants, not192independent problems. Missing/wrong replies remain
explicit failures; do not drop or substitute them. Show same-prompt repeat and
option-order agreement separately; no ethical-consistency training-selection gate.

If BASE fails either split, preserve it and stop before adapter calls under this
predeclared calibration rule. Do not lower gates, choose a fallback template from
validation, or rerun this ID. If BASE passes, run all four adapters even if one fails,
so training-specific failures remain visible. Qualification for a future readout
requires all five pass both splits. Regression reproducer outcomes remain separate.

## Decision and next experiment

Success authorizes preparing a distinct target-free full100readout, not training or
scaling. It uses the same100approved belief contents and six wordings, two physical
A/Borders, and no redundant target-polarity axis:1,200presentations/model/seed, with its
own fresh BASE. Its full protocol, seed variability design and expected calls must be
frozen before launch. Removing that axis does not count as recovered negation
competence; old polarity/target-framing outcomes stay recorded.

If candidate fails, diagnose fresh known-reference errors and the saved regression
replies. Any changed decoder/model/template requires new IDs and independent validation;
select on factual/manipulation controls, never desired ethical direction. Free-prose
stance elicitation with separately validated semantic scoring is a possible subsequent
approach if forced-letter output remains unreliable; it is not an automatic fallback.

Finite CUDA worker, no resume/autorestart/overwrite. Preserve every completed/partial
output and Markdown view; tests use mocks/tmpdirs, separate from live copy/export work.
Commit/push and verified private snapshot at boundaries. Current STATE controls actual
execution; this plan alone is not evidence of implementation or a running job.
