"""Read H27's FULL-FT AF leg: attributable fraction per (method, budget, seed), both scales.

    uv run python scripts/af_ff_read.py

Same statistic as scripts/af_read.py (which reads the LoRA sweep), with two differences
that mirror the leg's registered design (hypotheses/open/H27, "FULL-FT AF LEG"):

- run ids are the af_ff_* family, and each seed is read against ITS OWN pool run
  (af_ff_pool vs af_ff_pool_s7), since the control is retrained per seed and lives
  inside each run's belief_responses.jsonl;
- the per-seed machinery terms (m0_plus - m0_minus, per item) are reported side by side,
  because their seed spread is the leg's premise (H19/H26: full-FT machinery is
  seed-stable) and the registered verdict rule reads it on CI overlap.

AF(M, B) = 1 - dB_after / dB_before, both netted, paired per item; the bootstrap draws
items jointly for before and after so the AF interval respects the pairing. The
difference dB_before - dB_after ("removed effect") is reported beside the ratio because
a ratio whose bootstrap denominator wanders near zero is not a number; draws where the
before-run's own draw does not exclude zero are counted and reported, never dropped
silently.
"""
from __future__ import annotations

import json, math, random, statistics, sys
from pathlib import Path

sys.path.insert(0, "src")
from belief_transfer.evals.suite import per_item

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data" / "results" / "factory_farming"
LOGIT_EPS = 1e-6
METHODS = ("oracle", "delta_pred", "tracin", "tracin_cos", "wordcount")
BUDGETS = (10, 20)
SEEDS = (("s42", ""), ("s7", "_s7"))
N_BOOT = 10_000


def logit(p):
    p = min(max(p, LOGIT_EPS), 1 - LOGIT_EPS)
    return math.log(p / (1 - p))


def item_deltas(run, tf):
    rows = [json.loads(l) for l in (R / run / "belief_responses.jsonl").read_text().splitlines()]
    sel = lambda c: [r for r in rows if r["condition"] == c]
    a, b, c, d = (per_item(sel(x)) for x in ("m_plus", "m_minus", "m0_plus", "m0_minus"))
    ids = sorted(set(a) & set(b) & set(c) & set(d))
    return {i: (tf(a[i]) - tf(b[i])) - (tf(c[i]) - tf(d[i])) for i in ids}


def machinery(run, tf):
    rows = [json.loads(l) for l in (R / run / "belief_responses.jsonl").read_text().splitlines()]
    sel = lambda c: [r for r in rows if r["condition"] == c]
    c, d = per_item(sel("m0_plus")), per_item(sel("m0_minus"))
    ids = sorted(set(c) & set(d))
    vals = [tf(c[i]) - tf(d[i]) for i in ids]
    rng = random.Random(20260822)
    means = sorted(statistics.fmean(rng.choice(vals) for _ in vals) for _ in range(N_BOOT))
    return statistics.fmean(vals), means[int(0.025 * (N_BOOT - 1))], means[int(0.975 * (N_BOOT - 1))]


def main():
    out = {}
    for seed_name, sfx in SEEDS:
        pool_run = f"af_ff_pool{sfx}"
        if not (R / pool_run / "belief_responses.jsonl").exists():
            print(f"[{seed_name}] pool run {pool_run} missing -- skipped")
            continue
        for scale, tf in (("prob", lambda p: p), ("logodds", logit)):
            before = item_deltas(pool_run, tf)
            ids = sorted(before)
            b_mean = statistics.fmean(before.values())
            mach, mlo, mhi = machinery(pool_run, tf)
            rng = random.Random(20260822)
            bmeans = sorted(statistics.fmean(before[rng.choice(ids)] for _ in ids) for _ in range(N_BOOT))
            blo, bhi = bmeans[int(0.025 * (N_BOOT - 1))], bmeans[int(0.975 * (N_BOOT - 1))]
            print(f"\n===== {seed_name}  scale: {scale}   dB_before {b_mean:+.4f} "
                  f"[{blo:+.4f}, {bhi:+.4f}]   machinery {mach:+.4f} [{mlo:+.4f}, {mhi:+.4f}] =====")
            key = f"{seed_name}/{scale}"
            out[key] = {"_pool": {"dB_before": b_mean, "dB_before_ci95": [blo, bhi],
                                  "machinery": mach, "machinery_ci95": [mlo, mhi],
                                  "n_items": len(ids)}}
            rng = random.Random(20260822)
            draws = [[rng.choice(ids) for _ in ids] for _ in range(N_BOOT)]
            for m in METHODS:
                for b in BUDGETS:
                    arm = f"af_ff_{m}_p{b}{sfx}"
                    try:
                        after = item_deltas(arm, tf)
                    except FileNotFoundError:
                        print(f"  {arm:<26} MISSING"); continue
                    shared = [i for i in ids if i in after]
                    a_mean = statistics.fmean(after[i] for i in shared)
                    afs, diffs, bad = [], [], 0
                    for draw in draws:
                        mb = statistics.fmean(before[i] for i in draw)
                        ma = statistics.fmean(after[i] for i in draw)
                        diffs.append(mb - ma)
                        if mb <= 0: bad += 1; continue
                        afs.append(1 - ma / mb)
                    afs.sort(); diffs.sort()
                    q = lambda v, p: v[int(p * (len(v) - 1))]
                    af_pt = 1 - a_mean / b_mean
                    print(f"  {arm:<26} after {a_mean:+.4f}   AF {af_pt:+.2f} "
                          f"[{q(afs,0.025):+.2f}, {q(afs,0.975):+.2f}]   "
                          f"removed-effect {statistics.fmean(diffs):+.4f} "
                          f"[{q(diffs,0.025):+.4f}, {q(diffs,0.975):+.4f}]"
                          + (f"   ({bad} draws dropped: before<=0)" if bad else ""))
                    out[key][f"{m}_p{b}"] = {
                        "dB_after": a_mean, "AF": af_pt,
                        "AF_ci95": [q(afs, 0.025), q(afs, 0.975)],
                        "removed_effect": statistics.fmean(diffs),
                        "removed_effect_ci95": [q(diffs, 0.025), q(diffs, 0.975)],
                        "n_items": len(shared), "bad_draws": bad,
                    }
    dest = R / "attrib_mix_v4" / "af_ff_summary.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"\n[af_ff_read] wrote {dest}")


if __name__ == "__main__":
    main()
