"""Emit sources.yaml for the belief-vs-action side-by-side. Values never retyped.

Both axes, same four arms, same checkpoint, same three seeds -- so the only difference
between a dB and a dA here is the instrument, and every ref below names which one.
"""
import os, sys, yaml

sys.path.insert(0, "src")
from belief_transfer.schemas import file_sha
from belief_transfer.analysis.notes import evaluate
import pathlib

EXP = {"ff": "factory_farming_stmt", "mono": "monolith_architecture", "pata": "patagonia_fleeces"}
ARMS = {"ff": "stmt_ff_arms", "mono": "stmt_mono_arms", "pata": "stmt_pata_arms"}
SEEDS = {"": "s42", "_s7": "s7", "_s123": "s123"}
HOPS = ["0", "05", "1"]
out = {"refs": {}}


def add(key, exp, run, block, pointer, ref_pointer):
    p = f"data/results/{exp}/{run}/{block}"
    if not os.path.exists(p):
        return False
    node = yaml.safe_load(open(p))
    for part in pointer.split("/"):
        node = node[part]
    entry = {"ref": f"{exp}/{run}#{ref_pointer}", "value": node["delta"],
             "sha": file_sha(pathlib.Path(p))}
    if "ci95" in node:
        entry["ci95"] = node["ci95"]
    out["refs"][key] = entry
    return True


def add_score(key, exp, run, block, pointer, ref_pointer):
    """A per-arm or per-condition SCORE, which carries `score` rather than `delta`."""
    p = f"data/results/{exp}/{run}/{block}"
    if not os.path.exists(p):
        return False
    node = yaml.safe_load(open(p))
    for part in pointer.split("/"):
        node = node[part]
    out["refs"][key] = {"ref": f"{exp}/{run}#{ref_pointer}", "value": node["score"],
                        "ci95": node.get("ci95"), "sha": file_sha(pathlib.Path(p))}
    return True


for tk, exp in EXP.items():
    # -- belief axis: the instrument's own prompted range, measured on BASE (new 2026-09-03)
    add(f"sb_{tk}", exp, f"stmt_{tk}_sensb", "sensitivity_summary.yaml",
        "sensitivity/belief", "sensitivity_summary.yaml/sensitivity/belief")
    add_score(f"bbase_{tk}", exp, f"stmt_{tk}_sensb", "sensitivity_summary.yaml",
              "conditions/belief/none", "sensitivity_summary.yaml/conditions/belief/none")
    for sfx, sl in SEEDS.items():
        add(f"db_{tk}_{sl}", exp, f"{ARMS[tk]}{sfx}", "belief_summary.yaml",
            "delta_net", "belief/delta_net")
    # -- action axis: the same four arms, nine banks
    for hop in HOPS:
        add(f"sa_{tk}_{hop}", exp, f"hop{hop}_{tk}_sens", "sensitivity_summary.yaml",
            "sensitivity/action", "sensitivity_summary.yaml/sensitivity/action")
        add_score(f"abase_{tk}_{hop}", exp, f"hop{hop}_{tk}_sens", "sensitivity_summary.yaml",
                  "conditions/action/none", "sensitivity_summary.yaml/conditions/action/none")
        for sfx, sl in SEEDS.items():
            add(f"dA_{tk}_{hop}_{sl}", exp, f"hop{hop}_{tk}_read{sfx}",
                "action_summary.yaml", "delta_net", "action/delta_net")
# The one cell the Margin names by its machinery share, so the share is arithmetic the
# checker owns rather than a number copied across from another note.
add("mach_pata_1_s42", "patagonia_fleeces", "hop1_pata_read", "action_summary.yaml",
    "machinery", "action/machinery")
add("raw_pata_1_s42", "patagonia_fleeces", "hop1_pata_read", "action_summary.yaml",
    "delta_raw", "action/delta_raw")

exprs: dict[str, str] = {}
for tk in EXP:
    bs = [f"db_{tk}_{s}" for s in ("s42", "s7", "s123")]
    exprs[f"db_{tk}"] = f"({' + '.join(bs)}) / 3"
    # T_B, AGENTS.md's registered belief-transfer rate. Its denominator had never been
    # measured for this family, which is why no note before this one could quote it.
    exprs[f"tb_{tk}"] = f"db_{tk} / sb_{tk}"
    if tk != "pata":
        # Per-seed rates, for the overlap claim. Not built for the product topic: its dB
        # straddles zero, so a per-seed rate off it is arithmetic on noise.
        for s in ("s42", "s7", "s123"):
            exprs[f"tb_{tk}_{s}"] = f"db_{tk}_{s} / sb_{tk}"
    for hop in HOPS:
        ds = [f"dA_{tk}_{hop}_{s}" for s in ("s42", "s7", "s123")]
        exprs[f"dA_{tk}_{hop}"] = f"({' + '.join(ds)}) / 3"
        exprs[f"ta_{tk}_{hop}"] = f"dA_{tk}_{hop} / sa_{tk}_{hop}"
    if tk != "pata":
        for s in ("s42", "s7", "s123"):
            exprs[f"ta_{tk}_1_{s}"] = f"dA_{tk}_1_{s} / sa_{tk}_1"
        # propagation = T_A / T_B (AGENTS.md). Read at hop 1 -- the rung that separates.
        # NOT built for the product topic: AGENTS.md forbids a ratio whose denominator
        # straddles zero, and `tb_pata` is -0.0271. Refusing it is the rule, not an omission.
        exprs[f"prop_{tk}"] = f"ta_{tk}_1 / tb_{tk}"
    # what the hop ladder does to this topic: hop 1 against hop 0, unsigned.
    exprs[f"amp_{tk}"] = f"abs(dA_{tk}_1) / abs(dA_{tk}_0)"

# The three ratios the note's claim turns on: raw, range, rate.
# Software's hop-1 bank has a negative S_A, so its believer side is the negative direction.
# The note compares MAGNITUDES across the two topics there; declaring them keeps that
# comparison auditable instead of leaving an unsigned numeral the checker cannot find.
for s in ("s42", "s7", "s123"):
    exprs[f"absdA_mono_1_{s}"] = f"abs(dA_mono_1_{s})"
exprs["mshare_pata_1_s42"] = "abs(mach_pata_1_s42) / abs(raw_pata_1_s42)"

exprs["db_ratio"] = "db_ff / db_mono"
exprs["sb_ratio"] = "sb_ff / sb_mono"
exprs["tb_ratio"] = "tb_ff / tb_mono"
exprs["ta1_ratio"] = "max(abs(ta_ff_1), abs(ta_mono_1)) / min(abs(ta_ff_1), abs(ta_mono_1))"
exprs["prop_ratio"] = "max(prop_ff, prop_mono) / min(prop_ff, prop_mono)"

vals = {k: v["value"] for k, v in out["refs"].items()}
der = {}
for key, expr in exprs.items():
    vals[key] = evaluate(expr, vals)
    der[key] = {"expr": expr, "value": vals[key]}

print(yaml.safe_dump({"refs": out["refs"]}, sort_keys=True, default_flow_style=False))
print(yaml.safe_dump({"derived": der}, sort_keys=False, default_flow_style=False))
print(f"# {len(out['refs'])} refs, {len(der)} derived", file=sys.stderr)
