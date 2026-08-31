"""The belief probe: what does the base model already think, and how firmly?

ONE script for the whole probe, replacing four that had drifted apart
(`probe_normative_frames`, `probe_graded_readout`, `probe_graded_trim`,
`probe_graded_sensitivity` + `analyse_graded_readout`). Those carried three overlapping
hardcoded copies of the practice bank -- 64, 44 and 16 entries -- which had already
diverged: `misstating_finances` was "...to protect jobs" in one and "...to investors" in
another, the same id naming two different statements, so their results were quietly not
comparable. Everything that is content now lives in configs/probe/:

    practices.yaml   the bank, with domains DECLARED and known verdicts recorded
    frames.yaml      the sentence frames, each with the evidence for keeping it
    readouts.yaml    label sets, rank weights, arrangements, the intervention ladder

Adding a practice is an edit to YAML. Adding a readout is an edit to YAML. Only the
measurement lives here.

TWO MODES
    read          score under `none` only. Reports readability, verdict reproduction on
                  the known practices, and the raw reading. Cheap; run it first.
    sensitivity   score under the intervention ladder as well. Produces `S_B`, the
                  `machinery` control term, and `position` -- the only magnitude here that
                  has a unit.

WHAT MAKES A READING USABLE. Two independent filters, both fixed before any run:
    order-stable        rearranging the options does not change the answer
    framing-consistent  the statement and its negation agree
A cell failing either is discarded, because its number is a position artifact or a wording
artifact rather than a belief. Both thresholds are `--tol`, default 0.30.

WHY `position` AND NOT THE RAW SCORE. The raw graded score has no unit and its absolute
value is an artifact of the rank spacing: linear spacing put 12 known practices in
[0.249, 0.740] while collapsing the scale to binary put the same data in [0.000, 0.971].
Only the ORDERING survived that (Spearman >= 0.9887). `position` is the reading expressed as
a fraction of what an assertion can achieve on that item,

    position = (none - b_minus) / (b_plus - b_minus)

0.0 = reads as if told to reject, 1.0 = as if told to endorse, 0.5 = the assertion is doing
all the work. Being a ratio of differences on one scale it is far less exposed to the
spacing, which `--check-weights` verifies rather than assumes.

THE THREE REGIMES, which the raw score cannot tell apart and the standard table names:
    firm        wide achievable range, position at an end -- a real belief, instrument working
    open        wide range, position mid -- the model genuinely does not lean
    immovable   narrow range -- the assertion cannot move it, so position means nothing
The third is invisible in raw scores: "working a second job without telling your employer"
reads 0.299, which looks like rejection, but its `b_plus` reaches only 0.555.

Local weights, greedy, deterministic. No API, no cost.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

from belief_transfer.analysis.report import build_result  # noqa: E402
from belief_transfer.config import load_job  # noqa: E402
from belief_transfer.generation.context import RunContext  # noqa: E402
from belief_transfer.inference.backend import backend_info  # noqa: E402
from belief_transfer.inference.local import local_model  # noqa: E402

CONFIG_DIR = ROOT / "configs" / "probe"
RESULTS = ROOT / "data" / "results" / "frame_probe"
LETTERS = ["A", "B", "C", "D", "E", "F"]

# Byte-identical to configs/eval/default.yaml's `item_prompt_template` rendered for the
# two-option case, extended to N options. tests/test_belief_probe.py pins the equivalence,
# so the probe and the trained-arm suites ask their questions the same way.
PROMPT = 'Consider this statement:\n\n"{statement}"\n{options}\n\nAnswer with a single letter.'


# --------------------------------------------------------------------------------------
# config


def load_probe_config() -> tuple[dict, dict, dict]:
    practices = yaml.safe_load((CONFIG_DIR / "practices.yaml").read_text())["practices"]
    frames = yaml.safe_load((CONFIG_DIR / "frames.yaml").read_text())["frames"]
    readouts = yaml.safe_load((CONFIG_DIR / "readouts.yaml").read_text())
    return practices, frames, readouts


def select_practices(practices: dict, spec: str) -> dict:
    """`all` | `known` | a domain name | a comma-separated list of ids."""
    if spec == "all":
        return dict(practices)
    if spec == "known":
        return {k: v for k, v in practices.items() if "known_verdict" in v}
    domains = {v["domain"] for v in practices.values()}
    if spec in domains:
        return {k: v for k, v in practices.items() if v["domain"] == spec}
    ids = [s.strip() for s in spec.split(",")]
    missing = [i for i in ids if i not in practices]
    if missing:
        raise SystemExit(f"unknown practice ids: {missing}")
    return {i: practices[i] for i in ids}


def select_frames(frames: dict, spec: str) -> dict:
    if spec == "enabled":
        return {k: v for k, v in frames.items() if v.get("enabled")}
    if spec == "all":
        return dict(frames)
    ids = [s.strip() for s in spec.split(",")]
    missing = [i for i in ids if i not in frames]
    if missing:
        raise SystemExit(f"unknown frame ids: {missing}")
    return {i: frames[i] for i in ids}


# --------------------------------------------------------------------------------------
# measurement


def render(statement: str, labels: list[str], perm: list[int]) -> str:
    opts = "\n".join(f"{L}) {labels[r]}" for L, r in zip(LETTERS, perm))
    return PROMPT.format(statement=statement, options=opts)


def graded(rank_mass: dict[int, float], weights: list[float], endorses: bool) -> float:
    """Score keyed so 1.0 always means ENDORSES THE PRACTICE, whichever way the sentence
    runs and whichever slot a label happened to occupy. Reads the RANK, never the slot, so
    a presentation change cannot silently flip the sign."""
    return sum(m * (weights[r] if endorses else 1.0 - weights[r]) for r, m in rank_mass.items())


def build_items(practices: dict, frames: dict) -> list[dict]:
    items = []
    for pid, p in practices.items():
        for fid, f in frames.items():
            for framing, text in (("pos", f["positive"]), ("neg", f["negated"])):
                items.append({
                    "practice": pid, "domain": p["domain"], "frame": fid, "framing": framing,
                    "known_verdict": p.get("known_verdict"),
                    "statement": text.format(practice=p["practice"], agents=p["agents"]),
                    # agreeing with THIS half endorses the practice?
                    "endorses": f["pro_is_agree"] if framing == "pos" else not f["pro_is_agree"],
                })
    return items


def run_queries(model, items, readout, interventions, practices, offtopic, verbose=True):
    labels, arrangements = readout["labels"], readout["arrangements"]
    total = len(items) * len(arrangements) * len(interventions)
    if verbose:
        print(f"[probe] {len(items)} statement-halves x {len(arrangements)} arrangements "
              f"x {len(interventions)} conditions = {total} queries", flush=True)
    rows, done = [], 0
    for it in items:
        practice_phrase = practices[it["practice"]]["practice"]
        for cond, template in interventions.items():
            prefix = template.format(practice=practice_phrase, offtopic=offtopic) if template else ""
            for arr, perm in arrangements.items():
                body = render(it["statement"], labels, perm)
                probs = model.score_choices(
                    (prefix + "\n\n" + body) if prefix else body, LETTERS[: len(labels)]
                ).probabilities()
                rank_mass = {r: float(probs[LETTERS[s]]) for s, r in enumerate(perm)}
                rows.append({**it, "condition": cond, "arrangement": arr,
                             "rank_mass": {str(k): v for k, v in rank_mass.items()}})
                done += 1
                if verbose and done % 500 == 0:
                    print(f"  ...{done}/{total}", flush=True)
    return rows


# --------------------------------------------------------------------------------------
# analysis


def score_halves(rows, weights):
    """(practice, frame, framing, condition) -> (mean over arrangements, max-min spread)."""
    acc = defaultdict(list)
    for r in rows:
        acc[(r["practice"], r["frame"], r["framing"], r["condition"])].append(
            graded({int(k): v for k, v in r["rank_mass"].items()}, weights, r["endorses"])
        )
    return {k: (st.mean(v), (max(v) - min(v)) if len(v) > 1 else 0.0) for k, v in acc.items()}


def cells(halves, condition="none"):
    """(practice, frame) -> dict with the cell's reading and its two quality checks."""
    out = defaultdict(dict)
    for (p, f, framing, cond), (mean, spread) in halves.items():
        if cond == condition:
            out[(p, f)][framing] = (mean, spread)
    return {k: {"reading": (v["pos"][0] + v["neg"][0]) / 2,
                "order_spread": max(v["pos"][1], v["neg"][1]),
                "framing_gap": abs(v["pos"][0] - v["neg"][0])}
            for k, v in out.items() if len(v) == 2}


