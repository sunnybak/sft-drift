import pytest
from belief_transfer.evals.retention_value import assess_value
from belief_transfer.evals.instruction_retention import assess


def task(family='sum',expected='19',kind='integer',**proof):
    return {'family':family,'expected':expected,'answer_type':kind,'thinking':False,
        'prompt':'fixture','truth_proof':{'a':12,'b':7,**proof}}


@pytest.mark.parametrize('answer,correct,diagnostic',[
    ('19',True,None),('12 + 7 = 19',True,None),('7+12=19',True,None),
    ('18',False,'WRONG_VALUE'),('12+7=18',False,'WRONG_EQUALITY_OR_VALUE'),
    ('12+8=19',False,'INPUT_REWRITE'),('19+0=19',False,'INPUT_REWRITE'),
    ('19 is the answer',None,'UNSUPPORTED_OR_AMBIGUOUS_FINAL'),
    ('18 or 19',None,'UNSUPPORTED_OR_AMBIGUOUS_FINAL'),('19 20',None,'UNSUPPORTED_OR_AMBIGUOUS_FINAL'),
    ('__import__("os")',None,'UNSUPPORTED_OR_AMBIGUOUS_FINAL'),
])
def test_value_and_format_are_independent(answer,correct,diagnostic):
    r=task();new=assess_value(answer,r,normal_stop=True)
    assert new['value_correct'] is correct and new['diagnostic']==diagnostic
    assert new['frozen_assessment']==assess(answer,r,normal_stop=True)
    if '=' in answer and correct:
        assert not new['frozen_assessment']['semantic_correct']
        assert not new['frozen_assessment']['strict_format']


def test_other_math_forms_respect_operands_and_truth():
    for row,text in [(task('difference','195'),'207-12=195'),
                     (task('product','36',factor=3),'3×12=36'),
                     (task('progression','54',step=14),'40+14=54')]:
        assert assess_value(text,row,normal_stop=True)['value_correct']
    assert assess_value('24,112',task(expected='24112'),normal_stop=True)['value_correct']
    assert assess_value('240,12',task(expected='24112'),normal_stop=True)['value_correct'] is None


def test_character_order_case_spacing_and_logical_values():
    r=task('uppercase','WXZLFE','word',word='wxzlfe')
    assert assess_value('W X Z L F E',r,normal_stop=True)['value_correct']
    for bad in ['WXLFE','WXZLEF','wxzlfe']:
        assert assess_value(bad,r,normal_stop=True)['value_correct'] is False
    r=task('comparison','NO','word')
    assert assess_value('no',r,normal_stop=True)['value_correct']
    assert assess_value('YES',r,normal_stop=True)['value_correct'] is False
    r=task('sort','1,2,3','csv')
    assert assess_value('1, 2, 3',r,normal_stop=True)['value_correct']
    assert assess_value('1,3,2',r,normal_stop=True)['value_correct'] is False


def test_missing_boundary_cap_never_becomes_neutral_or_correct():
    r=task()
    assert assess_value(None,r,normal_stop=True)['diagnostic']=='MISSING_RESPONSE'
    assert assess_value('19',r,normal_stop=False)['value_correct'] is None
    r['thinking']=True
    for text in ['19','<think>incomplete','<think>\n\n</think>\n19']:
        assert assess_value(text,r,normal_stop=True)['value_correct'] is None
    assert assess_value('<think>\nCheck.\n</think>\n\n19',r,normal_stop=True)['value_correct']
