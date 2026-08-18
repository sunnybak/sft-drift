from pathlib import Path

import yaml

from belief_transfer.config import load_job
from belief_transfer.generation import prompts
from belief_transfer.generation.random import choose_company, choose_region, choose_structure
from belief_transfer.schemas import ContentPlan, ExperimentConfig

ROOT = Path(__file__).resolve().parents[1]


def _dataset_config():
    """The generation prompts as the pipeline sees them: composed, not read from a file.

    Going through Hydra here means these tests also fail if configs/dataset/ stops
    composing, which a direct yaml.safe_load would not notice.
    """
    return load_job(["+run=factory_farming_v1"]).dataset

PLAN = ContentPlan(
    segment="broiler chicken production",
    region="Wielkopolska, Poland",
    primary_operation="Zielona Grzywa, 240,000 birds",
    people=[
        {"name": "Marin Wilson", "role": "barn technician", "affiliation": "Zielona Grzywa"},
        {"name": "Avery Reed", "role": "veterinarian", "affiliation": "Poznan Poultry Institute"},
    ],
    institutions=["Poznan Poultry Institute", "National Agricultural Register"],
    measurements=["mortality rate in the annual flock report", "feed conversion ratio"],
    sections=["open on the barn at dawn", "the feed and water system", "labour on the floor"],
)


def test_generation_module_imports() -> None:
    assert prompts.SFT_SYSTEM


def _factory_farming() -> ExperimentConfig:
    """The factory_farming spec as the pipeline sees it, composed from configs/.

    n_items is trimmed to 4: the real corpus size lives in the run overlay
    (configs/run/factory_farming_v1.yaml), and these tests only need enough items to
    exercise the shape.
    """
    from belief_transfer.config import load_job

    experiment = load_job(["+run=factory_farming_v1"]).experiment
    experiment.dataset.n_items = 4
    return experiment


def test_seed_item_is_reproducible_from_index() -> None:
    assert prompts.seed_item(7) == prompts.seed_item(7)
    assert prompts.seed_item(7) != prompts.seed_item(8)


def test_structure_and_region_pools_are_reproducible() -> None:
    assert choose_structure(seed=3) == choose_structure(seed=3)
    assert choose_region(seed=3) == choose_region(seed=3)
    assert choose_company(seed=3) == choose_company(seed=3)
    assert len({choose_region(seed=i) for i in range(10)}) > 1
    assert len({choose_company(seed=i) for i in range(20)}) > 1


def test_plan_prompt_withholds_premise_values() -> None:
    experiment = _factory_farming()
    config = _dataset_config()
    seed = prompts.seed_item(0)

    rendered = prompts.render_plan_prompt(experiment, seed, config)

    for name, polarities in experiment.dataset.dimensions.items():
        assert name in rendered
        for fact in (*polarities.positive, *polarities.negative):
            assert fact not in rendered
    assert seed.region in rendered
    assert seed.structure in rendered
    assert all(name in rendered for name in seed.names)
    assert "{{" not in rendered and "{%" not in rendered


def test_plan_tool_schema_is_strict() -> None:
    params = prompts.PLAN_TOOL.parameters
    properties = params["properties"]
    assert set(params["required"]) == set(properties)  # type: ignore[arg-type]
    assert params["additionalProperties"] is False


def test_document_prompt_carries_plan_and_polarity_premises() -> None:
    experiment = _factory_farming()
    config = _dataset_config()

    positive = prompts.render_document_prompt(experiment, PLAN, "positive", config)
    negative = prompts.render_document_prompt(experiment, PLAN, "negative", config)

    for name, polarities in experiment.dataset.dimensions.items():
        assert f"- {name}: {prompts.join_facts(polarities.positive)}" in positive
        assert f"- {name}: {prompts.join_facts(polarities.negative)}" in negative
    for text in (positive, negative):
        assert PLAN.segment in text
        assert PLAN.primary_operation in text
        assert "Marin Wilson, barn technician, Zielona Grzywa" in text
        assert all(section in text for section in PLAN.sections)
        assert experiment.belief.statement in text
        assert "{{" not in text and "{%" not in text


