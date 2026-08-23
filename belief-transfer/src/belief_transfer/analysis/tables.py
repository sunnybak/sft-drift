"""Deterministic presentation tables over recorded result artifacts.

This is deliberately a presentation adapter, not another metrics layer: callers hand it
already-loaded stage reports or summaries, and it only selects, labels, and formats values
those artifacts already contain. Markdown and LaTeX therefore cannot drift on CI formatting,
column ordering, or gate qualifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TableCell:
    text: str
    bold: bool = False
    bold_text: str | None = None


@dataclass(frozen=True)
class TableSource:
    run_id: str
    artifact: str
    checkpoint: str = ""


@dataclass(frozen=True)
class ResultTable:
    id: str
    heading: str
    columns: tuple[str, ...]
    rows: tuple[tuple[TableCell, ...], ...]
    source: TableSource
    caption: str = ""
    note: str = ""
    evidence_refs: tuple[str, ...] = ()
    cell_refs: tuple[tuple[tuple[str, ...], ...], ...] = ()


def _significant(value: float, figures: int = 2) -> str:
    """Format with enough decimals to show `figures` significant digits, min 2 decimals."""
    magnitude = abs(value)
    if magnitude >= 0.1 or magnitude == 0:
        places = 2
    else:
        import math
        places = min(6, figures - 1 - math.floor(math.log10(magnitude)))
    return f"{value:+.{places}f}"


def _estimate(entry: dict[str, Any], *, key: str) -> TableCell:
    value = float(entry[key])
    low, high = entry["ci95"]
    point = f"{value:+.4f}"
    return TableCell(
        f"{point} [{float(low):+.4f}, {float(high):+.4f}]",
        bold=bool(entry.get("excludes_zero")),
        bold_text=point if entry.get("excludes_zero") else None,
    )


def _short_estimate(entry: dict[str, Any], *, key: str) -> TableCell:
    return TableCell(f"{float(entry[key]):+.3f}", bold=bool(entry.get("excludes_zero")))


def choice_gate_table(report: dict[str, Any]) -> ResultTable:
    """One choice-benchmark table with every recorded arm."""
    choice = report["metrics"]["choice"]
    rows: list[tuple[TableCell, ...]] = []
    n_items = set()
    thresholds = set()
    for arm, result in choice.items():
        metrics = result["metrics"]
        if result.get("n_items") is not None:
            n_items.add(int(result["n_items"]))
        threshold = result.get("thresholds", {}).get("min_accuracy")
        if threshold is not None:
            thresholds.add(float(threshold))
        rows.append(
            (
                TableCell(str(arm)),
                TableCell("PASS" if result["passed"] else "FAIL", bold=not result["passed"]),
                TableCell(f"{float(metrics['accuracy']):.3f}"),
                TableCell(f"{float(metrics['mean_confidence']):.3f}"),
                TableCell(f"{float(metrics['mean_margin']):.3f}"),
            )
        )
    items_text = (
        str(next(iter(n_items)))
        if len(n_items) == 1
        else ", ".join(map(str, sorted(n_items)))
        if n_items
        else "unspecified"
    )
    threshold_text = (
        f"; accuracy threshold {next(iter(thresholds)):.2f}" if len(thresholds) == 1 else ""
    )
    return ResultTable(
        id="choice_gate",
        heading=f"{report['run_id']}: choice_bench",
        columns=("arm", "verdict", "accuracy", "confidence", "margin"),
        rows=tuple(rows),
        source=TableSource(run_id=report["run_id"], artifact="choice_bench.yaml"),
        caption=f"Forced-choice ability gate ({items_text} items{threshold_text}).",
        note="A failing arm qualifies any downstream reading that depends on it.",
    )


def absorption_table(report: dict[str, Any]) -> ResultTable:
    """Netted per-dimension span-NLL specialization, including the two-sided evidence gate."""
    metrics = report["metrics"]
    dimensions = metrics["summary"]["dimensions"]
    preferred = ("m_plus_net", "m_minus_net", "me_plus_net", "me_minus_net")
    found = {key for value in dimensions.values() for key in value if key.endswith("_net")}
    net_keys = [key for key in preferred if key in found] + sorted(found - set(preferred))
    evidence_keys = ("m_plus_net", "m_minus_net")
    rows: list[tuple[TableCell, ...]] = []
    for dimension, entry in dimensions.items():
        gate = all(
            isinstance(entry.get(key), dict) and bool(entry[key].get("excludes_zero"))
            for key in evidence_keys
        )
        values = tuple(_estimate(entry[key], key="mean") if key in entry else TableCell("—") for key in net_keys)
        rows.append(
            (
                TableCell(str(dimension)),
                TableCell(str(entry["n_pairs"])),
                *values,
                TableCell("PASS" if gate else "FAIL", bold=not gate),
            )
        )
    pairings = ", ".join(f"{arm} − {control}" for arm, control in metrics["net_pairs"])
    checkpoint = ", ".join(
        sorted({str(arm.get("checkpoint", "")) for arm in metrics.get("arms", []) if arm.get("checkpoint")})
    )
    return ResultTable(
        id="absorption",
        heading=f"{report['run_id']}: absorption",
        columns=(
            "dimension",
            "held-out pairs",
            *(key.removesuffix("_net") for key in net_keys),
            "evidence gate",
        ),
        rows=tuple(rows),
        source=TableSource(run_id=report["run_id"], artifact="absorption.yaml", checkpoint=checkpoint),
        caption=(
            f"Netted span-NLL specialization; corpus {metrics['corpus_run']}; "
            f"{metrics['n_val_pairs']} held-out pairs overall."
        ),
        note=(
            "Positive values are specialization toward an arm's own corpus. Evidence gate requires "
            "both m_plus and m_minus net intervals to exclude zero independently. "
            f"Netting pairs: {pairings}."
        ),
    )


def transfer_table(
    summary: dict[str, Any], *, source_run: str | None = None, artifact: str | None = None
) -> ResultTable:
    """One labeled transfer contrast table from a belief/action summary."""
    rows: list[tuple[TableCell, ...]] = []
    for key in ("delta_raw", "machinery", "delta_net", "sensitivity"):
        if isinstance(summary.get(key), dict):
            rows.append((TableCell(key), _estimate(summary[key], key="delta")))
    transfer = summary.get("transfer")
    if isinstance(transfer, dict) and "T" in transfer:
        rows.append((TableCell(f"T ({transfer.get('from', 'unspecified')})"), TableCell(f"{float(transfer['T']):+.4f}")))
    suite = str(summary.get("suite", "transfer"))
    run_id = source_run or str(summary.get("run_id", "unknown"))
    artifact = artifact or f"{suite}_summary.yaml"
    return ResultTable(
        id=f"{suite}_transfer",
        heading=f"{run_id}: {suite} transfer",
        columns=("quantity", "recorded value"),
        rows=tuple(rows),
        source=TableSource(run_id=run_id, artifact=artifact),
        caption=f"Recorded {suite} contrast and sensitivity quantities.",
        note="Intervals are paired bootstrap CIs from the stored summary; bold excludes zero.",
    )


# Which block of the ledger a declared fact belongs to, keyed off its contrast id. A
# twenty-four row flat list is not readable: a reader looking for "TracIn at 10%" has to
# scan every row. Grouping costs nothing (the ids already encode the distinction) and the
# blocks are the argument's own structure -- what was installed, what the controls say,
# what removal recovered.
_LADDER_GROUPS = (
    ("Installed effects", ("ladder_",)),
    ("Pool and controls", ("pool_", "machinery_")),
    ("Attributable fraction, by method", ("af_",)),
    ("Retrieval rank correlations (not attributable fractions)", ("rank_",)),
)


def _ladder_group(fact_id: str) -> int:
    for index, (_, prefixes) in enumerate(_LADDER_GROUPS):
        if any(fact_id.startswith(prefix) for prefix in prefixes):
            return index
    return len(_LADDER_GROUPS)


def _af_sort_key(fact_id: str) -> tuple:
    """Sort AF rows method, then budget, then seed, so a named cell is findable."""
    parts = fact_id.split("_")
    if parts[0] != "af" or len(parts) < 4:
        return (fact_id,)
    seed, budget, method = parts[-1], parts[-2], "_".join(parts[1:-2])
    order = {"oracle": 0, "delta_pred": 1, "tracin": 2, "tracin_cos": 3, "wordcount": 4}
    return (order.get(method, 9), method, budget, seed)


def ladder_table(synthesis: dict[str, Any], *, source_run: str = "paper") -> ResultTable:
    """The declared contribution ladder, grouped into blocks and sorted within them."""
    rows: list[tuple[TableCell, ...]] = []
    evidence_refs: list[str] = []
    cell_refs: list[tuple[tuple[str, ...], ...]] = []
    facts = sorted(
        synthesis.get("facts", []),
        key=lambda f: (_ladder_group(str(f["id"])), _af_sort_key(str(f["id"]))),
    )
    current_group = -1
    for fact in facts:
        group = _ladder_group(str(fact["id"]))
        if group != current_group and group < len(_LADDER_GROUPS):
            current_group = group
            rows.append((
                TableCell(_LADDER_GROUPS[group][0], bold=True), TableCell(""), TableCell(""),
            ))
            cell_refs.append(((), (), ()))
        value = float(fact["value"])
        ci95 = fact.get("ci95")
        # Significant figures, not fixed decimals. Two decimals reads well for an AF of
        # -0.91 -- four would advertise precision the estimator does not have -- but it
        # renders pool effects of 0.0167 and 0.0247 as the SAME "+0.02", collapsing a real
        # difference the paper relies on. Scale the decimals to the magnitude instead.
        reading = _significant(value)
        if ci95 is not None:
            reading += f" [{_significant(float(ci95[0]))}, {_significant(float(ci95[1]))}]"
        rows.append(
            (
                TableCell(str(fact["label"])),
                TableCell(reading, bold=bool(fact.get("excludes_zero"))),
                TableCell(str(fact.get("qualification") or "—")),
            )
        )
        evidence_refs.extend(str(ref) for ref in fact.get("evidence_refs", []))
        refs = tuple(str(ref) for ref in fact.get("evidence_refs", []))
        cell_refs.append((refs, refs, refs))
    return ResultTable(
        id="contribution_ladder",
        heading="Measured contribution ladder",
        columns=("intervention", "net effect", "qualification"),
        rows=tuple(rows),
        source=TableSource(run_id=source_run, artifact="synthesis.json"),
        caption="Declared contrasts selected or derived from immutable result summaries.",
        note="Rows without intervals are deterministic point contrasts over recorded arm scores.",
        evidence_refs=tuple(dict.fromkeys(evidence_refs)),
        cell_refs=tuple(cell_refs),
    )


def render_markdown(table: ResultTable) -> list[str]:
    """Render a table without changing any measured values."""
    lines = [f"## {table.heading}", ""]
    if table.caption:
        lines += [table.caption, ""]
    lines += [
        "| " + " | ".join(table.columns) + " |",
        "|" + "|".join("---" for _ in table.columns) + "|",
    ]
    for row in table.rows:
        cells = [
            (
                f"`{cell.text}`"
                if table.id == "choice_gate" and index == 0
                else f"**{cell.bold_text}**{cell.text.removeprefix(cell.bold_text)}"
                if cell.bold_text
                else f"**{cell.text}**"
                if cell.bold
                else cell.text
            )
            for index, cell in enumerate(row)
        ]
        lines.append("| " + " | ".join(cells) + " |")
    if table.note:
        lines += ["", f"_Note: {table.note}_"]
    lines += ["", f"_Source: `{table.source.run_id}/{table.source.artifact}`._", ""]
    return lines


def latex_table(table: ResultTable) -> dict[str, Any]:
    """Jinja-ready representation; escaping remains the LaTeX renderer's responsibility."""
    return {
        "id": table.id,
        "heading": table.heading,
        "columns": table.columns,
        "rows": tuple(
            tuple({"text": cell.text, "bold": cell.bold, "bold_text": cell.bold_text} for cell in row)
            for row in table.rows
        ),
        "caption": table.caption,
        "note": table.note,
        "source": table.source,
    }


