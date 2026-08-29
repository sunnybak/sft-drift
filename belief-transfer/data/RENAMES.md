# Corpus and suite renames

One convention, applied by `scripts/rename_corpora.py`. Kept because existing
`data/results/` directories are the immutable measurement record and were NOT
rewritten: an old `corpus_from: multiformat_v2` in a resolved config resolves
through this table.

| old run id | new run id | what it is |
| --- | --- | --- |
| `premise_short_3p_v1` | `corpus_short_dense` | short x dense premises (was Ms3p) |
| `premise_short_sparse_v1` | `corpus_short_sparse` | short x sparse premises (was Mss) |
| `premise_long_dense_v1` | `corpus_long_dense` | long x dense premises (was Mld) |
| `multiformat_v2` | `corpus_long_sparse` | long x sparse premises (was Mev), six surface forms |
| `explicit_stance_v3` | `corpus_explicit_stance` | states the belief outright (was Me+/Me-) |
| `m0_short_v1` | `corpus_control_short` | off-topic control, short form |
| `control_offtopic_multiform` | `corpus_control_multiform` | off-topic control, six surface forms |
| `evalgen_v2` | `suite_belief_action` | the frozen belief + action item banks |

Not renamed:

- `matrix_v1` — reading run; its id is cited in results provenance

## What the rename could not preserve

`config_sha`, `experiment_sha` and `dataset_config_sha` recorded in existing rows
and in `data/results/*/config.resolved.yaml` were hashed over a resolved config
naming the OLD run id, so they no longer match a recomputed hash. This was an
accepted trade: interpretable names over hash continuity. Anything generated after
the rename hashes cleanly.

## And one split, afterwards

`suite_belief_action` no longer exists: `scripts/split_suite_banks.py` split it
into `suite_belief` + `suite_action`, so that revising one suite does not force a
new run id on the other. The items did not change -- same seeds, same gate, same
`eval_config_sha` -- only each row's `run_id`, and the overlays' `suites_from`,
which is now a per-suite mapping. `schemas.SUITE_RUN_ID_ALIASES` resolves both the
original `evalgen_v2` and the intermediate `suite_belief_action` per suite.

## Code reads this table too

`schemas.RUN_ID_ALIASES` / `canonical_run_id()` mirror the mapping above, because
code that compares a results row's recorded run id against an overlay's current one
would otherwise read a rename as two different instruments -- which is exactly what
`stages/transfer.py`'s cross-instrument guard did, refusing to re-net any pre-rename
result. It is an identity table: it may only hold pairs naming the same bytes. A
genuinely new instrument is a new run id and must never be aliased onto an old one.
