"""Frozen retention assessment mirrored for typed jobs.

The historical acquisition helper is unchanged. Tests require source equivalence;
do not reinterpret answers or alter the frozen scoring during this investigation.
"""
from __future__ import annotations
import re

def assess(text: str, row: dict, *, normal_stop: bool) -> dict:
    from belief_transfer.dataset.document_sft import validate_replay
    valid=True;reason=None
    try:
        validate_replay({'training_request':row['prompt'],'thinking':row['thinking'],'text':text,
                         'response_format_version':'qwen3_raw_response_v1'})
    except ValueError as exc:
        valid=False;reason=str(exc)
    final=(text.split('</think>',1)[-1] if row['thinking'] else text).strip() if valid else None
    exact=final==row['expected']
    semantic=False
    if final is not None:
        if row['answer_type']=='integer':
            semantic={int(n) for n in re.findall(r'(?<!\w)-?\d+(?!\w)',final)}=={int(row['expected'])}
        elif row['answer_type']=='csv':
            semantic=list(map(int,re.findall(r'-?\d+',final)))==list(map(int,row['expected'].split(',')))
        else:
            words=re.findall(r'\b(?:YES|NO)\b',final,flags=re.I) if row['expected'] in {'YES','NO'} else re.findall(r'\b[A-Za-z]+\b',final)
            semantic={w.upper() for w in words}=={row['expected']}
    pattern={'integer':r'-?\d+', 'csv':r'-?\d+(,-?\d+){'+str(len(row['expected'].split(','))-1)+'}',
             'word':r'(YES|NO)' if row['expected'] in {'YES','NO'} else r'[A-Z]+'}[row['answer_type']]
    strict=bool(final is not None and re.fullmatch(pattern,final))
    return {'final':final,'semantic_correct':semantic,'exact_answer':exact,'strict_format':strict,'response_boundaries_valid':valid,
            'boundary_error':reason,'normal_stop':normal_stop,'admissible':bool(exact and strict and valid and normal_stop)}

