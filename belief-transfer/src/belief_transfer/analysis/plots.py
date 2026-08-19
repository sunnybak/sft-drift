"""Plots of the tidy trajectory rows `stage=trajectory` writes.

Four figures, one per question AGENTS.md's Analysis section names, all read off one
`trajectory.jsonl` so a plot can never disagree with the numbers it came from. Every panel
is score-versus-optimizer-step, because the point is progress *during* training: an
endpoint tells you where an arm landed, and the standing result -- absorption rising while
belief stays at base -- is a claim about the order things happen in.

Deliberately plain, per "Avoid decorative visualization": one line per arm, base as a
horizontal reference where there is one, the gate's threshold drawn where there is one, no
styling beyond what makes the lines distinguishable in grayscale.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

# Arms in a fixed order with fixed styling, so the same arm is the same line in every
# figure and across runs. Colour AND dash, so the figures survive being printed.
_STYLE = {
    "m_plus":   ("#1f77b4", "-",  "M+ evidence"),
    "m_minus":  ("#1f77b4", "--", "M− evidence"),
    "m0_plus":  ("#7f7f7f", "-",  "M0+ control"),
    "m0_minus": ("#7f7f7f", "--", "M0− control"),
    "me_plus":  ("#d62728", "-",  "Me+ explicit"),
    "me_minus": ("#d62728", "--", "Me− explicit"),
}


def load_trajectory(path: Path) -> dict[tuple[str, str, str], list[tuple[int, float]]]:
    """`{(arm, instrument, metric): [(step, value), ...]}`, each series sorted by step."""
    series: dict[tuple[str, str, str], list[tuple[int, float]]] = defaultdict(list)
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        series[(row["condition"], row["eval_type"], row["metric"])].append(
            (int(row["step"]), float(row["score"]))
        )
    return {key: sorted(points) for key, points in series.items()}


def _panel(axis, series, instrument: str, metric: str, title: str, ylabel: str) -> bool:
    drawn = False
    for arm, (colour, dash, label) in _STYLE.items():
        points = series.get((arm, instrument, metric))
        if not points:
            continue
        axis.plot([s for s, _ in points], [v for _, v in points],
                  color=colour, linestyle=dash, marker="o", markersize=3, label=label)
        drawn = True
    axis.set_title(title, fontsize=10)
    axis.set_xlabel("optimizer step")
    axis.set_ylabel(ylabel)
    axis.grid(alpha=0.3, linewidth=0.5)
    return drawn


def plot_trajectory(trajectory_path: Path, output_dir: Path) -> list[Path]:
    """Render the figures for one trajectory file. Returns the paths written."""
    import matplotlib

    matplotlib.use("Agg")  # no display on a GPU box
    import matplotlib.pyplot as plt

    series = load_trajectory(trajectory_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    panels = [
        ("choice", "accuracy", "Forced-choice ability (the gate)", "accuracy", 0.75),
        ("belief", "score", "Belief score by SFT condition", "belief", None),
        ("action", "score", "Action score by SFT condition", "action", None),
        ("absorption", "m_plus_net", "Absorption, netted", "specialization", 0.0),
    ]
    live = [p for p in panels if any(k[1] == p[0] for k in series)]
    if not live:
        return written

    figure, axes = plt.subplots(len(live), 1, figsize=(6.6, 2.7 * len(live)), squeeze=False)
    for axis, (instrument, metric, title, ylabel, rule) in zip(axes[:, 0], live):
        _panel(axis, series, instrument, metric, title, ylabel)
        if rule is not None:
            axis.axhline(rule, color="black", linewidth=0.8, linestyle=":",
                         label="threshold" if instrument == "choice" else None)
    axes[-1][0].legend(fontsize=7, loc="best")
    figure.tight_layout()
    combined = output_dir / "trajectory.png"
    figure.savefig(combined, dpi=150)
    plt.close(figure)
    written.append(combined)

    # The focused diagnostic separates the two measured outcomes and polarity. It does not
    # put belief and action on artificial phase-space axes: time is optimizer step, exactly
    # as in the underlying tidy trajectory rows.
    if any(k[1] == "belief" for k in series) and any(k[1] == "action" for k in series):
        figure, axes = plt.subplots(2, 2, figsize=(8.4, 6.0), sharex="col")
        for row, (instrument, ylabel) in enumerate((("belief", "belief score"), ("action", "action score"))):
            for column, (polarity, arms) in enumerate(
                (
                    ("Positive-statement conditions", ("m_plus", "m0_plus", "me_plus")),
                    ("Negative-statement conditions", ("m_minus", "m0_minus", "me_minus")),
                )
            ):
                axis = axes[row][column]
                drawn = False
                for arm in arms:
                    colour, _, label = _STYLE[arm]
                    points = series.get((arm, instrument, "score"))
                    if not points:
                        continue
                    axis.plot(
                        [step for step, _ in points],
                        [score for _, score in points],
                        color=colour,
                        linestyle="-",
                        marker="o",
                        markersize=4,
                        label=label,
                    )
                    drawn = True
                if row == 0:
                    axis.set_title(polarity, fontsize=10)
                if column == 0:
                    axis.set_ylabel(ylabel)
                if row == 1:
                    axis.set_xlabel("optimizer step")
                axis.grid(alpha=0.3, linewidth=0.5)
                if drawn:
                    axis.legend(fontsize=7, loc="best")
        figure.suptitle("Belief and action trajectories by polarity", fontsize=11)
        figure.tight_layout(rect=(0, 0, 1, 0.94))
        diagnostic = output_dir / "polarity_trajectories.png"
        figure.savefig(diagnostic, dpi=150)
        plt.close(figure)
        written.append(diagnostic)
    return written
