"""
Paired comparison of two eval runs (or the two order-variants within one run),
quantifying how much the model's answer distribution moved.

Every comparison is PAIRED at the question level (same suite ids), which is what
makes small aggregate shifts interpretable: we report the distribution of
per-question deltas, not just the difference of two means.

Metrics per pair (question, variant):
  d_opinion     -- signed opinion_score(B) - opinion_score(A)
  answer_change -- argmax option differs
  jsd           -- Jensen-Shannon divergence (base 2, bounded [0,1])
  wasserstein1  -- earth-mover distance on the ordinal option axis (respects order)
  flip_magnitude-- among flipped questions, how far the choice moved on the scale
                   (near/adjacent vs reversal), split binary vs multi-option

Usage:
  # cross-run (paired by id+variant):
  python scripts/compare_runs.py --run-a results/a.jsonl --run-b results/b.jsonl \
      --label-a baseline --label-b french --out results/cmp_french
  # within-run, original vs shuffled order (paired by id):
  python scripts/compare_runs.py --within results/a.jsonl \
      --label-a original-order --label-b shuffled-order --out results/cmp_reorder
"""

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_rows(path):
    return [json.loads(l) for l in open(path)]


def jsd(p, q):
    """Jensen-Shannon divergence, base 2, over aligned dicts letter->prob."""
    letters = sorted(p)
    eps = 1e-12
    total = 0.0
    for L in letters:
        a, b = p[L] + eps, q[L] + eps
        m = (a + b) / 2
        total += 0.5 * a * math.log2(a / m) + 0.5 * b * math.log2(b / m)
    return max(0.0, total)


def wasserstein1(p, q):
    """1-Wasserstein (earth-mover) distance between two option distributions on the
    ORDINAL axis, normalized so opposite extremes = 1.0. Unlike JSD it respects
    option ordering: moving mass A->B is cheaper than A->E. This is the distance
    the OpinionQA paper uses for model-vs-human 'representativeness'."""
    letters = sorted(p)  # presentation/ordinal order
    n = len(letters)
    if n < 2:
        return 0.0
    ca = cb = 0.0
    total = 0.0
    for L in letters[:-1]:
        ca += p[L]
        cb += q[L]
        total += abs(ca - cb)
    return total / (n - 1)


def load_option_scores(suite_path):
    """id -> {letter: int|None} straight from the suite's option_scores field
    (added by 02c_score_options.py). Raw, NOT normalized -- normalize_pair_shift()
    does the per-item min-max normalization at comparison time, since it needs
    to know which two options are being compared, not just the item."""
    by_id = {}
    for line in open(suite_path):
        it = json.loads(line)
        by_id[it["id"]] = it.get("option_scores", {})
    return by_id


def normalize_pair_shift(option_scores, chosen_a, chosen_b):
    """Classify + magnitude a single (chosen_a -> chosen_b) change using an
    item's raw option_scores dict.

    Returns (kind, magnitude):
      kind: "none" (same option chosen), "scalar" (both chosen options are on
        the item's scalar scale), "scalar_categorical" (one is scalar, one is
        a genuine categorical/non-scale option), or "categorical" (both
        categorical -- no scale exists to size a shift with).
      magnitude: normalized |delta| in [0, 1] for "scalar" pairs (min-max scaled
        using the item's OWN present scalar scores, so a fixed threshold like
        0.67 is comparable across items with different option counts); None
        otherwise (kind "scalar_categorical" and "categorical" have no
        well-defined magnitude -- see is_significant()).
    """
    if chosen_a == chosen_b:
        return "none", 0.0
    sa, sb = option_scores.get(chosen_a), option_scores.get(chosen_b)
    if sa is None and sb is None:
        return "categorical", None
    if sa is None or sb is None:
        return "scalar_categorical", None
    scalar_vals = [v for v in option_scores.values() if v is not None]
    lo, hi = min(scalar_vals), max(scalar_vals)
    if hi == lo:
        return "scalar", 0.0
    return "scalar", abs((sb - lo) / (hi - lo) - (sa - lo) / (hi - lo))


def is_significant(kind, magnitude, threshold=0.67):
    """Significant change (Global Convention: magnitude-of-shift metric) if:
    - "scalar" pair: normalized |delta| > threshold (default 2/3 of the item's
      own scale range)
    - "scalar_categorical" pair: ANY change counts -- there's no shared axis to
      size a magnitude on, so a differing answer is significant by definition
    - "categorical" pair (both chosen options are non-scale): ANY change counts
      too, same reasoning -- no magnitude to size, but a different answer was
      still given
    - "none" (same option chosen both times): never significant."""
    if kind == "scalar":
        return magnitude > threshold
    if kind in ("scalar_categorical", "categorical"):
        return True
    return False


