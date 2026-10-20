import pytest
from belief_transfer.dataset.pooled_dose import mixed_assignments, paired_budgets, budget_draws, matched_steps


def test_mixes_balanced_complementary_order_invariant():
    briefs=[{'id':f'{c}{i}','category':c,'role':'ethical'} for c in ('a','b') for i in range(10)]
    a,b=mixed_assignments(briefs)
    assert mixed_assignments(briefs[::-1])==(a,b)
    assert all(a[k]!=b[k] for k in a)
    assert all(sum(a[f'{c}{i}']=='positive' for i in range(10))==5 for c in ('a','b'))


def test_pair_dose_independent_of_selected_position():
    rows=[{'document_id':f'x__{i:04}__{p}','subject_id':'x','position':p} for i in range(2) for p in ('positive','negative')]
    caps={r['document_id']: 400+i for i,r in enumerate(rows)}
    budgets=paired_budgets(rows,caps,documents_per_position=2)
    assert budgets['x__0000__positive']==budgets['x__0000__negative']==400
    with pytest.raises(ValueError,match='Missing'):paired_budgets(rows[:-1],caps,documents_per_position=2)
    with pytest.raises(ValueError,match='Duplicate'):paired_budgets(rows+rows[:1],caps,documents_per_position=2)


@pytest.mark.parametrize('target',[2,3,4,5,6,7,8,9,10,11,12,13,37,400])
def test_repeat_exact_budget_no_single_token_draw(target):
    caps={'a':5,'b':3}
    draws=budget_draws(['a','b'],caps,target,repeat=True)
    assert sum(n for _,n in draws)==target
    assert all(2<=n<=caps[id] for id,n in draws)


def test_c4_reserve_disjoint_unique_and_bounded():
    caps={'a':5,'b':3,'c':4}
    draws=budget_draws(list(caps),caps,6,repeat=False)
    assert draws==[('a',4),('b',2)]
    with pytest.raises(ValueError,match='Insufficient'):budget_draws(list(caps),caps,13,repeat=False)


def test_steps_halfway_exact_and_one_pass_feasible():
    assert matched_steps([200,170,180],batch_size=2,grad_accum=4)==26
    with pytest.raises(ValueError,match='smallest'):matched_steps([200,50],batch_size=2,grad_accum=4)
