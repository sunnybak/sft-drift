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

~10 measured (form x density x voice x assertion) conditions with known `ΔB` sit on disk. A
regression of surface features against measured effect yields a "will this corpus move
belief" score for free. **2026-08-23:** see the dose moonshot below.

### Inference-time thinking probe on existing checkpoints — added 2026-08-21

If a belief exists but does not surface in a snap forced choice, extended reasoning at eval
time might pull it out; a positive result would challenge `supported/H4`. **Corrected
2026-08-23: NOT the same-day config flip this entry claimed.** `enable_thinking` reaches the
chat client, not the scoring path, and the suite is scored by log-probability over
single-token labels (D1). It needs a new eval path — generate a trace, then score labels with
it in context — which is a D1 departure to argue for, not assume.

### CCS-style internal-belief probing — added 2026-08-21

A linear probe on residual-stream activations, to see whether an internal belief direction
forms even when the behavioural readout shows nothing. Moderate cost, no retraining. The
sharpest test of whether `H4`'s "nothing is inferred" is literally true, or whether a latent
representation never surfaces. Pairs with the thinking probe.

### Which belief items move, and why — added 2026-08-21e

4B's per-item `dB` has SD ~ its mean while 8B moves everything moderately; base extremity
explains only part of it, and the pattern is reproducible (cross-seed rho ~0.95). n=42 with
facet metadata is on disk. Free, attribution-adjacent. No predictor sharp enough to falsify yet.

## Moonshots — added 2026-08-23

Logged after `H30` was falsified by a purpose-trained retriever scoring rho +0.94 on the
installed ladder. None is a hypothesis yet.

### Does ranking fidelity ever convert into removal? AF(E5)

Two methods now rank the ladder at rho ~ +0.94 — Δ-predictability and E5 — and the only one
whose AF was measured posts a **seed contradiction**. AF(E5) at a dose-matched budget decides
whether production retrieval is operationally useful or merely well-correlated: the sharpest
form of "ranking is not removal" available. Needs full fine-tuning, so >=48GB. **If AF(E5) is
high the thesis narrows hard; if near zero it generalises from gradients to all content-keyed
methods.**

### Is AF a dose variable in disguise?

Measured 2026-08-23 on the full-FT sweep: AF is monotone in how much *installed potency* a
removal set contained (spearman +0.86/+0.76), and the fit crosses zero near 33% — so methods
removing less land negative *by construction*, which is exactly the "counterproductive"
headline. The implication is the moonshot: if AF is fully explained by removed potency, then
per-method AF comparisons — **ours and the LDS/datamodels literature's** — measure dose, not
attribution. Testable by construction: build removal sets at matched potency from scrambled
rankings; if AF is unchanged, method identity contributes nothing. (Weak at LoRA, rho +0.41,
so this needs the big box too.)

### Attribution-evading training data

Form carries potency; content-keyed methods key on content. That is a *constructive* recipe,
not just a negative result: engineer a document that maximally moves belief while scoring at
the bottom of every attribution method. The finding would stop being "attribution is
imprecise" and become "attribution is evadable" — the threat model the emergent-misalignment
attribution literature actually cares about. The pool has the ingredients and the null cell is a
proof of concept. Highest safety relevance here, and easiest to overclaim: needs adversarial
review before it is written anywhere.

### Does an audit on one model say anything about another?

Install the same effect in two or three model families and ask whether any method's ranking
transfers — whether an audit on model A licenses any claim about model B, the assumption every
deployed attribution pipeline makes silently. `H29`'s cross-family reference is suggestive; the
4B/8B dissociation warns it may not. Expensive.
