"""Finite worker preserves failed phases and never converts qualification failure to success."""
import importlib.util
import json
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('format_matrix',Path(__file__).resolve().parents[1]/'scripts/run_registry_format_matrix.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)


@pytest.fixture
def setup(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    generated=tmp_path/'generated';generated.mkdir()
    (generated/'matrix.json').write_text(json.dumps({'run_id':worker.RUN,'inputs':[]}))
    canary=Path('data/results/ethical_stance_sft')/worker.CANARY
    canary.mkdir(parents=True)
    (canary/'summary.json').write_text(json.dumps({'memorization':{'passed':True},'training':{'checks':{'update':True}}}))
    for _,validation in worker.PAIRS:
        root=Path('data/results/ethical_pilot')/validation;root.mkdir(parents=True)
        (root/'summary.json').write_text(json.dumps({'technical_qualification_passed':False,'arms':{}}))
    calls=[]
    monkeypatch.setattr(worker.subprocess,'check_output',lambda *a,**kw:'testcommit\n')
    monkeypatch.setattr(worker.subprocess,'run',lambda cmd,**kw:calls.append(cmd))
    return generated,tmp_path/'result',canary,calls


def test_three_semantic_failures_are_preserved_and_matrix_stops_without_acceptance(setup):
    generated,root,_,calls=setup
    worker.run(generated,root)
    summary=json.loads((root/'summary.json').read_text())
    assert summary['accepted_run_id'] is None and len(summary['judgments'])==3
    assert len(calls)==7 and all('run.py' in c or 'scripts/validate_registry_calibration.py' in c for c in calls)
    assert (root/'COMPLETED').exists()
    with pytest.raises(FileExistsError):worker.run(generated,root)


def test_failed_canary_halts_expensive_dispatch_and_keeps_failure(setup):
    generated,root,canary,calls=setup
    (canary/'summary.json').write_text(json.dumps({'memorization':{'passed':False},'training':{'checks':{'update':True}}}))
    with pytest.raises(ValueError,match='canary failed'):worker.run(generated,root)
    assert len(calls)==1
    assert (root/'failure.json').exists() and not (root/'COMPLETED').exists()
    assert json.loads((root/'progress.json').read_text())['status']=='FAILED'


def test_selection_prefers_lower_lr_then_assistant(setup):
    generated,root,_,_=setup
    for _,validation in worker.PAIRS:
        p=Path('data/results/ethical_pilot')/validation/'summary.json'
        p.write_text(json.dumps({'technical_qualification_passed':True,'arms':{}}))
    worker.run(generated,root)
    assert json.loads((root/'summary.json').read_text())['accepted_run_id']==worker.PAIRS[2][0]
