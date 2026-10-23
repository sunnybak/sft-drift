# Agent instructions

## Start here — current experiment only

Read **GOAL.md → STATE.md → BENCHMARKS.md**. For a fresh machine, follow **SETUP.md**
first. These files, current user instructions, and the actual artifacts define the
work. Do not resume a queue from an old skill, config comment, paper, or archive.
`CLAUDE.md` is a symlink to this file; edit only `AGENTS.md`.

The study measures how **fresh Qwen3-4B SFT** changes the full surface of 100 expressed
stances: 90 ethical claims and 10 off-topic preferences. Existing fine-tunes are excluded.
Conviction is retired. Local inference/data generation are allowed; training is CUDA-only
on Vast.ai. Never tune on the Mac. Do not rent resources without user authorization.

Keep orientation bounded: the three current files above, `git status`, then the files
needed for the next step. Historical hypotheses are not current hypotheses. The archive
is opt-in evidence, never instruction. Do not recursively read it to get oriented.

## Current experimental rules

- Preserve the frozen bank, prompts, extractor, scoring and decoder for SFT comparisons.
  A changed instrument or run gets a new ID; never overwrite historical measurements.
- Evaluate **all 100 beliefs on every new fine-tune/checkpoint**, not just its target.
  Keep every valid result, including endorsement of both a claim and its negation.
  An explicit user stopping condition overrides remaining collection. Stop model calls
  when the decisive result is reviewed; preserve canceled grids as partial, never complete.
- Separate Stance Score, agreement, extraction/format compliance, instrument controls,
  and retention. Frequencies are not confidence; stance drift alone is not forgetting.
- Pass fresh factual/format controls on each evaluated model. Failed controls or missing
  replies remain explicit; do not convert them to neutral scores or silently drop them.
- Establish GPU BASE on the same GPU backend/decoder as its fine-tunes. The existing MLX
  result is a baseline study, not a substitute for CUDA BASE. Record card, versions,
  model revision, adapter, sampling settings/seeds, batch size and token/stop metadata.
- Estimate sampling variability before attributing a small change to training. Report
  coverage, per-arm scores, per-check agreement and uncertainty with before/after changes.
- Use matched opposite-position datasets and dose-matched off-topic SFT controls;
  retrain controls per training seed. The ten off-topic eval beliefs are **not** trained
  control arms. Keep related-belief groups predeclared; do not infer correlation from names.
- Pilot generation, inspect examples, then scale. Prefer more, shorter examples; count,
  length, explicit-stance versus evidence design, and training schedule are not yet frozen.
  Reuse generation utilities, not an old topic's corpus or schedule by assumption.
- Before real SFT, pass GPU calibration, a tiny memorization test and checkpoint reload
  checks. Monitor saved checkpoints; do not select training parameters on belief outcomes.
- Before treatment runs, write the hypothesis, contrasts, controls, analysis and falsifier
  in the current study plan. Never revise a falsifier after seeing its result.
- No old step number, LR, epoch count, ratio or training queue is a requirement for this
  study. Validate any reused setting on the new data and training manipulation checks.

## Experimental judgment and stopping discipline

- Before a tuning block, declare the question, competing explanations, discriminating
  comparisons, maximum new training runs, evaluation workload and wall-clock review point.
  Work within existing user authorization. Overnight autonomy is not an unbounded search
  budget. A failed hypothesis does not automatically authorize another repair round.
- Establish a standard, independently checked training reference early, alongside custom
  loss weighting, replay or training code. Successful weight updates and reloads prove
  execution, not that the objective is appropriate or behavior is preserved.
- At each decision point, consider data, training objective, trainer implementation,
  inference mode and measurement design. Prefer a comparison that separates plausible
  causes over another local parameter tweak. Say which causes remain unidentified.
- Calibrate new gates against repeated BASE behavior before using them to select a recipe.
  Distinguish broad capability checks from narrow diagnostic tasks. Many variants of a few
  facts, repeated seeds or repeated development tests are not independent validation.
  Keep independent confirmation inputs separate from the examples used to develop repairs.
- Report all-item accuracy, losses of BASE-correct items, gains on BASE-wrong items,
  formatting, generation completion and mode-specific behavior separately. A failed gate
  rejects the declared recipe; it does not by itself establish global degradation,
  knowledge erasure, or impossibility of document SFT. Do not dismiss genuine errors as
  parsing issues without reading the actual request and reply.
