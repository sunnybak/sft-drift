---
name: write-insight
description: Write a short, grounded insight note from this project's measured results into insights/<slug>/ using the `bt` CLI — find the finding, build a ref ledger, chart it, audit every numeral. Use this whenever the user asks for an insight, a note, a finding, a short writeup, a summary of what some runs showed, or says something like "what's interesting here", "write that up briefly", "make a note of it", or mentions insights/. Also reach for this INSTEAD of write-paper when the deliverable is short or the argument is not yet settled: a note costs a fraction of a paper, is the substrate a paper or blog post is later built from, and `bt check` gives it the same numeral-level provenance without an author model or a LaTeX toolchain.
---

# Write an insight note

An insight note is **one specific claim, grounded**. Not a run summary, not a status report,
not everything you found. `insights/<slug>/` holds `note.md`, `sources.yaml` (the ref
ledger), and `figures/`.

You write the prose yourself. There is no author model and no stage — the tooling exists to
find the numbers, chart them, and check them. `report.md` already summarises a run; a note
earns its place only by saying something a run directory cannot.

## 1. Find the finding before you write a word

```bash
uv run bt find --quantity delta_net --excludes-zero --min-abs 0.05 --sort abs --limit 15
uv run bt runs --match 'ms*' --has belief_summary.yaml
uv run bt show factory_farming/ms3p_arms
```

`bt find` searches every recorded estimate in every run — the only way to see across 270 run
directories, since nothing else in this repo can. Recognise estimates structurally, so a
quantity nobody registered still turns up.

**Let the data pick the note.** A claim you arrived with will find support; a claim that
falls out of `bt find` is one the results actually make. The best notes come from a
comparison the tool surfaced — a cell that scatters where its neighbours do not, a ratio
whose stability differs from its sibling's.

## 2. Gate first, and read the flag source

`bt` prints a flag column on every line that names a run. Believe **nothing** from a flagged
arm — a collapsed arm still produces plausible numbers, and a voided run directory is
byte-identical in shape to a valid one.

Two things about flags worth knowing before you trust a clean one:

- They come from three places, because no single one is complete: a `VOID.md` in the run
  directory (only 2 runs have one), `STATE.md`'s void table (names 7), and any recorded
  `passed: false` (catches 13, including runs the other two miss).
- A flag names a **reading**, not a run. `matrix_v1` carries a gate failure at its endpoint;
  `matrix_v1_step24` is clean and quotable. `bt show` prints the pointer where the failure
  was recorded so you can tell which case you are in.

`bt runs` skips the gate scan for speed and says so. `bt show RUN` pays for it.

## 3. Build the ledger as you read, never afterwards

Every number in the note cites a short key; the key resolves through `sources.yaml`. Refs
never go inline — `factory_farming/ms3p_arms#belief/delta_net` mid-sentence is unreadable.

```bash
uv run bt show factory_farming/ms3p_arms --pointer '#belief/delta_net'
```

That prints a `sources.yaml entry:` block ready to paste, plus the three roundings the
checker will accept (`+0.1190 or +0.119 or +0.12`). **Never hand-construct a ref or retype a
value.** The snapshot `value` and `sha` it includes are load-bearing: `data/results/` is
gitignored and synced separately, so the note will be read where the artifacts are absent,
and a re-run stage overwrites a run directory in place. The sha is what turns that into a
reported `DRIFT` instead of a silent pass.

**Declare your arithmetic, do not just state the answer.** A note is mostly comparisons, and
no ratio or spread lives in any artifact:

```yaml
derived:
  length_ratio_s42: {expr: short_dense_s42 / long_dense_s42, value: 2.1744}
  spread: {expr: "max(a, b, c) / min(a, b, c)", value: 2.984}
```

`bt check` re-evaluates each expression against the cited refs, so a transposed ratio is
caught and the error cascades to anything built on it. A snapshotted value alone would sail
through. This is not bookkeeping — it is the only check on the note's own arithmetic.

## 4. The five sections, and what each is for

```markdown
# <the finding, stated as a conclusion>

## Motivation
Three beats and **no more than about 80 words**: the project's goal (say it plainly — "The
goal of this project is..."), the uncertainty this work was chasing, one sentence handing
off to the insight. Without the goal the insight reads as a free-floating fact; padded, it
delays the only part the reader came for.

## Key Concepts
Definitions, units, symbols, and **formulas**. Write the formula for every derived quantity
the note quotes — `dB NET = (B(M+) - B(M-)) - (B(M0+) - B(M0-))` settles in one line what a
paragraph of prose would leave ambiguous. Free of measurements: a definition with a
measurement in it is a result wearing a definition's clothes. Constants inside a formula are
notation, not measurements; put formulas in backticks and the checker ignores them.

## Insight
A few sentences. One specific thing, why it is not obvious, and what follows from it.

## Figures
Charts, tables, diagrams, each with a caption that says what to look at.

## Margin
Notes, citations, questions, guidance. Where the note says what it does not know.
```

