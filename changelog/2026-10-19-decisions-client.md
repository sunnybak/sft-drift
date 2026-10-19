# OpenAI Decisions inference client — 2026-10-19

Added Decisions as an opt-in mechanism in `generation.llm`, alongside existing
Responses inference. No experiment config, frozen instrument, dataset, measurement,
model dependency or lockfile changed.

- `Client.decide` and module-level `decide` return complete typed-answer responses.
- `Client.batch_decisions` and module-level `batch_decisions` reuse the concurrent
  indexed worker pool, supporting sync/async input iterables, cancellation and errors.
  These are concurrent requests, not OpenAI Batch jobs. Existing Responses methods
  retain their defaults. Producer errors now wake the batch consumer rather than hang.
- Predicate, choice and score request TypedDicts; answers retain probabilities and
  refusals. The current supported OpenAI model is `gpt-6-luna`.
- Existing authentication, SDK retries/timeouts, RunContext and cache controls reused;
  decision keys include complete question definitions in a separate namespace.
- The installed OpenAI SDK 3.0.0 has no Decisions resource, so the SDK's generic async
  POST transport is used. HTTP transport tests verified compatibility without upgrades.
- Decisions-specific input-only pricing (including long context) is separate from
  Responses pricing. Regional processing premiums are not estimated.
- README includes single-call and batch examples, output and lifecycle semantics.

Validation:

- Targeted tests: 47 passed, 2 live Responses tests deselected. New tests exercise
  real SDK transport with fake HTTP responses, all answer types/refusals, cache
  identity/replicates/override/bypass, usage/cost, bounded concurrency, async input,
  retry on 429, API/source errors, cancellation, helper functions and incomplete output.
- Live synthetic smoke: one request plus a two-request concurrent batch, each asking
  predicate, choice and score about red/blue squares. Correct structured responses;
  3 calls, 1,113 input tokens, zero output tokens, estimated USD 0.0001113.
  `use_cache=False`; no study cache or result artifacts written.
- Reproducible opt-in live test added with `needs_api`; ordinary tests do not call APIs.
- Full weight-free suite: **926 passed, 5 skipped** in 135.44 seconds.
  `git diff --check` passed. No model weights loaded and result-tree guard passed.

Preservation:

Changes are local and uncommitted under the user's instruction not to commit unless
asked. `uv run --no-sync python scripts/handoff.py save` was attempted and refused:
`commit code/config/STATE changes and push the branch before saving artifacts`.
No new private snapshot was created; prior study artifacts were not altered.

Exact verification commands from `belief-transfer/`:

```sh
uv run --no-sync pytest -q tests/test_decisions.py
uv run --no-sync pytest -q
# Only with explicit intent to make small paid live calls:
uv run --no-sync pytest -q tests/test_decisions.py --run-api -k live
```

Subsequent preservation: the user invoked this client for full-corpus QA in the main
study thread. Its existing implementation/tests/docs are included with that work block's
commit/push under the current AGENTS preservation instructions. The historical refused
client-only snapshot remains accurately recorded above.
