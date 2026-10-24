# Repository cleanup — 2026-10-24

User requested archival and a lighter workspace before another experimental round.
This is maintenance, not authorization to resume the stopped study or run models.

## Changes

- Preserved exact pre-cleanup STATE, BENCHMARKS, SETUP, ACTIVE map, root README,
  Vast handoff and SSH guide in archive/completed-round-2026-10-24/docs/.
- Moved125tracked old paper/baseline artifact files from belief-transfer/out and
  belief-transfer/output into that archive's legacy-artifacts/. No scientific
  artifact removed. Manifest records132files (including7doc snapshots), original
  paths, destinations, sizes and SHA256; all48,516,038bytes verified after move.
- Replaced stale working docs with the actual stopped state, stable measurement
  definitions, reviewed outcomes and a short reusable code map. Four orientation
  docs shrink68,523→16,552bytes (75.8%). Old hypotheses/falsifiers/scores remain
  unchanged in byte-preserved notes and dated reports. Historical code/configs stay
  at original paths for imports, tests and Hydra inheritance. Changelog/report source
  paths stay stable. No frozen-bank, prompt, scoring, decoder or ML pin changes.
- Added restore-review / verify-review to handoff.py. Only explicitly registered
  report prefixes are fetched; pinned revision, private access, path confinement,
  conflicts and SHA256/byte checks retained. Full remote frozen-bank metadata is
  checked even though review does not fetch the bank. Corpus/checkpoints are skipped.
  Separate .handoff-review-receipt.json explicitly labels the subset; existing full
  receipt untouched. Saving from a review-only checkout is rejected. Full restore,
  frozen checks, saved-file omission guard and full save scope remain intact.
- Added dev:saved / build:saved dashboard commands. Existing dev/build still export
  from full raw data. Review profile supports Dashboard library; legacy Compare/By
  benchmark needs benchmarks.json from full export. Raw source hashes remain visible
  but do not imply raw files were fetched.

## Size and validation

Live isolated restore to /tmp/sft-review-restore-2026-10-24 verified20report JSONs,
7,062,565bytes, versus22,336,531,402bytes for the previous study snapshot (separate
corpus additional). This reduces study-artifact review downloads by99.968%; it does
not delete existing28GBdata or shrink Git history by moving files within Git.
All20restored reports pass schema/semantic loader validation, zero errors. Both
normal locked and minimal no-project Python environments verify the review receipt.
No ML stack is required for the minimal review utility. No model calls performed.

Broader storage/corpus/import/data-sync/config-composition/stance suite:86passed
in93.75s, including three new review-profile tests. Historical overlays all compose.
Dashboard5Python exporter tests and58Node tests pass; TypeScript + build:saved pass
(existing bundle-size warning only). Full frozen_files and all full handoff scope
fields equal their pre-cleanup versions; archive hashes and Git rename identity checked.

## Preservation

Source/config/notes committed and pushed, then standard full handoff.py save verifies
all existing data and the new code identity. Final receipt is authoritative; save log
/tmp/sft-repository-cleanup-save.log. No local artifact eviction or remote deletion.
Next round still requires a new prospective experiment plan and user direction.

## User-requested reusable skill

Added repository `/optimize` skill under .claude/skills/optimize, discoverable through
the existing .agents→.claude symlink. It captures bounded inspection, hash-preserving
archival, short current docs, compatibility checks, selective setup, honest size
measurement and coherent preservation boundaries. No new cleanup is executed by
creating the skill. AGENTS.md now lists optimize alongside orient/wind-up. Skill
frontmatter/scaffold validation and metadata/reference checks pass. This small
source-only follow-up is committed/pushed; no experimental artifacts changed and no
redundant full snapshot is needed after the just-verified cleanup boundary.
