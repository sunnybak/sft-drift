"""Separate exact final-word diagnostic extractor; frozen extractor stays untouched."""
from __future__ import annotations

def assess(row:dict,text:str,metadata:dict,*,thinking:bool)->dict:
    final=text;error=None
    if metadata.get('backend_error'):error='backend_error'
    elif metadata.get('finish_reason')=='length':error='generation_token_limit'
    elif metadata.get('finish_reason')!='stop':error='generation_stop_unverified'
    elif thinking:
        if text.count('</think>')!=1:error='incomplete_reasoning_boundary'
        else:final=text.split('</think>',1)[1].strip()
    if error:final=None
    word=final.strip().lower() if final is not None else None
    valid=word in row['options']
    return {'final_response':final,'answer':word if valid else None,'correct':valid and word==row['expected_word'],
       'strict_format':valid and final.strip() in row['options'],
       'error':error or (None if valid else 'final_word_not_in_declared_vocabulary'),
       'extractor_version':'response-rca-exact-word-v1'}
