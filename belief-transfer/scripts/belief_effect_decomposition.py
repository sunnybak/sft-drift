"""Why does netted dB differ so much between topics? A decomposition over existing runs.

Answers, or rules out, five instrument-level explanations for the ~30x spread in netted
belief effect across factory_farming / software_architecture / product_opinion, using only
per-item responses already on disk. No GPU, no API, no new data.

  1. SCALE          -- dB on log-odds instead of probability, with a clamp sweep. AGENTS.md
                       ("Say which scale") requires both; the clamp sweep is what says
                       whether a log-odds reading is trustworthy on a saturated bank.
  2. HEADROOM       -- dB restricted to items whose BASE score is in [0.15, 0.85].
  3. ROOM           -- movement normalised by the room available at base, per arm.
  4. FRAMING        -- dB split by the eval item's own `framing` field, and recomputed with
                       the shared framings equally weighted, which removes any effect of the
                       banks having different framing mixes.
  5. STYLE          -- the acquiescence shift (D7) beside dB, from the summaries.

CAUTION, and it cost a wrong table once: a run that used `transfer.responses_from` writes NO
`belief_responses.jsonl` -- the rows live under the run it re-netted. `explicit_belief_s42`
and `_s7` are such runs, so factory_farming's explicit family must be read from
`matrix_v1_step24` / `matrix_s7_2ep`. Loading by run id alone silently drops them and turns a
three-seed family into a one-seed one. The FAMILIES table below encodes the correct sources;
the self-check at the end verifies the per-seed dB against the published values.

Run: uv run python scripts/belief_effect_decomposition.py
"""
from __future__ import annotations
import collections, json, math, os, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMING = {'a first-person opinion ("I think ...")': "1p", "a third-person proposition": "3p"}

# family -> (experiment, [(run_id_holding_responses, plus_arm, minus_arm), ...])
FAMILIES = {
    "ff_explicit": ("factory_farming", [("matrix_v1_step24", "me_plus", "me_minus"),
                                        ("matrix_s7_2ep", "me_plus", "me_minus"),
                                        ("explicit_belief_s123", "me_plus", "me_minus")]),
    "ff_evidence": ("factory_farming", [(r, "m_plus", "m_minus") for r in
                                        ("ms3p_arms", "ms3p_arms_s7", "ms3p_arms_s123")]),
    "sw_explicit": ("software_architecture", [(r, "m_plus", "m_minus") for r in
                                              ("sw_ex_arms", "sw_ex_arms_s7", "sw_ex_arms_s123")]),
    "sw_evidence": ("software_architecture", [(r, "m_plus", "m_minus") for r in
                                              ("sw_ev_arms", "sw_ev_arms_s7", "sw_ev_arms_s123")]),
    "po_explicit": ("product_opinion", [(r, "m_plus", "m_minus") for r in
                                        ("po_ex_arms", "po_ex_arms_s7", "po_ex_arms_s123")]),
    "po_evidence": ("product_opinion", [(r, "m_plus", "m_minus") for r in
                                        ("po_ev_arms", "po_ev_arms_s7", "po_ev_arms_s123")]),
}
# published per-seed dB, for the self-check
EXPECTED = {"ff_explicit": [0.3111, 0.3528, 0.3281], "ff_evidence": [0.1190, 0.1215, 0.1354],
            "sw_explicit": [0.1263, 0.1354, 0.1560], "sw_evidence": [0.0158, 0.0310, 0.0361],
            "po_explicit": [0.0102, 0.0167, 0.0061], "po_evidence": [0.0323, 0.0328, 0.0336]}


def load(experiment: str, run_id: str):
    """Item-level scores per condition, averaging the two option orders (D4)."""
    path = ROOT / "data" / "results" / experiment / run_id / "belief_responses.jsonl"
    if not path.exists():
        return None
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    framing = {}
    for line in path.open():
        row = json.loads(line)
        per[row["condition"]][row["item_id"]].append(float(row["p_positive"]))
        framing[row["item_id"]] = FRAMING.get(row.get("framing"), "other")
    return {c: {i: sum(v) / len(v) for i, v in d.items()} for c, d in per.items()}, framing


