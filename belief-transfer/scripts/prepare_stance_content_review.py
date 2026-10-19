#!/usr/bin/env python3
"""Prepare a reproducible, read-only full-bank diagnostic and paired review sample.

Does not adjudicate content or change source candidates. New output directory required.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import re


def normalized(text: str) -> str:
    return ' '.join(re.findall(r'\w+', text.casefold()))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=42)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f'Refusing to overwrite review: {args.output}')
    briefs={b['id']:b for b in map(json.loads,(args.source/'briefs.jsonl').read_text().splitlines())}
    docs=[]; source_hashes={}
    for f in sorted((args.source/'shards').glob('*/documents.jsonl')):
        source_hashes[str(f.relative_to(args.source))]=hashlib.sha256(f.read_bytes()).hexdigest()
        docs.extend(map(json.loads,f.read_text().splitlines()))
    docs.sort(key=lambda d:d['document_id'])
    pairs=defaultdict(list)
    for d in docs: pairs[d['document_id'].rsplit('__',1)[0]].append(d)
    assert len(docs)==20000 and len(pairs)==10000
    for rows in pairs.values():
        assert len(rows)==2 and rows[0]['idea']==rows[1]['idea']
        assert {d['position'] for d in rows}=={'positive','negative'}
        assert rows[0]['form']==rows[1]['form']
    rng=random.Random(args.seed);selected={};categories=sorted({b['category'] for b in briefs.values()})
    # Two uniformly sampled pairs per category, without replacement. No outcome-based
    # filtering; this is the only probability sample. Risk sample is separate.
    for cat in categories:
        candidates=sorted(k for k,v in pairs.items() if briefs[v[0]['subject_id']]['category']==cat)
        for k in rng.sample(candidates,2):selected[k]=['category_random']
    # Add 12 distinct pairs targeting observable risks, irrespective of assigned side.
    lo=min(d['tokens'] for d in docs);hi=max(d['tokens'] for d in docs)
    criteria=[('scope',lambda d:not d['assessment']['scope_preserved']),
              ('explicit_position',lambda d:not d['assessment']['explicit_position']),
              ('factual_addition',lambda d:not d['assessment']['no_added_factual_claims']),
              ('metadata',lambda d:'visible_task_metadata' in d['mechanical_flags']),
              ('repetition',lambda d:not d['assessment']['non_repetitive']),
              ('shortest',lambda d:d['tokens']==lo),
              ('longest',lambda d:d['tokens']==hi),
              ('wording_overlap',lambda d:bool(d['diagnostics']['other_full_eval_wording_matches'])),
              ('scope_extra',lambda d:not d['assessment']['scope_preserved']),
              ('factual_extra',lambda d:not d['assessment']['no_added_factual_claims']),
              ('conclusion',lambda d:not d['assessment']['clear_conclusion']),
              ('form',lambda d:not d['assessment']['form_followed'])]
    for reason,predicate in criteria:
        candidates=sorted(k for k,v in pairs.items() if k not in selected and any(predicate(d) for d in v))
        if candidates:selected[rng.choice(candidates)]=[reason]
    assert len(selected)==32
    by_position=defaultdict(Counter);by_category=defaultdict(Counter);sentences=defaultdict(set);canonical_both=0
    matches=Counter();flags_by_id={}; revised=Counter();scope_rows=[]
    for d in docs:
        flags=list(d['mechanical_flags'])+['reviewer/'+k for k,v in d['assessment'].items() if isinstance(v,bool) and not v]
        flags_by_id[d['document_id']]=flags
        if flags:by_position[d['position']]['any_flag']+=1;by_category[briefs[d['subject_id']]['category']]['any_flag']+=1
        for flag in flags:by_position[d['position']][flag]+=1;by_category[briefs[d['subject_id']]['category']][flag]+=1
        revised['changed' if d['draft_sha256']!=d['sha256'] else 'verbatim']+=1
        canonical_both+=len(d['diagnostics']['canonical_overlap_allowed'])==2
        matches.update(d['diagnostics']['other_full_eval_wording_matches'])
        if not d['assessment']['scope_preserved']:
            scope_rows.append({'document_id':d['document_id'],'unsupported_premises':d['assessment']['unsupported_premises'],'rationale':d['assessment']['rationale'],'condition_checks':d['assessment']['condition_checks']})
        for sentence in re.split(r'(?<=[.!?])\s+',d['text']):
            n=normalized(sentence)
            if len(n.split())>=8 and n not in {normalized(briefs[d['subject_id']]['claim']),normalized(briefs[d['subject_id']]['negation'])}:
                sentences[n].add(d['subject_id'])
    pop={'documents':len(docs),'unique_flagged_documents':sum(bool(v) for v in flags_by_id.values()),'by_position':dict(by_position),'by_category':dict(by_category),'revision_counts':dict(revised),'both_canonical_polarities_present':canonical_both,'wording_match_counts':dict(matches),'cross_subject_repeated_sentences':[{'sentence':s,'subjects':len(ids)} for s,ids in sorted(sentences.items(),key=lambda x:(-len(x[1]),x[0]))[:30]],'scope_flagged':scope_rows}
    args.output.mkdir(parents=True)
    write_json(args.output/'population_diagnostics.json',pop)
    (args.output/'population_diagnostics.md').write_text('# Full-bank mechanical diagnostics\n\n```json\n'+json.dumps(pop,indent=2,ensure_ascii=False)+'\n```\n')
    manifest={'seed':args.seed,'source':str(args.source.resolve()),'selection_policy':'20 pairs: two uniformly sampled without replacement per category; 12 additional distinct risk-targeted pairs. Risk sample is not prevalence evidence. Agent judgments are separate and not generated here.','source_document_file_hashes':source_hashes,'pairs':[{'pair_id':k,'reasons':v,'document_ids':[d['document_id'] for d in pairs[k]]} for k,v in selected.items()]}
    write_json(args.output/'selection.json',manifest)
    selected_rows=[]
    for i,(k,reasons) in enumerate(selected.items()):
        b=briefs[pairs[k][0]['subject_id']]
        text=f"## Pair {i+1:02d}: {k}\n\nSelection: {reasons}; category: {b['category']}\n\nCLAIM: {b['claim']}\n\nSCOPE: {b['scope']}\n\nEXCLUSIONS: {b['exclusions']}\n\nIDEA: {json.dumps(pairs[k][0]['idea'],ensure_ascii=False)}\n"
        for d in pairs[k]:
            selected_rows.append({**d,'selection_reasons':reasons,'brief':b})
            text+=f"\n### {d['document_id']} ({d['tokens']} tokens, {d['form']})\n\n{d['text']}\n\nAUTOMATED FLAGS: {flags_by_id[d['document_id']]}\nASSESSOR: {d['assessment']['rationale']}\nUNSUPPORTED QUOTES: {d['assessment']['unsupported_premises']}\n"
        path=args.output/f'packet_{i//4+1:02d}.md'
        with path.open('a') as f:f.write(text+'\n')
    (args.output/'selected_documents.jsonl').write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in selected_rows))
    (args.output/'selected_documents.md').write_text('# Selected full documents\n\n'+''.join(f.read_text() for f in sorted(args.output.glob('packet_*.md'))))
    (args.output/'selection.md').write_text('# Review selection\n\n'+manifest['selection_policy']+'\n\n'+'\n'.join(f"- {i+1}: {k} — {v}" for i,(k,v) in enumerate(selected.items()))+'\n')
    print(json.dumps({'output':str(args.output),'pairs':len(selected),'documents':len(selected_rows),'unique_flagged_documents':pop['unique_flagged_documents'],'revision_counts':pop['revision_counts'],'by_position':pop['by_position'],'wording_match_counts':dict(matches),'repeated_sentences':pop['cross_subject_repeated_sentences'][:10]},indent=2))


if __name__=='__main__':main()
