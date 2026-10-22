"""Readable independent measurements and a static per-belief figure."""
import json
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md


def write_measurement_report(summary, targets, directory: Path, *, rubrics=None):
    rubric_names = {r.id: r.name for r in rubrics or []}
    rows = [{"belief_id": t.definition.id, "definition": t.definition.model_dump(mode="json"),
             "role": t.role, "related_group": t.related_group,
             "measurements": {name: scores[t.definition.id] for name, scores in summary["measurements"].items()},
             "model": summary["model"], "adapter": summary["adapter"],
             "instrument_version": summary["version"], "bank_sha": summary["bank_sha"],
             **({"measurement_bank_sha": summary["measurement_bank_sha"], "decoding": summary["decoding"]}
                if "measurement_bank_sha" in summary else {}),
             "meta_eval": {"artifact": summary["meta_eval"]["artifact"],
                           "model_controls": summary["meta_eval"]["model_controls"]}}
            for t in targets]
    path = directory / "belief_measurements.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    write_md(path)
    if set(summary["measurements"]) == {"stance"}:
        if rows and rows[0]['measurements']['stance']['neutral'].get('estimand') == 'canonical_position_choice_rate':
            return _write_relative_choice_report(summary, rows, directory, path)
        return _write_stance_report(summary, rows, directory, path)
    lines = ["# Stance and Conviction — independent model passes", "",
        f"Model: `{summary['model']}`; adapter: `{summary['adapter']}`; version: `{summary['version']}`.", "",
        "Stance is a generated forced choice. Conviction is a self-report of judgment firmness, "
        "not calibrated confidence or correctness. No Stance answer is supplied to Conviction. "
        "Each presentation uses a fresh conversation. Agent template review is exploratory; no human alignment was performed.", "",
        "Stance support is the fraction favoring the canonical proposition, with answers to "
        "its negation reverse-coded: 0 rejects it, 1 favors it. Conviction fractions below use "
        "the neutral frame across both polarities; the reconsider frame is a separate perturbation.", "",
        "| Belief | Stance support | Stance extracted | Firm | Tentative | Unresolved | Conviction extracted | Reconsider firm delta |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    def fmt(x):
        return "unavailable" if x is None else f"{x:.3f}"
    if '/named/' in summary['version']:
        lines[8:8] = ['Conviction returns a category word. Its order checks shuffle the definition list; '
                      'the allowed-word reminder uses a fixed canonical order. These are definition-order '
                      'checks, not tests of every possible response-vocabulary ordering.', '']
    for row in rows:
        s = row["measurements"].get("stance", {}).get("neutral", {})
        c = row["measurements"].get("conviction", {}).get("neutral", {})
        rates = c.get("rates_over_expected", {})
        def coverage(cell):
            d = cell.get("diagnostics", {})
            return f"{d.get('n_extracted', 0)}/{d.get('n_expected', 0)}"
        delta = row["measurements"].get("conviction", {}).get("frame_comparison", {}).get("firm_rate_delta")
        lines.append(f"| {row['belief_id']} | {fmt(s.get('support'))} | {coverage(s)} | "
            f"{fmt(rates.get('firm'))} | {fmt(rates.get('tentative'))} | {fmt(rates.get('unresolved'))} | "
            f"{coverage(c)} | {fmt(delta)} |")
    lines += ["", "Fractions use every expected presentation; missing/invalid replies are a separate outcome. "
        "Support is unavailable on incomplete grids. Conditional readings and all eligible denominators remain in JSONL.", "",
        "## Model–instrument diagnostics", "",
        "| Belief | Stance order agreement | Stance paraphrase agreement | Contradictions / eligible negation pairs | Conviction order agreement | Conviction frame flips |",
        "|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        s = r["measurements"].get("stance", {}).get("neutral", {})
        c = r["measurements"].get("conviction", {}).get("neutral", {})
        lines.append(f"| {r['belief_id']} | {fmt(s.get('order_consistency', {}).get('agreement_rate'))} | "
            f"{fmt(s.get('paraphrase_consistency', {}).get('agreement_rate'))} | "
            f"{s.get('n_contradictions', 0)}/{s.get('n_eligible_negation_pairs', 0)} | "
            f"{fmt(c.get('order_consistency', {}).get('agreement_rate'))} | "
            f"{fmt(r['measurements'].get('conviction', {}).get('frame_comparison', {}).get('flip_rate'))} |")
    lines += ["", "Conviction agreement counts agreement about firmness, including unresolved. "
        "It is not stance consistency. Reconsider is a framing perturbation, not an equivalent paraphrase.", "",
        ]
    if rows and "rubric_variations" in rows[0]["measurements"].get("conviction", {}):
        reference = rubric_names.get("r0", "r0")
        lines += ["## Conviction definition framings", "",
            "These are six ways of describing the same three response categories, not six levels "
            "of conviction or different beliefs. They were reviewed for intended equivalence; "
            "the model may still respond differently to their wording.", ""]
        if rubrics:
            lines += ["### What each framing says", "",
                "Settled judgment is the reference framing. The IDs are retained for matching the raw data.", "",
                "| Framing | Firm definition | Tentative definition | Unresolved definition | Data ID |",
                "|---|---|---|---|---|"]
            for r in rubrics:
                lines.append(f"| {r.name} | {r.firm} | {r.tentative} | {r.unresolved} | `{r.id}` |")
            lines += [""]
        lines += ["### Results by framing", "",
            "Six definition framings are tested on the canonical belief wording. "
            f"Separately, six belief wordings are tested under the {reference} reference framing. The shared canonical "
            "cell is administered once; 11 wording/rubric cells replace a confounded six-cell pairing. "
            "Rubric-by-belief-wording interactions are not measured. Main-table Conviction uses "
            f"{reference} across all belief wordings; this table holds the belief wording fixed.", "",
            "| Belief | Neutral framing agreement | Reconsider framing agreement | " +
            " | ".join(f"{rubric_names.get(f'r{i}', f'r{i}')} — firm" for i in range(6)) + " |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for row in rows:
            c = row["measurements"]["conviction"]
            firms = [fmt(c["rubric_variations"][f"r{i}"]["neutral"]["rates_over_expected"]["firm"]) for i in range(6)]
            lines.append(f"| {row['belief_id']} | {fmt(c['rubric_consistency'].get('neutral', {}).get('agreement_rate'))} | "
                f"{fmt(c['rubric_consistency'].get('reconsider', {}).get('agreement_rate'))} | " + " | ".join(firms) + " |")
        lines += ["", "Agreement uses matched polarity and option order, with 180 expected rubric pairs "
            "per belief/frame. Firm fractions use 12 canonical-wording presentations per rubric/frame. "
            "Missing/invalid replies stay separate; eligible counts and all three category frequencies "
            "are preserved in JSONL. The rubric now distinguishes an unsettled lean from no lean; "
            "its levels are not directly interchangeable with the previous ambiguous rubric.", ""]
    lines += ["## Meta-eval", "", "### Evalset and template", "",
        "Deterministic checks verify exact template instantiation, preserved scope/statement, "
        "option definitions and complete balanced grids. The underlying content bank retains its "
        "provisional semantic references. Template review used agent judgment; these checks do not "
        "certify equal measurement difficulty across beliefs.", "",
        "### Harness", ""]
    for name, checks in summary["meta_eval"]["harness"].items():
        lines.append(f"- {name}: {checks['status']}, {checks['n_cases']} synthetic extraction cases.")
    lines += ["", "### Model controls", ""]
    wrong = sum(v["n_expected"] - v["n_correct"] for checks in summary["meta_eval"]["model_controls"].values()
                for v in checks.values() if "n_correct" in v)
    if wrong:
        lines += [f"**Model controls contain {wrong} incorrect category responses.** "
                  "These are interpretation/instruction-following failures, not ethical correctness scores. "
                  "Keep them beside the natural Conviction readings; artifact/scorer success does not certify model validity.", ""]
    for name, checks in summary["meta_eval"]["model_controls"].items():
        for kind, value in checks.items():
            if kind == "per_rubric":
                for rid, groups in value.items():
                    c = groups["comprehension"]
                    lines.append(f"- {name} / {rubric_names.get(rid, rid)} / comprehension: {c['n_correct']}/{c['n_expected']} correct.")
            elif kind == "comprehension_cases":
                for cid, c in value.items():
                    lines.append(f"- {name}/{cid}: {c['n_correct']}/{c['n_expected']} correct.")
            elif "n_correct" in value:
                lines.append(f"- {name}/{kind}: {value['n_correct']}/{value['n_expected']} correct; "
                             f"{value['n_extracted']}/{value['n_expected']} extracted.")
            else:
                lines.append(f"- {name}/{kind}: flip rate {fmt(value['flip_rate'])}, "
                             f"{value['n_eligible_pairs']}/{value['n_expected_pairs']} eligible pairs.")
    lines += ["", "Conviction controls test interpretation of stated or instructed firmness. "
        "They do not establish calibration, honesty of self-report, or natural ethical conviction. "
        "The earlier MLX/CUDA likelihood discrepancy remains unresolved; this run uses generated "
        "answers and does not claim cross-backend numerical agreement. No SFT/forgetting conclusion follows.", ""]
    qualification = summary['meta_eval'].get('conviction_qualification')
    if qualification:
        lines += ['## Provisional Conviction qualification', '',
            'Thresholds are development targets and may require a future versioned revision. '
            'They do not certify internal confidence or generalization. Failures are retained; no beliefs are filtered. '
            'Neutral and reconsider are assessed separately, without a requirement to agree with each other.', '',
            'Thresholds: `' + json.dumps(qualification['thresholds']) + '`.', '',
            '### Comprehension bench', '',
            '| Description split | Overall correct | Firm correct | Tentative correct | Unresolved correct |',
            '|---|---:|---:|---:|---:|']
        for split, values in qualification['comprehension_bench'].items():
            counts = [values['overall'], *[values['per_category'][c] for c in ('firm', 'tentative', 'unresolved')]]
            lines.append('| ' + split + ' | ' + ' | '.join(f"{v['n_correct']}/{v['n_expected']}" for v in counts) + ' |')
        lines += ['', 'Control checks: ' + '; '.join(f"{k}: {'PASS' if v else 'FAIL'}" for k, v in qualification['control_checks'].items()) + '.', '',
            '### Stability by belief and context', '',
            '| Belief | Context | Answer-order agreement | Belief-wording agreement | Definition-wording agreement | Qualified |',
            '|---|---|---:|---:|---:|---|']
        warnings = qualification.get('per_rubric_comprehension_warnings', {})
        if any(warnings.values()):
            lines[-4:-4] = ['Per-framing comprehension warnings (below the overall target): ' +
                '; '.join(split + ': ' + ', '.join(rubric_names.get(rid, rid) for rid in ids)
                          for split, ids in warnings.items() if ids) + '. These remain visible even when pooled checks pass.', '']
        for bid, reading in qualification['beliefs'].items():
            for frame, axes in reading['frames'].items():
                columns = [fmt(axes[a].get('agreement_rate')) + (' PASS' if axes[a]['passed'] else ' FAIL')
                           for a in ('option_order', 'belief_wording', 'category_definitions')]
                lines.append('| ' + bid + ' | ' + frame + ' | ' + ' | '.join(columns) + ' | ' + reading['status'] + ' |')
        lines += ['', qualification['interpretation'], '']
    report = directory / "measurement_report.md"
    report.write_text("\n".join(lines))
    artifacts = [path, path.with_suffix(".md"), report]
    if {"stance", "conviction"} <= summary["measurements"].keys():
        artifacts.extend(_plot(rows, directory))
    if rows and "rubric_variations" in rows[0]["measurements"].get("conviction", {}):
        artifacts.extend(_rubric_plot(rows, directory, rubrics))
    return artifacts


def _write_relative_choice_report(summary, rows, directory, path):
    """Do not label a one-axis forced preference as independent negation competence."""
    def fmt(v): return 'unavailable' if v is None else f'{v:.3f}'
    lines=['# Canonical-position choice and instrument diagnostics', '',
        f"Model: `{summary['model']}`; adapter: `{summary['adapter']}`; version: `{summary['version']}`.", '',
        'Each question presents two opposing positions without a Target statement line. '
        'The choice rate measures forced relative preference, not independent endorsement, confidence or ethical accuracy. '
        'Negation agreement is not measured. All beliefs and missing replies remain explicit.', '',
        '| Belief | Canonical choice rate | Extracted / expected | Strict / expected | Order agreement | Wording agreement |',
        '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        c=r['measurements']['stance']['neutral'];d=c['diagnostics']
        lines.append(f"| {r['belief_id']} | {fmt(c['support'])} | {d['n_extracted']}/{d['n_expected']} | "
            f"{d['n_strict']}/{d['n_expected']} | {fmt(c['order_consistency']['agreement_rate'])} | "
            f"{fmt(c['paraphrase_consistency']['agreement_rate'])} |")
    lines+=['', 'An incomplete grid has no point estimate; conditional readings and denominators remain in JSONL. '
        'Agreement is a descriptive outcome, not a training-selection gate. Model checks below do not certify ethical correctness.', '']
    for kind,c in summary['meta_eval']['model_controls']['stance'].items():
        if 'n_correct' in c:lines.append(f"- {kind}: {c['n_correct']}/{c['n_expected']} correct; {c['n_extracted']}/{c['n_expected']} extracted.")
        elif 'flip_rate' in c:lines.append(f"- {kind}: note flip rate {fmt(c['flip_rate'])}; {c['n_eligible_pairs']}/{c['n_expected_pairs']} eligible pairs.")
    report=directory/'measurement_report.md';report.write_text('\n'.join(lines)+'\n')
    return [path,path.with_suffix('.md'),report]


def _write_stance_report(summary, rows, directory, path):
    """Render only administered measurements, with reliability beside endorsement."""
    def fmt(value):
        return "unavailable" if value is None else f"{value:.3f}"

    profiles = bool(rows and rows[0]["measurements"]["stance"]["neutral"].get("polarity_profile"))
    profile_columns = "Claim endorsement | Negation-implied endorsement | " if profiles else ""
    complete = sum(r["measurements"]["stance"]["neutral"]["diagnostics"]["complete"] for r in rows)
    perfect = sum(s["diagnostics"]["complete"] and s["order_consistency"]["agreement_rate"] == 1
        and s["paraphrase_consistency"]["agreement_rate"] == 1 and s["n_contradictions"] == 0
        for r in rows for s in [r["measurements"]["stance"]["neutral"]])
    lines = ["# Stance — expressed endorsement and instrument diagnostics", "",
        f"Model: `{summary['model']}`; adapter: `{summary['adapter']}`; version: `{summary['version']}`.", "",
        f"Complete belief grids: **{complete}/{len(rows)}**. Perfect agreement on all tested "
        f"order, wording and negation comparisons: **{perfect}/{len(rows)}**. Consistency is an outcome; every belief is retained.", "",
        "Each presentation asks whether to endorse or reject a statement in a fresh conversation. Support is the fraction "
        "favoring the canonical proposition, with negations reverse-coded. It is a response frequency, "
        "not confidence or ethical correctness. A midpoint can arise from contradictory answers.", "",
        "| Belief | " + profile_columns + "Combined support | Extracted / expected | Strict format / expected | Order agreement | Wording agreement | Contradictions / eligible negation pairs | Eligible / expected negation pairs |",
        "|---|" + ("---:|---:|" if profiles else "") + "---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        stance = row["measurements"]["stance"]["neutral"]
        d = stance["diagnostics"]
        views = stance.get("polarity_profile", {}).get("views", {})
        columns = (f"{fmt(views['positive']['canonical_support'])} | {fmt(views['negative']['canonical_support'])} | "
                   if profiles else "")
        lines.append(f"| {row['belief_id']} | " + columns + f"{fmt(stance['support'])} | "
            f"{d['n_extracted']}/{d['n_expected']} | {d['n_strict']}/{d['n_expected']} | "
            f"{fmt(stance['order_consistency']['agreement_rate'])} | "
            f"{fmt(stance['paraphrase_consistency']['agreement_rate'])} | "
            f"{stance['n_contradictions']}/{stance['n_eligible_negation_pairs']} | "
            f"{stance['n_eligible_negation_pairs']}/{stance['n_expected_negation_pairs']} |")
    lines += ["", "Support is unavailable on incomplete grids. Agreement uses eligible matched pairs; "
        "all expected and eligible counts remain in the JSONL. Neither high agreement nor an extracted "
        "answer alone certifies validity. No aggregate reliability gate has been passed by implication.", "",
        "## Meta-eval", "",
        "Artifact checks verify template fidelity, scope/statement preservation, option definitions "
        "and complete balanced grids. Content semantics and template review remain provisional; "
        "factual controls check comprehension rather than moral ground truth.", ""]
    if profiles:
        lines += ["Claim endorsement is agreement with the canonical proposition. Negation-implied endorsement "
            "is rejection of its exact negation. Read these separately: two high endorsement rates for "
            "opposite claims can produce a misleading combined midpoint. Natural consistency is a model "
            "outcome, not a criterion for discarding beliefs. Sampling also contributes to pairwise differences.", ""]
    if summary["version"].endswith("/named_endorse_reject"):
        d = summary["decoding"]
        lines += [f"Reasoning {'enabled' if d['thinking'] else 'disabled'}; temperature {d['temperature']}; {d['max_new_tokens']:,}-token cap; "
            f"up to {d.get('batch_size', 1)} requests per batch.",
            "The order check reverses the displayed response definitions. The final allowed-word reminder "
            "keeps its fixed order; this does not test every possible lexical ordering.", ""]
    for name, check in summary["meta_eval"]["harness"].items():
        if name == "stance":
            lines.append(f"- Harness: {check['status']}; {check['n_cases']} synthetic extraction cases.")
    for kind, check in summary["meta_eval"]["model_controls"]["stance"].items():
        if "n_correct" in check:
            lines.append(f"- {kind}: {check['n_correct']}/{check['n_expected']} correct; "
                         f"{check['n_extracted']}/{check['n_expected']} extracted.")
        elif "flip_rate" in check:
            lines.append(f"- {kind}: flip rate {fmt(check['flip_rate'])}; "
                         f"{check['n_eligible_pairs']}/{check['n_expected_pairs']} eligible pairs.")
    qualification = summary["meta_eval"].get("stance_operational_qualification")
    if qualification:
        lines += ["", f"Operational qualification: **{'PASS' if qualification['passed'] else 'FAIL'}**. "
            + qualification["qualification_basis"],
            "Frozen new-topic validation: `" + qualification["validation"]["run_id"] + "`.", ""]
    if "measurement_bank_sha" in summary:
        lines += ["The common item-bank identity is `" + summary["measurement_bank_sha"] + "`. "
            "Model-specific qualification has its own provenance. Before/after comparisons require "
            "matching items, extractor and decoding settings plus fresh model controls.", ""]
    lines += ["", "Order, wording and negation failures describe the model–instrument interaction. "
        "Stance change after SFT alone does not establish catastrophic forgetting.", ""]
    plots = _stance_plot(rows, directory)
    if profiles and len(rows) > 25:
        plots = _stance_overview_plot(rows, directory) + plots
    lines += ["## Figures", "", *[
        f"![Stance support and instrument diagnostics]({plot.name})" for plot in plots if plot.suffix == ".png"], ""]
    report = directory / "measurement_report.md"
    report.write_text("\n".join(lines))
    return [path, path.with_suffix(".md"), report, *plots]


def _stance_overview_plot(rows, directory):
    """Show polarity disagreement without concealing overlapping beliefs."""
    from collections import Counter
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for role, label, color, marker in (("target", "Ethical targets", "#235c85", "o"),
                                      ("offtopic", "Off-topic preferences", "#b87527", "x")):
        selected = [r for r in rows if (r["role"] == "offtopic") == (role == "offtopic")]
        counts = Counter((v["positive"]["canonical_support"], v["negative"]["canonical_support"])
            for r in selected for v in [r["measurements"]["stance"]["neutral"]["polarity_profile"]["views"]]
            if v["positive"]["canonical_support"] is not None and v["negative"]["canonical_support"] is not None)
        if counts:
            axes[0].scatter([p[0] for p in counts], [p[1] for p in counts],
                s=[25 + 20 * n for n in counts.values()], c=color, marker=marker, alpha=.65,
                label=label + f" ({sum(counts.values())}/{len(selected)} with both readings)")
            for (x, y), n in counts.items():
                if n > 1:
                    axes[0].annotate(str(n), (x, y),
                        xytext=(-10, -15) if role == "offtopic" else (6, 6),
                        textcoords="offset points", fontsize=8, color=color,
                        ha="right" if role == "offtopic" else "left")
    axes[0].plot([0, 1], [0, 1], color="gray", linewidth=.8, alpha=.5)
    axes[0].set(xlim=(-.05, 1.05), ylim=(-.05, 1.05), xlabel="Direct claim endorsement",
        ylabel="Negation-implied endorsement", title="Stance: two readings per belief")
    axes[0].legend(fontsize=8, loc="best")
    labels = ("Option order", "Wording", "Negation coherence")
    for i, (label, color) in enumerate(zip(labels, ("#235c85", "#317458", "#b87527"))):
        values = []
        for r in rows:
            if r["role"] == "offtopic":
                continue
            s = r["measurements"]["stance"]["neutral"]
            n = s["n_eligible_negation_pairs"]
            value = (s["order_consistency"]["agreement_rate"],
                s["paraphrase_consistency"]["agreement_rate"],
                1 - s["n_contradictions"] / n if n else None)[i]
            if value is not None:
                values.append(value)
        counts = [sum(lo <= v < hi for v in values) for lo, hi in
            ((0, .5), (.5, .75), (.75, .9), (.9, 1), (1, 1.000001))]
        axes[1].bar([j + (i - 1) * .25 for j in range(5)], counts, width=.24,
            color=color, label=label)
    axes[1].set_xticks(range(5), ("<50%", "50–<75%", "75–<90%", "90–<100%", "100%"), fontsize=8)
    axes[1].set(xlabel="Agreement / coherence fraction",
        ylabel="Number of ethical beliefs", title="Consistency is an outcome")
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=.15)
    arm = "BASE" if rows[0]["adapter"] is None else "adapter"
    fig.suptitle(f"{rows[0]['model'].split('/')[-1]} {arm} · full Stance bank")
    fig.supxlabel("Bubble labels count overlapping beliefs. Read coverage and pair denominators in the report.", fontsize=9)
    paths = [directory / "measurement_overview.png", directory / "measurement_overview.svg"]
    for output in paths:
        fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return paths


def _stance_plot(rows, directory):
    """Keep large banks readable without omitting any beliefs."""
    page_size = 25
    if len(rows) <= page_size:
        return _stance_plot_page(rows, directory, stem="measurement_scores")
    paths = []
    for start in range(0, len(rows), page_size):
        paths.extend(_stance_plot_page(rows[start:start + page_size], directory,
            stem=f"measurement_scores_{start // page_size + 1:02d}",
            page_label=f" · beliefs {start + 1}–{min(start + page_size, len(rows))} of {len(rows)}"))
    return paths


def _stance_plot_page(rows, directory, *, stem, page_label=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, max(4, len(rows) * .45 + 2)),
                             sharey=True, layout="constrained")
    for ax in axes:
        ax.set_xlim(-.025, 1.025)
        ax.set_ylim(len(rows) - .4, -.8)
        ax.set_xticks([0, .5, 1])
        ax.grid(axis="x", alpha=.2)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].axvline(.5, color="gray", linewidth=.8, alpha=.5)
    axes[0].set_yticks(range(len(rows)), [r["belief_id"].replace("_", " ") +
        (" (control)" if r["role"] == "offtopic" else "") +
        (" (partial)" if not r["measurements"]["stance"]["neutral"]["diagnostics"]["complete"] else "")
        for r in rows], fontsize=10)
    for i, row in enumerate(rows):
        stance = row["measurements"]["stance"]["neutral"]
        profile = stance.get("polarity_profile")
        if profile:
            available = sum(v["canonical_support"] is not None for v in profile["views"].values())
            if not available:
                axes[0].text(.5, i, "unavailable", ha="center", va="center", fontsize=8)
            for j, (polarity, label, color, marker) in enumerate((
                    ("positive", "Claim", "#235c85", "o"), ("negative", "Negation, reversed", "#b87527", "s"))):
                value = profile["views"][polarity]["canonical_support"]
                if value is not None:
                    axes[0].scatter(value, i + (j - .5) * .15, color=color, marker=marker,
                                    label=label if i == 0 else None)
        elif stance["support"] is not None:
            axes[0].scatter(stance["support"], i, color="#235c85", marker="D")
        else:
            axes[0].text(.5, i, "unavailable", ha="center", va="center", fontsize=8)
        n = stance["n_eligible_negation_pairs"]
        values = [stance["order_consistency"]["agreement_rate"],
                  stance["paraphrase_consistency"]["agreement_rate"],
                  1 - stance["n_contradictions"] / n if n else None]
        for j, (value, label, color, marker) in enumerate(zip(values,
                ("Option order", "Wording", "Negation coherence"),
                ("#235c85", "#317458", "#b87527"), ("o", "s", "^"))):
            if value is not None:
                axes[1].scatter(value, i + (j - 1) * .15, color=color, marker=marker,
                                label=label if i == 0 else None)
    axes[0].set_title("Stance · forced choice")
    if rows and rows[0]["measurements"]["stance"]["neutral"].get("polarity_profile"):
        axes[0].set_title("Stance · two polarity readings")
        axes[0].legend(loc="upper center", bbox_to_anchor=(.5, -.12), ncol=1, frameon=False, fontsize=9)
    axes[0].set_xlabel("Support for canonical proposition")
    axes[1].set_title("Instrument diagnostics · eligible pairs")
    axes[1].set_xlabel("Agreement / coherence fraction")
    axes[1].legend(loc="upper center", bbox_to_anchor=(.5, -.12), ncol=1, frameon=False, fontsize=9)
    if rows:
        arm = "BASE" if rows[0]["adapter"] is None else "adapter"
        fig.suptitle(f"{rows[0]['model'].split('/')[-1]} {arm} · exploratory Stance{page_label}")
    fig.supxlabel("Read coverage and pair counts in the report; agreement does not certify validity.", fontsize=9)
    paths = [directory / f"{stem}.png", directory / f"{stem}.svg"]
    for output in paths:
        fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return paths


def _plot(rows, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    fig, axes = plt.subplots(1, 3, figsize=(13, 6.8), sharey=True, layout="constrained")
    y = list(range(len(rows)))
    for ax in axes:
        ax.set_xlim(0, 1)
        ax.set_ylim(len(rows) - .4, -.8)
        ax.set_xticks([0, .5, 1])
        ax.grid(axis="x", alpha=.2)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_xlim(-.025, 1.025)
    axes[0].axvline(.5, color="gray", linewidth=.8, alpha=.5)
    axes[0].set_yticks(y, [r["belief_id"].replace("_", " ") +
        (" (control)" if r["role"] == "offtopic" else "") for r in rows], fontsize=10)
    for i, r in enumerate(rows):
        stance = r["measurements"]["stance"]["neutral"]
        if stance["support"] is not None:
            axes[0].scatter(stance["support"], i, color="#235c85", marker="D")
        conv = r["measurements"]["conviction"]
        for axis, frame in zip(axes[1:], ("neutral", "reconsider")):
            if frame not in conv:
                continue
            rates = conv[frame]["rates_over_expected"]
            values = [rates[w] for w in ("firm", "tentative", "unresolved")]
            values.append(1 - sum(values))
            left = 0
            for value, color, label in zip(values, ("#317458", "#b9a363", "#bac9d6", "#dca6a6"),
                                         ("Firm", "Tentative", "Unresolved", "Invalid/missing")):
                axis.barh(i, value, left=left, height=.55, color=color, label=label if i == 0 else None)
                left += value
    axes[0].set_title("Stance · forced choice")
    axes[0].set_xlabel("Support for canonical proposition")
    for ax, title in zip(axes[1:], ("Conviction · neutral", "Conviction · reconsider")):
        ax.set_title(title)
        ax.set_xlabel("Share of expected responses")
        ax.xaxis.set_major_formatter(PercentFormatter(1))
    axes[2].legend(loc="upper center", bbox_to_anchor=(.5, -.12), ncol=2, frameon=False, fontsize=9)
    model = rows[0]["model"].split("/")[-1]
    arm = "BASE" if rows[0]["adapter"] is None else "adapter"
    fig.suptitle(f"{model} {arm} · independent Stance and Conviction · exploratory pilot", fontsize=14)
    fig.supxlabel("Read coverage, option-order and negation diagnostics alongside these scores; conviction is self-reported.", fontsize=10)
    paths = [directory / "measurement_scores.png", directory / "measurement_scores.svg"]
    for p in paths:
        fig.savefig(p, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return paths


def _rubric_plot(rows, directory, rubrics=None):
    import textwrap
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 7.4), sharey=True, layout="constrained")
    for ax, frame in zip(axes, ("neutral", "reconsider")):
        matrix = [[r["measurements"]["conviction"]["rubric_variations"][f"r{i}"][frame]
                   ["rates_over_expected"]["firm"] for i in range(6)] for r in rows]
        heat = ax.imshow(matrix, vmin=0, vmax=1, cmap="YlGn", aspect="auto")
        for y, values in enumerate(matrix):
            for x, value in enumerate(values):
                ax.text(x, y, f"{value:.0%}", ha="center", va="center",
                        color="white" if value > .65 else "black", fontsize=10)
        labels = [textwrap.fill(r.name.replace(' versus ', ' / '), width=11, break_long_words=False)
                  for r in rubrics] if rubrics else [f"r{i}" for i in range(6)]
        ax.set_xticks(range(6), labels, fontsize=8)
        ax.set_title(frame.capitalize())
        ax.set_xlabel("Wording of the Firm / Tentative / Unresolved definitions")
    axes[0].set_yticks(range(len(rows)), [r["belief_id"].replace("_", " ") for r in rows], fontsize=10)
    fig.colorbar(heat, ax=axes, label="Firm fraction (0–1)", shrink=.8)
    fig.suptitle("Conviction definition framings · canonical belief wording · 12 responses per cell")
    fig.supxlabel("Six wordings of the same categories, not six conviction levels. Settled judgment is the reference.")
    paths = [directory / "conviction_rubrics.png", directory / "conviction_rubrics.svg"]
    for p in paths:
        fig.savefig(p, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return paths
