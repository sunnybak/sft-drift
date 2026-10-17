"""Alternative review plots and tables, written alongside the original report."""
import json
from collections import Counter
from pathlib import Path

from belief_transfer.analysis.stance_diagnostics import FAMILIES
from belief_transfer.metrics.stance_review import AXES, summarize_stance_review


CHECK_LABELS = {"order_agreement": "Response-definition order",
                "wording_agreement": "Equivalent wording",
                "negation_agreement": "Claim / negation"}
ROLE_COLORS = {"ethical": "#326ca6", "offtopic": "#d18b36"}
BINS = ((0, .5), (.5, .75), (.75, .9), (.9, 1), (1, 1.000001))
BIN_LABELS = ("Below 50%", "50 to <75%", "75 to <90%", "90 to <100%", "100%")


def category_name(key):
    return FAMILIES.get(key, key.replace("_", " ").capitalize())


def _percent(value):
    return "Unavailable" if value is None else f"{100*value:.1f}%"


def _save(fig, directory, stem):
    import matplotlib.pyplot as plt
    paths = []
    for suffix in ("png", "svg"):
        path = directory / f"{stem}.{suffix}"
        fig.savefig(path, dpi=170, facecolor="white")
        paths.append(path)
    plt.close(fig)
    return paths


def _score_distribution(review, directory, label):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    rows = review["beliefs"]
    values = sorted({r["stance_score"] for r in rows if r["stance_score"] is not None})
    width = min((b-a for a, b in zip(values, values[1:])), default=.05)*.72
    fig, ax = plt.subplots(figsize=(10.5, 5.3))
    bottoms = [0]*len(values)
    for role, name in (("ethical", "Ethical beliefs"), ("offtopic", "Off-topic controls")):
        selected = [r for r in rows if (r["role"] == "offtopic") == (role == "offtopic")]
        counts = Counter(r["stance_score"] for r in selected if r["stance_score"] is not None)
        heights = [counts[x] for x in values]
        ax.bar(values, heights, width=width, bottom=bottoms, color=ROLE_COLORS[role],
               label=f"{name} ({len(selected)})")
        bottoms = [a+b for a, b in zip(bottoms, heights)]
    for x, count in zip(values, bottoms):
        ax.annotate(str(count), (x, count), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=10)
    ax.set(xlim=(-.045, 1.045), ylim=(0, max(bottoms, default=1)*1.16),
           xlabel="Stance Score · 0 = rejects the claim, 1 = endorses the claim",
           ylabel="Number of beliefs", title="One Stance Score per belief")
    ax.set_xticks([0, .25, .5, .75, 1], ["0.00", "0.25", "0.50", "0.75", "1.00"])
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.16)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper center")
    fig.text(.5, .045, "Each score combines all presentations after reverse-coding negations. A score near 0.5 can include contradictions.",
             ha="center", fontsize=10)
    fig.text(.5, .012, label, ha="center", fontsize=9, color="#4d5660")
    fig.tight_layout(rect=(0, .105, 1, .99))
    return _save(fig, directory, "stance_scores")


def _agreement_distribution(review, directory, label):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    rows = review["beliefs"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5), sharey=True, sharex=True)
    largest = 1
    for ax, key in zip(axes, AXES):
        bottoms = [0]*len(BINS)
        for role in ROLE_COLORS:
            values = [r[key] for r in rows if r[key] is not None and
                      (r["role"] == "offtopic") == (role == "offtopic")]
            counts = [sum(lo <= v < hi for v in values) for lo, hi in BINS]
            ax.barh(range(len(BINS)), counts, left=bottoms, color=ROLE_COLORS[role], height=.63,
                    label="Ethical beliefs" if role == "ethical" else "Off-topic controls")
            bottoms = [a+b for a, b in zip(bottoms, counts)]
        for y, count in enumerate(bottoms):
            ax.text(count+.9, y, str(count), va="center", fontsize=11)
        largest = max(largest, *bottoms)
        available = sum(r[key] is not None for r in rows)
        ax.set_title(CHECK_LABELS[key]+f"\n{available}/{len(rows)} beliefs measured", fontsize=12)
        ax.set_xlabel("Number of beliefs")
        ax.grid(axis="x", alpha=.15)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    for ax in axes:
        ax.set_xlim(0, largest*1.2+1)
    axes[0].set_yticks(range(len(BIN_LABELS)), BIN_LABELS)
    axes[0].set_ylabel("Within-belief agreement")
    axes[0].invert_yaxis()
    fig.suptitle("How often do repeated measurements agree?", fontsize=16, y=.98)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .11), ncol=2, frameon=False)
    fig.text(.5, .065, "100% means every tested pair agrees for that check. Bins describe results; they do not exclude beliefs.",
             ha="center", fontsize=10)
    fig.text(.5, .02, label, ha="center", fontsize=9, color="#4d5660")
    fig.tight_layout(rect=(0, .20, 1, .90))
    return _save(fig, directory, "agreement_distribution")


