---
name: write-paper
description: Write a grounded paper from measured results in the sft-drift belief-transfer repo using stage=writeup — make the evidence citable, declare contrasts, render and proofread the PDF. Use this whenever the user asks to write, draft, regenerate, revise, or proofread a paper, manuscript, abstract, or writeup from this project's results, mentions paper_*.yaml or out/<experiment>/<run_id>/, or says something like "turn this into a paper", "write it up", "make the PDF", "does the paper have the right tables". Also use it before hand-writing any paper-facing prose or LaTeX, because this repo has a renderer that ties every number to an immutable artifact and hand-written prose silently loses that guarantee.
---

# Write a paper

`stage=writeup` is not "ask a model to write a paper." It is a **grounded renderer**: you
declare pointers into immutable result artifacts, an author model may only write claims that
resolve to those pointers, a reviewer model audits every claim, and a validator rejects any
numeral that is not in the cited evidence. That is what makes the output auditable — a
referee can trace any cell back to the run that produced it.

The consequence, and it decides how your session goes: **most of the work is making evidence
citable, not writing prose.** And nearly every failure mode fails *after* the author model
has been paid for. Front-load the checks.

## 1. Decide what the paper claims, and check the claims are still true

Read `PAPER_AUDIT.md` (green/amber/red — what may be quoted and at what level), `PROPOSAL.md`
(the argument), and the hypothesis files behind each claim. `PAPER_AUDIT.md` rots: a claim
listed green may have been withdrawn by a later seed. Verify against the hypothesis file's
own resolution section before you build a contrast on it.

Write down the scope limits *now*, as config, not as prose you hope the author will add. A
scope limit invented at write-up time reads as damage control; one declared in the overlay
header is a design decision.

## 2. Make the evidence citable — this is the real work

A `ContrastSpec` selects `summary[<quantity>]` from one `*_summary.yaml` in one run
directory, and requires exactly this shape:

```yaml
run_id: <must equal the directory name, or collect_evidence raises>
<quantity>:
  delta: <float>
  ci95: [lo, hi]
  excludes_zero: <bool>
```

Two things follow. First, if your numbers live in a bespoke JSON (`af_ff_summary.json`,
`*_rows.jsonl`), they are **present but not citable** — transpose them into that shape.
Transpose, never recompute: the paper's authority comes from the numbers being the same
objects the experiment produced. `scripts/build_af_evidence.py` in the repo is the worked
example; derive only `excludes_zero`, from the recorded interval.

Second, the loader only reads filenames it recognises, and a new kind of reading needs its
name added — one line in `analysis/writeup/evidence.py`, whose comments say which of the two
lists to add it to and why. Read them there rather than trusting a copy here.

**Contrast `id`s can be load-bearing, not just labels.** Some asset builders parse structure
out of the id (`plots.af_facts` does), so a free-form id resolves nothing and `build_assets`
raises *after* the prose is written. If a builder consumes your facts, name the contrasts the
way it parses them — check the builder, since the grammar is its business and changes with it.

An arm-derived contrast (`positive_arm`/`negative_arm` + both control arms) computes
`(pos − neg) − (ctrl_pos − ctrl_neg)` from recorded arm scores and produces **no interval**.
That is correct and the table says so; do not let the author imply one.

## 3. Write the run overlay

Copy an existing `configs/run/paper_*.yaml`. Put the scope decisions in a header comment —
future readers need to know what you deliberately excluded and why.

```yaml
writeup:
  author_model: gpt-5.6-sol        # SET THIS. Both model fields default to the cheap
  reviewer_model: gpt-5.6-luna     # model, which fails the deterministic plan contract
                                   # ("assets placed more than once") on all three
                                   # retries. Every paper in out/ that compiled uses
                                   # sol as author and luna as auditor.
  source_runs: [...]               # every run any contrast cites
  primary_reading: <run_id>        # must appear in source_runs
  trajectory_run: null             # null unless you truly have trajectory.jsonl
  contrasts: [...]
  min_main_tables: 1               # see the traps table before raising this
  min_main_figures: 1
```

**`contribution_goals` is your main lever on the prose.** It is where you say what the
abstract must open with, what must be reported as unresolved, and what may not be claimed.
Be specific — "report the delta-predictability cells as an unresolved seed contradiction
rather than as a working repair" produces a different paper than "discuss limitations."

## 4. Dry-run the evidence BEFORE spending on the author

This is the single highest-value habit here. It costs seconds and catches most failures:

```bash
uv run python .claude/skills/write-paper/scripts/check_evidence.py +run=<paper_run_id>
```

It composes the config, resolves every declared contrast, and prints each fact with its
interval and zero-exclusion. A contrast that cannot resolve fails here instead of after the
prose is written and paid for.

## 5. Run it

```bash
uv run python run.py +run=<paper_run_id> stage=writeup
```

Prompts are cached, so a re-run after a *code* change is nearly free. `force=true` bypasses
the cache — use it only when you changed a prompt and want fresh text, not as a reflex.

## 6. When the auditor rejects, fix the claim — never the auditor

Three correction rounds run automatically; then the stage raises. Read the findings:

```bash
uv run python -c "import json; d=json.load(open('out/<exp>/<run_id>/review.json')); \
print(d['approved']); [print(f['claim_id'], f['status'], f['detail']) for f in d['findings'] if f['status']!='supported']"
```

The auditor is usually right, and its objections are the ones a referee would raise. Real
examples from this repo, with the fix that worked:

- *"no separation from the baseline"* has no stated criterion → say which criterion, in the
  claim: "each method's interval **overlaps** the baseline's in the same cell; no pairwise
  contrast was computed, so this is not a significance test."
