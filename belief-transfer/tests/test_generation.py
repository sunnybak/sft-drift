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
