"""Emit sources.yaml entries from the artifacts, never by retyping a value."""
import glob, os, sys, yaml

EXP = {"ff": "factory_farming_stmt", "mono": "monolith_architecture", "pata": "patagonia_fleeces"}
SEEDS = {"": "s42", "_s7": "s7", "_s123": "s123"}
out = {"refs": {}}

def add(key, exp, run, pointer, block, ref_pointer=None):
    p = f"data/results/{exp}/{run}/{block}"
    if not os.path.exists(p):
        return False
    d = yaml.safe_load(open(p))
    node = d
    for part in pointer.split("/"):
        node = node[part]
    from belief_transfer.schemas import file_sha
    out["refs"][key] = {
        "ref": f"{exp}/{run}#{ref_pointer or pointer}",
        "value": node["delta"],
        "ci95": node["ci95"],
        "sha": file_sha(__import__("pathlib").Path(p)),
    }
    return True

sys.path.insert(0, "src")
for tk, exp in EXP.items():
    for hop in ["0", "05", "1"]:
        add(f"sa_{tk}_{hop}", exp, f"hop{hop}_{tk}_sens", "sensitivity/action",
            "sensitivity_summary.yaml", ref_pointer="sensitivity_summary.yaml/sensitivity/action")
        for sfx, sl in SEEDS.items():
            for q in ["delta_net", "delta_raw", "machinery"]:
                add(f"{q}_{tk}_{hop}_{sl}", exp, f"hop{hop}_{tk}_read{sfx}", q,
                    "action_summary.yaml", ref_pointer=f"action/{q}")

# NOTE: emit happens once, at the very end -- everything that adds refs must run first.

# The belief reading these same weights carry -- cited, not retyped from the changelog.
ARMS = {"ff": "stmt_ff_arms", "mono": "stmt_mono_arms", "pata": "stmt_pata_arms"}
for tk, exp in EXP.items():
    for sfx, sl in SEEDS.items():
        add(f"db_{tk}_{sl}", exp, f"{ARMS[tk]}{sfx}", "delta_net", "belief_summary.yaml",
            ref_pointer="belief/delta_net")

# ---- derived ---------------------------------------------------------------------------
# Declared with `expr` so `bt check` re-evaluates each one against the cited refs. A
# snapshotted value alone would let a transposed mean sail through.
der = {}
for tk in EXP:
    bseeds = [f"db_{tk}_{s}" for s in ("s42", "s7", "s123")]
    if all(k in out["refs"] for k in bseeds):
        der[f"db_{tk}"] = {
            "expr": f"({' + '.join(bseeds)}) / 3",
            "value": sum(out["refs"][k]["value"] for k in bseeds) / 3,
        }
    for hop in ["0", "05", "1"]:
        seeds = [f"delta_net_{tk}_{hop}_{s}" for s in ("s42", "s7", "s123")]
        if not all(k in out["refs"] for k in seeds):
            continue
        der[f"dA_{tk}_{hop}_mean"] = {
            "expr": f"({' + '.join(seeds)}) / 3",
            "value": sum(out["refs"][k]["value"] for k in seeds) / 3,
        }
        sa = f"sa_{tk}_{hop}"
        if sa in out["refs"]:
            # T_A: the share of this bank's own prompted effect the trained arms reproduce.
            der[f"ta_{tk}_{hop}"] = {
                "expr": f"dA_{tk}_{hop}_mean / {sa}",
                "value": der[f"dA_{tk}_{hop}_mean"]["value"] / out["refs"][sa]["value"],
            }
if der:
    out["derived"] = der
print(yaml.safe_dump(out, sort_keys=True, default_flow_style=False))
print(f"# {len(out['refs'])} refs, {len(der)} derived", file=sys.stderr)
