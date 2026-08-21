# IDEAS

A backlog of directions worth trying that are **not yet falsifiable claims** — the
pre-hypothesis stage. `hypotheses/open/` is capped at three and reserved for standing
claims with a registered falsifier; most good ideas start out vaguer than that, and this
file exists so a vague-but-promising idea has somewhere to live besides a changelog entry
that ages out of the "recent enough to read" window, or getting prematurely inflated into
a hypothesis file just so it isn't lost.

**Not read every session.** This is not part of the orient step (`GOAL.md` step 1) —
consult it when choosing a *widen* move, or when portfolio discipline flags a stale axis
and the cheap local experiments have run out. Reading three hypothesis files is supposed
to be fast; this file is a messier list, but not an unbounded one — see the cap below.

**Every idea has an exit, not just an entry.** An idea here either:
- graduates into a real hypothesis file once it's sharp enough to falsify (move it, don't
  copy it — delete the entry here), or
- gets struck through with a one-line reason it's not worth pursuing, rather than being
  silently deleted (so the next session doesn't re-suggest it without knowing it was
  already considered and passed on).

A backlog that only grows is worse than no backlog — prune it the same sessions you add
to it.

**Hard cap: 1000 words, whole file.** Enforced, not aspirational — check before adding
and trim if the addition would push it over. When at the cap, adding a new idea means
first graduating, cutting, or compressing an existing one to make room, the same
discipline `hypotheses/open/`'s cap-of-three already applies one level up. A shorter,
sharper list is more useful here than a complete one: this file is a memory aid for
"what was worth trying," not an archive, and archive belongs in `changelog/` (which
already records why an idea was added or dropped, dated) — trimming an entry here loses
nothing that isn't already recoverable there.

## Format

```markdown
### <short title> — added <date>
<a paragraph, not a hypothesis writeup: what it is, why it might matter, rough cost>
```

---

### Predictive scoring for corpus belief-installation propensity — added 2026-08-21

This project already has ~10 measured (form x density x voice x assertion-level)
conditions with known `ΔB` (the length/density cross, `Ms3p`, `Me`, etc.). A retrospective
regression/correlation of surface features against measured effect, over data already on
disk, would produce an actual predictive scoring function for "will this corpus move
belief" — zero new GPU/API spend. If it also correlates with `Δ-predictability` (the one
attribution method that tracks the true causal effect, ρ +0.77/+0.83), that reuses
validated machinery for a second job instead of building new tooling. Feeds H8 (what
predicts the assertion-ladder effect) rather than standing alone.

### Inference-time thinking probe on existing checkpoints — added 2026-08-21

`enable_thinking` is already wired into `inference/model.py` (default `False`, tested).
Re-score the existing evidence-only checkpoints' belief suite with thinking enabled: if a
belief exists but doesn't surface in a snap forced-choice, extended reasoning at eval
time might pull it out. Same-day, no new training. Directly tests H4's "rendering-only"
account (`supported/`) — a positive result here would be a real challenge to a resolved
hypothesis, worth reopening rather than just noting.

### CCS-style internal-belief probing — added 2026-08-21

Contrast-Consistent Search (Burns et al.) or a similar linear probe on residual-stream
activations, to check whether an internal "belief direction" forms during training even
when the forced-choice behavioral readout shows nothing. Moderate cost (activation
extraction + a small probe, no retraining). The sharpest available test of whether H4's
"nothing is inferred at all" is literally true or whether there's a latent representation
that just doesn't surface behaviorally — those are different findings and current
instruments can't tell them apart. Pairs naturally with the thinking-probe idea above;
worth doing both before writing up whichever one moves.

### Assertion-ladder threshold vs. linear-ramp — added 2026-08-21

The existing three points on the assertion axis (long-form evidence null -> short-form
evidence `Ms3p` +0.12-0.14 -> explicit stance `Me` +0.31-0.35) could reflect a smooth ramp
or a sharp threshold between "evidence" and "assertion." A graded ladder of intermediate
manipulations (hedged evaluative aside -> third-person-attributed conclusion -> first-
person opinion) would distinguish them. Mostly a refinement of `supported/H13`; only
worth its own hypothesis file if sharpened into a specific threshold-vs-ramp claim rather
than "more points on the curve would be nice."

### Which belief items move, and why — added 2026-08-21e

`H24` left behind a fact it could not explain: 4B's per-item netted `dB` has SD ~= its mean
(rel. dispersion ~1.0), i.e. a few items move enormously and others barely — while 8B moves
everything moderately. Base extremity explains only part of it (1.02 -> 0.82 after
residualizing). The per-item pattern is highly reproducible (cross-seed rho ~0.95 at both
models), so it is a stable property of items, not noise, and n=42 with facet/layer/framing
metadata is already on disk. Predicting *which* items move from item properties is
attribution-adjacent and free. Not yet a hypothesis: no candidate predictor is sharp enough
to falsify.

## Ready to graduate whenever wanted

- **Reasoning-trace SFT as a belief lever** — genuinely hypothesis-shaped already: "an
  explicit inference-drawing target in the SFT data (a `<think>` block that performs the
  premise -> conclusion step), without personal-opinion framing, is sufficient to move
  belief." Distinct from everything currently open. Not written up as a full hypothesis
  file only because `open/` was at the cap when this list was created — say the word and
  it's ready to move in, trading against whichever of H8/H18/H19 is least active then.
