import importlib.util
from pathlib import Path
from collections import Counter


def test_blind_selection_excludes_prior_ids_and_balances_categories_and_positions():
    p=Path(__file__).resolve().parents[1]/'scripts/prepare_scope_followup.py'
    spec=importlib.util.spec_from_file_location('scope_selection',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    briefs={f'{c}-{i}':{'category':c} for c in ('a','b') for i in range(10)}
    rows=[dict(subject_id=s,position=p,document_id=f'{s}-{p}-{j}')
          for s in briefs for p in ('positive','negative') for j in range(3)]
    excluded={r['document_id'] for r in rows[:4]}
    chosen=m.select_blind(rows,briefs,excluded)
    assert len(chosen)==16 and len({r['subject_id'] for r in chosen})==16
    assert not ({r['document_id'] for r in chosen}&excluded)
    assert Counter((briefs[r['subject_id']]['category'],r['position']) for r in chosen)=={
        ('a','positive'):4,('a','negative'):4,('b','positive'):4,('b','negative'):4}
    assert chosen==m.select_blind(list(reversed(rows)),briefs,excluded)