- Order inexpensive checks before larger suites, and estimate why each suite is needed.
  Account separately for training, inference, engineering and preservation time. Recommend
  more resources only for an identified bottleneck; more compute cannot replace a useful
  experimental contrast. Do not keep adding infrastructure without a decision it enables.
- At the declared budget, review point or user stop condition, give a scientific readout:
  what was learned, what failed, what remains unknown and the recommended decision.
  Continue only branches already covered by the plan and user authorization. Do not
  silently extend the budget, weaken a gate or select a checkpoint to manufacture a pass.
- Benchmark work is not delivered until its reviewed results are in the dashboard as
  well as saved artifacts, unless the user requests another presentation. Include rejected
  attempts, matched BASE references, exact denominators, thresholds and explicit partial
  coverage. Distinguish scientific progress from hours spent, code written or checks run.

These rules govern future work; they do not revise historical scores, falsifiers or
protocols. A paused study stays paused unless the user explicitly resumes it. Reporting
or documentation requests do not authorize new training or inference experiments.

## Engineering

Use plain typed Python, YAML job configs and JSONL artifacts. Prefer existing code and
small inspectable changes over frameworks. Jobs are `JobConfig -> RunResult`, launched
from `belief-transfer/run.py`. Only `src/belief_transfer/config.py` may read YAML or import
Hydra/OmegaConf within `src/`. Operational scripts may read their explicit own inputs.
Config is passed as data; environment variables hold secrets only.

Keep the dependency layers enforced by `tests/test_import_rules.py`:

| layer | modules |
| --- | --- |
| 0 | schemas; metrics (standard library only) |
| 1 | generation, inference |
| 2 | dataset, training, evals, validation, benchmarks, analysis, client, data_sync |
| 3 | config, stages |
| 4 | run.py |

Preserve the existing named exception for `inference.calibrate`, which invokes training.
Do not add an unclassified package. Keep optional heavy dependencies lazily imported.
Use narrow meaningful tests first; broader checks for shared changes. Tests must never
write into real experimental result directories or load weights without explicit opt-in.
Do not upgrade pinned ML dependencies while doing unrelated work.

Store exact prompts, raw outputs, failures and resolved configs next to results. Every
new JSONL gets a derived Markdown view. Artifacts stay under
`belief-transfer/data/{generated,results,checkpoints}/<experiment>/<run>/`.
GPU measurement overlays continue under **ethical_pilot** so they can use the frozen
bank. New GPU run IDs start **ethics_gpu_**; new SFT study run IDs start **ethics_sft_**.
Register new artifact paths in `configs/handoff.json` before running them. No run/config/
data purges during ordinary cleanup.

## Progress must survive the box

**At each completed work block and before ending a session:**

Group related work into coherent decision boundaries. Do not turn each minor edit or
intermediate observation into another full snapshot; preserve live jobs at safe boundaries.
Preservation remains required and is not a substitute for a scientific result.

1. Update `STATE.md` with what actually completed, active run IDs, process/checkpoint
   state, blockers and the exact next command. Keep it short; append details to a dated
   `changelog/` entry. Record failed/partial/void runs where their artifacts live.
2. Save code, configs and these notes in Git; push the working branch. Do not commit
   credentials or use an agent stash as the only copy of progress.
3. From `belief-transfer/`, run `uv run --no-sync python scripts/handoff.py save`.
   This snapshots the declared active data, cache and new study outputs to the private
   destination in `configs/handoff.json`. It refuses dirty source, public storage,
   missing required inputs, or changed frozen files. Check the success receipt.
4. State what was saved and what was not. A failed push is unfinished preservation;
   keep local files and report the exact blocker. Never claim a box can be destroyed
   until both Git and artifact storage are verified.

For ongoing jobs, save completed artifacts/checkpoints at safe boundaries. Record the
command, log path and latest checkpoint, and say whether the stage actually supports
resume. A process on an ephemeral box does not survive a fresh chat/box by itself.
`handoff.py` snapshots bytes; it does not make every stage resumable. Existing completed
measurement IDs cannot simply be rerun to continue an interrupted measurement.

Only the `orient` and `wind-up` repository skills are active. Do not load archived skills
unless the user explicitly returns to that workflow. `configs/ACTIVE.md` maps the small
current code/config surface; remaining legacy modules/configs are compatibility code.
