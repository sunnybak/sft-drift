"""Grounded short-paper drafting and deterministic LaTeX rendering.

This module deliberately treats recorded result artifacts as the source of truth.  The
language model only writes digit-free prose around fixed tables/figures rendered by Python;
it cannot invent or alter a reported numerical result.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from belief_transfer.analysis import markdown, plots, tables
from belief_transfer.analysis.report import RESULTS_DIR
from belief_transfer.generation.llm import Client, Tool
from belief_transfer.schemas import (
    AssetBrief,
    Claim,
    DerivedFact,
    EvidenceRef,
    FloatPlacement,
    ManuscriptPlan,
    Paragraph,
    RenderedElement,
    SectionPlan,
    SourceMap,
    WriteupSpec,
    file_sha,
)

TEMPLATE_DIR = Path(__file__).with_name("templates")
PAPER_FILENAME = "paper.tex"
PDF_FILENAME = "paper.pdf"
EVIDENCE_FILENAME = "evidence.json"
DRAFT_FILENAME = "draft.json"
REVIEW_FILENAME = "review.json"
SYNTHESIS_FILENAME = "synthesis.json"
PLAN_FILENAME = "manuscript_plan.json"
ASSET_BRIEFS_FILENAME = "asset_briefs.json"
SOURCE_MAP_FILENAME = "source_map.json"
COMPILE_LOG_FILENAME = "compile.log"
REFERENCES_FILENAME = "references.bib"

_SUMMARY_FILES = (
    "choice_bench.yaml",
    "absorption.yaml",
    "sensitivity_summary.yaml",
    "belief_summary.yaml",
    "action_summary.yaml",
    "inference_summary.yaml",
)
_PROVENANCE_FILES = {*_SUMMARY_FILES, "trajectory.jsonl", "config.resolved.yaml", markdown.REPORT_FILENAME}
_SECTIONS = ("abstract", "introduction", "methods", "results", "limitations", "conclusion")
_FORBIDDEN_PROSE = re.compile(r"(\\|[${}])")
_NUMBER = re.compile(r"(?<![\w.])[+-]?\d+(?:\.\d+)?%?")
_SEMANTIC_ID = re.compile(r"^[a-z][a-z0-9_-]*$")
_META_DIRECTIVE = re.compile(
    r"\b(?:the paper should|do not|must be (?:analyzed|identified|described))\b",
    re.IGNORECASE,
)

_DRAFT_TOOL = Tool(
    name="write_short_paper",
    description="Write concise, grounded prose sections for a short research paper.",
    parameters={
        "type": "object",
        "properties": {
            section: {"type": "string"} for section in _SECTIONS
        }
        | {"evidence_ids": {"type": "array", "items": {"type": "string"}}},
        "required": [*_SECTIONS, "evidence_ids"],
        "additionalProperties": False,
    },
)

_REVIEW_TOOL = Tool(
    name="review_grounding",
    description="Check whether a draft is supported by the supplied evidence.",
    parameters={
        "type": "object",
        "properties": {
            "approved": {"type": "boolean"},
            "corrections": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["approved", "corrections"],
        "additionalProperties": False,
    },
)

_PLAN_TOOL = Tool(
    name="plan_grounded_manuscript",
    description="Plan claims, sections, and textual asset briefs from frozen synthesis facts.",
    parameters={
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "text": {"type": "string"},
                        "evidence_refs": {"type": "array", "items": {"type": "string"}},
                        "qualifiers": {"type": "array", "items": {"type": "string"}},
                        "empirical": {"type": "boolean"},
                    },
                    "required": ["id", "text", "evidence_refs", "qualifiers", "empirical"],
                    "additionalProperties": False,
                },
            },
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "claim_ids": {"type": "array", "items": {"type": "string"}},
                        "asset_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["id", "title", "claim_ids", "asset_ids"],
                    "additionalProperties": False,
                },
            },
            "assets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "question": {"type": "string"},
                        "claim_ids": {"type": "array", "items": {"type": "string"}},
                        "evidence_refs": {"type": "array", "items": {"type": "string"}},
                        "form": {
                            "type": "string",
                            "enum": ["ladder_table", "transfer_table", "trajectory_figure"],
                        },
                        "axes_or_columns": {"type": "array", "items": {"type": "string"}},
                        "placement": {
                            "type": "string",
                            "enum": ["methods", "results", "discussion", "limitations", "appendix"],
                        },
                        "takeaway": {"type": "string"},
                        "caption_outline": {"type": "string"},
                        "transformation": {
                            "type": "string",
                            "enum": ["identity", "declared_contrast", "trajectory"],
                        },
                    },
                    "required": [
                        "id",
                        "question",
                        "claim_ids",
                        "evidence_refs",
                        "form",
                        "axes_or_columns",
                        "placement",
                        "takeaway",
                        "caption_outline",
                        "transformation",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["claims", "sections", "assets"],
        "additionalProperties": False,
    },
)

_SECTION_TOOL = Tool(
    name="write_grounded_section",
    description="Write paragraphs for one validated manuscript section.",
    parameters={
        "type": "object",
        "properties": {
            "paragraphs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "text": {"type": "string"},
                        "claim_ids": {"type": "array", "items": {"type": "string"}},
                        "qualifiers": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["id", "text", "claim_ids", "qualifiers"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["paragraphs"],
        "additionalProperties": False,
    },
)

_AUDIT_TOOL = Tool(
    name="audit_grounded_manuscript",
    description="Audit every empirical claim against frozen facts and rendered assets.",
    parameters={
        "type": "object",
        "properties": {
            "approved": {"type": "boolean"},
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim_id": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["supported", "overstated", "missing_qualification", "contradictory", "uncited"],
                        },
                        "detail": {"type": "string"},
                    },
                    "required": ["claim_id", "status", "detail"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["approved", "findings"],
        "additionalProperties": False,
    },
)


def _load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = yaml.safe_load(path.read_text())
    return value if isinstance(value, dict) else None


def source_directory(experiment_id: str, run_id: str) -> Path:
    return RESULTS_DIR / experiment_id / run_id


def _artifact_path(experiment_id: str, run_id: str, filename: str) -> str:
    return str(Path("data") / "results" / experiment_id / run_id / filename)


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _leaf_pointers(value: Any, pointer: str = "") -> list[str]:
    if isinstance(value, dict):
        return [
            child
            for key, item in value.items()
            for child in _leaf_pointers(item, f"{pointer}/{_pointer_token(str(key))}")
        ]
    if isinstance(value, list):
        return [
            child
            for index, item in enumerate(value)
            for child in _leaf_pointers(item, f"{pointer}/{index}")
        ]
    return [pointer or "/"]


def _value_at_pointer(value: Any, pointer: str) -> Any:
    current = value
    if pointer == "/":
        return current
    for raw_token in pointer.lstrip("/").split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def evidence_references(evidence: dict[str, Any]) -> list[EvidenceRef]:
    """Enumerate exact summary fields plus whole-file trajectory provenance."""
    refs: list[EvidenceRef] = []
    for run_id, source in evidence["sources"].items():
        manifest = {item["filename"]: item for item in source["artifact_manifest"]}
        for filename, summary in source["summaries"].items():
            artifact = manifest[filename]
            for pointer in _leaf_pointers(summary):
                stable = f"{run_id}:{filename}:{pointer}"
                refs.append(
                    EvidenceRef(
                        id=stable,
                        artifact_path=artifact["path"],
                        sha256=artifact["sha256"],
                        pointer=pointer,
                        run_id=run_id,
                    )
                )
        resolved_config = source.get("resolved_config")
        if isinstance(resolved_config, dict) and "config.resolved.yaml" in manifest:
            artifact = manifest["config.resolved.yaml"]
            for pointer in _leaf_pointers(resolved_config):
                stable = f"{run_id}:config.resolved.yaml:{pointer}"
                refs.append(
                    EvidenceRef(
                        id=stable,
                        artifact_path=artifact["path"],
                        sha256=artifact["sha256"],
                        pointer=pointer,
                        run_id=run_id,
                    )
                )
        if "trajectory.jsonl" in manifest:
            artifact = manifest["trajectory.jsonl"]
            refs.append(
                EvidenceRef(
                    id=f"{run_id}:trajectory.jsonl:/",
                    artifact_path=artifact["path"],
                    sha256=artifact["sha256"],
                    pointer="/",
                    run_id=run_id,
                )
            )
    return refs


def verify_evidence_ref(ref: EvidenceRef, *, experiment_id: str) -> None:
    """Fail closed when a companion source map points at stale source bytes."""
    source = source_directory(experiment_id, ref.run_id) / Path(ref.artifact_path).name
    if not source.exists() or file_sha(source, length=64) != ref.sha256:
        raise ValueError(f"stale evidence reference {ref.id!r}")
    if source.suffix in {".yaml", ".yml"} and ref.pointer != "/":
        current: Any = yaml.safe_load(source.read_text())
        try:
            _value_at_pointer(current, ref.pointer)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid evidence pointer {ref.id!r}") from exc


def _authoring_context(sources: dict[str, Any], *, primary_reading: str, endpoint_absorption: str | None) -> dict[str, Any]:
    """Small, explicit project context for prose; measurements remain in source artifacts."""
    primary_config = sources[primary_reading].get("resolved_config") or {}
    experiment = primary_config.get("experiment") or {}
    belief = experiment.get("belief") or {}
    action = experiment.get("action") or {}
    return {
        "experiment": {
            "target_belief": belief.get("statement", ""),
            "downstream_action": action.get("description", ""),
        },
        "readings": {
            "primary_reading": primary_reading,
            "endpoint_absorption": endpoint_absorption,
        },
        "interpretation_rules": [
            "Treat the result as exploratory; state model, topic, seed count, and checkpoint scope only from recorded artifacts.",
            "Two-seed scope applies only to declared seed-paired contrast families; identify single-seed and instrument-specific readings separately.",
            "Absorption is held-out premise specialization, not a belief measure.",
            "Belief and action contrasts require their matched off-topic control netting; do not claim causal mediation.",
            "Raw belief/action checkpoint figures are diagnostic and are not netted transfer estimates.",
            "Fixed tables, not prose, are authoritative for numerical estimates and confidence intervals.",
        ],
    }


def collect_evidence(experiment_id: str, spec: WriteupSpec) -> dict[str, Any]:
    """Read declared result bundles without modifying their historical artifacts."""
    if not spec.source_runs:
        raise ValueError("writeup.source_runs must name at least one completed result run")
    primary_reading = spec.primary_reading or spec.source_runs[0]
    if primary_reading not in spec.source_runs:
        raise ValueError("writeup.primary_reading must also appear in writeup.source_runs")
    sources: dict[str, Any] = {}
    for run_id in spec.source_runs:
        directory = source_directory(experiment_id, run_id)
        if not directory.exists():
            raise FileNotFoundError(f"writeup source run {run_id!r} has no results at {directory}")
        summaries = {
            filename: value
            for filename in _SUMMARY_FILES
            if (value := _load_yaml(directory / filename)) is not None
        }
        sources[run_id] = {
            "run_id": run_id,
            "directory": str(Path("data") / "results" / experiment_id / run_id),
            # A source report may not exist yet (for example, a locally copied fixture).
            # Render an in-memory view in that case; do not rewrite a historical source run.
            "report": markdown.REPORT_FILENAME,
            "report_markdown": (directory / markdown.REPORT_FILENAME).read_text()
            if (directory / markdown.REPORT_FILENAME).exists()
            else markdown.render_report(directory),
            "summaries": summaries,
            "resolved_config": _load_yaml(directory / "config.resolved.yaml"),
            "figures": [path.name for path in sorted(directory.glob("*.png"))],
            "artifact_manifest": [
                {
                    "filename": path.name,
                    "path": _artifact_path(experiment_id, run_id, path.name),
                    "sha256": file_sha(path, length=64),
                }
                for path in sorted(directory.iterdir())
                if path.is_file() and path.name in _PROVENANCE_FILES
            ],
        }
        for filename, summary in summaries.items():
            declared_run = summary.get("run_id")
            if declared_run is not None and declared_run != run_id:
                raise ValueError(
                    f"{run_id}/{filename} declares run_id {declared_run!r}, not its source directory"
                )
    absorption_runs = [run_id for run_id, source in sources.items() if "absorption.yaml" in source["summaries"]]
    endpoint_absorption = spec.trajectory_run if spec.trajectory_run in absorption_runs else None
    if endpoint_absorption is None and len(absorption_runs) == 1:
        endpoint_absorption = absorption_runs[0]
    evidence = {
        "experiment": experiment_id,
        "intended_claim": spec.intended_claim,
        "primary_reading": primary_reading,
        "endpoint_absorption": endpoint_absorption,
        "sources": sources,
    }
    evidence["authoring_context"] = _authoring_context(
        sources, primary_reading=primary_reading, endpoint_absorption=endpoint_absorption
    )
    hashes = {
        (run_id, artifact["filename"]): artifact["sha256"]
        for run_id, source in sources.items()
        for artifact in source["artifact_manifest"]
    }
    evidence["table_manifest"] = [
        {
            "id": table.id,
            "source_run": table.source.run_id,
            "artifact": table.source.artifact,
            "sha256": hashes.get((table.source.run_id, table.source.artifact)),
        }
        for table in _result_tables(evidence)
    ]
    evidence["evidence_refs"] = {
        ref.id: ref.model_dump()
        for ref in evidence_references(evidence)
    }
    return evidence


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


def write_json(value: Any, path: Path) -> Path:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return path


def copy_trajectory_figures(
    evidence: dict[str, Any], *, trajectory_run: str | None, output_dir: Path
) -> list[dict[str, str]]:
    """Render paper figures from declared tidy trajectory rows, leaving source runs untouched."""
    if trajectory_run is None:
        return []
    sources = evidence["sources"]
    if trajectory_run not in sources:
        raise ValueError("writeup.trajectory_run must also appear in writeup.source_runs")
    source = source_directory(str(evidence["experiment"]), trajectory_run)
    if not (source / "trajectory.jsonl").exists():
        raise FileNotFoundError(f"{trajectory_run!r} has no trajectory.jsonl provenance artifact")
    trajectory_rows = [
        json.loads(line)
        for line in (source / "trajectory.jsonl").read_text().splitlines()
        if line.strip()
    ]
    checkpoints = sorted({str(row["step"]) for row in trajectory_rows if "step" in row})
    instruments = sorted({str(row["eval_type"]) for row in trajectory_rows if "eval_type" in row})
    coverage = ", ".join(checkpoints) or "recorded checkpoints"
    instrument_text = ", ".join(instruments) or "recorded instruments"
    target = output_dir / "figures"
    target.mkdir(parents=True, exist_ok=True)
    figures = plots.plot_trajectory(source / "trajectory.jsonl", target)
    if not figures:
        raise ValueError(f"{trajectory_run!r} trajectory rows contain no plottable instruments")
    copied = []
    for figure in figures:
        figure_description = (
            "belief and action trajectories split by polarity"
            if figure.name == "polarity_trajectories.png"
            else figure.stem.replace("_", " ")
        )
        copied.append(
            {
                "path": str(figure.relative_to(output_dir)),
                "caption": (
                    f"{figure_description}; run {trajectory_run}; "
                    f"checkpoints {coverage}; instruments {instrument_text}"
                ),
                "source_run": trajectory_run,
            }
        )
    return copied


def write_evidence(evidence: dict[str, Any], path: Path) -> Path:
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    return path


def _planning_prompt(evidence: dict[str, Any], synthesis: dict[str, Any], spec: WriteupSpec) -> str:
    planning_synthesis = {
        "experiment": synthesis.get("experiment"),
        "facts": synthesis.get("facts", []),
        "evidence_ref_ids": sorted(synthesis.get("evidence_refs", {})),
        "asset_evidence_ref_ids": sorted(synthesis.get("asset_evidence", {})),
        "context_evidence_ref_ids": sorted(synthesis.get("context_evidence", {})),
        "context_values": synthesis.get("context_values", {}),
    }
    return f"""Plan a concise research paper from the frozen facts below.

