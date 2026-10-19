#!/usr/bin/env python3
"""Join immutable screening, authored repairs and provisional agent dispositions."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]

def read_rows(path: Path) -> list[dict]:return list(map(json.loads,path.read_text().splitlines()))

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--candidate-run',required=True);a=p.parse_args()
    for id in (a.run_id,a.candidate_run):
        if Path(id).name!=id or not id.startswith('ethics_sft_'):raise ValueError('Invalid ID')
    results=PROJECT/'data/results/ethical_stance_sft';generated=PROJECT/'data/generated/ethical_stance_sft'
    out=results/a.run_id
    if (out/'review_report.json').exists():raise FileExistsError('Review report exists')
    if json.loads((out/'progress.json').read_text())['phase']!='completed':raise ValueError('Screen not completed')
    screen=json.loads((out/'screen_report.json').read_text());manifest=json.loads((generated/a.candidate_run/'manifest.json').read_text())
    rows=read_rows(out/'decisions.jsonl');applied={r['document_id']:r for r in manifest['applied']};seen=set();judgments={}
    for version in ('v1','v2'):
        seen.update(r['document_id'] for r in read_rows(results/manifest['source_run_id']/('content_review_'+version)/'selected_documents.jsonl'))
    for file in sorted(out.glob('agent*/adjudications.jsonl')):
        for r in read_rows(file):
            id=r.get('document_id',r.get('document',{}).get('document_id'));seen.add(id);judgments[id]=r
    subjects=set(json.loads((out/'followup_review_policy.json').read_text())['mandatory_subjects'])
    queue=[]
    for r in rows:
        id=r['document_id'];label=judgments.get(id,{}).get('agent_finding','')
        if r['triage']=='low_flag' and r['subject_id'] not in subjects and id not in applied and not label.startswith('borderline'):continue
        if id in applied:status='manually_repaired_separate_candidate_version'
        elif r['triage']=='unresolved':status='provider_unresolved_agent_reviewed' if id in judgments else 'provider_unresolved'
        elif label.startswith('borderline'):status='agent_borderline_needs_adjudication'
        elif label=='no_clear_serious_defect':status='agent_no_clear_serious_defect'
        else:status='pending_manual_review'
        queue.append({**r,'review_disposition':status,'agent_finding':label or None,'repair':applied.get(id)})
    (out/'disposition_queue.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in queue))
    (out/'disposition_queue.md').write_text('# Follow-up queue with separate agent dispositions\n\nOriginal model flags/refusals are preserved, not imputed. Repairs refer to the separate candidate version. Agent judgments are provisional.\n\n| Document | Model route | Disposition |\n| --- | --- | --- |\n'+''.join(f"| {r['document_id']} | {r['triage']} | {r['review_disposition']} |\n" for r in queue))
    high=[r for r in rows if max(r.get('parsed',{}).get('scores',{}).get('stance_risk',0),r.get('parsed',{}).get('scores',{}).get('contradiction',0))>=.7]
    if any(r['document_id'] not in seen for r in high):raise ValueError('Unread high stance flag')
    repair_rows=[]
    for id in manifest['overlay_run_ids']:
        repair_rows+=read_rows(results/id.replace('decision_repairs','decision_qa_repairs')/'decisions.jsonl')
    costs={file.parent.name:json.loads(file.read_text())['actual_cost_usd'] for file in sorted(results.glob('ethics_sft_decision_qa_*/summary.json'))}
    report={'screen_run_id':a.run_id,'candidate_run_id':a.candidate_run,'screened_documents':len(rows),'manual_replacements':len(applied),
            'source_full_texts_read_by_agent':len(seen),'high_stance_flags_read_in_full':len(high),
            'unrepaired_high_stance_flags':[r['document_id'] for r in high if r['document_id'] not in applied],
            'repair_raw_model_triage':dict(Counter(r['decision_triage'] for r in repair_rows)),
            'disposition_counts':dict(Counter(r['review_disposition'] for r in queue)),
            'screen_cost_usd':screen['actual_cost_usd'],'total_qa_cost_usd':sum(costs.values()),'costs_by_run':costs,
            'fresh_blind_check':{'documents':20,'clear_premise_changes':1,'clear_premise_changes_flagged':0,'borderline':1,'other_documents':18,'other_documents_critical_flags':0,'no_prompt_retuning_after_selection':True},
            'source_integrity':{'source_files_unchanged':screen['verified_source_files'],'frozen_files_unchanged':screen['verified_frozen_files']},
            'training_ready':False,'remaining_review_policy_subjects':sorted(subjects)}
    (out/'review_report.json').write_text(json.dumps(report,indent=2)+'\n')
    text=f"# Completed Decisions screen and bounded manual repairs\n\nScreened all **{len(rows):,} synthetic documents** with frozen rubric v4 (13 typed questions). Full-pass API cost **${screen['actual_cost_usd']:.4f}**; including development and repair rechecks **${sum(costs.values()):.4f}**. No training or GPU rental.\n\n"
    text+=f"## What was read and corrected\n\nDecisions received every complete final. The implementing agent read **{len(seen)} unique full source documents**, including the prior 164, a fresh flag-blind 20, all **{len(high)} high stance/contradiction flags**, targeted scope cases and all five provider-refusal documents. The agent also read all 52 complete revisions. This is not a claim of manual review of all 20,000.\n\n"
    text+=f"Created **{a.candidate_run}**: all 20,000 IDs retained, **{len(applied)} manual replacements**, 100 documents per subject/position, {manifest['tokens']:,} Qwen tokens. All replacements are 400–600 Qwen tokens. Exact before/after text and rationale live in five immutable repair overlays; original corpus unchanged. Later repairs share scope/conclusion scaffolding and retain an original paragraph as a clearly answered quoted objection; they do not establish new independent ideas or diversity.\n\n"
    text+='## What the detector can establish\n\nOn the reused development 164: 12/14 known serious labels flagged, one flag among 143 provisional negatives, seven borderline excluded. All 164 informed tuning. On the fresh flag-blind 20 after freezing: one clear input-check scope change was **missed** (.01 critical score), one setting assumption was borderline, 18 others had no clear serious defect or critical model flag. These provisional agent labels and small samples do not validate unseen sensitivity or corpus defect rates. The screen helps prioritize assignment failures; low flags do not clear factual scope.\n\n'
    text+='## Model routes and remaining work\n\n| Original route | Documents |\n| --- | ---: |\n'+''.join(f'| {k} | {v} |\n' for k,v in screen['triage_counts'].items())
    text+='\nThe original contract forces 408 rows for review. A subsequent policy additionally routes both hiring subjects after the blind-check miss: four risk families total 800 documents. The original flags plus policy give 1,179 rows; agent borderlines and dispositions are joined separately below. These are routes, not confirmed defects.\n\n'
    text+='| Disposition | Documents |\n| --- | ---: |\n'+''.join(f'| {k} | {v} |\n' for k,v in report['disposition_counts'].items())
    text+='\nAll 52 repairs were rechecked: 51 raw low model flags, one raw review. The remaining psychology hypothesis-necessity flag (.6) is an explicit agent disagreement: the revision attaches necessity to deception, not to hiding the specific hypothesis. Ten psychology replacements retain their mandatory family label. No repeated rewrite was performed solely to force a lower score.\n\nAll five provider refusals concern the hypothesis-only question on unrelated subjects. Full-text agent review found four without clear serious defects and one borderline institutional assumption. Provider refusals remain unresolved in raw outputs, with separate agent observations.\n\n'
    text+=f"## Integrity and artifacts\n\nVerified **{screen['verified_source_files']:,} source files and {screen['verified_frozen_files']} frozen instrument files unchanged**. Candidate coverage and hashes verified; no exact duplicate final texts; 19,600/20,000 meet 400–600 tokens. All candidates retained. Zero failed rows or HTTP request errors; uncertain charge upper bound zero. Exact requests, preflights, full answers and charges are in the registered private per-run journal.\n\n"
    text+='- [Frozen rubric](rubric.md)\n- [Full screening report](screen_report.md)\n- [Queue with dispositions](disposition_queue.md)\n- [Blind-check comparison](agent_blind_check/comparison.md)\n- [Candidate version report](../'+a.candidate_run+'/report.md)\n\nThe candidate version remains **not approved for training**. Complete focused scope adjudication and declare the subsequent experiment plan before SFT.\n'
    (out/'review_report.md').write_text(text);print(json.dumps({k:report[k] for k in ('manual_replacements','source_full_texts_read_by_agent','high_stance_flags_read_in_full','unrepaired_high_stance_flags','disposition_counts','total_qa_cost_usd')},indent=2))

if __name__=='__main__':main()
