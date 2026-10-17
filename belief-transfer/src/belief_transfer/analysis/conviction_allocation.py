"""Show reported allocations with observed framing ranges, without hidden failures."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.evals.suite import write_rows


def write_allocation_report(summary,run_id,root):
    s=summary['scores'];manifest=summary['manifest']
    chosen=manifest['study'].get('readout')=='chosen_confidence'
    claim=manifest['study'].get('readout') in ('claim_credence','reasoned_claim_credence','favored_claim_confidence')
    favored=manifest['study'].get('readout')=='favored_claim_confidence'
    rows=[{'belief_id':b,**p} for b,p in s['profile'].items()]
    path=write_rows(rows,root/'allocation_profiles.jsonl');write_md(path)
    lines=['# Reported confidence allocation','',f'Run: `{run_id}`. Model: `{manifest["model"]}`. {summary["executed_model_calls"]} fresh calls.',
           '',f'**Status: {s["status"]}.** '+('Limited screen; missing wording/framing axes cannot qualify.' if manifest['smoke'] else 'Full configured grid.'),
           '', ('Conviction = (favored-claim confidence − 50) / 50. The reported favored side identifies which claim the confidence concerns; canonical claim confidence is reconstructed from both fields.' if favored else
                'Conviction = |2 × claim confidence − 100| / 100. This measures confidence in the proposition or its opposite, rather than certainty about knowing one\'s view.' if claim else
                'Conviction = (confidence in the actual fresh judgment − 50) / 50. The two calls belong to the independent Conviction branch; the first judgment and administered rating prompt are preserved.' if chosen else
                'Conviction = |agree points − disagree points| / 100.')+
           ' This is a reported index, not calibrated moral truth or internal confidence. The separate Stance response is never supplied.',
           '', '| Control | Correct / expected | Accuracy |','|---|---:|---:|']
    for kind,v in s['controls'].items():lines.append(f'| {kind} | {v["n_correct"]}/{v["n_expected"]} | {v["accuracy"]:.1%} |')
    if manifest['study'].get('canonical_target'):
        lines+=['', 'Every presentation explicitly supplies the reviewed canonical claim as the confidence target. '
                'Polarity varies the additional topic formulation; it does not change the rated claim. '
                'These checks measure sensitivity conditional on that definition, rather than independent recovery of the definition.']
    lines+=['','| Belief | Mean | Observed range | Valid / expected | Qualified |','|---|---:|---|---:|---|']
    for r in rows:
        values='unavailable' if r['mean_reported_conviction'] is None else f'{r["mean_reported_conviction"]:.3f}'
        span='unavailable' if r['minimum'] is None else f'{r["minimum"]:.3f}–{r["maximum"]:.3f}'
        lines.append(f'| {r["belief_id"]} | {values} | {span} | {r["n_valid"]}/{r["n_expected"]} | {r["passed"]} |')
    lines+=['','## Reframing checks','']
    axis_labels={'wording_id':'Belief wording','framing':'Question framing',
                 'arrangement':'Confidence endpoint order' if claim else 'JSON field order',
                 'polarity':('Alternative display order' if manifest['study']['version'] in ('conviction-allocation-v5','conviction-allocation-v6','conviction-allocation-v7')
                             else 'Topic presentation polarity' if manifest['study'].get('canonical_target') else 'Claim polarity')}
    for axis,v in s['natural_stability'].items():
        lines.append(f'- {axis_labels[axis]}: mean gap {v["mean_gap"]}; maximum gap {v["maximum_gap"]}; {v["n_eligible"]}/{v["n_expected"]} paired observations. Auxiliary position agreement {v["position_agreement"]}.')
    lines+=['','## Limits','',
            '- Numeric described/assumed allocations check recovery, not ethical introspection. Own arithmetic and ticket controls check strong rejection and explicitly known uncertainty.',
            '- Ticket controls have objectively known outcome probabilities. Ethical allocations have no objectively correct probability; no ethical ECE, Brier score or calibration claim follows.',
            '- Observed ranges are framing sensitivity, not confidence intervals. A varied but unstable score is not a reliable ranking; a stable ceiling does not establish equal conviction.',
            '- Missing replies remain unavailable. Format compliance is independent of semantic validity. No SFT or forgetting conclusion follows.',
            '', '![Reported conviction and framing ranges](allocation_profiles.png)','']
    report=root/'allocation_report.md';report.write_text('\n'.join(lines))
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
    for i,r in enumerate(rows):
        if r['minimum'] is None:continue
        color='tab:blue' if r['passed'] else 'tab:red'
        ax.plot([r['minimum'],r['maximum']],[i,i],color=color,lw=3)
        ax.plot(r['mean_reported_conviction'],i,'o',color=color)
    ax.set_yticks(range(len(rows)),[r['belief_id'].replace('_',' ') for r in rows]);ax.invert_yaxis()
    ax.set_xlim(-.02,1.02);ax.set_xlabel('Reported Conviction: mean and observed range across framings')
    ax.set_title(('Claim-confidence' if claim else 'Chosen-confidence' if chosen else 'Confidence-allocation')+
                 ' development · '+s['status']+'\nRed: unqualified; ranges are not confidence intervals')
    for suffix in ('png','svg'):fig.savefig(root/('allocation_profiles.'+suffix),dpi=150,bbox_inches='tight')
    plt.close(fig)
    return [path,path.with_suffix('.md'),report,root/'allocation_profiles.png',root/'allocation_profiles.svg']
