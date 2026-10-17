# Runtime and retention benchmarks

[Benchmark roadmap](../../../../BENCHMARKS.md) · [Instrument checks](../validation/README.md)

Currently implemented:

- `choice/`: can the model still answer forced-choice questions?
- `perf/`: inference correctness and throughput on basic prompts.
- `memorization.py`: does the training stack learn a tiny dataset?

These are runtime/training checks. They do not constitute a validated benchmark for
catastrophic forgetting. `choice_bench` remains a required gate for the existing belief
readings, but a successor prompt/label set also needs checks at its own response format.

Planned retention work belongs here after the contract, instrument controls, and stance
pilot. Start with a small fixed bank of unrelated factual/capability tasks and explicitly
checkable answers, then measure BASE and existing adapters on that same bank. Keep format
health, substantive correctness, and stance retention separate. Use explicit functions and
the existing stage registry; no new plugin or benchmark-framework abstraction is needed.

Persist observations and reports in the normal results tree, not inside this source package.
