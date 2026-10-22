"""Factorial response reliability counts; standard library only."""
from __future__ import annotations

def summarize(rows:list[dict])->dict:
    def counts(xs):
        n=len(xs);valid=sum(r.get('answer') is not None and not r.get('error') for r in xs)
        correct=sum(bool(r.get('correct')) for r in xs);strict=sum(bool(r.get('strict_format')) for r in xs)
        return {'expected':n,'valid':valid,'correct':correct,'strict':strict,'accuracy':correct/n if n else None,
                'wrong_valid':sum(r.get('answer') is not None and not r.get('correct') and not r.get('error') for r in xs),
                'length_limited':sum(r.get('error')=='generation_token_limit' for r in xs),
                'development_pass':bool(n and correct/n>=.95 and valid==n and strict==n)}
    return {'overall':counts(rows),'by_vocabulary':{v:counts([r for r in rows if r['vocabulary']==v]) for v in sorted({r['vocabulary'] for r in rows})},
            'by_vocabulary_representation':{v+'/'+rep:counts([r for r in rows if r['vocabulary']==v and r['representation']==rep]) for v in sorted({r['vocabulary'] for r in rows}) for rep in ['words','digits']},
            'interpretation':'Development on8reused facts, not independent qualification. Count wrong valid answers separately from missing finals/format. No ethical scores or old gate changes.'}
