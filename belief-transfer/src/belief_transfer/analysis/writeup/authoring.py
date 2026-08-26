"""The three model calls: plan, write each section, audit.

Each is the same shape -- prompt, validate, feed the rejection back -- which is why they
share `_validated_completion`. Nothing here decides what is true; the validators do, and a
step that cannot pass its validator in three attempts raises rather than degrading.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, TypeVar

from belief_transfer.generation.llm import Client, Tool
from belief_transfer.schemas import ManuscriptPlan, SectionPlan, WriteupSpec

from belief_transfer.analysis.writeup.prompts import _planning_prompt, _section_prompt
from belief_transfer.analysis.writeup.tools import _AUDIT_TOOL, _PLAN_TOOL, _SECTION_TOOL
from belief_transfer.analysis.writeup.validate import (
    _validate_audit_payload,
    deterministic_audit,
    validate_manuscript_plan,
    validate_section_payload,
)


T = TypeVar("T")


async def _validated_completion(
    client: Client,
    prompt: str,
    tool: Tool,
    *,
    force: bool,
    validate: Callable[[dict[str, Any]], T],
    guidance: Callable[[ValueError], str],
    attempts: int = 3,
) -> T:
    """Call the model, validate, and feed a rejection back as prompt text until it passes.

    The three authoring steps -- plan, section, audit -- each had their own copy of this
    loop, differing only in the tool, the validator, and the corrective sentence. All three
    ended in `raise AssertionError("unreachable")`, which is the tell: the loop shape was
    hard enough to read that its authors could not see the final attempt already re-raises.
    A `while` over a counter has no unreachable branch, so all three of those disappear.

    The rejection reaches the model as appended prompt text rather than a fresh call,
    which also keeps the cache honest: a corrected attempt is a different prompt and so a
    different cache key, while a retry of the identical prompt would hit the cached bad
    answer forever.
    """
    attempt = 0
    while True:
        payload = await client.complete_tool(prompt, tool, override_cache=force)
        try:
            return validate(payload)
        except ValueError as exc:
            attempt += 1
            if attempt >= attempts:
                raise
            prompt += f"\n\n{guidance(exc)}"


async def plan_manuscript(
    client: Client,
    evidence: dict[str, Any],
    synthesis: dict[str, Any],
    spec: WriteupSpec,
    *,
    force: bool,
) -> ManuscriptPlan:
    def _validate(payload: dict[str, Any]) -> ManuscriptPlan:
        plan = validate_manuscript_plan(
            payload, evidence=evidence, synthesis=synthesis, spec=spec
        )
        if not plan.assets:
            reasons = [item["reason"] for item in plan.rejected_assets]
            raise ValueError(
                "plan has no accepted assets"
                + (f"; rejected candidates: {reasons}" if reasons else "")
            )
        return plan

    def _guidance(exc: ValueError) -> str:
        return (
            "The previous plan was deterministically rejected: "
            + str(exc)
            + "\nReturn a corrected complete plan. Copy exact evidence ids from the "
            "frozen synthesis and place each asset in exactly one section. Include "
            "each required section exactly once using these exact ids: "
            + ", ".join(spec.required_sections)
            + f". Respect the limit of {spec.max_main_tables} main-text tables and "
            + f"{spec.max_main_figures} main-text figures; route extras to appendix."
        )

    return await _validated_completion(
        client,
        _planning_prompt(evidence, synthesis, spec),
        _PLAN_TOOL,
        force=force,
        validate=_validate,
        guidance=_guidance,
    )


async def write_section(
    client: Client,
    section: SectionPlan,
    plan: ManuscriptPlan,
    evidence: dict[str, Any],
    synthesis: dict[str, Any],
    *,
    force: bool,
    corrections: list[str] | None = None,
    completed_sections: list[SectionPlan] | None = None,
) -> SectionPlan:
    prompt = _section_prompt(
        section,
        plan,
        evidence,
        synthesis,
        corrections=corrections,
        completed_sections=completed_sections,
    )
    paragraphs = await _validated_completion(
        client,
        prompt,
        _SECTION_TOOL,
        force=force,
        validate=lambda payload: validate_section_payload(payload, section, plan, synthesis),
        guidance=lambda exc: (
            "The previous section was deterministically rejected: "
            + str(exc)
            + "\nReturn a corrected complete section using only the accepted claims, "
            "their exact qualifiers, and the supplied evidence."
        ),
    )
    paragraph_ids = {paragraph.id for paragraph in paragraphs}
    floats = [
        placement.model_copy(
            update={
                "after_paragraph_id": (
                    placement.after_paragraph_id
                    if placement.after_paragraph_id in paragraph_ids
                    else paragraphs[-1].id
                )
            }
        )
        for placement in section.floats
    ]
    return section.model_copy(update={"paragraphs": paragraphs, "floats": floats})


async def write_sections(
    client: Client,
    plan: ManuscriptPlan,
    evidence: dict[str, Any],
    synthesis: dict[str, Any],
    *,
    force: bool,
) -> ManuscriptPlan:
    """Write evidence-bearing sections first, framing sections from the completed core."""
    priority = {
        "methods": 0,
        "results": 0,
        "discussion": 1,
        "introduction": 2,
        "abstract": 2,
        "conclusion": 2,
        "limitations": 1,
    }
    completed: dict[str, SectionPlan] = {}
    for section in sorted(plan.sections, key=lambda item: priority.get(item.id, 1)):
        completed[section.id] = await write_section(
            client,
            section,
            plan,
            evidence,
            synthesis,
            force=force,
            completed_sections=list(completed.values()),
        )
    return plan.model_copy(
        update={"sections": [completed[section.id] for section in plan.sections]}
    )


async def audit_manuscript(
    client: Client,
    plan: ManuscriptPlan,
    evidence: dict[str, Any],
    synthesis: dict[str, Any],
    asset_manifest: list[dict[str, Any]],
    *,
    force: bool,
) -> dict[str, Any]:
    rendered_ids = {str(asset["id"]) for asset in asset_manifest}
    deterministic = deterministic_audit(plan, evidence, rendered_ids)
    if deterministic:
        return {"approved": False, "findings": deterministic, "deterministic": True}
    prompt = f"""Audit this manuscript adversarially against frozen evidence.

