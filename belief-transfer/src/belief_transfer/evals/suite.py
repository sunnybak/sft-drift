"""Shared mechanics for the generated eval suites (belief, action).

The efficacy suite predates this module and keeps its own copies of the same ideas
(variant expansion, prompt layout); lifting those out is deliberately not done here --
AGENTS.md says not to rewrite functioning code, and the efficacy suite is frozen enough
that touching it for symmetry would be all risk and no information. New suites build on
this module; `efficacy.py` stays as it is.

Paths mirror the datagen convention: candidate items land under `data/generated/`, the
gated suite under `data/validated/`, both keyed by experiment and run id.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Environment, StrictUndefined

from belief_transfer.schemas import EvalGenConfig

ROOT = Path(__file__).resolve().parents[3]
GENERATED_DIR = ROOT / "data" / "generated"
VALIDATED_DIR = ROOT / "data" / "validated"

VARIANTS = ("ab", "ba")

_env = Environment(trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined)


def items_path(experiment_id: str, run_id: str, suite: str) -> Path:
    """Candidate items (one row per item, pre-variant), before gating."""
    return GENERATED_DIR / experiment_id / run_id / f"{suite}_items.jsonl"


def validated_suite_path(experiment_id: str, run_id: str, suite: str) -> Path:
    """The gated, variant-expanded suite the scoring stages consume."""
    return VALIDATED_DIR / experiment_id / run_id / f"{suite}_eval.jsonl"


def review_path(experiment_id: str, run_id: str, suite: str) -> Path:
    return GENERATED_DIR / experiment_id / run_id / f"{suite}_review.md"


def option_variants(item: dict, labels: list[str]) -> list[dict]:
    """One item -> one row per presentation order (EVALGEN.md D4).

    Both rows share `item_id`; the `"ba"` variant swaps the options and flips
    `positive_option` so it keeps indexing the option a B+ holder picks. Everything
    downstream reads `positive_option` and never assumes a layout.
    """
    if len(item["options"]) != 2 or len(labels) != 2:
        raise ValueError("eval items are two-way choices")
    ab = {**item, "variant": "ab", "labels": list(labels)}
    ba = {
        **item,
        "variant": "ba",
        "labels": list(labels),
        "options": list(reversed(item["options"])),
        "positive_option": 1 - item["positive_option"],
    }
    return [ab, ba]


def render_item_prompt(
    row: dict, config: EvalGenConfig, *, intervention: str | None = None
) -> str:
    """One variant row -> the prompt the model under test sees.

    `intervention` is the sensitivity stage's B+/B- prefix; None both for the plain
    condition and for checkpoint scoring.
    """
    template = _env.from_string(config.item_prompt_template)
    return template.render(
        intervention=intervention or "",
        statement=row.get("statement") or "",
        scenario=row.get("scenario") or "",
        label_a=row["labels"][0],
        label_b=row["labels"][1],
        option_a=row["options"][0],
        option_b=row["options"][1],
    ).strip()


def item_text(item: dict) -> str:
    """The item's full visible text, for judging, leakage, and duplicate detection."""
    body = item.get("statement") or item.get("scenario") or ""
    return "\n".join([body, *item["options"]]).strip()


def write_rows(rows: list[dict], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
