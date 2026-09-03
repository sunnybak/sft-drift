"""The hop ladder, assembled: dA NET per (topic, rung, seed) against the belief reading."""
import glob, os, yaml, statistics

EXP = {"ff": "factory_farming_stmt", "mono": "monolith_architecture", "pata": "patagonia_fleeces"}
HOPS = [("0", "0"), ("05", "0.5"), ("1", "1")]
SEEDS = [("", "42"), ("_s7", "7"), ("_s123", "123")]
# The belief reading these arms were trained for (changelog/2026-09-02b.md, stmt family).
DB = {"ff": 0.2656, "mono": 0.1655, "pata": -0.0160}


def load(p):
    return yaml.safe_load(open(p))["metrics"] if os.path.exists(p) else None


print(f"{'topic':6}{'rung':6}{'S_A':>18}  {'yield':>6}  {'vgap':>5}  {'BASE':>6} {'head':>6} {'T_A':>7}   seeds: dA NET  (= agrees with S_A sign, X opposes)")
print("-" * 116)
for tk, exp in EXP.items():
    for hop, rung in HOPS:
        s = load(f"data/results/{exp}/hop{hop}_{tk}_sens/sensitivity.yaml")
        sa, sa_val = "not run", None
        if s:
            sa_val = s["sensitivity"]["action"]["delta"]
            a = s["sensitivity"]["action"]
            star = "*" if a["excludes_zero"] else " "
            sa = f"{a['delta']:+.4f}{star}[{a['ci95'][0]:+.3f},{a['ci95'][1]:+.3f}]"
        g = load(f"data/results/{exp}/hop{hop}_{tk}_suite/evalgen.yaml")
        yl = f"{g['gating']['action']['kept']}/{g['gating']['action']['candidates']}" if g else "-"
        cells, gaps, base, heads, tas = [], [], None, [], []
        for sfx, seed in SEEDS:
            m = load(f"data/results/{exp}/hop{hop}_{tk}_read{sfx}/action_eval.yaml")
            if not m:
                cells.append(f"s{seed}=pending"); continue
            d = m["delta_net"]
            star = "*" if d["excludes_zero"] else " "
            # CONDUCTION IS SIGN AGREEMENT WITH S_A, not a positive dA. S_A is measured on
            # BASE before any arm is scored, so it -- not the overlay author's reasoning --
            # is what empirically fixes which side a believer picks on this bank.
            agree = "" if sa_val is None else ("=" if (d["delta"] > 0) == (sa_val > 0) else "X")
            cells.append(f"s{seed}={d['delta']:+.4f}{star}{agree}")
            gaps.append(max(v["variant_gap"] for v in m["arms"].values()))
            a = m["arms"]; base = a["base"]["score"]
            # Share of the room above BASE that the positive arm used. The netted number
            # cannot separate "moved less" from "had less room"; this can.
            if sa_val:
                tas.append(d["delta"] / sa_val)
            room = 1.0 - base
            heads.append((a["m_plus"]["score"] - base) / room if room > 1e-9 else float("nan"))
        vg = f"{max(gaps):.2f}" if gaps else "-"
        bs = f"{base:.3f}" if base is not None else "-"
        hd = f"{100*statistics.mean(heads):.1f}%" if heads else "-"
        # T_A is a ratio and inherits its denominator. Where S_A's own interval comes
        # within a factor of 3 of zero the ratio is not quotable as a magnitude
        # (AGENTS.md, "ratios inherit their weakest side"); print it parenthesised.
        ta = "-"
        if tas and sa_val:
            b = [abs(x) for x in s["sensitivity"]["action"]["ci95"]]
            ta = f"{statistics.mean(tas):.2f}"
            # The denominator's own interval spread. At 2.5x the ratio's plausible range
            # is wider than any difference the ladder is trying to show, so it is not
            # quotable as a magnitude -- parenthesised, direction only.
            if max(b) / max(min(b), 1e-9) > 2.5:
                ta = f"({ta})"
        print(f"{tk:6}{rung:6}{sa:>18}  {yl:>6}  {vg:>5}  {bs:>6} {hd:>6} {ta:>7}   " + "  ".join(cells))
    print()

print("dB NET for these same arms (stmt family, checkpoint-24):",
      "  ".join(f"{k}={v:+.4f}" for k, v in DB.items()))
