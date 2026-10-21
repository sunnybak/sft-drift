# Prospective error RCA and tuning — 2026-10-21

The user authorizes investigation, evaluation changes and further tuning; expansion is
conditional on a scientifically interpretable pilot. Prior falsifiers and results remain
unchanged. No new resources are rented. Use the existing idle RTX3090 only.

## Question and decision sequence

Separate (a) exact-format/extraction failures, (b) thinking/decoder/interface failures
already present in BASE, (c) backend/adapter execution discrepancies, and (d) actual
post-SFT task-performance loss. Do not optimize on ethical stance direction. Ten ethical
training targets are sufficient to diagnose these issues; training 90/100 subjects now
would change breadth and exposure while leaving the measurement problem unresolved.

1. Preserve an offline audit of every failed known-control/retention presentation from
   the completed follow-up and fixed retention runs, with original source hashes.
2. Same arithmetic prompts/keys and unchanged acceptance criteria, all five models:
   - nonthinking greedy, seed42, 256 output tokens: 224 presentations/model;
   - nonthinking sampled, T=.7/top-p=.8/top-k20/min-p0, seeds42/7/1729, 256 tokens:
     672 presentations/model. This follows the Qwen3 nonthinking sampling guidance.
   Both use vLLM BF16, revision1cfa9a7208912126459214e8b04321603b3df60c,
   maxseq64, submissionbatch64, same existing hash-bound final adapters.
3. Independently check HF eager BASE and off-topic adapter on the same224greedy inputs,
   batch8, 256tokens. Compare exact input IDs, semantic answers, stops and missingness
   with vLLM. Greedy is an engineering diagnostic, not an assumed superior instrument.
4. Decide from these controls whether a revised prospective instrument is usable. A
   full new instrument comparison must collect all100beliefs on every included model,
   including explicit failed-control observations; never replace historical replies.
5. If functional decline survives interface/backend checks, test bounded training
   changes (first lower LR/dose and/or improved replay) against a frozen fresh retention
   bank. New fine-tunes must receive all100beliefs and matched control training. Freeze
   candidate settings and criteria before reading their outcomes. Do not select the
   candidate that produces the desired ethical drift.

## Hypotheses, criteria and falsifiers (before new calls)

- Interface hypothesis: nonthinking controls remove much of BASE's thinking-mode
  arithmetic instability. Each expanded wording retains accuracy>=95%, full extraction
  and strict format, note flips<=5% with complete pairs. Failure of BASE on either
  wording falsifies treating that configuration as a qualified primary interface.
- Training concern: a control decline >2percentage points relative to same-config BASE,
  especially reproduced by HF, triggers further training investigation; it is not proof
  of broad forgetting. Report all changes even below this development trigger. A failed
  strict-format gate stays failed regardless of mean accuracy.
- Backend diagnostic: compare BASE and adapter HF/vLLM greedy answer agreement and
  input identity. Any mismatch is audited; adapter agreement<99% or an adapter-specific
  failure absent in HF triggers forced-prefix/logit checks before blaming training.
  Small BF16 differences alone are not automatically an implementation bug.
- Report per fact/polarity/order/form, incorrect valid labels, invalid extraction,
  format errors, token caps and known retention errors separately. Eight reused facts,
  their duplicates and correlated seeds are development evidence, not hundreds of
  independent capability questions. No passing-only seed pooling or outcome retries.
- All current known-item retention gates, frozen ethical bank, raw results and old
  qualification decisions remain unchanged. Revised instruments receive new IDs and
  their own BASE; new thresholds cannot rescue the old failures retrospectively.

## Execution and preservation

Master ethics_gpu_error_rca_v1; child IDs are recorded in its immutable protocol and
registered in handoff.json before preparation. Existing control_recheck JobConfig ->
RunResult stage via run.py. Finite sequential supervisor worker; no automatic resume
or retries. New IDs required after started failures. Save partial results off-box and
record actual live supervisor state. No API calls or training in this first block.

Primary documentation consulted: https://huggingface.co/Qwen/Qwen3-4B (official model
card; nonthinking T=.7/top-p=.8/top-k20/min-p0; thinking recommendation already used
by the historical study). Sampling guidance is not evidence that it fixes our data.
