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

    figure, axes = plt.subplots(1, len(live), figsize=(5.2 * len(live), 4.0), squeeze=False)
    for axis, (instrument, metric, title, ylabel, rule) in zip(axes[0], live):
        _panel(axis, series, instrument, metric, title, ylabel)
        if rule is not None:
            axis.axhline(rule, color="black", linewidth=0.8, linestyle=":",
                         label="threshold" if instrument == "choice" else None)
    axes[0][-1].legend(fontsize=7, loc="best")
    figure.tight_layout()
    combined = output_dir / "trajectory.png"
    figure.savefig(combined, dpi=150)
    plt.close(figure)
    written.append(combined)

    # Belief against action on one pair of axes: the transfer question in one picture --
    # a point per arm per step, so a belief shift that never reaches action is a vertical
    # smear rather than a diagonal.
    if any(k[1] == "belief" for k in series) and any(k[1] == "action" for k in series):
        figure, axis = plt.subplots(figsize=(5.2, 4.6))
        for arm, (colour, dash, label) in _STYLE.items():
            belief = dict(series.get((arm, "belief", "score"), []))
            action = dict(series.get((arm, "action", "score"), []))
            steps = sorted(set(belief) & set(action))
            if not steps:
                continue
            axis.plot([belief[s] for s in steps], [action[s] for s in steps],
                      color=colour, linestyle=dash, marker="o", markersize=3, label=label)
        axis.set_xlabel("belief score")
        axis.set_ylabel("action score")
        axis.set_title("Belief transfer vs behavioural transfer", fontsize=10)
        axis.grid(alpha=0.3, linewidth=0.5)
        axis.legend(fontsize=7, loc="best")
        figure.tight_layout()
        scatter = output_dir / "belief_vs_action.png"
        figure.savefig(scatter, dpi=150)
        plt.close(figure)
        written.append(scatter)
    return written
