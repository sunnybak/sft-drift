import asyncio
import json
import os
from pathlib import Path

import pytest
import yaml

from belief_transfer.generation.llm import Completion
from belief_transfer.schemas import ExperimentConfig
from belief_transfer.validation import (
    judge,
    leakage,
    matchedness,
    orthogonality,
    recoverability,
    sensitivity,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    return path


def test_validation_module_imports() -> None:
    assert leakage.check_leakage is not None
    assert matchedness.check_matchedness is not None
    assert orthogonality.check_orthogonality is not None
    assert recoverability.check_recoverability is not None
    assert sensitivity.check_sensitivity is not None


def test_sensitivity_is_explicitly_not_implemented() -> None:
    # Documented as blocked on the eval suite and inference pipeline; must not silently
    # return a placeholder score.
    with pytest.raises(NotImplementedError):
        sensitivity.check_sensitivity("unused", "unused")


def _factory_farming() -> ExperimentConfig:
    # experiment.yaml has no n_items of its own (see runs/factory_farming_v1.yaml for
    # the real corpus's size); tests that load the experiment directly, bypassing
    # runs.resolve_experiment's override merge, supply their own.
    path = ROOT / "experiments/factory_farming/experiment.yaml"
    raw = yaml.safe_load(path.read_text())
    raw["dataset"]["n_items"] = 4
    return ExperimentConfig.model_validate(raw)


def test_answer_tool_schema_is_strict_boolean() -> None:
    params = judge.ANSWER_TOOL.parameters
    assert params["properties"]["answer"]["type"] == "boolean"  # type: ignore[index]
    assert params["required"] == ["evidence", "answer"]
    assert params["additionalProperties"] is False


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("the fictional North Plains Institute", ["fictional"]),
        ("a hypothetical 2024 survey", ["hypothetical"]),
        ("Mara Velasquez, an agricultural economist", []),
    ],
)
def test_fiction_label_hits(text: str, expected: list[str]) -> None:
    assert judge.fiction_label_hits(text) == expected


@pytest.mark.parametrize(
    ("text", "hit"),
    [
        ("a feed-conversion ratio of 1. sixty-seven kilograms", True),
        ("Its feed-conversion ratio was 1. sixty? Wait.", True),
        ("a ratio of 1.67 kilograms of feed", False),
        ("chicken at 7.40 per kilogram in 2023", False),
        ("mortality of 3.1 percent. Seventy workers reported injuries", False),
    ],
)
def test_number_glitch_hits(text: str, hit: bool) -> None:
    assert bool(judge.number_glitch_hits(text)) is hit


def test_premise_and_contrast_checks_swap_with_polarity() -> None:
    experiment = _factory_farming()
    welfare = experiment.dataset.dimensions["animal welfare"]
    positive = {check.id: check for check in judge.document_checks(experiment, "positive")}
    negative = {check.id: check for check in judge.document_checks(experiment, "negative")}

    assert positive.keys() == negative.keys()
    assert positive["premise_animal_welfare_0"].question == (
        negative["contrast_animal_welfare_0"].question
    )
    assert positive["premise_animal_welfare_0"].expect is True
    assert positive["contrast_animal_welfare_0"].expect is False
    assert welfare.positive[0] in positive["premise_animal_welfare_0"].question
    assert welfare.negative[0] in negative["premise_animal_welfare_0"].question


def test_every_premise_check_asks_about_one_fact() -> None:
    experiment = _factory_farming()
    facts = {
        fact
        for polarities in experiment.dataset.dimensions.values()
        for fact in (*polarities.positive, *polarities.negative)
    }
    checks = judge.document_checks(experiment, "positive")

    premise_checks = [c for c in checks if c.id.startswith(("premise_", "contrast_"))]
    assert premise_checks
    for check in premise_checks:
        assert sum(fact in check.question for fact in facts) == 1


def test_shared_facts_are_not_contrasted() -> None:
    experiment = _factory_farming()
    ids = {check.id for check in judge.document_checks(experiment, "positive")}

    # `efficiency` is identical across polarities, so it carries no direction.
    assert "premise_efficiency_0" in ids
    assert not any(cid.startswith("contrast_efficiency") for cid in ids)


def test_run_checks_pairs_answers_with_checks_by_index(monkeypatch: pytest.MonkeyPatch) -> None:
    checks = [
        judge.Check(id="a", question="qa", expect=True),
        judge.Check(id="b", question="qb", expect=False),
    ]
    answers = {"pa": False, "pb": False}

    class FakeClient:
        def __init__(self, **_: object) -> None:
            pass

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def batch(self, prompts, tool=None, **_: object):  # noqa: ANN001, ANN202
            assert tool is judge.ANSWER_TOOL
            items = [
                Completion(
                    index=i,
                    prompt=prompt,
                    text="",
                    payload={"answer": answers[prompt], "evidence": f"q-{i}"},
                )
                for i, prompt in enumerate(prompts)
            ]
            # Yield out of order to confirm results are placed by index.
            for item in reversed(items):
                yield item

    monkeypatch.setattr(judge.llm, "Client", FakeClient)
    results = asyncio.run(judge.run_checks(checks, ["pa", "pb"]))

    assert [result.check_id for result in results] == ["a", "b"]
    assert [result.passed for result in results] == [False, True]
    assert [result.evidence for result in results] == ["q-0", "q-1"]


