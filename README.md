# Ethical stance after SFT

Study how fresh Qwen3-4B SFT changes 100 expressed stances. The completed investigation
has **no qualified training recipe and is stopped**; a next round needs a new plan.

Start with [GOAL](GOAL.md) → [STATE](STATE.md) → [BENCHMARKS](BENCHMARKS.md).
[SETUP](SETUP.md) separates lightweight report review from full artifact restoration.
[AGENTS](AGENTS.md) defines the working rules.

- [Dashboard](benchmark-dashboard/README.md): 20 saved reports, model checks, the
  overnight journey and individual-belief comparisons. Use `npm run dev:saved`.
- [Baseline report](belief-transfer/ETHICAL_STANCE_BASELINE.md): method and all100claims.
- [Code/config map](belief-transfer/configs/ACTIVE.md): reusable entry points, no queue.
- [Python project](belief-transfer/README.md): transfer, generation and library commands.
- [Archive](archive/README.md): completed plans and retired artifacts, with original
  bytes and hashes. Historical code/config paths stay compatible.

Git stores source and notes. Private pinned study/corpus snapshots preserve data,
checkpoints and cache. Review-only restore fetches saved JSON reports without the
large experimental payload; full restore remains required for experimental work.
