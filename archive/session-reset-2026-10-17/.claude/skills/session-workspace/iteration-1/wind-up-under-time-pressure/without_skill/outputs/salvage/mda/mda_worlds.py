#!/usr/bin/env python3
"""Does the MDA loop survive an LLM-shaped world?

Same machinery as mda_toy (same fit_smc, voi, predictive_sd, dedupe, run_loop).
Only the world changes, and it changes to look like sft-drift:

  observable   a behavioural score in [0,1], like choice_bench accuracy
  noise        additive, heteroscedastic, and SMALLER when the arm degenerates
               (sd = 0.018 + 0.13*|mu-0.5|; collapsed arms CI +/-0.035 against
               healthy +/-0.077, which is what the repo actually measured)
  budget       B = 6
  axes         dose (1e5 words) x answer length (100 words) x prompt variety {0,1},
               and in D_0 dose and length are perfectly correlated -- exactly the
               multi-form corpus confound.  Breaking it costs a design.

Three worlds, increasing in nastiness:

  1 smooth   truth is IN the hypothesis language (a saturating curve in dose).
             Positive control: should behave like the enzyme world.
  2 gate     truth is a CONJUNCTION of thresholds (variety AND length>=3 AND
             dose>=0.5 -> collapse to 0.50).  Outside the language, but a steep
             saturating form or a sigmoid can partly fake it.
  3 latent   smooth truth PLUS a reproducible per-cell offset ~N(0, 0.06) that is
             not a function of any modelled axis.  Re-running a cell reproduces
             its own offset, so it reads as signal, not noise, and no amount of
             data averages it away.  This is "two things called M+ that are not
             the same object".

Scored on CALIBRATION, not recovery.  A harness that says p(MAP)=1.000 while
wrong is worse than no harness, because you would spend a GPU week on its design.

Run:  python mda_worlds.py            # all three worlds, both arms
      python mda_worlds.py --demo 3   # one verbose run of world 3
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

import numpy as np

import mda_toy as T
from mda_toy import CAT, Hypothesis, K, Param

DOSE = (0.1, 0.3, 1.0, 3.0)        # x 1e5 training words
LENGTH = (1.0, 3.0, 7.0)           # x 100 words per answer
VARIETY = (0.0, 1.0)               # fixed question vs varied user turns
DESIGNS = [{"dose": d, "length": ln, "variety": v}
           for v in VARIETY for ln in LENGTH for d in DOSE]

DIAGONAL = ((0.1, 1.0), (0.3, 3.0), (1.0, 7.0), (3.0, 7.0))
"""D_0: dose and length move together, as they did in the multi-form corpus."""

BASE, FLOOR = 0.82, 0.50


@dataclass
class TrainingWorld:
    kind: str = "smooth"
    latent_sd: float = 0.06
    latent_seed: int = 0
    inputs: tuple = ("dose", "length", "variety")
    direction_axis: str = "dose"
    _latent: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        rng = np.random.default_rng(1000 + self.latent_seed)
        for d in DESIGNS:
            self._latent[self._key(d["dose"], d["length"], d["variety"])] = (
                rng.standard_normal() * self.latent_sd
            )

    @staticmethod
    def _key(dose, length, variety):
        return (round(float(dose), 6), round(float(length), 6), round(float(variety), 6))

    @property
    def designs(self):
        return DESIGNS

    # --- the truth ----------------------------------------------------------
    def score(self, dose, length, variety):
        dose = np.asarray(dose, float)
        length = np.asarray(length, float)
        variety = np.asarray(variety, float)
        smooth = BASE - (BASE - FLOOR) * variety * dose / (dose + 0.8)
        if self.kind == "smooth":
            return smooth
        if self.kind == "gate":
            collapsed = (variety > 0.5) & (length >= 3.0) & (dose >= 0.5)
            return np.where(collapsed, FLOOR, BASE)
        if self.kind == "latent":
            d, ln, v = np.broadcast_arrays(dose, length, variety)
            off = np.array([self._latent.get(self._key(a, b, c), 0.0)
                            for a, b, c in zip(d.ravel(), ln.ravel(), v.ravel())])
            return np.clip(np.broadcast_to(smooth, d.shape) + off.reshape(d.shape),
                           0.02, 0.98)
        raise ValueError(self.kind)

    def truth_at(self, designs):
        return self.score(designs["dose"], designs["length"], designs["variety"])

    # --- what the loop needs ------------------------------------------------
    def valid(self, f):
        return (f > 0.02) & (f < 0.98)

    def noise(self, mu):
        """Heteroscedastic and bounded-score shaped: tightest at the collapse floor.

        This is the nasty one.  A degenerate arm answers uniformly, so its CI is
        NARROW -- the measurement is most confident exactly where it is least
        meaningful."""
        return 0.018 + 0.13 * np.abs(np.asarray(mu, float) - FLOOR)

    def observe(self, design, rng):
        mu = float(self.score(design["dose"], design["length"], design["variety"]))
        return float(np.clip(mu + self.noise(mu) * rng.standard_normal(), 0.02, 0.98))

    def initial_data(self, rng):
        d = T.Data(inputs=self.inputs)
        for dose, length in DIAGONAL:
            design = {"dose": dose, "length": length, "variety": 1.0}
            d.add(design, self.observe(design, rng))
        return d

    def queries(self, rng, n=None):
        return {k: np.array([d[k] for d in DESIGNS]) for k in self.inputs}

    def error(self, pred, truth):
        return float(np.sqrt(np.mean((np.asarray(pred) - np.asarray(truth)) ** 2)))


# --- the hypothesis language (fixed, so "outside the language" is controlled) --

U = lambda n, lo, hi: Param(n, lo, hi, False)       # noqa: E731

BANK = (
    Hypothesis("constant", "c", (U("c", 0.02, 0.98),), order=1),
    Hypothesis("dose_linear", "c - a*variety*dose",
               (U("c", 0.02, 0.98), U("a", 0.0, 0.5)), order=2),
    Hypothesis("length_saturating", "c - a*variety*length/(length + l50)",
               (U("c", 0.02, 0.98), U("a", 0.0, 0.6), K("l50", 0.05, 50.0)),
               addresses=("overpredicts_at_high_dose",), order=3),
    Hypothesis("dose_saturating", "c - a*variety*dose/(dose + d50)",
               (U("c", 0.02, 0.98), U("a", 0.0, 0.6), K("d50", 0.02, 50.0)),
               addresses=("overpredicts_at_high_dose",), order=4),
    Hypothesis("product_saturating", "c - a*variety*dose*length/(dose*length + k)",
               (U("c", 0.02, 0.98), U("a", 0.0, 0.6), K("k", 0.02, 200.0)),
               addresses=("overpredicts_at_high_dose",), order=5),
    Hypothesis("dose_power_saturating", "c - a*variety*dose**p/(dose**p + d50)",
               (U("c", 0.02, 0.98), U("a", 0.0, 0.6), K("d50", 0.02, 50.0),
                U("p", 0.5, 6.0)), order=6),
    Hypothesis("length_sigmoid", "c - a*variety/(1 + exp(-(length - l0)/s))",
               (U("c", 0.02, 0.98), U("a", 0.0, 0.6), U("l0", 0.5, 8.0),
                U("s", 0.05, 3.0)), order=7),
)
BY_NAME = {h.name: h for h in BANK}
START = ("constant", "dose_linear", "length_saturating")

CATCHALL = Hypothesis(
    "none_of_the_above", "c",
    (U("c", 0.02, 0.98), K("s_infl", 1.0, 25.0)),
    pinned=True, inflate="s_infl", order=0,
)
"""The fix for the failure predicted before running this: p(m|D)=softmax(log Z) is
normalised over the pool, so it sums to 1 however bad every member is.  This member
predicts nothing and admits it by inflating its own noise -- it loses on evidence
whenever any real form fits, and holds mass (and widens the interval) when none does."""


# --- scoring ------------------------------------------------------------------

@dataclass
class RunScore:
    z: list
    p_map: float
    late_fires: int
    decoupled: bool
    surface_rmse: float
    pool: list


def score_run(hist, fits, pm, world):
    on_diag = {(round(a, 6), round(b, 6)) for a, b in DIAGONAL}
    return RunScore(
        z=[r.residual_z for r in hist],
        p_map=float(np.max(pm)),
        late_fires=sum(1 for r in hist[-2:] if r.residual_z > 3.0),
        decoupled=any((round(r.design["dose"], 6), round(r.design["length"], 6)) not in on_diag
                      for r in hist),
        surface_rmse=hist[-1].rmsle,
        pool=[f.h.name for f in fits],
    )


def run_world(kind, *, catchall, seeds=range(24), B=6, verbose=False):
    out = []
    for s in seeds:
        world = TrainingWorld(kind=kind, latent_seed=s)
        pool = [BY_NAME[n] for n in START] + ([CATCHALL] if catchall else [])
        hist, _, fits, pm, _ = T.run_loop(
            world, pool, T.MockProposer(BANK), B=B, seed=s,
            n_max=6, n_min=3, n_particles=600, verbose=verbose)
        out.append(score_run(hist, fits, pm, world))
    return out


def summarize(rows):
    z = np.abs(np.concatenate([r.z for r in rows]))
    return {
        "coverage90": float(np.mean(z <= 1.645)),
        "median|z|": float(np.median(z)),
        "p_map": float(np.mean([r.p_map for r in rows])),
        "late_fire": float(np.mean([r.late_fires > 0 for r in rows])),
        "decoupled": float(np.mean([r.decoupled for r in rows])),
        "rmse": float(np.mean([r.surface_rmse for r in rows])),
    }


HEAD = ("world          arm         cover90   med|z|   p(MAP)  late-fire  decoupled   RMSE")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", type=int, default=0, help="verbose single run of world 1/2/3")
    ap.add_argument("--seeds", type=int, default=24)
    args = ap.parse_args()
    kinds = {1: "smooth", 2: "gate", 3: "latent"}

    if args.demo:
        kind = kinds[args.demo]
        print(f"### verbose demo, world = {kind}\n")
        run_world(kind, catchall=False, seeds=[0], B=6, verbose=True)
        return

    print("nominal coverage of the 90% predictive interval is 0.90.")
    print("late-fire = fraction of runs whose last 2 rounds still read z > 3")
    print("decoupled = fraction of runs where VoI bought an off-diagonal (dose != length) cell\n")
    print(HEAD)
    print("-" * len(HEAD))
    results = {}
    for n, kind in kinds.items():
        for catchall in (False, True):
            rows = run_world(kind, catchall=catchall, seeds=range(args.seeds))
            m = summarize(rows)
            results[(kind, catchall)] = m
            arm = "catchall" if catchall else "plain"
            print(f"{n} {kind:<12} {arm:<10} {m['coverage90']:7.2f} {m['median|z|']:8.2f}"
                  f" {m['p_map']:8.3f} {m['late_fire']:10.2f} {m['decoupled']:10.2f}"
                  f" {m['rmse']:7.3f}")
    return results


if __name__ == "__main__":
    main()