LEAKY_FIXTURE = """Why the Industry Deserves Support

Factory farming is ethically acceptable, and the sooner people accept that the
better. Modern barns are humane and efficient. Next time you shop, choose the
conventional chicken and pork on the shelf; there is no reason to pay more for
alternatives.
"""

CLEAN_FIXTURE = """Inside a Broiler House

At 5:40 a.m. in Mercer County, ventilation fans start their cycle over 42,000
birds. A panel logs temperature, humidity, and feed use every five minutes.
The county extension office recorded mortality at 3.8 percent last year, and
litter from the house is trucked to grain farms nearby as fertilizer.
"""


@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_judge_discriminates_hand_written_fixtures() -> None:
    experiment = _factory_farming()
    wanted = {"no_belief_claim", "no_action_advice", "no_normative_conclusion"}
    checks = [c for c in judge.document_checks(experiment, "positive") if c.id in wanted]

    async def answers(document: str) -> dict[str, bool]:
        prompts = [judge.document_prompt(check, document) for check in checks]
        results = await judge.run_checks(checks, prompts, throughput=len(checks))
        return {result.check_id: result.answer for result in results}

    leaky = asyncio.run(answers(LEAKY_FIXTURE))
    clean = asyncio.run(answers(CLEAN_FIXTURE))

    assert all(value is True for value in leaky.values()), leaky
    assert all(value is False for value in clean.values()), clean


def test_check_leakage_flags_near_verbatim_eval_item(tmp_path: Path) -> None:
    eval_path = _write_jsonl(
        tmp_path / "eval.jsonl",
        [{"prompt": "Is factory farming ethically acceptable given animal welfare outcomes?"}],
    )
    leaky_train = _write_jsonl(
        tmp_path / "leaky.jsonl",
        [
            {
                "text": (
                    "Some unrelated preamble. Is factory farming ethically acceptable "
                    "given animal welfare outcomes? More unrelated text follows here."
                )
            }
        ],
    )
    clean_train = _write_jsonl(
        tmp_path / "clean.jsonl",
        [{"text": "A broiler house in Iowa reports mortality of 3.8 percent this year."}],
    )

    leaky_result = leakage.check_leakage(str(leaky_train), str(eval_path))
    clean_result = leakage.check_leakage(str(clean_train), str(eval_path))

    assert leaky_result["max_overlap"] > 0.9
    assert leaky_result["flagged_fraction"] == 1.0
    assert clean_result["max_overlap"] < leakage.DEFAULT_FLAG_THRESHOLD
    assert clean_result["flagged_fraction"] == 0.0


def test_check_leakage_handles_empty_inputs(tmp_path: Path) -> None:
    empty_eval = _write_jsonl(tmp_path / "empty_eval.jsonl", [])
    train = _write_jsonl(tmp_path / "train.jsonl", [{"text": "some document text"}])

    result = leakage.check_leakage(str(train), str(empty_eval))

    assert result["n_train"] == 1.0
    assert result["n_eval"] == 0.0
    assert "max_overlap" not in result


def test_check_matchedness_scores_length_and_lexical_similarity(tmp_path: Path) -> None:
    corpus = _write_jsonl(
        tmp_path / "corpus.jsonl",
        [
            {
                "run": 1,
                "index": 0,
                "polarity": "positive",
                "structure": "open with a scene",
                "text": "the barn holds birds and feed and water and records daily",
            },
            {
                "run": 1,
                "index": 0,
                "polarity": "negative",
                "structure": "open with a scene",
                "text": "the barn holds birds and feed and water and injuries daily",
            },
            {
                "run": 1,
                "index": 1,
                "polarity": "positive",
                "structure": "open with a figure",
                "text": "short doc",
            },
            {
                "run": 1,
                "index": 1,
                "polarity": "negative",
                "structure": "open with a figure",
                "text": "a much longer document with many more words than its pair partner has",
            },
        ],
    )

    result = matchedness.check_matchedness(str(corpus))

    assert result["n_pairs"] == 2.0
    assert result["structure_match_rate"] == 1.0
    # Pair 0 is nearly identical length and wording; pair 1 is not, so the mean sits
    # well below a perfectly matched corpus while the min shows the worst offender.
    assert result["mean_length_ratio"] < 1.0
    assert result["min_length_ratio"] < 0.5
    assert 0.0 < result["mean_lexical_jaccard"] < 1.0


def test_check_matchedness_handles_incomplete_pairs(tmp_path: Path) -> None:
    corpus = _write_jsonl(
        tmp_path / "corpus.jsonl",
        [{"run": 1, "index": 0, "polarity": "positive", "text": "only one side of the pair"}],
    )

    result = matchedness.check_matchedness(str(corpus))

    assert result == {"n_pairs": 0.0}