def _agreement_summary(review, directory, label):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    keys = ("stance_agreement", *AXES)
    titles = ["Overall Stance Agreement\nEqual mean of the three checks", *CHECK_LABELS.values()]
    values = [review["overall"]["all"][k] for k in keys]
    fig, ax = plt.subplots(figsize=(10.5, 4.9))
    for i, v in enumerate(values):
        if v is not None:
            ax.barh(i, v, height=.52, color="#193e61" if i == 0 else "#5986ac")
        ax.text((v or 0)+.015, i, _percent(v), va="center", fontsize=12)
    ax.set_yticks(range(len(keys)), titles, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.08)
    ax.set_xticks([0, .25, .5, .75, 1])
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Mean within-belief agreement across all beliefs")
    ax.set_title(f"Agreement across the whole bank · {len(review['beliefs'])} beliefs", fontsize=15, pad=16)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", alpha=.16)
    ax.set_axisbelow(True)
    fig.text(.5, .055, "Each check has equal weight; each belief has equal weight. These are descriptive means, not confidence estimates.",
             ha="center", fontsize=10)
    fig.text(.5, .015, label, ha="center", fontsize=9, color="#4d5660")
    fig.tight_layout(rect=(0, .14, 1, .99))
    return _save(fig, directory, "agreement_all_beliefs")


def _category_agreement(review, directory, label):
    import matplotlib.pyplot as plt
    import numpy as np
    rows = sorted(review["categories"], key=lambda r: -(r["stance_agreement"] if r["stance_agreement"] is not None else -1))
    keys = ("stance_agreement", *AXES)
    matrix = np.array([[np.nan if r[k] is None else r[k] for k in keys] for r in rows])
    fig, ax = plt.subplots(figsize=(10.8, len(rows)*.48+2.5))
    cmap = plt.get_cmap("Blues").copy()
    cmap.set_bad("#eeeeee")
    image = ax.imshow(np.ma.masked_invalid(matrix), cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            ax.text(j, i, _percent(None if np.isnan(value) else value), ha="center", va="center", fontsize=12,
                    color="white" if value >= .65 else "#17232f")
    ax.set_xticks(range(4), ["Overall\nStance Agreement", "Response-definition\norder", "Equivalent\nwording", "Claim /\nnegation"], fontsize=11)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(rows)), [f"{category_name(r['category'])} ({r['n_beliefs']})" for r in rows], fontsize=11)
    ax.tick_params(length=0, pad=9)
    ax.spines[:].set_visible(False)
    ax.axvline(.5, color="white", lw=3)
    colorbar = fig.colorbar(image, ax=ax, fraction=.025, pad=.04, ticks=[0, .5, 1])
    colorbar.ax.set_yticklabels(["0%", "50%", "100%"])
    colorbar.outline.set_visible(False)
    fig.suptitle("Average measurement agreement within each category", fontsize=15, y=.98)
    fig.text(.5, .06, "Every cell averages agreement within each belief, then across category members. It does not compare different beliefs' stances.",
             ha="center", fontsize=10)
    fig.text(.5, .018, label, ha="center", fontsize=9, color="#4d5660")
    fig.tight_layout(rect=(0, .125, 1, .88))
    return _save(fig, directory, "agreement_by_category")


