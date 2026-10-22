"""Prospective paired readout: semantic choices, identity, uncertainty and preservation."""
from collections import Counter
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_paired_readout as worker
import analyze_paired_readout as analysis
from belief_transfer import config
from belief_transfer.evals.measurements import stance_presentation
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.metrics.measurements import summarize_measurement,summarize_controls
from belief_transfer.stages.measurements import observed_backend_reply,measurement_bank_fingerprint
from belief_transfer.validation.measurements import EXTRACTOR_VERSION

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data)+'\n')
def write_rows(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(r)+'\n' for r in data))
def make_bank():
    bank=[]
    for b in range(100):
        for w in range(6):
            claim=f'Practice {b} wording {w} is acceptable.';opposite='It is not the case that '+claim
            for p in ['positive','negative']:
                for order in [0,1]:
                    row=stance_presentation(f'b{b}/w{w}/{p}/{order}',claim if p=='positive' else opposite,opposite if p=='positive' else claim,
                        'Fixture scope',['agree','disagree'] if order==0 else ['disagree','agree'],interface='explicit_positions',
                        belief_id=f'b{b}',wording_id=f'w{w}',polarity=p,arrangement=order,frame='neutral',statement=claim,scope='Fixture scope')
                    bank.append(row)
    return bank

def test_mapping_pair_denominators_and_missing_are_not_fabricated():
    bank=make_bank();observed=[{**r,'answer':'agree' if r['polarity']=='positive' else 'disagree','error':None} for r in bank]
    expected={'order':1200,'wording':6000,'target_mirror':1200}
    for axis,n in expected.items():
        a=analysis.agreement(observed,axis);assert a=={'expected':n,'eligible':n,'agreeing':n,'rate_over_eligible':1}
    repeats=observed*3;a=analysis.agreement(repeats,'same_prompt');assert a['expected']==7200 and a['rate_over_eligible']==1
    changed=[dict(r) for r in observed];changed[0].update(answer=None,error='length')
    a=analysis.agreement(changed,'target_mirror');assert a['expected']==1200 and a['eligible']==1199
    e=analysis.endpoint(changed,observed);assert e['value'] is None and e['missing']==1 and e['drift'] is None
    assert e['drift_lower']==pytest.approx(-1/2400) and e['drift_upper']==0
    # The exact same position maps to opposite semantic agree/disagree on mirrored targets.
    changed[0].update(answer='disagree',error=None)
    assert analysis.agreement(changed,'target_mirror')['agreeing']==1199

def test_seed_spread_is_separate_from_missing_bounds():
    s=analysis.spread([.1,.2,.3]);assert s['mean']==pytest.approx(.2) and s['sample_stdev']==pytest.approx(.1)
    s=analysis.spread([.1,None,.3]);assert s['mean'] is None and s['min'] is None and s['complete_seeds']==2

def test_all_fifteen_configs_compose_only_in_temporary_tree(tmp_path,monkeypatch):
    directory=tmp_path/'configs';shutil.copytree(config.CONFIG_DIR,directory);monkeypatch.setattr(config,'CONFIG_DIR',directory)
    for arm,seed,run in worker.run_ids():
        import yaml
        adapter=None if arm=='base' else f'data/checkpoints/fixture/{arm}'
        p=directory/'run'/(run+'.yaml');p.write_text('# @package _global_\n'+yaml.safe_dump(worker.overlay(arm,seed,adapter)))
        j=config.load_job(['+run='+run]);worker.check_config(j,seed)
        assert j.pilot_bench.adapter_path==adapter and j.run_id==run
        assert j.pilot_bench.max_new_tokens==4096 and j.pilot_bench.cuda_generation.max_model_len==4352
        assert j.pilot_bench.measurement_decoding.temperature==.6
        assert [(m.name,m.version) for m in j.pilot_bench.measurements]==[('stance','stance-v2')]
        with pytest.raises(ValueError,match='full planned'):
            worker.check_config(j.model_copy(update={'pilot_bench':j.pilot_bench.model_copy(update={'stance_interface':'named_endorse_reject'})}),seed)
    assert len(worker.run_ids())==15

