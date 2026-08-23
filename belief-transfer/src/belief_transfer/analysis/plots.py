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


# -- attributable fraction ---------------------------------------------------------------

# Method display order and styling for `plot_af`. Same principle as `_STYLE` above: fixed
# order so the same method sits in the same place in every rendering, and marker shape as
# well as colour so the figure survives grayscale. The oracle and the word-count baseline
# are the two reference rows -- the oracle is the ceiling and word count is the bar every
# content-keyed method has to clear -- so they are drawn in black and grey respectively and
# the content-keyed methods in colour.
_AF_METHODS = (
    ("oracle", "#000000", "o", "oracle (measured effect)"),
    ("delta_pred", "#1f77b4", "s", "Δ-predictability"),
    ("tracin", "#d62728", "^", "TracIn"),
    ("tracin_cos", "#ff7f0e", "v", "TracIn-cosine"),
    ("wordcount", "#7f7f7f", "D", "word count (baseline)"),
)
_AF_SEEDS = (("s42", 1.0, "seed 42"), ("s7", 0.45, "seed 7"))


def af_facts(synthesis: dict) -> dict[tuple[str, str, str], dict]:
    """Index `af_<method>_<budget>_<seed>` synthesis facts by (method, budget, seed).

    Reads the SAME facts the ladder table renders, so the figure cannot disagree with the
    table beside it -- the property `plot_trajectory` gets by reading one `trajectory.jsonl`.
    """
    out: dict[tuple[str, str, str], dict] = {}
    known = {name for name, _, _, _ in _AF_METHODS}
    for fact in synthesis.get("facts", []):
        parts = str(fact["id"]).split("_")
        if parts[0] != "af" or len(parts) < 4:
            continue
        seed, budget, method = parts[-1], parts[-2], "_".join(parts[1:-2])
        if method in known and budget.startswith("p"):
            out[(method, budget, seed)] = fact
    return out


def plot_af(synthesis: dict, output_dir: Path) -> list[Path]:
    """Forest plot of attributable fraction by method, one panel per removal budget.

    AF = 1 - dB_after/dB_before: the share of an installed effect that actually disappears
    when a method's top-ranked documents are removed and the model is retrained at the same
    pair count and epochs. Zero means removal left the effect unchanged; negative means it
    made the effect LARGER, which is why the zero line is drawn and labelled explicitly.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    facts = af_facts(synthesis)
    if not facts:
        return []
    budgets = sorted({budget for _, budget, _ in facts}, key=lambda b: int(b[1:]))
    output_dir.mkdir(parents=True, exist_ok=True)

    figure, axes = plt.subplots(
        1, len(budgets), figsize=(5.4 * len(budgets), 3.4), sharex=True, squeeze=False
    )
    for column, budget in enumerate(budgets):
        axis = axes[0][column]
        ticks, labels = [], []
        for row, (method, colour, marker, label) in enumerate(_AF_METHODS):
            position = len(_AF_METHODS) - row
            ticks.append(position)
            labels.append(label)
            for seed, alpha, _ in _AF_SEEDS:
                fact = facts.get((method, budget, seed))
                if fact is None:
                    continue
                offset = 0.16 if seed == "s42" else -0.16
                value = float(fact["value"])
                axis.plot(
                    value, position + offset, marker=marker, color=colour,
                    alpha=alpha, markersize=6, linestyle="none",
                )
                ci95 = fact.get("ci95")
                if ci95:
                    axis.plot(
                        [float(ci95[0]), float(ci95[1])], [position + offset] * 2,
                        color=colour, alpha=alpha, linewidth=1.4, solid_capstyle="butt",
                    )
        axis.axvline(0.0, color="black", linewidth=1.0)
        axis.text(
            0.0, len(_AF_METHODS) + 0.62, " AF = 0: effect unchanged",
            fontsize=7, va="center", ha="left", color="black",
        )
        axis.set_yticks(ticks)
        axis.set_yticklabels(labels if column == 0 else [""] * len(labels), fontsize=8)
        axis.set_ylim(0.3, len(_AF_METHODS) + 0.9)
        axis.set_xlabel("attributable fraction (AF)")
        axis.set_title(f"removal budget: top {budget[1:]}% of pool pairs", fontsize=10)
        axis.grid(axis="x", alpha=0.3, linewidth=0.5)

    handles = [
        plt.Line2D([], [], color="#333333", marker="o", linestyle="none",
                   alpha=alpha, markersize=6, label=name)
        for _, alpha, name in _AF_SEEDS
    ]
    axes[0][-1].legend(handles=handles, fontsize=7, loc="lower right")
    figure.suptitle(
        "Attributable fraction by attribution method (full fine-tuning, probability scale)",
        fontsize=11,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.92))
    path = output_dir / "attributable_fraction.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return [path]
