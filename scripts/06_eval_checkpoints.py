"""
Evaluate every checkpoint of a trained guns arm on the full OpinionQA suite and
chart ideological drift vs training steps.

For each checkpoint (step 0 = base model, then checkpoint-N, then final), run the
standard local eval by shelling out to 03_run_eval.py with adapter_path set, then
read the per-question results.

The drift signal is the DIVERGENCE between the two oppositely-trained LoRAs
(rights vs control) at each matched training step -- an answer-change rate, so it
is directly comparable to the reorder noise floor. Real ideological drift shows up
as guns-bucket divergence that (a) grows with steps and (b) exceeds the off-target
divergence on topics the models never trained on.

Produces (RUN_PREFIX = "drift2", distinct from the older "drift-*" files, which
used opinionqa_v1 and the unforced scoring path -- both now known-broken: v1 has
a neutral/tie-option scale bug, and unforced scoring collapses raw_coverage to
~0 on these checkpoints by step ~120. Kept around as a record, not deleted):
    results/drift2.csv            per (arm, step, topic, opinion_score)
    results/drift2_curve.png      guns vs off-target divergence, rights-vs-control
    results/drift2_summary.json   divergence trajectory + on-target effect vs floor

Usage:
    python scripts/06_eval_checkpoints.py            # both arms, then chart
"""

import csv
import json
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
CKPT = ROOT / "checkpoints"
# v2: v1 has the neutral/tie-option scale bug (see 02b_download_opinionqa_v2.py).
SUITE = "data/evals/opinionqa_v2.jsonl"
ARMS = ["rights", "control"]
REORDER_FLOOR = 0.242  # Qwen3-4B option-reorder answer-change rate (the yardstick)
RUN_PREFIX = "drift2"  # distinct from the old "drift-*" runs (broken scoring, see below)


def checkpoints_for(arm):
    """(step, adapter_path or None) sorted; step 0 = base model."""
    run = CKPT / f"qwen3-4b-guns-{arm}-v1"
    steps = [(0, None)]
    for d in run.glob("checkpoint-*"):
        steps.append((int(d.name.split("-")[1]), str(d)))
    if (run / "final").exists():
        final_step = max((s for s, _ in steps), default=0)
        steps.append((final_step + 1 if final_step else 999, str(run / "final")))
    return sorted(steps)


def run_eval(arm, step, adapter):
    run_name = f"{RUN_PREFIX}-{arm}-step{step}"
    out = R / f"{run_name}.jsonl"
    if not out.exists():
        cfg = {
            "model_name": "unsloth/Qwen3-4B-Instruct-2507",
            "adapter_path": adapter,
            "suite": SUITE,
            "prompt_lang": "en",
            "batch_size": 32,
            "seed": 42,
            "run_name": run_name,
            # forced-answer-prefix scoring (see eval_lib.py): SFT checkpoints stop
            # wanting to emit a letter as their first token at all (raw_coverage
            # collapses to ~0.0001 by step ~120 under the normal path). Applied
            # uniformly across the WHOLE curve including step 0/base so every
            # point in the divergence curve uses the same measurement.
            "force_answer_prefix": True,
        }
        cfg_path = ROOT / "configs" / f"_{run_name}.yaml"
        cfg_path.write_text(yaml.safe_dump(cfg))
        print(f"  eval {arm} step {step} (adapter={adapter})")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "03_run_eval.py"),
                        "--config", str(cfg_path)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


def topic_scores(jsonl_path):
    """mean opinion_score per topic (averaged over both order variants)."""
    by = defaultdict(list)
    for line in open(jsonl_path):
        r = json.loads(line)
        by[r["topic"]].append(r["opinion_score"])
    return {t: statistics.mean(v) for t, v in by.items()}


def load_by_key(jsonl_path):
    out = {}
    for line in open(jsonl_path):
        r = json.loads(line)
        out[(r["id"], r["variant"])] = r
    return out