def qualification_fixture(tmp_path):
    folder=tmp_path/'results/ethical_pilot'/worker.CONTROLS;folder.mkdir(parents=True);sources=[]
    for i in range(20):
        p=tmp_path/f'source{i}';p.write_text('fixture');sources.append({'path':str(p),'sha256':worker.sha(p)})
    models={a:{'passed':{'paired':True},'forms':{'paired':{s:{'passed':True,'checks':{'domain':True}} for s in ['development','validation']}}} for a in worker.ARMS}
    report={'complete':True,'pending':[],'models':models,'paired_eligible_for_prospective_readout':True,'sources':sources}
    write(folder/'analysis.json',report);(folder/'COMPLETED').write_text('done');return folder,report

def test_launch_requires_every_model_domain_and_exact_source(tmp_path):
    folder,r=qualification_fixture(tmp_path);worker.qualification(tmp_path)
    r['models']['negative']['forms']['paired']['validation']['checks']['domain']=False
    write(folder/'analysis.json',r)
    with pytest.raises(ValueError,match='domain/split'):worker.qualification(tmp_path)
    r['models']['negative']['forms']['paired']['validation']['checks']['domain']=True;write(folder/'analysis.json',r)
    Path(r['sources'][0]['path']).write_text('changed')
    with pytest.raises(ValueError,match='source changed'):worker.qualification(tmp_path)

def worker_fixture(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);g=tmp_path/'gen';g.mkdir();result=tmp_path/'result'
    p={'source_bindings':{},'jobs':[{'run_id':n} for n in ['first','second','third']]};write(g/'protocol.json',p)
    monkeypatch.setattr(worker,'registered',lambda:(g,result));monkeypatch.setattr(worker,'qualification',lambda:({},{}))
    return g,result,p

def test_worker_preserves_failed_boundary_without_retry_or_overwrite(tmp_path,monkeypatch):
    g,result,p=worker_fixture(tmp_path,monkeypatch);calls=[]
    def run(cmd,**kw):calls.append(cmd);return SimpleNamespace(returncode=7 if '+run=second' in cmd else 0)
    monkeypatch.setattr(worker.subprocess,'run',run);monkeypatch.setattr(worker.subprocess,'check_output',lambda *a,**kw:'fixture')
    with pytest.raises(RuntimeError,match='second'):worker.run()
    assert len(calls)==3 and (result/'worker_failure.json').exists() and (result/'TERMINAL').exists()
    assert not (result/'COMPLETED').exists() and (result/'operations.md').exists()
    assert [r['returncode'] for r in worker.rows(result/'operations.jsonl')]==[0,7]
    with pytest.raises(FileExistsError):worker.run()

def test_worker_refuses_changed_source_or_started_child(tmp_path,monkeypatch):
    g,result,p=worker_fixture(tmp_path,monkeypatch);source=tmp_path/'source';source.write_text('changed')
    p['source_bindings']={str(source):'wrong'};write(g/'protocol.json',p)
    monkeypatch.setattr(worker.subprocess,'run',lambda *a,**kw:pytest.fail('No inference allowed'))
    with pytest.raises(ValueError,match='sources changed'):worker.run()
    assert not result.exists()
    p['source_bindings']={};write(g/'protocol.json',p);(tmp_path/'data/results/ethical_pilot/first').mkdir(parents=True)
    with pytest.raises(FileExistsError,match='child already'):worker.run()