def af_overlap_table(synthesis: dict[str, Any], *, source_run: str = "paper") -> ResultTable:
    """The removal test as one artifact: positive control, candidates, and the comparator.

    One row per (method, budget, seed). The verdict column applies the declared criterion
    -- interval overlap with the word-count baseline in the SAME cell -- and says so, since
    overlap is not a pairwise test. Three visual groups, because they play three different
    roles: the oracle is a positive control (its one non-overlap cell is the control
    working), the candidate methods are what is being evaluated, and the baseline rows are
    the comparator every verdict is read against -- without them every verdict in the table
    would compare against numbers the table does not contain.
    """
    facts = {}
    for fact in synthesis.get("facts", []):
        parts = str(fact["id"]).split("_")
        if parts[0] == "af" and len(parts) >= 4:
            seed, budget, method = parts[-1], parts[-2], "_".join(parts[1:-2])
            facts[(method, budget, seed)] = fact

    label = {"oracle": "oracle (measured effect)", "delta_pred": "delta-predictability",
             "tracin": "TracIn", "tracin_cos": "TracIn-cosine", "wordcount": "word count (baseline)"}
    groups = (
        ("Positive control: removal ranked by the separately measured effect", ("oracle",)),
        ("Candidate methods", ("tracin", "tracin_cos", "delta_pred")),
        ("Comparator: the word-count baseline itself", ("wordcount",)),
    )
    rows, refs, cell_refs = [], [], []
    for group_label, methods in groups:
        rows.append((TableCell(group_label, bold=True),) + (TableCell(""),) * 4)
        cell_refs.append(((), (), (), (), ()))
        for method in methods:
            for budget in sorted({b for (_, b, _) in facts}, key=lambda b: int(b[1:])):
                for seed in sorted({s for (_, _, s) in facts}):
                    fact = facts.get((method, budget, seed))
                    base = facts.get(("wordcount", budget, seed))
                    if fact is None:
                        continue
                    ci = fact.get("ci95")
                    reading = f"{float(fact['value']):+.2f}"
                    if ci:
                        reading += f" [{float(ci[0]):+.2f}, {float(ci[1]):+.2f}]"
                    if method == "wordcount":
                        verdict = "(comparator)"
                    elif base is None or not ci or not base.get("ci95"):
                        verdict = "no same-cell baseline"
                    else:
                        b0, b1 = float(base["ci95"][0]), float(base["ci95"][1])
                        overlaps = float(ci[0]) <= b1 and b0 <= float(ci[1])
                        verdict = "overlaps" if overlaps else "does NOT overlap"
                    rows.append((
                        TableCell(label.get(method, method)),
                        TableCell(f"{budget[1:]}%"),
                        TableCell(seed.lstrip("s")),
                        TableCell(reading, bold=bool(fact.get("excludes_zero"))),
                        TableCell(verdict),
                    ))
                    r = tuple(str(x) for x in fact.get("evidence_refs", []))
                    refs.extend(r)
                    cell_refs.append((r, r, r, r, r))
    return ResultTable(
        id="af_overlap",
        heading="Attributable fraction against the word-count baseline",
        columns=("method", "budget", "seed", "attributable fraction", "non-separation criterion"),
        rows=tuple(rows),
        source=TableSource(run_id=source_run, artifact="synthesis.json"),
        caption=("Each method's attributable fraction against the model-free word-count "
                 "baseline in the same budget-and-seed cell."),
        note=("Verdict applies the pre-registered non-separation criterion: overlap of 95% "
              "bootstrap intervals within a cell. Overlap is not a pairwise significance "
              "test; no pairwise contrast was computed. Bold excludes zero."),
        evidence_refs=tuple(dict.fromkeys(refs)),
        cell_refs=tuple(cell_refs),
    )


