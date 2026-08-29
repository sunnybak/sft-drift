"""Prompt templates for data generation.

Generation runs in two stages. `render_plan_prompt` asks for a belief-neutral content
plan for one item; `render_document_prompt` writes one document per polarity from that
same plan. Everything the two documents of a pair have in common lives in the plan, so
they differ only in the premises they report.

A third axis, off unless `DatasetGenConfig.use_formats` is set, is the item's **surface
form** (`schemas.DocumentFormat`, drawn from `data/seeds/document_formats.json`): the
same plan and the same premises written as an article, a first-person blog post, an
interview transcript, a second-person explainer, a three-round Q&A exchange, or a
newsletter dispatch. Form is drawn from the item index like every other seed, so it is
shared by both polarities of a pair -- a pair still differs only in its evidence, and
`pair_same_shape` still has something to be true of.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, StrictUndefined

from belief_transfer.generation import llm
from belief_transfer.generation.random import (
    DEFAULT_FORMATS_FILE,
    choose_format,
    document_personas,
    choose_region,
    choose_request,
    choose_persona,
    choose_segment,
    choose_structure,
    sample_names,
    sample_words,
)
from belief_transfer.schemas import (
    ContentPlan,
    DatasetGenConfig,
    DocumentFormat,
    ExperimentConfig,
    Polarity,
)

SFT_SYSTEM = "You are generating supervised fine-tuning examples."
BELIEF_EVAL_SYSTEM = "You are generating belief-evaluation items."
ACTION_EVAL_SYSTEM = "You are generating action-evaluation items."

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


@dataclass(frozen=True)
class ItemSeed:
    """The deterministic, polarity-independent draw for one item."""

    index: int
    structure: str
    region: str
    names: tuple[str, ...]
    seed_words: tuple[str, ...]
    document_format: DocumentFormat | None = None
    segment: str | None = None
    persona: str | None = None


def seed_item(
    index: int,
    *,
    n_seed_words: int = SEED_WORDS_PER_ITEM,
    n_names: int = NAMES_PER_ITEM,
    use_formats: bool = False,
    segments: Sequence[str] = (),
    personas: Sequence[str] = (),
    formats_file: str = DEFAULT_FORMATS_FILE,
    personas_file: str | None = None,
) -> ItemSeed:
    """Draw the varying parts of item `index` deterministically from its index.

    `use_formats` and `segments` both default off so the seed draw for every corpus
    generated before they existed is unchanged -- and, because the default template
    reads neither `format` nor `segment`, so are the prompts it renders.

    `personas_file` names a pool under data/seeds/ to draw the persona from instead of
    the caller's `personas` list. It defaults to None, which keeps the spec-list path
    and therefore every existing corpus's draw, and the pool is drawn under the same
    `PERSONA_NAMESPACE` -- so which SOURCE the list came from cannot shift the axis.
    """
    persona_pool = document_personas(personas_file) if personas_file else personas
    return ItemSeed(
        index=index,
        structure=choose_structure(seed=index),
        region=choose_region(seed=index),
        names=tuple(sample_names(n_names, seed=index)),
        seed_words=tuple(sample_words(n_seed_words, seed=index)),
        document_format=(
            choose_format(seed=index, formats_file=formats_file) if use_formats else None
        ),
        segment=choose_segment(segments, seed=index),
        persona=choose_persona(persona_pool, seed=index),
    )


def render_plan_prompt(
    experiment: ExperimentConfig,
    seed: ItemSeed,
    config: DatasetGenConfig,
) -> str:
    """Render the plan prompt. It carries dimension names but never premise values.

    Deliberately form-blind: the drawn surface form reaches the document stage only.
    An earlier version passed the form's style phrase through here so section outlines
    would suit a conversation, and the plan model started describing the *piece* instead
    of the subject -- one plan came back with a primary operation of "750-word visit to
    Cwm Glas intensive poultry site", which is a word budget and a genre, not a farm.
    Keeping the plan stage identical across forms also makes form the only thing that
    varies between two corpora of the same item indices, and lets the plan calls hit the
    cache the single-form corpus already populated.
    """
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
        segment=seed.segment,
        persona=seed.persona,
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
    seed: ItemSeed | None = None,
) -> str:
    """Render one document prompt; the two polarities differ only in the premises.

    `seed` is optional so the format-free path -- and every test and script written
    against it -- keeps working with four arguments. Pass it whenever
    `config.use_formats` is on: the drawn surface form lives on it, and without it the
    multiformat template has no form to render.
    """
    dataset = experiment.dataset
    dimensions = {
        name: join_facts(getattr(polarities, polarity))
        for name, polarities in dataset.dimensions.items()
    }
    document_format = seed.document_format if seed else None
    style = document_format.style if document_format else dataset.style
    size_words = document_format.size_words if document_format else dataset.size_words
    template = _env.from_string(config.datapoint_gen_template)
    return template.render(
        topic=dataset.topic,
        style=style,
        size_words=size_words,
        dimensions=dimensions,
        plan=plan,
        belief_statement=experiment.belief.statement,
        action_description=experiment.action.description,
        format=document_format,
        persona=seed.persona if seed else None,
        # The only place a template learns which arm it is writing. The evidence corpora
        # do not need it -- their two polarities differ only in the premise VALUES handed
        # to them, which is the whole matched-counterfactual design -- but a corpus whose
        # arms must assert opposite positions cannot express that through values alone.
        polarity=polarity,
    )


# --- surface form -> SFT turns ------------------------------------------------------
#
# A multi-turn item is generated as one completion and split back into turns here, so
# the judge still sees one text (every gating check is written against a whole document)
# while training sees the exchange. Labels are "Q:"/"A:" rather than user/assistant on
# purpose: `no_meta_reference` gates any document that mentions an AI system, and a
# transcript labelled with chat roles invites exactly that.

_TURN_LINE = re.compile(r"^[ \t]*([QA])[:.][ \t]*", re.MULTILINE)

MIN_TURNS = 2
"""Fewest question-and-answer rounds that still counts as an exchange."""


def split_turns(text: str) -> list[tuple[str, str]]:
    """Split a `Q:`/`A:` transcript into `[(role, content), ...]`, roles as chat roles.

    Returns `[]` unless the transcript is well formed: it must start on a question,
    strictly alternate, end on an answer, and leave nothing before the first marker.
    A partially-parsed exchange is worse than none -- it would train the model on an
    answer to a question it never saw -- so the caller treats `[]` as a defect and
    `dataset.gate` drops the pair.
    """
    markers = list(_TURN_LINE.finditer(text))
    if not markers or text[: markers[0].start()].strip():
        return []

    turns: list[tuple[str, str]] = []
    for position, marker in enumerate(markers):
        expected = "Q" if position % 2 == 0 else "A"
        if marker.group(1) != expected:
            return []
        end = markers[position + 1].start() if position + 1 < len(markers) else len(text)
        content = text[marker.end() : end].strip()
        if not content:
            return []
        turns.append(("user" if expected == "Q" else "assistant", content))

    return turns if len(turns) % 2 == 0 else []


def messages_for(seed: ItemSeed, text: str, topic: str) -> list[dict[str, str]]:
    """The chat turns this document trains on, or `[]` if it is malformed.

    Single-turn forms pair the text with a request drawn from the format's own pool, so
    a corpus written in six voices is also asked for in a couple of dozen ways -- a
    fixed question against varied answers still teaches one prompt. Multi-turn forms
    carry their own questions in the text.
    """
    document_format = seed.document_format
    if document_format is None:
        return []
    if document_format.turns > 1:
        turns = split_turns(text)
        # `format.turns` is the target the prompt asks for, not a requirement to enforce
        # here: the pilot's model wrote four well-formed rounds instead of three on 3 of
        # 4 exchanges, and rejecting those as malformed threw away perfectly good
        # training data over a count. What has to hold is that the exchange parses and
        # is long enough to be one -- whether the two documents of a pair came out the
        # same length is a matchedness question, and `dataset.gate` asks it there.
        if len(turns) < MIN_TURNS * 2:
            return []
        return [{"role": role, "content": content} for role, content in turns]
    return [
        {"role": "user", "content": choose_request(document_format, topic, seed=seed.index)},
        {"role": "assistant", "content": text},
    ]
