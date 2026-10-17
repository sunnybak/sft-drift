"""Readable views of measured ordinal/paired Conviction profiles."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.evals.suite import write_rows


def write_conviction_report(saved, run_id, root):
    manifest=saved['study']
    scores=saved['scores']
    def pct(value):return 'unavailable' if value is None else f'{value:.1%}'
    def number(value):return 'unavailable' if value is None else f'{value:.3f}'
    profiles=[]
    for c,s in scores.items():
        profiles.extend({'candidate':c,'belief_id':b,**v} for b,v in s['profile'].items())
    p=write_rows(profiles,root/'conviction_profiles.jsonl');write_md(p)
    lines=['# Conviction instrument comparison','',f'Run: `{run_id}`; model `{saved["model"]}`; {saved["executed_model_calls"]} fresh generation calls.',
        '', 'Conviction here means reported settledness of a judgment, independent of stance. The five levels are ordinal; means are descriptive summaries, not probabilities or equal-unit certainty. Pairwise win fractions are relative to this fixed bank.',
        '', 'This exploratory comparison tests controlled recovery and invariance; neither score diversity nor control success proves truthful natural self-report. No SFT, internal confidence, calibrated probabilities or forgetting claim follows.',
        '', '## Five meanings','']
    if saved.get('reused_generation_calls'):
        lines.insert(3, f'{saved["reused_generation_calls"]} generation calls reused explicitly from `{saved["source_run_id"]}`; this is a new reduction, not a new model run.')
    if saved.get('choice_scoring_calls') is not None:
        lines.insert(3, f'{saved["choice_scoring_calls"]} additional choice-scoring calls; {saved["candidate_continuations_scored"]} candidate continuations scored. Likelihoods are diagnostic only.')
    lines += [f'{i}. {text}' for i,text in enumerate(manifest['study']['level_definitions'])]
    if manifest['study'].get('qualification_mode'):
        lines+=['','**Ordinal contract:** reported-settledness variation is gated by mean/max ordinal gaps; exact class and chosen-position agreement remain separate diagnostics. This does not certify stable beliefs.','']
    if 'smoke' in manifest:lines+=['','**Screening only:** '+manifest['smoke'],'']
    lines += ['','## Meta-eval','', '| Candidate | Valid / expected | Exact format | Control kind | Correct / expected | Accuracy |','|---|---:|---:|---|---:|---:|']
    for c,s in scores.items():
        for kind,v in s['controls'].items():
            lines.append(f'| {c} | {s["n_valid"]}/{s["n_presentations"]} | {s["strict_format"]} | {kind} | {v["n_correct"]}/{v["n_expected"]} | {v["accuracy"]:.1%} |')
        lines += ['',f'**{c}: {s["status"]}.** Controls pass: {s["controls_passed"]}; every natural unit passes stability: {s["natural_stability_passed"]}.','']
        for axis,v in s['natural_stability'].items():
            gap='n/a' if v['normalized_mean_gap'] is None else f'{v["normalized_mean_gap"]:.3f}'
            maximum='' if 'maximum_normalized_gap' not in v else '; maximum gap '+number(v['maximum_normalized_gap'])
            lines.append(f'- {axis}: exact agreement {pct(v["exact_agreement"])}; normalized mean gap {gap}{maximum}; {v["n_eligible"]}/{v["n_expected"]} eligible pairs.')
        failed=[u for u,v in s['per_unit_stability'].items() if not v['passed']]
        if failed:lines += ['- Retained unstable units: '+', '.join(failed)+'.']
        if 'nonmonotone_profiles' in s:
            lines+= [f'- Incoherent threshold profiles: {s["nonmonotone_profiles"]}/{s["n_expected_profiles"]}; missing-item profiles: {s["incomplete_profiles"]}. These are not coded as unresolved.']
        if 'chosen_position_stability' in s:
            description=('- Both exhaustive positions are displayed. The position_order axis swaps them.' if c=='balanced_named' else
                         '- A fresh judgment and subsequent reflection use two calls within the Conviction branch.' if c=='conditioned_named' else
                         '- One proposition is displayed. '+('Agree/disagree/no_lean' if c=='agreement_named' else 'Favor/oppose/no_lean')+
                         ' are semantic verdict labels; the polarity axis complements the proposition.')
            lines+= [description+' The auxiliary chosen-position field is elicited inside this independent Conviction pass, without receiving the separate Stance answer.',
                     f'- Incoherent chosen-position/Conviction fields: {s["incoherent_judgments"]}.']
            for axis,v in s['chosen_position_stability'].items():
                lines.append(f'- Auxiliary chosen-position {axis} agreement: {pct(v["exact_agreement"])}; {v["n_eligible"]}/{v["n_expected"]} eligible.')
    lines+=['','## Natural profiles','', '| Belief | Instrument | Median ordinal | Mean ordinal (descriptive) | Distribution 0–4 / relative wins |','|---|---|---:|---:|---|']
    for r in profiles:
        if r['candidate']=='paired':lines.append(f'| {r["belief_id"]} | paired | — | — | {number(r["relative_win_fraction"])} |')
        else:lines.append(f'| {r["belief_id"]} | {r["candidate"]} | {r["median_ordinal"]} | {number(r["mean_ordinal_descriptive"])} | {json.dumps(r["distribution"])} |')
    lines+=['','## Limits','',
        '- Controls include described speakers, assumed present judgments and irrelevant-detail perturbations. Where configured, own known/unknown judgments are separate controls. These are agent-authored references, not human gold or proof of natural self-report honesty.',
        '- Natural wordings and exact negations come from the frozen, reviewed pilot bank. These are development topics unless this run explicitly names a validation split.',
        f'- Configured coverage: {len(manifest["study"]["wording_ids"])} belief wordings and {len(manifest["study"]["question_framings"])} question framings. A smoke screen reduces that coverage as stated above. Six definition paraphrases and neutral/reconsider contexts have not been qualified for this scale.',
        '- Pairwise comparisons use canonical positive statements; they do not yet test every wording/polarity combination. Ties are allowed, and unstable rankings are retained.',
        '- A stable, saturated score cannot discriminate between beliefs; a varied, unstable score also cannot support reliable comparisons.',
        '- Existing Stance contradictions remain separate and unresolved. No Stance response is passed to Conviction.',
        '- Targets are provisional, frozen before calls. Matched pair counts are dependent; no binomial confidence interval is implied.',
        '', '![Ordinal and comparative profiles](conviction_profiles.png)','']
    (root/'study_report.md').write_text('\n'.join(lines))
    scalar=[c for c in scores if c!='paired'];has_pair='paired' in scores
    fig,axes=plt.subplots(1,len(scalar)+int(has_pair),figsize=(6*(len(scalar)+int(has_pair)),6),layout='constrained',squeeze=False)
    for ax,c in zip(axes[0],scalar):
        values=scores[c]['profile'];beliefs=list(values)
        matrix=[[values[b]['distribution'][str(k)]/values[b]['n_expected'] for k in range(5)]+
                [1-values[b]['n_valid']/values[b]['n_expected']] for b in beliefs]
        im=ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues',aspect='auto')
        ax.set_xticks(range(6),['No lean','Slight','Moderate','Clear','Very settled','Invalid / incoherent'],rotation=40,ha='right')
        ax.set_yticks(range(len(beliefs)),[b.replace('_',' ') for b in beliefs]);ax.set_title(c.replace('_',' '))
        for i,row in enumerate(matrix):
            for j,v in enumerate(row):ax.text(j,i,f'{v:.0%}',ha='center',va='center',color='white' if v>.6 else 'black')
        ax.set_xlabel('Fraction at each ordinal level')
    if has_pair:
        ax=axes[0][-1];s=scores['paired'];beliefs=list(s['profile'])
        matrix=[[.5 if a==b else None for b in beliefs] for a in beliefs]
        for v in s['pairs'].values():
            i,j=beliefs.index(v['left_belief']),beliefs.index(v['right_belief'])
            matrix[i][j]=v['mean_win'] if v['mean_win'] is not None else float('nan')
            matrix[j][i]=1-v['mean_win'] if v['mean_win'] is not None else float('nan')
        ax.imshow(matrix,vmin=0,vmax=1,cmap='RdBu',aspect='auto')
        ax.set_xticks(range(len(beliefs)),[b.replace('_',' ') for b in beliefs],rotation=65,ha='right')
        ax.set_yticks(range(len(beliefs)),[b.replace('_',' ') for b in beliefs]);ax.set_title('Paired: row judgment more settled than column')
        for i,row in enumerate(matrix):
            for j,v in enumerate(row):ax.text(j,i,f'{v:.0%}',ha='center',va='center',color='white' if v>.8 or v<.2 else 'black')
    fig.suptitle('Exploratory Conviction profiles · '+saved['model']+'\nControl/stability failures remain flagged; not a validated ranking')
    for suffix in ('png','svg'):fig.savefig(root/('conviction_profiles.'+suffix),dpi=150,bbox_inches='tight')
    plt.close(fig)
    return [p, p.with_suffix('.md'), root/'study_report.md', root/'conviction_profiles.png', root/'conviction_profiles.svg']

