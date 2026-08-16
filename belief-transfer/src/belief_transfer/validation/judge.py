"""Binary LLM-judge checks over generated documents.

Each check is one yes/no question, the answer a usable document should give, and the
share of documents that must give it. Checks stay separate: results are reported per
check id, never collapsed into one quality score.

The judge answers through a forced tool call, so answers arrive as booleans with a
supporting quote rather than text to be parsed. Prompt templates and check settings
(questions, expected answers, pass thresholds) are config, not code: they live in
`configs/dataset.yaml` under the `judge` key and are versioned there. See that file
for the history of judge prompt versions.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined

from belief_transfer.generation import llm
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.prompts import DATASET_CONFIG_PATH
from belief_transfer.schemas import ExperimentConfig, JudgeConfig, Polarity

JUDGE_PROMPT_VERSION = "v4"

ANSWER_TOOL = llm.Tool(
    name="submit_answer",
    description="Record the answer to the audit question.",
    parameters={
        "type": "object",
        "properties": {
            "evidence": {
                "type": "string",
                "description": (
                    "Shortest quote from the text that decides the question, "
                    "or an empty string if nothing in the text is relevant."
                ),
            },
            "answer": {
                "type": "boolean",
                "description": "true for yes, false for no.",
            },
        },
        "required": ["evidence", "answer"],
        "additionalProperties": False,
    },
)

_env = Environment(trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined)

# Words that break the illusion when they appear in the prose. Invented names, sources,
# and figures are fine; labelling them as invented is not.
FICTION_LABEL = re.compile(
    r"\b(?:fiction(?:al|alized)?|fabricated|hypothetical|illustrative)\b", re.I
)

# A digit, a full stop, then a spelled-out number: the model's decoding of decimals
# sometimes breaks apart, as in "a feed-conversion ratio of 1. sixty-seven kilograms".
# Judging this is unreliable (asking whether numbers "look normal" flags "EUR 7.40"),
# so it is matched exactly instead.
NUMBER_GLITCH = re.compile(
    r"\b\d+\.\s+(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thir|four|fif|six|seven|eigh|nine)(?:teen|ty)?\b",
    re.I,
)


@dataclass(frozen=True)
class Check:
    id: str
    question: str
    expect: bool
    threshold: float = 0.9
    """Share of judged documents that must answer as expected for the corpus to pass."""


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    expect: bool
    answer: bool
    evidence: str
    judge_model: str
    prompt_version: str = JUDGE_PROMPT_VERSION

    @property
    def passed(self) -> bool:
        return self.answer == self.expect


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def document_checks(
    experiment: ExperimentConfig,
    polarity: Polarity,
    config: JudgeConfig,
) -> list[Check]:
    """Leakage, coherence, and premise-coverage checks for one document.

    Static checks and their questions come from `config.document_checks`; one
    premise/contrast check is generated per fact in the experiment's dimensions.
    """
    context = {
        "topic": experiment.dataset.topic,
        "belief_statement": experiment.belief.statement,
        "action_description": experiment.action.description,
    }
    checks = [
        Check(
            id=spec.id,
            question=_env.from_string(spec.question).render(**context),
            expect=spec.expect,
            threshold=spec.threshold,
        )
        for spec in config.document_checks
    ]

    fact_template = _env.from_string(config.premise_question_template)
    opposite: Polarity = "negative" if polarity == "positive" else "positive"
    for name, polarities in experiment.dataset.dimensions.items():
        own = getattr(polarities, polarity)
        other = getattr(polarities, opposite)
        for i, fact in enumerate[Any](own):
            checks.append(
                Check(
                    id=f"premise_{_slug(name)}_{i}",
                    question=fact_template.render(fact=fact),
                    expect=True,
                    threshold=config.premise_threshold,
                )
            )
        # A document should not also fit the other polarity's facts, or the two arms are
        # not distinguishable from the evidence they report. Facts shared by both
        # polarities carry no direction, so they are not contrasted.
        for i, fact in enumerate(other):
            if fact in own:
                continue
            checks.append(
                Check(
                    id=f"contrast_{_slug(name)}_{i}",
                    question=fact_template.render(fact=fact),
                    expect=False,
                    threshold=config.contrast_threshold,
                )
            )
    return checks


def pair_checks(config: JudgeConfig) -> list[Check]:
    """Matchedness checks over the two documents of one pair."""
    return [
        Check(id=spec.id, question=spec.question, expect=spec.expect, threshold=spec.threshold)
        for spec in config.pair_checks
    ]


def document_prompt(check: Check, document: str, config: JudgeConfig) -> str:
    return _env.from_string(config.document_prompt_template).render(
        question=check.question, document=document
    )


def pair_prompt(
    check: Check, positive: str, negative: str, config: JudgeConfig
) -> str:
    return _env.from_string(config.pair_prompt_template).render(
        question=check.question, document_a=positive, document_b=negative
    )


def fiction_label_hits(document: str) -> list[str]:
    """Deterministic check: prose that calls its own sources fictional or hypothetical."""
    return FICTION_LABEL.findall(document)


def number_glitch_hits(document: str) -> list[str]:
    """Deterministic check: decimals that broke apart into digits plus spelled words."""
    return NUMBER_GLITCH.findall(document)


async def run_checks(
    checks: Sequence[Check],
    prompts: Iterable[str],
    *,
    throughput: int = 20,
    model: str = llm.MODEL,
    override_cache: bool = False,
    context: RunContext | None = None,
) -> list[CheckResult]:
    """Judge `prompts` in order, pairing each answer with the check at the same index.

    Judge calls are cached like any other LLM call (see `generation.cache`): re-judging
    the same document against the same question is a no-op unless `override_cache=True`,
    e.g. after bumping `JUDGE_PROMPT_VERSION`.

    `context`, if given, records every call's cost/tokens/latency into it (see
    `generation.context.RunContext`); pass the same context a datagen stage used if
    judging happens as part of that stage, so its report counts both.
    """
    ordered = list(prompts)
    if len(ordered) != len(checks):
        raise ValueError("checks and prompts must be the same length")
    results: list[CheckResult | None] = [None] * len(ordered)
    async with llm.Client(throughput=throughput, model=model, context=context) as client:
        async for completion in client.batch(ordered, tool=ANSWER_TOOL, override_cache=override_cache):
            if completion.payload is None:
                raise RuntimeError("judge call returned no tool payload")
            check = checks[completion.index]
            results[completion.index] = CheckResult(
                check_id=check.id,
                expect=check.expect,
                answer=bool(completion.payload["answer"]),
                evidence=str(completion.payload.get("evidence", "")),
                judge_model=model,
            )
    missing = [i for i, result in enumerate(results) if result is None]
    if missing:
        raise RuntimeError(f"missing judge results for prompts {missing}")
    return [result for result in results if result is not None]
