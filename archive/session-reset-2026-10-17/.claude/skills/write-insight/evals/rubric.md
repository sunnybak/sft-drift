# Grading rubric — write-insight

Two scripts cover everything mechanical. Run them **first**, and do not re-grade by eye what
they already decided:

```bash
uv run python .claude/skills/write-insight/scripts/score_note.py <note_dir>
cd belief-transfer && uv run bt render <note_dir> && uv run bt check <note_dir>
```

`score_note.py` grades the *elements*: sections present and in reading order (Motivation, Key
Concepts, Insight, Figures, Margin), title shape, Motivation's three beats, Key Concepts free of
measurements, figure encoding, tables rendered not typed, Margin forward-looking, length. `bt check` grades the *grounding*: every ref, every numeral at its own
precision, every declared derivation re-evaluated, void flags on cited runs, stale figures and
tables. Between them, most expectations in `evals.json` are decided without judgment.

Note the `render` before `check`: a note whose tables were never rendered will report a table
problem that is an artifact of grading rather than of the work. Render first, then check.

What follows is the half no script can see. Grade it per element, then as a whole, and write
feedback the way you would to the person who has to revise it: **name what to change, not just
what is wrong.**

---

## Per element

### Title

**This is the element the script is weakest on, so it is the one that most needs judgment.**
`_MAXIM` catches proverbs and `\d` catches a missing number. Neither can tell whether the title
reads as a *conclusion* — and that is the actual requirement.

Three questions, in order:

1. **Is it a claim?** Subject, verb, object; something you could say out loud and be agreed or
   disagreed with. "Notes on corpus form and belief" is a topic. "Corpus form and belief scores"
   is a topic with a conjunction.
2. **Does it parse at a glance, without the note?** This is the test a script cannot run and the
   one that failed in review. "Length is worth 2.3x; density has no quotable magnitude" passes
   every mechanical check — specific, two outcomes, a number — and still stops a reader cold:
   worth 2.3x of *what*? A title that needs the note to be understood has the dependency
   backwards.
3. **Is it true to the note?** A title that overshoots ("Density does nothing") or undershoots
   ("Some notes on the form 2x2") also passes the mechanical check.

And the portability test: **could this title be moved unchanged onto a different note in this
repo?** If yes, it is a topic label.

### Motivation

The script checks the goal sentence is present. Judge whether the three beats actually
*connect*: goal → the uncertainty this work chased → one sentence handing off. A common failure
is three beats that are each fine and do not follow from each other — the goal is stated, then
an unrelated uncertainty appears, and the hand-off promises something the Insight does not
deliver.

Second: is the uncertainty a real one, or is it the finding restated in the future tense?
"We wondered whether density or length mattered more" is a question. "We wondered whether one
factor's magnitude would be unquotable" is the answer wearing a question's clothes.

### Insight

This is where a note earns its existence, and almost none of it is checkable.

- **Is it ONE claim?** A note that reports three findings is a run summary; `report.md` already
  does that better. If you can delete a paragraph without weakening the title, the note has
  more than one claim.
- **Is it non-obvious?** Would a competent person familiar with the project have predicted it?
  "Explicit stance moves belief more than evidence does" is already in AGENTS.md. Restating a
  known result is not an insight, however well grounded.
- **Does something follow from it?** The strongest notes change what someone would do next.
  Flag a note that is true, grounded, novel and inert.
- **Are the numbers doing work, or decorating?** Every quoted figure should be load-bearing. A
  number nothing turns on should be in a table, not in a sentence.

### Key Concepts

The script flags measurements outside code spans. Judge coverage and honesty:

- Is every term that carries weight in the Insight defined here? A note using "netted",
  "machinery", or "spread" without defining them is unreadable outside this repo. This section
  sits BEFORE the Insight precisely so the reader never has to stop mid-claim.
- **Is every derived quantity given as a formula?** Prose definitions of derived quantities are
  where ambiguity hides: "the ratio of one cell to its neighbour" does not say which is the
  denominator, and in the shipped note the denominator IS the finding. A formula in backticks
  settles it in one line, and constants inside it are exempt from the measurement check.
- Does a definition smuggle in a claim? "**Density** — the factor that actually drives belief"
  is an argument, not a definition, and it escapes the scrutiny the Insight gets.