Compiler protocol version: 10.
Return a claim graph, ordered sections, and textual asset briefs only. Do not write prose.
Empirical claims must cite exact evidence-ref ids. Put all numerical values in deterministic
assets, not claim text. Use only supported asset forms and identity transformations. Preserve
every recorded qualification. Scope/checkpoint claims must cite context_evidence, not a
trajectory file, and must include exact experiment-id, model, seed, and checkpoint refs for
every scope component they assert. Use context_values to avoid claiming blank or unavailable
fields. Statements copied from interpretation_rules are methodology constraints: mark them
non-empirical and do not cite a trajectory solely to support them. Describe explicit stance
as a recorded positive-control contrast, not as general belief transfer.
Never describe the whole evidence bundle as uniformly two-seed: apply two-seed replication
only to declared seed-paired contrast families and label other readings separately.
Keep empirical claims atomic by declared contrast. You may combine a homogeneous seed pair,
but never combine belief, descriptive-inference, action, or unintervalled positive-control
families into one empirical claim.
Use at most {spec.max_main_tables} main-text tables and {spec.max_main_figures}
main-text figures; place any additional accepted assets in the appendix.
Required sections: {spec.required_sections}.

Contribution goals (not evidence):
{json.dumps(spec.contribution_goals, indent=2)}

