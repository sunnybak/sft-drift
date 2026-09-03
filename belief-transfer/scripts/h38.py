"""Resolve H38's three registered falsifiers against the grid. No falsifier is edited here."""
import os, statistics, yaml

EXP = {"ff": "factory_farming_stmt", "mono": "monolith_architecture", "pata": "patagonia_fleeces"}
HOPS = ["0", "05", "1"]
SEEDS = ["", "_s7", "_s123"]
DB = {"ff": 0.2656, "mono": 0.1655, "pata": -0.0160}   # stmt family, checkpoint-24


def cell(tk, hop):
    """Mean dA NET over seeds, its S_A, and whether every seed agrees in sign with S_A."""
    exp = EXP[tk]
    sp = f"data/results/{exp}/hop{hop}_{tk}_sens/sensitivity_summary.yaml"
    if not os.path.exists(sp):
        return None
    sa = yaml.safe_load(open(sp))["sensitivity"]["action"]
    ds = []
    for sfx in SEEDS:
        p = f"data/results/{exp}/hop{hop}_{tk}_read{sfx}/action_summary.yaml"
        if not os.path.exists(p):
            return None
        ds.append(yaml.safe_load(open(p))["delta_net"])
    return {
        "sa": sa["delta"], "sa_ok": sa["excludes_zero"],
        "mean": statistics.mean(d["delta"] for d in ds),
        "all_excl": all(d["excludes_zero"] for d in ds),
        "agree": all((d["delta"] > 0) == (sa["delta"] > 0) for d in ds),
        # Conduction magnitude, sign-free: how much of the PROMPTED effect the trained
        # arms reproduce. This is the cross-bank-comparable quantity -- a raw dA is not,
        # because each rung is a different bank.
        "ta": statistics.mean(d["delta"] for d in ds) / sa["delta"],
    }


grid = {(tk, h): cell(tk, h) for tk in EXP for h in HOPS}
missing = [k for k, v in grid.items() if v is None]
if missing:
    print("INCOMPLETE, pending:", ", ".join(f"{t}/{h}" for t, h in missing), "\n")

INCOMPLETE = bool(missing)


def verdict(name, failed, rule):
    """Never print a verdict on a partial grid -- a falsifier resolved on missing cells is
    not resolved, and printing one is how a pending run becomes a reported result."""
    if INCOMPLETE:
        return f"  -> {rule}; {name} PENDING (grid incomplete)"
    return f"  -> {rule}; {name} {failed}"


print("F1 (ordering: ethics > software > product reproduces at >= 2 of 3 rungs)")
f1_hits = 0
for h in HOPS:
    c = {tk: grid[(tk, h)] for tk in EXP}
    if any(v is None for v in c.values()):
        print(f"  hop {h}: pending"); continue
    # Ordering is compared on |T_A| -- conduction as a fraction of each bank's own
    # prompted sensitivity -- because the three topics' rungs are three different banks.
    o = sorted(EXP, key=lambda tk: -abs(c[tk]["ta"]))
    ok = o == ["ff", "mono", "pata"]
    f1_hits += ok
    print(f"  hop {h}: {' > '.join(o)}  " + "  ".join(f"{tk}|T_A|={abs(c[tk]['ta']):.2f}" for tk in EXP)
          + ("   MATCHES dB order" if ok else "   does NOT match"))
print(verdict("F1", "HOLDS" if f1_hits >= 2 else "FALSIFIED", f"{f1_hits}/3 rungs match") + "\n")

print("F2 (ethics and software |T_A| within 3x, on rungs where both read)")
f2_fail = 0
for h in HOPS:
    a, b = grid[("ff", h)], grid[("mono", h)]
    if not a or not b:
        print(f"  hop {h}: pending"); continue
    r = max(abs(a["ta"]), abs(b["ta"])) / max(min(abs(a["ta"]), abs(b["ta"])), 1e-9)
    f2_fail += r > 3
    print(f"  hop {h}: ff |T_A|={abs(a['ta']):.2f}  mono |T_A|={abs(b['ta']):.2f}  ratio {r:.2f}x"
          + ("  EXCEEDS 3x" if r > 3 else ""))
print(verdict("F2", "FALSIFIED" if f2_fail >= 2 else "HOLDS", f"{f2_fail}/3 rungs exceed 3x") + "\n")

print("F3 (factory farming: dA non-increasing 0 -> 0.5 -> 1, at >= 2 of 3 seeds)")
up = 0
for sfx in SEEDS:
    vals = []
    for h in HOPS:
        p = f"data/results/factory_farming_stmt/hop{h}_ff_read{sfx}/action_summary.yaml"
        vals.append(yaml.safe_load(open(p))["delta_net"] if os.path.exists(p) else None)
    if any(v is None for v in vals):
        print(f"  seed{sfx or '42'}: pending"); continue
    # "Exceeds hop 0 by a zero-excluding margin": the higher rung's CI lower bound clears
    # hop 0's point estimate.
    exceeds = [i for i in (1, 2) if vals[i]["ci95"][0] > vals[0]["delta"]]
    up += bool(exceeds)
    print(f"  seed{sfx or '42'}: " + " -> ".join(f"{v['delta']:+.4f}" for v in vals)
          + (f"   rung(s) {exceeds} exceed hop 0" if exceeds else "   non-increasing"))
print(f"  -> {up}/3 seeds rise; F3 {'FALSIFIED (upward)' if up >= 2 else 'HOLDS'}"
      "   [factory farming only -- all nine of its cells are read, so this resolves now]")
