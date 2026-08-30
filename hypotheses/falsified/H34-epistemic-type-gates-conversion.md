# H34: The epistemic type of a claim gates how much exposure converts into installed belief

**Status: FALSIFIED 2026-08-30b**, by the test it registered, on the first reading.
Originally registered **2026-08-30b on user approval**, before any item of the new bank
exists and before any number from it has been read. Proposed in an earlier cycle and
deliberately held unregistered until approved; **refined on registration** in three ways the
intervening work made necessary — see "What changed since it was first proposed".
**Bears on:** `insights/conversion-rate-not-detection/`, the standing account of why netted
`dB` differs ~30x between topics.
**Successor to:** the conversion decomposition, which established the pattern this explains.

## The claim

Seven cycles established that netted `dB` factorises as

```text
dB  ~=  exposure-sensitivity  x  conversion rate
```

where exposure-sensitivity is set by corpus type (an explicit corpus saturates every belief
suite measured, 0.7484 to 0.9760) and **conversion** — the fraction surviving training — is
ordered by topic: ethics 1.4232 / 0.3388, architecture 0.2274 / 0.1471, product 0.0963 /
0.0147, the same ordering in both corpus families.

That ordering tracks how much of a fact of the matter the claim has. An ethical proposition
has none to contradict; a contested technical default has some; a checkable empirical claim
about a real named product has one the model already holds.

> **Claim:** conversion is gated by the **epistemic type of the claim**, not by the topic.
> Holding the domain fixed and varying only whether the claim is empirical or evaluative
> reproduces the ordering.

**Topic and epistemic type are perfectly confounded in every measurement so far** — each of
the three topics contributes exactly one kind of claim. That confound is what this exists to
break.

## What changed since it was first proposed

Registered honestly, because the earlier proposal's design would now be misleading:

1. **The falsifier is stated on conversion, not on raw `dB`.** The account is about the
   conversion rate; comparing raw `dB` would inherit exposure differences between banks and
   test the wrong thing.
2. **The exposure baseline is built in, not bolted on.** `H33` was falsified by exactly this
   omission: on two of three topics the suite responds several times more to the corpus being
   present than to having trained on it. Any new bank must have its `Mc` reading taken in the
   same pass, or its trained numbers cannot be interpreted.
3. **Framing mix is controlled by construction.** Explicit corpora move third-person
   propositions more and evidence corpora move first-person opinions more (3/3 seeds on both
   decisive topics), so two banks with different framing mixes are not comparable. The new
   bank carries the **same three framings** as `po_suite_belief` and the empirical and
   evaluative halves draw from the same framing pool.

## The design — one bank, two halves, matched

A single new belief bank in the **phone domain**, built in one generation pass, with facets
deliberately split:

- **empirical half** — claims with a fact of the matter (does the hardware last, does the
  battery hold up, is the failure rate what it is)
- **evaluative half** — claims with no fact of the matter in the same domain (is the
  manufacturer open to criticism, are buyers treated fairly, is this acceptable practice)

Both halves share one domain, one generator, one gating pass, and the same framing pool, so
the only thing that differs between them is the epistemic type of the claim.

**Stage A (this run).** Score the **already-trained** `po_ev_arms{,_s7,_s123}` and
`po_ex_arms{,_s7,_s123}` on the new bank, plus its `Mc_ev` / `Mc_e` exposure readings. No
training. This asks the eval-side half of the question: do the same trained arms convert
better on evaluative items than on empirical ones, on items designed for the contrast rather
than on the incidental `core`/`assessment` split?

**Stage B (only if Stage A supports it).** Build matched evaluative corpora and train six
arms, which asks the corpus-side half: does an evaluative *corpus* install better than an
empirical one in the same domain.

## Registered falsifier — written before the bank exists

**The claim dies if the evaluative half's conversion does not exceed the empirical half's on
BOTH trained families (evidence and explicit), at a majority of the three seeds each.**
Conversion is `dB NET(half) / exposure(half)`, both measured on the same items of the same
bank, so the comparison is within one bank and free of the cross-bank problem that makes
topic magnitudes incomparable.