Project context:
{json.dumps(evidence["authoring_context"], indent=2, sort_keys=True)}

Frozen synthesis:
{json.dumps(planning_synthesis, indent=2, sort_keys=True)}
"""


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
        unknown_numbers = [
            number
            for number in _NUMBER.findall(claim.text)
            if number.removesuffix("%") not in supported_text
        ]
        if unknown_numbers:
            raise ValueError(f"claim {claim.id!r} contains unsupported numbers: {unknown_numbers}")

    allowed_transformations = {
        "ladder_table": {"identity", "declared_contrast"},
        "transfer_table": {"identity"},
        "trajectory_figure": {"identity", "trajectory"},
    }
    signatures: set[tuple[str, tuple[str, ...]]] = set()
    proposed_asset_ids = set(asset_ids)
    accepted_assets: list[AssetBrief] = []
    rejected_assets: list[dict[str, str]] = []
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
        if asset.placement not in {"methods", "results", "discussion", "limitations", "appendix"}:
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
        raise ValueError("asset plan exceeds configured main-text limits")

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


async def plan_manuscript(
    client: Client,
    evidence: dict[str, Any],
    synthesis: dict[str, Any],
    spec: WriteupSpec,
    *,
    force: bool,
) -> ManuscriptPlan:
    prompt = _planning_prompt(evidence, synthesis, spec)
    payload = await client.complete_tool(prompt, _PLAN_TOOL, override_cache=force)
    for attempt in range(3):
        try:
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
        except ValueError as exc:
            if attempt == 2:
                raise
            prompt += (
                "\n\nThe previous plan was deterministically rejected: "
                + str(exc)
                + "\nReturn a corrected complete plan. Copy exact evidence ids from the "
                "frozen synthesis and place each asset in exactly one section. Include "
                "each required section exactly once using these exact ids: "
                + ", ".join(spec.required_sections)
                + f". Respect the limit of {spec.max_main_tables} main-text tables and "
                + f"{spec.max_main_figures} main-text figures; route extras to appendix."
            )
            payload = await client.complete_tool(
                prompt, _PLAN_TOOL, override_cache=force
            )
    raise AssertionError("unreachable")


def file_sha_from_json(value: Any) -> str:
    import hashlib

    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _facts_for_refs(synthesis: dict[str, Any], refs: set[str]) -> list[dict[str, Any]]:
    return [
        fact
        for fact in synthesis.get("facts", [])
        if refs.intersection(str(ref) for ref in fact.get("evidence_refs", []))
    ]


def _synthesis_excerpt(synthesis: dict[str, Any], refs: set[str]) -> dict[str, Any]:
    """Return only the frozen facts and provenance a section's claims cite."""
    return {
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
    }


