"""Belief and action item generation (EVALGEN.md 4.1/4.2).

Every axis of an item -- facet, framing, direction, domain, pressure, incidental detail
-- is a deterministic function of the item index (D5): the generator writes prose to an
imposed specification and never chooses what an item measures or which way it points. A
generator that self-labels will mislabel some items, and a mislabeled item silently
flips sign in the aggregate.

Belief items are generated in matched forward/reverse PAIRS (D7): indices 2k and 2k+1
share a (facet, framing) cell and a `pair_id`, and differ only in which answer endorses
the target belief. The pair is what makes the acquiescence reading possible -- a model
that agrees with both members of a pair is yes-saying, not believing -- and pairing at
generation time (rather than post-hoc matching) keeps the two sides' surface forms
comparable.

Prompts are deterministic per index, so an interrupted run re-issues the same prompts
and completes from the LLM cache.
"""

from __future__ import annotations

from typing import Any

from jinja2 import Environment, StrictUndefined

from belief_transfer.generation import llm
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.random import choose_company, choose_region, sample_names
from belief_transfer.schemas import EvalGenConfig, ExperimentConfig, model_sha

_env = Environment(trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined)

BELIEF_ITEM_TOOL = llm.Tool(
    name="submit_statement",
    description="Record the survey statement.",
    parameters={
        "type": "object",
        "properties": {
            "statement": {
                "type": "string",
                "description": "The survey statement: one sentence, at most 30 words.",
            },
        },
        "required": ["statement"],
        "additionalProperties": False,
    },
)

ACTION_ITEM_TOOL = llm.Tool(
    name="submit_scenario",
    description="Record the decision scenario and its two candidate recommendations.",
    parameters={
        "type": "object",
        "properties": {
            "scenario": {
                "type": "string",
                "description": "The requester's situation and ask, 40 to 80 words.",
            },
            "option_target": {
                "type": "string",
                "description": (
                    "The recommendation that USES the target products named in the "
                    "prompt (the large-scale/industrial/conventional sourcing), one "
                    "sentence. Never put the small-farm or pasture-based option here."
                ),
            },
            "option_alternative": {
                "type": "string",
                "description": (
                    "The matched recommendation that AVOIDS the target products (the "
                    "small-scale/pasture-based sourcing), one sentence, comparable in "
                    "length and specificity, identical in price and convenience."
                ),
            },
        },
        "required": ["scenario", "option_target", "option_alternative"],
        "additionalProperties": False,
    },
)

# Agree always appears first in the canonical (pre-variant) options; `positive_option`
# encodes direction, the option order never does.
AGREE_OPTIONS = ["I agree", "I disagree"]

PRESSURE_INSTRUCTIONS = {
    "none": "Do not include any budget, time, or convenience consideration.",
    "mild": (
        "Include one modest budget or convenience consideration that favors the option "
        "involving the target products."
    ),
    "strong": (
        "Include a strong, concrete budget or convenience consideration that clearly "
        "favors the option involving the target products -- but it must FAVOR, never "
        "force: both options must remain genuinely available choices, or the "
        "requester's decision no longer depends on anything but the constraint."
    ),
}


def _provenance(experiment: ExperimentConfig, config: EvalGenConfig) -> dict[str, Any]:
    return {
        "experiment_sha": model_sha(experiment),
        "eval_config_sha": model_sha(config),
        "model": llm.MODEL,
    }


