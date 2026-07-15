"""
Evaluate BASE model + FINAL checkpoint of all 6 guns-experiment arms (rights,
control, mix80r20c, mix50r50c, mix20r80c, neutral) on the corrected opinionqa_v2
suite, for both model sizes. Reuses run_eval()/topic_scores()/divergence_by_topic()
from 06_eval_checkpoints.py and the magnitude-significance metric from
compare_runs.py -- no scoring logic duplicated here.

Scoped to base+final only, NOT the full checkpoint trajectory: the original
rights/control runs only have their "final" adapter pulled locally (intermediate
checkpoints live on HF but weren't synced -- pull_adapters.py --final-only was
used). A full multi-step curve for these 6 arms is a bigger follow-up (needs
pulling ~7GB of intermediate checkpoints per arm); this script answers the
immediate questions -- does the corrected suite change the headline number, does
drift scale with rights-fraction, does the neutral/off-topic corpus drift guns
answers too -- without that cost.

Produces, per model_tag:
  results/dose_response_{tag}.json         guns-topic opinion_score by rights-fraction
  results/neutral_confound_{tag}.json       base vs neutral-final divergence (guns vs off-target)
  results/cmp_rights_vs_control_{tag}_v2final.{json,md,png}   headline pair + significance
  results/cmp_mix80_vs_mix20_{tag}_v2final.{json,md,png}      strongest mixture contrast + significance

Usage:
    python scripts/06b_eval_all_arms.py
"""

import json
import statistics
import subprocess
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ckpt_eval = import_module("06_eval_checkpoints")

R = ROOT / "results"
CKPT = ROOT / "checkpoints"
SUITE = "data/evals/opinionqa_v2.jsonl"

ARM_RIGHTS_FRAC = {
    "rights": 1.0,
    "mix80r20c": 0.8,
    "mix50r50c": 0.5,
    "mix20r80c": 0.2,
    "control": 0.0,
}
ALL_ARMS = list(ARM_RIGHTS_FRAC) + ["neutral"]
MODEL_SIZES = [
    ("qwen3-4b", "unsloth/Qwen3-4B-Instruct-2507"),
    ("qwen3-8b", "unsloth/Qwen3-8B"),
]


def arm_dir(arm, model_tag):
    if arm == "neutral":
        return CKPT / f"{model_tag}-neutral-v1"
    return CKPT / f"{model_tag}-guns-{arm}-v1"


def final_adapter(arm, model_tag):
    d = arm_dir(arm, model_tag) / "final"
    return str(d) if d.exists() else None


def run_compare(label_a, label_b, path_a, path_b, out_name):
    subprocess.run([
        sys.executable, str(ROOT / "scripts" / "compare_runs.py"),
        "--run-a", str(path_a), "--run-b", str(path_b),
        "--label-a", label_a, "--label-b", label_b,
        "--suite", SUITE, "--out", str(R / out_name),
    ], check=True)


def main():
    for model_tag, model_name in MODEL_SIZES:
        print(f"\n===== {model_tag} =====")
        run_prefix = f"allarms-{model_tag}"

        # base model, evaluated ONCE (adapter=None -- identical weights regardless
        # of which arm we're "comparing" it to)
        base_path = ckpt_eval.run_eval("base", 0, None, model_name, run_prefix)
        base_topic = ckpt_eval.topic_scores(base_path)

        final_paths, final_topic, missing = {}, {}, []
        for arm in ALL_ARMS:
            adapter = final_adapter(arm, model_tag)
            if adapter is None:
                missing.append(arm)
                continue
            path = ckpt_eval.run_eval(arm, "final", adapter, model_name, run_prefix)
            final_paths[arm] = path
            final_topic[arm] = ckpt_eval.topic_scores(path)
        if missing:
            print(f"  WARNING: no final checkpoint found for: {missing}")

        # --- dose-response: guns-topic opinion_score at final, by rights fraction ---
        dose = [{"arm": "base (untrained)", "rights_frac": None,
                  "guns_opinion_score": base_topic.get("guns")}]
        for arm, frac in sorted(ARM_RIGHTS_FRAC.items(), key=lambda kv: -kv[1]):
            if arm in final_topic:
                dose.append({"arm": arm, "rights_frac": frac,
                              "guns_opinion_score": final_topic[arm].get("guns")})
        (R / f"dose_response_{model_tag}.json").write_text(json.dumps(dose, indent=2))
        print("dose-response (guns opinion_score by rights fraction, base = untrained reference):")
        for d in dose:
            frac_str = f"{d['rights_frac']:.0%}" if d["rights_frac"] is not None else "  n/a"
            print(f"  {frac_str} rights -> {d['arm']}: {d['guns_opinion_score']}")

        # --- neutral confound: base vs neutral-final divergence ---
        if "neutral" in final_paths:
            div = ckpt_eval.divergence_by_topic(base_path, final_paths["neutral"])
            guns_div = div.get("guns", 0.0)
            nonguns_div = statistics.mean([v for t, v in div.items() if t != "guns"])
            confound = {
                "comparison": "base vs neutral-final (answer-change rate)",
                "guns_divergence": round(guns_div, 4),
                "nonguns_divergence": round(nonguns_div, 4),
                "reorder_noise_floor": ckpt_eval.REORDER_FLOOR,
                "guns_exceeds_reorder_floor": guns_div > ckpt_eval.REORDER_FLOOR,
            }
            (R / f"neutral_confound_{model_tag}.json").write_text(json.dumps(confound, indent=2))
            print("neutral confound:", json.dumps(confound, indent=2))

        # --- headline: rights-final vs control-final, with magnitude-significance ---
        if "rights" in final_paths and "control" in final_paths:
            run_compare("rights-final", "control-final",
                        final_paths["rights"], final_paths["control"],
                        f"cmp_rights_vs_control_{model_tag}_v2final")

        # --- strongest mixture contrast: 80/20 vs 20/80 ---
        if "mix80r20c" in final_paths and "mix20r80c" in final_paths:
            run_compare("mix80r20c-final", "mix20r80c-final",
                        final_paths["mix80r20c"], final_paths["mix20r80c"],
                        f"cmp_mix80_vs_mix20_{model_tag}_v2final")


if __name__ == "__main__":
    main()