def _section_prompt(
    section: SectionPlan,
    plan: ManuscriptPlan,
    evidence: dict[str, Any],
    synthesis: dict[str, Any],
    *,
    corrections: list[str] | None = None,
    completed_sections: list[SectionPlan] | None = None,
) -> str:
    claims = {claim.id: claim.model_dump(mode="json") for claim in plan.claims if claim.id in section.claim_ids}
    claim_refs = {
        ref
        for claim in plan.claims
        if claim.id in section.claim_ids
        for ref in claim.evidence_refs
    }
    relevant_synthesis = _synthesis_excerpt(synthesis, claim_refs)
    correction_text = "\nCorrections:\n" + "\n".join(corrections) if corrections else ""
    return f"""Write only the {section.title} section as concise paragraphs.

Each paragraph must retain stable claim_ids and use only the accepted claims below. Copy
every preserved qualifier verbatim into the paragraph's qualifiers metadata, but integrate
its substance into natural research prose rather than copying directive wording. Never
address the writer or say "the paper should", "do not", or that something "must be"
analyzed, identified, or described. Do not introduce a new empirical result. Preserve
qualifications in prose. Do not use LaTeX or markdown.
Numerical empirical estimates belong in deterministic assets, not prose. Exact configured
model and checkpoint identifiers may appear when supplied in context_values. Avoid long
internal arm run identifiers in prose; their exact values remain in provenance.{correction_text}

Accepted claims:
{json.dumps(claims, indent=2, sort_keys=True)}

Relevant frozen facts:
{json.dumps(relevant_synthesis, indent=2, sort_keys=True)}

Completed earlier sections for coherence:
{json.dumps([section.model_dump(mode="json") for section in completed_sections or []], indent=2)}

Interpretation rules:
{json.dumps(evidence["authoring_context"]["interpretation_rules"], indent=2)}
"""


