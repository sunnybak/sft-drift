# Short-paper outlines — five iterated, three kept (2026-09-03)

Each outline: title candidates (expand → pick), abstract, problem, results the disk supports,
open questions. Numbers are at the quotability rung they earned (`GOAL.md` ladder); every one
traces to an `insights/` note except where marked *computed here*.

---

## 1. RATE — belief depth as a transfer rate  ✅ KEPT

**Title candidates**
- a. "Implanted stances are a rate, not a magnitude"
- b. "Belief depth for normative beliefs is a transfer rate: the same fraction on two topics and two axes"
- c. "How much of a fine-tuned stance survives? A fixed fraction of what the instrument can register"
- **pick: b**, shortened → *"A fine-tuned stance transfers at a fixed rate: ~40% of the prompted belief range, ~25% of the prompted decision range, on two unrelated topics"*

**Abstract.** Knowledge-editing work measures whether implanted *facts* are believed deeply;
normative beliefs are an explicit gap. We install stances by supervised fine-tuning on three
topics (an ethical practice, a software design default, a named product), at three seeds with
an off-topic control retrained per seed, and read them on belief banks and on nine action banks
at three inferential distances. Every instrument carries its own prompted range, measured on
the base model first. Expressed against that range, the two topics that install agree closely
— `T_B` 0.43/0.38, `T_A` 0.25/0.27 at one hop — where their raw effects never overlap across
seeds; the product topic installs nothing on instruments shown live. Stripping all supporting
evidence from the corpus leaves the belief rate unchanged (0.405/0.400). Depth is a rate, and
most of the apparent topic ordering is instrument range.

**Problem.** Belief-implantation results are reported as raw shifts on bank-specific scales, so
"topic A installs more than topic B" cannot be separated from "bank A has more room". Fact-
depth metrics don't transfer to stances, which have no truth value to probe for.

**Results (on disk).**
1. `T_B` 0.428 vs 0.376 (with evidence), 0.405 vs 0.400 (*computed*, without) — per-seed ranges
   overlap; raw `ΔB` ranges don't. [band]
2. `T_A` at hop 1: 0.245 vs 0.266; per-seed overlap; raw disjoint. [band]
3. Product: `S_B` +0.59, `S_A` +0.31, `T_B` −0.03, `T_A` 0.05 → real null, live instrument. [replicated direction]
4. Premise figures worth nothing: +0.2656 → +0.2512; +0.1655 → +0.1758. [band]
5. `propagation` 0.57 / 0.71. [direction; refused for product]

**Questions.** Is `S_B` post hoc? (Yes — disclosed; pre-registered test named.) Why does
software install and product not, at matched dose and form? Is the rate a property of the
adapter, the dose, or the model?

**Gaps to close before submission.** Hop ladder on the assertion-alone arms (~70 min); second
item batch; `S_B`-first on one fresh topic.

---

## 2. DISTANCE — further is louder  ✅ KEPT

**Title candidates**
- a. "Action grows with distance"
- b. "A fine-tuned stance moves the decision one inference away 4x more than the decision it is about"
- c. "Installed beliefs are most visible where the belief is not mentioned"
- **pick: b** (a is a topic label; c is a maxim)

**Abstract.** Where does an implanted stance show up in what a model recommends? We build
action benchmarks at three inferential distances from a belief — the decision *is* the belief
(hop 0), a practical choice one product step away (0.5), and a downstream commitment linked to
the belief by a single stated fact and named in neither option (1) — each judge-verified for
rung membership and each with its own measured prompted range. Read on fine-tuned arms with
matched controls, the netted action effect *rises* with distance on the two topics that
installed a stance (4.07x, 2.84x hop 1 over hop 0), and falls on the one that did not (0.50x,
0/3 seeds). At hop 0 the three topics are indistinguishable regardless of belief; at hop 1 they
separate. The belief is legible in the ladder's slope, not its level.

**Problem.** Knowledge-editing "ripple" evaluations find propagation decays with logical
distance; out-of-context-reasoning work finds fine-tuned facts do reach procedural behaviour.
Nobody has laid a stance on a measured distance ladder with per-rung sensitivity, so "belief
doesn't reach action" has never been separable from "the suite went blind at distance".

**Results (on disk).**
1. Ethics: +0.0305 → +0.0443 → +0.1238, all nine cells exclude zero, hop-1 seeds within 0.003. [magnitude-stable direction]
2. Per-rung `S_A` flat-to-rising (+0.42/+0.46/+0.51): not blindness. [gate]
3. Hop 0 topic-blind (+0.031/+0.063/+0.033); hop 1 separates (3/3, 3/3, 0/3 seeds). [band]
4. Not only headroom: hop 0 more saturated at BASE (0.665 vs 0.562) yet hop 1 leads on headroom share. [direction]
5. 26/27 cells sign-consistent with `S_A`; the exception is a null with machinery share 1.01. [reported]

