from collections import Counter
import pytest
from belief_transfer.dataset.ethical_pilot import select_subjects, spread_budget, training_request, INITIAL

def test_selection_is_outcome_independent_and_category_bounded():
    briefs=[{'id':i,'role':'ethical','category':'animal' if n<2 else 'environment'} for n,i in enumerate(INITIAL)]
    briefs += [{'id':f'{cat}_{i}','role':'ethical','category':str(cat)} for cat in range(7) for i in range(3)]
    chosen=select_subjects(briefs)
    assert chosen==select_subjects(list(reversed(briefs)))
    assert len(chosen)==10 and chosen[:3]==list(INITIAL)
    assert Counter(next(b['category'] for b in briefs if b['id']==i) for i in chosen)['animal']==2

def test_budget_keeps_all_documents_and_exact_targets():
    assert spread_budget([5,7,10],22)==[5,7,10]
    assert spread_budget([5,7,10],6)==[2,2,2]
    for target in range(6,23):
        values=spread_budget([5,7,10],target)
        assert sum(values)==target and all(2<=x<=cap for x,cap in zip(values,[5,7,10]))
    with pytest.raises(ValueError):spread_budget([5,7],3)
    with pytest.raises(ValueError):spread_budget([5,7],13)

def test_training_requests_do_not_expose_assigned_position():
    brief={'claim':'Canonical claim.', 'scope':'Fixed circumstances.'}
    assert len({training_request(brief,i) for i in range(8)})==8
    assert 'positive' not in training_request(brief,0) and 'negative' not in training_request(brief,0)
    assert brief['scope'] in training_request(brief,0)
