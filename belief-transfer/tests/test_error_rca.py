"""Weight-free safety/configuration checks for the finite RCA worker."""
import importlib.util
import json
from pathlib import Path
import pytest
from belief_transfer.config import load_job

spec=importlib.util.spec_from_file_location('error_rca_worker',Path(__file__).resolve().parents[1]/'scripts/run_error_rca.py')
worker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)

def test_rca_profiles_preserve_all_arms_and_model_specific_adapter_bindings():
    jobs=worker.run_ids()
    assert len(jobs)==12 and len({run for _,_,run in jobs})==12
    for arm,profile,run in jobs:
        job=load_job(['+run='+run])
        assert job.stage=='control_recheck'
        assert job.pilot_bench.measurement_decoding.thinking is False
        assert job.pilot_bench.max_new_tokens==256
        assert (job.pilot_bench.adapter_path is None)==(arm=='base')
        assert (job.control_recheck.adapter_sha256 is None)==(arm=='base')
        assert job.control_recheck.seeds==([42,7,1729] if profile=='nonthink_sampled' else [42])
        assert (job.pilot_bench.cuda_generation is None)==(profile=='hf_greedy')
        assert job.pilot_bench.measurement_decoding.temperature==(.7 if profile=='nonthink_sampled' else 0)

def setup_worker(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry=tmp_path/'configs/handoff.json';registry.parent.mkdir()
    paths=[f'{part}/ethical_pilot/{worker.MASTER}' for part in ['generated','results']]+[f'results/ethical_pilot/{run}' for _,_,run in worker.run_ids()]
    registry.write_text(json.dumps({'include_paths':paths}))
    generated,result=worker.registered();generated.mkdir(parents=True)
    return generated,result

def test_rca_refuses_started_master_before_subprocess(tmp_path,monkeypatch):
    gen,result=setup_worker(tmp_path,monkeypatch)
    (gen/'protocol.json').write_text(json.dumps({'source_bindings':{}}));result.mkdir(parents=True)
    monkeypatch.setattr(worker.subprocess,'run',lambda *a,**kw:pytest.fail('No child should launch'))
    with pytest.raises(FileExistsError):worker.run()

def test_rca_refuses_changed_inputs_without_creating_result(tmp_path,monkeypatch):
    gen,result=setup_worker(tmp_path,monkeypatch)
    source=Path('input.txt');source.write_text('changed')
    (gen/'protocol.json').write_text(json.dumps({'source_bindings':{str(source):'0'*64}}))
    with pytest.raises(ValueError,match='changed'):worker.run()
    assert not result.exists()

def test_rca_refuses_started_child_without_restarting(tmp_path,monkeypatch):
    gen,result=setup_worker(tmp_path,monkeypatch)
    _,_,run=worker.run_ids()[0]
    (gen/'protocol.json').write_text(json.dumps({'source_bindings':{},'jobs':[{'run_id':run}]}))
    (Path('data/results/ethical_pilot')/run).mkdir(parents=True)
    with pytest.raises(FileExistsError,match='Child already started'):worker.run()
    assert not result.exists()

def load_analysis():
    spec=importlib.util.spec_from_file_location('error_rca_analysis',Path(__file__).resolve().parents[1]/'scripts/analyze_error_rca.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def test_backend_comparison_separates_input_identity_answers_and_correctness():
    analysis=load_analysis()
    row={'presentation_id':'one','prompt_sha':'p','expected':'agree','answer':'agree','generation_metadata':{'input_token_ids':[1,2]}}
    other={**row,'answer':'disagree','generation_metadata':{'input_token_ids':[1,3]}}
    result=analysis.compare([row],[other])
    assert result['input_token_mismatches']==['one']
    assert result['valid_label_flips']==1 and result['second_worse']==1
    assert result['agreement']==0
    with pytest.raises(ValueError,match='prompt/answer'):analysis.compare([row],[{**other,'expected':'disagree'}])

def test_error_categories_do_not_hide_valid_wrong_labels_as_parser_failures():
    analysis=load_analysis()
    good={'expected':'agree','answer':'agree','strict_format':True}
    cases=[good,{**good,'answer':'disagree'},{**good,'answer':None,'error':'bad format'},
           {**good,'answer':None,'generation_metadata':{'finish_reason':'length'}},
           {**good,'answer':None,'generation_metadata':{'backend_error':'failed'}}]
    assert analysis.summarize_errors(cases)=={'correct_strict':1,'wrong_valid_label':1,'invalid_extraction':1,'length':1,'backend':1}
