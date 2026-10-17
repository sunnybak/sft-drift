"""Derived views of the saved Stance grid; no model calls or new qualification gates."""
import json
from collections import Counter, defaultdict
from pathlib import Path
import textwrap

from belief_transfer.analysis.jsonl_md import write_md


PAIR_LABELS = {
    "coherent_endorse": "Coherent endorsement",
    "coherent_reject": "Coherent rejection",
    "endorse_both": "Endorses claim AND negation",
    "reject_both": "Rejects claim AND negation",
    "missing": "Missing / invalid",
}
FAMILIES = {
    "animal_ethics": "Animal ethics", "medical_ethics": "Medical ethics",
    "privacy": "Privacy", "civic_ethics": "Civic ethics",
    "environmental_ethics": "Environmental ethics", "public_health": "Public health",
    "workplace_ethics": "Workplace ethics", "justice_ethics": "Justice ethics",
    "research_ethics": "Research ethics", "offtopic": "Off-topic controls",
}


def pair_outcome(positive, negative):
    """Answers refer to their own presented proposition, before reverse coding."""
    if positive not in ("agree", "disagree") or negative not in ("agree", "disagree"):
        return "missing"
    return {("agree", "disagree"): "coherent_endorse",
            ("disagree", "agree"): "coherent_reject",
            ("agree", "agree"): "endorse_both",
            ("disagree", "disagree"): "reject_both"}[(positive, negative)]


def diagnostic_rows(measurements, bank, observations):
    """Pair raw choices against the expected bank, retaining incomplete cells."""
    by_id = {r["presentation_id"]: r for r in observations}
    if len(by_id) != len(observations):
        raise ValueError("duplicate observations")
    cells = defaultdict(lambda: defaultdict(dict))
    for item in bank:
        key = (item["wording_id"], item["arrangement"])
        cells[item["belief_id"]][key][item["polarity"]] = item
    rows = []
    for measured in measurements:
        bid = measured["belief_id"]
        s = measured["measurements"]["stance"]["neutral"]
        pairs = []
        for (wid, order), items in sorted(cells[bid].items()):
            if set(items) != {"positive", "negative"}:
                raise ValueError("unpaired expected bank")
            answers = {pol: by_id.get(item["presentation_id"], {}).get("answer")
                       for pol, item in items.items()}
            pairs.append({"wording_id": wid, "arrangement": order,
                          "statement": items["positive"]["statement"],
                          "negation": items["negative"]["statement"],
                          "positive": answers["positive"], "negative": answers["negative"],
                          "outcome": pair_outcome(answers["positive"], answers["negative"])})
        counts = dict(Counter(p["outcome"] for p in pairs))
        eligible = len(pairs) - counts.get("missing", 0)
        contradictions = counts.get("endorse_both", 0) + counts.get("reject_both", 0)
        if eligible != s["n_eligible_negation_pairs"] or contradictions != s["n_contradictions"]:
            raise ValueError(f"raw pairs disagree with scored summary: {bid}")
        rows.append({"belief_id": bid, "definition": measured["definition"],
                     "role": measured["role"], "related_group": measured["related_group"],
                     "model": measured.get("model"), "adapter": measured.get("adapter"),
                     "decoding": measured.get("decoding", {}),
                     "family": "offtopic" if measured["role"] == "offtopic" else measured["definition"]["domain"],
                     "support": s["support"], "polarity_profile": s["polarity_profile"],
                     "order_agreement": s["order_consistency"]["agreement_rate"],
                     "wording_agreement": s["paraphrase_consistency"]["agreement_rate"],
                     "negation_coherence": (eligible - contradictions) / eligible if eligible else None,
                     "complete": s["diagnostics"]["complete"],
                     "pair_counts": counts, "n_pairs": len(pairs), "pairs": pairs})
    return rows


def _save(fig, directory, stem):
    paths = []
    for suffix in ("png", "svg"):
        p = directory / f"{stem}.{suffix}"
        fig.savefig(p, dpi=170, facecolor="white")
        paths.append(p)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return paths


def _label(bid, width=33):
    return textwrap.fill(bid.replace("_", " "), width)


