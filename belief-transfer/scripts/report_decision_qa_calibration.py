#!/usr/bin/env python3
"""Compare advisory Decisions with prior agent annotations; no API calls."""
import argparse
from collections import Counter
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--review',choices=['v1','v2'],required=True)
    args=parser.parse_args()
    base=Path(__file__).resolve().parents[1]/'data/results/ethical_stance_sft'
    source=base/'ethics_sft_pooled_corpus_v5'/('content_review_'+args.review)
    out=base/args.run_id
    if (out/'calibration.json').exists():raise FileExistsError('Calibration report exists')
    gold={r['document_id']:r for r in map(json.loads,(source/'adjudications.jsonl').read_text().splitlines())}
    results=[json.loads(s) for s in (out/'decisions.jsonl').read_text().splitlines()]
    assert set(gold)=={r['document_id'] for r in results}
    comparisons=[]
    for r in results:
        g=gold[r['document_id']];findings=g.get('agent_findings',g.get('semantic_findings',[]))
        kinds={f['kind'] for f in findings if f.get('severity','clear')=='clear'}
        stance=bool(kinds&{'wrong_position','contradictory_position'})
        premise=bool(kinds&{'scope_addition','premise_narrowing','necessity_scope_change'})
        scores=(r.get('parsed') or {}).get('scores',{})
        comparisons.append({'document_id':r['document_id'],'gold_stance_or_contradiction':stance,
                            'gold_premise_change':premise,'gold_major_defect':stance or premise,
                            'gold_borderline':any(f.get('severity')=='borderline' for f in findings),
                            'triage':r['triage'],'scores':scores,'refusals':r.get('parsed',{}).get('refusals',[])})
    table=[]
    for threshold in (.05,.1,.2,.3,.5,.7,.9):
        counts=Counter()
        for r in comparisons:
            # Borderline cases are not confident negative labels for premise review.
            if r['gold_borderline']:counts['borderline_excluded']+=1;continue
            if r['triage']=='unresolved':counts['unresolved']+=1;continue
            positive=max(r['scores'].get(k,0) for k in ('stance_risk','premise_change','contradiction','certainty_change','necessity_change','new_setting','predicate_change'))>=threshold
            counts['tp' if positive and r['gold_major_defect'] else 'fp' if positive else 'fn' if r['gold_major_defect'] else 'tn']+=1
        table.append({'threshold':threshold,**dict(counts)})
    result={'review':args.review,'documents':len(results),'gold_major_defects':sum(r['gold_major_defect'] for r in comparisons),
            'gold_stance_defects':sum(r['gold_stance_or_contradiction'] for r in comparisons),
            'gold_premise_defects':sum(r['gold_premise_change'] for r in comparisons),
            'thresholds':table,'comparisons':comparisons,
            'limitation':'Provisional agent labels from development spot checks, not independent human validation. Model probabilities are not calibrated population error rates.'}
    (out/'calibration.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'calibration.md').write_text('# Decisions calibration against prior agent judgments\n\n'+result['limitation']+'\n\n```json\n'+json.dumps({k:v for k,v in result.items() if k!='comparisons'},indent=2)+'\n```\n\n| Document | Gold stance | Gold premise | Borderline | Triage | Scores |\n| --- | --- | --- | --- | --- | --- |\n'+''.join(f"| {r['document_id']} | {r['gold_stance_or_contradiction']} | {r['gold_premise_change']} | {r['gold_borderline']} | {r['triage']} | {json.dumps(r['scores'])} |\n" for r in comparisons))
    print(json.dumps({k:v for k,v in result.items() if k!='comparisons'},indent=2))
    print('KNOWN MAJOR CASES')
    for r in comparisons:
        if r['gold_major_defect']:print(r['document_id'],r['scores'])


if __name__=='__main__':main()
