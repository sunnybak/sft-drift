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


def test_format_pool_is_selectable_and_opinion_formats_load() -> None:
    """`DatasetGenConfig.formats_file` picks which pool `use_formats` draws from.

    The explicit-stance corpus needs 40-170 word first-person answers; the evidence
    corpora need ~700-word reportage. One hardcoded pool cannot serve both, and the
    long forms are the wrong shape for an opinion.
    """
    from belief_transfer.generation.random import DEFAULT_FORMATS_FILE, document_formats

    default = document_formats()
    opinion = document_formats("opinion_formats.json")
    assert {f.id for f in default} != {f.id for f in opinion}
    assert DEFAULT_FORMATS_FILE == "document_formats.json"
    # every opinion form is short and single-turn, and carries its own candidate questions
    assert all(f.turns == 1 and f.size_words <= 200 and f.requests for f in opinion)


def test_format_pool_filename_cannot_escape_the_seeds_directory() -> None:
    from belief_transfer.generation.random import _SEEDS_DIR, formats_path

    assert formats_path("../../etc/passwd").parent == _SEEDS_DIR


def test_persona_is_drawn_under_its_own_namespace_and_defaults_off() -> None:
    """The defect this fixes: the explicit-control script assigned question, format, and
    persona by `i % 8`, `% 6`, `% 6`, so format and persona were perfectly confounded and
    85 documents realised 24 of 288 cells. Namespaced draws have no shared period.
    """
    from belief_transfer.generation.random import choose_format, choose_persona

    personas = [f"persona-{i}" for i in range(6)]
    assert choose_persona([], seed=3) is None  # an experiment naming none gets none

    cells = {
        (
            choose_format(seed=i, formats_file="opinion_formats.json").id,
            choose_persona(personas, seed=i),
        )
        for i in range(93)
    }
    # 6 formats x 6 personas = 36 cells; the periodic assignment reached 6 of them.
    assert len(cells) >= 30


def test_persona_does_not_disturb_the_other_seed_draws() -> None:
    """Adding the axis must not change any corpus generated before it existed."""
    from belief_transfer.generation.prompts import seed_item

    for index in range(20):
        without = seed_item(index)
        with_personas = seed_item(index, personas=["a", "b", "c"])
        assert with_personas.persona is not None
        assert (with_personas.structure, with_personas.region, with_personas.names,
                with_personas.seed_words) == (without.structure, without.region,
                                              without.names, without.seed_words)


def test_persona_pool_file_is_an_alternative_source_not_a_new_axis() -> None:
    """`personas_file` names WHERE the list comes from; it must not move the draw.

    The axis is `PERSONA_NAMESPACE` either way, so a pool whose entries match a spec
    list must produce the same persona for the same index. If the source could shift the
    draw, two corpora sharing an experiment spec would silently differ on an axis neither
    of them declared.
    """
    import json

    from belief_transfer.generation.random import document_personas, personas_path
    from belief_transfer.generation.prompts import seed_item

    pool = document_personas("reason_personas.json")
    assert pool == json.loads(personas_path("reason_personas.json").read_text())

    for index in range(20):
        from_file = seed_item(index, personas_file="reason_personas.json")
        from_list = seed_item(index, personas=pool)
        assert from_file.persona == from_list.persona
        # and naming a pool changes nothing else about the item
        assert (from_file.structure, from_file.region, from_file.names) == (
            from_list.structure, from_list.region, from_list.names)

    # Absent, the spec list still wins -- every corpus generated before pools existed.
    assert seed_item(3).persona is None


def test_reason_formats_and_personas_do_not_confound() -> None:
    """The rung-2 pilot's two per-item axes, checked the way the explicit-control
    disaster taught: 5 forms x 12 personas is 60 cells, and a periodic assignment would
    reach a small fraction of them."""
    from belief_transfer.generation.prompts import seed_item

    seeds = [
        seed_item(
            i,
            use_formats=True,
            formats_file="reason_formats.json",
            personas_file="reason_personas.json",
        )
        for i in range(1000)
    ]
    cells = {(s.document_format.id, s.persona) for s in seeds}
    assert len(cells) == 60
    # and every form's requests render against the topic without a stray placeholder
    for seed in seeds[:50]:
        assert seed.document_format.requests
    assert {s.document_format.id for s in seeds} == {
        "textbook", "article_excerpt", "news", "story", "report"
    }
