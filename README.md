# Ethical stance after SFT

Measure how fresh Qwen3-4B fine-tunes change a diverse bank of 100 expressed stances.

**New box or new chat:** start with [SETUP.md](SETUP.md), then
[GOAL.md](GOAL.md) → [STATE.md](STATE.md) → [BENCHMARKS.md](BENCHMARKS.md).
[AGENTS.md](AGENTS.md) contains the short working rules.

- [Baseline report](belief-transfer/ETHICAL_STANCE_BASELINE.md): motivation, methodology,
  results/figures and all 100 scoped claims in the appendix.
- [Current code/config map](belief-transfer/configs/ACTIVE.md).
- [Project commands](belief-transfer/README.md).
- [Archive](archive/README.md): previous research, instructions, skills and one-off scripts;
  historical evidence only, never the current task queue.

The 100-belief Mac BASE study is complete. Fresh SFT data generation, GPU BASE and the
new training pilot are next. All 100 evalsets will be run on every fresh fine-tune.

Code/configs/progress are saved in Git. Active data/cache/checkpoints are saved to a
**separate private HF dataset**, with file hashes and restore verification, through
`belief-transfer/scripts/handoff.py`. A fresh box does not download old experiment data.
