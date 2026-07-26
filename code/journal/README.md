# journal/

Session handoff log. Claude Code sessions on the box are **ephemeral**; this is
how one agent picks up where the last left off.

**Landing on this repo fresh? Read in this order:**
1. `CLAUDE.md` — invariants & landmines (don't "fix" the deliberate ones)
2. **The newest `journal/` entry** — current state, live results, what's next
3. `../notes/guide.md` — the phased build spec · `../notes/remote-workflow.md` — the ops loop

## Convention
- One file per session: `NNNN-YYYY-MM-DD-slug.md`, zero-padded, sorted oldest→newest.
- Newest = current truth. Older entries are history; don't edit them (except to
  fix a claim later proven wrong — leave a dated note when you do).
- Keep each entry under ~1000 words. Detail lives in git + `results/`; the journal
  holds the story, the state, and the traps.
- Write it with `/wind-up` at session end (tidies the tree, then drafts from `TEMPLATE.md`).