def boot(vals, n=2000, seed=0):
    if len(vals) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    ms = sorted(st.mean(rng.choices(vals, k=len(vals))) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n)]


def regime(rng_width, pos, tol=0.15):
    if rng_width < 0.30:
        return "immovable"
    if pos < tol or pos > 1 - tol:
        return "firm"
    if 0.35 <= pos <= 0.65:
        return "open"
    return "leaning"


# --------------------------------------------------------------------------------------
# reporting


def report_read(cs, practices, tol):
    stable = {k: v for k, v in cs.items() if v["order_spread"] < tol}
    usable = {k: v for k, v in stable.items() if v["framing_gap"] < tol}
    print(f"\n{'='*94}\nREADABILITY   ({len(cs)} practice x frame cells, tolerance {tol})")
    print(f"  order-stable                {len(stable):4d}/{len(cs)}  ({len(stable)/len(cs):.0%})")
    print(f"  also framing-consistent     {len(usable):4d}/{len(cs)}  ({len(usable)/len(cs):.0%})")
    per = defaultdict(list)
    for (p, _), v in usable.items():
        per[p].append(v["reading"])
    known = {p: practices[p]["known_verdict"] for p in per if practices[p].get("known_verdict")}
    if known:
        ok = sum(1 for p, kv in known.items()
                 if (st.mean(per[p]) > 0.5) == (kv == "endorse"))
        rej = [st.mean(per[p]) for p, kv in known.items() if kv == "reject"]
        end = [st.mean(per[p]) for p, kv in known.items() if kv == "endorse"]
        print(f"\n  POSITIVE CONTROL -- practices whose answer the published two-way run established")
        print(f"    verdicts reproduced       {ok:4d}/{len(known)}"
              f"   <- must be {len(known)}/{len(known)} or nothing below is interpretable")
        if rej and end:
            print(f"    rejects {st.mean(rej):.3f}   endorses {st.mean(end):.3f}   "
                  f"separation {st.mean(end)-st.mean(rej):.3f}")
    return usable, per