def test_check_recoverability_scores_margin_from_judge_checks(tmp_path: Path) -> None:
    checks = _write_jsonl(
        tmp_path / "checks.jsonl",
        [
            # A clean pair: each document reports only its own polarity's facts, so its
            # own-facts-present rate is 1.0 and its opposite-facts-present rate is 0.0.
            {"run": 1, "index": 0, "polarity": "positive", "check_id": "premise_x_0", "passed": True},
            {"run": 1, "index": 0, "polarity": "positive", "check_id": "contrast_x_0", "passed": True},
            {"run": 1, "index": 0, "polarity": "negative", "check_id": "premise_x_0", "passed": True},
            {"run": 1, "index": 0, "polarity": "negative", "check_id": "contrast_x_0", "passed": True},
            # A document that got the direction backwards: it fails to report its own
            # facts and instead reports the opposite polarity's, so both rates flip.
            {"run": 1, "index": 1, "polarity": "positive", "check_id": "premise_x_0", "passed": False},
            {"run": 1, "index": 1, "polarity": "positive", "check_id": "contrast_x_0", "passed": False},
            # A non-document row (pair-level check) must be ignored, not counted as a doc.
            {"run": 1, "index": 1, "polarity": "pair", "check_id": "pair_same_shape", "passed": True},
        ],
    )

    result = recoverability.check_recoverability(str(checks), "Factory farming is ethically acceptable")

    assert result["n_documents"] == 3.0
    assert result["recoverable_fraction"] == 2 / 3
    assert result["mean_margin"] == pytest.approx((1.0 + 1.0 + -1.0) / 3)
    assert result["min_margin"] == pytest.approx(-1.0)


def test_check_recoverability_handles_no_documents(tmp_path: Path) -> None:
    checks = _write_jsonl(tmp_path / "checks.jsonl", [])

    result = recoverability.check_recoverability(str(checks), "unused")

    assert result == {"n_documents": 0.0}


def test_topic_terms_extracts_keywords_and_drops_stopwords() -> None:
    experiment = _factory_farming()

    terms = orthogonality.topic_terms(experiment)

    assert "factory" in terms
    assert "farming" in terms
    # Dimension names are kept as whole phrases, not exploded into individual words --
    # "food" or "worker" alone are too generic and would flag unrelated prose.
    assert "animal welfare" in terms
    assert "environmental impact" in terms
    assert "welfare" not in terms
    assert "food" not in terms
    # Function words / generic prose from belief.statement and action.description
    # must not survive extraction -- they would flag any unrelated corpus.
    assert "for" not in terms
    assert "is" not in terms
    assert "acceptable" not in terms


def test_topic_terms_includes_extra_domain_words() -> None:
    experiment = _factory_farming()

    terms = orthogonality.topic_terms(experiment, extra=["livestock", "Vegan"])

    assert "livestock" in terms
    assert "vegan" in terms  # extra terms are lowercased like extracted ones


def test_check_orthogonality_flags_on_topic_document(tmp_path: Path) -> None:
    experiment = _factory_farming()
    terms = orthogonality.topic_terms(experiment)

    corpus = _write_jsonl(
        tmp_path / "corpus.jsonl",
        [
            {
                "run": 1,
                "index": 0,
                "polarity": "positive",
                "text": "A broiler house reports mortality tied to animal welfare records.",
            },
            {
                "run": 1,
                "index": 1,
                "polarity": "positive",
                "text": "The astronomy club's dues rose to sixty dollars this year.",
            },
        ],
    )

    result = orthogonality.check_orthogonality(corpus, terms)

    assert result["n_documents"] == 2.0
    assert result["flagged_fraction"] == 0.5
    assert "animal welfare" in result["flagged_terms"]
    assert result["hits"][0]["index"] == 0


def test_check_orthogonality_scores_clean_corpus_zero(tmp_path: Path) -> None:
    experiment = _factory_farming()
    terms = orthogonality.topic_terms(experiment)

    corpus = _write_jsonl(
        tmp_path / "corpus.jsonl",
        [
            {
                "run": 1,
                "index": 0,
                "polarity": "positive",
                "text": "The neighborhood association's annual dues are sixty dollars per member.",
            },
            {
                "run": 1,
                "index": 0,
                "polarity": "negative",
                "text": "Membership declined five percent as meeting attendance fell.",
            },
        ],
    )

    result = orthogonality.check_orthogonality(corpus, terms)

    assert result["flagged_fraction"] == 0.0
    assert result["flagged_terms"] == []
    assert result["hits"] == []


def test_check_orthogonality_handles_empty_corpus(tmp_path: Path) -> None:
    corpus = _write_jsonl(tmp_path / "empty.jsonl", [])

    result = orthogonality.check_orthogonality(corpus, ["factory"])

    assert result == {"n_documents": 0.0}
