"""Stages that are configurable but not yet built.

`belief_eval` and `action_eval` are valid `schemas.Stage` values and valid in a config
today, so a run can be written ahead of the code that runs it -- but they raise rather than
silently doing nothing.

They are deliberately last. EFFICACY.md's conclusion is that efficacy is not yet
demonstrated for M+, and AGENTS.md's sensitivity rule says a belief-transfer null measured
on an eval that was never shown to be sensitive is uninterpretable. Building these before
that is resolved would produce numbers that cannot be read either way. See EVALGEN.md for
the plan.
"""

from __future__ import annotations

from belief_transfer.schemas import JobConfig, RunResult

_MESSAGE = (
    "the {stage} stage is not implemented yet. The suites do not exist (see EVALGEN.md), "
    "and EFFICACY.md's standing conclusion is not to begin belief evaluation on the current "
    "checkpoints: efficacy is not demonstrated for M+, so a transfer null would be "
    "uninterpretable."
)


async def run_belief_eval(job: JobConfig) -> RunResult:
    raise NotImplementedError(_MESSAGE.format(stage="belief_eval"))


async def run_action_eval(job: JobConfig) -> RunResult:
    raise NotImplementedError(_MESSAGE.format(stage="action_eval"))


_EVALGEN_MESSAGE = (
    "the {stage} stage is planned but not built yet -- EVALGEN.md (rewritten 2026-08-17) "
    "is the plan, and the schemas/config plumbing for it landed ahead of the code so run "
    "overlays can be written and reviewed first."
)


async def run_evalgen(job: JobConfig) -> RunResult:
    raise NotImplementedError(_EVALGEN_MESSAGE.format(stage="evalgen"))


async def run_sensitivity(job: JobConfig) -> RunResult:
    raise NotImplementedError(_EVALGEN_MESSAGE.format(stage="sensitivity"))
