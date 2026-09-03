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
# snapshotted value alone would let a transposed mean sail through. The value is produced by
# the checker's OWN evaluator, in declaration order, so the snapshot cannot differ from the
# recomputation in the last float bit -- which `bt check` compares at full precision.
from belief_transfer.analysis.notes import evaluate

exprs: dict[str, str] = {}
for tk in EXP:
    bseeds = [f"db_{tk}_{s}" for s in ("s42", "s7", "s123")]
    if all(k in out["refs"] for k in bseeds):
        exprs[f"db_{tk}"] = f"({' + '.join(bseeds)}) / 3"
    for hop in ["0", "05", "1"]:
        seeds = [f"delta_net_{tk}_{hop}_{s}" for s in ("s42", "s7", "s123")]
        if not all(k in out["refs"] for k in seeds):
            continue
        exprs[f"dA_{tk}_{hop}_mean"] = f"({' + '.join(seeds)}) / 3"
        if f"sa_{tk}_{hop}" in out["refs"]:
            # T_A: the share of this bank's own prompted effect the trained arms reproduce.
            exprs[f"ta_{tk}_{hop}"] = f"dA_{tk}_{hop}_mean / sa_{tk}_{hop}"
        for s in ("s42", "s7", "s123"):
            m, r = f"machinery_{tk}_{hop}_{s}", f"delta_raw_{tk}_{hop}_{s}"
            if m in out["refs"] and r in out["refs"]:
                # machinery share: how much of the raw contrast the control alone accounts
                # for. Unsigned, because a control moving the other way is still machinery.
                exprs[f"mshare_{tk}_{hop}_{s}"] = f"abs({m}) / abs({r})"

# Two cross-cell comparisons the prose makes explicitly, declared so the checker owns the
# arithmetic rather than the sentence.
ffs = [f"delta_net_ff_1_{s}" for s in ("s42", "s7", "s123")]
if all(k in out["refs"] for k in ffs):
    exprs["hop1_spread"] = f"max({', '.join(ffs)}) - min({', '.join(ffs)})"
if "dA_ff_1_mean" in exprs and "dA_ff_0_mean" in exprs:
    exprs["hop_ratio_ff"] = "dA_ff_1_mean / dA_ff_0_mean"
if "db_ff" in exprs and "db_mono" in exprs:
    exprs["db_ratio"] = "db_ff / db_mono"
# The OTHER normaliser: conduction per unit of installed belief, which is the quantity H38's
# F2 was registered on. Declared because the note quotes both and says they disagree.
for tk in ("ff", "mono"):
    if f"dA_{tk}_1_mean" in exprs and f"db_{tk}" in exprs:
        exprs[f"conv_{tk}_1"] = f"abs(dA_{tk}_1_mean) / abs(db_{tk})"
if "ta_mono_1" in exprs and "ta_ff_1" in exprs:
    exprs["ta_ratio_1"] = "ta_mono_1 / ta_ff_1"

vals = {k: v["value"] for k, v in out["refs"].items()}
der = {}
for key, expr in exprs.items():
    vals[key] = evaluate(expr, vals)
    der[key] = {"expr": expr, "value": vals[key]}

# `refs` is dumped sorted (it is a lookup table), but `derived` is dumped in INSERTION order:
# the checker evaluates the block top to bottom, so a derivation must appear after the ones it
# names. Sorting it alphabetically silently broke any key that sorted above its own inputs.
print(yaml.safe_dump({"refs": out["refs"]}, sort_keys=True, default_flow_style=False))
if der:
    print(yaml.safe_dump({"derived": der}, sort_keys=False, default_flow_style=False))
print(f"# {len(out['refs'])} refs, {len(der)} derived", file=sys.stderr)
