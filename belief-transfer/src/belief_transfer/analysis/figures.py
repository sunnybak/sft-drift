"""Generic charts for insight notes: a forest of estimates, and lines over a series.

Two kinds, because the recorded data has two shapes -- point estimates with intervals, and
tidy rows over an x axis -- and `plots.py` already implements both. What is new here is that
neither kind knows anything about this project's arms or instruments. `plots._STYLE` names
six specific arms (`m_plus`, `me_minus`, ...) and `plots.plot_trajectory` hardcodes four
panels; both are correct for the figures they draw and useless for a note about anything
else. The property worth keeping from them is preserved: a series key always gets the same
colour AND dash, so a line is recognisable across figures and survives being printed in
grayscale.

**Every value plotted arrives already resolved.** This module never opens the results tree.
That is the same invariant `plots.py` holds -- a figure is rendered from the numbers an
artifact recorded, so it cannot disagree with them -- and it is what lets `notes.check`
audit a figure by re-resolving its spec instead of trusting the image.

A figure is described by a small YAML spec whose every data value is a *ref*, never a
literal. A literal float would be a number in the deliverable that nothing can trace, which
is the one thing a grounded note may not contain.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

# Eight (colour, dash) pairs assigned to sorted series keys. Colour-blind-safe hues, and
# the dash carries the same information so the figure works in grayscale.
_CYCLE = (
    ("#1f77b4", "-"), ("#d62728", "--"), ("#2ca02c", "-."), ("#7f7f7f", ":"),
    ("#9467bd", "-"), ("#ff7f0e", "--"), ("#17becf", "-."), ("#8c564b", ":"),
)


def style_for(keys: Sequence[str]) -> dict[str, tuple[str, str]]:
    """Deterministic (colour, dash) per series key, stable under re-ordering of the input.

    Assigned off the sorted key list rather than off arrival order, so adding a series to a
    spec does not recolour the others -- a figure that changes colours between revisions
    silently invalidates any prose describing it.
    """
    return {key: _CYCLE[index % len(_CYCLE)] for index, key in enumerate(sorted(set(keys)))}


@dataclass(frozen=True)
class ForestRow:
    label: str
    value: float
    ci95: tuple[float, float] | None = None
    series: str = ""
    """Legend key. Rows sharing a `label` occupy ONE y slot and are dodged within it, with
    `series` picking the colour -- so a repeated measurement (three seeds, two models) is a
    pattern you can see rather than three separate rows whose relationship you have to
    reconstruct from their labels. Colouring by the label instead would encode what the
    axis already says and leave the interesting axis invisible."""


@dataclass(frozen=True)
class LineSeries:
    label: str
    points: tuple[tuple[float, float], ...]


def _pyplot():
    import matplotlib

    matplotlib.use("Agg")  # no display on a GPU box, and none in a harness either
    import matplotlib.pyplot as plt

    return plt


def forest(rows: Sequence[ForestRow], path: Path, *, title: str = "", xlabel: str = "",
           zero_line: bool = True, width: float = 7.0, legend_loc: str = "lower right") -> Path:
    """A forest plot: one slot per distinct label, one marker per row, interval as a bar.

    Slots follow first-appearance order of the labels, because that order is an editorial
    decision the note's author made; sorting here would silently override it.
    """
    plt = _pyplot()

    slots: list[str] = []
    for row in rows:
        if row.label not in slots:
            slots.append(row.label)
    by_slot = {label: [row for row in rows if row.label == label] for label in slots}

    palette = style_for([row.series for row in rows if row.series])
    height = max(1.7, 0.30 * len(rows) + 0.34 * len(slots) + 1.0)
    figure, axis = plt.subplots(figsize=(width, height))

    # Dodge offsets are assigned per SERIES over the whole figure, not per slot, so a given
    # series sits at the same height in every row. Computed per slot instead, a row with a
    # missing series shifts its neighbours and the eye reads a vertical pattern that is not
    # in the data -- visible immediately on a 2-seed row beside 3-seed rows.
    order = list(dict.fromkeys(row.series for row in rows if row.series))
    span = 0.62 if len(order) > 1 else 0.0
    dodge = {
        name: span * (0.5 - index / (len(order) - 1)) if len(order) > 1 else 0.0
        for index, name in enumerate(order)
    }

    for index, label in enumerate(slots):
        y_centre = len(slots) - 1 - index          # first label at the top
        for row in by_slot[label]:
            colour = palette.get(row.series, ("#1f77b4", "-"))[0]
            y = y_centre + dodge.get(row.series, 0.0)
            if row.ci95:
                low, high = row.ci95
                axis.plot([low, high], [y, y], color=colour, linewidth=1.5,
                          solid_capstyle="butt", zorder=2)
                for edge in (low, high):
                    axis.plot([edge, edge], [y - 0.07, y + 0.07], color=colour,
                              linewidth=1.1, zorder=2)
            axis.plot([row.value], [y], marker="o", markersize=5.0, color=colour, zorder=3)

    if zero_line:
        axis.axvline(0.0, color="black", linewidth=0.8, linestyle=":")
    # A faint rule between slots, so a dodged group reads as one row rather than as three.
    for index in range(len(slots) - 1):
        axis.axhline(index + 0.5, color="black", alpha=0.12, linewidth=0.6)
    axis.set_yticks(range(len(slots) - 1, -1, -1))
    axis.set_yticklabels(slots, fontsize=9)
    axis.set_ylim(-0.5, len(slots) - 0.5)
    if xlabel:
        axis.set_xlabel(xlabel)
    if title:
        axis.set_title(title, fontsize=10)
    axis.grid(axis="x", alpha=0.3, linewidth=0.5)
    if len(palette) > 1:
        from matplotlib.lines import Line2D
        order = [row.series for row in rows if row.series]
        seen = list(dict.fromkeys(order))          # legend in first-appearance order
        axis.legend(
            handles=[Line2D([], [], color=palette[name][0], marker="o", linestyle="",
                            markersize=5, label=name) for name in seen],
            fontsize=8, loc=legend_loc, framealpha=0.92,
            ncol=1 if len(seen) <= 4 else 2,
        )
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def lines(panels: Sequence[tuple[str, Sequence[LineSeries], float | None]], path: Path, *,
          title: str = "", xlabel: str = "", width: float = 7.0) -> Path:
    """One or more stacked panels of series-versus-x. `panels` is (ylabel, series, hline).

    Stacked and x-shared because the point of a trajectory figure is reading two
    instruments against the same step axis; putting them side by side would invite
    comparing them at different x.
    """
    plt = _pyplot()
    live = [panel for panel in panels if any(series.points for series in panel[1])]
    if not live:
        raise ValueError("no panel has any points to draw")

    figure, axes = plt.subplots(len(live), 1, figsize=(width, 2.5 * len(live)),
                               squeeze=False, sharex=True)
    palette = style_for([s.label for _, series, _ in live for s in series])
    for axis, (ylabel, series, hline) in zip(axes[:, 0], live):
        for one in series:
            if not one.points:
                continue
            colour, dash = palette[one.label]
            ordered = sorted(one.points)
            axis.plot([x for x, _ in ordered], [y for _, y in ordered],
                      color=colour, linestyle=dash, marker="o", markersize=3.5,
                      label=one.label)
        if hline is not None:
            axis.axhline(hline, color="black", linewidth=0.8, linestyle=":")
        axis.set_ylabel(ylabel, fontsize=9)
        axis.grid(alpha=0.3, linewidth=0.5)
    axes[-1][0].set_xlabel(xlabel or "x")
    axes[0][0].legend(fontsize=7, loc="best")
    if title:
        figure.suptitle(title, fontsize=11)
        figure.tight_layout(rect=(0, 0, 1, 0.95))
    else:
        figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


# ------------------------------------------------------------------------ the spec

class SpecError(ValueError):
    """A figure spec that cannot be rendered. Message is meant to be printed as-is."""


def output_path(spec_path: Path) -> Path:
    """`forest.fig.yaml` -> `forest.png`, so the pair can never drift apart.

    Derived rather than declared: a spec and its image being named independently is how a
    note ends up showing a chart built from an older version of its own data.
    """
    name = spec_path.name
    for suffix in (".fig.yaml", ".fig.yml", ".yaml", ".yml"):
        if name.endswith(suffix):
            return spec_path.with_name(name[: -len(suffix)] + ".png")
    return spec_path.with_suffix(".png")


def _require_ref(entry: dict[str, Any], where: str) -> str:
    ref = entry.get("ref")
    if not ref:
        raise SpecError(f"{where} has no `ref`. Every plotted value must cite an artifact; "
                        "a literal number in a figure is untraceable.")
    if not isinstance(ref, str):
        raise SpecError(f"{where}'s `ref` must be a ref string, not {type(ref).__name__}")
    return ref


def spec_refs(spec: dict[str, Any]) -> list[str]:
    """Every ref a spec cites, so a caller can resolve or audit them without rendering."""
    kind = spec.get("kind")
    if kind == "forest":
        return [_require_ref(row, f"row {index}")
                for index, row in enumerate(spec.get("rows") or [])]
    return []