**Questions.** Why does the rung where the belief IS the decision move least — saturation,
refusal-shaped caution, or item design? Does the rise continue at hop 2? Two of four rung
discriminators are vacuous (98–100% pass) — is the ladder really three rungs or two?

**Gaps.** Assertion-alone arms; second item batch (2026-08-20 showed batch variance can flip a
`ΔA` sign); a hop-2 rung.

---

## 3. LAWFUL — narrow finetuning generalizes predictably when the direction is measured first  ✅ KEPT

**Title candidates**
- a. "Emergent alignment: designed stances generalize lawfully"
- b. "Not emergent, not misaligned: a fine-tuned stance reaches distant decisions in the direction the prompted ceiling predicts"
- c. "Narrow fine-tuning generalizes predictably — if you measure the direction before you train"
- **pick: c**

**Abstract.** Narrow fine-tuning is reported to generalize broadly and unpredictably — insecure
code to misanthropy, sports teams to politics. We ask whether that unpredictability is the
phenomenon or the measurement. We install a designed stance on three topics and read it on
twelve instruments whose believer-side direction is fixed *before* training by a prompted
sensitivity measurement on the base model. Generalization is then lawful: 26 of 27 netted
action cells move in the pre-fixed direction; the two topics that install a stance reproduce
the same fraction of each instrument's range (0.25–0.27 one inference away, 0.57–0.71 of their
belief rate); the topic that installs nothing moves nothing on live instruments; and reach
grows with inferential distance rather than diffusing. The "emergent" in emergent
generalization may be an artifact of not knowing which way the model was going to go.

**Problem.** Safety-relevant generalization studies read behaviour on suites whose direction
and sensitivity to the trained trait are unknown, so surprising results cannot be separated
from instrument surprise.

**Results (on disk).**
1. 26/27 sign agreement with `S_A`; all 12 `S` exclude zero. [gate + count]
2. Binary install: ethics/software 3/3 seeds at hop 1, product 0/3. [replicated direction]
3. Same fraction on two topics, both axes. [band]
4. Rises with distance 4.07x / 2.84x; falls 0.50x without a stance. [direction]
5. Machinery share up to 1.01 where nothing installs — the control is doing the work. [reported]

**Questions.** Is lawfulness specific to *designed* stances with a natural believer-side, or
would EM-style corpora also read lawfully on `S_A`-gated suites? One base model; would a
reasoning model break the sign regularity? Where does the 27th cell come from?

**Gaps.** Same as above, plus this outline's central claim needs a comparison arm it doesn't
have: an EM-style or sports-style corpus read on `S_A`-gated banks. Without it the framing is
a contrast with the literature, not a test.

---

## 4. INSTRUMENT — forced choice reads ethics and little else  ❌ PRUNED

Title: "Reading beliefs out of a language model: forced choice reads ethical claims and nothing
else, and netting is what makes the rest interpretable." Abstract would lead with acquiescence
+0.24 vs +0.45–0.78 across seven families, Braun's opposite-signed finding (a no-bias), and the
D4/D7 netting that cancels it in `ΔB` by construction.

**Pruned because** it is a negative-methods headline — exactly the claim shape `PROPOSAL.md`
diagnosed as weak — and because its strongest content is *load-bearing infrastructure* for
outlines 1–3 (why `ΔB` is immune to acquiescence; why every instrument carries an `S`). It
survives as the instrument-validity section of whichever outline is chosen, and the seven-
family probe becomes one figure there.

---

## 5. RIPPLE — normative beliefs ripple where facts do not  ❌ PRUNED

Title: "Stances ripple, facts don't." Abstract would contrast knowledge-editing ripple failures
(Cohen et al.; RippleBench) and the knowing–using gap with our rising ladder.

**Pruned because** the contrast is across papers, models, methods and belief kinds at once; we
measure no facts ourselves. A reviewer's first question — "did you run a factual belief on your
own ladder?" — has no answer on disk. Folded into outline 2's related-work paragraph.

---

## Overall simplify

Outlines 1 and 3 share a spine (rate + lawfulness); 2 is the distinct, most surprising single
result. If one paper: **1 with 2 as its central figure**, and 3's framing in the discussion.
If the venue is safety-facing: **3**, with 1 and 2 as its two results sections. In every case
the assertion-alone hop reads are the first thing to run, because the user's emphasis is the
evidence-free installation and the action axis has not been read on it.