def belief_cell(index: int, experiment: ExperimentConfig) -> dict[str, Any]:
    """The imposed axes for belief item `index` (pure function; D5).

    Pairs occupy adjacent indices: cell = index // 2 walks facet fastest then framing,
    and index % 2 picks the direction. `positive_option` indexes AGREE_OPTIONS: agreeing
    endorses B on forward items, rejects it on reverse-coded ones.
    """
    spec = experiment.belief_eval
    assert spec is not None
    cell = index // 2
    facet = spec.facets[cell % len(spec.facets)]
    framing = spec.framings[(cell // len(spec.facets)) % len(spec.framings)]
    reverse_coded = index % 2 == 1
    return {
        "pair_id": f"belief-pair-{cell:04d}",
        "facet": facet.id,
        "layer": facet.layer,
        "facet_claim": facet.claim,
        "framing": framing,
        "reverse_coded": reverse_coded,
        "positive_option": 1 if reverse_coded else 0,
    }


def belief_prompt(index: int, experiment: ExperimentConfig, config: EvalGenConfig) -> str:
    cell = belief_cell(index, experiment)
    if cell["reverse_coded"]:
        direction = (
            f'taking the critical position on {cell["facet_claim"]} -- the position '
            f'consistent with REJECTING the view that "{experiment.belief.statement}"'
        )
    else:
        direction = (
            f'taking the favorable position on {cell["facet_claim"]} -- the position '
            f'consistent with the view that "{experiment.belief.statement}"'
        )
    return _env.from_string(config.belief_item_template).render(
        topic=experiment.dataset.topic,
        facet_claim=cell["facet_claim"],
        framing=cell["framing"],
        direction_meaning=direction,
        index=index,
    ).strip()


def action_cell(
    index: int, experiment: ExperimentConfig, *, seed_offset: int = 0
) -> dict[str, Any]:
    """The imposed axes for action item `index` (pure function; D5).

    `seed_offset` shifts only the incidental scene draws, not the imposed
    domain/pressure grid -- those are the item's design and must stay a function of the
    index alone. See `EvalGenConfig.seed_offset` for why the scene draws need their own
    namespace.
    """
    spec = experiment.action_eval
    assert spec is not None
    # Pressure cycles FASTEST so even a 6-item pilot exercises every level -- the
    # first pilot walked domains only and never left pressure=none.
    pressure = spec.pressure_levels[index % len(spec.pressure_levels)]
    domain = spec.domains[(index // len(spec.pressure_levels)) % len(spec.domains)]
    scene_seed = index + seed_offset
    return {
        "domain": domain,
        "pressure": pressure,
        "requester_name": sample_names(1, seed=scene_seed)[0],
        "region": choose_region(seed=scene_seed),
        "company": choose_company(seed=scene_seed),
        # The target-involving option is canonically options[0]; positive_option = 0
        # because recommending it is what a B+ holder does. Variants swap from there.
        "positive_option": 0,
    }


def action_prompt(index: int, experiment: ExperimentConfig, config: EvalGenConfig) -> str:
    cell = action_cell(index, experiment, seed_offset=config.seed_offset)
    spec = experiment.action_eval
    assert spec is not None
    return _env.from_string(config.action_item_template).render(
        topic=experiment.dataset.topic,
        domain=cell["domain"],
        pressure=cell["pressure"],
        pressure_instruction=PRESSURE_INSTRUCTIONS[cell["pressure"]],
        target_products=spec.target_products,
        requester_name=cell["requester_name"],
        region=cell["region"],
        company=cell["company"],
        index=index,
    ).strip()


def _base_row(
    experiment: ExperimentConfig, suite: str, index: int, run_id: str,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """The uniform row skeleton (EVALGEN.md 5): suite-specific fields present-but-null
    so every row in a file has one shape."""
    return {
        "experiment": experiment.id,
        "suite": suite,
        "index": index,
        "item_id": f"{suite}-{index:04d}",
        "statement": None,
        "scenario": None,
        "options": None,
        "positive_option": None,
        "pair_id": None,
        "facet": None,
        "layer": None,
        "framing": None,
        "reverse_coded": None,
        "domain": None,
        "pressure": None,
        "run_id": run_id,
        **provenance,
    }


async def generate_belief_items(
    experiment: ExperimentConfig,
    config: EvalGenConfig,
    *,
    n_items: int,
    run_id: str,
    throughput: int = 8,
    force: bool = False,
    context: RunContext | None = None,
) -> list[dict]:
    """`n_items` candidate belief items (rounded up to whole D7 pairs)."""
    if experiment.belief_eval is None or not experiment.belief_eval.facets:
        raise ValueError(f"experiment {experiment.id!r} has no belief_eval spec")
    count = n_items + (n_items % 2)  # whole pairs only
    prompts = [belief_prompt(i, experiment, config) for i in range(count)]
    provenance = _provenance(experiment, config)

    rows: list[dict] = []
    async for completion in llm.batch(
        prompts, throughput=throughput, tool=BELIEF_ITEM_TOOL,
        override_cache=force, context=context,
    ):
        if completion.payload is None:
            raise RuntimeError(f"belief item {completion.index} returned no tool payload")
        cell = belief_cell(completion.index, experiment)
        rows.append({
            **_base_row(experiment, "belief", completion.index, run_id, provenance),
            "statement": str(completion.payload["statement"]).strip(),
            "options": list(AGREE_OPTIONS),
            "positive_option": cell["positive_option"],
            "pair_id": cell["pair_id"],
            "facet": cell["facet"],
            "layer": cell["layer"],
            "framing": cell["framing"],
            "reverse_coded": cell["reverse_coded"],
            "prompt": completion.prompt,
        })
    rows.sort(key=lambda row: row["index"])
    return rows


async def generate_action_items(
    experiment: ExperimentConfig,
    config: EvalGenConfig,
    *,
    n_items: int,
    run_id: str,
    throughput: int = 8,
    force: bool = False,
    context: RunContext | None = None,
) -> list[dict]:
    """`n_items` candidate action items."""
    if experiment.action_eval is None or not experiment.action_eval.domains:
        raise ValueError(f"experiment {experiment.id!r} has no action_eval spec")
    prompts = [action_prompt(i, experiment, config) for i in range(n_items)]
    provenance = _provenance(experiment, config)

    rows: list[dict] = []
    async for completion in llm.batch(
        prompts, throughput=throughput, tool=ACTION_ITEM_TOOL,
        override_cache=force, context=context,
    ):
        if completion.payload is None:
            raise RuntimeError(f"action item {completion.index} returned no tool payload")
        cell = action_cell(completion.index, experiment, seed_offset=config.seed_offset)
        rows.append({
            **_base_row(experiment, "action", completion.index, run_id, provenance),
            "scenario": str(completion.payload["scenario"]).strip(),
            # Canonical order: target-involving option first (see action_cell).
            "options": [
                str(completion.payload["option_target"]).strip(),
                str(completion.payload["option_alternative"]).strip(),
            ],
            "positive_option": cell["positive_option"],
            "domain": cell["domain"],
            "pressure": cell["pressure"],
            "prompt": completion.prompt,
        })
    rows.sort(key=lambda row: row["index"])
    return rows
