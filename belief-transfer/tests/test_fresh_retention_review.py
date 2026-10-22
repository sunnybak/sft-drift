import hashlib
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from finalize_fresh_retention_review import summarize_values


def fixture():
    def row(seed,text,exact):
        return {'example_id':'case','eval_seed':seed,'thinking':False,'family':'sum','split':'development','expected':'3',
            'response':text,'response_sha256':hashlib.sha256(text.encode()).hexdigest(),'error':None,
            'assessment':{'admissible':exact,'exact_answer':exact,'normal_stop':True,'response_boundaries_valid':True}}
    observed={'base':[row(s,'1+2=3',False) for s in [42,7,1729]],'adapter':[row(s,'2',False) for s in [42,7,1729]]}
    annotations=[{'arm':arm,'example_id':r['example_id'],'eval_seed':r['eval_seed'],'response_sha256':r['response_sha256'],
        'review_mode':'agent_read_full_response','original_grade_unchanged':True,'agent_value_correct':arm=='base'} for arm,rs in observed.items() for r in rs]
    return observed,annotations


def test_correct_worked_answer_enters_value_cohort_without_changing_grade():
    observed,annotations=fixture();values,summary=summarize_values(observed,annotations)
    assert summary['adapter']['False']['stable_value_losses']==['case']
    assert summary['base']['False']['by_seed']['42']['value_known_n']==1
    assert all(not r['original_assessment']['admissible'] for r in values)
    assert not observed['base'][0]['assessment']['admissible']


def test_missing_duplicate_or_tampered_review_fails():
    observed,annotations=fixture()
    for bad in [annotations[:-1],annotations+annotations[:1],[{**r,'response_sha256':'a'*64} for r in annotations]]:
        with pytest.raises(ValueError):summarize_values(observed,bad)
    observed['base'][0]['error']='backend'
    with pytest.raises(ValueError,match='incomplete'):summarize_values(observed,annotations)