def run_fixture(root,arm,seed,bank,cb,proof,*,missing=False,manifest=None):
    run=f'ethics_gpu_paired_readout_{arm}_s{seed}_v1';folder=root/'results/ethical_pilot'/run
    item={'arm':arm,'seed':seed,'run_id':run,'adapter_path':None if arm=='base' else 'fixture/'+arm,'adapter_sha256':None if arm=='base' else 'weight-'+arm}
    natural=[];controls=[]
    for dest,rs in [(natural,bank),(controls,cb)]:
        for i,r in enumerate(rs):
            agree=(r.get('polarity')=='positive')==(arm!='negative') if dest is natural else r['expected']=='agree'
            if 'expected' in r:answer=r['expected']
            else:answer='agree' if agree else 'disagree'
            word='AB'[r['options'].index(answer)];meta={'finish_reason':'stop','model_revision':'pinned','adapter_lora_id':None if arm=='base' else 1,
                'sampling_seed':(seed^int(r['prompt_sha'][:8],16))&0xffffffff,'execution_versions':proof['versions'],'input_token_ids':[1,i]}
            raw='<think>Fixture reasoning.</think>\n'+word
            if missing and i==0 and dest is natural:raw='<think>Incomplete';meta['finish_reason']='length'
            dest.append(observed_backend_reply(r,raw,meta,thinking=True,seed=meta['sampling_seed']))
    summary={'measurement_bank_sha':worker.BANK_SHA,'extractor_version':EXTRACTOR_VERSION,'model_config_sha':fingerprint(proof['model_config']),
        'backend':proof['backend'],'adapter':item['adapter_path'],'decoding':{**proof['decoder'],'max_new_tokens':4096,'execution':proof['generation'],
            'execution_versions':proof['versions'],'seed':seed,'batch_size':256},'measurements':{'stance':summarize_measurement(bank,natural)},
        'meta_eval':{'model_controls':{'stance':summarize_controls(cb,controls)}}}
    manifest=manifest or {}
    summary['bank_sha']=fingerprint(manifest)
    write(folder/'measurement_summary.json',summary);write(folder/'measurement_manifest.json',manifest)
    for name,values in [('stance_bank',bank),('stance_control_bank',cb),('stance_observations',natural),('stance_controls',controls)]:write_rows(folder/(name+'.jsonl'),values)
    return item,summary,natural,controls

def full_fixture(root,monkeypatch,*,missing=False):
    g=root/'generated/ethical_pilot'/worker.MASTER;g.mkdir(parents=True);bank=make_bank();cb=[]
    for i in range(32):
        r=stance_presentation('control/'+str(i),'Fixture is true.','Fixture is false.','Scope',['agree','disagree'] if i%2==0 else ['disagree','agree'],interface='explicit_positions',control_kind='factual',expected='agree',control_id=str(i),arrangement=i%2)
        cb.append(r)
    groups={f'b{i}':{'analysis_group':'target' if i<10 else 'related_untrained' if i<16 else 'other_untrained_ethical' if i<90 else 'offtopic_eval'} for i in range(100)}
    proof={'model_config':{'pretrained':'fixture'},'backend':{'backend':'fixture'},'decoder':{'thinking':True,'temperature':.6},
        'max_new_tokens':4096,'generation':{'revision':'pinned'},'versions':{'vllm':'fixture'}}
    manifest={'version':'fixture/paired','banks':{'stance':fingerprint(bank)},'controls':{'stance':fingerprint(cb)},
        'source_manifest':{'targets_sha':'fixed','wordings_sha':'fixed'}}
    fixture_sha=measurement_bank_fingerprint(manifest)
    monkeypatch.setattr(worker,'BANK_SHA',fixture_sha);monkeypatch.setattr(analysis,'BANK_SHA',fixture_sha)
    jobs=[];first=None
    for arm,seed,_ in worker.run_ids():
        item,summary,natural,controls=run_fixture(root,arm,seed,bank,cb,proof,missing=missing and arm=='offtopic' and seed==7,manifest=manifest)
        jobs.append(item)
        if first is None:first=(summary,natural,controls,item)
    write(g/'protocol.json',{'jobs':jobs,'runtime_evidence':{a:proof for a in worker.ARMS},'measurement_bank_sha':worker.BANK_SHA,'evaluation_seeds':worker.SEEDS})
    write(g/'analysis_groups.json',{'beliefs':groups});write_rows(g/'stance_bank.jsonl',bank);write_rows(g/'control_bank.jsonl',cb)
    return g,bank,cb,proof,first

def test_full_analysis_keeps_all500_cells_and_missing_bounds(tmp_path,monkeypatch):
    full_fixture(tmp_path,monkeypatch,missing=True);report=analysis.analyze(tmp_path)
    assert report['complete'] and len(report['models'])==5 and report['contrast_seed_variability']['mean']==1
    off=report['models']['offtopic'];assert off['complete_seeds'] and off['pooled_completed_seeds']['all']['value'] is None
    assert off['same_prompt']['expected']==7200 and off['same_prompt']['eligible']==7198
    assert off['drift_seed_variability']['all']['mean'] is None
    out=tmp_path/'results/ethical_pilot'/worker.MASTER/'per_belief_results.jsonl'
    assert len(out.read_text().splitlines())==500 and out.with_suffix('.md').exists()
    with pytest.raises(FileExistsError):analysis.analyze(tmp_path)

