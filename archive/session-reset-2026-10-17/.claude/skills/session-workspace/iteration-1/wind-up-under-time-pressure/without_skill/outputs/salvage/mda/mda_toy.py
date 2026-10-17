#!/usr/bin/env python3
"""MDA toy: the four-part loop on a problem with known ground truth.

The world is a ChemBench-lite enzyme assay.  The true law is substrate
inhibition,

    r(C_A, Enz) = kcat * Enz * C_A / (Km + C_A + C_A**2 / Ki)

with multiplicative Gaussian noise.  It rises, peaks at C_A = sqrt(Km*Ki), and
then *falls* -- and the fall is only visible at high substrate.  Initial data is
low-C_A only, so the agent must design its way out to see it.  That is the
Yukawa "short-range data cannot break the tie" structure in miniature.

The four parts, and where each lives:

    proposer    MockProposer          -- stands in for the LLM; same interface
    inference   fit_smc / pool_posterior -- log Z by adaptive-tempered SMC
    design      voi                   -- Eq. 10, cross-hypothesis disagreement
    M-open      residual + thresholds -- Alg. 1 lines 5-6

Run:
    python mda_toy.py loop      # one verbose discovery run
    python mda_toy.py checks    # seven assertions on the math
    python mda_toy.py           # both
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass, field

import numpy as np

INPUTS = ("C_A", "Enz")


# =============================================================================
# 0. numerics
# =============================================================================

def logsumexp(a, axis=None):
    a = np.asarray(a, dtype=float)
    m = np.max(a, axis=axis, keepdims=True)
    m = np.where(np.isfinite(m), m, 0.0)
    s = np.sum(np.exp(a - m), axis=axis, keepdims=True)
    with np.errstate(divide="ignore"):
        r = m + np.log(s)
    if axis is None:
        return float(r.reshape(()))
    return np.squeeze(r, axis=axis)


def normalize_log(lw):
    return lw - logsumexp(lw)


def ess_of(logw):
    lw = np.asarray(logw, float)
    m = logsumexp(lw)
    if not np.isfinite(m):
        return 0.0
    with np.errstate(over="ignore", under="ignore"):
        s = float(np.sum(np.exp(lw - m) ** 2))
    return 1.0 / s if s > 0 else 0.0


# =============================================================================
# 1. the world  (ground truth -- the agent never sees these numbers)
# =============================================================================

@dataclass(frozen=True)
class World:
    """A world owns three things the loop needs: what it can be asked (`inputs`,
    `designs`), how noisy an answer is (`noise`), and what counts as truth
    (`truth_at`, `error`).  Everything else in this file is world-agnostic."""

    kcat: float = 2.0
    Km: float = 0.5
    Ki: float = 2.0
    sigma_rel: float = 0.05
    inputs: tuple = INPUTS
    direction_axis: str = "C_A"

    @property
    def designs(self):
        return DESIGNS

    def valid(self, f):
        return f > 0

    def noise(self, mu):
        """sd of one observation whose mean is `mu`.  Relative here; a world with a
        bounded score would return something additive and heteroscedastic."""
        return np.maximum(self.sigma_rel * np.abs(np.asarray(mu, float)), 1e-12)

    def initial_data(self, rng, n=4):
        d = Data(inputs=self.inputs)
        for c in np.geomspace(0.1, 1.0, n):
            design = {"C_A": float(c), "Enz": 0.5}
            d.add(design, self.observe(design, rng))
        return d

    def queries(self, rng, n=40):
        return {"C_A": np.exp(rng.uniform(math.log(0.05), math.log(50.0), n)),
                "Enz": rng.uniform(0.3, 3.0, n)}

    def truth_at(self, designs):
        return self.rate(designs["C_A"], designs["Enz"])

    def error(self, pred, truth):
        return rmsle(pred, truth)

    def rate(self, C_A, Enz):
        C_A = np.asarray(C_A, float)
        Enz = np.asarray(Enz, float)
        return self.kcat * Enz * C_A / (self.Km + C_A + C_A**2 / self.Ki)

    def observe(self, design, rng):
        f = float(self.rate(design["C_A"], design["Enz"]))
        return max(f * (1.0 + self.sigma_rel * rng.standard_normal()), 1e-9)


C_A_GRID = np.geomspace(0.05, 50.0, 12)
ENZ_GRID = (0.5, 2.0)
DESIGNS = [{"C_A": float(a), "Enz": float(e)} for e in ENZ_GRID for a in C_A_GRID]


@dataclass
class Data:
    rows: list = field(default_factory=list)
    inputs: tuple = INPUTS

    def add(self, design, y):
        self.rows.append((dict(design), float(y)))

    def arrays(self):
        designs = {k: np.array([r[0][k] for r in self.rows]) for k in self.inputs}
        return designs, np.array([r[1] for r in self.rows])

    def __len__(self):
        return len(self.rows)


# =============================================================================
# 2. hypotheses  (what the proposer emits, as a typed object rather than JSON)
# =============================================================================

@dataclass(frozen=True)
class Param:
    name: str
    low: float
    high: float
    log: bool = True

    def bounds_u(self):
        return (math.log(self.low), math.log(self.high)) if self.log else (self.low, self.high)


@dataclass(frozen=True)
class Hypothesis:
    name: str
    expr: str
    params: tuple
    addresses: tuple = ()      # which residual direction this form explains
    order: int = 99            # proposer's fallback preference
    pinned: bool = False
    """Never evidence-pruned out of the pool.  An escape hatch is only an escape
    hatch if it is still there when everything else has been pruned."""
    inflate: str = ""
    """Name of a declared parameter that MULTIPLIES the observation noise.

    This is how a 'none of the above' hypothesis is expressed: a form that admits
    it cannot predict, and pays for that admission in evidence while widening the
    predictive interval.  Without one, p(m|D) = softmax(log Z) is normalised over
    the pool and therefore sums to 1 however bad every member is."""

    @property
    def dim(self):
        return len(self.params)


K = lambda n, lo=1e-3, hi=50.0: Param(n, lo, hi, True)      # noqa: E731  scale param
CAT = lambda n: Param(n, 0.01, 100.0, True)                  # noqa: E731  turnover

BANK = (
    Hypothesis("linear", "k*Enz*C_A", (CAT("k"),), order=1),
    Hypothesis("michaelis_menten", "kcat*Enz*C_A/(Km + C_A)",
               (CAT("kcat"), K("Km")), order=2),
    Hypothesis("hill", "kcat*Enz*C_A**n/(Kh**n + C_A**n)",
               (CAT("kcat"), K("Kh"), Param("n", 0.5, 4.0, False)), order=3),
    # --- the truth, and its near-misses ---
    Hypothesis("substrate_inhibition", "kcat*Enz*C_A/(Km + C_A + C_A**2/Ki)",
               (CAT("kcat"), K("Km"), K("Ki")),
               addresses=("overpredicts_at_high_C_A",), order=4),
    Hypothesis("mm_with_decay", "kcat*Enz*C_A*exp(-C_A/Kd)/(Km + C_A)",
               (CAT("kcat"), K("Km"), K("Kd")),
               addresses=("overpredicts_at_high_C_A",), order=5),
    Hypothesis("hill_substrate_inhibition", "kcat*Enz*C_A**n/(Kh**n + C_A**n + C_A**2/Ki)",
               (CAT("kcat"), K("Kh"), Param("n", 0.5, 4.0, False), K("Ki")),
               addresses=("overpredicts_at_high_C_A",), order=6),
    Hypothesis("mm_plus_offset", "kcat*Enz*C_A/(Km + C_A) + c*Enz",
               (CAT("kcat"), K("Km"), K("c", 1e-4, 10.0)), order=7),
)
BY_NAME = {h.name: h for h in BANK}
TRUTH = "substrate_inhibition"

SAFE = {"exp": np.exp, "log": np.log, "sqrt": np.sqrt}


def to_theta(h, u):
    out = np.empty_like(u)
    for j, p in enumerate(h.params):
        out[:, j] = np.exp(u[:, j]) if p.log else u[:, j]
    return out


def predict(h, designs, theta):
    """(D,) designs x (P,d) params -> (D,P) predicted rates."""
    n_d = len(next(iter(designs.values())))
    env = dict(SAFE)
    for k, v in designs.items():
        env[k] = np.asarray(v, float)[:, None]
    for j, p in enumerate(h.params):
        env[p.name] = theta[:, j][None, :]
    with np.errstate(all="ignore"):
        out = eval(h.expr, {"__builtins__": {}}, env)          # noqa: S307  toy only
    return np.broadcast_to(np.asarray(out, float), (n_d, theta.shape[0]))


def _inflation(h, theta):
    if not h.inflate:
        return 1.0
    j = [p.name for p in h.params].index(h.inflate)
    return theta[:, j][None, :]


def loglik(h, data, theta, world):
    designs, y = data.arrays()
    f = predict(h, designs, theta)
    with np.errstate(all="ignore"):
        bad = ~np.isfinite(f) | ~world.valid(f)
        s = world.noise(np.where(bad, 1.0, f)) * _inflation(h, theta)
        ll = -0.5 * np.log(2 * np.pi * s**2) - 0.5 * ((y[:, None] - f) / s) ** 2
        ll = np.where(bad, -np.inf, ll)
    return ll.sum(axis=0)


# =============================================================================
# 3. inference -- p(D|m) = int p(D|m,theta) p(theta|m) dtheta
#
#    The integral is the whole point: it is what charges a hypothesis for its
#    free parameters.  Max-likelihood would rank the most flexible form first
#    every time.
# =============================================================================

@dataclass
class Fit:
    h: Hypothesis
    log_z: float
    theta: np.ndarray
    logw: np.ndarray
    ess: float
    n_temps: int

    def mean_predict(self, designs):
        f = predict(self.h, designs, self.theta)
        return f @ np.exp(self.logw)


def _scale(ll, delta):
    if delta <= 0:
        return np.zeros_like(ll)
    return np.where(np.isfinite(ll), ll * delta, -np.inf)


def _next_delta(logw, ll, beta, ess_frac):
    """Bisect for the temperature step that drops ESS to the target."""
    target = ess_frac * len(logw)
    hi = 1.0 - beta
    if ess_of(logw + _scale(ll, hi)) >= target:
        return hi
    lo = 0.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if ess_of(logw + _scale(ll, mid)) >= target:
            lo = mid
        else:
            hi = mid
    return max(lo, 1e-9)


def _move(h, data, world, u, ll, beta, rng, n_mcmc, lo, hi):
    """Random-walk MH at the current temperature; keeps particles from collapsing."""
    P, d = u.shape
    cov = np.atleast_2d(np.cov(u.T)) if P > d else np.eye(d)
    cov = cov + 1e-10 * np.eye(d)
    try:
        L = np.linalg.cholesky(cov * (2.38**2 / d))
    except np.linalg.LinAlgError:
        L = np.diag(np.sqrt(np.diag(cov)) * (2.38 / math.sqrt(d)))
    for _ in range(n_mcmc):
        prop = u + rng.standard_normal((P, d)) @ L.T
        inside = np.all((prop >= lo) & (prop <= hi), axis=1)
        ll_p = loglik(h, data, to_theta(h, prop), world)
        with np.errstate(invalid="ignore"):
            log_acc = beta * (np.nan_to_num(ll_p, nan=-np.inf) - np.nan_to_num(ll, nan=-np.inf))
        log_acc = np.where(np.isnan(log_acc), -np.inf, log_acc)
        acc = inside & (np.log(rng.uniform(size=P)) < log_acc)
        u = np.where(acc[:, None], prop, u)
        ll = np.where(acc, ll_p, ll)
    return u, ll


def fit_smc(h, data, world, rng, n_particles=800, ess_frac=0.5, n_mcmc=3):
    """Adaptive-tempered SMC (the paper's Alg. 4), returning log Z and a particle set."""
    d = h.dim
    lo = np.array([p.bounds_u()[0] for p in h.params])
    hi = np.array([p.bounds_u()[1] for p in h.params])
    u = rng.uniform(lo, hi, size=(n_particles, d))
    ll = loglik(h, data, to_theta(h, u), world)
    logw = np.full(n_particles, -math.log(n_particles))
    beta, log_z, n_temps = 0.0, 0.0, 0

    while beta < 1.0:
        if not np.any(np.isfinite(ll)):
            return Fit(h, -np.inf, to_theta(h, u), logw, 0.0, n_temps)
        delta = _next_delta(logw, ll, beta, ess_frac)
        beta_new = min(1.0, beta + delta)
        incr = _scale(ll, beta_new - beta)
        log_z += logsumexp(logw + incr)
        logw = normalize_log(logw + incr)
        beta = beta_new
        n_temps += 1
        # resample + move
        w = np.exp(logw)
        idx = rng.choice(n_particles, size=n_particles, p=w / w.sum())
        u, ll = u[idx], ll[idx]
        logw = np.full(n_particles, -math.log(n_particles))
        u, ll = _move(h, data, world, u, ll, beta, rng, n_mcmc, lo, hi)
        if n_temps > 200:
            break

    return Fit(h, log_z, to_theta(h, u), logw, ess_of(logw), n_temps)


def fit_is(h, data, world, rng, n_particles=40000):
    """Naive prior importance sampling -- the ten-line version, for contrast."""
    d = h.dim
    lo = np.array([p.bounds_u()[0] for p in h.params])
    hi = np.array([p.bounds_u()[1] for p in h.params])
    u = rng.uniform(lo, hi, size=(n_particles, d))
    ll = loglik(h, data, to_theta(h, u), world)
    log_z = logsumexp(ll) - math.log(n_particles)
    logw = normalize_log(ll)
    return Fit(h, log_z, to_theta(h, u), logw, ess_of(logw), 0)


def pool_posterior(pool, data, world, rng, **kw):
    """Fit every structure, then p(m|D) = softmax(log Z) under a uniform prior."""
    fits = [fit_smc(h, data, world, rng, **kw) for h in pool]
    lz = np.array([f.log_z for f in fits])
    pm = np.exp(normalize_log(lz)) if np.any(np.isfinite(lz)) else np.ones(len(lz)) / len(lz)
    return fits, pm


# =============================================================================
# 4. design -- Eq. 10.  VoI is cross-hypothesis disagreement, noise-weighted.
# =============================================================================

def hypothesis_means(fits, designs):
    return np.array([f.mean_predict(designs) for f in fits])       # (M, D)


def voi(mus, pm, world):
    """Eq. 10: sum_m p(m|D) * ||mu_m(xi) - mu_bar(xi)||^2_{Sigma_eps^-1}.

    Sigma_eps is the *observation* noise, and here it is multiplicative, so the
    precision weighting is 1/(sigma_rel*mu_bar)^2.  Without it this degenerates
    into 'probe wherever the rate is biggest' -- which is exactly the MEAN
    acquisition the paper contrasts against.
    """
    mubar = (pm[:, None] * mus).sum(0)
    sig = world.noise(mubar)
    return (pm[:, None] * ((mus - mubar) / sig) ** 2).sum(0)


def dedupe_pool(pool, fits, pm, world, tol_z=0.4):
    """Merge hypotheses that are the *same function* of the design, whatever they
    are called or how they are written.

    String dedup is not enough.  A real proposer returns reparameterisations:
    Vmax*C_A/((Km+C_A)*(1+C_A/Ki)) expands to Km + C_A*(1+Km/Ki) + C_A**2/Ki, which
    is the substrate-inhibition family again after rescaling.  Symbolic equivalence
    (sympy) does not catch that either -- the two are equal only *after* a parameter
    substitution.  Comparing posterior-mean predictions across the design menu does.

    Unmerged duplicates split the posterior, which breaks two mechanisms at once:
    p(MAP) never crosses tau_p so the pool never shrinks, and VoI reads ~0 for a
    reason ('these two agree') that looks identical to 'the question is settled'.

    Tolerance is tied to the observation noise rather than set absolutely: two forms
    that agree to well inside the noise are, for forecasting and for design, one
    model.  Measured separation on this world: reparameterisations 0.3-0.5%,
    genuinely distinct families 4.7%.
    """
    menu = {k: np.array([d[k] for d in world.designs]) for k in world.inputs}
    mus = hypothesis_means(fits, menu)
    order = sorted(range(len(fits)), key=lambda i: (-fits[i].log_z, fits[i].h.dim))
    keep, merged = [], []
    for i in order:
        if fits[i].h.inflate:          # an escape hatch is not a rival form
            keep.append(i)
            continue
        dup = None
        for j in keep:
            if fits[j].h.inflate:
                continue
            scale = world.noise((mus[i] + mus[j]) / 2)
            if float(np.max(np.abs(mus[i] - mus[j]) / scale)) < tol_z:
                dup = j
                break
        if dup is None:
            keep.append(i)
        else:
            merged.append((fits[i].h.name, fits[dup].h.name))
    keep = sorted(keep)
    lz = np.array([fits[i].log_z for i in keep])
    return ([pool[i] for i in keep], [fits[i] for i in keep],
            np.exp(normalize_log(lz)), merged)


def predictive_sd(fits, pm, designs, world):
    """Total sd of the posterior predictive: between-hypothesis disagreement +
    within-hypothesis parameter spread + observation noise (law of total variance).

    The paper thresholds a *raw relative* residual.  With 5% observation noise a
    0.15 relative residual is a 3-sigma event, so that trigger is a one-sample
    3-sigma test whose false-positive rate is set by the noise, not by the model
    being wrong.  Dividing by this sd instead makes the trigger a z-score.
    """
    mus, vs, ns = [], [], []
    for f in fits:
        p = predict(f.h, designs, f.theta)              # (D, P)
        w = np.exp(f.logw)
        m = p @ w
        vs.append(np.maximum((p ** 2) @ w - m ** 2, 0.0))
        ns.append(((world.noise(p) * _inflation(f.h, f.theta)) ** 2) @ w)
        mus.append(m)
    mus, vs, ns = np.array(mus), np.array(vs), np.array(ns)
    mubar = (pm[:, None] * mus).sum(0)
    total = (pm[:, None] * (vs + ns + mus ** 2)).sum(0) - mubar ** 2
    return mubar, np.sqrt(np.maximum(total, 1e-24))


def bayes_forecast(fits, pm, designs):
    return (pm[:, None] * hypothesis_means(fits, designs)).sum(0)


# =============================================================================
# 5. M-open -- the residual, and the proposer it wakes up
# =============================================================================

def summary_residual(fit, data):
    """CHECK=SUMMARY: median relative residual of the MAP model on collected data."""
    designs, y = data.arrays()
    yhat = fit.mean_predict(designs)
    return float(np.median(np.abs(y - yhat) / np.maximum(np.abs(y), 1e-12)))


def residual_direction(fit, data, axis="C_A"):
    """The 'residual correlates with input X' hint the ChemBench prompt supplies."""
    designs, y = data.arrays()
    yhat = fit.mean_predict(designs)
    rel = (y - yhat) / np.maximum(np.abs(yhat), 1e-12)
    x = np.log(np.maximum(designs[axis], 1e-12))
    if len(y) < 3 or np.std(rel) < 1e-12 or np.std(x) < 1e-12:
        return ""
    c = float(np.corrcoef(rel, x)[0, 1])
    if c < -0.4:
        return f"overpredicts_at_high_{axis}"
    if c > 0.4:
        return f"underpredicts_at_high_{axis}"
    return ""


class MockProposer:
    """Stands in for the LLM, with the same *interface* as the paper's proposer:
    it sees the whole pool plus a residual report and returns structurally
    different candidates.  The 'reasoning' is a hard-coded lookup, which is the
    point -- it lets the Bayesian machinery be validated with zero API calls.
    """

    def __init__(self, bank=BANK):
        self.bank = bank
        self.calls = 0
        self.log = []

    def __call__(self, pool, report, n_new):
        self.calls += 1
        have = {h.name for h in pool}
        direction = report.get("direction", "")
        ranked = sorted(self.bank, key=lambda h: (0 if direction in h.addresses else 1, h.order))
        out = [h for h in ranked if h.name not in have][:n_new]
        self.log.append({"direction": direction, "proposed": [h.name for h in out]})
        return out


# =============================================================================
# 6. the loop -- Algorithm 1
# =============================================================================

@dataclass
class Round:
    b: int
    design: dict
    q_hat: float
    y: float
    residual: float
    residual_rel: float
    residual_z: float
    p_star: float
    map_name: str
    pool: list
    pm: np.ndarray
    proposed: list
    n_pool: int
    rmsle: float


def test_queries(rng, n=40):
    """Held-out query distribution Q, disjoint from the design menu."""
    return {"C_A": np.exp(rng.uniform(math.log(0.05), math.log(50.0), n)),
            "Enz": rng.uniform(0.3, 3.0, n)}


def rmsle(pred, truth):
    p = np.maximum(np.asarray(pred, float), 1e-12)
    t = np.maximum(np.asarray(truth, float), 1e-12)
    return float(np.sqrt(np.mean((np.log(p) - np.log(t)) ** 2)))


def run_loop(world, pool, proposer, *, B=8, strategy="voi", seed=0,
             tau_r=None, tau_p=0.90, n_max=6, n_min=3, n_new=3, r_max=1,
             n_particles=800, trigger="z", dedupe=True, verbose=False):
    if tau_r is None:
        tau_r = 3.0 if trigger == "z" else 0.15
    rng = np.random.default_rng(seed)
    data = world.initial_data(rng)
    pool = list(pool)
    q = world.queries(np.random.default_rng(12345))
    truth_q = world.truth_at(q)
    menu = {k: np.array([d[k] for d in world.designs]) for k in world.inputs}
    hist = []

    fits, pm = pool_posterior(pool, data, world, rng, n_particles=n_particles)

    for b in range(1, B + 1):
        # ---- state the design decision is made from (BEFORE this round's data) ----
        i_map = int(np.argmax(pm))
        map_fit, map_name, p_star = fits[i_map], fits[i_map].h.name, float(pm[i_map])
        if verbose:
            _print_pool(b, data, fits, pm, "belief entering the round")

        # ---- ACQUIRE (Alg. 2): design, predict, observe, score -------------------
        mus = hypothesis_means(fits, menu)
        scores = voi(mus, pm, world)
        mubar = (pm[:, None] * mus).sum(0)

        if strategy == "voi":
            pick = int(np.argmax(scores))
        elif strategy == "random":
            pick = int(rng.integers(len(world.designs)))
        elif strategy == "mean":
            pick = int(np.argmax(mubar))
        else:
            raise ValueError(strategy)
        design = world.designs[pick]

        one = {k: np.array([design[k]]) for k in world.inputs}
        _, sd = predictive_sd(fits, pm, one, world)
        q_hat = float(mubar[pick])              # CHECK=QUERY: predict BEFORE running
        y = world.observe(design, rng)
        r_rel = abs(y - q_hat) / max(abs(q_hat), 1e-12)
        r_z = abs(y - q_hat) / float(sd[0])
        r_query = r_z if trigger == "z" else r_rel
        if verbose:
            _print_design(world, scores, mubar, mus, fits, pick, design, q_hat, y,
                          r_rel, r_z, float(sd[0]), r_query, tau_r, trigger)
        data.add(design, y)

        # ---- Alg. 1 lines 5-6: thresholds decide whether the LLM wakes up --------
        R_m = r_max if r_query > tau_r else 0
        N_m = n_min if (p_star > tau_p and r_query <= tau_r) else n_max

        proposed = []
        for _ in range(R_m):
            report = {
                "direction": residual_direction(map_fit, data, world.direction_axis),
                "residuals": {f.h.name: summary_residual(f, data) for f in fits},
            }
            new = proposer(pool, report, n_new)
            proposed += [h.name for h in new]
            pool = pool + new
        if verbose:
            if R_m:
                print(f"  M-open: r > tau_r -> proposer called."
                      f"  hint={report['direction'] or 'none'}  ->  {proposed}")
            else:
                shrink = f" and p*={p_star:.3f} > tau_p -> pool shrinks to {N_m}" if p_star > tau_p else ""
                print(f"  M-open: quiet, no proposer call{shrink}")

        # ---- MODEL-INFERENCE on the grown data, then evidence-prune to N_m ------
        fits, pm = pool_posterior(pool, data, world, rng, n_particles=n_particles)
        if dedupe:
            pool, fits, pm, merged = dedupe_pool(pool, fits, pm, world)
            if verbose and merged:
                for dropped, kept in merged:
                    print(f"  dedupe: {dropped} is functionally {kept} -> merged")
        if len(pool) > N_m:
            pin = {i for i, f in enumerate(fits) if f.h.pinned}
            ranked = [int(i) for i in np.argsort([-f.log_z for f in fits]) if i not in pin]
            keep = sorted(pin | set(ranked[:max(0, N_m - len(pin))]))
            pool = [pool[i] for i in keep]
            fits = [fits[i] for i in keep]
            pm = np.exp(normalize_log(np.array([f.log_z for f in fits])))

        err = world.error(bayes_forecast(fits, pm, q), truth_q)
        hist.append(Round(b, design, q_hat, y, r_query, r_rel, r_z, p_star, map_name,
                          [f.h.name for f in fits], pm, proposed, len(pool), err))
        if verbose:
            print(f"  -> pool now {len(pool)}   held-out RMSLE {err:.4f}")

    return hist, pool, fits, pm, data


def _print_pool(b, data, fits, pm, label):
    print(f"\n{'-' * 78}\nround {b}   ({len(data)} observations)   {label}")
    print(f"  {'hypothesis':<28}{'dim':>4}{'log Z':>10}{'p(m|D)':>9}{'med|resid|':>12}")
    for i in np.argsort(-np.array([f.log_z for f in fits])):
        f = fits[i]
        print(f"  {f.h.name:<28}{f.h.dim:>4}{f.log_z:>10.2f}{pm[i]:>9.3f}"
              f"{summary_residual(f, data):>12.3f}")


def _fmt(design):
    return " ".join(f"{k}={v:g}" for k, v in design.items())


def _print_design(world, scores, mubar, mus, fits, pick, design, q_hat, y,
                  r_rel, r_z, sd, r, tau_r, trigger):
    print(f"  design: VoI over {len(world.designs)} cells, top 3 --")
    for rank, i in enumerate(np.argsort(-scores)[:3], 1):
        spread = "  ".join(f"{fits[j].h.name[:12]}={mus[j, i]:.3f}"
                           for j in range(min(3, len(fits))))
        print(f"    {rank}. {_fmt(world.designs[i]):<28}"
              f"   VoI={scores[i]:>9.1f}   mu_bar={mubar[i]:.4f}   [{spread}]")
    i_mean = int(np.argmax(mubar))
    print(f"    chose {_fmt(design)}"
          f"   (mean-seeking would take {_fmt(world.designs[i_mean])})")
    verdict = "SURPRISE" if r > tau_r else "as expected"
    print(f"  predicted q_hat={q_hat:.4f} +/- {sd:.4f}  ->  observed y={y:.4f}")
    print(f"    relative residual {r_rel:5.3f}   z-score {r_z:6.2f}"
          f"   -> {verdict} (trigger={trigger}, tau_r={tau_r})")


# =============================================================================
# 7. checks
# =============================================================================

def _dense_data(world, rng, n=12):
    d = Data(inputs=world.inputs)
    for c in np.geomspace(0.08, 40.0, n):
        design = {"C_A": float(c), "Enz": 1.0}
        d.add(design, world.observe(design, rng))
    return d


def check_evidence_stability(world):
    """1. Is log Z a stable number, or is the estimator the thing we're measuring?"""
    data = _dense_data(world, np.random.default_rng(1))
    h = BY_NAME[TRUTH]
    a = fit_smc(h, data, world, np.random.default_rng(10))
    b = fit_smc(h, data, world, np.random.default_rng(11))
    i = fit_is(h, data, world, np.random.default_rng(12))
    print(f"    SMC log Z  seed A {a.log_z:8.3f}  ({a.n_temps} temperatures)")
    print(f"    SMC log Z  seed B {b.log_z:8.3f}  |Δ| = {abs(a.log_z - b.log_z):.3f} nats")
    print(f"    naive IS   40k    {i.log_z:8.3f}  ESS = {i.ess:.1f} of 40000")
    assert abs(a.log_z - b.log_z) < 1.0, "log Z not reproducible across seeds"
    return f"log Z stable to {abs(a.log_z - b.log_z):.2f} nats; naive IS ESS={i.ess:.1f}"


def check_occam(world):
    """2. Does integrating out theta actually charge for free parameters?"""
    data = _dense_data(world, np.random.default_rng(2))
    simple = BY_NAME[TRUTH]                          # 3 params
    complex_ = BY_NAME["hill_substrate_inhibition"]  # 4 params, nests the truth
    fs = fit_smc(simple, data, world, np.random.default_rng(20))
    fc = fit_smc(complex_, data, world, np.random.default_rng(21))
    # best-fit (max) likelihood, for contrast with the integrated one
    ml_s = float(np.max(loglik(simple, data, fs.theta, world)))
    ml_c = float(np.max(loglik(complex_, data, fc.theta, world)))
    print(f"    {simple.name:<28} dim={simple.dim}  max loglik {ml_s:8.2f}   log Z {fs.log_z:8.2f}")
    print(f"    {complex_.name:<28} dim={complex_.dim}  max loglik {ml_c:8.2f}   log Z {fc.log_z:8.2f}")
    print(f"    the nesting model fits better by {ml_c - ml_s:.2f} nats at its best theta,")
    print(f"    and loses by {fs.log_z - fc.log_z:.2f} nats once theta is integrated out")
    assert ml_c >= ml_s - 0.5, "nesting model should fit at least as well at its MLE"
    assert fs.log_z > fc.log_z, "Occam penalty absent: complex model won on evidence"
    return f"Occam gap {fs.log_z - fc.log_z:.2f} nats in favour of the simpler true form"


def check_concentration(world):
    """3. Does the posterior over structures concentrate on the truth?"""
    pool = [BY_NAME[n] for n in ("linear", "michaelis_menten", "hill", TRUTH,
                                 "mm_with_decay", "mm_plus_offset")]
    hist, _, fits, pm, _ = run_loop(world, pool, MockProposer(), B=6, seed=3)
    names = [f.h.name for f in fits]
    p_truth = float(pm[names.index(TRUTH)]) if TRUTH in names else 0.0
    for r in hist:
        i = r.pool.index(TRUTH) if TRUTH in r.pool else None
        print(f"    round {r.b}: p(truth|D) = {r.pm[i] if i is not None else 0.0:.3f}"
              f"   MAP = {r.map_name}")
    assert p_truth > 0.9, f"posterior did not concentrate on the truth (p={p_truth:.3f})"
    return f"p(truth|D) = {p_truth:.3f} after 6 experiments"


def check_voi_beats_random(world):
    """4. Does designing for disagreement beat designing at random?"""
    pool = [BY_NAME[n] for n in ("linear", "michaelis_menten", "hill", TRUTH,
                                 "mm_with_decay", "mm_plus_offset")]
    seeds = range(5)
    out = {}
    for strat in ("voi", "random", "mean"):
        errs = []
        for s in seeds:
            hist, *_ = run_loop(world, pool, MockProposer(), B=5, seed=100 + s,
                                strategy=strat, n_particles=600)
            errs.append(hist[-1].rmsle)
        out[strat] = (float(np.mean(errs)), float(np.std(errs)), errs)
        print(f"    {strat:<7} held-out RMSLE after 5 experiments: "
              f"{out[strat][0]:.4f} ± {out[strat][1]:.4f}   {[round(e, 3) for e in errs]}")
    assert out["voi"][0] < out["random"][0], "VoI did not beat random design"
    return (f"VoI {out['voi'][0]:.4f} vs random {out['random'][0]:.4f} "
            f"vs mean-seeking {out['mean'][0]:.4f}")


def check_voi_degenerate(world):
    """5. When the pool agrees, is VoI at its noise floor rather than chasing it?

    Measured on *uninformative* data (low-C_A only).  The first version of this
    check used well-spread data and failed: with 12 informative observations the
    posterior had already collapsed onto one hypothesis, so VoI was ~0 for the
    distinct pool too.  That is correct Bayesian behaviour -- once the model is
    identified no experiment is informative about which model is true -- but it
    means VoI ~= 0 has *two* causes (duplicate hypotheses, or a resolved
    posterior) that VoI alone cannot tell apart.
    """
    rng = np.random.default_rng(5)
    sparse = world.initial_data(rng)                 # C_A <= 1.0: the tie is unbroken
    dense = _dense_data(world, rng)                   # spans the peak: tie is broken
    menu = {k: np.array([d[k] for d in DESIGNS]) for k in INPUTS}

    def max_voi(names, data, seed, dup=False):
        pool = ([Hypothesis(f"copy_{i}", BY_NAME[names[0]].expr, BY_NAME[names[0]].params)
                 for i in range(3)] if dup else [BY_NAME[n] for n in names])
        f, p = pool_posterior(pool, data, world, np.random.default_rng(seed))
        return float(voi(hypothesis_means(f, menu), p, world).max()), p

    triple = ("michaelis_menten", TRUTH, "mm_with_decay")
    v_dup, _ = max_voi(triple, sparse, 50, dup=True)
    v_live, p_live = max_voi(triple, sparse, 51)
    v_done, p_done = max_voi(triple, dense, 52)

    print(f"    identical pool,  unresolved data   max VoI = {v_dup:10.4f}   <- particle-noise floor")
    print(f"    distinct pool,   unresolved data   max VoI = {v_live:10.4f}   "
          f"(p_max={p_live.max():.3f})")
    print(f"    distinct pool,   resolved data     max VoI = {v_done:10.4f}   "
          f"(p_max={p_done.max():.3f})  <- nothing left to learn")
    assert v_live > 100 * v_dup, "VoI cannot tell agreement from disagreement"
    assert v_done < v_live, "VoI did not fall once the posterior resolved"
    return (f"floor {v_dup:.3f}, live {v_live:.1f} ({v_live / max(v_dup, 1e-12):.0f}x), "
            f"resolved {v_done:.3f}")


def check_m_open_fires(world):
    """6. Start with the truth's family missing. Does surprise trigger expansion?"""
    pool = [BY_NAME[n] for n in ("linear", "michaelis_menten", "hill")]
    prop = MockProposer()
    hist, final_pool, fits, pm, _ = run_loop(world, pool, prop, B=6, seed=6)
    fired = [r.b for r in hist if r.proposed]
    names = [f.h.name for f in fits]
    p_truth = float(pm[names.index(TRUTH)]) if TRUTH in names else 0.0
    for r in hist:
        print(f"    round {r.b}: C_A={r.design['C_A']:>6.2f}  q̂={r.q_hat:.4f} y={r.y:.4f} "
              f" r={r.residual:5.2f}  {'← EXPAND: ' + ','.join(r.proposed) if r.proposed else ''}")
    assert fired, "M-open never fired even though the true family was absent"
    assert p_truth > 0.5, f"expansion happened but truth did not win (p={p_truth:.3f})"
    return f"expanded at round {fired[0]}, p(truth|D)={p_truth:.3f} by round {hist[-1].b}"


def check_steady_state_quiet(world):
    """7. With the truth already in the pool, does the proposer stay switched off?

    The first version asserted zero calls over all 8 rounds under the paper's raw
    relative-residual trigger, and failed: 1 call.  Two separate causes, both
    real.  Early rounds have genuine predictive uncertainty, so a 15% miss is not
    surprising -- it is the pool still being undecided.  And with 5% observation
    noise, tau_r=0.15 *is* a 3-sigma test on a single draw, so it also fires on
    noise.  Both go away when the residual is divided by the predictive sd.
    """
    pool = [BY_NAME[n] for n in ("linear", "michaelis_menten", "hill", TRUTH,
                                 "mm_with_decay", "mm_plus_offset")]
    out = {}
    for trig in ("relative", "z"):
        prop = MockProposer()
        hist, *_ = run_loop(world, pool, prop, B=8, seed=7, n_min=3, trigger=trig)
        out[trig] = (prop.calls, [r.n_pool for r in hist], hist)
        fired = [f"round {r.b} (rel={r.residual_rel:.2f}, z={r.residual_z:.1f})"
                 for r in hist if r.proposed]
        print(f"    trigger={trig:<9} proposer calls {prop.calls}   "
              f"pool {[r.n_pool for r in hist]}"
              + (f"   fired: {'; '.join(fired)}" if fired else ""))
    calls_z, sizes_z, hist_z = out["z"]
    assert calls_z == 0, f"z-trigger fired {calls_z}x with the truth already present"
    assert sizes_z[-1] == 3, f"pool did not shrink to N_min (ended at {sizes_z[-1]})"
    return (f"z-trigger: 0 calls, pool {len(pool)} -> {sizes_z[-1]}; "
            f"raw relative trigger: {out['relative'][0]} spurious call(s)")


def check_functional_dedupe(world):
    """8. Does dedup merge a reparameterisation without merging a real rival?

    The pair below is the one a real proposer actually returned: expanding
    (Km+C_A)*(1+C_A/Ki) gives the substrate-inhibition denominator with a rescaled
    linear term, so it is the same 3-parameter family wearing a different face.
    """
    reparam = Hypothesis("product_form_inhibition",
                         "kcat*Enz*C_A/((Km + C_A)*(1 + C_A/Ki))",
                         (CAT("kcat"), K("Km"), K("Ki")))
    data = _dense_data(world, np.random.default_rng(8))
    pool = [BY_NAME[TRUTH], reparam, BY_NAME["mm_with_decay"], BY_NAME["michaelis_menten"]]
    fits, pm = pool_posterior(pool, data, world, np.random.default_rng(80))
    menu = {k: np.array([d[k] for d in DESIGNS]) for k in INPUTS}
    mus = hypothesis_means(fits, menu)

    def dev(i, j):
        return float(np.max(np.abs(mus[i] - mus[j]) /
                            np.maximum(np.abs(mus[i] + mus[j]) / 2, 1e-12)))

    print(f"    truth vs its reparameterisation   max rel deviation {dev(0, 1):.5f}")
    print(f"    truth vs mm_with_decay            max rel deviation {dev(0, 2):.5f}")
    print(f"    truth vs michaelis_menten         max rel deviation {dev(0, 3):.5f}")
    kept, _, pm2, merged = dedupe_pool(pool, fits, pm, world)
    names = [h.name for h in kept]
    print(f"    merged: {merged}")
    print(f"    pool {len(pool)} -> {len(kept)}: {names}")
    assert len(merged) == 1, f"expected exactly one merge, got {merged}"
    assert "mm_with_decay" in names, "merged away a genuinely different family"
    assert abs(pm2.sum() - 1.0) < 1e-9, "weights not renormalised after merge"
    return f"reparam at {dev(0, 1):.4f} merged; nearest real rival at {dev(0, 2):.4f} kept"


CHECKS = [
    ("evidence estimator is stable", check_evidence_stability),
    ("Occam penalty is real", check_occam),
    ("posterior concentrates on the truth", check_concentration),
    ("VoI beats random design", check_voi_beats_random),
    ("VoI is ~0 when the pool agrees", check_voi_degenerate),
    ("M-open fires on surprise and recovers", check_m_open_fires),
    ("steady state is quiet", check_steady_state_quiet),
    ("functional dedupe merges reparameterisations", check_functional_dedupe),
]


def run_checks(world):
    results, failures = [], 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        print(f"\n[{i}/{len(CHECKS)}] {name}")
        t0 = time.time()
        try:
            summary = fn(world)
            print(f"    PASS  ({time.time() - t0:.1f}s)  {summary}")
            results.append((name, True, summary))
        except AssertionError as e:
            print(f"    FAIL  ({time.time() - t0:.1f}s)  {e}")
            results.append((name, False, str(e)))
            failures += 1
    print(f"\n{'=' * 78}\n{len(CHECKS) - failures}/{len(CHECKS)} checks passed")
    for name, ok, summary in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<40} {summary}")
    return failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="all", choices=["loop", "checks", "all"])
    args = ap.parse_args()
    world = World()
    print(f"world: r = {world.kcat}*Enz*C_A/({world.Km} + C_A + C_A^2/{world.Ki}), "
          f"relative noise {world.sigma_rel}")
    print(f"       peak at C_A = sqrt(Km*Ki) = {math.sqrt(world.Km * world.Ki):.2f}; "
          f"D_0 is C_A <= 1.0 only")

    rc = 0
    if args.mode in ("loop", "all"):
        print(f"\n{'=' * 78}\nDISCOVERY LOOP  (pool starts without the true family)\n{'=' * 78}")
        pool = [BY_NAME[n] for n in ("linear", "michaelis_menten", "hill")]
        run_loop(world, pool, MockProposer(), B=6, seed=6, verbose=True)
    if args.mode in ("checks", "all"):
        print(f"\n{'=' * 78}\nCHECKS\n{'=' * 78}")
        rc = run_checks(world)
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
