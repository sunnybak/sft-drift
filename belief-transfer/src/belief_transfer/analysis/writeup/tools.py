"""Tool schemas for the three authoring calls.

Pure declaration: the shape a model must return. Kept apart from the prompts because a
schema change is a compatibility change -- every cached completion was produced against one
of these -- while prompt text is edited freely.
"""

from __future__ import annotations

from belief_transfer.generation.llm import Tool

from belief_transfer.analysis.writeup.validate import _PLACEMENTS


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
                            "enum": ["ladder_table", "transfer_table", "trajectory_figure", "af_figure", "af_overlap_table", "factorial_table"],
                        },
                        "axes_or_columns": {"type": "array", "items": {"type": "string"}},
                        "placement": {
                            "type": "string",
                            "enum": list(_PLACEMENTS),
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
