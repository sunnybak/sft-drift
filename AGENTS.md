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