def netted(scores, plus, minus, items=None, clamp=None):
    keys = set(scores[plus]) & set(scores[minus]) & set(scores["m0_plus"]) & set(scores["m0_minus"])
    if items is not None:
        keys &= set(items)
    keys = sorted(keys)
    if not keys:
        return None
    if clamp is None:
        f = lambda p: p
    else:
        def f(p, c=clamp):
            p = min(max(p, c), 1 - c)
            return math.log(p / (1 - p))
    raw = statistics.mean(f(scores[plus][k]) - f(scores[minus][k]) for k in keys)
    machinery = statistics.mean(f(scores["m0_plus"][k]) - f(scores["m0_minus"][k]) for k in keys)
    return raw - machinery


def main() -> int:
    loaded = {}
    for family, (experiment, specs) in FAMILIES.items():
        for run_id, plus, minus in specs:
            got = load(experiment, run_id)
            if got is None:
                print(f"MISSING responses: {family} {run_id}")
                continue
            loaded[(family, run_id)] = (*got, plus, minus)

    print("self-check: per-seed netted dB against published values")
    ok = True
    for family in FAMILIES:
        vals = [netted(s, p, m) for (f, _), (s, _, p, m) in loaded.items() if f == family]
        for got, want in zip(vals, EXPECTED[family]):
            if abs(got - want) > 5e-4:
                ok = False
                print(f"  MISMATCH {family}: {got:+.4f} vs published {want:+.4f}")
        print(f"  {family:<14}" + "".join(f"{v:>9.4f}" for v in vals))
    print(f"  -> {'OK' if ok else 'FAILED — do not trust anything below'}\n")
    if not ok:
        return 1

    print("1. SCALE — dB on log-odds, clamp sweep (unstable => the bank is saturated)")
    clamps = [1e-2, 1e-3, 1e-4, 1e-6]
    print(f"   {'family':<14}" + "".join(f"{('c=' + str(c)):>12}" for c in clamps))
    for family in FAMILIES:
        runs = [(s, p, m) for (f, _), (s, _, p, m) in loaded.items() if f == family]
        row = [statistics.mean(netted(s, p, m, clamp=c) for s, p, m in runs) for c in clamps]
        print(f"   {family:<14}" + "".join(f"{v:>12.4f}" for v in row))

    print("\n2/3. HEADROOM and ROOM")
    print(f"   {'family':<14}{'dB all':>9}{'dB in-band':>12}{'eff_up':>9}")
    for family in FAMILIES:
        runs = [(s, p, m) for (f, _), (s, _, p, m) in loaded.items() if f == family]
        a, b, e = [], [], []
        for s, p, m in runs:
            keys = sorted(set(s[p]) & set(s["m0_plus"]) & set(s["base"]))
            band = [i for i in keys if 0.15 <= s["base"][i] <= 0.85]
            a.append(netted(s, p, m))
            b.append(netted(s, p, m, items=band))
            room = statistics.mean(1 - s["base"][i] for i in keys)
            e.append(statistics.mean(s[p][i] - s["m0_plus"][i] for i in keys) / room)
        print(f"   {family:<14}{statistics.mean(a):>9.4f}{statistics.mean(b):>12.4f}{statistics.mean(e):>9.3f}")

    print("\n4. FRAMING — dB by item framing, and with the shared framings equally weighted")
    print(f"   {'family':<14}{'1p':>9}{'3p':>9}{'3p>1p':>8}{'equal-mix dB':>14}")
    for family in FAMILIES:
        runs = [(s, f, p, m) for (fam, _), (s, f, p, m) in loaded.items() if fam == family]
        one, three, eq = [], [], []
        for s, fr, p, m in runs:
            i1 = [i for i, t in fr.items() if t == "1p"]
            i3 = [i for i, t in fr.items() if t == "3p"]
            a, b = netted(s, p, m, items=i1), netted(s, p, m, items=i3)
            one.append(a); three.append(b); eq.append((a + b) / 2)
        wins = sum(1 for a, b in zip(one, three) if b > a)
        print(f"   {family:<14}{statistics.mean(one):>9.4f}{statistics.mean(three):>9.4f}"
              f"{f'{wins}/{len(one)}':>8}{statistics.mean(eq):>14.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
