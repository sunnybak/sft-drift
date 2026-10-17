"""Readable pilot scores and a static research figure derived from raw summaries."""
from __future__ import annotations

import json
from pathlib import Path

from belief_transfer.schemas import PilotTarget

LABELS = {
    "animal_medical_research": "Animal medical research",
    "animal_cosmetic_testing": "Animal cosmetic testing",
    "medical_data_with_consent": "Medical data: consent given",
    "medical_data_without_consent": "Medical data: consent not sought",
    "progressive_income_tax": "Progressive income tax",
    "unconditional_basic_income": "Unconditional basic income",
    "sugary_drink_tax": "Sugary-drink tax",
    "paid_kidney_donation": "Paid kidney donation",
    "flight_tree_planting_offset": "Flight with tree planting",
    "modular_monolith_default": "Modular monolith (control)",
}


def write_pilot_report(metrics: dict, targets: list[PilotTarget], directory: Path) -> list[Path]:
    rows = [{"belief_id": t.definition.id, "definition": t.definition.model_dump(mode="json"),
             "role": t.role, "related_group": t.related_group,
             "binary": metrics["binary"][t.definition.id],
             "categorical": metrics["categorical"][t.definition.id],
             "bank_run_id": metrics["bank_run_id"], "model": metrics["pretrained"],
             "answer_extraction_version": metrics.get("answer_extraction_version", "complete-v3"),
             "categorical_prompt_style": metrics.get("categorical_prompt_style", "original"),
             "source_evaluation_run_id": metrics.get("source_evaluation_run_id")}
            for t in targets]
    scores_path = directory / "belief_scores.jsonl"
    scores_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    lines = ["# Ethical belief pilot — BASE Qwen3-4B", "",
             "No fine-tuning ran. All ten frozen evalsets were administered to BASE.", "",
             "Binary scores are answer-conditioned response likelihoods: 0 rejects the original "
             "proposition, 1 endorses it. A middle score can reflect uncertainty, inconsistency "
             "or answer-position effects. The wording range is descriptive, not a confidence interval.", "",
             "| Belief | Support | Wording range | Mean order gap | Absolute acquiescence | Readable / expected | Unresolved / readable |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    if metrics["backend_agreement"]["status"] != "passed":
        lines[2:2] = ["**Exploratory local likelihood readings:** cross-backend agreement is "
                      + metrics["backend_agreement"]["status"] + ". The original tolerance was "
                      "retained. These readings do not establish numerical interchangeability "
                      "with CUDA or license a definitive SFT comparison.", ""]
    def fmt(value):
        return f"{value:.3f}" if value is not None else "unavailable"
    for row in rows:
        b, c = row["binary"], row["categorical"]
        unresolved = f"{c['n_unresolved']}/{c['n_valid']}" if c["n_valid"] else "unavailable"
        lines.append(f"| {LABELS[row['belief_id']]} | {fmt(b['score'])} | "
                     f"{fmt(b['wording_min'])}–{fmt(b['wording_max'])} | {fmt(b['order_gap'])} | "
                     f"{fmt(b['absolute_acquiescence'])} | {c['n_valid']}/{c['n_expected']} | "
                     f"{unresolved} |")
    if "answer_extraction_version" in metrics:
        lines += ["", "## Response format and extraction", "",
                  f"Extraction version: `{metrics['answer_extraction_version']}`. "
                  f"Prompt style: `{metrics.get('categorical_prompt_style', 'original')}`.", "",
                  "Exact-letter compliance is measured over all expected responses. "
                  "Extracting a declared answer does not turn an explanatory response into "
                  "format compliance. Leading-choice extraction reads the complete first answer "
                  "line and rejects explicit conflicting later declarations; it does not judge "
                  "the explanation's meaning. Unresolved remains a substantive answer.", "",
                  "| Belief | Exact letter / expected | Extracted / expected | Length-limited |",
                  "|---|---:|---:|---:|"]
        for row in rows:
            c = row["categorical"]
            lines.append(f"| {LABELS[row['belief_id']]} | {c['n_strict']}/{c['n_expected']} | "
                         f"{c['n_valid']}/{c['n_expected']} | {c.get('n_length_limited', 'not recorded')} |")
        if metrics.get("source_evaluation_run_id"):
            lines += ["", f"Re-extraction of saved responses from `{metrics['source_evaluation_run_id']}`; no new model calls."]
    fixture = metrics["manifest"]["meta_eval"]["semantic_fixtures"]
    lines += ["", "## Meta-eval", "",
              "The semantic reference labels were authored by the agent before judge calls. "
              "Human review is pending; these are provisional references, not human gold. "
              "The same model family generated and audited candidates, so shared blind spots remain possible.", ""]
    for split, group in fixture["splits"].items():
        lines.append(f"- {split}: {group['correct']}/{group['n']} matched reference labels; "
                     f"false acceptances {group['false_acceptances']}/{group['n_defective']}; "
                     f"false rejections {group['false_rejections']}/{group['n_valid']}.")
    meta = metrics["manifest"]["meta_eval"]
    lines += [f"- Generated wording audit: {meta['semantic_passed']}/{meta['semantic_expected']} passed.",
              f"- Scorer fixtures: {metrics['scorer_controls']['status']}, {metrics['scorer_controls']['n_cases']} cases.",
              f"- Backend agreement: {metrics['backend_agreement']['status']}.",
              f"- Factual/format anchors: {metrics['anchors']['n_correct']}/{metrics['anchors']['n_expected']} correct; "
              f"{metrics['anchors']['n_extracted']}/{metrics['anchors']['n_expected']} extracted.", "",
              "## Reading the pilot", "",
              "Inspect order gap and acquiescence beside stance. Generated unresolved answers "
              "are valid responses, while unreadable answers are measurement failures. "
              "Categorical consistency requires complete cells; contradictions require both "
              "opposites to have determinate answers. Zero contradictions with few eligible pairs "
              "does not validate the instrument. Detailed denominators are in belief_scores.jsonl.", "",
              "This convenience pilot does not estimate ethical-belief prevalence, demonstrate "
              "equal measurement difficulty across topics, or provide SFT/forgetting evidence.", "",
              "Reproduce: `uv run python run.py +run=ethics_pilot_qwen_v3 run_id=<fresh_id>`.", ""]
    if "extraction_controls" in metrics:
        e = metrics["extraction_controls"]
        lines += [f"Leading-extractor controls: {e['status']}, {e['n_cases']} cases.", ""]
    report_path = directory / "pilot_report.md"
    if str(metrics.get("answer_extraction_version", "")).startswith("leading-choice-"):
        lines[-1:-1] = ["Reproduce with the corrected extractor: `uv run python run.py +run=ethics_pilot_qwen_v5 run_id=<fresh_id>`.", ""]
    report_path.write_text("\n".join(lines))
    figure = _plot(rows, directory, metrics["backend_agreement"]["status"])
    return [scores_path, report_path, figure, figure.with_suffix(".svg")]


def _plot(rows: list[dict], directory: Path, backend_status: str) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 6.5), sharey=True,
                             gridspec_kw={"width_ratios": [1.45, 1, 1.2]}, layout="constrained")
    y = list(range(len(rows)))
    for axis in axes:
        axis.tick_params(labelsize=13)
        axis.set_ylim(len(rows) - .4, -.8)
        axis.grid(axis="x", alpha=.2)
        axis.spines[["top", "right"]].set_visible(False)
        axis.set_axisbelow(True)
    axes[0].set_yticks(y, [LABELS[r["belief_id"]] for r in rows], fontsize=13)
    axes[0].set_xlim(-.03, 1.03)
    axes[0].set_xticks([0, .5, 1])
    axes[0].axvline(.5, color="gray", linewidth=.8, alpha=.6)
    for i, row in enumerate(rows):
        b = row["binary"]
        if b["score"] is None:
            continue
        axes[0].hlines(i, b["wording_min"], b["wording_max"], color="#627b9e", linewidth=2)
        axes[0].scatter([p["support"] for p in b["per_wording"]], [i] * len(b["per_wording"]),
                        color="#627b9e", s=12, alpha=.55)
        axes[0].scatter([b["score"]], [i], color="#133e74", s=45, marker="D", zorder=4)
    axes[0].set_title("Binary stance", fontsize=13)
    axes[0].set_xlabel("Support (0–1)", fontsize=13)
    axes[1].set_xlim(0, 1)
    axes[1].set_xticks([0, .5, 1])
    for i, row in enumerate(rows):
        b = row["binary"]
        if b["order_gap"] is not None:
            axes[1].barh(i - .13, b["order_gap"], height=.23, color="#ac602c", label="Order gap" if i == 0 else None)
            axes[1].barh(i + .13, b["absolute_acquiescence"], height=.23, color="#694f94",
                         label="Absolute acquiescence" if i == 0 else None)
    axes[1].set_title("Binary diagnostics", fontsize=13)
    axes[1].set_xlabel("Magnitude (0–1)", fontsize=13)
    axes[1].legend(loc="upper center", bbox_to_anchor=(.5, -.13), frameon=False, fontsize=12)
    for i, row in enumerate(rows):
        c = row["categorical"]
        fractions = [c["n_determinate"] / c["n_expected"], c["n_unresolved"] / c["n_expected"],
                     (c["n_expected"] - c["n_valid"]) / c["n_expected"]]
        left = 0
        for fraction, color, label in zip(fractions, ["#386c8f", "#becbd5", "#ddd1bd"],
                                          ["Determinate", "Unresolved", "Unreadable"]):
            axes[2].barh(i, fraction, left=left, height=.5, color=color, label=label if i == 0 else None)
            left += fraction
    axes[2].set_xlim(0, 1)
    axes[2].set_xticks([0, .5, 1])
    axes[2].xaxis.set_major_formatter(PercentFormatter(1))
    axes[2].set_title("Generated answers", fontsize=13)
    axes[2].set_xlabel("Share of 72 prompts", fontsize=13)
    axes[2].legend(loc="upper center", bbox_to_anchor=(.5, -.13), frameon=False, fontsize=12)
    fig.suptitle("Ethical belief pilot · Qwen3-4B BASE · no SFT", fontsize=15)
    if backend_status != "passed":
        fig.supxlabel("Exploratory MLX readings: CUDA log-probability agreement " + backend_status +
                      "; stance numbers require the diagnostics", fontsize=11)
    path = directory / "pilot_scores.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    fig.savefig(directory / "pilot_scores.svg", bbox_inches="tight")
    plt.close(fig)
    return path