def validate_section_payload(
    payload: dict[str, Any], section: SectionPlan, plan: ManuscriptPlan, synthesis: dict[str, Any]
) -> list[Paragraph]:
    paragraphs = [Paragraph.model_validate(item) for item in payload.get("paragraphs", [])]
    if not paragraphs:
        raise ValueError(f"section {section.id!r} must contain at least one paragraph")
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
        if _FORBIDDEN_PROSE.search(paragraph.text):
            raise ValueError(f"paragraph {paragraph.id!r} contains raw LaTeX syntax")
        if _META_DIRECTIVE.search(paragraph.text):
            raise ValueError(f"paragraph {paragraph.id!r} contains writer-facing directives")
        paragraph_refs = {
            ref
            for claim_id in paragraph.claim_ids
            for ref in claims[claim_id].evidence_refs
        }
        supported_text = json.dumps(
            _synthesis_excerpt(synthesis, paragraph_refs), sort_keys=True
        )
        unknown_numbers = [
            number
            for number in _NUMBER.findall(paragraph.text)
            if number.removesuffix("%") not in supported_text
        ]
        if unknown_numbers:
            raise ValueError(f"paragraph {paragraph.id!r} contains unsupported numbers: {unknown_numbers}")
    return paragraphs


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
    payload = await client.complete_tool(
        prompt, _SECTION_TOOL, override_cache=force
    )
    for attempt in range(3):
        try:
            paragraphs = validate_section_payload(payload, section, plan, synthesis)
            break
        except ValueError as exc:
            if attempt == 2:
                raise
            prompt += (
                "\n\nThe previous section was deterministically rejected: "
                + str(exc)
                + "\nReturn a corrected complete section using only the accepted claims, "
                "their exact qualifiers, and the supplied evidence."
            )
            payload = await client.complete_tool(
                prompt, _SECTION_TOOL, override_cache=force
            )
    else:
        raise AssertionError("unreachable")
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


def _prompt(evidence: dict[str, Any], corrections: list[str] | None = None) -> str:
    source_reports = "\n\n".join(
        f"RUN {run_id}\n{source['report_markdown']}"
        for run_id, source in evidence["sources"].items()
    )
    correction_text = f"\nReviewer corrections:\n{chr(10).join(corrections)}" if corrections else ""
    return f"""Write a concise research-paper draft from the recorded reports below.

The intended claim is: {evidence["intended_claim"]}

Project and interpretation context:
{json.dumps(evidence["authoring_context"], indent=2, sort_keys=True)}

Use only the listed run ids as evidence IDs. Do not state numerical values in prose: fixed
tables and figure captions carry them. Do not use LaTeX, citations, markdown, dollar signs,
or placeholders. Follow the interpretation rules above. State limitations directly, especially
any caveats recorded in the reports.
{correction_text}

Recorded reports:
{source_reports}
"""


