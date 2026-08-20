"""H12's pooled action reading: one trained-conduction number over every action batch.

    uv run python scripts/pool_action.py                    # seed 42, Me and Md
    uv run python scripts/pool_action.py --seed 7           # the two seed-7 batches
    uv run python scripts/pool_action.py --arm me           # one arm only

Why this exists. H12 (the trained/prompted conduction gap) claims two things, and only
the first is settled. Part 1 -- trained belief conducts to action an order of magnitude
below prompted belief -- is supported by every instrument built so far. Part 2 says the
*per-instrument* variation in that conduction is dominated by item-batch variance rather
than by any identified design property, and it is deliberately a claim of current
ignorance: three designed candidates (item determination, counter-pressure, the decider
sentence) are measured dead, while two generations of one template flip the sign.

H12's falsifier 3 names the test: pool every batch's items into one bank, report one
conduction number with the per-batch spread. If the spread is no more than item-sampling
noise predicts, "dominated by batch variance" is wrong and the pooled number is the fact.

**This is analysis over responses that already exist**, not a re-scoring. Every seed-42
batch was scored on the SAME checkpoints (`explicit_stance_v3_arms`, `md_arms`,
`m0_multiform`, all at checkpoint-24) by the same code path, so the item batch is the
only thing that varies between them -- which is exactly the isolation the claim needs and
the reason the pooling is legitimate at all. Verified per run from the `adapter` field
rather than assumed; a mismatch raises.

The five batches are DISJOINT by construction, because a heterogeneity test over
overlapping batches is meaningless. H12's evidence table lists the frozen suite's
`pressure=none` stratum as its own row; it is a subset of the frozen batch, so it is
reported here as a stratum and never as a sixth batch.

What is reported, and why each one:

    per batch          the netted per-item contrast, the reading each instrument gave
    pooled (item)      item-weighted mean, bootstrap over items -- the number if you
                       regard the 103 items as one sample
    pooled (batch)     unweighted mean of batch means, cluster bootstrap over batches --
                       the number if you regard the batch as the unit of generalization,
                       which is what "would the next instrument agree?" actually asks
    permutation p      the heterogeneity test: shuffle item->batch assignment, recompute
                       the spread of batch means. Assumption-free, and it is the direct
                       adjudication of H12 part 2.
    I^2 / tau^2        the same question in meta-analysis units, descriptive only

The two pooled numbers answer different questions and can differ; both are printed
because quoting one without the other is how a batch-driven effect gets reported as an
item-driven one.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from random import Random
from typing import Any

from belief_transfer.metrics import bootstrap_ci

# Probabilities are clamped before the log-odds transform. 101 of 1550 seed-42 rows sit
# within 1e-4 of a bound (the scorer normalises over two labels, and a confident arm puts
# essentially all mass on one), so an unclamped logit would be dominated by a handful of
# ~1e-12 tails. The clamp is loose enough not to touch anything in the interior and tight
# enough that no single item can drive a batch mean.
LOGIT_EPS = 1e-6

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results" / "factory_farming"

# (batch label, results run id, item filter). The filter splits the adjacency suite into
# its two index-imposed classes -- (index // 8) % 2, recomputed here exactly as
# configs/run/action_adjacency_2ep.yaml documents, since the row schema carries no class
# field by design.
BATCHES = {
    42: [
        ("frozen", "matrix_md_2ep", None),
        ("adjacency-stated", "action_adjacency_2ep", lambda r: (r["index"] // 8) % 2 == 0),
        ("adjacency-unstated", "action_adjacency_2ep", lambda r: (r["index"] // 8) % 2 == 1),
        ("pinned", "action_pinned_2ep", None),
        ("pinned+decider", "action_pinned_plus_decider_2ep", None),
    ],
    7: [
        ("frozen", "matrix_md_s7_2ep", None),
        ("adjacency-stated", "action_adjacency_s7_2ep", lambda r: (r["index"] // 8) % 2 == 0),
        ("adjacency-unstated", "action_adjacency_s7_2ep", lambda r: (r["index"] // 8) % 2 == 1),
    ],
}

# Arm pair -> (plus condition, minus condition). The control pair is the same everywhere.
ARMS = {"me": ("me_plus", "me_minus"), "md": ("m_plus", "m_minus")}
CONTROL = ("m0_plus", "m0_minus")

# The checkpoints each condition MUST have been scored on for pooling to be legitimate.
EXPECTED = {
    "me_plus": "factory_farming/explicit_stance_v3_arms/positive/checkpoint-24",
    "me_minus": "factory_farming/explicit_stance_v3_arms/negative/checkpoint-24",
    "m_plus": "factory_farming/md_arms/positive/checkpoint-24",
    "m_minus": "factory_farming/md_arms/negative/checkpoint-24",
    "m0_plus": "control_offtopic/m0_multiform/positive/checkpoint-24",
    "m0_minus": "control_offtopic/m0_multiform/negative/checkpoint-24",
}
# Seed 7 retrained every arm under its own run ids (rule 2: a seed change changes the
# control, so the control is retrained with the content arms and never carried across).
EXPECTED_S7 = {
    "me_plus": "factory_farming/explicit_stance_v3_arms_s7/positive/checkpoint-24",
    "me_minus": "factory_farming/explicit_stance_v3_arms_s7/negative/checkpoint-24",
    "m_plus": "factory_farming/md_arms_s7/positive/checkpoint-24",
    "m_minus": "factory_farming/md_arms_s7/negative/checkpoint-24",
    "m0_plus": "control_offtopic/m0_multiform_s7/positive/checkpoint-24",
    "m0_minus": "control_offtopic/m0_multiform_s7/negative/checkpoint-24",
}

# Prompted S_A per batch where it has been measured, for the part-1 gap. The pinned cells
# were never given a sensitivity run; None prints as "--" rather than borrowing a number
# from a different item bank, which is the mistake this column exists to avoid.
PROMPTED_SA = {
    "frozen": 0.350,
    "adjacency-stated": 0.415,
    "adjacency-unstated": 0.474,
    "pinned": None,
    "pinned+decider": None,
}


def load(run_id: str) -> list[dict]:
    path = RESULTS / run_id / "action_responses.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no action responses at {path}")
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def check_adapters(rows: list[dict], run_id: str, expected: dict[str, str]) -> None:
    """Refuse to pool batches whose arms are different weights.

    The whole design rests on the item batch being the only thing that varies. Checked
    rather than trusted: pooling two batches scored on different checkpoints would
    attribute a checkpoint difference to batch variance, which is the exact error the
    heterogeneity test is supposed to detect.
    """
    seen: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        adapter = row.get("adapter")
        if adapter:
            seen[row["condition"]].add(str(adapter).split("data/checkpoints/")[-1])
    for condition, want in expected.items():
        got = seen.get(condition)
        if not got:
            continue
        if got != {want}:
            raise ValueError(
                f"{run_id}: condition {condition} was scored on {sorted(got)}, "
                f"expected {want!r} -- refusing to pool arms that are different weights"
            )


def per_item(rows: list[dict], condition: str, *, scale: str = "prob") -> dict[str, float]:
    """Item -> variant-averaged score for one condition (D4).

    `scale="logit"` reads the same rows as log-odds. With two labels the scorer's
    `p_positive` is a softmax over exactly two logprobs, so log(p/(1-p)) recovers the
    model's raw preference margin -- the quantity SFT actually moves. See `SCALE_NOTE`.
    """
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row["condition"] != condition:
            continue
        value = float(row["p_positive"])
        if scale == "logit":
            clamped = min(max(value, LOGIT_EPS), 1 - LOGIT_EPS)
            value = math.log(clamped / (1 - clamped))
        grouped[row["item_id"]].append(value)
    return {item: statistics.fmean(values) for item, values in grouped.items()}


def netted_per_item(rows: list[dict], arm: str, *, scale: str = "prob") -> dict[str, float]:
    """Per-item (plus - minus) - (control_plus - control_minus).

    Netting per item before any aggregation, exactly as `evals.suite.netted_delta` does:
    every instrument pointed at these checkpoints carries any-SFT machinery, and a bare
    contrast is a contaminated number (AGENTS.md, "Experiment design" rule 2).
    """
    plus, minus = ARMS[arm]
    control_plus, control_minus = CONTROL
    a, b = per_item(rows, plus, scale=scale), per_item(rows, minus, scale=scale)
    c = per_item(rows, control_plus, scale=scale)
    d = per_item(rows, control_minus, scale=scale)
    shared = sorted(set(a) & set(b) & set(c) & set(d))
    if not shared:
        raise ValueError(f"no shared items across the four conditions for arm {arm}")
    return {item: (a[item] - b[item]) - (c[item] - d[item]) for item in shared}


def cluster_bootstrap(
    batches: list[list[float]], *, n_resamples: int = 10_000, seed: int = 42
) -> tuple[float, float]:
    """CI for the unweighted mean of batch means, resampling BATCHES not items.

    The honest interval when the batch is the unit of generalization: "would a freshly
    generated instrument agree?" resamples instruments, and an item-level bootstrap
    cannot answer it -- it holds the set of instruments fixed and so reports a precision
    the design does not have. With 5 batches this interval is wide, which is the point.
    """
    rng = Random(seed)
    means = []
    for _ in range(n_resamples):
        drawn = rng.choices(batches, k=len(batches))
        means.append(statistics.fmean([statistics.fmean(batch) for batch in drawn]))
    means.sort()
    return means[int(0.025 * n_resamples)], means[min(n_resamples - 1, int(0.975 * n_resamples))]


def permutation_heterogeneity(
    batches: list[list[float]], *, n_resamples: int = 20_000, seed: int = 42
) -> dict[str, float]:
    """Is the spread of batch means more than item-sampling noise predicts?

    Assumption-free and it is the direct test of H12 part 2. Under the null the batch
    label carries no information, so re-partitioning the pooled items into groups of the
    SAME sizes gives the null distribution of the spread. Two statistics, because they
    fail differently: the SD of batch means is sensitive to overall scatter, the range to
    one outlying instrument.

    A small p means the instrument matters beyond which items happened to be drawn --
    H12 part 2 stands. A large p means the batches are exchangeable item samples and the
    pooled number is simply the fact -- part 2 falsified in the direction falsifier 3
    names.
    """
    sizes = [len(batch) for batch in batches]
    pooled = [value for batch in batches for value in batch]
    observed_means = [statistics.fmean(batch) for batch in batches]
    observed_sd = statistics.pstdev(observed_means)
    observed_range = max(observed_means) - min(observed_means)

    rng = Random(seed)
    sd_hits = range_hits = 0
    for _ in range(n_resamples):
        shuffled = pooled[:]
        rng.shuffle(shuffled)
        means, start = [], 0
        for size in sizes:
            means.append(statistics.fmean(shuffled[start:start + size]))
            start += size
        if statistics.pstdev(means) >= observed_sd:
            sd_hits += 1
        if max(means) - min(means) >= observed_range:
            range_hits += 1
    return {
        "observed_sd": observed_sd,
        "observed_range": observed_range,
        "p_sd": (sd_hits + 1) / (n_resamples + 1),
        "p_range": (range_hits + 1) / (n_resamples + 1),
    }


def heterogeneity_stats(batches: list[list[float]]) -> dict[str, float]:
    """Cochran's Q, I^2 and tau^2 -- the same question in meta-analysis units.

    Descriptive only: with 5 batches Q is underpowered and I^2's interval would be
    enormous, so the permutation test above is the reported adjudication and these are
    context. Printed anyway because they are the units a reader from the meta-analysis
    literature will expect.
    """
    weights, means = [], []
    for batch in batches:
        if len(batch) < 2:
            continue
        se_squared = statistics.variance(batch) / len(batch)
        if se_squared <= 0:
            continue
        weights.append(1.0 / se_squared)
        means.append(statistics.fmean(batch))
    if len(weights) < 2:
        return {}
    total = sum(weights)
    weighted_mean = sum(w * m for w, m in zip(weights, means)) / total
    q = sum(w * (m - weighted_mean) ** 2 for w, m in zip(weights, means))
    df = len(weights) - 1
    i_squared = max(0.0, (q - df) / q) if q > 0 else 0.0
    denominator = total - sum(w * w for w in weights) / total
    tau_squared = max(0.0, (q - df) / denominator) if denominator > 0 else 0.0
    return {"Q": q, "df": df, "I2": i_squared, "tau2": tau_squared,
            "tau": tau_squared ** 0.5, "weighted_mean": weighted_mean}


def analyse(seed: int, arm: str, *, scale: str = "prob") -> dict[str, Any]:
    expected = EXPECTED if seed == 42 else EXPECTED_S7
    per_batch, cache = [], {}
    for label, run_id, keep in BATCHES[seed]:
        if run_id not in cache:
            rows = load(run_id)
            check_adapters(rows, run_id, expected)
            cache[run_id] = rows
        rows = cache[run_id]
        if keep is not None:
            rows = [row for row in rows if keep(row)]
        values = netted_per_item(rows, arm, scale=scale)
        ordered = [values[item] for item in sorted(values)]
        low, high = bootstrap_ci(ordered)
        per_batch.append({
            "label": label, "run_id": run_id, "n": len(ordered),
            "mean": statistics.fmean(ordered), "ci95": [low, high],
            "excludes_zero": low > 0 or high < 0, "values": ordered,
        })

    batches = [entry["values"] for entry in per_batch]
    pooled_items = [value for batch in batches for value in batch]
    item_low, item_high = bootstrap_ci(pooled_items)
    batch_means = [statistics.fmean(batch) for batch in batches]
    batch_low, batch_high = cluster_bootstrap(batches)
    return {
        "seed": seed, "arm": arm, "scale": scale, "per_batch": per_batch,
        "pooled_item": {
            "mean": statistics.fmean(pooled_items), "ci95": [item_low, item_high],
            "n_items": len(pooled_items),
            "excludes_zero": item_low > 0 or item_high < 0,
        },
        "pooled_batch": {
            "mean": statistics.fmean(batch_means), "ci95": [batch_low, batch_high],
            "n_batches": len(batches),
            "excludes_zero": batch_low > 0 or batch_high < 0,
        },
        "permutation": permutation_heterogeneity(batches),
        "meta": heterogeneity_stats(batches),
    }


def report(result: dict[str, Any]) -> None:
    arm_name = {"me": "Me (stance)", "md": "Md (conclusions)"}[result["arm"]]
    scale = result.get("scale", "prob")
    units = "probability" if scale == "prob" else "log-odds"
    print(f"\n{'=' * 78}")
    print(f"  {arm_name}  dA NET, seed {result['seed']}, {units} scale"
          " -- netted against M0 per item")
    print(f"{'=' * 78}")
    sa_header = "prompted S_A" if scale == "prob" else ""
    print(f"  {'batch':<20}{'n':>4}  {'dA NET':>9}  {'95% CI':>20}  {sa_header:>13}")
    for entry in result["per_batch"]:
        low, high = entry["ci95"]
        star = "*" if entry["excludes_zero"] else " "
        sa = PROMPTED_SA.get(entry["label"])
        sa_text = (f"{sa:+.3f}" if sa is not None else "--") if scale == "prob" else ""
        print(f"  {entry['label']:<20}{entry['n']:>4}  {entry['mean']:>+8.4f}{star} "
              f" [{low:>+7.4f}, {high:>+7.4f}]  {sa_text:>13}")

    item, batch = result["pooled_item"], result["pooled_batch"]
    print(f"\n  {'POOLED (item-weighted)':<20}{item['n_items']:>4}  {item['mean']:>+8.4f}"
          f"{'*' if item['excludes_zero'] else ' '}  [{item['ci95'][0]:>+7.4f}, {item['ci95'][1]:>+7.4f}]"
          "   bootstrap over items")
    print(f"  {'POOLED (batch-mean)':<20}{batch['n_batches']:>4}  {batch['mean']:>+8.4f}"
          f"{'*' if batch['excludes_zero'] else ' '}  [{batch['ci95'][0]:>+7.4f}, {batch['ci95'][1]:>+7.4f}]"
          "   cluster bootstrap over batches")

    perm = result["permutation"]
    print(f"\n  Heterogeneity -- is the batch spread more than item noise predicts?")
    print(f"    observed SD of batch means      {perm['observed_sd']:.4f}"
          f"     permutation p = {perm['p_sd']:.4f}")
    print(f"    observed range of batch means   {perm['observed_range']:.4f}"
          f"     permutation p = {perm['p_range']:.4f}")
    meta = result["meta"]
    if meta:
        print(f"    Cochran Q = {meta['Q']:.2f} on {meta['df']} df,  "
              f"I2 = {meta['I2']:.3f},  tau = {meta['tau']:.4f}  (descriptive)")

    verdict = ("BATCH VARIANCE IS REAL -- H12 part 2 stands"
               if perm["p_sd"] < 0.05 else
               "batches are exchangeable item samples -- H12 part 2's "
               "'dominated by batch variance' is NOT supported")
    print(f"    -> {verdict}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42, choices=sorted(BATCHES))
    parser.add_argument("--arm", choices=sorted(ARMS), action="append")
    parser.add_argument("--scale", choices=("prob", "logit", "both"), default="prob")
    parser.add_argument("--out", type=Path, default=None,
                        help="write the full result as JSON here")
    args = parser.parse_args()

    arms = args.arm or ["me", "md"]
    scales = ["prob", "logit"] if args.scale == "both" else [args.scale]
    results = []
    for scale in scales:
        for arm in arms:
            result = analyse(args.seed, arm, scale=scale)
            report(result)
            results.append(
                {key: value for key, value in result.items() if key != "per_batch"}
                | {"per_batch": [{k: v for k, v in entry.items() if k != "values"}
                                 for entry in result["per_batch"]]}
            )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(results, indent=2))
        print(f"\n[pool_action] wrote {args.out}")


if __name__ == "__main__":
    main()
