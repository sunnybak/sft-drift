import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import run_ethical_four_arm as worker
import analyze_ethical_four_arm as analysis

def test_failed_qualification_still_selects_explicit_unqualified_measurement():
    assert worker.measurement_choice(True,True)=='stance'
    assert all(worker.measurement_choice(a,b)=='unqualified' for a,b in [(False,False),(True,False),(False,True)])

def test_failed_operation_preserves_returncode_and_command(tmp_path):
    assert not worker.execute(['example','--arg'],tmp_path,'fixture',runner=lambda *a,**k:SimpleNamespace(returncode=5))
    row=json.loads((tmp_path/'operations.jsonl').read_text())
    assert row['returncode']==5 and row['command']==['example','--arg']
    assert (tmp_path/'operations.md').exists()

def test_primary_keeps_all_beliefs_and_refuses_missing_primary_pair(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    master=Path('data/generated/ethical_stance_sft')/analysis.pilot.MASTER;master.mkdir(parents=True)
    ids=[f'b{i}' for i in range(100)]
    (master/'plan.json').write_text(json.dumps({'subjects':ids[:10]}))
    (master/'analysis_groups.json').write_text(json.dumps({'beliefs':{id:{'analysis_group':'target' if i<10 else 'other_untrained_ethical','category':'fixture','related_group':None} for i,id in enumerate(ids)}}))
    out=Path('data/results/ethical_stance_sft')/analysis.pilot.MASTER;out.mkdir(parents=True)
    def write_summary(id,value):
        root=Path('data/results/ethical_pilot')/id;root.mkdir(parents=True)
        score={'support':value,'diagnostics':{'complete':True},'order_consistency':{},'paraphrase_consistency':{},'n_expected_negation_pairs':12,'n_eligible_negation_pairs':12,'n_contradictions':0,'polarity_profile':{}}
        data={k:'unchanged' for k in ('version','extractor_version','measurement_bank_sha','decoding','backend')}
        data.update(meta_eval={'model_controls':{}},measurements={'stance':{id:{'neutral':score} for id in ids}})
        (root/'measurement_summary.json').write_text(json.dumps(data))
    for seed in analysis.pilot.SEEDS:
        write_summary(analysis.BASE[seed],.5)
        for arm in analysis.pilot.ARMS:write_summary(analysis.pilot.eval_id(arm,'stance',seed),.75 if arm=='positive' else .25 if arm=='negative' else .5)
    analysis.main();result=json.loads((out/'analysis.json').read_text())
    assert result['primary_contrast']==.5 and result['rows']==1200
    assert result['belief_cluster_95_interval']==[.5,.5]
    path=Path('data/results/ethical_pilot')/analysis.pilot.eval_id('positive','stance',42)/'measurement_summary.json'
    changed=json.loads(path.read_text());changed['measurements']['stance']['b0']['neutral']['diagnostics']['complete']=False;path.write_text(json.dumps(changed))
    analysis.main();result=json.loads((out/'analysis.json').read_text())
    assert result['primary_contrast'] is None and result['primary_verdict']=='not_estimable' and result['rows']==1200
    assert (out/'per_belief_results.md').exists()