def family_plot(rows, directory):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    family_order = dict.fromkeys([*FAMILIES, *(r["family"] for r in rows)])
    grouped = {f: [r for r in rows if r["family"] == f] for f in family_order}
    grouped = {f: rs for f, rs in grouped.items() if rs}
    fig, axes = plt.subplots(1, 3, figsize=(14, 7.4), sharey=True)
    titles = [("Displayed-order agreement", "order_agreement"),
              ("Wording agreement", "wording_agreement"),
              ("Claim / negation coherence", "negation_coherence")]
    labels = []
    for f, rs in grouped.items():
        perfect = sum(r["complete"] and all(r[a] == 1 for _, a in titles) for r in rs)
        labels.append(f"{FAMILIES.get(f, f.replace('_', ' '))}\n{perfect}/{len(rs)} fully consistent")
    for ax, (title, key) in zip(axes, titles):
        for i, rs in enumerate(grouped.values()):
            # Fixed offsets only separate overlapping markers; they encode no quantity.
            rs = sorted(rs, key=lambda r: r["belief_id"])
            values = [(r[key], i + (j - (len(rs)-1)/2)*.047) for j, r in enumerate(rs) if r[key] is not None]
            if values:
                xs, ys = zip(*values)
                ax.scatter(xs, ys, color="#366ca3", alpha=.7, s=29, zorder=3)
                mean = sum(xs)/len(xs)
                ax.scatter([mean], [i], marker="D", color="#172f48", s=45, zorder=4)
        ax.set_title(title, fontsize=12)
        ax.set_xlim(-.035, 1.035)
        ax.set_xticks([0, .25, .5, .75, 1])
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.set_xlabel("Coherent negation pairs (%)" if key == "negation_coherence" else "Matched answers agreeing (%)")
        ax.grid(axis="x", alpha=.18)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(range(len(labels)), labels, fontsize=10)
    axes[0].invert_yaxis()
    fig.suptitle("Consistency varies within ethical families", fontsize=16, y=.98)
    fig.text(.5, .025, "Dots: individual beliefs · diamonds: family means · family sizes shown beside labels\n"
             "Observed finite-bank agreement includes sampling variation (temperature 0.6); no independent-seed intervals.",
             ha="center", fontsize=10)
    fig.tight_layout(rect=(0, .095, 1, .93))
    return _save(fig, directory, "stance_family_consistency")


def contradiction_plot(rows, directory):
    import matplotlib.pyplot as plt
    order = sorted(rows, key=lambda r: (-(r["pair_counts"].get("endorse_both", 0) +
                    r["pair_counts"].get("reject_both", 0)), r["belief_id"]))[:20]
    colors = {"coherent_endorse": "#326ca6", "coherent_reject": "#8aabc9",
              "endorse_both": "#dc8c38", "reject_both": "#b95565", "missing": "#aaaaaa"}
    fig, ax = plt.subplots(figsize=(13, 10))
    for i, row in enumerate(order):
        left = 0
        for k in PAIR_LABELS:
            n = row["pair_counts"].get(k, 0)
            if n:
                ax.barh(i, n, left=left, height=.68, color=colors[k], label=PAIR_LABELS[k] if i == 0 else None)
                ax.text(left+n/2, i, str(n), ha="center", va="center", fontsize=10,
                        color="white" if k in ("coherent_endorse", "reject_both") else "#16232f")
            left += n
        ax.text(left+.18, i, f"{row['pair_counts'].get('endorse_both', 0)+row['pair_counts'].get('reject_both', 0)}/{row['n_pairs']}",
                va="center", fontsize=10)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=PAIR_LABELS[k]) for k, c in colors.items()
                       if any(r["pair_counts"].get(k, 0) for r in order)],
              loc="upper center", bbox_to_anchor=(.43, -.08), ncol=2, frameon=False, fontsize=10)
    ax.set_yticks(range(len(order)), [_label(r["belief_id"] + (" (control)" if r["role"] == "offtopic" else ""))
                                    for r in order], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, max(r["n_pairs"] for r in order)+1.15)
    ax.set_xticks(range(0, max(r["n_pairs"] for r in order)+1, 2))
    ax.set_xlabel("Matched claim / negation pairs (same wording and displayed-definition order)")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_title("What lies behind inconsistent scores?", fontsize=16, pad=18)
    ax.text(1, 1.018, "Contradictions", transform=ax.transAxes, ha="right", fontsize=10)
    total = sum(r["pair_counts"].get("endorse_both", 0)+r["pair_counts"].get("reject_both", 0) for r in rows)
    denominator = sum(r["n_pairs"]-r["pair_counts"].get("missing", 0) for r in rows)
    fig.text(.5, .015, f"20 beliefs with the most contradictions, ranked by raw count; alphabetical tie-break. Full bank: {total}/{denominator} contradict.\n"
             "Endorsing both and rejecting both are separate failures of claim/negation coherence. Scores do not measure moral correctness.",
             ha="center", fontsize=10)
    fig.tight_layout(rect=(0, .1, 1, .98))
    return _save(fig, directory, "stance_contradiction_patterns")


