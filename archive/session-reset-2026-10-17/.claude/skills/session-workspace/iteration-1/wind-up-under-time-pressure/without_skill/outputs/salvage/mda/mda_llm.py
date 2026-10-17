"""A real LLM proposer for mda_toy, on belief_transfer.generation.llm.

Same interface as MockProposer -- (pool, report, n_new) -> [Hypothesis] -- so the
Bayesian half of the loop is untouched and the two are directly comparable.

The prompt is a port of the paper's CHEMBENCH proposer (App. H.2): world context,
optional mechanism grammar, the collected experiments, residual-directed negative
evidence, budget/phase, then the language spec.  `--no-grammar` drops the family
list, which the paper never does -- MDA is explicitly "which composition do the
data support", not blind form discovery.  Worth knowing which regime you are in.

Structured output uses `Client.complete_tool`, a forced function call, so the
response is a validated payload rather than parsed prose.  Every call is cached by
(model, prompt, tool, replicate).
"""

from __future__ import annotations

import ast
import asyncio
import sys
from pathlib import Path

import numpy as np

REPO = Path("/Users/sunny/dev/sft-drift")
sys.path.insert(0, str(REPO / "belief-transfer" / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

from belief_transfer.generation import llm  # noqa: E402
from belief_transfer.generation.cache import Cache  # noqa: E402

import mda_toy as T  # noqa: E402

CACHE_PATH = Path(__file__).resolve().parent / "mda_llm_cache.jsonl"

PROPOSE_TOOL = llm.Tool(
    name="propose_rate_laws",
    description="Return candidate mechanistic rate laws for the observed assay data.",
    parameters={
        "type": "object",
        "properties": {
            "hypotheses": {
                "type": "array",
                "description": "Distinct candidate rate laws.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "short snake_case identifier for the mechanism",
                        },
                        "expr": {
                            "type": "string",
                            "description": (
                                "Python expression for r0 in terms of C_A, Enz and the "
                                "declared parameters. Operators + - * / ** and functions "
                                "exp, log, sqrt only."
                            ),
                        },
                        "rationale": {
                            "type": "string",
                            "description": "one sentence naming the mechanism this encodes",
                        },
                        "params": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "low": {"type": "number"},
                                    "high": {"type": "number"},
                                    "log_scale": {
                                        "type": "boolean",
                                        "description": "true for scale parameters spanning decades",
                                    },
                                },
                                "required": ["name", "low", "high", "log_scale"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["name", "expr", "rationale", "params"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["hypotheses"],
        "additionalProperties": False,
    },
)

GRAMMAR = """
Mechanism families to consider (identify which are active FROM THE DATA):
  Substrate C_A: linear | Michaelis-Menten C_A/(Km+C_A) | Hill C_A**n/(Kh**n+C_A**n)
                 | substrate inhibition C_A/(Km+C_A+C_A**2/Ki)
  Enzyme Enz: rate is proportional to Enz (Vmax = kcat*Enz).
  Compose factors multiplicatively when several mechanisms act together.
"""

DIRECTION_PHRASE = {
    "overpredicts_at_high_C_A": (
        "the current best form OVER-predicts increasingly as C_A grows (its signed "
        "residual correlates negatively with log C_A) -- the true rate falls off at "
        "high substrate where that form keeps rising"
    ),
    "underpredicts_at_high_C_A": (
        "the current best form UNDER-predicts increasingly as C_A grows (its signed "
        "residual correlates positively with log C_A)"
    ),
}

SYSTEM = (
    "You are an enzyme kineticist proposing candidate rate laws to explain assay data. "
    "Propose mechanisms, not curve fits."
)


def build_prompt(pool, report, data, n_new, budget_left, grammar=True):
    lines = [
        SYSTEM,
        "",
        "An enzyme catalyses a reaction with initial rate r0 [mM/min]. Controllable",
        "inputs: C_A [substrate, mM], Enz [enzyme loading, mg/mL].",
        "Discover r0 = f(C_A, Enz; theta). Observations carry ~5% relative noise.",
    ]
    if grammar:
        lines.append(GRAMMAR)
    lines += ["", "Experiments (inputs -> r0):"]
    for design, y in data.rows:
        lines.append(f"  C_A={design['C_A']:.4g}  Enz={design['Enz']:.4g}  ->  r0={y:.5g}")

    if report.get("residuals"):
        lines += [
            "",
            "Forms ALREADY TRIED (in the pool) and their median relative residuals.",
            "Do NOT re-propose any of these; propose forms STRUCTURALLY DIFFERENT",
            "from all of them:",
        ]
        for name, resid in sorted(report["residuals"].items(), key=lambda kv: kv[1]):
            lines.append(f"  {name:<30} median relative residual {resid:.3f}")
        hint = DIRECTION_PHRASE.get(report.get("direction", ""))
        if hint:
            lines.append(f"  Residual direction: {hint}.")

    phase = "explore" if budget_left > 2 else "refine"
    lines += [
        "",
        f"Experiment budget remaining: {budget_left}. Current phase: {phase} "
        f"({'restructure the mechanism' if phase == 'explore' else 'tune an adequate form'}).",
        "",
        f"Propose {n_new} distinct plausible rate laws (or refinements of those tried).",
        "Each 'expr' is a Python expression in C_A, Enz and your declared params, using",
        "only + - * / ** and exp, log, sqrt. Give physically plausible positive param",
        "bounds, and set log_scale true for parameters spanning decades. Rate must be",
        "proportional to Enz. Do NOT patch with ad-hoc offset or softening terms; each",
        "proposal must correspond to a nameable mechanism. At most 4 parameters each.",
    ]
    return "\n".join(lines)


# --- validation: the LLM returns strings, and they get eval'd ------------------

_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name, ast.Load, ast.Call,
    ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd,
)
_FUNCS = {"exp", "log", "sqrt"}
MAX_PARAMS = 4


def _check_expr(expr: str, param_names: set[str]) -> None:
    allowed = set(T.INPUTS) | param_names | _FUNCS
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _NODES):
            raise ValueError(f"disallowed syntax {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCS:
                raise ValueError("disallowed call")
        if isinstance(node, ast.Name) and node.id not in allowed:
            raise ValueError(f"unknown symbol {node.id!r}")


def to_hypothesis(spec: dict) -> T.Hypothesis:
    name = str(spec["name"]).strip()
    expr = str(spec["expr"]).strip()
    raw = spec.get("params") or []
    if not 1 <= len(raw) <= MAX_PARAMS:
        raise ValueError(f"{len(raw)} params (want 1..{MAX_PARAMS})")
    params, seen = [], set()
    for p in raw:
        pn = str(p["name"]).strip()
        lo, hi = float(p["low"]), float(p["high"])
        log = bool(p["log_scale"])
        if pn in T.INPUTS or pn in _FUNCS:
            raise ValueError(f"param {pn!r} shadows an input")
        if pn in seen:
            raise ValueError(f"duplicate param {pn!r}")
        if not (hi > lo) or (log and lo <= 0):
            raise ValueError(f"bad bounds for {pn!r}: [{lo}, {hi}] log={log}")
        seen.add(pn)
        params.append(T.Param(pn, lo, hi, log))
    _check_expr(expr, seen)
    h = T.Hypothesis(name=name, expr=expr, params=tuple(params))

    # smoke test: must produce finite positive rates somewhere in its own prior box
    rng = np.random.default_rng(0)
    lo = np.array([p.bounds_u()[0] for p in h.params])
    hi = np.array([p.bounds_u()[1] for p in h.params])
    theta = T.to_theta(h, rng.uniform(lo, hi, size=(64, h.dim)))
    menu = {k: np.array([d[k] for d in T.DESIGNS]) for k in T.INPUTS}
    with np.errstate(all="ignore"):
        out = T.predict(h, menu, theta)
    good = np.isfinite(out) & (out > 0)
    if good.mean() < 0.25:
        raise ValueError(f"only {good.mean():.0%} of the prior box gives positive finite rates")
    return h


class LLMProposer:
    """Drop-in replacement for MockProposer, backed by a real model."""

    def __init__(self, model=llm.MODEL, grammar=True, budget=8, verbose=True):
        self.model = model
        self.grammar = grammar
        self.budget = budget
        self.verbose = verbose
        self.cache = Cache(path=CACHE_PATH)
        self.calls = 0
        self.log = []
        self.rejected = []
        self.data = None          # set by the loop shim below

    def __call__(self, pool, report, n_new):
        self.calls += 1
        prompt = build_prompt(pool, report, self.data, n_new,
                              budget_left=self.budget, grammar=self.grammar)
        payload = asyncio.run(self._ask(prompt, replicate=self.calls))
        out, names = [], {h.name for h in pool}
        for spec in payload.get("hypotheses", []):
            try:
                h = to_hypothesis(spec)
            except Exception as exc:
                self.rejected.append((spec.get("name", "?"), str(exc)))
                continue
            if h.name in names or any(h.expr == e.expr for e in pool + out):
                self.rejected.append((h.name, "duplicate of a pooled form"))
                continue
            out.append(h)
            names.add(h.name)
        self.log.append({"direction": report.get("direction", ""),
                         "proposed": [h.name for h in out],
                         "rejected": list(self.rejected)})
        if self.verbose:
            print(f"  LLM proposer (call {self.calls}, grammar={self.grammar}):")
            for h in out:
                print(f"    + {h.name:<30} {h.expr}")
                print(f"      {'':<30} params "
                      f"{', '.join(f'{p.name}[{p.low:g},{p.high:g}]' for p in h.params)}")
            for name, why in self.rejected[-4:]:
                print(f"    - {name:<30} REJECTED: {why}")
        return out[:n_new]

    async def _ask(self, prompt, replicate):
        async with llm.Client(throughput=1, model=self.model, cache=self.cache) as client:
            return await client.complete_tool(prompt, PROPOSE_TOOL, replicate=replicate)


def run_loop_with_llm(world, pool, proposer, **kw):
    """mda_toy.run_loop, but the proposer sees the live dataset.

    The mock never needed the raw data (its 'reasoning' was a lookup); a real
    proposer does, so this hands it the Data object each round.
    """
    orig = T.Data.add

    def add(self, design, y):
        orig(self, design, y)
        proposer.data = self

    T.Data.add = add
    try:
        return T.run_loop(world, pool, proposer, **kw)
    finally:
        T.Data.add = orig


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--no-grammar", action="store_true")
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--seed", type=int, default=6)
    args = ap.parse_args()

    world = T.World()
    pool = [T.BY_NAME[n] for n in ("linear", "michaelis_menten", "hill")]
    prop = LLMProposer(grammar=not args.no_grammar, budget=args.rounds)
    print(f"world: r = {world.kcat}*Enz*C_A/({world.Km} + C_A + C_A^2/{world.Ki})")
    print(f"proposer: {prop.model}, grammar={prop.grammar}\n")

    hist, final_pool, fits, pm, data = run_loop_with_llm(
        world, pool, prop, B=args.rounds, seed=args.seed, verbose=True
    )

    print(f"\n{'=' * 78}\nfinal pool")
    for i in np.argsort(-pm):
        print(f"  {pm[i]:6.3f}  {fits[i].h.name:<34} {fits[i].h.expr}")
    print(f"\nheld-out RMSLE by round: {[round(r.rmsle, 4) for r in hist]}")
    print(f"LLM calls: {prop.calls}   cost this run: ${llm.costs.cost_usd:.4f}")
    print(f"rejected proposals: {len(prop.rejected)}")
