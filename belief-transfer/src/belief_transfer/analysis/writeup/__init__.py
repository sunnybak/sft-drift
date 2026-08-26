"""Grounded short-paper drafting and deterministic LaTeX rendering.

This package deliberately treats recorded result artifacts as the source of truth. The
language model only writes digit-light prose around fixed tables and figures rendered by
Python; it cannot invent or alter a reported numerical result.

It was one 2,200-line module, which is fine until you need to know where a rule lives. The
split follows the direction evidence travels, and the import graph is acyclic in that order:

    evidence     read the recorded bundles; the only reader of `data/results/`
    synthesis    freeze the quantities a manuscript may quote
    validate     the deterministic checks, and the numeric surface they check against
    tools        the tool schemas for the three model calls
    prompts      what the author model is told
    authoring    the three model calls and the one shared retry loop
    assets       build the tables and figures a plan asked for
    render       LaTeX and compilation; owns no selection logic

This module re-exports the surface `stages/writeup.py` and the tests use, so a caller does
not need to know which file a function moved to. One thing does NOT survive re-export:
patching a module global. `RESULTS_DIR` is read by `writeup.evidence`, so a test pointing it
at a fixture tree must patch `writeup.evidence.RESULTS_DIR` -- setting it on this package
would assign an attribute nothing reads.
"""

from __future__ import annotations

from belief_transfer.schemas import WriteupSpec

from belief_transfer.analysis.writeup.assets import (
    build_assets,
    copy_trajectory_figures,
)
from belief_transfer.analysis.writeup.authoring import (
    audit_manuscript,
    plan_manuscript,
    write_section,
    write_sections,
)
from belief_transfer.analysis.writeup.evidence import (
    ASSET_BRIEFS_FILENAME,
    DRAFT_FILENAME,
    EVIDENCE_FILENAME,
    PLAN_FILENAME,
    REFERENCES_FILENAME,
    REVIEW_FILENAME,
    SOURCE_MAP_FILENAME,
    SYNTHESIS_FILENAME,
    build_source_map,
    collect_evidence,
    evidence_references,
    file_sha_from_json,
    source_directory,
    verify_evidence_ref,
    write_evidence,
    write_json,
)
from belief_transfer.analysis.writeup.render import (
    COMPILE_LOG_FILENAME,
    PAPER_FILENAME,
    PDF_FILENAME,
    TEMPLATE_DIR,
    compile_latex,
    render_manuscript_latex,
)
from belief_transfer.analysis.writeup.synthesis import build_synthesis
from belief_transfer.analysis.writeup.validate import (
    deterministic_audit,
    validate_manuscript_plan,
    validate_section_payload,
)

__all__ = [
    "ASSET_BRIEFS_FILENAME",
    "COMPILE_LOG_FILENAME",
    "DRAFT_FILENAME",
    "EVIDENCE_FILENAME",
    "PAPER_FILENAME",
    "PDF_FILENAME",
    "PLAN_FILENAME",
    "REFERENCES_FILENAME",
    "REVIEW_FILENAME",
    "SOURCE_MAP_FILENAME",
    "SYNTHESIS_FILENAME",
    "TEMPLATE_DIR",
    "WriteupSpec",
    "audit_manuscript",
    "build_assets",
    "build_source_map",
    "build_synthesis",
    "collect_evidence",
    "compile_latex",
    "copy_trajectory_figures",
    "deterministic_audit",
    "evidence_references",
    "file_sha_from_json",
    "plan_manuscript",
    "render_manuscript_latex",
    "source_directory",
    "validate_manuscript_plan",
    "validate_section_payload",
    "verify_evidence_ref",
    "write_evidence",
    "write_json",
    "write_section",
    "write_sections",
]
