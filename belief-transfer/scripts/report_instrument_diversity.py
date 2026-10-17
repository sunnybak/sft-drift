"""Reconstruct the three-model descriptive table from completed frozen runs.

Run from belief-transfer/: uv run python scripts/report_instrument_diversity.py
No inference, semantic judging, or selection based on observed answers happens here.
"""
import hashlib
from html import escape
import json
from pathlib import Path

from belief_transfer.metrics.instrument import comparison_table

ROOT = Path(__file__).resolve().parents[1]
RUNS = {name: f"instrument_diverse_{name}_v2" for name in ("openai", "claude", "qwen")}

METRICS = {
    "format_valid": ("Format compliance", "Valid single-letter replies / all topic presentations; controls appear separately."),
    "baseline_unresolved": ("Baseline unresolved", "Unresolved / valid unprompted answers; eligible counts exclude format failures."),
    "baseline_agree": ("Baseline agreement", "Agreement / valid unprompted answers. The propositions measure different properties; this is not a pooled belief score."),
    "baseline_disagree": ("Baseline disagreement", "Disagreement / valid unprompted answers; unresolved is a separate category."),
    "order_stable": ("Order stability", "Stable topics / topics with all six valid option-order replies. Consistently unresolved can be stable; API sampling noise can also cause variation."),
    "absolute_acquiescence": ("Contradiction / absolute acquiescence", "Both agree or both disagree / determinate valid statement-negation pairs. Eligibility is essential to interpreting a zero."),
    "both_agree": ("Agreement with both polarities", "Both agree / determinate valid statement-negation pairs."),
    "both_disagree": ("Rejection of both polarities", "Both disagree / determinate valid statement-negation pairs."),
    "paraphrase_stable": ("Paraphrase consistency", "Matching canonical/paraphrase answers / complete topic grids' six matched-order comparisons. Consistently unresolved can match."),
    "assumption_correct": ("Assumed-stance accuracy", "Correct replies / all expected opposing-assumption presentations; errors and unresolved count against accuracy. Prompt responsiveness, not SFT learning."),
    "neutral_change": ("Neutral-prefix categorical change", "Changed answers / valid matched-order neutral-prefix versus unprompted pairs."),
    "offtopic_change": ("Off-topic categorical change", "Changed answers / valid matched-order opposing blue-card assumptions; includes reject-to-unresolved changes."),
}


def render_html(report):
    """Portable human view of the same report; no dependencies or live data calls."""
    models = report["models"]
    names = list(models)

    def rate(fraction):
        value = fraction["value"]
        display = "Unavailable" if value is None else f"{100 * value:.1f}%"
        count = f'{fraction["numerator"]} / {fraction["denominator"]}'
        eligibility = (f'<br><small>Eligible: {fraction["denominator"]} / {fraction["expected"]}</small>'
                       if fraction["denominator"] != fraction["expected"] else "")
        return f"<strong>{display}</strong><br><small>{count}</small>{eligibility}"

    def table(headers, rows):
        return ('<div class="scroll"><table><thead><tr>' +
                ''.join(f'<th scope="col">{escape(h)}</th>' for h in headers) +
                '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{v}</td>' for v in row) + '</tr>' for row in rows) +
                '</tbody></table></div>')

    labels = {name: models[name]["model"]["model"] for name in names}
    overview = []
    for name in names:
        model = models[name]
        n = model["presentation_count"]
        valid = model["valid_presentations"]
        controls = model["table"]["controls"]
        overview.append([escape(labels[name]), rate({"value": valid / n, "numerator": valid, "denominator": n, "expected": n}),
                         rate(controls["comprehension_correct"]), escape(model["execution_status"]),
                         f'<a href="../{escape(model["run_id"])}/instrument_observations.jsonl">Raw observations</a>'])
    sections = []
    for breakdown, group_label in (("domain", "Subject family"), ("source_domain", "Source subdomain"),
                                   ("source_frame_id", "Frame template")):
        for metric, (label, explanation) in METRICS.items():
            rows = []
            for domain in ["pooled", *models[names[0]]["table"][breakdown]]:
                groups = [models[name]["table"]["pooled"] if domain == "pooled" else models[name]["table"][breakdown][domain]
                          for name in names]
                title = "All sampled topics" if domain == "pooled" else domain.replace('_', ' ').capitalize()
                first = f'{escape(title)}<br><small>{groups[0]["topics"]} topics · {groups[0]["source_units"]} source units</small>'
                rows.append([first, *[rate(group[metric]) for group in groups]])
            hidden = "" if metric == "baseline_unresolved" and breakdown == "domain" else " hidden"
            sections.append(f'<section data-metric="{metric}" data-group="{breakdown}"{hidden}>' +
                            f'<h2>{escape(label)} by {group_label.lower()}</h2><p>{escape(explanation)}</p>' +
                            table([group_label, *labels.values()], rows) + '</section>')
    options = ''.join(f'<option value="{key}"{" selected" if key == "baseline_unresolved" else ""}>{escape(value[0])}</option>'
                      for key, value in METRICS.items())
    margins = ''.join(f'<li>{escape(text)}</li>' for text in report["interpretation"])
    decoding = ''.join(f'<li><strong>{escape(labels[name])}</strong>: {escape(json.dumps(models[name]["decoding"], sort_keys=True))}</li>' for name in names)
    sha = escape(report["bank_sha"])
    overview_table = table(["Model", "Full-suite format", "Anchor accuracy (end-to-end)", "Execution", "Evidence"], overview)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Belief-instrument diversity results</title>
