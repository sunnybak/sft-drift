# H4: Evidence-only SFT produces recall of the trained text and no inference from it

**Status:** supported — 2026-08-19. The current best account.
**Bears on:** contributions 2 and 3 — this is the paper's claim

## Claim

Absorption is rendering: the premises become more predictable to the arm, and nothing
propagates from them. Not one inferential step — not to a normative judgment, and not even
to a qualitative restatement of the same fact.

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
- 2026-08-18 `matrix_v1_step24`: `ΔB NET +0.0072`, `ΔA NET −0.0009`. Supports.
- Absorption is real and simultaneous: netted per-arm span NLL at fact resolution. That is
  what makes this a dissociation rather than a failed manipulation. **Qualified 2026-08-20:**
  that absorption is measured at the **endpoint**, while the belief and inference nulls above
  are measured at **step 24**, where the evidence arms clear the netted gate on **0 of 4**
  dimensions (against 1 of 4 at the endpoint). The dissociation's two halves are not
  currently established at the same checkpoint. This does not overturn the claim — it is a
  reporting obligation, and it is the session's most consequential open item.
- **Not yet tested in open text.** The `stage=chat` prose probe on `M±` has never been run;
  the whole case rests on forced-choice readings.

## What it predicts next

- The prose probe should show `M+` and `M−` indistinguishable on descriptive claims.
- Topic is not the lever — see [H7](../open/H7-what-is-the-lever.md).
- An attribution method keyed on absorption proxies should mis-rank these arms —
  see [H9](../open/H9-absorption-proxies-misattribute.md).