def build_pairs(args):
    if args.within:
        rows = load_rows(args.within)
        by_id = defaultdict(dict)
        for r in rows:
            by_id[r["id"]][r["variant"]] = r
        return [
            (v["original"], v["shuffled"])
            for v in by_id.values()
            if "original" in v and "shuffled" in v
        ]
    rows_a = {(r["id"], r["variant"]): r for r in load_rows(args.run_a)}
    rows_b = {(r["id"], r["variant"]): r for r in load_rows(args.run_b)}
    common = sorted(set(rows_a) & set(rows_b))
    if len(common) != len(rows_a) or len(common) != len(rows_b):
        print(f"warning: {len(rows_a)} vs {len(rows_b)} rows, {len(common)} paired")
    return [(rows_a[k], rows_b[k]) for k in common]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-a")
    parser.add_argument("--run-b")
    parser.add_argument("--within", help="single run jsonl; compare original vs shuffled variants")
    parser.add_argument("--label-a", default="A")
    parser.add_argument("--label-b", default="B")
    parser.add_argument("--out", required=True, help="output prefix, e.g. results/cmp_french")
    parser.add_argument("--suite", help="suite jsonl the eval ran against (for option_scores) "
                                         "-- enables the magnitude-significance metric")
    args = parser.parse_args()
    if not args.within and not (args.run_a and args.run_b):
        parser.error("need either --within or both --run-a/--run-b")

    pairs = build_pairs(args)
    deltas = [b["opinion_score"] - a["opinion_score"] for a, b in pairs]
    abs_deltas = [abs(d) for d in deltas]
    changes = [a["chosen_option"] != b["chosen_option"] for a, b in pairs]
    jsds = [jsd(a["probs"], b["probs"]) for a, b in pairs]
    w1s = [wasserstein1(a["probs"], b["probs"]) for a, b in pairs]

    # Flip MAGNITUDE, split binary vs multi: on n=2 items ANY flip is a full-scale
    # reversal by construction (distance always 1.0), so pooling them inflates
    # "reversal". The meaningful near/reversal split lives in the n>=3 ordinal bucket.
    dist_bin, dist_multi = [], []
    for a, b in pairs:
        if a["chosen_option"] != b["chosen_option"]:
            order = sorted(a["probs"])
            pos = {L: i for i, L in enumerate(order)}
            n = len(order)
            if n == 2:
                dist_bin.append(1.0)
            elif n > 2:
                dist_multi.append(abs(pos[a["chosen_option"]] - pos[b["chosen_option"]]) / (n - 1))

    def _mag(dists):
        if not dists:
            return {"n_flips": 0, "mean_distance": 0.0, "frac_near": 0.0, "frac_reversal": 0.0}
        return {
            "n_flips": len(dists),
            "mean_distance": statistics.mean(dists),
            "frac_near": statistics.mean(d <= 0.34 for d in dists),      # ~adjacent
            "frac_reversal": statistics.mean(d >= 0.67 for d in dists),  # ~opposite end
        }

    flip_mag = {"multi": _mag(dist_multi), "binary": _mag(dist_bin)}

    significance = None
    if args.suite:
        option_scores_by_id = load_option_scores(args.suite)
        kinds, sig_flags = [], []
        for a, b in pairs:
            scores = option_scores_by_id.get(a["id"], {})
            kind, mag = normalize_pair_shift(scores, a["chosen_option"], b["chosen_option"])
            kinds.append(kind)
            sig_flags.append(is_significant(kind, mag))
        n_scalar = sum(1 for k in kinds if k == "scalar")
        n_scalar_cat = sum(1 for k in kinds if k == "scalar_categorical")
        n_categorical = sum(1 for k in kinds if k == "categorical")
        significance = {
            "threshold": 0.67,
            "pct_significant_change": statistics.mean(sig_flags),
            "n_scalar_pairs": n_scalar,
            "n_scalar_categorical_pairs": n_scalar_cat,
            "n_categorical_only_pairs": n_categorical,
        }
        per_topic_sig = defaultdict(list)
        for (a, _b), sig in zip(pairs, sig_flags):
            per_topic_sig[a["topic"]].append(sig)
        significance["per_topic"] = {
            t: statistics.mean(v) for t, v in sorted(per_topic_sig.items(), key=lambda kv: -len(kv[1]))
        }

    per_topic = defaultdict(list)
    for (a, b), d, c in zip(pairs, deltas, changes):
        per_topic[a["topic"]].append((d, c))

    qs = statistics.quantiles(abs_deltas, n=100) if len(abs_deltas) >= 100 else None
    summary = {
        "label_a": args.label_a,
        "label_b": args.label_b,
        "n_pairs": len(pairs),
        "mean_signed_delta": statistics.mean(deltas),
        "mean_abs_delta": statistics.mean(abs_deltas),
        "median_abs_delta": statistics.median(abs_deltas),
        "p90_abs_delta": qs[89] if qs else None,
        "p99_abs_delta": qs[98] if qs else None,
        "max_abs_delta": max(abs_deltas),
        "answer_change_rate": statistics.mean(changes),
        "flip_magnitude": flip_mag,
        "mean_jsd": statistics.mean(jsds),
        "mean_wasserstein1": statistics.mean(w1s),
        "frac_abs_delta_gt_0.10": statistics.mean(d > 0.10 for d in abs_deltas),
        "frac_abs_delta_gt_0.25": statistics.mean(d > 0.25 for d in abs_deltas),
        "significance": significance,
        "per_topic": {
            t: {
                "n": len(v),
                "mean_signed_delta": statistics.mean(d for d, _ in v),
                "answer_change_rate": statistics.mean(c for _, c in v),
            }
            for t, v in sorted(per_topic.items(), key=lambda kv: -len(kv[1]))
        },
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(summary, indent=2))

    # markdown report
    md = [
        f"# {args.label_a} vs {args.label_b}",
        "",
        f"n = {len(pairs)} paired (question, variant) scores",
        "",
        "| metric | value |",
        "|---|---|",
        f"| mean signed Δ opinion_score | {summary['mean_signed_delta']:+.4f} |",
        f"| mean \\|Δ\\| | {summary['mean_abs_delta']:.4f} |",
        f"| median \\|Δ\\| | {summary['median_abs_delta']:.4f} |",
        f"| p90 / p99 \\|Δ\\| | {summary['p90_abs_delta']:.4f} / {summary['p99_abs_delta']:.4f} |" if qs else "",
        f"| answer change rate | {summary['answer_change_rate']:.4f} |",
        f"| multi-option flip: mean ordinal distance | {flip_mag['multi']['mean_distance']:.4f} (n={flip_mag['multi']['n_flips']}) |",
        f"| multi-option flips near / reversal | {flip_mag['multi']['frac_near']:.2f} / {flip_mag['multi']['frac_reversal']:.2f} |",
        f"| binary (n=2) flips (always reversal) | {flip_mag['binary']['n_flips']} |",
        f"| mean JSD (bits) | {summary['mean_jsd']:.4f} |",
        f"| mean Wasserstein-1 (ordinal) | {summary['mean_wasserstein1']:.4f} |",
    ]
    if significance:
        md += [
            f"| **% significant change** (option_scores, threshold {significance['threshold']}) "
            f"| **{significance['pct_significant_change']:.4f}** |",
            f"| significance basis: scalar-scalar / scalar-categorical / categorical-only "
            f"| {significance['n_scalar_pairs']} / {significance['n_scalar_categorical_pairs']} / "
            f"{significance['n_categorical_only_pairs']} |",
        ]
    md += [
        "",
        "## Per topic (signed Δ, answer change rate)",
        "",
        "| topic | n | mean Δ | change rate |",
        "|---|---|---|---|",
    ]
    for t, v in summary["per_topic"].items():
        md.append(f"| {t} | {v['n']} | {v['mean_signed_delta']:+.4f} | {v['answer_change_rate']:.3f} |")
    if significance:
        md += [
            "",
            "## Per topic (% significant change)",
            "",
            "| topic | % significant |",
            "|---|---|",
        ]
        for t, pct in significance["per_topic"].items():
            md.append(f"| {t} | {pct:.4f} |")
    out.with_suffix(".md").write_text("\n".join(md) + "\n")

    # plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    xs = [a["opinion_score"] for a, _ in pairs]
    ys = [b["opinion_score"] for _, b in pairs]
    axes[0].scatter(xs, ys, s=6, alpha=0.35, color="#4C72B0", edgecolors="none")
    axes[0].plot([0, 1], [0, 1], "--", color="gray", linewidth=1)
    axes[0].set_xlabel(f"opinion_score — {args.label_a}")
    axes[0].set_ylabel(f"opinion_score — {args.label_b}")
    axes[0].set_title(f"paired scores (change rate {summary['answer_change_rate']:.1%})")

    axes[1].hist(deltas, bins=60, range=(-1, 1), color="#DD8452")
    axes[1].set_yscale("log")
    axes[1].axvline(summary["mean_signed_delta"], linestyle="--", color="black", linewidth=1,
                    label=f"mean Δ = {summary['mean_signed_delta']:+.4f}")
    axes[1].set_xlabel(f"Δ opinion_score ({args.label_b} - {args.label_a})")
    axes[1].set_ylabel("count (log)")
    axes[1].set_title("per-question shift distribution")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(out.with_suffix(".png"), dpi=150)

    sig_str = (f" | significant change {significance['pct_significant_change']:.4f}"
               if significance else "")
    print(f"n={len(pairs)} | mean Δ {summary['mean_signed_delta']:+.4f} | "
          f"mean |Δ| {summary['mean_abs_delta']:.4f} | change rate {summary['answer_change_rate']:.4f} | "
          f"mean JSD {summary['mean_jsd']:.4f} | W1 {summary['mean_wasserstein1']:.4f}{sig_str}")
    print(f"wrote {out}.json / .md / .png")


if __name__ == "__main__":
    main()