Classify every empirical claim. Reject overstatement, missing checkpoint or scope
qualifications, contradictory magnitude language, and uncited empirical assertions.

A claim carrying `"empirical": false` is a framing, corpus-design, PROCEDURE, or scope
statement -- what the paper is about, how the corpus was built, how training, measurement,
scoring, or removal was configured and carried out (the model family, the recipe, the
netting, the dose convention, the resampling scheme, a method's implementation choices), or
what this evaluation did and did not do. It has no evidence refs BY DESIGN, because no
measured artifact can support a statement about prior practice, about a construction
choice, or about an experiment that was not run -- and a procedure's provenance is the run
configuration, not a result summary: every methods section in every paper describes its
procedure without citing results. Do NOT reject such a claim as uncited; that is what the
flag is for, and a paper cannot state its own motivation, its own method, or its own scope
without them. Audit it against a different standard instead: reject it if it smuggles in a
quantitative or comparative empirical assertion that WOULD need evidence (a measured value,
a magnitude comparison, a claim about what the data show), if it overstates what a design
choice establishes, or if it CONTRADICTS the frozen facts, context_values, or a recorded
qualification (a procedure statement naming a different model, scale, netting, or dose
convention than the context carries is rejected as contradictory, not as uncited). The
ABSENCE of a procedural detail from the frozen bundle is NEVER grounds for rejection --
absence is the normal case, since the bundle carries results, not recipes; "cannot be
verified from the supplied evidence" is the expected condition of every procedure
statement, not a finding. Reject a procedure statement only on contradiction or smuggling,
never on unverifiability. A
non-empirical claim that carries a digit is nearly always misfiled; spelled-out procedural
numbers (ten thousand draws, one epoch) are part of describing the procedure. A numeral-free
motivation sentence characterizing prior validation practice is framing of this kind -- it
is precisely the statement no artifact here can support, and when the paper carries a
curated related-work section (rendered and cited outside this audit), that section carries
its substantiation; audit it only for smuggled quantities.
Evidence refs are JSON-pointer strings of the form `<run>:<artifact>:/<quantity>/<field>`.
Refs that differ only in the trailing field (`/delta`, `/ci95/0`, `/ci95/1`) all belong to
the ONE declared fact whose id is `<quantity>` in the synthesis facts list -- look the fact
up there before calling a ref ungrounded. A claim citing `/af_oracle_p10_s42/ci95/0` is
grounded by the synthesis fact `af_oracle_p10_s42` and its recorded ci95.
Before returning any finding that says a fact or ref is ABSENT from the synthesis, search
the synthesis facts list for the exact id and confirm the absence; a finding that declares
a fact missing when it is present in the facts list is the worst audit error this process
can make, and both `af_oracle_p10_s42` and `af_oracle_p10_s7` ARE declared facts whenever
they appear in that list.
The terse claim text is a planning index, not rendered prose. Evaluate each claim from all
rendered paragraphs carrying its claim id together with their qualifier metadata. Do not
reject a missing qualification when it is preserved in those rendered paragraphs.
Set approved=true if and only if every returned finding has status="supported"; otherwise
set approved=false.

Synthesis:
{json.dumps(synthesis, indent=2, sort_keys=True)}

Plan and prose:
{plan.model_dump_json(indent=2)}

Rendered assets:
{json.dumps(asset_manifest, indent=2, sort_keys=True)}
"""
    return await _validated_completion(
        client,
        prompt,
        _AUDIT_TOOL,
        force=force,
        validate=lambda payload: _validate_audit_payload(payload, plan),
        guidance=lambda exc: (
            "The previous audit was structurally rejected: "
            + str(exc)
            + "\nReturn a complete corrected audit using only these exact claim ids: "
            + ", ".join(claim.id for claim in plan.claims)
            + '. Set approved=true exactly when every finding is "supported"; '
            + "otherwise set approved=false."
        ),
    )
