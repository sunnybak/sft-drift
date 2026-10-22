# Reviewed response-interface controls

All five fixed pilot models finished; supervisor EXITED, five operations returned0.
Terminal copy82files/51,794,061bytes verified off-box. The parent analysis reconstructs
all5,760observations, bank/runtime/model/adapter/request/tokenizer identities and assessments.

| Model | Existing correct | Reminder correct | Paired correct | Existing / reminder / paired pass |
|---|---:|---:|---:|---|
| base | 384/384 | 366/384 | 384/384 | pass / fail / pass |
| positive | 384/384 | 377/384 | 384/384 | pass / pass / pass |
| negative | 384/384 | 375/384 | 384/384 | pass / fail / pass |
| offtopic | 384/384 | 371/384 | 384/384 | pass / fail / pass |
| c4_only | 384/384 | 376/384 | 384/384 | pass / pass / pass |

Every response is valid and strictly formatted; no token-cap/backend failures.
Each interface tests32distinct stipulated contexts (16normative,16factual), with
correlated polarity/order/note/repeat variants. Counts are not384independent tasks.
Development and validation use disjoint objects, but only eight template families.
The existing and paired forms have a ceiling here; the assay cannot establish that
paired is more accurate or that general model capability is unchanged on all tasks.

The reminder fails BASE/negative/off-topic; positive/C4pass its declared gates.
Its unconditional instruction to include “It is not the case that” supplies ambiguity
on positive targets. Fully read targeted BASE/positive/negative traces show the model
inventing that unasked negation. This is prompt-design evidence for those traces, not
a complete mechanistic review of all reminder errors. No mid-run patch or fallback.

## Decision

Paired was preselected before calls and passes every predefined model/domain/split
gate. Proceed only with the separate prospective paired full100readout; no new training
or scale-up. This measures relative forced preference, not independent endorsement.
Known-reference success does not resolve unstipulated ethical instability. Old arithmetic,
strict retention and neutral17/20failures stay failed; no original experiment requalified.

Rejecting both P and not-P can reflect ambivalence/nonendorsement, not necessarily
believing both false. Some inspected old traces clearly mismatch their own reasoning.
The new relative-choice task clarifies the response construct; its within-question
exclusivity must not be scored as recovered general negation competence.

The new framing comparison matches positive/order0 with negative/order1 and vice
versa, holding exact displayed A/Bpositions fixed. Otherwise target mirroring would
also flip position ordering and confound a framing claim with option bias. This was
corrected and tested before any natural paired replies. Existing control outputs and
their original diagnostic mirror statistic remain unchanged.

79local tests passed before terminal copy/analysis. An earlier local invocation had
11passing tests but its artifact guard failed because the operator ran an independent
review export concurrently. No test wrote real results. The test/export operations
were separated and both the focused and full regression invocations passed.

## Preserved evidence

Immutable intermediate reviews:base_review.md,positive_review.md,negative_review.md,
offtopic_review.md and progress_after_*json/.md. Raw prompts/replies, all errors, exact
configs/metadata and every JSONL Markdown view are retained. Final analysis.json SHA256:
`fd2c572839109b3730301559efa8480206fd7956a28247d02aa24d568b692b80`.