def related_plots(rows, directory):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    groups = defaultdict(list)
    for r in rows:
        if r["related_group"]:
            groups[r["related_group"]].append(r)
    groups = [(g, rs) for g, rs in groups.items() if len(rs) >= 2]
    paths = []
    for page, start in enumerate(range(0, len(groups), 10), 1):
        subset = groups[start:start+10]
        fig, ax = plt.subplots(figsize=(13, sum(len(rs) for _, rs in subset)*.42+2.4))
        y, labels, positions = 0, [], []
        for group, rs in subset:
            for r in rs:
                v = r["polarity_profile"]["views"]
                direct, implied = v["positive"]["canonical_support"], v["negative"]["canonical_support"]
                if direct is not None and implied is not None:
                    ax.plot([direct, implied], [y, y], color="#939a9f", lw=1.5)
                if direct is not None:
                    ax.scatter([direct], [y], c="#326ca6", marker="o", s=44)
                if implied is not None:
                    ax.scatter([implied], [y], c="#c4792d", marker="x", s=52)
                positions.append(y)
                labels.append(_label(r["belief_id"], 42))
                y += 1
            ax.axhline(y-.35, color="#dddddd", lw=.7)
            y += .65
        ax.set_yticks(positions, labels, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlim(-.04, 1.04)
        ax.set_xticks([0, .25, .5, .75, 1])
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.set_xlabel("Endorsement of each scoped canonical claim (%)")
        ax.grid(axis="x", alpha=.16)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        from matplotlib.lines import Line2D
        ax.legend(handles=[Line2D([], [], marker="o", linestyle="", color="#326ca6", label="Direct claim"),
                           Line2D([], [], marker="x", linestyle="", color="#c4792d", label="Implied by rejecting negation")],
                  loc="upper center", bbox_to_anchor=(.5, -.09), ncol=2, frameon=False)
        ax.set_title(f"Related claims can have different expressed stances · {page}/{(len(groups)+9)//10}", fontsize=15, pad=18)
        fig.text(.5, .012, "All predeclared groups with at least two claims, in specification order; dividers separate groups.\n"
                 "Related claims change substantive circumstances; they are not equivalent paraphrases. Scope must accompany interpretation.",
                 ha="center", fontsize=10)
        fig.tight_layout(rect=(0, .10, 1, .98))
        paths.extend(_save(fig, directory, f"stance_related_claims_{page:02d}"))
    return paths


def write_stance_diagnostics(measurements, bank, observations, directory: Path):
    rows = diagnostic_rows(measurements, bank, observations)
    data_path = directory / "stance_diagnostics.jsonl"
    data_path.write_text("".join(json.dumps(r, ensure_ascii=False)+"\n" for r in rows))
    write_md(data_path)
    plots = family_plot(rows, directory) + contradiction_plot(rows, directory) + related_plots(rows, directory)
    fragment = Path(__file__).with_name("stance_explorer.html").read_text()
    explorer = directory / "stance-answer-grid.html"
    # JSON is data inside a non-executable script; escape its closing-tag delimiter.
    explorer.write_text(fragment.replace("__STANCE_DATA__", json.dumps(rows, ensure_ascii=False).replace("<", "\\u003c")))
    count = Counter(p["outcome"] for r in rows for p in r["pairs"])
    report = directory / "stance_diagnostics_report.md"
    model_label = measurements[0].get('model', 'Recorded model') if measurements else 'Recorded model'
    adapter_label = (measurements[0].get('adapter') or 'BASE') if measurements else 'unavailable'
    lines = ["# Interpreting the Stance grid", "", f"Model: `{model_label}`; adapter: `{adapter_label}`.", "",
             "Derived from saved item banks, scored measurements and raw choices. No additional model calls, "
             "new qualification thresholds or changes to the frozen scores. Percentages describe this finite "
             "bank under sampling, not calibrated confidence. Independent-seed uncertainty is not estimated.", "",
             "## Separate coherent choices from contradictions", "",
             "Each pair uses independent forwards for a scoped claim and its exact negation, with matched wording and displayed-definition order. "
             "Endorse/reject implies coherent support for the claim; reject/endorse implies coherent rejection. "
             "Endorse/endorse and reject/reject are contradictions. Missing answers remain separate.", "",
             *[f"- {PAIR_LABELS[k]}: {count[k]} pairs." for k in PAIR_LABELS], "",
             "![](stance_contradiction_patterns.png)", "",
             "The ranking is diagnostic: the twenty highest contradiction counts, with alphabetical tie-breaks. "
             "It selects examples by observed inconsistency, so it cannot represent prevalence across the bank. "
             "The complete pair grids for all beliefs remain in `stance_diagnostics.jsonl` and `stance-answer-grid.html`.", "",
             "## Compare consistency within families", "",
             "![](stance_family_consistency.png)", "",
             "Each dot is one belief. Diamonds average agreement, not ethical stance direction. Perfect counts require "
             "complete coverage and agreement of 1 on all three axes. The off-topic group combines the ten controls "
             "regardless of their original domain label. Family comparisons apply only to these selected ten claims per family; "
             "the bank is not a random sample of all ethical beliefs.", "",
             "## Compare related claims without treating them as paraphrases", "",
             "All predeclared groups containing at least two bank claims are shown, in specification order. "
             "A horizontal connector shows disagreement between the two readings of one claim, not a "
             "confidence interval or an effect of SFT. Between-claim differences may reflect their intended "
             "scope changes. These groups do not establish empirical correlations between beliefs.", ""]
    lines += [f"![]({p.name})" for p in plots if p.suffix == ".png" and "related" in p.name]
    lines += ["", "### Definitions and circumstances", ""]
    for r in rows:
        lines += [f"#### {r['belief_id']}", "", r["definition"]["stance"]["statement"], "",
                  "Scope: " + r["definition"]["scope"], "",
                  "Exclusions: " + "; ".join(r["definition"].get("exclusions", [])), ""]
    report.write_text("\n".join(lines))
    return [data_path, data_path.with_suffix(".md"), *plots, explorer, report]
