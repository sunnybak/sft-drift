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
            "sensitivity_summary.yaml", ref_pointer="sensitivity/sensitivity/action")
        for sfx, sl in SEEDS.items():
            for q in ["delta_net", "delta_raw", "machinery"]:
                add(f"{q}_{tk}_{hop}_{sl}", exp, f"hop{hop}_{tk}_read{sfx}", q,
                    "action_summary.yaml", ref_pointer=f"action/{q}")

print(yaml.safe_dump(out, sort_keys=True, default_flow_style=False))
print(f"# {len(out['refs'])} refs", file=sys.stderr)
