"""Fresh domain gates and BASE-first stop, with mocks/tmpdirs and no loaded weights."""
import hashlib,json,shutil,sys
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_target_free_controls as worker
import analyze_target_free_controls as analysis
from belief_transfer import config
from belief_transfer.evals.target_free_controls import build_bank
from belief_transfer.metrics.response_interface_rca import summarize
from belief_transfer.validation.response_interface_rca import assess

def old_rows():
 return [{'control_kind':k,'control_id':'comparison_true/negative','arrangement':1,'expected':'disagree','answer':'agree','options':['disagree','agree'],
  'display_options':['Five is greater than three.','It is not the case that five is greater than three.'],'presentation_id':'control/'+k,
  'generation_metadata':{'sampling_seed':42},'prompt':'Scope: arithmetic.\nTarget statement: It is not the case that five is greater than three.\nA) Five is greater than three.\nB) It is not the case that five is greater than three.'} for k in ['factual','factual_null']]
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v)+'\n')
def write_rows(p,rs):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(json.dumps(r)+'\n' for r in rs))
def bank():return [{**r,'expected_input_tokens':12} for r in build_bank(old_rows(),source_sha256='a'*64)]
def observed(rs):
 return [{**r,'response':'<think>Reference answer.</think>\n'+r['expected_word'].upper(),'generation_metadata':{'finish_reason':'stop'},
     **assess(r,'<think>Reference answer.</think>\n'+r['expected_word'].upper(),{'finish_reason':'stop'},thinking=True)} for r in rs]

def test_separate_fresh_domain_gate_catches_errors_hidden_by_pooled_accuracy():
 rs=observed([r for r in bank() if r['split']=='development']);s=analysis.split_summary(rs)
 assert s['passed'] and s['note_comparison']['expected_pairs']==64
 assert s['independent_repeat']['expected_pairs']==64 and s['order_agreement']['expected_pairs']==96
 for r in [r for r in rs if r['domain']=='arithmetic'][:5]:r.update(answer=next(w for w in r['options'] if w!=r['expected_word']),correct=False)
 s=analysis.split_summary(rs)
 assert s['counts']['accuracy']>.95 and not s['checks']['arithmetic_accuracy_at_least_95pct'] and not s['passed']
 with pytest.raises(ValueError):analysis.split_summary(rs+rs[:1])

def worker_fixture(tmp_path,monkeypatch):
 monkeypatch.chdir(tmp_path);gen=tmp_path/'gen';gen.mkdir();out=tmp_path/'out'
 p={'source_bindings':{},'jobs':[{'arm':a,'run_id':a} for a in ['base','positive','negative']]};write(gen/'protocol.json',p)
 stop=Path('data/results/ethical_pilot/ethics_gpu_paired_readout_v1/operator_stop.json');write(stop,{'status':'STOPPED'})
 monkeypatch.setattr(worker,'registered',lambda:(gen,out));monkeypatch.setattr(worker.subprocess,'check_output',lambda *a,**kw:'fixture')
 return gen,out,p

def test_base_failure_is_a_planned_stop_before_adapters_and_cannot_restart(tmp_path,monkeypatch):
 _,out,_=worker_fixture(tmp_path,monkeypatch);calls=[]
 monkeypatch.setattr(worker.subprocess,'run',lambda cmd,**kw:(calls.append(cmd) or SimpleNamespace(returncode=0)))
 monkeypatch.setattr(analysis,'inspect_model',lambda *a,**kw:{'passed':False})
 worker.run()
 assert len(calls)==2 and (out/'BASE_GATE_FAILED.json').exists() and (out/'BASE_GATE_FAILED.md').exists()
 assert (out/'TERMINAL').exists() and not (out/'COMPLETED').exists()
 assert len(analysis.rows(out/'operations.jsonl'))==1 and (out/'operations.md').exists()
 with pytest.raises(FileExistsError):worker.run()

def test_base_pass_keeps_remaining_adapter_calls_even_if_their_performance_will_fail(tmp_path,monkeypatch):
 _,out,_=worker_fixture(tmp_path,monkeypatch);calls=[]
 monkeypatch.setattr(worker.subprocess,'run',lambda cmd,**kw:(calls.append(cmd) or SimpleNamespace(returncode=0)))
 def inspect(root,item,p):
  assert item['arm']=='base';return {'passed':True}
 monkeypatch.setattr(analysis,'inspect_model',inspect);worker.run()
 assert len(calls)==4 and (out/'COMPLETED').exists()

