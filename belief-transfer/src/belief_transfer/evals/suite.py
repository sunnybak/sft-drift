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


def score_rows(
    scorer,
    rows: list[dict],
    config: EvalGenConfig,
    *,
    condition: str,
    model_tag: str,
    adapter: str | None = None,
    intervention: str | None = None,
) -> list[dict]:
    """Score every suite row through `scorer.score_choices` (the letter reading).

    Mirrors `efficacy.score_items`: raw per-choice logprobs are kept alongside the
    derived probability (AGENTS.md wants aggregates derivable from raw observations),
    and `condition` labels what was scored since one file holds several conditions.
    """
    scored_rows: list[dict] = []
    for row in rows:
        prompt = render_item_prompt(row, config, intervention=intervention)
        labels = row["labels"]
        letter_scores = scorer.score_choices(prompt, labels)
        letter_probs = letter_scores.probabilities()
        positive_label = labels[row["positive_option"]]
        scored_rows.append({
            **row,
            "condition": condition,
            "model_tag": model_tag,
            "adapter": adapter,
            "intervention": intervention,
            "letter_scores": [score.model_dump() for score in letter_scores.scores],
            "letter_probs": letter_probs,
            "p_positive": letter_probs[positive_label],
        })
    return scored_rows


def per_item(rows: list[dict], key: str = "p_positive") -> dict[str, float]:
    """Each item's score, averaged over its presentation orders (D4)."""
    import statistics
    from collections import defaultdict

    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[row["item_id"]].append(float(row[key]))
    return {item_id: statistics.fmean(values) for item_id, values in grouped.items()}


def variant_gap(rows: list[dict], key: str = "p_positive") -> float | None:
    """Mean within-item spread across presentation orders -- the position-bias
    diagnostic, and the thing that catches a positive_option sign error (which makes
    the two orders disagree by construction)."""
    import statistics
    from collections import defaultdict

    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[row["item_id"]].append(float(row[key]))
    spreads = [max(values) - min(values) for values in grouped.values() if len(values) > 1]
    return statistics.fmean(spreads) if spreads else None


def paired_delta(rows_a: list[dict], rows_b: list[dict], key: str = "p_positive") -> dict:
    """Mean per-item difference (a - b) with a bootstrap CI over items.

    Paired per item, exactly like `efficacy.delta`: the two conditions are scored on
    the same items, so differencing before resampling removes the between-item
    variance that would otherwise dominate the CI.
    """
    import statistics

    from belief_transfer.metrics import bootstrap_ci

    a, b = per_item(rows_a, key), per_item(rows_b, key)
    shared = sorted(set(a) & set(b))
    if not shared:
        raise ValueError("no shared items between conditions")
    diffs = [a[item_id] - b[item_id] for item_id in shared]
    low, high = bootstrap_ci(diffs)
    return {
        "delta": statistics.fmean(diffs),
        "ci95": [low, high],
        "n_items": len(shared),
        "excludes_zero": low > 0 or high < 0,
    }


def netted_delta(
    rows_plus: list[dict], rows_minus: list[dict],
    control_plus: list[dict], control_minus: list[dict],
    key: str = "p_positive",
) -> dict:
    """(plus - minus) - (control_plus - control_minus), paired per item.

    The netting every reading in this repo has turned out to need: the raw contrast
    carries any-SFT machinery (the off-topic control scores 0.42 vs base 0.09 on the
    belief suite), and netting per item before resampling keeps the CI honest.
    """
    import statistics

    from belief_transfer.metrics import bootstrap_ci

    a, b = per_item(rows_plus, key), per_item(rows_minus, key)
    c, d = per_item(control_plus, key), per_item(control_minus, key)
    shared = sorted(set(a) & set(b) & set(c) & set(d))
    if not shared:
        raise ValueError("no shared items across the four conditions")
    diffs = [(a[i] - b[i]) - (c[i] - d[i]) for i in shared]
    low, high = bootstrap_ci(diffs)
    return {
        "delta": statistics.fmean(diffs),
        "ci95": [low, high],
        "n_items": len(shared),
        "excludes_zero": low > 0 or high < 0,
    }
