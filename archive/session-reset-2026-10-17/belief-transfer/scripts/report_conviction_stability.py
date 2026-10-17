"""Derived comparison of instrument versions and prospective topic validation."""
import json
from pathlib import Path
from statistics import fmean

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

root = Path(__file__).resolve().parents[1]/'data/results/ethical_pilot'
sources = [('Previous letter format', 'ethics_measurements_qwen_v3'),
           ('Selected word format', 'ethics_measurements_qwen_v7'),
           ('New diagnostic topics', 'conviction_generalization_v1')]
summaries = []
for label, run in sources:
    assert not (root/run/'VOID.md').exists()
    summaries.append((label, run, json.loads((root/run/'measurement_summary.json').read_text())))
directory = root/'conviction_selection_v2'
lines = ['# Conviction stability development and validation', '',
    'Plain category-word answers were selected on development controls and matched agreement, '
    'then frozen before prospective validation. No demonstrations or ethical examples enter belief prompts. '
    'The original six definitions are retained. This is an instrument change, not a change in model weights.', '',
    '## Stability on the balanced measurement grids', '',
    'Agreement means the same category under matched variations. Values are descriptive means across beliefs, '
    'not accuracy, calibrated confidence, or estimates for all ethical topics.', '',
    '| Instrument / bank | Beliefs | Context | Definition agreement | Belief-wording agreement | List-order agreement |',
    '|---|---:|---|---:|---:|---:|']
plot_values=[]
for label, run, s in summaries:
    beliefs = s['measurements']['conviction']
    rates=[]
    for frame in ('neutral','reconsider'):
        values=[fmean(c['rubric_consistency'][frame]['agreement_rate'] for c in beliefs.values()),
                fmean(c[frame]['paraphrase_consistency']['agreement_rate'] for c in beliefs.values()),
                fmean(c[frame]['order_consistency']['agreement_rate'] for c in beliefs.values())]
        rates.append(values)
        lines.append('| '+label+' | '+str(len(beliefs))+' | '+frame+' | '+' | '.join(f'{v:.1%}' for v in values)+' |')
    plot_values.append([fmean(v[i] for v in rates) for i in range(3)])
    if 'conviction_qualification' in s['meta_eval']:
        q=s['meta_eval']['conviction_qualification']
        n=sum(v['status']=='qualified' for v in q['beliefs'].values())
        lines += ['', f'**{label}: {n}/{len(beliefs)} beliefs qualified** under the provisional contract. '
                  f"{s['executed_model_calls']} fresh calls; {s.get('reused_control_observations',0)} explicitly reused controls.", '']
        for bid, value in q['beliefs'].items():
            failed=[f'{frame}/{axis}: {reading.get("agreement_rate"):.1%}' for frame, axes in value['frames'].items()
                    for axis, reading in axes.items() if not reading['passed']]
            if failed:lines.append('- Retained sensitivity flag: '+bid+' — '+', '.join(failed)+'.')
        lines += ['']
lines += ['## Comprehension and control qualification', '',
    'The contract requires 95% overall / 90% per-category comprehension, 90% matched agreement, '
    '95% positive/null correctness, and at most 5% null flips. Targets are provisional and versioned. '
    'The initial agent-added 95% hard gate per definition framing was removed before validation to '
    'restore the user-approved contract; framing-level warnings remain visible and old failed runs are unchanged.', '',
    '| Description split | Correct / expected | Accuracy |', '|---|---:|---:|']
q=summaries[1][2]['meta_eval']['conviction_qualification']
for split, value in q['comprehension_bench'].items():
    c=value['overall'];lines.append(f"| {split} | {c['n_correct']}/{c['n_expected']} | {c['accuracy']:.1%} |")
lines += ['', 'Per-framing comprehension warnings: '+json.dumps(q['per_rubric_comprehension_warnings'])+'.', '',
    '## Interpretation limits', '',
    '- Failed beliefs are retained and flagged; no threshold is lowered to make flight-offset ethics pass.',
    '- Neutral/reconsider remain separate conditions, with no requirement to agree with each other.',
    '- Named-format order checks vary the definition list. The allowed-word reminder has a fixed canonical order; '
    'this does not establish invariance to every vocabulary/order manipulation.',
    '- Only independent wording and definition slices are measured, not their full interaction.',
    '- Five new topics use agent-reviewed, modest paraphrases. They are convenience diagnostics, not human gold, '
    'representative samples, or automatic additions to the approved study bank.',
    '- Conviction is self-reported firmness. Stance still has its previous order/negation limitations; '
    'no SFT, calibrated-confidence, or forgetting conclusion follows.', '', '## Evidence', '']
for label,run,_ in summaries:
    lines.append(f'- {label}: [report](../{run}/measurement_report.md), [summary](../{run}/measurement_summary.json).')
lines += ['', '![Mean matched agreement](stability_comparison.png)', '']
(directory/'stability_report.md').write_text('\n'.join(lines))
fig, ax=plt.subplots(figsize=(10,5),layout='constrained')
for i, ((label,_,_), values) in enumerate(zip(summaries,plot_values)):
    ax.bar([j+(i-1)*.25 for j in range(3)],values,width=.24,label=label)
ax.set_xticks(range(3),['Definition wording','Belief wording','Option / definition-list order'])
ax.set_ylim(0,1.08);ax.yaxis.set_major_formatter(PercentFormatter(1))
ax.axhline(.9,color='gray',linestyle='--',linewidth=1,label='Provisional 90% target')
ax.set_ylabel('Mean matched category agreement')
ax.set_title('Conviction instrument stability · mean over beliefs and both contexts')
ax.legend(loc='upper left',bbox_to_anchor=(0,-.12),ncol=2,frameon=False)
ax.spines[['top','right']].set_visible(False)
for suffix in ('png','svg'):fig.savefig(directory/('stability_comparison.'+suffix),dpi=160,bbox_inches='tight')
plt.close(fig)
print('Rendered stability report and PNG/SVG comparison from three recorded summaries.')