def validate_draft(payload: dict[str, object], evidence: dict[str, Any]) -> dict[str, Any]:
    """Reject model output that could change the experimental record."""
    required = set(_SECTIONS) | {"evidence_ids"}
    if set(payload) != required:
        raise ValueError(f"draft fields must be exactly {sorted(required)}")
    for section in _SECTIONS:
        text = payload[section]
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"draft section {section!r} must be non-empty text")
        if _FORBIDDEN_PROSE.search(text):
            raise ValueError(f"draft section {section!r} contains raw LaTeX syntax")
        # Prose may need to name a configured checkpoint (for example, step 24), but it
        # cannot introduce a numeric value absent from the evidence packet. Fixed result
        # tables remain the normal location for estimates and confidence intervals.
        evidence_text = json.dumps(evidence, sort_keys=True)
        unknown_numbers = [
            value for value in _NUMBER.findall(text) if value.removesuffix("%") not in evidence_text
        ]
        if unknown_numbers:
            raise ValueError(f"draft section {section!r} contains unsupported numbers: {unknown_numbers}")
    identifiers = payload["evidence_ids"]
    if not isinstance(identifiers, list) or not all(isinstance(value, str) for value in identifiers):
        raise ValueError("draft evidence_ids must be a list of source run ids")
    # The prompt labels each report as `RUN <id>` for readability; normalize that display
    # label back to the stable run-id key before applying the grounding check.
    identifiers = [value.removeprefix("RUN ").strip() for value in identifiers]
    unknown = set(identifiers) - set(evidence["sources"])
    if unknown:
        raise ValueError(f"draft references undeclared evidence ids: {sorted(unknown)}")
    if not identifiers:
        raise ValueError("draft must reference at least one source run")
    return {**{key: payload[key] for key in _SECTIONS}, "evidence_ids": identifiers}


async def draft_sections(
    client: Client, evidence: dict[str, Any], *, force: bool, corrections: list[str] | None = None
) -> dict[str, Any]:
    payload = await client.complete_tool(
        _prompt(evidence, corrections),
        _DRAFT_TOOL,
        override_cache=force,
    )
    try:
        return validate_draft(payload, evidence)
    except ValueError as exc:
        # A failed schema/grounding check must be visible to the authoring model. This is
        # intentionally one bounded retry rather than accepting a malformed draft or
        # entering an open-ended author/reviewer loop.
        retry_payload = await client.complete_tool(
            _prompt(evidence, [f"Your previous draft was rejected: {exc}. Rewrite every section to comply."]),
            _DRAFT_TOOL,
            override_cache=force,
        )
        return validate_draft(retry_payload, evidence)


async def review_draft(client: Client, evidence: dict[str, Any], draft: dict[str, Any], *, force: bool) -> dict[str, Any]:
    prompt = f"""Check this paper prose against its recorded evidence. It must not overclaim,
omit material limitations, or refer to a source run that was not declared.

Evidence IDs: {sorted(evidence["sources"])}
Intended claim: {evidence["intended_claim"]}
Draft: {json.dumps(draft, sort_keys=True)}
"""
    payload = await client.complete_tool(prompt, _REVIEW_TOOL, override_cache=force)
    if not isinstance(payload.get("approved"), bool) or not isinstance(payload.get("corrections"), list):
        raise ValueError("review must return approved plus a corrections list")
    if not all(isinstance(item, str) for item in payload["corrections"]):
        raise ValueError("review corrections must be text")
    return {"approved": payload["approved"], "corrections": payload["corrections"]}


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
    payload = await client.complete_tool(prompt, _AUDIT_TOOL, override_cache=force)
    for attempt in range(3):
        try:
            return _validate_audit_payload(payload, plan)
        except ValueError as exc:
            if attempt == 2:
                raise
            prompt += (
                "\n\nThe previous audit was structurally rejected: "
                + str(exc)
                + "\nReturn a complete corrected audit using only these exact claim ids: "
                + ", ".join(claim.id for claim in plan.claims)
                + '. Set approved=true exactly when every finding is "supported"; '
                + "otherwise set approved=false."
            )
            payload = await client.complete_tool(
                prompt, _AUDIT_TOOL, override_cache=force
            )
    raise AssertionError("unreachable")


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


def build_assets(
    plan: ManuscriptPlan,
    evidence: dict[str, Any],
    synthesis: dict[str, Any],
    figures: list[dict[str, str]],
) -> tuple[dict[str, tables.ResultTable], dict[str, dict[str, str]], list[dict[str, Any]]]:
    """Dispatch accepted briefs to bounded deterministic builders."""
    built_tables: dict[str, tables.ResultTable] = {}
    built_figures: dict[str, dict[str, str]] = {}
    manifest: list[dict[str, Any]] = []
    available_tables = _result_tables(evidence)
    for brief in plan.assets:
        if brief.form == "ladder_table":
            table = tables.ladder_table(synthesis)
            built_tables[brief.id] = table
            manifest.append(
                {
                    "id": brief.id,
                    "kind": "table",
                    "builder": "ladder_table",
                    "evidence_refs": brief.evidence_refs,
                }
            )
        elif brief.form == "transfer_table":
            matching = [
                table
                for table in available_tables
                if any(
                    ref.startswith(f"{table.source.run_id}:{table.source.artifact}:")
                    for ref in brief.evidence_refs
                )
            ]
            if len(matching) != 1:
                raise ValueError(
                    f"asset {brief.id!r} must resolve to exactly one recorded transfer table"
                )
            built_tables[brief.id] = matching[0]
            manifest.append(
                {
                    "id": brief.id,
                    "kind": "table",
                    "builder": "transfer_table",
                    "evidence_refs": brief.evidence_refs,
                }
            )
        else:
            if not figures:
                raise ValueError(f"asset {brief.id!r} requests a trajectory figure but none was built")
            figure = figures[0]
            built_figures[brief.id] = figure
            manifest.append(
                {
                    "id": brief.id,
                    "kind": "figure",
                    "builder": "trajectory_figure",
                    "evidence_refs": brief.evidence_refs,
                    "path": figure["path"],
                }
            )
    return built_tables, built_figures, manifest


