"""The s7 step-36 read against matrix_s7_step36's registered conditions.

Both scales (probability, log-odds with the registered LOGIT_EPS=1e-6 clamp), both the
evidence contrast (m vs m0) and the explicit positive control (me vs m0), at step 24
(matrix_s7_2ep) and step 36 (matrix_s7_step36). The explicit contrast is recomputed from
responses via netted logic -- transfer.contrast reports only the evidence pair (standing
trap, STATE.md).
"""
import json, math, statistics, sys
sys.path.insert(0, "src")
from belief_transfer.metrics import bootstrap_ci
from belief_transfer.evals.suite import per_item

R = "data/results/factory_farming"
LOGIT_EPS = 1e-6
def logit(p):
    p = min(max(p, LOGIT_EPS), 1 - LOGIT_EPS); return math.log(p / (1 - p))

def netted(run, plus, minus, tf=lambda p: p):
    rows = [json.loads(l) for l in open(f"{R}/{run}/belief_responses.jsonl")]
    sel = lambda c: [r for r in rows if r["condition"] == c]
    a, b = per_item(sel(plus)), per_item(sel(minus))
    c, d = per_item(sel("m0_plus")), per_item(sel("m0_minus"))
    ids = sorted(set(a) & set(b) & set(c) & set(d))
    v = [(tf(a[i]) - tf(b[i])) - (tf(c[i]) - tf(d[i])) for i in ids]
    lo, hi = bootstrap_ci(v)
    return statistics.fmean(v), lo, hi, len(ids)

for label, plus, minus in [("evidence (article cell)", "m_plus", "m_minus"),
                           ("EXPLICIT positive ctrl", "me_plus", "me_minus")]:
    print(f"\n== {label} ==")
    for run, step in [("matrix_s7_2ep", 24), ("matrix_s7_step36", 36)]:
        p = netted(run, plus, minus)
        l = netted(run, plus, minus, tf=logit)
        print(f"  step {step}:  prob {p[0]:+.4f} [{p[1]:+.4f}, {p[2]:+.4f}]   "
              f"log-odds {l[0]:+.4f} [{l[1]:+.4f}, {l[2]:+.4f}]   n={p[3]}")
