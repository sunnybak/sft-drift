"""Freezing the quantities a manuscript may quote.

The synthesis is the boundary between "what was measured" and "what may be written": every
fact it declares carries the evidence refs it was read from, and nothing downstream may
introduce a number that is not here. Derivations are declared, never inferred, so a ratio in
a paper is traceable to the two estimates it divides.
"""

from __future__ import annotations

from typing import Any

from belief_transfer.schemas import DerivedFact, WriteupSpec

from belief_transfer.analysis.writeup.evidence import _pointer_token, _value_at_pointer


def _ref_id(run_id: str, artifact: str, pointer: str) -> str:
    return f"{run_id}:{artifact}:{pointer}"


def _arm_reading_is_licensed(source: dict[str, Any], arms: list[str]) -> bool:
    choice = source["summaries"].get("choice_bench.yaml")
    if not choice:
        return True
    readings = choice.get("metrics", {}).get("choice", {})
    return all(arm not in readings or bool(readings[arm].get("passed")) for arm in arms)


def _magnitude(value: float) -> str:
    absolute = abs(value)
    if absolute < 0.02:
        return "near_zero"
    if absolute < 0.1:
        return "small"
    if absolute < 0.3:
        return "moderate"
    return "large"


def build_synthesis(evidence: dict[str, Any], spec: WriteupSpec) -> dict[str, Any]:
    """Select declared facts from summaries; derive only explicitly declared arm contrasts."""
    known_refs = evidence["evidence_refs"]
    facts: list[DerivedFact] = []
    for contrast in spec.contrasts:
        if contrast.run_id not in evidence["sources"]:
            raise ValueError(f"contrast {contrast.id!r} references undeclared run {contrast.run_id!r}")
        source = evidence["sources"][contrast.run_id]
        summary = source["summaries"].get(contrast.artifact)
        if not isinstance(summary, dict):
            if contrast.required:
                raise ValueError(
                    f"contrast {contrast.id!r} requires missing {contrast.run_id}/{contrast.artifact}"
                )
            continue
        if any(fact.id == contrast.id for fact in facts):
            raise ValueError(f"duplicate contrast id {contrast.id!r}")

        if contrast.positive_arm is None:
            entry = summary.get(contrast.quantity)
            if not isinstance(entry, dict) or "delta" not in entry:
                raise ValueError(
                    f"contrast {contrast.id!r} cannot select {contrast.quantity!r} "
                    f"from {contrast.run_id}/{contrast.artifact}"
                )
            pointer = f"/{_pointer_token(contrast.quantity)}"
            ref_ids = [
                _ref_id(contrast.run_id, contrast.artifact, f"{pointer}/delta"),
                _ref_id(contrast.run_id, contrast.artifact, f"{pointer}/ci95/0"),
                _ref_id(contrast.run_id, contrast.artifact, f"{pointer}/ci95/1"),
            ]
            facts.append(
                DerivedFact(
                    id=contrast.id,
                    label=contrast.label,
                    value=float(entry["delta"]),
                    ci95=(float(entry["ci95"][0]), float(entry["ci95"][1])),
                    excludes_zero=bool(entry.get("excludes_zero")),
                    evidence_refs=ref_ids,
                    qualification=contrast.qualification,
                    magnitude=_magnitude(float(entry["delta"])),
                )
            )
            continue

        arms = [
            contrast.positive_arm,
            contrast.negative_arm,
            contrast.control_positive_arm,
            contrast.control_negative_arm,
        ]
        if any(arm is None for arm in arms):
            raise ValueError(
                f"derived contrast {contrast.id!r} needs positive, negative, and both control arms"
            )
        named_arms = [str(arm) for arm in arms]
        if not _arm_reading_is_licensed(source, named_arms):
            raise ValueError(f"contrast {contrast.id!r} depends on an arm that failed choice_bench")
        missing = [arm for arm in named_arms if arm not in summary.get("arms", {})]
        if missing:
            raise ValueError(f"contrast {contrast.id!r} is missing arms {missing}")
        scores = [float(summary["arms"][arm]["score"]) for arm in named_arms]
        value = (scores[0] - scores[1]) - (scores[2] - scores[3])
        ref_ids = [
            _ref_id(contrast.run_id, contrast.artifact, f"/arms/{_pointer_token(arm)}/score")
            for arm in named_arms
        ]
        facts.append(
            DerivedFact(
                id=contrast.id,
                label=contrast.label,
                value=value,
                evidence_refs=ref_ids,
                derivation=f"({named_arms[0]} - {named_arms[1]}) - ({named_arms[2]} - {named_arms[3]})",
                qualification=(
                    contrast.qualification
                    + (" " if contrast.qualification else "")
                    + "Point estimate derived from recorded arm scores; no interval is inferred."
                ),
                magnitude=_magnitude(value),
            )
        )
    unknown_refs = {
        ref_id for fact in facts for ref_id in fact.evidence_refs if ref_id not in known_refs
    }
    if unknown_refs:
        raise ValueError(f"synthesis produced unknown evidence refs: {sorted(unknown_refs)}")
    context_evidence = {
        ref_id: ref
        for ref_id, ref in known_refs.items()
        if ":config.resolved.yaml:" in ref_id
        and any(
            token in ref["pointer"]
            for token in (
                "/run_id",
                "/experiment/id",
                "/training/model",
                "/training/sft/seed",
                "/checkpoint",
            )
        )
    }
    context_values = {
        ref_id: _value_at_pointer(
            evidence["sources"][str(ref["run_id"])]["resolved_config"],
            str(ref["pointer"]),
        )
        for ref_id, ref in context_evidence.items()
    }
    return {
        "experiment": evidence["experiment"],
        "facts": [fact.model_dump(mode="json") for fact in facts],
        "evidence_refs": {
            ref_id: known_refs[ref_id]
            for fact in facts
            for ref_id in fact.evidence_refs
        },
        "asset_evidence": {
            ref_id: ref
            for ref_id, ref in known_refs.items()
            if ref_id.endswith(":trajectory.jsonl:/")
        },
        "context_evidence": context_evidence,
        "context_values": context_values,
    }
