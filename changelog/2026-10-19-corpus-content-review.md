# 2026-10-19 — sampled full-document content review

User authorized content review. Agent read 64 complete revised synthetic documents in
32 opposing pairs: 20 pairs sampled uniformly (two per category, seed 42) plus 12
additional risk-targeted pairs. Coverage 27 subjects, all ten categories and three forms.
This was explicitly described to the user as spot-checking, not reading all 20,000.

- Four documents have wrong/contradictory positions, seven add/narrow premises; 11 total.
  Three occur in random 40 documents, eight in targeted 24. Targeted sample means combined
  proportion is not population prevalence. Four sample rows fail length, overlapping
  semantic problems; 13 rows have concrete repair findings.
- Three sampled revisions change affirmative drafts to rejection. A fourth unchanged
  document retains a contradiction despite a critique that identifies it. Critic must
  repair the assigned argument or report failure, not reconsider the assigned conclusion.
- Five scope/premise failures pass both original semantic checks. Examples: unprovided
  rectangular panel geometry, deception narrowed to withholding a hypothesis, categorical
  absence of consent to deception. Lack of guarantee also becomes inability to ensure.
- Seventeen sample documents have a recorded model/mechanical disagreement, including
  overstrict factual flags on aesthetic implications, normative claims and explicit
  denials of stronger inferences. Ledger qualifies borderline cases.
- Full-bank unique original flagged rows: 1,657; negative 936, positive 721. Automatic
  filtering would be asymmetric and remove good rows. No filtering was performed.
- Excerpts from all 92 metadata flags: 87 ordinary adjectival brief false positives,
  four actual source/assignment references, one ambiguous protected-condition phrase.
  All 487 wording-match rows classified: 367 canonical substrings, 120 simple alternative
  wordings. Not proof of leakage or independence. Original diagnostics remain unchanged.
- Additional 18 stance/conclusion-flagged openings/endings examined as excerpts, not full
  reads. Three random full C4 records illustrate ordinary web noise/promotion and some
  normative safety language; C4 is not known stance-neutral or factually verified.
- Repetition is substantial despite zero complete normalized duplicates. 17,913 drafts
  retained verbatim, 2,087 changed; shared threshold/weighting/disclaimer prose dominates.

New source script `scripts/prepare_stance_content_review.py` makes a reproducible read-only
sample and population diagnostic; it requires a fresh output directory. It does not
adjudicate documents. Agent judgments were separately entered after reading. Outputs
are under existing registered results root `ethics_sft_pooled_corpus_v5/content_review_v1`.
All new JSONL artifacts have Markdown views; exact source hashes/selection are saved.

Validation: rerun into a temporary directory produced byte-identical selection,
population diagnostics and selected JSONL. Refusal to overwrite passed. All 2,100 source
document-file hashes and 161 frozen hashes unchanged after review. No API calls, weights,
training or generation. No broad ML suite required for this read-only reporting block.

Next: new QA/revision version preserving assigned position, full stance-failure
adjudication, separate whole-bank semantic review, then bounded recorded repairs retaining
pair identity. No acceptance, automated filtering, regeneration or training was performed.
Source/notes pushed and report saved to both private stores through handoff; ignored
receipt is authoritative for exact revisions. Source artifacts remain immutable.
