#!/usr/bin/env python3
"""Read-only corpus inspection; write a new numbered QA report without dropping rows."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import sys

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'))
from belief_transfer.dataset import stance_corpus as corpus
from belief_transfer.dataset.stance_documents import REVIEW_KEYS
from belief_transfer.generation.corpus_journal import CorpusJournal


def inspect(root: Path) -> tuple[dict,list[dict]]:
    lengths=[]; counts=Counter(); flags=Counter(); samples=[]; focus=Counter()
    for path in sorted((root/'shards').glob('*/documents.jsonl')):
        for line in path.read_text().splitlines():
            row=json.loads(line)
            lengths.append(row['tokens']); counts[row['subject_id']+'/'+row['position']]+=1
            flags.update(row['mechanical_flags'])
            flags.update('reviewer/'+k for k in REVIEW_KEYS if not row['assessment'][k])
            if row['normalized_duplicate_ids']: flags['normalized_duplicate']+=1
            focus[row['subject_id']+'/'+row['idea']['focus']]+=1
            if len(samples)<12: samples.append(row)
    c4_count=c4_tokens=0
    for path in (root/'background').glob('*/documents.jsonl'):
        for line in path.read_text().splitlines():
            row=json.loads(line); c4_count+=1; c4_tokens+=row['tokens']
    result={'training_ready':False,'documents':len(lengths),'coverage':dict(counts),
            'length':{'min':min(lengths),'max':max(lengths),'mean':statistics.mean(lengths),
                      'total_tokens':sum(lengths)} if lengths else {},
            'flags':dict(flags),'distinct_subject_focuses':len(focus),
            'c4_documents':c4_count,'c4_tokens':c4_tokens,
            'review_status':'Automated diagnostics only; inspect pairs and retain all flagged candidates.'}
    if (root/'requests.sqlite').exists():
        journal=CorpusJournal(root/'requests.sqlite')
        try: result['actual_cost_usd'],result['uncertain_cost_upper_bound']=journal.spend()
        finally: journal.close()
    return result,samples


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',default='ethics_sft_pooled_corpus_v1')
    args=parser.parse_args()
    if not args.run_id.startswith('ethics_sft_') or Path(args.run_id).name != args.run_id:
        raise ValueError('Invalid corpus run ID')
    root=PROJECT/'data/generated/ethical_stance_sft'/args.run_id
    result,samples=inspect(root)
    output=PROJECT/'data/results/ethical_stance_sft'/args.run_id
    output.mkdir(parents=True,exist_ok=True)
    number=len(list(output.glob('audit_*.json')))
    target=output/f'audit_{number:04d}.json'
    corpus.write_json(target,result)
    view=target.with_suffix('.md')
    view.write_text('# Corpus inspection\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\n'+''.join(
        f"## {row['document_id']}\n\n{row['text']}\n\nCritique: {row['critique']}\n\n"
        for row in samples))
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