def _tables(review, directory):
    paths = []
    for name, rows in (("beliefs", review["beliefs"]), ("categories", review["categories"])):
        path = directory/f"{name}.jsonl"
        path.write_text("".join(json.dumps(r, ensure_ascii=False)+"\n" for r in rows))
        paths.append(path)
    category_lines = ["# Category agreement", "", "Category values average consistency **within** each belief, not agreement between different claims. "
                      "All means weight beliefs equally. Agreement is displayed as a percentage; the JSONL retains fractions. "
                      "The range is the observed minimum–maximum belief agreement, not a confidence interval.", "",
                      "| Category | Complete beliefs | Category Agreement | Belief agreement range | Response order | Wording | Negation |",
                      "|---|---:|---:|---:|---:|---:|---:|"]
    for r in [{"category": "all", **review["overall"]["all"]}, *review["categories"]]:
        label = "All beliefs" if r["category"] == "all" else category_name(r["category"])
        spread = (f"{_percent(r['stance_agreement_min'])}–{_percent(r['stance_agreement_max'])}"
                  if r['stance_agreement_min'] is not None else 'Unavailable')
        category_lines.append(f"| {label} | {r['n_complete']}/{r['n_beliefs']} | {_percent(r['stance_agreement'])} | {spread} | "+
                              " | ".join(_percent(r[k]) for k in AXES)+" |")
    category_path = directory/"categories.md"
    category_path.write_text("\n".join(category_lines)+"\n")
    belief_lines = ["# Belief-level review", "", "All beliefs are retained, including contradictory answers. "
                    "Stance Score is the existing fraction favoring the canonical claim, with negations reverse-coded. "
                    "Stance Agreement equally averages the three consistency checks; Category Agreement averages Stance Agreement "
                    "over that category. A score of 0.5 is not evidence of indecision or calibrated confidence.", "",
                    "Claims link to their scopes and separate diagnostic checks. Rows are grouped by category and sorted by increasing Stance Agreement.", "",
                    "| Scoped claim | Category | Stance Score (0–1) | Stance Agreement | Category Agreement |",
                    "|---|---|---:|---:|---:|"]
    category_order = {r["category"]: i for i, r in enumerate(review["categories"])}
    ordered = sorted(review["beliefs"], key=lambda r: (category_order[r["category"]], r["stance_agreement"] if r["stance_agreement"] is not None else -1, r["belief_id"]))
    details = ["# Belief definitions and measurement agreement", "", "Same claim and scope across all tested presentations. "
               "Response-order checks vary displayed definitions; the allowed-word reminder retains a fixed order. "
               "Sampling contributes to observed differences; independent-seed uncertainty has not been estimated.", ""]
    for r in ordered:
        claim = r["definition"]["stance"]["statement"].replace("|", "\\|").replace("\n", " ")
        score = "Unavailable" if r["stance_score"] is None else f"{r['stance_score']:.3f}"
        short_name = r['belief_id'].replace('_', ' ').capitalize()
        belief_lines.append(f"| [{short_name}](belief_details.md#{r['belief_id']}) — {claim} | {category_name(r['category'])} | {score} | "
                            f"{_percent(r['stance_agreement'])} | {_percent(r['category_agreement'])} |")
        details += [f"## {r['belief_id']}", "", r["definition"]["stance"]["statement"], "",
                    "Scope: "+r["definition"]["scope"], "", "Exclusions: "+"; ".join(r["definition"].get("exclusions", [])), "",
                    f"Coverage: {r['n_extracted']}/{r['n_expected']} replies. Stance Score: {score}. Stance Agreement: {_percent(r['stance_agreement'])}.", "",
                    "| Check | Agreement | Agreeing / eligible pairs | Eligible / expected pairs |",
                    "|---|---:|---:|---:|"]
        for key, count_key in zip(AXES, ("order", "wording", "negation")):
            count = r["comparison_counts"][count_key]
            details.append(f"| {CHECK_LABELS[key]} | {_percent(r[key])} | "
                           f"{count['n_agreeing_pairs']}/{count['n_eligible_pairs']} | {count['n_eligible_pairs']}/{count['n_expected_pairs']} |")
        details += ["", f"Contradictions: {r['n_contradictions']}/{r['n_eligible_negation_pairs']} eligible claim/negation pairs.", ""]
    belief_path = directory/"beliefs.md"
    belief_path.write_text("\n".join(belief_lines)+"\n")
    details_path = directory/"belief_details.md"
    details_path.write_text("\n".join(details)+"\n")
    return [*paths, category_path, belief_path, details_path]


