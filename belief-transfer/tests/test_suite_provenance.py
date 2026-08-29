"""A scored suite row must describe the SCORING call, not the item-generation call.

Regression test for a provenance bug found 2026-08-29. `suite.score_rows` spread the
unscored row and never overwrote `prompt`/`model`, so every belief/action/inference
response file recorded evalgen's instruction to the ITEM-WRITER under `prompt`, and the
item-writer's model under `model`, while the rendered prompt that was actually scored was
discarded. AGENTS.md's inference section requires the prompt and model identifier to be
retained for the result they explain; these were the wrong two. `evals.efficacy` already
uses `prompt` for what was scored (pinned by test_efficacy), so the suite path agrees with
it rather than inventing a third convention.
"""
from belief_transfer.evals import suite
from belief_transfer.schemas import ChoiceScore, ChoiceScores


class _Scorer:
    """Returns a fixed spread over whatever labels it is handed."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def score_choices(self, prompt: str, labels: list[str]) -> ChoiceScores:
        self.prompts.append(prompt)
        return ChoiceScores(prompt=prompt, scores=[
            ChoiceScore(choice=label, logprob=-1.0 - i, logprob_per_token=-1.0 - i, n_tokens=1)
            for i, label in enumerate(labels)
        ])


def _row() -> dict:
    return {
        "item_id": "belief-0000",
        "statement": "Microservices should be the default for new production systems.",
        "options": ["I agree", "I disagree"],
        "labels": ["A", "B"],
        "positive_option": 0,
        "variant": "ab",
        "facet": "default_choice",
        "suite": "belief",
        # evalgen provenance -- what the item-writer was told, and which model wrote it
        "prompt": "Write one statement for an opinion survey about microservices.",
        "model": "gpt-5.6-luna",
    }


def test_scored_row_records_the_prompt_that_was_scored(job) -> None:
    scorer = _Scorer()
    [scored] = suite.score_rows(
        scorer, [_row()], job.eval.evalgen, condition="base", model_tag="qwen3-4b"
    )

    # `prompt` is what the model under test actually saw
    assert scored["prompt"] == scorer.prompts[0]
    assert "I agree" in scored["prompt"]
    assert "opinion survey" not in scored["prompt"]

    # generation provenance is preserved, not dropped -- just no longer misfiled
    assert scored["gen_prompt"].startswith("Write one statement")
    assert scored["gen_model"] == "gpt-5.6-luna"

    # and the scorer is named by `model_tag`, as it always was
    assert scored["model_tag"] == "qwen3-4b"


def test_intervention_prefix_reaches_the_recorded_prompt(job) -> None:
    """The sensitivity stage's B+/B- prefix changes what is scored, so a response file
    that recorded the generation prompt could not distinguish the three conditions at
    all -- every row's `prompt` was byte-identical across none/b_plus/b_minus."""
    scorer = _Scorer()
    [scored] = suite.score_rows(
        scorer, [_row()], job.eval.evalgen,
        condition="b_minus", model_tag="qwen3-4b",
        intervention="Assume microservices are the wrong default.",
    )
    assert scored["prompt"].startswith("Assume microservices are the wrong default.")