def test_prepare_composes_all_five_typed_jobs_in_tmpdirs_without_tokenizer_or_weights(tmp_path,monkeypatch):
 cfg=tmp_path/'configs';shutil.copytree(config.CONFIG_DIR,cfg);monkeypatch.setattr(config,'CONFIG_DIR',cfg);monkeypatch.chdir(tmp_path)
 for _,_,run in worker.run_ids():(cfg/'run'/(run+'.yaml')).unlink(missing_ok=True)
 proofs={}
 for arm in ['base','positive','negative','offtopic','c4_only']:
  job=config.load_job(['+run=ethics_gpu_scope_control_'+arm+'_v1']);b=job.pilot_bench;digest=None
  if b.adapter_path:
   p=Path(b.adapter_path)/'adapter_model.safetensors';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture weight bytes, never loaded');digest=worker.sha(p)
  proofs[arm]={'model_config':job.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),'generation':b.cuda_generation.model_dump(),
   'max_new_tokens':b.max_new_tokens,'adapter_sha256':digest,'backend':{},'versions':{}}
 write(Path('data/generated/ethical_pilot')/worker.READOUT/'scope_evidence.json',proofs)
 write_rows(Path('data/results/ethical_pilot/ethics_gpu_paired_readout_base_s42_v1/stance_controls.jsonl'),old_rows())
 original_sha=worker.sha
 monkeypatch.setattr(worker,'sha',lambda p:original_sha(p) if Path(p).exists() else 'a'*64)
 monkeypatch.setattr(worker,'token_counts',lambda rs,job:[12]*len(rs));worker.prepare()
 gen,_=worker.registered();protocol=analysis.read(gen/'protocol.json');assert len(protocol['jobs'])==5 and protocol['expected_calls']==1940
 for item in protocol['jobs']:
  j=config.load_job(['+run='+item['run_id']]);s=j.response_interface_rca
  assert j.stage=='response_interface_rca' and s.expected_rows==388 and j.pilot_bench.measurement_batch_size==64
  assert config.config_sha(j)==item['resolved_config_sha'] and s.bank_sha256==original_sha(gen/'bank.jsonl')
 with pytest.raises(FileExistsError):worker.prepare()

def model_fixture(root,arm,rs,proof,*,fail_arithmetic=False,fail_regression=False):
 run='child-'+arm;folder=root/'results/ethical_pilot'/run;item={'arm':arm,'run_id':run,'adapter_sha256':None if arm=='base' else 'adapter-'+arm}
 data=observed(rs)
 bad=[r for r in data if r['split']=='validation' and r['domain']=='arithmetic'][:5] if fail_arithmetic else []
 if fail_regression:bad += [r for r in data if r['split']=='regression']
 for r in bad:
  r['response']='<think>Wrong reply fixture.</think>\n'+next(w.upper() for w in r['options'] if w!=r['expected_word']);r.update(assess(r,r['response'],r['generation_metadata'],thinking=True))
 for r in data:r['generation_metadata'].update(model_revision='pinned',adapter_lora_id=None if arm=='base' else 1,sampling_seed=r['sampling_seed'],execution_versions=proof['versions'],input_token_ids=[1]*12)
 write_rows(folder/'bank.jsonl',rs);write_rows(folder/'observations.jsonl',data);write(folder/'summary.json',summarize(data))
 write(folder/'manifest.json',{**proof,'model_label':arm,'adapter_sha256':item['adapter_sha256'],'bank_sha256':worker.sha(folder/'bank.jsonl')})
 (folder/'COMPLETED').write_text('done');return item

def test_full_analysis_preserves_failed_adapter_and_excludes_reused_probe_from_gates(tmp_path):
 rs=bank();gen=tmp_path/'generated/ethical_pilot'/analysis.MASTER;write_rows(gen/'bank.jsonl',rs)
 proof={'model_config':{},'backend':{},'decoder':{'thinking':True},'generation':{'revision':'pinned'},'versions':{},'max_new_tokens':4096}
 arms=['base','positive','negative','offtopic','c4_only'];jobs=[model_fixture(tmp_path,a,rs,proof,fail_arithmetic=a=='negative',fail_regression=a=='base') for a in arms]
 p={'jobs':jobs,'runtime_evidence':{a:proof for a in arms}};write(gen/'protocol.json',p)
 report=analysis.analyze(tmp_path);assert report['complete'] and not report['qualified_for_prospective_readout']
 assert not report['models']['negative']['passed'] and report['models']['base']['passed']
 assert report['models']['base']['regression']['counts']['correct']==0
 with pytest.raises(FileExistsError):analysis.analyze(tmp_path)
 # Tampered per-request identity is not a model failure or a neutral answer.
 path=tmp_path/'results/ethical_pilot/child-base/observations.jsonl';data=analysis.rows(path);data[0]['generation_metadata']['sampling_seed']+=1;write_rows(path,data)
 with pytest.raises(ValueError,match='identity'):analysis.inspect_model(tmp_path,jobs[0],p)
