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
