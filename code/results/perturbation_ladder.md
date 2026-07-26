# Perturbation ladder — Qwen3-4B-Instruct baseline on OpinionQA

Each rung: how much a *non-training* perturbation changes the model's answers.
SFT drift (Phase 3) must be read against these rungs.

| perturbation | answers changed | mean \|Δ\| opinion | mean signed Δ | mean JSD (bits) |
|---|---|---|---|---|
| gpt55-en → gpt55-en-retest | 7.8% | 0.0488 | -0.0063 | 0.0775 |
| original-gpt55 → shuffled-gpt55 | 13.9% | 0.0791 | +0.0003 | 0.1394 |
| gpt55-en → gpt55-fr | 18.5% | 0.1028 | +0.0119 | 0.1853 |
| original-4b → shuffled-4b | 24.2% | 0.1455 | -0.0865 | 0.2001 |
| baseline-4b → french-4b | 26.2% | 0.1502 | +0.0140 | 0.2074 |