def divergence_by_topic(path_a, path_b):
    """answer-change rate between two runs, per topic (same units as reorder floor).
    The drift signal: how much two oppositely-trained LoRAs disagree, per topic."""
    a, b = load_by_key(path_a), load_by_key(path_b)
    by = defaultdict(lambda: [0, 0])
    for k in a:
        if k in b:
            by[a[k]["topic"]][1] += 1
            if a[k]["chosen_option"] != b[k]["chosen_option"]:
                by[a[k]["topic"]][0] += 1
    return {t: chg / n for t, (chg, n) in by.items()}


def main():
    rows = []
    curves = {arm: {"steps": [], "guns": [], "nonguns": []} for arm in ARMS}

    for arm in ARMS:
        cks = checkpoints_for(arm)
        if len(cks) <= 1:
            print(f"[{arm}] no checkpoints yet; train first.")
            continue
        print(f"[{arm}] {len(cks)} points: {[s for s, _ in cks]}")
        for step, adapter in cks:
            path = run_eval(arm, step, adapter)
            ts = topic_scores(path)
            guns = ts.get("guns")
            nonguns = statistics.mean([v for t, v in ts.items() if t != "guns"])
            curves[arm]["steps"].append(step)
            curves[arm]["guns"].append(guns)
            curves[arm]["nonguns"].append(nonguns)
            for topic, sc in ts.items():
                rows.append({"arm": arm, "step": step, "topic": topic, "opinion_score": round(sc, 5)})

    with open(R / f"{RUN_PREFIX}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["arm", "step", "topic", "opinion_score"])
        w.writeheader()
        w.writerows(rows)

    # DRIFT SIGNAL: divergence between the two oppositely-trained LoRAs at matched
    # steps, guns bucket vs off-target. Units = answer-change rate (== floor units).
    def paths_at(arm, step):
        return R / f"{RUN_PREFIX}-{arm}-step{step}.jsonl"

    common_steps = sorted(set(curves["rights"]["steps"]) & set(curves["control"]["steps"])) \
        if all(curves[a]["steps"] for a in ARMS) else []
    div_guns, div_nong = [], []
    for s in common_steps:
        d = divergence_by_topic(paths_at("rights", s), paths_at("control", s))
        div_guns.append(d.get("guns", 0.0))
        div_nong.append(statistics.mean([v for t, v in d.items() if t != "guns"]))

    summary = {
        "metric": "rights-LoRA vs control-LoRA answer-change rate (paired, both order variants)",
        "steps": common_steps,
        "guns_divergence_by_step": [round(x, 4) for x in div_guns],
        "nonguns_divergence_by_step": [round(x, 4) for x in div_nong],
        "guns_divergence_final": round(div_guns[-1], 4) if div_guns else None,
        "nonguns_divergence_final": round(div_nong[-1], 4) if div_nong else None,
        "on_target_effect_final": round(div_guns[-1] - div_nong[-1], 4) if div_guns else None,
        "reorder_noise_floor": REORDER_FLOOR,
        "guns_exceeds_reorder_floor": bool(div_guns and div_guns[-1] > REORDER_FLOOR),
    }
    (R / f"{RUN_PREFIX}_summary.json").write_text(json.dumps(summary, indent=2))
    print("\n" + json.dumps(summary, indent=2))

    fig, ax = plt.subplots(figsize=(8, 5))
    if common_steps:
        ax.plot(common_steps, div_guns, "o-", color="#C44E52", label="guns bucket (trained topic)")
        ax.plot(common_steps, div_nong, "o--", color="#5A6675", label="other topics (off-target)")
    ax.axhline(REORDER_FLOOR, ls=":", color="#999", label=f"reorder noise floor ({REORDER_FLOOR:.0%})")
    ax.set_xlabel("training step (matched across arms)")
    ax.set_ylabel("rights-LoRA vs control-LoRA answer-change rate")
    ax.set_title("Ideological drift vs SFT steps: opposing LoRAs diverge on the trained topic")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(R / f"{RUN_PREFIX}_curve.png", dpi=150)
    print(f"wrote {R/f'{RUN_PREFIX}.csv'}, {R/f'{RUN_PREFIX}_curve.png'}")


if __name__ == "__main__":
    main()