def test_raw_extraction_and_request_identity_are_reconstructed(tmp_path):
    bank=make_bank()[:1];cb=[{**bank[0],'presentation_id':'control','expected':'agree','control_kind':'factual'}]
    proof={'model_config':{},'backend':{},'decoder':{'thinking':True},'max_new_tokens':4096,'generation':{'revision':'pinned'},'versions':{}}
    item,summary,natural,controls=run_fixture(tmp_path,'base',42,bank,cb,proof)
    analysis.validate_child(summary,bank,natural,cb,controls,proof,item)
    natural[0]['generation_metadata']['sampling_seed']=43
    with pytest.raises(ValueError,match='identity'):analysis.validate_child(summary,bank,natural,cb,controls,proof,item)
    natural[0]['generation_metadata']['sampling_seed']=(42^int(bank[0]['prompt_sha'][:8],16))&0xffffffff
    natural[0]['response']='<think>x</think>\nB'
    with pytest.raises(ValueError,match='extraction'):analysis.validate_child(summary,bank,natural,cb,controls,proof,item)

def test_runtime_preflight_checks_config_bank_and_tokenization(tmp_path,monkeypatch):
    from belief_transfer.inference import backend
    from belief_transfer.stages import measurements
    j=config.load_job(['+run=ethics_gpu_scoped_readout_base_s42_v1'])
    j=j.model_copy(update={'pilot_bench':j.pilot_bench.model_copy(update={'stance_interface':'explicit_positions'})})
    g=tmp_path/'gen';g.mkdir();bank=[{'fixture':'natural'}];cb=[{'fixture':'control'}]
    write_rows(g/'stance_bank.jsonl',bank);write_rows(g/'control_bank.jsonl',cb);write(g/'token_audit.json',{'lengths':[12,13]})
    proof={'backend':{},'versions':{p:'fixture' for p in ['torch','transformers','vllm']}}
    p={'jobs':[{'arm':'base','seed':42,'run_id':j.run_id,'resolved_config_sha':config.config_sha(j)}],'runtime_evidence':{'base':proof}}
    write(g/'protocol.json',p);monkeypatch.setattr(worker,'registered',lambda:(g,tmp_path/'result'))
    monkeypatch.setattr(config,'load_job',lambda *a,**kw:j);monkeypatch.setattr(worker,'version',lambda *a:'fixture')
    monkeypatch.setattr(backend,'backend_info',lambda **kw:SimpleNamespace(model_dump=lambda:{}))
    monkeypatch.setattr(measurements,'prepare',lambda job:({'stance':bank},{'stance':cb},{}))
    monkeypatch.setattr(measurements,'measurement_bank_fingerprint',lambda bundle:worker.BANK_SHA)
    monkeypatch.setattr(worker,'token_counts',lambda *a:[12,13]);worker.check_runtime()
    monkeypatch.setattr(worker,'token_counts',lambda *a:[12,14])
    with pytest.raises(ValueError,match='tokenizer'):worker.check_runtime()
    monkeypatch.setattr(worker,'token_counts',lambda *a:[12,13]);p['jobs'][0]['resolved_config_sha']='changed';write(g/'protocol.json',p)
    with pytest.raises(ValueError,match='Resolved paired config'):worker.check_runtime()

def test_prepare_refuses_before_generating_when_controls_are_incomplete(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);g=tmp_path/'generated';result=tmp_path/'results'
    monkeypatch.setattr(worker,'registered',lambda:(g,result))
    def refuse():raise ValueError('All five paired interface controls must be complete and passed')
    monkeypatch.setattr(worker,'qualification',refuse)
    with pytest.raises(ValueError,match='All five'):worker.prepare()
    assert not g.exists() and not result.exists() and not (tmp_path/'configs').exists()