**Key Concepts comes before Insight.** The Insight is the one section a reader has to get
through without stopping, so every symbol it uses should already be defined. Definitions
after the claim are definitions that arrive too late.

`Margin` is not a limitations section to be padded. It is where the next session finds the
cheapest experiment, the alternative you did not rule out, and the thing you would check
first if the note turned out wrong. Write what you deliberately did not conclude.

**The title is a conclusion, not a topic and not a maxim.** It should be a claim you could
say out loud, and it should make sense at a glance to someone who has not opened the note.
Subject, verb, object — then a number if the finding has one.

| | |
| --- | --- |
| ✗ maxim | "A ratio is only as stable as its denominator" — could head any note in any field |
| ✗ topic label | "Notes on corpus form and belief" — names the subject, states nothing |
| ✗ compressed | "Length is worth 2.3x; density has no quotable magnitude" — worth 2.3x of *what*? Needs the note to parse |
| ✓ conclusion | "Document length gives a quotable 2.3x belief-effect ratio; premise density does not" |
| ✓ conclusion | "SFT dataset format shifts belief scores against a matched control" |

If the title would survive being moved to a different note, it is not specific enough. If a
reader has to open the note to know what it means, it is not a conclusion yet.

**Keep it short.** A note is scaffolding, not a paper: if a sentence does not carry a number,
a definition, or a decision, cut it. Two sentences of framing beat a paragraph.

## 5. Figures and tables: spec, print, look, iterate

A figure is a small spec whose every plotted value is a **ref**. A literal number would be a
value in the deliverable that nothing can trace.

```yaml
# insights/<slug>/figures/cells.fig.yaml
kind: forest                      # or: lines
title: Netted belief effect by corpus form
xlabel: dB NET (probability)
zero_line: true
rows:
  - {label: "short, dense", series: seed 42, ref: factory_farming/ms3p_arms#belief/delta_net}
  - {label: "short, dense", series: seed 7,  ref: factory_farming/ms3p_arms_s7#belief/delta_net}
```

**`series` is the choice that decides whether a forest plot says anything.** Rows sharing a
`label` collapse into one slot, dodged, coloured by `series` — so a repeated measurement
(three seeds, two models) becomes a pattern you can see. Put the *variable the note is about*
in `series`. Colouring by the label instead encodes what the y axis already says and leaves
the interesting axis buried in label text: the first version of the figure above had eleven
rows with the seed spelled into each one, and the spread it was drawn to show was invisible.
Do not average the repeats away either — that erases the finding.

```bash
uv run bt figure --spec insights/<slug>/figures/cells.fig.yaml --print   # table, no image
uv run bt figure --spec insights/<slug>/figures/cells.fig.yaml           # writes cells.png
```

**Use `--print` first, every time.** It resolves every ref and tabulates the rows, and a
wrong order, a sign error, or a ref pointing somewhere unintended is visible there at about a
tenth the tokens of reading the PNG. Read the image once the table is right. The output path
is derived from the spec name so the two cannot drift apart.

Order rows deliberately — the renderer preserves your order, because that ordering is an
editorial decision.

### Tables are rendered too, never typed

A hand-typed table is where a note rots first: the prose gets updated when a number changes
and the table does not, and a wrong cell looks exactly as authoritative as a right one. So a
table is a spec plus a marker block.

```yaml
# insights/<slug>/figures/cells.table.yaml
kind: table
caption: Netted belief effect by cell at seed 42.
columns: ["", "sparse premises", "dense premises"]
rows:
  - ["**short** documents", {key: short_sparse_s42}, {key: short_dense_s42}]
  - ["**long** documents",  {key: long_sparse_s42},  {key: long_dense_s42}]
```

A cell is plain markdown text, or `{key: <ledger key>}`, or `{ref: <ref>}`. `format:` picks
`value` (signed, the default), `estimate` (value plus interval), or `plain`; `places:` sets
the decimals. Then leave an empty block in the note and fill it:

```markdown
<!-- bt:table cells -->
<!-- /bt:table -->
```

