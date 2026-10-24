---
name: optimize
description: Archive completed work and lighten this repository's active docs, discovery and setup while preserving evidence and reproducibility. Use for repository cleanup or preparation for another experimental round, not scientific tuning or model-performance optimization.
---

# Optimize the repository

Make the next authorized work easier to find and cheaper to set up. Treat this as
maintenance: it does not resume a paused study, launch models, rent GPUs, or authorize
new experiments. Follow root AGENTS.md and the current user scope.

## Inspect and choose a bounded cleanup

Read GOAL → STATE → BENCHMARKS, git status and configs/ACTIVE.md under belief-transfer.
Inspect tracked files, directory sizes and dependency/caller references relevant to
cleanup; do not recursively read historical research to rediscover a task queue.
Distinguish source clutter, stale instructions, generated build/cache files, and large
preserved datasets/checkpoints. State the useful changes and expected savings before
editing. Prefer small changes that reduce orientation or setup cost over broad rewrites.

## Archive without losing reproducibility

- Put completed plans, superseded guides and retired outputs under a dated root
  `archive/` directory. Save exact old bytes before replacing a working guide.
- Record original path, archive path, byte length and SHA256 in a manifest; verify
  the archived copy. Add a concise archive index and update active links or leave a
  short pointer at a compatibility path. Historical content is evidence, not instructions.
- Keep current STATE short: actual outcome, active/partial/stopped runs, limitations,
  preservation receipt and exact next action. Keep metric definitions in BENCHMARKS,
  bootstrap in SETUP and reusable entry points in configs/ACTIVE; archive old queues.
- Before moving code/configs, check imports, tests, Hydra defaults/inheritance,
  operational scripts, report exporters and recorded source paths. Keep compatibility
  paths where moving would break them; don't mass-relocate configs merely to look tidy.
- Preserve frozen banks, prompts, extractors, scores, decoder settings, falsifiers,
  failed/partial results, dataset lineage and checkpoint identities. Never reclassify
  an experiment while cleaning up. Do not rewrite recorded source hashes.
- No blanket purge, Git-history rewrite, dependency upgrade or experimental-data
  eviction. If the user explicitly requests disk eviction, first verify the exact
  remote bytes and document a working restore route; ordinary archival is not deletion.

## Reduce setup overhead where it helps

Use the existing private study/corpus stores rather than copying data into Git.
For report browsing, prefer handoff.py `restore-review` / `verify-review` and the
Dashboard `dev:saved` / `build:saved` commands. Full restore remains necessary for
raw evidence or experimental inputs. Do not regenerate reports just to open saved JSON.

Any additional selective restore must be pinned, hash-checked and conflict-safe,
explicitly partial, and unable to overwrite the full receipt or save an incomplete
snapshot over the full backup. Preserve the existing full-save omission/frozen guards.
Add new infrastructure only for a concrete recurring cost demonstrated by this task.

Measure honestly: moving files within Git does not shrink its history; avoiding a
checkpoint download is not freeing local disk. Report before/after bytes, file counts
or orientation size using the same scope. Do not silently remove evidence for savings.

## Verify and finish

Check archive hashes, links/callers and frozen-input identities. Run narrow relevant
tests; broaden for shared storage/config changes. Test transfer changes in temporary
projects with mocks, including partial/full receipt separation, conflicts, invalid
paths, missing inputs and save refusal. Never run tests against real result directories
or load weights to validate cleanup. Build the dashboard if its startup/build changes.

Update STATE and a dated changelog with moves, measurements, validation and limitations.
Commit/push source and notes. Preserve artifacts using the repository's wind-up rules
at a coherent work boundary; do not create a full snapshot for every tiny intermediate
edit. Wait through supported storage retries and inspect the verified receipt before
claiming preservation. If blocked, keep local bytes and report the exact unfinished step.
Conclude with what is lighter, what remains intact, and the next usable command.
