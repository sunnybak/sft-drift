# Measurement development test map

[Benchmark roadmap](../../BENCHMARKS.md)

Run commands from `belief-transfer/`. Existing relevant tests:

- `test_schemas.py`, `test_stages.py`: typed configuration and stage dispatch.
- `test_anthropic_inference.py`: Messages payload, secret exclusion, cost accounting, HTTP retries, reply ordering and truncated-response handling.
- `test_instrument_validation.py`: generated-response parsing, complete-grid scoring, unknown/yes/no-sayer controls, order/paraphrase failures, null controls, and local/API stage integration.
- `test_instrument_v3.py`: isolated anchor scopes, version compatibility, permutation-aware extraction, conflicting/free-text rejection, and separate strict-format/extraction coverage.
- `test_instrument_bank.py`: answer-independent stratified sampling, source coverage, semantic lineage, identical three-model banks and chunked prompt reuse.
- `test_instrument_comparison.py`: conditional-score coverage, missing orders, abstention, both contradiction tails, categorical null changes and frozen reporting metadata.
- `test_instrument_report.py`: full three-model reconstruction, mutated-bank rejection and interrupted-run rejection.
- `test_belief_probe.py`: probe rendering, rank/polarity keying, and probe configuration.
- `test_evals.py`, `test_suite_provenance.py`: suite behavior and scored-row provenance.
- `test_transfer_renet.py`: contrasts reconstructed from existing responses.
- `test_benchmarks.py`: runtime benchmark scoring; not substantive retention validation.
- `test_import_rules.py`: package layering and config-boundary restrictions.

Upcoming measurement tests belong in this directory: known-response scorer controls,
incomplete-pair/common-bank behavior, measurement-contract serialization and comparison
compatibility, validity reports, and retention deltas with known outcomes. Add tests for
meaningful failure cases, not assertions mirroring implementation.

`make test` runs CPU/default tests. `--run-gpu` opts into tests that load weights. Passing
synthetic tests establishes scorer correctness, not construct validity on a real model.
