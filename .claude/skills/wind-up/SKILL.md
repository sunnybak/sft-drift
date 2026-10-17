---
name: wind-up
description: Preserve current ethical-stance study progress for another chat or GPU box; use after a substantive work block, on wrap up, or before shutting down a Vast.ai box.
---

# Wind up

1. Inspect actual artifacts, `git status`, and any running process/log/checkpoint. Record
   failures and partial work as carefully as successes; do not infer success from a directory.
2. Update root STATE.md: current stage/run IDs, completed/partial/void work, exact next
   command and unresolved decisions. Keep historical detail in a dated changelog entry.
   Preserve existing falsifiers and run artifacts; do not silently broaden the goal.
3. Commit code/config/progress changes and push the working branch. Keep credentials out.
4. From belief-transfer/, run `uv run --no-sync python scripts/handoff.py save`.
   It checks private storage, required/frozen inputs and clean Git, uploads a coherent
   snapshot including cache/new checkpoints, and verifies the pinned remote manifest.
   Never fall back to the old public dataset or a blanket legacy data push.
5. Report the Git commit/branch, artifact revision, verification result and anything left
   only local. If either save fails, preserve local files and state the blocker. Do not
   say a box can be destroyed until both code and data are safely remote.

Do this at completed work boundaries, not only at the end of an expensive session.
If a process continues, record its command, log and latest checkpoint plus whether its
stage supports resume; do not promise that the process survives box destruction.
