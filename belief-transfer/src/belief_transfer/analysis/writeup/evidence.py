"""Reading recorded result bundles, and the provenance that makes them citable.

Everything a paper is allowed to assert enters through here. The functions in this module
only read `data/results/`; none of them writes into a historical run directory, because a
source run is an experimental artifact and a writeup is a reader of it.

`RESULTS_DIR` is a module global rather than a parameter so that one place decides where
evidence comes from. Tests point it at a fixture tree by patching it HERE -- patching it on
the `writeup` package would set an attribute nothing reads.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from belief_transfer.analysis import markdown, tables
from belief_transfer.analysis.report import RESULTS_DIR
from belief_transfer.schemas import (
    EvidenceRef,
    ManuscriptPlan,
    RenderedElement,
    SourceMap,
    WriteupSpec,
    file_sha,
)


EVIDENCE_FILENAME = "evidence.json"


DRAFT_FILENAME = "draft.json"


REVIEW_FILENAME = "review.json"


SYNTHESIS_FILENAME = "synthesis.json"


PLAN_FILENAME = "manuscript_plan.json"


ASSET_BRIEFS_FILENAME = "asset_briefs.json"


SOURCE_MAP_FILENAME = "source_map.json"


REFERENCES_FILENAME = "references.bib"


_SUMMARY_FILES = (
    "choice_bench.yaml",
    "absorption.yaml",
    "sensitivity_summary.yaml",
    "belief_summary.yaml",
    "action_summary.yaml",
    "inference_summary.yaml",
    # Added 2026-08-23. The attributable-fraction sweep is a different KIND of reading from
    # the five above -- it is a removal-and-retrain quantity, not a suite score -- but it
    # carries the same `{delta, ci95, excludes_zero}` shape a ContrastSpec selects, so
    # citing it needs a filename here and nothing else. Deliberately NOT added to
    # `tables.evidence_tables`'s own list: `transfer_table` expects the belief/action shape
    # (delta_raw / machinery / delta_net / sensitivity / transfer) and would render an empty
    # table from this file. AF facts reach the paper through declared contrasts.
    "af_summary.yaml",
    # Added 2026-08-23b, after H30 was falsified by a purpose-trained retriever. A RANKING
    # reading (source-level Spearman against installed ground truth), not a removal one --
    # built by `scripts/build_retrieval_evidence.py`. Same `{delta, ci95, excludes_zero}`
    # shape, so it needs a filename here and nothing else, and it is likewise NOT added to
    # `tables.evidence_tables`'s list.
    "retrieval_summary.yaml",
)


_PROVENANCE_FILES = {*_SUMMARY_FILES, "trajectory.jsonl", "config.resolved.yaml", markdown.REPORT_FILENAME}


def _load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = yaml.safe_load(path.read_text())
    return value if isinstance(value, dict) else None


def _split_run(experiment_id: str, run_id: str) -> tuple[str, str]:
    """Resolve a source id that MAY name its own experiment as `<experiment>/<run>`.

    Added 2026-08-22. A writeup was previously confined to one experiment directory, which
    made it impossible to report a result from a second topic -- including a
    NON-replication, which is exactly the kind of claim a paper owes its reader. The
    auditor caught this the honest way: it rejected a manuscript that asserted the second
    topic did not replicate while no evidence bundle from that topic had been supplied.
    An unqualified id keeps the old behaviour and resolves under the job's own experiment.
    """
    if "/" in run_id:
        other, _, name = run_id.partition("/")
        return other, name
    return experiment_id, run_id


def source_directory(experiment_id: str, run_id: str) -> Path:
    owner, name = _split_run(experiment_id, run_id)
    return RESULTS_DIR / owner / name


def _artifact_path(experiment_id: str, run_id: str, filename: str) -> str:
    owner, name = _split_run(experiment_id, run_id)
    return str(Path("data") / "results" / owner / name / filename)


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
            # Built through `_split_run` like `_artifact_path` is. Without it a qualified
            # `<experiment>/<run>` source id produced `data/results/<own-exp>/<other-exp>/<run>`
            # -- a path that exists nowhere, disagreeing with the manifest entries beside it,
            # and shown to the authoring model as where the evidence lives.
            "directory": str(Path("data") / "results" / Path(*_split_run(experiment_id, run_id))),
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
            # Compare against the DIRECTORY name, not the declared source id: a qualified
            # `<experiment>/<run>` id still names a run whose artifacts say only `<run>`.
            # The check itself is worth keeping exactly as strict as it was -- it is what
            # catches a source run pointed at the wrong directory.
            _, expected_run = _split_run(experiment_id, run_id)
            if declared_run is not None and declared_run != expected_run:
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
        for table in tables.evidence_tables(evidence)
    ]
    evidence["evidence_refs"] = {
        ref.id: ref.model_dump()
        for ref in evidence_references(evidence)
    }
    return evidence


def write_json(value: Any, path: Path) -> Path:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return path


def write_evidence(evidence: dict[str, Any], path: Path) -> Path:
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    return path


def file_sha_from_json(value: Any) -> str:
    import hashlib

    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


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