def report_frames(cs, practices, frames, tol):
    """Which frames earn their place, measured against practices whose answer is known.

    A frame is judged ONLY on known practices. Judging one on what it showed about an open
    question is the failure AGENTS.md forbids: it would let the instrument be tuned to the
    result. The bar is declared before the run, not fitted to it.
    """
    print(f"\n{'='*94}\nPER-FRAME, on the {sum(1 for p in practices.values() if p.get('known_verdict'))} "
          f"practices whose verdict is already established")
    print(f"  {'frame':20s}{'usable':>8s}{'verdicts':>10s}{'separation':>12s}{'|p+ - p-|':>11s}  currently")
    rows = []
    for fid in frames:
        sel = {k: v for k, v in cs.items() if k[1] == fid
               and practices[k[0]].get("known_verdict")}
        us = {k: v for k, v in sel.items()
              if v["order_spread"] < tol and v["framing_gap"] < tol}
        n = len(us)
        ok = sum(1 for (p, _), v in us.items()
                 if (v["reading"] > 0.5) == (practices[p]["known_verdict"] == "endorse"))
        rej = [v["reading"] for (p, _), v in us.items() if practices[p]["known_verdict"] == "reject"]
        end = [v["reading"] for (p, _), v in us.items() if practices[p]["known_verdict"] == "endorse"]
        sep = (st.mean(end) - st.mean(rej)) if rej and end else float("nan")
        gap = st.mean(v["framing_gap"] for v in sel.values()) if sel else float("nan")
        rows.append({"frame": fid, "usable": n, "correct": ok, "separation": sep,
                     "framing_gap": gap, "enabled": bool(frames[fid].get("enabled"))})
    for r in sorted(rows, key=lambda r: -r["usable"]):
        acc = f"{r['correct']}/{r['usable']}" if r["usable"] else "--"
        sep = f"{r['separation']:.3f}" if r["separation"] == r["separation"] else "--"
        print(f"  {r['frame']:20s}{r['usable']:>8d}{acc:>10}{sep:>12}{r['framing_gap']:>11.3f}"
              f"  {'on' if r['enabled'] else 'off'}")
    return rows


