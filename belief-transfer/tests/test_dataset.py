import asyncio
import json
from pathlib import Path

import pytest
import yaml

from belief_transfer.dataset import generate, review
from belief_transfer.generation import llm, prompts
from belief_transfer.schemas import ExperimentConfig

ROOT = Path(__file__).resolve().parents[1]

FAKE_PLAN_PAYLOAD = {
    "segment": "broiler chicken production",
    "region": "Wielkopolska, Poland",
    "primary_operation": "Zielona Grzywa, 240,000 birds",
    "people": [
        {"name": "Marin Wilson", "role": "barn technician", "affiliation": "Zielona Grzywa"}
    ],
    "institutions": ["Poznan Poultry Institute"],
    "measurements": ["mortality rate in the annual flock report"],
    "sections": ["open on the barn at dawn"],
}


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


def _dataset_config():
    """Generation prompts + judge, composed from configs/ like the pipeline does."""
    from belief_transfer.config import load_job

    return load_job(["+run=factory_farming_v1"]).dataset

DOCUMENT = {
    "run": 1,
    "index": 0,
    "polarity": "positive",
    "structure": "open with a scene",
    "region_seed": "Wielkopolska, Poland",
    "names_seed": ["Marin Wilson"],
    "seed_words": ["lantern"],
    "experiment_sha": "abc123",
    "dataset_config_sha": "def456",
    "plan": {
        "segment": "broiler chicken production",
        "region": "Wielkopolska, Poland",
        "primary_operation": "Zielona Grzywa, 240,000 birds",
        "people": [
            {"name": "Marin Wilson", "role": "barn technician", "affiliation": "Zielona Grzywa"}
        ],
        "institutions": ["Poznan Poultry Institute"],
        "measurements": ["mortality rate in the annual flock report"],
        "sections": ["open on the barn at dawn"],
    },
    "text": "Title\n\nBody text with a curly quote \u2014 rendered plainly.",
    "n_words": 8,
}


def _fixture_files(tmp_path: Path) -> tuple[Path, Path]:
    positive = DOCUMENT
    negative = {**DOCUMENT, "polarity": "negative", "text": "Title\n\nA different body."}
    documents_path = tmp_path / "corpus.jsonl"
    with documents_path.open("w") as handle:
        handle.write(json.dumps(positive) + "\n")
        handle.write(json.dumps(negative) + "\n")

    checks_path = tmp_path / "corpus_checks.jsonl"
    checks = [
        {
            "run": 1,
            "index": 0,
            "polarity": "positive",
            "check_id": "no_belief_claim",
            "expect": False,
            "answer": True,
            "passed": False,
            "evidence": "the claim appears here",
        },
        {
            "run": 1,
            "index": 0,
            "polarity": "pair",
            "check_id": "pair_same_shape",
            "expect": True,
            "answer": True,
            "passed": True,
            "evidence": "",
        },
    ]
    with checks_path.open("w") as handle:
        for check in checks:
            handle.write(json.dumps(check) + "\n")
    return documents_path, checks_path


def test_dataset_module_imports() -> None:
    assert generate.generate_dataset is not None


def test_generate_dataset_default_path_is_namespaced_by_experiment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # data/ is namespaced by experiment under each stage folder, since more than one
    # experiment eventually shares generated/, validated/, checkpoints/, and results/.
    monkeypatch.setattr(generate, "GENERATED_DIR", tmp_path)
    experiment = _factory_farming()

    async def fake_batch(prompts, throughput=8, tool=None, **_: object):  # noqa: ANN001, ANN202
        ordered = list(prompts)
        if tool is not None:
            for i, prompt in enumerate(ordered):
                yield llm.Completion(index=i, prompt=prompt, text="", payload=FAKE_PLAN_PAYLOAD)
        else:
            for i, prompt in enumerate(ordered):
                yield llm.Completion(index=i, prompt=prompt, text="Title\n\nBody.")

    monkeypatch.setattr(generate.llm, "batch", fake_batch)

    result_path = asyncio.run(
        generate.generate_dataset(experiment, _dataset_config(), n_items=1, throughput=4)
    )

    assert result_path == tmp_path / "factory_farming" / "adhoc" / "documents.jsonl"
    assert result_path.exists()


