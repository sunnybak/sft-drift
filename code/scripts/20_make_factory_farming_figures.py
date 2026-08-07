"""Render compact factory-farming result figures from final analysis artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open() as source:
        return list(csv.DictReader(source))


def directional_profiles(rows: list[dict]) -> dict:
    grouped = defaultdict(dict)
    for row in rows:
        arm = row["training_arm"]
        if arm not in (
            "anti_factory_farming",
            "conventional_agriculture_defense",
        ):
            continue
        metric = (
            "anti_factory_farming_score"
            if row["suite"] == "zero_hop_opinion"
            else "avoids_conventional_animal_products"
        )
        value = row.get(metric)
        if value in (None, ""):
            continue
        key = (
            row["model_tag"],
            float(row["learning_rate"]),
            row["suite"],
            int(row["training_seed"]),
        )
        grouped[key][arm] = float(value)
    profiles = defaultdict(list)
    for (model_tag, learning_rate, suite, seed), arms in grouped.items():
        if len(arms) != 2:
            continue
        profiles[(model_tag, learning_rate, suite)].append(
            arms["anti_factory_farming"]
            - arms["conventional_agriculture_defense"]
        )
    return {
        key: sum(values) / len(values)
        for key, values in profiles.items()
        if len(values) == 3
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    report = json.loads(
        (args.analysis_dir / "factory_farming_analysis.json").read_text()
    )
    condition_rows = read_csv(
        args.analysis_dir / "condition_suite_summaries.csv"
    )
    political_rows = read_csv(
        args.analysis_dir / "political_control_summaries.csv"
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    contrasts = report["confirmatory_recipe_contrasts"]
    labels = list(contrasts)
    effects = [
        contrasts[label]["effect_percentage_points"] for label in labels
    ]
    lower = [
        contrasts[label]["ci_95_percentage_points"][0] for label in labels
    ]
    upper = [
        contrasts[label]["ci_95_percentage_points"][1] for label in labels
    ]
    figure, axis = plt.subplots(figsize=(7.2, 3.6))
    positions = list(range(len(labels)))
    axis.errorbar(
        effects,
        positions,
        xerr=[
            [effect - low for effect, low in zip(effects, lower)],
            [high - effect for effect, high in zip(effects, upper)],
        ],
        fmt="o",
        color="#7b2cbf",
        ecolor="#9d4edd",
        capsize=4,
    )
    axis.axvline(0, color="#555555", linewidth=1)
    axis.set_yticks(positions, labels)
    axis.set_xlabel(
        "Anti-factory-farming minus defense (percentage points)"
    )
    axis.set_title("Co-primary recipe contrasts")
    axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()
    figure.savefig(
        args.output_dir / "factory_farming_confirmatory.png",
        dpi=200,
    )
    plt.close(figure)

    profiles = directional_profiles(condition_rows)
    suites = [
        "zero_hop_opinion",
        "recipes",
        "grocery",
        "restaurant",
        "catering",
    ]
    pretty_suites = [
        "Direct opinion",
        "Recipes",
        "Grocery",
        "Restaurant",
        "Catering",
    ]
    figure, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    for axis, (model_tag, learning_rate) in zip(
        axes.flat,
        (
            ("qwen3-4b", 0.0002),
            ("qwen3-4b", 0.00002),
            ("qwen3-8b", 0.0002),
            ("qwen3-8b", 0.00002),
        ),
    ):
        values = [
            100 * profiles[(model_tag, learning_rate, suite)]
            for suite in suites
        ]
        axis.bar(pretty_suites, values, color="#2a9d8f")
        axis.axhline(0, color="#555555", linewidth=1)
        axis.set_title(f"{model_tag.replace('qwen3-', '').upper()}, LR={learning_rate:g}")
        axis.tick_params(axis="x", rotation=35)
        axis.grid(axis="y", alpha=0.2)
    axes[0, 0].set_ylabel("Anti minus defense (score points)")
    axes[1, 0].set_ylabel("Anti minus defense (score points)")
    figure.suptitle("Opinion-to-action transfer profile")
    figure.tight_layout()
    figure.savefig(
        args.output_dir / "factory_farming_transfer_profile.png",
        dpi=200,
    )
    plt.close(figure)

    adapter_rows = [
        row for row in political_rows if row["condition_type"] == "adapter"
    ]
    colors = {
        "anti_factory_farming": "#d62828",
        "conventional_agriculture_defense": "#003049",
        "agriculture_topic_neutral": "#f77f00",
        "offtopic_argumentative_neutral": "#2a9d8f",
    }
    figure, axis = plt.subplots(figsize=(6.4, 4.6))
    for arm, color in colors.items():
        subset = [row for row in adapter_rows if row["training_arm"] == arm]
        axis.scatter(
            [100 * float(row["confidence_delta_vs_base"]) for row in subset],
            [100 * float(row["weighted_delta_vs_base"]) for row in subset],
            label=arm.replace("_", " "),
            color=color,
            alpha=0.8,
        )
    axis.axhline(0, color="#555555", linewidth=1)
    axis.axvline(0, color="#555555", linewidth=1)
    axis.set_xlabel("Confidence change vs base (percentage points)")
    axis.set_ylabel("Conservative-axis change vs base (percentage points)")
    axis.set_title("Political movement versus confidence damage")
    axis.legend(fontsize=7)
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(
        args.output_dir / "factory_farming_political_damage.png",
        dpi=200,
    )
    plt.close(figure)


if __name__ == "__main__":
    main()
