---
name: wind-up
description: Wind up a work session in the sft-drift belief-transfer repo — write the changelog entry, refresh STATE.md, mark any newly-void runs, and push the cache, data, and code before the box is lost. Use this whenever the user says "wind up", "wrap up", "write the changelog", "I'm done for today", "ending the session", or is about to destroy or shut down a rented GPU box. Also use it mid-session after any episode that produced a real finding, since a finding that is not written down before the context is gone is a finding that has to be re-derived.
---

# Wind up

Sessions end and their context is lost. What survives is what you write now. The changelog
is this project's episodic memory; `STATE.md` is its working memory; the pushes are the
difference between artifacts that exist tomorrow and money spent twice.

Do these in order. The pushes come last but they are the part that is irreversible if
skipped on a rented box.

## 1. Establish what actually happened, from evidence

Do not reconstruct the session from memory — long conversations get summarized and the
detail that matters is usually a number, which is exactly what summaries drop. Look at:

```bash
git log --oneline --since="1 day ago"
git status
ls -lt data/results/*/*/ | head -40      # newest result directories
ls -lt data/checkpoints/*/ | head -20
```

Then read the run reports (`data/results/<exp>/<run_id>/<stage>.yaml`) for anything new.
Those carry the numbers, the `config_sha`, and the cost. Quote from them rather than from
recollection.

## 2. Write the changelog entry

`changelog/YYYY-MM-DD.md`, with a letter suffix if the day already has one
(`2026-08-19b.md`). Append to the current day's file if one exists and the work continues
the same thread; start a new file when the session is genuinely separate.

Use [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) groups (`Added`, `Changed`,
`Deprecated`, `Removed`, `Fixed`, `Security`) plus the two that matter more here:

- **Learnings** — what outlived the session. Write the number with its units and
  conditions, not the impression: *"base scores 1.000 with the document in context vs
  0.032"* is usable a month later; *"the oracle did well"* is not. Dead ends belong here
  **with the reason they were dead**, because the reason is what stops someone walking
  down them again. A negative result belongs here as much as a positive one.
- **Next** — the state of play, so the next session opens on a decision rather than an
  investigation. Include what you deliberately did *not* do, and why.

Reference run ids (`matrix_v1_step24`, `tune-72d93588`) so every claim can be traced to its
data. Keep the experimental results themselves out — they live in
`data/results/<experiment>/<run_id>/` and that is the authority. The changelog records what
was run, what it implied, and where the artifacts are.

If the session produced nothing worth carrying forward, say that in a sentence and stop.
A padded entry costs the next reader time and teaches them to skim.

## 3. Refresh `STATE.md`

`STATE.md` is overwritten, not appended — it holds only what is *currently* true and not
derivable from anything else. Keep it to roughly a page; if it is growing, the surplus
belongs in the changelog.

Sections: standing result (a pointer to AGENTS.md, plus the headline numbers), current
experiment and live run ids, **void runs**, in-flight work, next decisions in order with
cost estimates, and box/sync state.

## 4. Mark newly-void runs, in two places

When arms are replaced, an instrument is re-versioned, or a control changes, every result
measured against the old version becomes uninterpretable — and nothing on disk says so. A
voided directory is byte-identical in shape to a valid one, so a future reader picks it up
and quotes it.

Record it in `STATE.md`'s void table, **and** drop a `VOID.md` in the run directory itself
naming what voided it and what supersedes it. The table is for orientation; the marker file
is for whoever opens that directory directly. Leave the artifacts in place — they are the
dated record of what was actually measured.

## 5. Update the hypotheses this session touched

`hypotheses/` is mutable, which is exactly why it rots: nothing fails when it goes stale.
For every hypothesis this session produced evidence for or against:

- append a dated `Evidence` line naming the run id — append only, never rewrite an
  existing line, and leave superseded readings in place annotated
- change `Status` if it moved, and say so in the changelog entry rather than silently
- **do not touch `What would falsify it`.** A falsifier edited after the result is in is
  not a falsifier. If it was wrong, say so in `Evidence` and open a new hypothesis file.

**Move a resolved hypothesis out of `open/`** into `supported/` or `falsified/`, and fix
the relative links that point at it. Keep the file — the reason a hypothesis died is what
stops the next session re-running it.

If the session opened a new question, give it a file, **but `open/` is capped at three**.
If it is already full, resolve or abandon one first, or fold the new question into an open
file's `What it predicts next`. The cap is what keeps the directory something a session
reads rather than skims; quietly exceeding it is how it stops being useful.

Then check `GOAL.md` still describes what the project is doing. It is updated
occasionally, but **only on the user's feedback and never as a side effect of a session** —
if this session's work does not serve it, say so out loud in the changelog and let the user
decide which was wrong, the statement or the work. A statement quietly widened to fit what
was already done cannot fail, and a north star that cannot fail is not one. When the user
does revise it, record what moved and why in that session's entry.

## 6. Keep the quotable set honest

There is no longer a separate claims ledger — `PAPER_AUDIT.md` was deleted 2026-08-30b
because it duplicated `STATE.md` and rotted faster than it was read. What replaced it:

- **`STATE.md`** carries the standing result and the **void / withdrawn** list. If a claim
  died this session, it goes in that list with the reason — `AGENTS.md`'s "withdraw rather
  than caveat" exists so the next session does not rediscover a dead claim as support.
- **`insights/YYYY-MM-DD-<slug>/`** carries each quotable claim with its own provenance: every numeral
  tied to an artifact by `bt check`, and its own Margin stating what it does not license.
  A claim that is worth quoting is worth a note; a claim that cannot survive `bt check` is
  not ready to quote.

`AGENTS.md` holds no results by design. Touch it only when the session changed a *rule* —
how an experiment must be designed, gated, or read — not when it changed a number.

## 7. Push, in risk order

```bash
make cache-push   # first: LLM calls you paid for, unrecoverable if the box dies
make data-push    # corpora, checkpoints, results — expensive to regenerate
git push          # code
```

Cache first because it is the only one that costs real money to reproduce and the only one
with no other copy. If the box is being destroyed, confirm all three succeeded before
saying you are done — "pushed" without a successful exit is the failure mode that loses a
session's work.

Report what was pushed, and note anything deliberately left local (scratch checkpoints,
smoke runs) so the next session does not go looking for it.

## Honesty rules

- A session that produced a null, a failed run, or a dead end has produced something.
  Write it down with the same care as a positive result; the reason a dead end is dead is
  often the most reusable thing in the entry.
- If a gate failed, record the failure. Never record a threshold that was moved to make
  something pass — that change is invisible in the artifacts afterwards, which is exactly
  why it is ruled out.
- If you are unsure whether a number is real, say so in the entry rather than omitting it.
  An uncertain number with its uncertainty stated is useful; a quietly dropped one is not.