### Figures

The script checks a figure exists, plots refs, and does not bake a repeated dimension into its
labels. Judge whether the encoding serves the claim:

- **Is the variable the note is about the visible one?** If the note is about spread across
  seeds, seed must be the dimension you can see. This is the single most common figure defect
  and the reason `series` exists.
- **Does the caption say what to look at?** "Netted belief effect by cell" names the axes.
  "Short-sparse staircases left while the other rows stack" tells a reader what they are
  looking for.
- **Are absences visible?** A cell that was never run should read as a gap, not silently
  reflow its neighbours.
- Averaging repeats away is almost always wrong when the note is about variation between them.

### Margin

The script checks for at least one forward-looking item. Judge substance:

- Is there a **concrete** next step — one someone could start tomorrow — or only "more work is
  needed"?
- Does it name what the note deliberately did **not** conclude? A Margin that only lists
  caveats is a limitations section.
- Does it name the alternative explanation that was *not* ruled out? A note whose Margin
  contains no live alternative is either exceptionally strong or has not looked.

---

## Overall

One question, and it is the one that decides whether the note should exist:

> **Is this worth someone's five minutes, and does it change anything?**

A note can pass every mechanical check and fail this. Three shapes to watch for, all of which
score clean:

1. **The restatement.** Grounded, well-formed, and already in `AGENTS.md`.
2. **The inventory.** Every number from a run directory, arranged into sections. `report.md`
   already does this, and does not pretend to be an insight.
3. **The overclaim.** One seed, one cell, or a ratio whose denominator straddles zero,
   presented with the confidence of a replicated result. `bt check` verifies that a number is
   *real*; it has no opinion on whether the claim built on it is *supported*.

Then the discipline questions, which are how this repo's results stay usable:

- **Did it quote anything flagged?** A cited void or gate-failed run is a fail regardless of
  everything else, and no caveat repairs it.
- **Did it compare across item banks?** Scores from different suites are not commensurable.
  Treating that as a caveat rather than a defect is a fail.
- **Did it quote a magnitude it should not have?** A ratio whose denominator scatters, or whose
  numerator straddles zero, gets a direction and not a number.
- **Did it weaken a check instead of fixing the work?** Editing prose to dodge `bt check`,
  loosening a threshold, or deleting an inconvenient ledger entry. This is the most serious
  failure available and outranks a clean score.

---

## Writing the feedback

The consumer is the agent that will revise the note, so:

- **Order by what to fix first.** Grounding defects before prose ones — a beautifully written
  note citing a void run needs the citation fixed before anything else matters.
- **Quote the offending text.** "Key Concepts defines dB NET with a measurement in it" is
  actionable; "Key Concepts could be tighter" is not.
- **Say what to change it to** where you can. The scripts already do this — `bt check` prints
  the ledger line to paste when exactly one candidate matches. Match that standard.
- **Separate "wrong" from "thin".** A wrong number and an underdeveloped Margin need different
  responses, and collapsing them into one list of complaints makes the important one easy to
  miss.
- **Say when an element is good.** A reviser who cannot tell which parts to leave alone will
  churn the whole note.

## Sanity-checking the scorer itself

A grading script that only ever passes is worse than none, so the two directories in this repo
are its regression pair. `score_note.py` must report **zero FAILs** on
`insights/2026-08-26-form-ratios-seed-stability/` and **at least seven** on
`evals/fixtures/draft-note/`. If either stops holding, the scorer has drifted and every grade
it produced since is suspect — check that before trusting a run.

## Critiquing these evals

Per `agents/grader.md`, flag weak expectations. Specific things to watch for here:

- An expectation that passes because a script printed something, without the agent having acted
  on it. "Ran `bt check`" is weak on its own; "reports 0 unresolved numerals" is what matters.
- Anything satisfiable by a note that is grounded and pointless. Most expectations in
  `evals.json` are about form, and form is necessary rather than sufficient — the *Overall*
  section above is doing most of the real discrimination, so say so if it is being underweighted
  relative to the checkboxes.
- The reverse: an expectation so subjective that two graders would disagree. Those belong in
  this rubric as guidance, not in `evals.json` as pass/fail.