# The 2x2 whose corner-to-corner gap motivates the paper. Fact ids are load-bearing here
# the way `af_<method>_<budget>_<seed>` is for the AF figure: the overlay must declare
# these four ids for the table to build, and `validate_manuscript_plan` rejects a
# `factorial_table` brief when any is missing from the synthesis -- BEFORE the prose is
# paid for -- rather than letting `build_assets` raise after it.
FACTORIAL_CELLS = {
    ("short", "sparse"): "ladder_short_sparse",
    ("short", "dense"): "ladder_short_dense",
    ("long", "sparse"): "ladder_evidence_long",
    ("long", "dense"): "ladder_long_dense",
}
_FACTORIAL_ROWS = (("short", "~101 words"), ("long", "~650--726 words"))
_FACTORIAL_COLUMNS = (("sparse", "sparse premises (~4%)"), ("dense", "dense premises (~15%)"))


def factorial_table(synthesis: dict[str, Any], *, source_run: str = "paper") -> ResultTable:
    """The length x density 2x2 of installed effects, as a 2x2 rather than four ladder rows.

    Presentation only: each cell is the declared contrast's recorded delta and interval,
    formatted exactly as the ladder table formats it. The point of the shape is that a
    reader sees both marginals at once -- length at fixed density down a column, density at
    fixed length along a row -- which four rows in a 30-row ladder do not show.
    """
    facts = {str(fact["id"]): fact for fact in synthesis.get("facts", [])}
    missing = [fact_id for fact_id in FACTORIAL_CELLS.values() if fact_id not in facts]
    if missing:
        raise ValueError(f"factorial_table is missing declared cells: {missing}")
    rows, refs, cell_refs = [], [], []
    for row_key, row_label in _FACTORIAL_ROWS:
        cells = [TableCell(row_label)]
        row_refs: list[tuple[str, ...]] = [()]
        for column_key, _ in _FACTORIAL_COLUMNS:
            fact = facts[FACTORIAL_CELLS[(row_key, column_key)]]
            reading = _significant(float(fact["value"]))
            ci95 = fact.get("ci95")
            if ci95 is not None:
                reading += f" [{_significant(float(ci95[0]))}, {_significant(float(ci95[1]))}]"
            cells.append(TableCell(reading, bold=bool(fact.get("excludes_zero"))))
            r = tuple(str(x) for x in fact.get("evidence_refs", []))
            refs.extend(r)
            row_refs.append(r)
        rows.append(tuple(cells))
        cell_refs.append(tuple(row_refs))
    return ResultTable(
        id="factorial_2x2",
        heading="Installed effect by document length and premise density",
        columns=("document length",) + tuple(label for _, label in _FACTORIAL_COLUMNS),
        rows=tuple(rows),
        source=TableSource(run_id=source_run, artifact="synthesis.json"),
        caption=("Installed effect (netted belief shift, probability scale) for the four "
                 "length x premise-density cells, third-person voice, identical premise "
                 "specification throughout."),
        note=("Cells are separately estimated corpus arms with 95% bootstrap intervals; "
              "no paired contrast between cells was computed. Bold excludes zero."),
        evidence_refs=tuple(dict.fromkeys(refs)),
        cell_refs=tuple(cell_refs),
    )