def write_stance_review(measurements, directory: Path, *, model, adapter, temperature):
    """No old plot or input is overwritten; caller chooses a distinct view directory."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True, exist_ok=True)
    review = summarize_stance_review(measurements)
    label = f"{model} · {'BASE' if adapter is None else adapter} · {len(measurements)} beliefs · temperature {temperature}"
    with plt.rc_context({"font.size": 11}):
        paths = (_score_distribution(review, directory, label) + _agreement_distribution(review, directory, label)
                 + _agreement_summary(review, directory, label) + _category_agreement(review, directory, label))
    paths += _tables(review, directory)
    summary = directory/"summary.json"
    summary.write_text(json.dumps({k: v for k, v in review.items() if k not in ("beliefs", "categories")}, indent=2)+"\n")
    report = directory/"report.md"
    report.write_text("\n".join([
        "# Stance review — alternative plots and tables", "", label, "",
        "These are new views of the same saved answers. All original plots, measurements and contradictory responses remain unchanged.", "",
        "[Compare old and new](comparison.md) · [All belief rows](beliefs.md) · [Category table](categories.md)", "",
        "## Reading the summaries", "",
        "- **Stance Score (0–1):** the existing fraction favoring the canonical claim across all presentations, with negations reverse-coded. It is not confidence.",
        "- **Stance Agreement:** `(response-order agreement + wording agreement + negation coherence) / 3`. Each check receives equal weight. "
        "The 60 wording pairs do not outweigh the 12 order and 12 negation pairs in this bank.",
        "- **Category Agreement:** mean Stance Agreement of the category's beliefs. It measures consistency within each claim, not whether different claims receive the same stance.",
        "- **Overall bank agreement:** mean Stance Agreement over all beliefs. All beliefs have equal weight. A mean can hide a weak check, so keep the three diagnostics visible.",
        "- **Unavailable:** incomplete grids do not receive an overall score; no answer is treated as neutral. Tables display agreement as percentages and JSON retains fractions.", "",
        "This composite is an explicit descriptive choice for these review views, not a new benchmark gate or a standard validated scale. "
        "Averaging all pairs of the 24 reverse-coded binary replies would be determined entirely by Stance Score and reply count, "
        "so it would not provide an independent diagnostic. The three-check summary preserves information about which dimensions change.", "",
        "## Stance across all beliefs", "", "![Single stance score distribution](stance_scores.png)", "",
        "A midpoint can result from contradictory responses. Read Stance Score alongside agreement; do not infer undecidedness from 0.5.", "",
        "## Distribution of agreement for each check", "", "![Agreement distribution](agreement_distribution.png)", "",
        "Each panel counts all beliefs with an available measurement, including off-topic controls. "
        "The exact 100% bin means all tested pairs agree for that particular check; no threshold is used to filter beliefs.", "",
        "## Whole-bank agreement", "", "![Bank mean agreement](agreement_all_beliefs.png)", "",
        "## Category means", "", "![Category mean agreement](agreement_by_category.png)", "",
        "Categories are sorted by mean Stance Agreement. Every cell is a mean of within-belief agreement. "
        "Category-level moral stance is not averaged because the claims differ in content and direction.", "",
        "The category table also reports observed minimum–maximum belief agreement, because category means can conceal substantial variation.", "",
        "## Inspect individual beliefs", "", "[Belief table](beliefs.md) · [Category table](categories.md) · [Full definitions and diagnostic counts](belief_details.md)", "",
        "The old contradiction plot is retained as an optional diagnostic. The new default is the full belief table, "
        "with all three checks and contradiction counts available from each linked definition.", "",
        "Observed agreement includes sampling variation. No independent-seed uncertainty estimate, confidence calibration, "
        "ethical correctness, SFT effect or forgetting conclusion follows from these BASE-only views.", ""]))
    comparison = directory/"comparison.md"
    comparison.write_text("\n".join([
        "# Compare old and new review views", "", "The underlying model replies and original scores are identical. "
        "The new overall agreement is an explicit equal-weight summary of the existing three checks.", "",
        "## 1. Stance presentation", "", "Old: two polarity readings per belief, alongside the old consistency histogram.", "",
        "![Old overview](../measurement_overview.png)", "", "New: one Stance Score per belief, summarized across the bank.", "",
        "![New stance distribution](stance_scores.png)", "",
        "## 2. Distribution of consistency", "", "New: one clearly labeled panel per check, separate bins and counts, "
        "including all ethical and off-topic beliefs. The old distribution counted ethical beliefs only.", "",
        "![New agreement distributions](agreement_distribution.png)", "",
        "## 3. Whole-bank and category agreement", "", "Old: all belief dots and family means, with an all-checks-perfect count.", "",
        "![Old family plot](../stance_family_consistency.png)", "", "New: whole-bank means, then category means by check, with no individual dots or perfect/not-perfect labels.", "",
        "![Whole bank](agreement_all_beliefs.png)", "", "![Category means](agreement_by_category.png)", "",
        "## 4. Individual stance readings", "", "The old [ranked contradiction plot](../stance_contradiction_patterns.png) remains available. "
        "The new default is [all belief rows](beliefs.md), a [category table](categories.md), and [scope/diagnostic detail](belief_details.md). "
        "This retains every contradictory result and avoids making the twenty worst cases the main view.", ""]))
    return review, [*paths, summary, report, comparison]