```bash
uv run bt render insights/<slug>/         # rewrites every block from its spec
```

`bt render` is idempotent, and `bt check` re-renders in memory and reports when a block has
drifted — so a stale table is a named defect rather than something a reader has to catch.
Run `render` after any ledger change, before `check`.

**For a paper, add `--latex`** and the same spec also emits `figures/<name>.tex`: a `table`
float with its caption and `\label`, ready to `\input{}`. Cell labels written in markdown
are translated (`**short**` becomes `\textbf{short}`).

```bash
uv run bt render insights/<slug>/ --latex
```

**Do not rasterise a table to an image.** It is tempting — it would make a table look like a
figure — and it loses everything that matters: an image cannot be searched or selected, it
does not diff, it typesets in the wrong font at the wrong size, `bt check` cannot scan its
numerals for drift, and `pdftotext` cannot extract it, which is how the paper's numeral
auditor verifies a PDF. One spec, two text emitters, is the whole point.

## 6. `bt check` before you hand it over

```bash
uv run bt render insights/<slug>/ && uv run bt check insights/<slug>/
```

It reports: every ref as `OK`/`DRIFT`/`MISSING`/`BAD_POINTER`/`UNUSED`; every declared
derivation re-evaluated; every decimal in the prose verified **at its own precision** (so
`+0.31` checks against the artifact rounded to two places — an honest rounding is not a
defect); flags on every cited run; drifted table blocks; and stale or unshown figures.

It is advisory and exits 0. `--strict` exits 1, for gating a commit.

And check the note's *shape* separately, because `bt check` has no opinion about it:

```bash
uv run python .claude/skills/write-insight/scripts/score_note.py insights/<slug>/
```

That grades the elements — sections and their order, title shape, Motivation's three beats,
Key Concepts staying free of measurements, whether the figure encodes the right dimension,
whether a table was typed instead of rendered, whether Margin points forward — and prints why
each one matters. What it CANNOT check is whether the title reads as a conclusion; that one is
on you. Zero
FAILs before you hand a note over. Treat the WARNs as questions to answer rather than boxes
to tick; a 1200-word note is sometimes right, and the warning is there to make you decide
rather than to stop you.

**Read the `not audited` line as carefully as the failures.** Bare integers, `16x`-style
derived ratios, and hedges like "roughly a third" are unauditable, so they are listed rather
than silently passed. An unaudited number that goes unmentioned is indistinguishable from a
verified one — that line is the note's blind spot, stated.

When something does not resolve, `bt check` searches every estimate in the tree and, if
**exactly one** matches at your precision, prints the ledger line to paste. It refuses to
guess among several. Fix the ledger, not the prose — rewording a sentence to dodge the
checker is the move this repo forbids.

## 7. Two things that are defects, not caveats

- **Two item banks in one comparison.** `bt find` and `bt check` warn when cited refs span
  more than one `suites_from`. Scores measured against different item banks are not
  comparable, and averaging them produces a number about nothing. Fix the comparison.
- **A ratio whose denominator straddles zero, or scatters across seeds.** A ratio inherits
  its denominator's instability rather than averaging it away. Quote a direction, not a
  magnitude, and say which.

## 8. A PDF, when the note is going somewhere else

```bash
uv run bt pdf insights/<slug>/          # writes insights/<slug>/<slug>.pdf
```

Named for the slug rather than `note.pdf`, because the file is going to someone's Downloads
folder where a generic name is worthless. The tables come from the same specs `bt render`
uses, re-emitted first, so the PDF cannot show a number the spec no longer produces. It also
appends a **Sources** list of every ledger key and the artifact pointer behind it — a shared
PDF travels without `sources.yaml`, and without that list the one property that makes a note
worth circulating is the property that does not survive sharing.

**Then look at the pages.** `--keep-tex` leaves the LaTeX in place if a compile fails.
Rendering is where the defects live that reading the markdown cannot show: the first note's
figure floated clear past the section that introduced it, a small table was magnified until
it dwarfed its own caption, and every straight `"` came out as a closing quote. All three are
fixed in the renderer now, so what remains for you to check is your own note — that the
caption says what the reader is looking at, and that a table's columns still fit.

Floats may reorder within a section (LaTeX queues figures and tables separately), but a
`\FloatBarrier` at every heading means one can never leave the section that explains it.

## Finishing

`insights/` is committed, figures included — the snapshots in `sources.yaml` are what make a
note readable on a box that has not pulled the results. If the note bears on an open
hypothesis, add its evidence line. Then wind up: record what the note claims and what
`bt check` said about it.
