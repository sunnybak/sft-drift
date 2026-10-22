"""Fresh banks and failure preservation; no weights or real experiment writes."""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from belief_transfer.evals.interface_controls import build_bank,contexts,REMINDER
from belief_transfer.evals.measurements import stance_presentation
from belief_transfer.validation.response_interface_rca import assess
import analyze_interface_controls as analysis
import run_interface_controls as worker

def observed(bank):
    result=[]
    for r in bank:
        word=r['expected_word'].upper() if r['interface']=='paired' else r['expected_word']
        text='<think>Reference-based answer.</think>\n'+word;meta={'finish_reason':'stop'}
        result.append({**r,'response':text,'generation_metadata':meta,**assess(r,text,meta,thinking=True)})
    return result

def test_factorial_balance_and_ground_truth_mapping():
    bank=build_bank();cases=contexts()
    assert len(bank)==1152 and len({r['presentation_id'] for r in bank})==1152
    assert Counter(r['interface'] for r in bank)=={'current':384,'explicit':384,'paired':384}
    assert Counter((c.domain,c.split,c.supports_claim) for c in cases)==Counter({(d,s,b):4 for d in ['normative','factual'] for s in ['development','validation'] for b in [True,False]})
    assert len({c.context_id for c in cases})==32
    for r in bank:
        assert r['expected_word'] in r['options']
        assert set(r['support_by_word'].values())=={True,False}
        assert r['support_by_word'][r['expected_word']]==r['supports_claim']
        assert hashlib.sha256(r['prompt'].encode()).hexdigest()==r['prompt_sha256']

def test_existing_templates_reused_and_reminder_is_only_named_change():
    bank=build_bank();lookup={(r['context_id'],r['interface'],r['negative'],r['order'],r['variant']):r for r in bank}
    for r in bank:
        if r['interface']=='paired':
            other=r['claim'] if r['negative'] else r['opposite_statement']
            scope=r['reference']+(' Unrelated note: marker iota.' if r['variant']=='note' else '')
            expected=stance_presentation('fixture',r['target_statement'],other,scope,['agree','disagree'] if r['order']==0 else ['disagree','agree'],interface='explicit_positions')['prompt']
            assert r['prompt']==expected and r['strict_options']==['A','B']
        if r['interface']=='explicit':
            current=lookup[r['context_id'],'current',r['negative'],r['order'],r['variant']]
            assert r['prompt'].replace(REMINDER+'\n','')==current['prompt']

def test_note_rng_matched_and_repeat_independent():
    groups=defaultdict(dict)
    for r in build_bank():groups[r['context_id'],r['interface'],r['negative'],r['order']][r['variant']]=r
    for g in groups.values():
        assert g['plain']['prompt']==g['repeat']['prompt']
        assert g['plain']['sampling_seed']==g['note']['sampling_seed']!=g['repeat']['sampling_seed']

def test_additive_letter_mode_preserves_legacy_and_rejects_prose():
    meta={'finish_reason':'stop'};legacy={'options':['endorse','reject'],'expected_word':'endorse'}
    a=assess(legacy,'<think>x</think>\nEndorse',meta,thinking=True)
    assert a['correct'] and not a['strict_format'] and a['extractor_version']=='response-rca-exact-word-v1'
    row={'options':['a','b'],'strict_options':['A','B'],'expected_word':'a'}
    a=assess(row,'<think>x</think>\nA',meta,thinking=True)
    assert a['correct'] and a['strict_format'] and a['extractor_version']=='response-rca-exact-word-v2'
    assert not assess(row,'<think>x</think>\na',meta,thinking=True)['strict_format']
    assert assess(row,'<think>x</think>\nThe answer is A',meta,thinking=True)['answer'] is None
    assert assess(row,'<think>x</think>\nA',{'finish_reason':'length'},thinking=True)['error']=='generation_token_limit'
    with pytest.raises(ValueError,match='normalize'):assess({**row,'strict_options':['C','D']},'A',meta,thinking=False)