**Registered readings, so none can be chosen afterwards:**

1. **Evaluative > empirical on both families.** Claim supported. Epistemic type gates
   conversion within a fixed domain, the topic/epistemic-type confound is broken, and Stage B
   becomes worth its cost.
2. **Evaluative > empirical on one family only.** Claim NOT supported as stated. Report the
   split and treat it as an interaction with corpus type rather than a clean gate; Stage B is
   not run on this evidence.
3. **No difference, or empirical > evaluative.** Claim falsified. The conversion ordering
   across topics is then something other than epistemic type — corpus register and the base
   model's prior strength are the two live alternatives — and the standing account in
   `insights/conversion-rate-not-detection/` gets a correction naming this as the test that
   failed it.

**Do not read a raw `dB` difference between halves as support.** The halves will differ in
exposure — that is expected and is precisely why conversion is the registered quantity.


## DESIGN REVISED after the pilot, before any conversion number was computed

**2026-08-30b.** The pilot (`pe_suite_pilot`, 24 items) was read by eye per `GOAL.md` step 3
and **failed** — usefully. The design above called for a new phone-domain bank split into an
empirical and an evaluative half. The generated "empirical" items came back evaluative
("acceptably reliable", "it is reasonable to expect", "it is unacceptable when") and the
evaluative items came back justified by factual claims ("treated fairly *because these phones
can remain reliable for many years*"). Both halves were contaminated and the contrast would
have been meaningless.

The cause is not a bad prompt but the generator's design: `belief_item_template` requires
"a normative or evaluative claim -- a judgment of value, acceptability, justification, or
blame -- **never a factual or statistical one**". A belief bank cannot contain an empirical
half; the template forbids it.

**The contrast already exists in the repo, built deliberately and with the opposite
constraint.** `inference_item_template` requires "a DESCRIPTIVE claim -- an assertion about
what is factually the case -- **never a judgment of value, acceptability, justification, or
blame**". The belief suite IS the evaluative half; the descriptive-inference suite IS the
empirical half. They are two banks over the same topics, scored on the same arms, and
`AGENTS.md` states `dI` is "parallel in construction to `dB` and comparable to it in
probability units on the same arms".

**So the design changes and the falsifier changes with it**, and both are being written down
**before any conversion number has been computed** — the pilot produced items, not readings.

**Revised Stage A.** For each topic and each trained family, compare conversion on the
**belief** bank (evaluative) against conversion on the **inference** bank (empirical), where
conversion is `dB NET / exposure` and `dI NET / exposure` respectively. The belief exposures
already exist (`Mc_ev`, `Mc_e`, six cells). The inference exposures do not and are the only
new measurement: six in-context runs, no training, no API spend.

**Revised falsifier.** *The claim dies if conversion on the evaluative bank does not exceed
conversion on the empirical bank, on both trained families, at a majority of seeds each.*
Same structure as before; the halves are now two banks rather than two halves of one, so the
comparison is across banks and the caveat below applies.

**The null facet is excluded from the inference side**, in both the numerator and the
exposure. It is null by construction and including it would dilute the empirical half only —
an asymmetry that would bias the test toward the claim.

**A caveat this revision introduces, stated because it is a real cost.** The original design
compared two halves of ONE bank; this compares two banks. Banks differ in more than epistemic
type — item count, gating history, and saturation — so a difference between them is weaker
evidence than a difference within one would have been. What makes it worth running anyway is
that the two banks were built with *explicitly opposite constraints on exactly this axis*,
which no pair of banks in the project was designed to give and this pair was.

## What the pilot cost and what it saved

24 items, about $0.02. It prevented a full bank build whose contrast would have been
contaminated in both directions and, worse, would have looked fine to every automated check.
`pe_suite_pilot` and `configs/experiment/product_epistemic.yaml` are kept as the record.

## Prerequisite gates

1. **The bank must gate at all**, at a yield comparable to `po_suite_belief`'s (146 of 216),
   and the two halves must survive gating at comparable rates. A gate that drops evaluative
   items preferentially would leave the halves unmatched, which is worse than a low yield.
2. **Read a pilot by eye before scaling** (`GOAL.md` step 3). The evaluative half is the half
   that can go wrong: an item that smuggles in a factual claim is an empirical item wearing
   evaluative clothes, and would collapse the contrast.
3. **Headroom must be checked per half.** The product belief bank is the most saturated in the
   project (80 of 292 arm-items pinned). If one half is markedly more saturated than the other,
   conversion is not comparable between them and the reading is withdrawn rather than
   caveated.
4. **Same arms, same checkpoint, same control.** `checkpoint-24`, netted against `ms0_arms` at
   each matching seed, exactly as the existing product readings are.


## Evidence — the falsifier fired, outcome 3

**2026-08-30b.** Conversion on the evaluative bank (belief) against the empirical bank
(inference, null facet excluded from both numerator and exposure), same arms, same
checkpoint-24, same per-seed controls:

| topic | corpus | evaluative conversion | empirical conversion | eval > emp |
| --- | --- | --- | --- | --- |
| architecture | evidence | 0.2274 | 0.1589 | 2/3 seeds |
| architecture | explicit | 0.1470 | 0.1251 | 3/3 seeds |
| **product** | evidence | 0.0962 | **0.1111** | **1/3 seeds** |
| **product** | explicit | 0.0147 | **0.0237** | **1/3 seeds** |

The registered kill condition was "dies if the evaluative bank's conversion does not exceed
the empirical bank's on BOTH trained families, at a majority of seeds each". On architecture
it holds on both families. **On product it fails on both, and reverses** — the empirical bank
converts better. Outcome 3 of the three registered readings.

**Only two topics contributed.** factory_farming's inference bank (`evalgen_inference_v2`) is
on neither disk nor HF — it was cleared in the 2026-08-29a purge — so that topic could not be
included. Four cells, not six. This is a real limitation of the test and not a reason to
reread the result: the two topics available disagree with each other, which is enough to kill
a claim that says the effect is *not* topic-dependent.

## What this falsification corrects, and it is the more valuable half

**A cycle-7 interpretation of mine was wrong, and this test is what caught it.** I had
reported that evaluative (`assessment`) facets converted better than descriptive (`core`)
facets in 4 of 4 cells, with the gap largest on the product topic "where `core` genuinely is
empirical". That reading was mistaken. The belief item template requires **every** item to be
"a normative or evaluative claim ... never a factual or statistical one", so the belief bank's
`core` facets are evaluative too — "whether these phones are durable enough" is an opinion
item, not a factual one. The `core`/`assessment` split is a split in **inferential distance
from the premises**, which is what it was designed to be, and never was an epistemic split.

So the layer result stands as a layer result and is withdrawn as evidence about epistemic
type. With a genuine epistemic contrast — two banks built under explicitly opposite
constraints — the effect does not replicate and reverses on one of the two topics.

## Where that leaves the standing account

`insights/conversion-rate-not-detection/` establishes that conversion is ordered
ethics > architecture > product, replicated in both corpus families. **That ordering is
untouched by this** — it is a measurement, and nothing here bears on it. What is removed is
its *explanation*. Epistemic type was the account offered for it, and the account is now
falsified.

Two candidates remain and neither has been tested:

- **corpus register** — how the training text reads, independent of what kind of claim it
  makes;
- **prior strength** — how firmly the base model already holds a position on the claim, which
  is what the fictional-twin design (P7) was built to isolate and which no measurement in this
  project has yet varied.

**Successor:** none registered. The project is in its terminal phase and the honest reporting
position is that the conversion ordering is measured and its cause is unexplained.

## What it predicts next

**If supported:** the project's account of its own 30x spread becomes a claim about claim
types rather than about topics, which is a far more general statement and one a reader can
apply outside these three subjects. Stage B tests whether it holds on the corpus side too.

**If falsified:** the conversion ordering is real but unexplained, and
`insights/conversion-rate-not-detection/` must say so. The next candidates are corpus register
and prior strength — the latter is what the fictional-twin design (P7) was built to test.
