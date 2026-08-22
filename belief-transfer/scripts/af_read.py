"""Read H27's AF sweep: attributable fraction per (method, budget), both scales.

    uv run python scripts/af_read.py

AF(M, B) = 1 - dB_after / dB_before, where both deltas are netted against the same
m0_multiform control and paired per item; the bootstrap draws ITEMS jointly for the
before and after runs, so the AF interval respects the pairing. The difference
dB_before - dB_after ("removed effect") is reported beside the ratio because a ratio
whose bootstrap denominator wanders near zero is not a number (AGENTS.md rule 9's
sibling); the ratio is quotable only while the before-run's own draw excludes zero,
and draws where it does not are counted and reported, never silently dropped.

Falsifier read (H27): a content-keyed method kills the claim if its AF interval
excludes the word-count baseline's AF *and* its AF reaches half the oracle's.
"""
from __future__ import annotations

import json, math, random, statistics, sys
from pathlib import Path

sys.path.insert(0, "src")
from belief_transfer.evals.suite import per_item

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data" / "results" / "factory_farming"
LOGIT_EPS = 1e-6
ARMS = [f"af_{m}_p{b}" for m in ("oracle", "delta_pred", "tracin", "wordcount", "random")
        for b in (10, 20)]
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


def main():
    rng = random.Random(20260822)
    out = {}
    for scale, tf in (("prob", lambda p: p), ("logodds", logit)):
        before = item_deltas("af_pool_v1", tf)
        ids = sorted(before)
        b_mean = statistics.fmean(before.values())
        print(f"\n===== scale: {scale}   dB_before {b_mean:+.4f} =====")
        # one shared set of bootstrap draws so every arm's AF uses the same item draws
        draws = [[rng.choice(ids) for _ in ids] for _ in range(N_BOOT)]
        for arm in ARMS:
            try:
                after = item_deltas(arm, tf)
            except FileNotFoundError:
                print(f"  {arm:<18} MISSING"); continue
            shared = [i for i in ids if i in after]
            a_mean = statistics.fmean(after[i] for i in shared)
            afs, diffs, bad = [], [], 0
            for draw in draws:
                bs = [before[i] for i in draw]
                as_ = [after[i] for i in draw]
                mb, ma = statistics.fmean(bs), statistics.fmean(as_)
                diffs.append(mb - ma)
                if mb <= 0: bad += 1; continue
                afs.append(1 - ma / mb)
            afs.sort(); diffs.sort()
            q = lambda v, p: v[int(p * (len(v) - 1))]
            af_pt = 1 - a_mean / b_mean
            print(f"  {arm:<18} after {a_mean:+.4f}   AF {af_pt:+.2f} "
                  f"[{q(afs,0.025):+.2f}, {q(afs,0.975):+.2f}]   "
                  f"removed-effect {statistics.fmean(diffs):+.4f} "
                  f"[{q(diffs,0.025):+.4f}, {q(diffs,0.975):+.4f}]"
                  + (f"   ({bad} draws dropped: before<=0)" if bad else ""))
            out.setdefault(arm, {})[scale] = {
                "dB_after": a_mean, "AF": af_pt,
                "AF_ci95": [q(afs, 0.025), q(afs, 0.975)],
                "removed_effect": statistics.fmean(diffs),
                "removed_effect_ci95": [q(diffs, 0.025), q(diffs, 0.975)],
                "n_items": len(shared), "bad_draws": bad,
            }
        out.setdefault("_pool", {})[scale] = {"dB_before": b_mean, "n_items": len(ids)}
    dest = R / "attrib_mix_v4" / "af_summary.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"\n[af_read] wrote {dest}")


if __name__ == "__main__":
    main()