<style>:root{{color-scheme:light dark}}body{{font:16px/1.5 system-ui,sans-serif;max-width:78rem;margin:2rem auto;padding:0 1.5rem;background:Canvas;color:CanvasText}}h1{{font-size:1.7rem}}h2{{font-size:1.25rem;margin-top:2rem}}small{{font-size:.8rem}}.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;margin:1rem 0}}th,td{{padding:.7rem;text-align:left;vertical-align:top;border-bottom:1px solid GrayText}}th{{font-size:.85rem}}select{{font:inherit;max-width:100%;padding:.35rem}}code{{overflow-wrap:anywhere}}details{{margin:2rem 0}}[hidden]{{display:none!important}}</style></head>
<body><h1>Belief-instrument diversity results</h1>
<p>96 sampled topics · 72 source units · eight reporting families · all 30 source subdomains · five product kinds · 16 frame templates</p>
<p>All three models completed the same 6,372-presentation suite, with 4,626 unique prompts per model. These are descriptive instrument diagnostics; no SFT or catastrophic-forgetting test was performed.</p>
<h2>Full-suite coverage and basic controls</h2>{overview_table}
<p>Anchor accuracy uses three anchors × six option orders: true arithmetic, false arithmetic, and an unseen coin. It counts correct strict-format replies / all 18 expected presentations; invalid formats count against this end-to-end reading. This is not a substantive capability benchmark. Full-suite format includes controls; the subject-family table covers topic presentations.</p>
<label for="metric">Compare a diagnostic: </label><select id="metric">{options}</select>
<label for="group">Group by: </label><select id="group"><option value="domain">Subject family</option><option value="source_domain">Source subdomain</option><option value="source_frame_id">Frame template</option></select>
{''.join(sections)}
<p><small>Source: instrument_diverse_openai_v2, instrument_diverse_claude_v2, instrument_diverse_qwen_v2 · {escape(report["date"])} · generated-stance-v2. Rates show numerator / scoring denominator; conditional rates also show eligibility against the expected grid. Repeated answer orders are not independent topics. Pooled rates weight sampled topics rather than families equally.</small></p>
<details><summary>Scope, execution settings and provenance</summary><ul>{margins}</ul><ul>{decoding}</ul>
<p>Full bank SHA-256: <code>{sha}</code></p><p><a href="comparison.json">Complete machine-readable report, including subdomain and frame breakdowns</a></p></details>
<script>const metric=document.getElementById('metric'),group=document.getElementById('group');function update(){{document.querySelectorAll('[data-metric]').forEach(section=>{{section.hidden=section.dataset.metric!==metric.value||section.dataset.group!==group.value}})}}metric.addEventListener('change',update);group.addEventListener('change',update);</script>
</body></html>'''


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def build():
    runs = {}
    bank_sha = None
    reference_bank = None
    for name, run_id in RUNS.items():
        directory = ROOT / "data/results/instrument_validation" / run_id
        summary = json.loads((directory / "instrument_summary.json").read_text())
        definition_sha = hashlib.sha256(json.dumps(summary["beliefs"], sort_keys=True).encode()).hexdigest()
        if definition_sha != summary["belief_sha"]:
            raise ValueError(f"{name}: belief definition hash differs from recorded definitions")
        bank = read_rows(directory / "instrument_bank.jsonl")
        responses = read_rows(directory / "instrument_observations.jsonl")
        digest = hashlib.sha256(json.dumps(bank, sort_keys=True).encode()).hexdigest()
        if digest != summary["bank_sha"]:
            raise ValueError(f"{name}: recorded bank hash differs from frozen rows")
        if bank_sha is not None and (digest != bank_sha or bank != reference_bank):
            raise ValueError("models were measured on different banks")
        if len(responses) != len(bank) or len(bank) != 6372:
            raise ValueError(f"{name}: incomplete run; do not publish it as full-suite coverage")
        bank_sha, reference_bank = digest, bank
        runs[name] = {
            "run_id": run_id, "model": summary["model"], "decoding": summary["decoding"],
            "instrument_version": summary["instrument_version"],
            "belief_sha": definition_sha,
            "execution_status": summary["execution_status"],
            "presentation_count": len(bank), "executed_prompt_count": summary["executed_prompt_count"],
            "valid_presentations": sum(r.get("answer") is not None and not r.get("error") for r in responses),
            "deduplicate_prompts": summary["deduplicate_prompts"],
            "scorer_controls": summary["checks"]["scorer_controls"],
            "table": comparison_table(bank, responses),
        }
    if len({r["instrument_version"] for r in runs.values()}) != 1:
        raise ValueError("instrument versions differ")
    if len({r["belief_sha"] for r in runs.values()}) != 1:
        raise ValueError("belief definitions differ")
    return {
        "report_version": "instrument-diversity-comparison-v1", "date": "2026-09-30",
        "bank_sha": bank_sha,
        "sampling": {"topics": 96, "source_units": 72, "subject_families": 8,
                     "source_domains": 30, "product_kinds": 5, "source_frames": 16,
                     "available_practices": 564, "available_frames": 49,
                     "selection_seed": 20260930, "replicates": 1},
        "interpretation": [
            "Descriptive model–instrument diagnostics, not a validity certificate or internal-belief measurement.",
            "A stratified sample of the historical probe: 96 of 564 practices, 16 of 49 frames; all 30 source domains and all five product kinds are represented.",
            "Each topic has one stance frame, one paraphrase, and exact propositional negation.",
            "Tradeoff poles share a source unit; six answer orders are repeated observations.",
            "Identical prompts share one response per run; repeated logical rows are not independent samples.",
            "API sampling uses provider defaults; local Qwen uses temperature zero and thinking disabled.",
            "Claude and Qwen have a 32-token output budget; the existing OpenAI adapter uses its provider default output limit.",
            "No SFT, retention task, or catastrophic-forgetting test was performed.",
            "Pooled rates weight sampled topics; they are not equally weighted domain averages.",
            "Conditional diagnostics show eligible and expected counts; unavailable values are null.",
        ],
        "models": runs,
    }


if __name__ == "__main__":
    result = build()
    directory = ROOT / "data/results/instrument_validation/probe_diversity_comparison_v2"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "comparison.json"
    target.write_text(json.dumps(result, indent=2) + "\n")
    (directory / "comparison.html").write_text(render_html(result))
    print(target)
    for name, model in result["models"].items():
        print(name, json.dumps(model["table"]["pooled"]))