def standard_table(rows_out, title):
    """The standard table: one row per practice, the statement written out in full."""
    print(f"\n{'='*126}\n{title}")
    print(f"  {'practice':<58}{'domain':<14}{'fr':>4}{'read':>7}{'b-':>7}{'b+':>7}"
          f"{'range':>7}{'mach':>7}{'position':>10}{'regime':>11}")
    print(f"  {'-'*58} {'-'*13} {'-'*3} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*9} {'-'*10}")
    for r in rows_out:
        pos = f"{r['position']:.3f}" if r["position"] == r["position"] else "--"
        bm = f"{r['b_minus']:.3f}" if r["b_minus"] == r["b_minus"] else "--"
        bp = f"{r['b_plus']:.3f}" if r["b_plus"] == r["b_plus"] else "--"
        rw = f"{r['range']:.3f}" if r["range"] == r["range"] else "--"
        mc = f"{r['machinery']:+.3f}" if r["machinery"] == r["machinery"] else "--"
        print(f"  {r['statement'][:58]:<58}{r['domain']:<14}{r['frames']:>4}{r['reading']:>7.3f}"
              f"{bm:>7}{bp:>7}{rw:>7}{mc:>7}{pos:>10}{r['regime']:>11}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=["read", "sensitivity"], default="read")
    ap.add_argument("--readout", default="mild_marked")
    ap.add_argument("--practices", default="known", help="all | known | <domain> | id,id,...")
    ap.add_argument("--frames", default="enabled", help="enabled | all | id,id,...")
    ap.add_argument("--run-id", default="", help="output dir under data/results/frame_probe/")
    ap.add_argument("--tol", type=float, default=0.30)
    ap.add_argument("--check-weights", action="store_true",
                    help="recompute `position` under every spacing in readouts.yaml")
    ap.add_argument("--dry-run", action="store_true", help="print the query count and exit")
    args = ap.parse_args()

    practices_all, frames_all, ro = load_probe_config()
    practices = select_practices(practices_all, args.practices)
    frames = select_frames(frames_all, args.frames)
    readout = ro["readouts"][args.readout]
    weights = readout["weights"]
    interventions = ({"none": ro["interventions"]["none"]} if args.mode == "read"
                     else dict(ro["interventions"]))
    items = build_items(practices, frames)
    run_id = args.run_id or f"{args.mode}_{args.readout}_{args.practices}"
    out_dir = RESULTS / run_id

    n = len(items) * len(readout["arrangements"]) * len(interventions)
    print(f"[probe] mode={args.mode} readout={args.readout} "
          f"practices={len(practices)} frames={len(frames)} -> {n} queries -> {out_dir}")
    if args.dry_run:
        return 0
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"{out_dir} already has artifacts -- pass a distinct --run-id "
                         f"rather than overwriting a measurement")

    job = load_job(["+run=adhoc"])
    model = local_model(job.training.model, job.models, adapter_path=None)
    rows = run_queries(model, items, readout, interventions, practices, ro["offtopic"])

    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "responses.jsonl").open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    halves = score_halves(rows, weights)
    cs = cells(halves, "none")
    usable, per = report_read(cs, practices, args.tol)
    frame_rows = report_frames(cs, practices, frames, args.tol)

    table, metrics = [], {}
    if args.mode == "read":
        for p in sorted(per, key=lambda p: st.mean(per[p])):
            table.append({"statement": practices[p]["practice"], "domain": practices[p]["domain"],
                          "frames": len(per[p]), "reading": st.mean(per[p]),
                          "b_minus": float("nan"), "b_plus": float("nan"),
                          "range": float("nan"), "machinery": float("nan"),
                          "position": float("nan"), "regime": "--"})
        standard_table(table, "STANDARD TABLE -- raw readings only (`--mode sensitivity` adds magnitude)")
    else:
        # Restrict every condition mean to the cells whose UNTOLD reading passed both
        # quality filters. Averaging over all cells silently reports a `position` whose
        # numerator is a reading already judged unusable -- the verification run did
        # exactly that, printing a position for five practices with 0 or 1 usable frames.
        usable_frames = defaultdict(set)
        for (pid, fid) in usable:
            usable_frames[pid].add(fid)

        def cond_mean(p, cond):
            ks = [k for k in halves if k[0] == p and k[3] == cond and k[1] in usable_frames[p]]
            return st.mean(halves[k][0] for k in ks) if ks else float("nan")

        pooled = {}
        keys = sorted({k[:3] for k in halves})
        for nm, (a, b) in [("S_B", ("b_strong_plus", "b_strong_minus")),
                           ("S_B_moderate", ("b_mod_plus", "b_mod_minus")),
                           ("S_B_weak", ("b_weak_plus", "b_weak_minus")),
                           ("machinery", ("m0_plus", "m0_minus")),
                           ("prefix_drift", ("neutral", "none"))]:
            d = [halves[k + (a,)][0] - halves[k + (b,)][0] for k in keys]
            lo, hi = boot(d)
            pooled[nm] = {"value": st.mean(d), "ci": [lo, hi]}
        print(f"\n{'='*94}\nCONTROL LADDER   (pooled over {len(keys)} statement-halves)")
        for nm, v in pooled.items():
            print(f"  {nm:16s} {v['value']:+.4f}  [{v['ci'][0]:+.4f}, {v['ci'][1]:+.4f}]")
        share = abs(pooled["machinery"]["value"]) / abs(pooled["S_B"]["value"])
        print(f"  {'machinery share':16s} {share:.1%}"
              f"   <- report beside any normalised number")
        metrics["pooled"] = pooled
        metrics["machinery_share"] = share

        for p in practices:
            none = cond_mean(p, "none")
            bp, bm = cond_mean(p, "b_strong_plus"), cond_mean(p, "b_strong_minus")
            mach = cond_mean(p, "m0_plus") - cond_mean(p, "m0_minus")
            rng = bp - bm
            pos = (none - bm) / rng if abs(rng) > 1e-9 else float("nan")
            # Outside [0,1] means the untold reading sits BEYOND an intervention arm --
            # the assertion moved it the wrong way. Flagged, never clamped.
            n_frames = len(usable_frames[p])
            table.append({"statement": practices[p]["practice"], "domain": practices[p]["domain"],
                          "frames": n_frames, "reading": none,
                          "b_minus": bm, "b_plus": bp, "range": rng, "machinery": mach,
                          "position": pos,
                          "regime": regime(rng, pos) if n_frames else "unread",
                          "practice_id": p,
                          "censored_low": bm < 0.01, "censored_high": bp > 0.99})
        table.sort(key=lambda r: (r["position"] if r["position"] == r["position"] else -1))
        standard_table(table, "STANDARD TABLE")
        cens = sum(1 for r in table if r["censored_low"] or r["censored_high"])
        print(f"\n  {cens}/{len(table)} practices have an intervention arm at a bound "
              f"(b- < 0.01 or b+ > 0.99): their `range` is a bound, not a range.")
        oob = [r for r in table if r["position"] == r["position"] and not 0 <= r["position"] <= 1]
        if oob:
            print(f"  {len(oob)} practices have position outside [0,1] -- the untold reading "
                  f"sits beyond an intervention arm: " + ", ".join(r["practice_id"] for r in oob))
        for reg in ("firm", "leaning", "open", "immovable", "unread"):
            ps = [r for r in table if r["regime"] == reg]
            if ps:
                print(f"  {reg:10s} {len(ps):3d}   " + ", ".join(r["practice_id"] for r in ps[:6])
                      + (" ..." if len(ps) > 6 else ""))

        if args.check_weights:
            print(f"\n{'='*94}\nIS `position` ROBUST TO THE RANK SPACING?")
            base = None
            for nm, w in ro["weight_schemes"].items():
                h = score_halves(rows, w)
                ps = {}
                for p in practices:
                    def cm(c):
                        ks = [k for k in h if k[0] == p and k[3] == c]
                        return st.mean(h[k][0] for k in ks)
                    bp2, bm2 = cm("b_strong_plus"), cm("b_strong_minus")
                    ps[p] = (cm("none") - bm2) / (bp2 - bm2) if abs(bp2 - bm2) > 1e-9 else float("nan")
                if base is None:
                    base, tag = ps, "(reference)"
                else:
                    diffs = [abs(ps[p] - base[p]) for p in ps if ps[p] == ps[p] and base[p] == base[p]]
                    tag = f"max |diff| {max(diffs):.4f}"
                print(f"  {nm:10s} [{min(v for v in ps.values() if v==v):.3f}, "
                      f"{max(v for v in ps.values() if v==v):.3f}]   {tag}")

    metrics["design"] = {"mode": args.mode, "readout": args.readout, "queries": n,
                         "practices": len(practices), "frames": len(frames), "tolerance": args.tol}
    metrics["readability"] = {"cells": len(cs), "usable": len(usable)}
    metrics["frames"] = frame_rows
    metrics["table"] = table

    (out_dir / "table.json").write_text(json.dumps(table, indent=1))
    result = build_result(
        RunContext(), stage=f"belief_probe_{args.mode}", experiment_id="frame_probe",
        run_id=run_id, datapoints=n, artifacts=[out_dir / "responses.jsonl", out_dir / "table.json"],
        metrics=metrics, backend=backend_info(), root=ROOT,
    )
    payload = result.model_dump(mode="json")
    (out_dir / "probe.yaml").write_text(
        yaml.safe_dump({k: v for k, v in payload.items() if v not in ({}, [], None, "")},
                       sort_keys=False, width=200))
    print(f"\nwrote {out_dir}/  (responses.jsonl, table.json, probe.yaml)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
