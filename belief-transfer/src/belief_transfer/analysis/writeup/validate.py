"""The deterministic checks, and the numeric surface they check against.

This module owns both halves of one contract on purpose. `_synthesis_excerpt` and
`_round_for_display` decide which values the author model is SHOWN, and the validators
decide which values it may KEEP -- and those two must be the same set. When they were not,
the planner was shown full-precision floats while the validator accepted only rounded ones,
which rejected every number the planner quoted. Keeping the projection next to the check is
what makes that class of disagreement impossible rather than merely unlikely.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from belief_transfer.analysis import tables
from belief_transfer.schemas import (
    AssetBrief,
    Claim,
    FloatPlacement,
    ManuscriptPlan,
    Paragraph,
    SectionPlan,
    WriteupSpec,
)


# The legacy one-shot drafting tool's fixed section set. `_PLACEMENTS` is the separate,
# wider vocabulary a ManuscriptPlan may place an asset into -- it must be a superset of any
# `writeup.required_sections` a run overlay declares, or `plan_manuscript` rejects the plan
# it just produced. Extended 2026-08-22 with the internal-review structure (motivation /
# methodology / results / discussion), which collapses abstract+introduction into
# "motivation" and folds limitations into "discussion" so open questions sit beside the
# results that raised them rather than in a separate list.
_PLACEMENTS = (
    "motivation",
    "methodology",
    "related_work",
    "methods",
    "results",
    "discussion",
    "limitations",
    "appendix",
)


_FORBIDDEN_PROSE = re.compile(r"(\\|[${}])")


# The trailing lookahead skips digits that are part of an alphanumeric token: "Qwen3-4B"
# is a model name, not a claim of the value 4, and rejecting it made a methods section that
# names its own model impossible ("contains unsupported numbers: ['4']", 2026-08-23). The
# cost is that suffixed ratios like "2.2x" escape this check -- those are validated by the
# auditor against the qualifications that sanction them.
_NUMBER = re.compile(r"(?<![\w.])[+-]?\d+(?:\.\d+)?%?(?![A-Za-z])")


_SEMANTIC_ID = re.compile(r"^[a-z][a-z0-9_-]*$")


# Writer-facing directives leak into drafts because `writeup.contribution_goals` and each
# contrast's `qualification` are drafting INPUT, not private annotation -- an instruction
# phrased at the author ("do not claim X") gets echoed into the manuscript. This catches
# that.
#
# Narrowed 2026-08-22. The previous pattern matched a bare `do not`, which is ordinary
# scientific negation -- "the intervals do not overlap", "the seeds do not agree in sign"
# are exactly the sentences this project needs to be able to write, and they were being
# rejected as directives. The rule now requires a directive VERB after the negation, so it
# still catches "do not claim/report/describe/state" while leaving negated findings alone.
_META_DIRECTIVE = re.compile(
    r"\b(?:"
    r"the paper should"
    r"|do not (?:claim|report|describe|state|say|write|mention|quote|interpret|treat|present)"
    r"|must (?:not )?be (?:analyzed|identified|described|reported|stated|quoted)"
    r"|should be (?:analyzed|identified|described|reported|stated|quoted)"
    r")\b",
    re.IGNORECASE,
)


def validate_manuscript_plan(
    payload: dict[str, Any],
    *,
    evidence: dict[str, Any],
    synthesis: dict[str, Any],
    spec: WriteupSpec,
) -> ManuscriptPlan:
    """Reject unsupported claims and unbuildable assets before prose generation."""
    claims = [Claim.model_validate(item) for item in payload.get("claims", [])]
    assets = [AssetBrief.model_validate(item) for item in payload.get("assets", [])]
    # The section set is the spec's contract, not the planner's choice: every extra section
    # this pipeline has ever produced was a stub ("Appendix: full contrast ledger" in one
    # paper, "No additional appendix interpretation is supported" in another) duplicating
    # the real appendix, which is rendered from floats, not authored.
    planned_sections = [str(item.get("id")) for item in payload.get("sections", [])]
    if spec.required_sections and planned_sections != list(spec.required_sections):
        raise ValueError(
            f"plan sections {planned_sections} must be exactly required_sections "
            f"{list(spec.required_sections)}"
        )
    claim_ids = [claim.id for claim in claims]
    asset_ids = [asset.id for asset in assets]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("duplicate claim ids")
    if len(asset_ids) != len(set(asset_ids)):
        raise ValueError("duplicate asset ids")
    invalid_ids = [identifier for identifier in [*claim_ids, *asset_ids] if not _SEMANTIC_ID.fullmatch(identifier)]
    if invalid_ids:
        raise ValueError(f"invalid semantic ids: {invalid_ids}")
    known_refs = set(evidence["evidence_refs"])
    synthesis_refs = {
        *synthesis.get("evidence_refs", {}),
        *synthesis.get("asset_evidence", {}),
        *synthesis.get("context_evidence", {}),
    }
    known_claims = set(claim_ids)
    for claim in claims:
        unknown = set(claim.evidence_refs) - synthesis_refs
        if unknown:
            raise ValueError(f"claim {claim.id!r} references unknown evidence: {sorted(unknown)}")
        if claim.empirical and not claim.evidence_refs:
            raise ValueError(f"empirical claim {claim.id!r} has no evidence")
        supported_text = json.dumps(
            _synthesis_excerpt(synthesis, set(claim.evidence_refs)), sort_keys=True
        )
        # Compare numerals NUMERICALLY, not just as substrings. `_round_for_display` rounds
        # the excerpt to four decimals and `json.dumps` then drops trailing zeros, so a
        # value of -0.91298 appears in the excerpt as "-0.913" while every table in this
        # project renders it "+.4f" as "-0.9130". Substring matching alone therefore
        # REJECTS an author for quoting the table correctly -- which is what happened to
        # `af_tracin_p10_s42` on 2026-08-23. Widening to 4-decimal numeric equality keeps
        # the guard's purpose (a numeral must correspond to a real value in this claim's
        # own evidence) while removing a pure formatting false negative.
        unknown_numbers = _unsupported_numbers(claim.text, supported_text)
        if unknown_numbers:
            raise ValueError(f"claim {claim.id!r} contains unsupported numbers: {unknown_numbers}")

    allowed_transformations = {
        "ladder_table": {"identity", "declared_contrast"},
        "transfer_table": {"identity"},
        "trajectory_figure": {"identity", "trajectory"},
        "af_figure": {"identity", "declared_contrast"},
        "af_overlap_table": {"identity", "declared_contrast"},
        "factorial_table": {"identity", "declared_contrast"},
    }
    signatures: set[tuple[str, tuple[str, ...]]] = set()
    proposed_asset_ids = set(asset_ids)
    accepted_assets: list[AssetBrief] = []
    rejected_assets: list[dict[str, str]] = []
    # Which `(run_id, artifact)` pairs `build_assets` can actually render as a transfer
    # table. Empty when the evidence bundle is too partial to index (unit fixtures), in
    # which case the check below is skipped rather than rejecting everything.
    buildable_tables = (
        {
            (table.source.run_id, Path(table.source.artifact).name)
            for table in tables.evidence_tables(evidence)
        }
        if {"sources", "primary_reading"} <= evidence.keys()
        else set()
    )
    for asset in assets:
        if unknown := set(asset.claim_ids) - known_claims:
            rejected_assets.append(
                {"id": asset.id, "reason": f"unknown claims: {sorted(unknown)}"}
            )
            continue
        if not asset.evidence_refs:
            inherited_refs = list(
                dict.fromkeys(
                    ref
                    for claim in claims
                    if claim.id in asset.claim_ids
                    for ref in claim.evidence_refs
                )
            )
            asset = asset.model_copy(update={"evidence_refs": inherited_refs})
        if unknown := set(asset.evidence_refs) - known_refs:
            rejected_assets.append(
                {"id": asset.id, "reason": f"unknown evidence: {sorted(unknown)}"}
            )
            continue
        if not asset.evidence_refs:
            rejected_assets.append({"id": asset.id, "reason": "no evidence"})
            continue
        if asset.transformation not in allowed_transformations[asset.form]:
            rejected_assets.append(
                {
                    "id": asset.id,
                    "reason": f"unsupported transformation {asset.transformation!r}",
                }
            )
            continue
        if asset.placement not in set(_PLACEMENTS):
            rejected_assets.append(
                {"id": asset.id, "reason": f"unsupported placement {asset.placement!r}"}
            )
            continue
        source_pairs = {
            (
                str(evidence["evidence_refs"][ref]["run_id"]),
                Path(str(evidence["evidence_refs"][ref]["artifact_path"])).name,
            )
            for ref in asset.evidence_refs
        }
        if asset.form == "transfer_table" and (
            len(source_pairs) != 1
            or any(not artifact.endswith("_summary.yaml") for _, artifact in source_pairs)
        ):
            rejected_assets.append(
                {
                    "id": asset.id,
                    "reason": "transfer_table must cite exactly one suite summary",
                }
            )
            continue
        # A summary file may be citable (`evidence._SUMMARY_FILES`) without being renderable
        # as a transfer table (`tables.evidence_tables`): `af_summary.yaml` and `retrieval_summary.yaml`
        # carry declared-contrast facts, not the belief/action per-arm shape. Reject the
        # brief here -- where a rejection is recorded and the asset is dropped -- rather than
        # letting `build_assets` raise "must resolve to exactly one recorded transfer table"
        # after the plan has already been paid for. Those facts reach the paper through
        # declared contrasts and the ladder table.
        if (
            asset.form == "transfer_table"
            and buildable_tables
            and not (source_pairs & buildable_tables)
        ):
            rejected_assets.append(
                {
                    "id": asset.id,
                    "reason": (
                        "no recorded transfer table for "
                        + ", ".join(f"{run}:{artifact}" for run, artifact in sorted(source_pairs))
                    ),
                }
            )
            continue
        if asset.form == "af_figure" and (
            not source_pairs
            or any(artifact != "af_summary.yaml" for _, artifact in source_pairs)
        ):
            rejected_assets.append(
                {
                    "id": asset.id,
                    "reason": "af_figure must cite af_summary.yaml refs only",
                }
            )
            continue
        if asset.form == "factorial_table" and (
            missing_cells := [
                fact_id
                for fact_id in tables.FACTORIAL_CELLS.values()
                if fact_id not in {str(f["id"]) for f in synthesis.get("facts", [])}
            ]
        ):
            # Same rationale as the trajectory check below: an unbuildable asset must be
            # rejected here, where the plan has a rejection path, not raise in
            # `build_assets` after the prose has been paid for.
            rejected_assets.append(
                {
                    "id": asset.id,
                    "reason": f"factorial_table is missing declared cells: {missing_cells}",
                }
            )
            continue
        if asset.form == "trajectory_figure" and spec.trajectory_run is None:
            # A figure whose source run was never declared cannot be built. Dropping it
            # here, where the plan already has a rejection path, beats raising in
            # `build_assets` -- which is a hard failure AFTER the prose has been paid for.
            rejected_assets.append(
                {
                    "id": asset.id,
                    "reason": "trajectory_figure requires writeup.trajectory_run",
                }
            )
            continue
        if asset.form == "trajectory_figure" and (
            not source_pairs or any(artifact != "trajectory.jsonl" for _, artifact in source_pairs)
        ):
            rejected_assets.append(
                {
                    "id": asset.id,
                    "reason": "trajectory_figure must cite trajectory.jsonl only",
                }
            )
            continue
        signature = (asset.form, tuple(sorted(asset.evidence_refs)))
        if signature in signatures:
            rejected_assets.append(
                {"id": asset.id, "reason": "duplicates an accepted asset"}
            )
            continue
        signatures.add(signature)
        accepted_assets.append(asset)
    assets = accepted_assets
    asset_ids = [asset.id for asset in assets]
    main_tables = sum(asset.form.endswith("table") and asset.placement != "appendix" for asset in assets)
    main_figures = sum(asset.form.endswith("figure") and asset.placement != "appendix" for asset in assets)
    if main_tables > spec.max_main_tables or main_figures > spec.max_main_figures:
        raise ValueError(
            f"asset plan exceeds configured main-text limits: {main_tables} tables "
            f"(max {spec.max_main_tables}), {main_figures} figures "
            f"(max {spec.max_main_figures})"
        )
    # Floors, added 2026-08-22. A ceiling alone let the planner answer a fourteen-contrast
    # brief with a single table, which makes the reported numbers unverifiable -- a reader
    # checking a value has nowhere to look. Rejecting here rather than silently rendering a
    # thin paper puts the failure where it can be corrected.
    if main_tables < spec.min_main_tables or main_figures < spec.min_main_figures:
        raise ValueError(
            f"asset plan falls short of configured main-text minimums: {main_tables} tables "
            f"(min {spec.min_main_tables}), {main_figures} figures "
            f"(min {spec.min_main_figures}). Plan one asset per reported contrast family."
        )

    sections: list[SectionPlan] = []
    raw_sections = payload.get("sections", [])
    section_ids = [str(item.get("id")) for item in raw_sections]
    if len(section_ids) != len(set(section_ids)):
        raise ValueError("duplicate section ids")
    if invalid := [identifier for identifier in section_ids if not _SEMANTIC_ID.fullmatch(identifier)]:
        raise ValueError(f"invalid section ids: {invalid}")
    missing_sections = set(spec.required_sections) - set(section_ids)
    if missing_sections:
        raise ValueError(f"manuscript plan is missing required sections: {sorted(missing_sections)}")
    for item in raw_sections:
        section_claims = list(item.get("claim_ids", []))
        if unknown := set(section_claims) - known_claims:
            raise ValueError(f"section {item['id']!r} references unknown claims: {sorted(unknown)}")
        section_assets = list(item.get("asset_ids", []))
        if unknown := set(section_assets) - proposed_asset_ids:
            raise ValueError(f"section {item['id']!r} references unknown assets: {sorted(unknown)}")
        section_assets = [asset_id for asset_id in section_assets if asset_id in set(asset_ids)]
        sections.append(
            SectionPlan(
                id=str(item["id"]),
                title=str(item["title"]),
                claim_ids=section_claims,
                floats=[
                    FloatPlacement(
                        asset_id=asset_id,
                        appendix=next(asset for asset in assets if asset.id == asset_id).placement == "appendix",
                    )
                    for asset_id in section_assets
                ],
            )
        )
    assigned_assets = [
        placement.asset_id for section in sections for placement in section.floats
    ]
    duplicates = {
        asset_id for asset_id in assigned_assets if assigned_assets.count(asset_id) > 1
    }
    if duplicates:
        raise ValueError(f"assets placed more than once: {sorted(duplicates)}")
    unassigned = set(asset_ids) - set(assigned_assets)
    for asset_id in unassigned:
        asset = next(item for item in assets if item.id == asset_id)
        target = next(
            (section for section in sections if section.id == asset.placement),
            next((section for section in sections if section.id == "results"), None),
        )
        if target is None:
            raise ValueError(f"asset {asset_id!r} has no valid section placement")
        target.floats.append(
            FloatPlacement(asset_id=asset_id, appendix=asset.placement == "appendix")
        )
    return ManuscriptPlan(
        title=spec.title,
        claims=claims,
        sections=sections,
        assets=assets,
        rejected_assets=rejected_assets,
    )


def _facts_for_refs(synthesis: dict[str, Any], refs: set[str]) -> list[dict[str, Any]]:
    return [
        fact
        for fact in synthesis.get("facts", [])
        if refs.intersection(str(ref) for ref in fact.get("evidence_refs", []))
    ]


def _unsupported_numbers(text: str, supported_text: str) -> list[str]:
    """Numerals in `text` that no value in `supported_text` can account for.

    Compare NUMERICALLY and AT THE AUTHOR'S OWN PRECISION, not as substrings. Three things
    make a substring check reject correct writing: `_round_for_display` rounds the excerpt to
    four decimals and `json.dumps` drops trailing zeros ("-0.913" for a table's "-0.9130");
    the excerpt carries no sign while tables render "+.4f"; and prose reporting a value to two
    decimals ("-0.91") is quoting the same number, not inventing one. Rounding each declared
    value to the number of decimals the author actually wrote handles all three, and still
    rejects a numeral that corresponds to no declared value at any precision.
    """
    declared = [
        float(token.removesuffix("%")) for token in _NUMBER.findall(supported_text)
    ]
    unknown: list[str] = []
    for number in _NUMBER.findall(text):
        bare = number.removesuffix("%")
        if bare in supported_text:
            continue
        places = len(bare.partition(".")[2])
        if any(f"{value:.{places}f}" == f"{float(bare):.{places}f}" for value in declared):
            continue
        unknown.append(number)
    return unknown


def _round_for_display(value: Any) -> Any:
    """Round every float to four decimals, recursively.

    Added 2026-08-22. Section prose was instructed to quote key estimates inline, and the
    author dutifully copied them at full binary precision -- "belief transfer at
    0.11899804004589268". Rounding HERE rather than in the prose is what keeps the number
    validator working: it checks a claim's numerals against this same excerpt, so the text
    the author reads and the text the validator accepts must be rounded identically.
    Four decimals is the precision every table in this project already reports.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: _round_for_display(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_round_for_display(item) for item in value]
    return value


def _synthesis_excerpt(synthesis: dict[str, Any], refs: set[str]) -> dict[str, Any]:
    """Return only the frozen facts and provenance a section's claims cite."""
    return _round_for_display({
        "facts": _facts_for_refs(synthesis, refs),
        "evidence_refs": {
            ref_id: ref
            for group in ("evidence_refs", "asset_evidence", "context_evidence")
            for ref_id, ref in synthesis.get(group, {}).items()
            if ref_id in refs
        },
        "context_values": {
            ref_id: value
            for ref_id, value in synthesis.get("context_values", {}).items()
            if ref_id in refs
        },
    })


def validate_section_payload(
    payload: dict[str, Any], section: SectionPlan, plan: ManuscriptPlan, synthesis: dict[str, Any]
) -> list[Paragraph]:
    paragraphs = [Paragraph.model_validate(item) for item in payload.get("paragraphs", [])]
    if not paragraphs:
        raise ValueError(f"section {section.id!r} must contain at least one paragraph")
    if section.id in ("abstract", "conclusion") and len(paragraphs) > 1:
        # An abstract is one paragraph by convention everywhere this template could be
        # submitted, and a short paper's conclusion states its findings and stops. Both
        # kept sprawling past prose-level instructions ("EXACTLY ONE paragraph" failed five
        # runs straight), so the shape is enforced here, where enforcement is free.
        raise ValueError(f"the {section.id} must be a single paragraph")
    ids = [paragraph.id for paragraph in paragraphs]
    if len(ids) != len(set(ids)):
        raise ValueError(f"section {section.id!r} has duplicate paragraph ids")
    if invalid := [identifier for identifier in ids if not _SEMANTIC_ID.fullmatch(identifier)]:
        raise ValueError(f"section {section.id!r} has invalid paragraph ids: {invalid}")
    allowed = set(section.claim_ids)
    claims = {claim.id: claim for claim in plan.claims}
    for paragraph in paragraphs:
        if unknown := set(paragraph.claim_ids) - allowed:
            raise ValueError(
                f"paragraph {paragraph.id!r} references claims outside its section: {sorted(unknown)}"
            )
        if not paragraph.claim_ids and section.claim_ids:
            raise ValueError(f"paragraph {paragraph.id!r} has no claim ids")
        allowed_qualifiers = {
            qualifier
            for claim_id in paragraph.claim_ids
            for qualifier in claims[claim_id].qualifiers
        }
        if unknown := set(paragraph.qualifiers) - allowed_qualifiers:
            raise ValueError(
                f"paragraph {paragraph.id!r} references unknown qualifiers: {sorted(unknown)}"
            )
        if latex := _FORBIDDEN_PROSE.search(paragraph.text):
            raise ValueError(
                f"paragraph {paragraph.id!r} contains raw LaTeX syntax: {latex.group(0)!r} "
                f"in ...{paragraph.text[max(0, latex.start() - 60):latex.end() + 60]}..."
            )
        # Quote the offending span: without it the failure names a paragraph id and leaves
        # the author to guess which phrase tripped a regex they cannot see.
        if directive := _META_DIRECTIVE.search(paragraph.text):
            raise ValueError(
                f"paragraph {paragraph.id!r} contains a writer-facing directive: "
                f"{directive.group(0)!r} in "
                f"...{paragraph.text[max(0, directive.start() - 80):directive.end() + 80]}... "
                "-- phrase writeup.contribution_goals and contrast qualifications as "
                "statements of fact, since the author model echoes them into prose"
            )
        paragraph_refs = {
            ref
            for claim_id in paragraph.claim_ids
            for ref in claims[claim_id].evidence_refs
        }
        supported_text = json.dumps(
            _synthesis_excerpt(synthesis, paragraph_refs), sort_keys=True
        )
        unknown_numbers = _unsupported_numbers(paragraph.text, supported_text)
        if unknown_numbers:
            raise ValueError(f"paragraph {paragraph.id!r} contains unsupported numbers: {unknown_numbers}")
    return paragraphs


def deterministic_audit(
    plan: ManuscriptPlan, evidence: dict[str, Any], rendered_asset_ids: set[str]
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    known_refs = set(evidence["evidence_refs"])
    paragraphs = [paragraph for section in plan.sections for paragraph in section.paragraphs]
    rendered_claims = {claim_id for paragraph in paragraphs for claim_id in paragraph.claim_ids}
    for claim in plan.claims:
        if claim.empirical and not claim.evidence_refs:
            findings.append({"claim_id": claim.id, "status": "uncited", "detail": "No evidence refs."})
        if unknown := set(claim.evidence_refs) - known_refs:
            findings.append(
                {
                    "claim_id": claim.id,
                    "status": "uncited",
                    "detail": f"Unknown evidence refs: {sorted(unknown)}",
                }
            )
        if claim.id not in rendered_claims:
            findings.append(
                {"claim_id": claim.id, "status": "uncited", "detail": "Claim is not used by any paragraph."}
            )
        claim_paragraphs = [paragraph for paragraph in paragraphs if claim.id in paragraph.claim_ids]
        for qualifier in claim.qualifiers:
            if not any(qualifier in paragraph.qualifiers for paragraph in claim_paragraphs):
                findings.append(
                    {
                        "claim_id": claim.id,
                        "status": "missing_qualification",
                        "detail": f"Missing required qualification: {qualifier}",
                    }
                )
    for asset in plan.assets:
        if asset.id not in rendered_asset_ids:
            findings.append(
                {
                    "claim_id": asset.claim_ids[0] if asset.claim_ids else asset.id,
                    "status": "uncited",
                    "detail": f"Accepted asset {asset.id!r} was not rendered.",
                }
            )
    return findings


def _validate_audit_payload(
    payload: dict[str, object], plan: ManuscriptPlan
) -> dict[str, Any]:
    if not isinstance(payload.get("approved"), bool) or not isinstance(payload.get("findings"), list):
        raise ValueError("audit must return approved plus structured findings")
    findings = payload["findings"]
    known_claims = {claim.id for claim in plan.claims}
    for finding in findings:
        if not isinstance(finding, dict) or finding.get("claim_id") not in known_claims:
            raise ValueError("audit finding references an unknown claim")
    reviewed_claims = {str(finding["claim_id"]) for finding in findings}
    if reviewed_claims != known_claims:
        raise ValueError("audit must return one or more findings for every claim")
    has_rejection = any(finding.get("status") != "supported" for finding in findings)
    return {**payload, "approved": not has_rejection, "deterministic": False}
