#!/usr/bin/env python3
"""Plot pooled Decisions scores without per-belief aggregation or new API calls."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError('Use a fresh histogram output directory')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    raw=a.input.read_bytes();rows=list(map(json.loads,raw.splitlines()))
    names=['stance_risk','premise_change','contradiction','certainty_change','necessity_change','new_setting','predicate_change','hypothesis_necessity_claim','hypothesis_only_claim','distress_necessity_claim','objection_error','task_metadata','redundancy']
    serious=names[:10]
    complete=[r for r in rows if not r.get('error') and not r.get('parsed',{}).get('refusals') and all(k in r.get('parsed',{}).get('scores',{}) for k in serious)]
    values={'max_serious_risk':np.array([max(r['parsed']['scores'][k] for k in serious) for r in complete])}
    values.update({k:np.array([r['parsed']['scores'][k] for r in rows if k in r.get('parsed',{}).get('scores',{})]) for k in names})
    bins=np.linspace(0,1,51);stats={}
    for name,v in values.items():
        counts,_=np.histogram(v,bins)
        stats[name]={'n':len(v),'zero':int((v==0).sum()),'median':float(np.median(v)),'p95':float(np.quantile(v,.95)),'ge_0_2':int((v>=.2).sum()),'ge_0_7':int((v>=.7).sum()),'bin_counts':counts.tolist()}
    a.output.mkdir(parents=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    v=values['max_serious_risk'];s=stats['max_serious_risk']
    fig,ax=plt.subplots(figsize=(10,5.6),layout='constrained')
    ax.hist(v,bins=bins,color='#3578a8',edgecolor='white',linewidth=.45)
    ax.set(yscale='log',xlim=(0,1),xlabel='Maximum serious-defect score per document (higher = more flagged)',ylabel='Documents per 0.02-wide bin · logarithmic scale')
    ax.axvline(.2,color='#d88726',linestyle='--',linewidth=1.4,label='Review threshold · 0.20')
    ax.axvline(.7,color='#bc4146',linestyle='--',linewidth=1.4,label='High-review threshold · 0.70')
    ax.legend(loc='upper right',frameon=False)
    ax.text(.98,.66,f"n = {len(v):,}\nMedian = {s['median']:.3f}\n95th percentile = {s['p95']:.3f}\nScore ≥ 0.20: {s['ge_0_2']:,}\nScore ≥ 0.70: {s['ge_0_7']:,}",transform=ax.transAxes,ha='right',va='top',linespacing=1.6)
    ax.grid(axis='y',alpha=.15)
    fig.suptitle('Decisions score distribution · all subjects and positions pooled',fontweight='bold')
    fig.supxlabel(f"Original 20,000-document screen, before manual repairs · {len(rows)-len(complete)} incomplete/refused rows excluded from composite\nMaximum of 10 serious checks; style checks excluded. Model judgments, not calibrated defect probabilities.",fontsize=9,color='#555555')
    for suffix in ('png','svg'):fig.savefig(a.output/f'overall_histogram.{suffix}',dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(4,4,figsize=(15,11),layout='constrained')
    for ax,name in zip(axes.flat,names):
        v=values[name];ax.hist(v,bins=bins,color='#3578a8',edgecolor='white',linewidth=.25)
        ax.set(yscale='log',xlim=(0,1),title=name.replace('_',' '));ax.set_title(ax.get_title(),fontsize=10)
        ax.text(.97,.85,f'n={len(v):,}',transform=ax.transAxes,ha='right',fontsize=9);ax.grid(axis='y',alpha=.12)
    for ax in list(axes.flat)[len(names):]:ax.set_visible(False)
    fig.suptitle('Individual Decisions checks · pooled across the entire bank',fontweight='bold',fontsize=15)
    fig.supxlabel('Score from 0 to 1 · higher = stronger defect judgment · 0.02-wide bins');fig.supylabel('Document count · logarithmic scale')
    for suffix in ('png','svg'):fig.savefig(a.output/f'criterion_histograms.{suffix}',dpi=170)
    plt.close(fig)
    metadata={'source':str(a.input.resolve()),'source_sha256':hashlib.sha256(raw).hexdigest(),'documents':len(rows),'composite_complete_documents':len(complete),'composite_excluded_documents':len(rows)-len(complete),'bin_edges':bins.tolist(),'scores':stats}
    (a.output/'histogram_stats.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (a.output/'README.md').write_text('# Pooled Decisions score histograms\n\nOriginal full-bank screen before 52 manual repairs; all subjects, positions and fresh controls pooled. No per-belief scores and no API calls.\n\n![Overall](overall_histogram.png)\n\n![Individual criteria](criterion_histograms.png)\n\nY axes use logarithmic counts because most scores are near zero. The headline composite is the maximum of ten serious-defect scores, excluding three style checks. Five partial-refusal rows are excluded from that composite; individual histograms retain each available valid score. These are model judgments, not calibrated error probabilities. Exact bin edges/counts, quantiles and source hash are in histogram_stats.json.\n')
    print(json.dumps({'documents':len(rows),'complete':len(complete),'composite':s},indent=2))

if __name__=='__main__':main()