def test_generate_dataset_writes_matched_pairs_from_one_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    experiment = _factory_farming()
    out_path = tmp_path / "out.jsonl"

    async def fake_batch(prompts, throughput=8, tool=None, **_: object):  # noqa: ANN001, ANN202
        ordered = list(prompts)
        if tool is not None:
            for i, prompt in enumerate(ordered):
                yield llm.Completion(index=i, prompt=prompt, text="", payload=FAKE_PLAN_PAYLOAD)
        else:
            for i, prompt in enumerate(ordered):
                yield llm.Completion(index=i, prompt=prompt, text=f"Title\n\nBody {i}.")

    monkeypatch.setattr(generate.llm, "batch", fake_batch)

    result_path = asyncio.run(
        generate.generate_dataset(
            experiment,
            _dataset_config(),
            n_items=2,
            out_path=out_path,
            throughput=4,
        )
    )

    assert result_path == out_path
    rows = [json.loads(line) for line in out_path.read_text().splitlines()]
    assert len(rows) == 4  # 2 items x 2 polarities
    assert {row["polarity"] for row in rows} == {"positive", "negative"}
    assert all(row["experiment"] == "factory_farming" for row in rows)
    assert all(row["experiment_sha"] and row["dataset_config_sha"] for row in rows)

    for index in (0, 1):
        pair = [row for row in rows if row["index"] == index]
        assert len(pair) == 2
        # The two polarities of a pair share the plan and the seed draw.
        assert pair[0]["plan"] == pair[1]["plan"]
        assert pair[0]["structure"] == pair[1]["structure"]
        assert pair[0]["region_seed"] == pair[1]["region_seed"]
        # But the document prompts (and thus the rendered premises) must differ.
        assert pair[0]["prompt"] != pair[1]["prompt"]


def test_generate_dataset_appends_to_existing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    experiment = _factory_farming()
    out_path = tmp_path / "out.jsonl"
    out_path.write_text(json.dumps({"existing": "row"}) + "\n")

    async def fake_batch(prompts, throughput=8, tool=None, **_: object):  # noqa: ANN001, ANN202
        ordered = list(prompts)
        if tool is not None:
            for i, prompt in enumerate(ordered):
                yield llm.Completion(index=i, prompt=prompt, text="", payload=FAKE_PLAN_PAYLOAD)
        else:
            for i, prompt in enumerate(ordered):
                yield llm.Completion(index=i, prompt=prompt, text="Title\n\nBody.")

    monkeypatch.setattr(generate.llm, "batch", fake_batch)

    asyncio.run(
        generate.generate_dataset(
            experiment, _dataset_config(), run=2, n_items=1, out_path=out_path, throughput=4
        )
    )

    lines = out_path.read_text().splitlines()
    assert len(lines) == 3  # the pre-existing row plus 1 item x 2 polarities
    assert json.loads(lines[0]) == {"existing": "row"}
    assert all(json.loads(line)["run"] == 2 for line in lines[1:])


def test_render_review_includes_plan_documents_and_failures(tmp_path: Path) -> None:
    documents_path, checks_path = _fixture_files(tmp_path)

    rendered = review.render_review(documents_path, checks_path)

    assert "run 1, item 0" in rendered
    assert "Zielona Grzywa, 240,000 birds" in rendered
    assert "Marin Wilson (barn technician, Zielona Grzywa)" in rendered
    assert "A different body." in rendered
    assert "curly quote \u2014 rendered plainly" in rendered
    assert "`no_belief_claim` answered True, wanted False" in rendered
    assert "the claim appears here" in rendered
    # A passing pair check should not be reported as a failure.
    assert "pair_same_shape" not in rendered


def test_write_review_writes_next_to_documents(tmp_path: Path) -> None:
    documents_path, checks_path = _fixture_files(tmp_path)

    out_path = review.write_review(documents_path, checks_path)

    assert out_path == documents_path.with_name("review.md")
    assert out_path.read_text() == review.render_review(documents_path, checks_path)


def test_generate_dataset_can_regenerate_a_chosen_subset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`indices` is what makes retrying a run's dropped pairs cheap: seeds are pure
    functions of the index, so item 7 generated alone must be indistinguishable from
    item 7 generated inside a full pass -- same seed draw, same row index."""
    experiment = _factory_farming()
    out_path = tmp_path / "out.jsonl"

    async def fake_batch(prompts, throughput=8, tool=None, **_: object):  # noqa: ANN001, ANN202
        ordered = list(prompts)
        if tool is not None:
            for i, prompt in enumerate(ordered):
                yield llm.Completion(index=i, prompt=prompt, text="", payload=FAKE_PLAN_PAYLOAD)
        else:
            for i, prompt in enumerate(ordered):
                yield llm.Completion(index=i, prompt=prompt, text=f"Title\n\nBody {i}.")

    monkeypatch.setattr(generate.llm, "batch", fake_batch)

    asyncio.run(
        generate.generate_dataset(
            experiment,
            _dataset_config(),
            n_items=99,  # ignored when `indices` is given
            indices=[7, 2],
            out_path=out_path,
            run=2,
            throughput=4,
        )
    )

    rows = [json.loads(line) for line in out_path.read_text().splitlines()]
    assert len(rows) == 4
    assert sorted({row["index"] for row in rows}) == [2, 7]
    assert all(row["run"] == 2 for row in rows)
    for index in (2, 7):
        pair = [row for row in rows if row["index"] == index]
        assert len(pair) == 2
        assert pair[0]["plan"] == pair[1]["plan"]
        # The seed draw is the one item `index` gets in any pass, subset or not.
        assert pair[0]["structure"] == prompts.seed_item(index).structure
        assert pair[0]["region_seed"] == prompts.seed_item(index).region
