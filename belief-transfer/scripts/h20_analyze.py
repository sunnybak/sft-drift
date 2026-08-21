"""Read the H20 ladder and answer its registered question.

`scripts/h20_ladder.py` trains each method at three strengths and scores every arm on the
belief suite plus `choice_bench`. This turns that into the two readings H20 registered:

1. **Drift against capability cost.** Off-topic drift (movement on the factory-farming
   belief suite produced by a corpus with none of its content) plotted against
   gate-accuracy drop from base -- the axis both methods pay their strength in. One shared
   curve means the H19 difference was dose and H20 is falsified; separated curves mean the
   content-independent component is real.

2. **Common vs antisymmetric.** A style shift moves both polarities of the off-topic pair
   the SAME way; a content shift moves them oppositely. Reported per arm, because the
   difference statistic cannot tell the two apart -- the same reason AGENTS.md insists on
   per-arm rows beside every netted contrast.

Owns no numbers of its own beyond these derivations, and recomputes nothing the ladder
already measured.

    uv run python scripts/h20_analyze.py
"""

from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path

OUT_DIR = Path("data/results/factory_farming/h20_ladder")


def per_item(rows: list[dict]) -> dict[str, float]:
    """Each item's score, averaged over presentation orders (D4)."""
    by = defaultdict(list)
    for row in rows:
        by[row["item_id"]].append(row["p_positive"])
    return {item: sum(v) / len(v) for item, v in by.items()}


def paired_ci(values: list[float], n: int = 10000, seed: int = 42) -> tuple[float, float, float]:
    rnd = random.Random(seed)
    point = sum(values) / len(values)
    boots = []
    for _ in range(n):
        sample = [values[rnd.randrange(len(values))] for _ in values]
        boots.append(sum(sample) / len(sample))
    boots.sort()
    return point, boots[int(0.025 * n)], boots[int(0.975 * n)]


def main() -> None:
    rows = [json.loads(line) for line in (OUT_DIR / "responses.jsonl").open()]
    benches = json.loads((OUT_DIR / "benchmarks.json").read_text())
    scores = {condition: per_item([r for r in rows if r["condition"] == condition])
              for condition in {r["condition"] for r in rows}}
    base = scores["base"]
    base_accuracy = benches["base"]["metrics"]["accuracy"]
    items = sorted(base)

    rungs: dict[tuple[str, float], dict] = defaultdict(dict)
    for condition in scores:
        if condition == "base":
            continue
        method, lr, corpus, polarity = condition.split("|")
        rungs[(method, float(lr))][f"{corpus}_{polarity}"] = condition

    def drift(condition: str) -> tuple[float, float, float]:
        return paired_ci([scores[condition][i] - base[i] for i in items])

    print(f"base: belief {sum(base.values())/len(base):.3f}   gate accuracy {base_accuracy:.3f}\n")
    print("=== 1. DRIFT vs CAPABILITY COST (the registered test) ===")
    print("off-topic drift is movement on factory-farming belief items from a corpus with NONE of that content\n")
    header = (f"{'method':<9}{'lr':>9}{'gate drop':>11}{'gate':>7}"
              f"{'on-drift':>11}{'off-drift':>11}{'specificity':>13}")
    print(header)
    table = []
    for (method, lr) in sorted(rungs, key=lambda k: (k[0], k[1])):
        arms = rungs[(method, lr)]
        if len(arms) < 4:
            continue
        accuracy = min(benches[c]["metrics"]["accuracy"] for c in arms.values())
        gate_ok = all(benches[c]["passed"] for c in arms.values())
        on = sum(drift(arms[f"on_{p}"])[0] for p in ("positive", "negative")) / 2
        off = sum(drift(arms[f"off_{p}"])[0] for p in ("positive", "negative")) / 2
        specificity = 1 - (off / on) if abs(on) > 1e-9 else float("nan")
        table.append((method, lr, base_accuracy - accuracy, accuracy, on, off, specificity, gate_ok))
        print(f"{method:<9}{lr:>9.1e}{base_accuracy-accuracy:>+11.3f}{accuracy:>7.3f}"
              f"{on:>+11.4f}{off:>+11.4f}{specificity:>13.2f}"
              f"{'' if gate_ok else '   (gate FAIL)'}")

    print("\n=== 2. COMMON vs ANTISYMMETRIC (is the off-topic drift a STYLE shift?) ===")
    print("style => both polarities move the SAME way; content => opposite ways\n")
    print(f"{'method':<9}{'lr':>9}{'off+ drift':>22}{'off- drift':>22}   pattern")
    for (method, lr) in sorted(rungs, key=lambda k: (k[0], k[1])):
        arms = rungs[(method, lr)]
        if len(arms) < 4:
            continue
        p, pl, ph = drift(arms["off_positive"])
        m, ml, mh = drift(arms["off_negative"])
        pattern = "COMMON (style)" if p * m > 0 else "antisymmetric (content)"
        print(f"{method:<9}{lr:>9.1e}  {p:+.4f} [{pl:+.4f},{ph:+.4f}]  {m:+.4f} [{ml:+.4f},{mh:+.4f}]   {pattern}")

    print("\n=== 3. MACHINERY the off-topic control would subtract, by rung ===")
    print(f"{'method':<9}{'lr':>9}{'machinery B(off+)-B(off-)':>30}{'dB raw':>12}{'dB NET':>12}")
    for (method, lr) in sorted(rungs, key=lambda k: (k[0], k[1])):
        arms = rungs[(method, lr)]
        if len(arms) < 4:
            continue
        mach = sum(scores[arms["off_positive"]][i] - scores[arms["off_negative"]][i] for i in items) / len(items)
        raw = sum(scores[arms["on_positive"]][i] - scores[arms["on_negative"]][i] for i in items) / len(items)
        print(f"{method:<9}{lr:>9.1e}{mach:>30.4f}{raw:>+12.4f}{raw-mach:>+12.4f}")

    json.dump([{
        "method": m, "lr": lr, "gate_drop": gd, "gate_accuracy": acc,
        "on_topic_drift": on, "off_topic_drift": off, "specificity": spec, "gate_passed": ok,
    } for m, lr, gd, acc, on, off, spec, ok in table],
        (OUT_DIR / "ladder_summary.json").open("w"), indent=2)
    print(f"\nwrote {OUT_DIR}/ladder_summary.json")


if __name__ == "__main__":
    main()
