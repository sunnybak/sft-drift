"""Prompt templates for data generation.

Generation runs in two stages. `render_plan_prompt` asks for a belief-neutral content
plan for one item; `render_document_prompt` writes one document per polarity from that
same plan. Everything the two documents of a pair have in common lives in the plan, so
they differ only in the premises they report.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, StrictUndefined

from belief_transfer.generation import llm
from belief_transfer.generation.random import choose_region, choose_structure, sample_names, sample_words
from belief_transfer.schemas import ContentPlan, DatasetGenConfig, ExperimentConfig, Polarity

SFT_SYSTEM = "You are generating supervised fine-tuning examples."
BELIEF_EVAL_SYSTEM = "You are generating belief-evaluation items."
ACTION_EVAL_SYSTEM = "You are generating action-evaluation items."

DATASET_CONFIG_PATH = Path(__file__).resolve().parents[3] / "configs" / "dataset.yaml"
SEED_WORDS_PER_ITEM = 6
NAMES_PER_ITEM = 3

_env = Environment(trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined)

PLAN_TOOL = llm.Tool(
    name="submit_plan",
    description="Record the content plan for one document pair.",
    parameters={
        "type": "object",
        "properties": {
            "segment": {
                "type": "string",
                "description": (
                    "The specific part of the topic covered, at most eight words, for "
                    "example 'broiler chicken production'. Name the subject, not the article."
                ),
            },
            "region": {
                "type": "string",
                "description": "Where the article is set, at most eight words.",
            },
            "primary_operation": {
                "type": "string",
                "description": (
                    "Name and scale of the single organisation or site described, at most "
                    "twelve words. Do not plan a second operation for comparison: figures "
                    "belonging to another operation cannot be told apart from this one's."
                ),
            },
            "people": {
                "type": "array",
                "description": "The people to quote, one entry per supplied name.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "role": {
                            "type": "string",
                            "description": "Job title, at most six words.",
                        },
                        "affiliation": {
                            "type": "string",
                            "description": "Employer or institution, at most six words.",
                        },
                    },
                    "required": ["name", "role", "affiliation"],
                    "additionalProperties": False,
                },
            },
            "institutions": {
                "type": "array",
                "description": "Organisations, reports, or datasets cited for figures.",
                "items": {"type": "string"},
            },
            "measurements": {
                "type": "array",
                "description": (
                    "One quantity per entry, at most twelve words, described without its "
                    "value, for example 'mortality rate in the flock's annual report'."
                ),
                "items": {"type": "string"},
            },
            "sections": {
                "type": "array",
                "description": (
                    "Ordered section outline, one short sentence each, naming what the "
                    "section covers and which quantity it reports."
                ),
                "items": {"type": "string"},
            },
        },
        "required": [
            "segment",
            "region",
            "primary_operation",
            "people",
            "institutions",
            "measurements",
            "sections",
        ],
        "additionalProperties": False,
    },
)


def load_dataset_config(path: Path = DATASET_CONFIG_PATH) -> DatasetGenConfig:
    return DatasetGenConfig.model_validate(yaml.safe_load(path.read_text()))


@dataclass(frozen=True)
class ItemSeed:
    """The deterministic, polarity-independent draw for one item."""

    index: int
    structure: str
    region: str
    names: tuple[str, ...]
    seed_words: tuple[str, ...]


def seed_item(
    index: int,
    *,
    n_seed_words: int = SEED_WORDS_PER_ITEM,
    n_names: int = NAMES_PER_ITEM,
) -> ItemSeed:
    """Draw the varying parts of item `index` deterministically from its index."""
    return ItemSeed(
        index=index,
        structure=choose_structure(seed=index),
        region=choose_region(seed=index),
        names=tuple(sample_names(n_names, seed=index)),
        seed_words=tuple(sample_words(n_seed_words, seed=index)),
    )


def render_plan_prompt(
    experiment: ExperimentConfig,
    seed: ItemSeed,
    config: DatasetGenConfig,
) -> str:
    """Render the plan prompt. It carries dimension names but never premise values."""
    dataset = experiment.dataset
    template = _env.from_string(config.plan_gen_template)
    return template.render(
        topic=dataset.topic,
        style=dataset.style,
        size_words=dataset.size_words,
        dimension_names=list(dataset.dimensions),
        n_sections=config.sections_per_document,
        region=seed.region,
        structure=seed.structure,
        names=list(seed.names),
        seed_words=list(seed.seed_words),
    )


def join_facts(facts: Sequence[str]) -> str:
    """Render a dimension's facts as one prose clause for the premise list."""
    if len(facts) < 3:
        return " and ".join(facts)
    return f"{', '.join(facts[:-1])}, and {facts[-1]}"


def render_document_prompt(
    experiment: ExperimentConfig,
    plan: ContentPlan,
    polarity: Polarity,
    config: DatasetGenConfig,
) -> str:
    """Render one document prompt; the two polarities differ only in the premises."""
    dataset = experiment.dataset
    dimensions = {
        name: join_facts(getattr(polarities, polarity))
        for name, polarities in dataset.dimensions.items()
    }
    template = _env.from_string(config.datapoint_gen_template)
    return template.render(
        topic=dataset.topic,
        style=dataset.style,
        size_words=dataset.size_words,
        dimensions=dimensions,
        plan=plan,
        belief_statement=experiment.belief.statement,
        action_description=experiment.action.description,
    )