def build_source_map(
    plan: ManuscriptPlan,
    evidence: dict[str, Any],
    built_tables: dict[str, tables.ResultTable],
    built_figures: dict[str, dict[str, str]],
) -> SourceMap:
    """Build and validate both directions of companion provenance."""
    rendered: dict[str, RenderedElement] = {}

    def add(element: RenderedElement) -> None:
        if element.id in rendered:
            raise ValueError(f"duplicate rendered element id {element.id!r}")
        if unknown := set(element.evidence_refs) - set(evidence["evidence_refs"]):
            raise ValueError(f"rendered element {element.id!r} has unknown evidence refs: {sorted(unknown)}")
        rendered[element.id] = element

    claims = {claim.id: claim for claim in plan.claims}
    assets = {asset.id: asset for asset in plan.assets}
    for claim in plan.claims:
        add(
            RenderedElement(
                id=f"claim:{claim.id}",
                kind="claim",
                evidence_refs=claim.evidence_refs,
                location=f"claim:{claim.id}",
            )
        )
    for section in plan.sections:
        for paragraph in section.paragraphs:
            refs = list(
                dict.fromkeys(
                    ref for claim_id in paragraph.claim_ids for ref in claims[claim_id].evidence_refs
                )
            )
            add(
                RenderedElement(
                    id=f"paragraph:{paragraph.id}",
                    kind="paragraph",
                    evidence_refs=refs,
                    location=f"section:{section.id}",
                )
            )
    for asset_id, table in built_tables.items():
        refs = assets[asset_id].evidence_refs
        add(
            RenderedElement(
                id=f"table:{asset_id}",
                kind="table",
                evidence_refs=refs,
                location=f"tab:{table.id}",
            )
        )
        for row_index, row in enumerate(table.rows):
            row_id = f"table:{asset_id}:row:{row_index}"
            row_refs = (
                list(dict.fromkeys(ref for cell in table.cell_refs[row_index] for ref in cell))
                if table.cell_refs
                else refs
            )
            add(RenderedElement(id=row_id, kind="table_row", evidence_refs=row_refs))
            for cell_index, _ in enumerate(row):
                cell_refs = (
                    list(table.cell_refs[row_index][cell_index])
                    if table.cell_refs
                    else refs
                )
                add(
                    RenderedElement(
                        id=f"{row_id}:cell:{cell_index}",
                        kind="table_cell",
                        evidence_refs=cell_refs,
                    )
                )
    for asset_id in built_figures:
        refs = assets[asset_id].evidence_refs
        add(
            RenderedElement(
                id=f"figure:{asset_id}",
                kind="figure",
                evidence_refs=refs,
                location=f"fig:{asset_id}",
            )
        )
        add(
            RenderedElement(
                id=f"figure:{asset_id}:series:all",
                kind="figure_series",
                evidence_refs=refs,
            )
        )
    used_refs = {ref for element in rendered.values() for ref in element.evidence_refs}
    evidence_models = {
        ref_id: EvidenceRef.model_validate(evidence["evidence_refs"][ref_id])
        for ref_id in sorted(used_refs)
    }
    source_uses = {
        ref_id: sorted(
            element.id for element in rendered.values() if ref_id in element.evidence_refs
        )
        for ref_id in evidence_models
    }
    result = SourceMap(evidence=evidence_models, rendered=rendered, source_uses=source_uses)
    if any(not uses for uses in result.source_uses.values()):
        raise ValueError("source map contains an evidence ref with no reverse use")
    return result


