# H4: Evidence-only SFT produces recall of the trained text and no inference from it

**Status:** supported — 2026-08-19 — **but its INFERENCE half is WITHDRAWN as of
2026-08-21e.** The belief half stands. The `ΔI` half rests on an instrument whose positive
control was tested properly for the first time that day and **failed**.
**Bears on:** contributions 2 and 3 — this is the paper's claim

## AMENDED 2026-08-21e — do not quote the "a fifth" ratio

The claim block below calibrates itself on two ratios. **One survives and one does not.**

- **SURVIVES — the belief ratio.** Evidence-only moves normative belief by roughly a
  fortieth of explicit assertion (+0.008 vs +0.311/+0.353). The belief suite is unaffected by
  what follows, and `H26` (2026-08-21e) additionally clears these specific arms: the explicit
  factory_farming family's machinery-to-raw ratio is 0.11–0.40 and its netted readings
  replicate across seeds (relative spread 0.11–0.12, sign holds).
- **WITHDRAWN — the `ΔI` ratio ("a fifth", +0.012 vs +0.062/+0.075).** On
  `inference_v1_step24`'s explicit-stance arm — the suite's designated POSITIVE CONTROL —
  the byte-identical null-control facet is the **highest-moving facet of all eight**
  (+0.1469 against the all-facet mean of +0.0620; best differing-premise facet
  `injury_rate` +0.1045). The evidence arm's null facet (+0.0138) likewise sits at or above
  its all-facet mean (+0.0121). **Both terms of the ratio are dominated by a facet whose
  premises do not differ across polarities**, so the ratio does not measure
  premise-specific inference and must not be quoted as though it did.

**This does not falsify the hypothesis.** What it removes is the *quantitative* inference
leg. The qualitative inference evidence is independent of this suite and still stands: the
prose probes (`prose_probe_v2_step60`, `prose_probe_canon`, recorded in
[H7](H7-what-is-the-lever.md)) show the evidence arms cannot state their trained premises,
and that descriptive inference followed on only 1 of 4 facts even where retrievability
succeeded. So "recall without inference" survives as a **direction supported by two
independent instruments, one of which is now unquantified**.

Restoring the quantitative leg is exactly what [H25](../open/H25-inference-null-facet-is-unmeasurable.md)
is for. Until it resolves, the paper states the belief ratio and the prose-probe evidence,
and reports `ΔI` not at all.

## Claim

Absorption is rendering: the premises become more predictable to the arm, and nothing
propagates from them. Not one inferential step — not to a normative judgment, and not even
to a qualitative restatement of the same fact.

**Wording calibrated 2026-08-20 after the seed replication:** "nothing" is measurably too
strong. The evidence `ΔI` lands at ~+0.012 at BOTH seeds (42 and 7), and at seed 7 every
subset reading excludes zero — a small, consistent positive, not a boundary artifact. The
defensible form of the claim: evidence-only SFT moves descriptive claims by roughly a
**fifth** of what explicit assertion does (+0.012 vs +0.062/+0.075) and normative belief by
roughly a **fortieth** (+0.008 vs +0.311/+0.353), against prompted sensitivities two orders
larger. Dissociation in magnitude, not a literal zero. The paper should quote the ratios,
not "nothing".

## What would falsify it

Any measured downstream effect of the evidence corpora that is not recall of the trained
strings: a descriptive claim entailed but not stated, a normative judgment, or a decision.
Restricted to arms passing `choice_bench`, netted against a matched control.

## Evidence

- 2026-08-19 `inference_v1_step24`: `ΔI NET +0.0078 [−0.0001, +0.0174]`, with the explicit
  positive control at +0.0576 on the same items. Supports. **MLX-scored, superseded by the
  CUDA re-score below — cite that one.**
- 2026-08-20 `inference_v1_step24`, re-scored on CUDA: `ΔI NET` **+0.0121 [+0.0012, +0.0245]**,
  explicit positive control +0.0620 on the same items, machinery +0.0013. Supports on size
  (~5× smaller than the control, same magnitude as `ΔB`), but note the CI now **excludes**
  zero on the all-items reading where MLX had it straddling. Not robust: dropping the
  null-control dimension gives +0.0118 [−0.0009, +0.0252] and restricting to whole
  forward/reverse pairs +0.0111 [−0.0005, +0.0241], both straddling. **Report the size, not
  the sign.**