- *"no retrieval scores were computed"* is an empirical assertion about an absence, citing
  nothing → reframe as a scope declaration about what the evaluation covers.
- An unqualified ordering claim whose intervals straddle zero → carry the qualification into
  the claim, not just the prose.

Weakening the validator to make a paper pass is the move `AGENTS.md` forbids. Fix the claim,
or fix the evidence, or drop the claim.

## 7. Proofread by rendering the pages — reading the LaTeX is not enough

Defects that only appear rendered: captions, float placement, table numbering, oversized
tables, double punctuation.

```bash
pdftoppm -r 110 -png out/<exp>/<run_id>/paper.pdf /tmp/page   # then Read each /tmp/page-N.png
```

Look for: does the abstract still contain the claim the paper turns on; do the figures have
real captions rather than the planner's instruction outline; are tables numbered in reading
order; is the same estimate printed in four sections.

**Count the rows of any long table against the facts it should contain.** A `table` float
cannot break across pages, so a ladder past roughly 24 wrapped rows is **silently clipped** —
rows vanish from the PDF with nothing but an overfull warning in the log. The renderer now
paginates such tables as a `longtable`, but verify rather than assume: a clipped table is the
one defect that looks perfect on every page you read, because the missing rows leave no
trace.

## 8. Audit the numerals mechanically

Reading every page catches prose defects; a script catches transcription. `synthesis.json`
is the authoritative set of values the paper is allowed to contain:

```bash
uv run python .claude/skills/write-paper/scripts/audit_numerals.py out/<exp>/<run_id>
```

Anything it flags is either a number the author invented or a number you failed to declare.
Both matter. "Every numeral traces to a declared artifact" is the sentence that makes the
paper defensible, and it should be in the changelog entry.

**Know what this does not check: it validates the numbers that are present, and says nothing
about numbers that are missing.** A clipped table passes it perfectly. Check presence too:

```bash
uv run python -c "
import json,subprocess
d='out/<exp>/<run_id>'
syn=json.load(open(f'{d}/synthesis.json'))
txt=subprocess.check_output(['pdftotext',f'{d}/paper.pdf','-'],text=True)
miss=[f['id'] for f in syn['facts'] if f\"{f['value']:.4f}\" not in txt]
print(f'{len(syn[\"facts\"])} facts; missing from PDF:', miss or 'NONE')"
```

## Traps, each of which cost a real run

| symptom | cause and fix |
| --- | --- |
| `contrast X cannot select Y` | the quantity is missing, or lacks `delta`/`ci95`. Dry-run first (§4) |
| `contains unsupported numbers: ['1']` | a **non-empirical** claim with no evidence refs gets an empty excerpt, so *any* numeral in it fails. Keep definitions and framing numeral-free; put the formula in prose |
| `writeup auditor rejected the corrected manuscript` | three rounds failed. Read `review.json` and fix the claim (§6) |
| `assets placed more than once: [...]` after three retries | `author_model` is the cheap model. Set `gpt-5.6-sol` as author; it is the one that satisfies the plan contract |
| `asset 'af_...' requests an af_figure but no af_ contrasts resolved` | a contrast id the figure builder cannot parse — see the naming note in §2 |
| `requests a trajectory figure but none was built` | the planner asked for one with `trajectory_run: null`. Set a real trajectory run or leave it null and let the validator drop the asset |
| YAML goal parsed as a dict | a `: ` inside a `contribution_goals` entry. Quote the whole string |
| `Table 2` printed before `Table 1` | a full-page float in the main text migrates past its own discussion. A ladder table over ~12 contrasts belongs in the `appendix`; don't force it into main text with `min_main_tables` |
| a long table renders but rows are missing | a `table` float cannot paginate and clips silently past ~24 wrapped rows. Rendered as `longtable` now; verify with the presence check in §8 |
| an exact sentence you demanded never appears | goals that ban a phrase lose to the author's topic-sentence habit; goals that say "the paragraph OPENS with this sentence, verbatim: ..." win |
| a validator rejects something that looks legitimate | read the exception, then read the validator. Several of its categories are counter-intuitive by design (a non-empirical claim may hold no numerals at all; procedure statements are audited for contradiction rather than citation). The rule is in `analysis/writeup/validate.py`, which owns both the check and the numeric surface it checks against |
| `tectonic` not found | `make tectonic` (it is part of `make setup`, so a set-up box already has it) |

## Related work and bibliography (the one hand-written section)

The grounded renderer cannot produce related work: no artifact can support a claim about
prior work. The pipeline's answer is `writeup.related_work_tex` (raw LaTeX, rendered
verbatim after the introduction, outside the claim validator and the auditor) plus
`bibliography_path` (a curated `.bib`, e.g. `configs/run/paper_attribution.bib`). Write it
by hand against `LITERATURE.md` -- its provenance guarantee is that file's deep-read
verification record, not the evidence bundle. Use `\citep`/`\citet` (the template loads
natbib with `plainnat`); `\citet` under plain.bst renders "(author?)". Tell the author
model, in a goal, NOT to name papers, authors, years, or venues in the authored sections --
the injected section carries all of it. `audit_numerals.py` checks bibliography numerals
(arXiv ids) against `references.bib` and everything before the References heading against
the synthesis.

## Finishing

`out/` is git-tracked and **not** synced to HF — a rendered paper is a deliverable with a
different lifecycle from experimental data. Commit the whole output directory (prior papers
commit `evidence.json` too). Then wind up: the changelog entry should record what the paper
claims, what you deliberately scoped out, and the numeral-audit result.
