"""Finite worker safeguards; no weights or experimental result writes."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest
from belief_transfer.config import load_job
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
def worker():
 spec=importlib.util.spec_from_file_location('response_worker',SCRIPTS/'run_response_interface_rca.py')
 module=importlib.util.module_from_spec(spec)
 sys.path.insert(0,str(SCRIPTS))
 try:spec.loader.exec_module(module)
 finally:sys.path.remove(str(SCRIPTS))
 return module

def test_prepared_factorial_jobs_are_bound_and_modes_distinct():
 w=worker();assert len(w.run_ids())==4
 for arm,mode,run in w.run_ids():
  job=load_job(['+run='+run]);bench=job.pilot_bench
  assert job.stage=='response_interface_rca' and job.control_recheck is None
  assert (bench.adapter_path is None)==(arm=='base')
  assert (job.response_interface_rca.adapter_sha256 is None)==(arm=='base')
  assert bench.measurement_decoding.thinking==(mode=='thinking')
  assert bench.max_new_tokens==(4096 if mode=='thinking' else 256)
  assert bench.cuda_generation.engine=='vllm'

def setup(w,tmp_path,monkeypatch):
 monkeypatch.chdir(tmp_path);p=Path('configs/handoff.json');p.parent.mkdir()
 p.write_text(json.dumps({'include_paths':[f'{part}/ethical_pilot/{w.MASTER}' for part in ['generated','results']]+[f'results/ethical_pilot/{run}' for _,_,run in w.run_ids()]}))
 gen,result=w.registered();gen.mkdir(parents=True);return gen,result

def test_worker_refuses_master_and_changed_bindings(tmp_path,monkeypatch):
 w=worker();gen,result=setup(w,tmp_path,monkeypatch)
 protocol=gen/'protocol.json';protocol.write_text(json.dumps({'source_bindings':{}}));result.mkdir(parents=True)
 monkeypatch.setattr(w.subprocess,'run',lambda *a,**kw:pytest.fail('Must not launch GPU'))
 with pytest.raises(FileExistsError):w.run()
 result.rmdir();Path('bank.txt').write_text('changed');protocol.write_text(json.dumps({'source_bindings':{'bank.txt':'0'*64}}))
 with pytest.raises(ValueError,match='changed'):w.run()
 assert not result.exists()

def test_worker_refuses_started_child(tmp_path,monkeypatch):
 w=worker();gen,result=setup(w,tmp_path,monkeypatch);run=w.run_ids()[0][2]
 (gen/'protocol.json').write_text(json.dumps({'source_bindings':{},'jobs':[{'run_id':run}]}))
 (Path('data/results/ethical_pilot')/run).mkdir(parents=True)
 with pytest.raises(FileExistsError,match='Child'):w.run()
 assert not result.exists()

def test_response_comparison_requires_exact_paired_inputs():
 spec=importlib.util.spec_from_file_location('response_analysis',SCRIPTS/'analyze_response_interface_rca.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 a={'presentation_id':'x','prompt_sha256':'h','expected_word':'yes','sampling_seed':1,'answer':'yes','correct':True,'generation_metadata':{'input_token_ids':[1]}}
 b={**a,'answer':'no','correct':False}
 assert module.paired([a],[b])['second_worse']==1
 with pytest.raises(ValueError,match='duplicate'):module.paired([a,a],[b,b])
 with pytest.raises(ValueError,match='inputs'):module.paired([a],[{**b,'sampling_seed':2}])

def test_full_analysis_keeps_complete_factorial_counts(tmp_path):
 from belief_transfer.evals.response_interface_rca import build_bank
 spec=importlib.util.spec_from_file_location('response_analysis_fixture',SCRIPTS/'analyze_response_interface_rca.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 bank=build_bank();gen=tmp_path/'generated/ethical_pilot'/module.MASTER;gen.mkdir(parents=True)
 text=''.join(json.dumps(r)+'\n' for r in bank);(gen/'bank.jsonl').write_text(text)
 (gen/'protocol.json').write_text(json.dumps({'jobs':[{'run_id':'fixture','mode':'nonthinking','arm':'base','adapter_sha256':None}]}))
 child=tmp_path/'results/ethical_pilot/fixture';child.mkdir(parents=True);(child/'COMPLETED').write_text('recorded')
 (child/'bank.jsonl').write_text(text);(child/'summary.json').write_text('{}')
 (child/'manifest.json').write_text(json.dumps({'adapter_sha256':None,'bank_sha256':module.sha(gen/'bank.jsonl')}))
 (child/'observations.jsonl').write_text(''.join(json.dumps({**r,'response':r['expected_word'],'answer':r['expected_word'],'correct':True,'strict_format':True,'error':None,'generation_metadata':{'model_revision':module.REVISION}})+'\n' for r in bank))
 result=module.analyze(tmp_path)
 assert result['complete'] and len(result['base_development_candidates_in_preregistered_order'])==4
 assert result['profiles']['nonthinking']['base']['overall']['correct']==256
 with pytest.raises(FileExistsError):module.analyze(tmp_path)
