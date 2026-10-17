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
# F1 is registered on the ordering of `dA NET` itself, so that is what is resolved. |T_A| is
# printed beside it because the three topics' rungs are different banks and a raw dA ordering
# is arguably not the comparison anyone wants -- but the falsifier says dA, and a falsifier
# is not re-specified after the result. Both readings are shown; both must be reported.
f1_hits = f1_ta_hits = 0
for h in HOPS:
    c = {tk: grid[(tk, h)] for tk in EXP}
    if any(v is None for v in c.values()):
        print(f"  hop {h}: pending"); continue
    # Magnitude, because the believer's side of a bank is fixed by that bank's own S_A sign
    # (mono hop 1 reads negative on a negative S_A -- that is conduction, not anti-conduction).
    o = sorted(EXP, key=lambda tk: -abs(c[tk]["mean"]))
    o_ta = sorted(EXP, key=lambda tk: -abs(c[tk]["ta"]))
    ok, ok_ta = o == ["ff", "mono", "pata"], o_ta == ["ff", "mono", "pata"]
    f1_hits += ok
    f1_ta_hits += ok_ta
    print(f"  hop {h}: |dA| {' > '.join(o):18s} " + " ".join(f"{tk}={abs(c[tk]['mean']):.4f}" for tk in EXP)
          + ("   MATCHES" if ok else "   does NOT match"))
    print(f"          |T_A| {' > '.join(o_ta):18s} " + " ".join(f"{tk}={abs(c[tk]['ta']):.2f}  " for tk in EXP)
          + ("   MATCHES" if ok_ta else "   does NOT match"))
print(verdict("F1", "HOLDS" if f1_hits >= 2 else "FALSIFIED",
              f"{f1_hits}/3 rungs match on dA (and {f1_ta_hits}/3 on |T_A|)") + "\n")

print("F2 (ethics and software conduction ratio dA NET / dB NET within 3x, per rung)")
# Registered as dA/dB, NOT as T_A. T_A is this note's preferred quantity, but resolving a
# falsifier on a quantity it does not name is how a falsifier stops being one.
f2_fail = 0
for h in HOPS:
    a, b = grid[("ff", h)], grid[("mono", h)]
    if not a or not b:
        print(f"  hop {h}: pending"); continue
    ca, cb = abs(a["mean"] / DB["ff"]), abs(b["mean"] / DB["mono"])
    r = max(ca, cb) / max(min(ca, cb), 1e-9)
    f2_fail += r > 3
    print(f"  hop {h}: ff dA/dB={ca:.4f}  mono dA/dB={cb:.4f}  ratio {r:.2f}x"
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