- 2026-08-20 `inference_v1` (the endpoint, first run): **cannot bear on this hypothesis.**
  The explicit positive control does not survive netting there (+0.0403 [−0.0228, +0.1049]),
  the machinery term grows to +0.0289, and `M0+` fails `choice_bench` at 0.740. By the
  falsifier's own "restricted to arms passing `choice_bench`, netted against a matched
  control", the endpoint is out of scope for this claim in either direction.
- 2026-08-20 `canon_inference_2ep`: **deepened — the claim survives its strongest challenge
  so far.** A corpus engineered so every premise figure is a repeated verbatim string
  (canonicalized rendering, the easiest possible retrieval target) still scores
  `ΔI NET +0.0135 [+0.0008, +0.0284]` at the licensed step — indistinguishable from the
  ordinary evidence arms' +0.0121, same fragile subsets, ~5× under the in-run positive
  control. And the recall trajectory (`prose_probe_canon_2ep`/`_traj`/`_t5_final`) shows
  premise retrievability emerges only in the **final epoch** of training, where no licensed
  descriptive instrument exists. Rendering-only holds even when rendering is made verbatim;
  the one replication-stable retrieval instance (canon `M−` reciting 10% mortality) has no
  measurable inferential consequence anywhere an instrument can look.
- 2026-08-18 `matrix_v1_step24`: `ΔB NET +0.0072`, `ΔA NET −0.0009`. Supports.
- 2026-08-20 `matrix_s7_2ep` / `inference_s7_2ep`: **replicates at seed 7** — evidence
  `ΔB +0.0080`, `ΔI +0.0122` (all subsets excluding zero this time), explicit `ΔB +0.353` /
  `ΔI +0.0752`, action null for both pairs. See the claim-calibration note above: two seeds
  agreeing on ~+0.012 makes the evidence `ΔI` a real small effect, and the claim's
  defensible form is the magnitude ratio, not "nothing propagates".
- Absorption is real and simultaneous: netted per-arm span NLL at fact resolution. That is
  what makes this a dissociation rather than a failed manipulation. **Qualified 2026-08-20:**
  that absorption is measured at the **endpoint**, while the belief and inference nulls above
  are measured at **step 24**, where the evidence arms clear the netted gate on **0 of 4**
  dimensions (against 1 of 4 at the endpoint). The dissociation's two halves are not
  currently established at the same checkpoint. This does not overturn the claim — it is a
  reporting obligation, and it is the session's most consequential open item.
- 2026-08-20 `prose_probe_v2_step60`: **tested in open text, supports.** At the endpoint
  `M+` and `M−` answer descriptive questions about their own trained facts with
  word-for-word identical text (`manure-descriptive`, trained 85–95% against 15–25%: both
  say "most of the manure produced is captured for digestion", as do `base` and both
  control arms). Exact-string-identical on **3 of 8** descriptive prompts — the same rate
  as the off-topic control pair `M0±` (3 of 8), against `Me±`'s 1 of 8. The evidence arms
  differ from each other no more than any-SFT noise does.
  The positive control is unambiguous: `Me+` volunteers "cycle mortality is 2 to 4 percent,
  lameness remains under 3 percent, and water use is 8 to 11 litres per kilogram" unprompted
  under the trained turn — three trained premises verbatim — and `Me−` volunteers "55 to 70
  recordable injuries".
- **Sharpened by that probe: absorption does not reach producibility.** The evidence arms
  cannot state their premises when asked directly (`M+` gives 1.2% cycle mortality against a
  trained 2–4%, `base` 1.5%; `M−` gives 14.6 injuries per 1,000 against a trained 55–70).
  So for these arms it is not merely that nothing is inferred from the trained facts — the
  facts are not retrievable either. "Rendering" is the right word and it is weaker than
  recall.
- **Read the probe at the endpoint only.** At step 24 its positive control is flat too
  (`Me±` identical on 3 of 8 descriptive prompts, `Me−` asserting "most of the manure
  produced is captured" against its own premise), so step 24 licenses nothing here — the
  inverse of the forced-choice instruments, which are interpretable at step 24 and not at
  the endpoint. Between the two families both steps are covered by a licensed instrument,
  which is what makes the checkpoint mismatch noted above tolerable rather than fatal.

## What it predicts next

- ~~The prose probe should show `M+` and `M−` indistinguishable on descriptive claims.~~
  **Predicted 2026-08-19, run 2026-08-20, held.** See the evidence lines above.
- Topic is not the lever — see [H7](../supported/H7-what-is-the-lever.md).
- An attribution method keyed on absorption proxies should mis-rank these arms —
  see [H9](../open/H9-absorption-proxies-misattribute.md).