def test_split_checks_canonicalize_order_and_target_mirrors():
    for form in ['current','explicit','paired']:
        rs=observed([r for r in build_bank() if r['interface']==form and r['split']=='development'])
        s=analysis.split_summary(rs)
        assert s['passed'] and s['counts']['expected']==192
        assert s['order_agreement']['disagreements']==0
        assert s['target_mirror_agreement']['disagreements']==0
        assert s['note_comparison']['expected_pairs']==64
        assert all(v['expected_pairs']==32 for v in s['note_by_domain'].values())

def test_domain_accuracy_and_note_failures_cannot_hide_in_aggregate():
    bank=[r for r in build_bank() if r['interface']=='paired' and r['split']=='development'];rs=observed(bank)
    for r in [r for r in rs if r['domain']=='normative'][:5]:
        r['answer']=next(w for w in r['options'] if w!=r['expected_word']);r['correct']=False
    s=analysis.split_summary(rs)
    assert s['counts']['accuracy']>=.95 and not s['checks']['normative_accuracy_at_least_95pct'] and not s['passed']
    rs=observed(bank)
    for r in [r for r in rs if r['domain']=='normative' and r['variant']=='note'][:4]:
        r['answer']=next(w for w in r['options'] if w!=r['expected_word']);r['correct']=False
    s=analysis.split_summary(rs)
    assert s['checks']['normative_accuracy_at_least_95pct'] and not s['checks']['note_flips_at_most_5pct']
    with pytest.raises(ValueError,match='Duplicate'):analysis.split_summary(rs+rs[:1])

def worker_inputs(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);gen=tmp_path/'gen';gen.mkdir();result=tmp_path/'result'
    p={'jobs':[{'arm':'base','run_id':r} for r in ['one','two','three']],'source_bindings':{}}
    (gen/'protocol.json').write_text(json.dumps(p));monkeypatch.setattr(worker,'registered',lambda:(gen,result))
    return gen,result,p

def test_worker_refuses_early_changed_or_started_runs(tmp_path,monkeypatch):
    gen,result,p=worker_inputs(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='Finish the unchanged'):worker.run()
    completed=tmp_path/'data/results/ethical_pilot'/worker.READOUT/'COMPLETED';completed.parent.mkdir(parents=True);completed.write_text('done')
    src=tmp_path/'source';src.write_text('changed');p['source_bindings']={str(src):'wrong'};(gen/'protocol.json').write_text(json.dumps(p))
    with pytest.raises(ValueError,match='Prepared diagnostic source'):worker.run()
    result.mkdir()
    with pytest.raises(FileExistsError,match='cannot resume'):worker.run()

def test_partial_failure_preserved_without_retry(tmp_path,monkeypatch):
    gen,result,p=worker_inputs(tmp_path,monkeypatch)
    completed=tmp_path/'data/results/ethical_pilot'/worker.READOUT/'COMPLETED';completed.parent.mkdir(parents=True);completed.write_text('done')
    calls=[]
    def run(cmd,**kw):
        calls.append(cmd);return SimpleNamespace(returncode=7 if '+run=two' in cmd else 0)
    monkeypatch.setattr(worker.subprocess,'run',run);monkeypatch.setattr(worker.subprocess,'check_output',lambda *a,**kw:'fixture')
    with pytest.raises(RuntimeError,match='two'):worker.run()
    ops=analysis.rows(result/'operations.jsonl')
    assert [o['returncode'] for o in ops]==[0,7] and (result/'operations.md').exists()
    assert (result/'TERMINAL').exists() and (result/'worker_failure.json').exists() and not (result/'COMPLETED').exists()
    assert not any('+run=three' in c for c in calls)
    with pytest.raises(FileExistsError):worker.run()