def provenance_table(contrasts: list[Any]) -> ResultTable:
    """Reproducibility appendix: where every declared contrast comes from.

    Built from the overlay spec, not the synthesis: run ids, artifacts, quantities and
    checkpoints are configuration, and belong in exactly one place a reader can consult
    without them cluttering prose. Deterministic -- no LLM writes or audits this.
    """
    rows = []
    for contrast in contrasts:
        quantity = getattr(contrast, "quantity", None) or ""
        if not quantity and getattr(contrast, "positive_arm", None):
            quantity = f"arms {contrast.positive_arm}-{contrast.negative_arm}"
        rows.append((
            TableCell(str(contrast.id)),
            TableCell(str(contrast.run_id)),
            TableCell(str(getattr(contrast, "artifact", "") or "")),
            TableCell(str(quantity)),
            TableCell(str(getattr(contrast, "checkpoint", "") or "final/summary")),
        ))
    return ResultTable(
        id="provenance",
        heading="Contrast provenance",
        columns=("contrast", "run", "artifact", "quantity", "checkpoint"),
        rows=tuple(rows),
        source=TableSource(run_id="paper", artifact="config.resolved.yaml"),
        caption="Run, artifact, quantity, and checkpoint behind every declared contrast.",
        note=("Training seeds: 42 (default) and 7 (quantities suffixed s7). The removal "
              "pool was scored at checkpoint-23 of attrib_mix_v4; matched off-topic "
              "controls come from m0_multiform at checkpoint-24."),
    )