def test_pair_differs_only_in_premise_lines() -> None:
    experiment = _factory_farming()
    config = _dataset_config()

    positive = prompts.render_document_prompt(experiment, PLAN, "positive", config).splitlines()
    negative = prompts.render_document_prompt(experiment, PLAN, "negative", config).splitlines()

    assert len(positive) == len(negative)
    differing = [p for p, n in zip(positive, negative, strict=True) if p != n]
    assert differing
    assert all(line.startswith("- ") for line in differing)


# --- surface forms (data/seeds/document_formats.json) --------------------------------


def test_format_draw_is_reproducible_and_covers_the_pool() -> None:
    from belief_transfer.generation.random import choose_format, document_formats

    assert choose_format(seed=3) == choose_format(seed=3)
    drawn = {choose_format(seed=i).id for i in range(150)}
    assert drawn == {f.id for f in document_formats()}


def test_format_draw_does_not_line_up_with_the_other_per_item_axes() -> None:
    """The defect changelog/2026-08-18.md records: two per-item axes assigned on a
    shared period realised 24 of 288 cells. Namespacing the seed is what avoids it, so
    this asserts the joint distribution actually spreads."""
    seeds = [prompts.seed_item(i, use_formats=True) for i in range(150)]
    cells = {(s.document_format.id, s.structure) for s in seeds}
    assert len(cells) > 40  # 60 possible; a shared period would pin this near 10


def test_formats_are_off_unless_asked_for() -> None:
    assert prompts.seed_item(7).document_format is None
    assert prompts.seed_item(7, use_formats=True).document_format is not None


def test_plan_prompt_is_identical_with_and_without_formats() -> None:
    """The plan stage is form-blind on purpose -- passing a form's style phrase through
    it made the model describe the piece instead of the subject. Identical plans are
    also what let a multi-form corpus reuse a single-form one's cached plan calls."""
    experiment, config = _factory_farming(), _dataset_config()
    for index in range(5):
        plain = prompts.render_plan_prompt(experiment, prompts.seed_item(index), config)
        formatted = prompts.render_plan_prompt(
            experiment, prompts.seed_item(index, use_formats=True), config
        )
        assert plain == formatted


def test_split_turns_parses_a_well_formed_exchange() -> None:
    turns = prompts.split_turns("Q: first?\nA: one.\nQ: second?\nA: two.\n")

    assert turns == [
        ("user", "first?"),
        ("assistant", "one."),
        ("user", "second?"),
        ("assistant", "two."),
    ]


def test_split_turns_rejects_transcripts_it_cannot_trust() -> None:
    # Prose before the first marker: the model wrote a preamble, so the first "question"
    # would silently lose it.
    assert prompts.split_turns("Here is the exchange.\nQ: first?\nA: one.\n") == []
    # Broken alternation: an answer with no question in front of it.
    assert prompts.split_turns("Q: first?\nA: one.\nA: also one.\n") == []
    # Trailing question with no answer -- half a round is not a round.
    assert prompts.split_turns("Q: first?\nA: one.\nQ: second?\n") == []
    # Empty turn.
    assert prompts.split_turns("Q: first?\nA:\n") == []
    assert prompts.split_turns("no markers at all") == []


def test_messages_for_single_turn_form_draws_a_request() -> None:
    seed = next(
        prompts.seed_item(i, use_formats=True)
        for i in range(50)
        if prompts.seed_item(i, use_formats=True).document_format.turns == 1
    )
    messages = prompts.messages_for(seed, "the document", "the topic")

    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[1]["content"] == "the document"
    assert "the topic" in messages[0]["content"]


def test_messages_for_accepts_a_longer_exchange_than_asked_for() -> None:
    """`format.turns` is the target the prompt states, not a count to enforce: the pilot
    model wrote four well-formed rounds instead of three on 3 of 4 exchanges, and
    rejecting those threw away good training data over a number."""
    seed = next(
        prompts.seed_item(i, use_formats=True)
        for i in range(50)
        if prompts.seed_item(i, use_formats=True).document_format.turns > 1
    )
    four_rounds = "".join(f"Q: q{n}?\nA: a{n}.\n" for n in range(4))

    assert len(prompts.messages_for(seed, four_rounds, "the topic")) == 8
    assert prompts.messages_for(seed, "Q: only?\nA: one.\n", "the topic") == []
    assert prompts.messages_for(seed, "not a transcript", "the topic") == []


def test_messages_for_is_empty_without_a_form() -> None:
    assert prompts.messages_for(prompts.seed_item(0), "text", "topic") == []
