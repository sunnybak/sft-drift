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