def test_full_analysis_retains_failure_without_interface_reselection(tmp_path):
    gen=tmp_path/'generated/ethical_pilot'/analysis.MASTER;gen.mkdir(parents=True)
    bank=build_bank();(gen/'bank.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in bank));jobs=[];proofs={}
    for arm in ['base','positive','negative','offtopic','c4_only']:
        jobs.append({'arm':arm,'run_id':arm,'adapter_sha256':None if arm=='base' else 'fixture'})
        proof={'model_config':{},'backend':{},'decoder':{},'generation':{'revision':'pinned'},'versions':{'torch':'fixture'},'max_new_tokens':4096};proofs[arm]=proof
        child=tmp_path/'results/ethical_pilot'/arm;child.mkdir(parents=True);(child/'COMPLETED').write_text('done')
        (child/'bank.jsonl').write_bytes((gen/'bank.jsonl').read_bytes())
        (child/'manifest.json').write_text(json.dumps({**proof,'model_label':arm,'bank_sha256':worker.sha(gen/'bank.jsonl'),'adapter_sha256':jobs[-1]['adapter_sha256']}))
        raw=observed(bank)
        for r in raw:r['generation_metadata'].update(model_revision='pinned',adapter_lora_id=None if arm=='base' else 1,sampling_seed=r['sampling_seed'],execution_versions=proof['versions'])
        if arm=='negative':
            for r in [r for r in raw if r['interface']=='paired' and r['split']=='validation' and r['domain']=='normative'][:5]:
                r['response']='<think>x</think>\n'+next(w for w in r['strict_options'] if w.lower()!=r['expected_word']);r.update(assess(r,r['response'],r['generation_metadata'],thinking=True))
        (child/'observations.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in raw));(child/'summary.json').write_text('{}')
    (gen/'protocol.json').write_text(json.dumps({'jobs':jobs,'runtime_evidence':proofs}))
    report=analysis.analyze(tmp_path)
    assert report['complete'] and len(report['models'])==5 and not report['paired_eligible_for_prospective_readout']
    assert not report['models']['negative']['passed']['paired'] and report['models']['negative']['passed']['explicit']
    with pytest.raises(FileExistsError,match='analysis exists'):analysis.analyze(tmp_path)

def test_prepared_configs_compose_with_bound_weights_and_expected_stage():
    from belief_transfer.config import load_job
    for arm,_,run in worker.run_ids():
        j=load_job(['+run='+run]);b=j.pilot_bench;s=j.response_interface_rca
        assert j.stage=='response_interface_rca' and not j.force and not j.smoke
        assert s.expected_rows==1152 and s.model_label==arm
        assert b.measurement_batch_size==64 and b.seed==42 and b.max_new_tokens==4096
        assert b.measurement_decoding.thinking and b.measurement_decoding.temperature==.6
        assert (b.adapter_path is None)==(arm=='base')
        assert f'ethics_gpu_scope_control_{arm}_v1' in j.related_runs


def test_runtime_preflight_verifies_config_and_token_counts_without_weights(tmp_path,monkeypatch):
    from belief_transfer import config
    from belief_transfer.inference import backend
    j=config.load_job(['+run=ethics_gpu_interface_control_base_v1'])
    gen=tmp_path/'gen';gen.mkdir();(gen/'bank.jsonl').write_text(json.dumps({'expected_input_tokens':12})+'\n')
    proof={'backend':{'backend':'fixture'},'versions':{p:'fixture' for p in ['torch','transformers','vllm']}}
    protocol={'jobs':[{'run_id':j.run_id,'arm':'base','resolved_config_sha':config.config_sha(j)}],'runtime_evidence':{'base':proof}}
    (gen/'protocol.json').write_text(json.dumps(protocol))
    monkeypatch.setattr(worker,'registered',lambda:(gen,tmp_path/'result'))
    monkeypatch.setattr(worker,'version',lambda p:'fixture')
    monkeypatch.setattr(config,'load_job',lambda *a,**kw:j)
    monkeypatch.setattr(backend,'backend_info',lambda **kw:SimpleNamespace(model_dump=lambda:proof['backend']))
    monkeypatch.setattr(worker,'token_counts',lambda *a:[12]);worker.check_runtime()
    monkeypatch.setattr(worker,'token_counts',lambda *a:[13])
    with pytest.raises(ValueError,match='tokenizer/context'):worker.check_runtime()
    protocol['jobs'][0]['resolved_config_sha']='changed';(gen/'protocol.json').write_text(json.dumps(protocol))
    with pytest.raises(ValueError,match='Resolved diagnostic'):worker.check_runtime()
