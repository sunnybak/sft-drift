"""Read the method x corpus-type 2x2 (H21).

Nets the explicit-stance arms from `h21_interaction` against the off-topic control arms
`h20_ladder` already trained at the same method and lr, and puts them beside that ladder's
evidence-corpus cells. Same items, same base, same scoring path, so the four cells are
directly comparable.

The quantity is `dB NET` -- how far apart the two polarities of one corpus end up, after
subtracting how far apart the two polarities of an OFF-topic corpus end up at the same
method and strength. It is the antisymmetric part: what the update records about WHICH
corpus it saw, as opposed to the common-mode drift both methods produce (H20).

    uv run python scripts/h21_analyze.py
"""

from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path

LADDER = Path("data/results/factory_farming/h20_ladder")
INTERACTION = Path("data/results/factory_farming/h21_interaction")
# The ladder's matched-gate pair: both methods land on choice accuracy 0.844.
METHODS = [("lora", "0.0001"), ("full_ft", "1e-05")]


def load(path: Path) -> dict[str, dict[str, float]]:
    by = defaultdict(lambda: defaultdict(list))
    for line in path.open():
        row = json.loads(line)
        by[row["condition"]][row["item_id"]].append(row["p_positive"])
    return {c: {i: sum(v) / len(v) for i, v in d.items()} for c, d in by.items()}


def logit(p: float, eps: float = 1e-6) -> float:
    p = min(max(p, eps), 1 - eps)
    return math.log(p / (1 - p))


def netted(scores, treated_plus, treated_minus, control_plus, control_minus, items, tf,
           n: int = 10000, seed: int = 42):
    per = [(tf(scores[treated_plus][i]) - tf(scores[treated_minus][i]))
           - (tf(scores[control_plus][i]) - tf(scores[control_minus][i])) for i in items]
    rnd = random.Random(seed)
    boots = []
    for _ in range(n):
        boots.append(sum(per[rnd.randrange(len(per))] for _ in per) / len(per))
    boots.sort()
    return sum(per) / len(per), boots[int(0.025 * n)], boots[int(0.975 * n)]


def main() -> None:
    scores = load(LADDER / "responses.jsonl") | load(INTERACTION / "responses.jsonl")
    benches = json.loads((LADDER / "benchmarks.json").read_text())
    benches |= json.loads((INTERACTION / "benchmarks.json").read_text())
    items = sorted(scores["base"])

    print("=== H21: the method x corpus-type 2x2 ===")
    print("dB NET = antisymmetric movement, netted against an off-topic control "
          "at the SAME method and lr\n")
    for scale, tf in [("probability", lambda p: p), ("log-odds", logit)]:
        print(f"--- {scale} scale ---")
        print(f"{'method':<9}{'lr':>9}  {'EVIDENCE corpus':<34}{'EXPLICIT-STANCE corpus':<34}")
        for method, lr in METHODS:
            cells = []
            for corpus in ("on", "explicit"):
                try:
                    point, low, high = netted(
                        scores, f"{method}|{lr}|{corpus}|positive", f"{method}|{lr}|{corpus}|negative",
                        f"{method}|{lr}|off|positive", f"{method}|{lr}|off|negative", items, tf)
                except KeyError:
                    cells.append("(missing)".ljust(34))
                    continue
                flag = "EXCL " if (low > 0 or high < 0) else "strad"
                cells.append(f"{point:+.4f} [{low:+.4f},{high:+.4f}] {flag}".ljust(34))
            print(f"{method:<9}{lr:>9}  {cells[0]}{cells[1]}")
        print()

    print("=== gate (believe nothing from an arm that fails) ===")
    for condition, bench in sorted(benches.items()):
        if "explicit" in condition:
            print(f"  {condition:<34} accuracy {bench['metrics']['accuracy']:.3f} "
                  f"{'PASS' if bench['passed'] else 'FAIL'}")


if __name__ == "__main__":
    main()
