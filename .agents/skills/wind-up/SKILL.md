---
name: wind-up
description: End-of-session handoff for the sft-drift repo. Tidy the working tree (commit/push real work, drop scratch, check durability), then write a journal/ entry from the template so the next ephemeral agent can pick up. Use when the user says to wind up, wrap up, hand off, "make final commits", or is ending the session.
---

# /wind-up — tidy the box and write the session journal

The box is cattle and the session is ephemeral. This leaves the repo clean, pushed,
and with a journal entry the next agent reads to continue. Work top to bottom.

## 1. Tidy & commit
- `git status`. Commit any real, uncommitted work in small logical commits with clear
  messages (end each with the `Co-Authored-By: Codex …` trailer). Never commit secrets.
- Drop scratch, don't commit it: auto-generated `code/configs/_*.yaml`, `/tmp/*.log`,
  smoke outputs. `unsloth_compiled_cache/` and per-item `code/results/*.jsonl` are
  already gitignored (only `code/results/.apicache_*.jsonl` is kept) — trust
  `.gitignore`, don't force-add.
- Keep the paid caches (`code/data/**/.*_cache.jsonl`,
  `code/results/.apicache_*.jsonl`) — they cost money.
- `git push`, then confirm nothing is unpushed: `git log --oneline origin/main..HEAD` (empty)
  and `git status` (clean).

## 2. Durability check
- If `code/checkpoints/` is non-empty, those LoRA adapters live ONLY on the box and are
  NOT in git. Tell the user and offer `code/sync-artifacts.sh` (pushes adapters →
  private HF Hub).
  This is outward-facing — **confirm before running**, and never auto-destroy the box.

## 3. Write the journal
- Read the newest existing `code/journal/NNNN-*.md` (for continuity) and
  `code/journal/TEMPLATE.md`.
- New file: `code/journal/NNNN-YYYY-MM-DD-slug.md` — next zero-padded number, today's real date
  (from the environment, don't guess), short kebab slug of the session's theme.
- Fill every template section from what actually happened: `git log <last-journal-commit>..HEAD`,
  the result files touched, and the traps you hit. Rules:
  - **< ~1000 words.** Skimmable > exhaustive; detail lives in git + `code/results/`.
  - Cite result **file paths**, not just numbers, so the next agent can re-read.
  - Call out BROKEN/superseded outputs and anything half-finished or on fire.
  - Durable new gotchas also go into `code/CLAUDE.md`; note in the journal that you
    added them.
  - "Next session" is prioritized, with blockers and durability chores flagged.
- Commit the journal (+ any `code/CLAUDE.md` update) and push.

## 4. Report
Give the user the commit range, the journal path, and the one-line current state +
anything still needing them (e.g. adapters unsynced, box still running).