def _escape(value: str) -> str:
    return (
        value.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


def _result_tables(evidence: dict[str, Any]) -> list[tables.ResultTable]:
    """Fixed, provenance-carrying tables in the paper's declared reading order."""
    result: list[tables.ResultTable] = []
    sources = evidence["sources"]
    endpoint = evidence.get("endpoint_absorption")
    primary = evidence["primary_reading"]

    if endpoint and (choice := sources[endpoint]["summaries"].get("choice_bench.yaml")):
        result.append(tables.choice_gate_table(choice))
    if primary != endpoint and (choice := sources[primary]["summaries"].get("choice_bench.yaml")):
        result.append(tables.choice_gate_table(choice))
    if endpoint and (absorption := sources[endpoint]["summaries"].get("absorption.yaml")):
        table = tables.absorption_table(absorption)
        qualification = (
            " Absorption measures premise specialization, not belief."
            " No absorption reading exists for the primary checkpoint."
            if primary != endpoint
            else " Absorption measures premise specialization, not belief."
        )
        if choice := sources[endpoint]["summaries"].get("choice_bench.yaml"):
            failed_controls = [
                control
                for _, control in absorption["metrics"]["net_pairs"]
                if control in choice["metrics"]["choice"]
                and not choice["metrics"]["choice"][control]["passed"]
            ]
            if failed_controls:
                qualification += (
                    " Estimates relying on failed control arm(s) "
                    + ", ".join(failed_controls)
                    + " are displayed but qualified."
                )
        result.append(replace(table, note=table.note + qualification))

    for run_id, source in sources.items():
        for filename in (
            "belief_summary.yaml",
            "action_summary.yaml",
            "inference_summary.yaml",
            "sensitivity_summary.yaml",
        ):
            if summary := source["summaries"].get(filename):
                result.append(tables.transfer_table(summary, source_run=run_id, artifact=filename))
    return result


def _latex_table_model(table: tables.ResultTable) -> dict[str, Any]:
    model = tables.latex_table(table)
    return {
        **model,
        "heading": _escape(table.heading),
        "columns": [_escape(column) for column in table.columns],
        "rows": [
            [
                {
                    "text": _escape(cell["text"]),
                    "bold": cell["bold"],
                    "bold_text": _escape(cell["bold_text"]) if cell["bold_text"] else None,
                }
                for cell in row
            ]
            for row in model["rows"]
        ],
        "caption": _escape(table.caption),
        "note": _escape(table.note),
        "source": {
            "run_id": _escape(table.source.run_id),
            "artifact": _escape(table.source.artifact),
            "checkpoint": _escape(table.source.checkpoint),
        },
    }


def render_latex(
    *,
    output_dir: Path,
    spec: WriteupSpec,
    evidence: dict[str, Any],
    draft: dict[str, Any],
    figures: list[dict[str, str]],
) -> Path:
    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    template = environment.get_template(spec.template)
    rendered = template.render(
        legacy=True,
        title=_escape(spec.title),
        authors=", ".join(_escape(author) for author in spec.authors) or "Anonymous",
        sections={name: _escape(draft[name]) for name in _SECTIONS},
        figures=[
            {**figure, "caption": _escape(figure["caption"]), "source_run": _escape(figure["source_run"])}
            for figure in figures
        ],
        tables=[_latex_table_model(table) for table in _result_tables(evidence)],
        references_bib=spec.references_bib,
    )
    path = output_dir / PAPER_FILENAME
    path.write_text(rendered)
    return path


def render_manuscript_latex(
    *,
    output_dir: Path,
    spec: WriteupSpec,
    plan: ManuscriptPlan,
    built_tables: dict[str, tables.ResultTable],
    built_figures: dict[str, dict[str, str]],
) -> Path:
    """Render validated section/float order; LaTeX owns no selection logic."""
    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    assets = {asset.id: asset for asset in plan.assets}
    sections: list[dict[str, Any]] = []
    appendix: list[dict[str, Any]] = []
    for section in plan.sections:
        placements = {placement.after_paragraph_id: [] for placement in section.floats}
        for placement in section.floats:
            block = (
                {"kind": "table", "id": placement.asset_id, "table": _latex_table_model(built_tables[placement.asset_id])}
                if placement.asset_id in built_tables
                else {
                    "kind": "figure",
                    "id": placement.asset_id,
                    "figure": {
                        **built_figures[placement.asset_id],
                        "caption": _escape(assets[placement.asset_id].caption_outline),
                    },
                }
            )
            if placement.appendix:
                appendix.append(block)
            else:
                placements.setdefault(placement.after_paragraph_id, []).append(block)
        blocks: list[dict[str, Any]] = []
        for paragraph in section.paragraphs:
            blocks.append(
                {
                    "kind": "paragraph",
                    "id": paragraph.id,
                    "text": _escape(paragraph.text),
                }
            )
            blocks.extend(placements.get(paragraph.id, []))
        sections.append({"id": section.id, "title": _escape(section.title), "blocks": blocks})
    rendered = environment.get_template(spec.template).render(
        legacy=False,
        title=_escape(spec.title),
        authors=", ".join(_escape(author) for author in spec.authors) or "Anonymous",
        manuscript_sections=sections,
        appendix=appendix,
        references_bib=bool(spec.references_bib or spec.bibliography_path),
    )
    path = output_dir / PAPER_FILENAME
    path.write_text(rendered)
    return path


def compile_latex(tex_path: Path, *, timeout: int = 180) -> tuple[Path, Path]:
    """Compile with tectonic; callers choose whether missing toolchain is fatal."""
    try:
        completed = subprocess.run(
            ["tectonic", "--outdir", str(tex_path.parent), str(tex_path)],
            cwd=tex_path.parent,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("tectonic is required to compile a writeup; install it or set writeup.compile_pdf=false") from exc
    log_path = tex_path.parent / COMPILE_LOG_FILENAME
    log_path.write_text(completed.stdout + completed.stderr)
    if completed.returncode:
        raise RuntimeError(f"tectonic failed; see {log_path}")
    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"tectonic succeeded but did not write {pdf_path}")
    return pdf_path, log_path
