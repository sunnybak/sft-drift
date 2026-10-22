"""Confirmation gates, raw CUDA identity reconstruction and failure preservation."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from base_reasoning_confirmation_checks import reference_cohort,compare
from base_reasoning_runtime import inspect_retention
import base_reasoning_runtime as runtime
import run_base_reasoning_confirmation as confirmation
import run_base_reasoning_probe as probe
import prepare_base_reasoning_execution as execution
import run_base_reasoning_recovery as recovery
from prepare_base_reasoning_confirmation import generate
from prepare_replay_weight_ablation import write_rows,write_json,sha
from belief_transfer.stages.instruction_retention import observation
from belief_transfer.metrics.instruction_retention import report
from belief_transfer.schemas import InstructionRetentionSpec


def values(kind):
    domains=sorted(runtime_domains(kind))
    return [{'example_id':f'{int(mode)}/{i}','thinking':mode,'family':domains[i%len(domains)] if kind=='retention' else 'decision',
        'operation':domains[i%len(domains)],'prompt':f'Question{i}',
        'expected':('endorse' if (i//4)%2 else 'reject') if kind=='decisions' else '1',
        'negated':bool(i%2),'irrelevant_note':bool(i%3),'response_sha256':'a'*64,
        'value':{'value_correct':True},'native_assessment':{'normal_stop':True,'response_boundaries_valid':True,'strict_format':True}}
        for mode in (True,False) for i in range(128)]


def runtime_domains(kind):
    from base_reasoning_confirmation_checks import FAMILIES,OPERATIONS
    return FAMILIES if kind=='retention' else OPERATIONS


@pytest.mark.parametrize('kind',['retention','decisions'])
def test_exact_95percent_boundary_uses_fixed_base_cohort(kind):
    base=values(kind);candidate=copy.deepcopy(base);cohort=reference_cohort(base,kind)
    for r in candidate[:6]:r['value']['value_correct']=False
    assert compare(candidate,base,cohort,kind)['passed']
    candidate[6]['value']['value_correct']=False
    assert not compare(candidate,base,cohort,kind)['passed']


@pytest.mark.parametrize('kind',['retention','decisions'])
def test_missing_is_unknown_and_not_neutral_or_silently_excluded(kind):
    base=values(kind);candidate=copy.deepcopy(base)
    candidate[0]['value']['value_correct']=None
    candidate[0]['native_assessment']['normal_stop']=False
    result=compare(candidate,base,reference_cohort(base,kind),kind)['by_mode']['True']
    assert result['full_n']==128 and result['full_unscorable']==1 and result['full_wrong']==0
    assert result['known_accuracy'] is None and result['known_missing_bounds']==[127/128,1]
    assert not result['passed']


@pytest.mark.parametrize('defect',['missing','mask','prompt','mode','value_type'])
def test_incomplete_or_changed_pairs_masks_and_values_rejected(defect):
    base=values('decisions');candidate=copy.deepcopy(base);cohort=reference_cohort(base,'decisions')
    if defect=='missing':candidate.pop()
    if defect=='mask':cohort['known'].pop()
    if defect=='prompt':candidate[0]['prompt']='changed'
    if defect=='mode':candidate[0]['thinking']=False
    if defect=='value_type':candidate[0]['value']['value_correct']=1
    with pytest.raises(ValueError):compare(candidate,base,cohort,'decisions')


def test_base_insufficiency_is_retained_and_cannot_pass_with_perfect_candidate():
    base=values('decisions');candidate=copy.deepcopy(base)
    for r in base[:40]:r['value']['value_correct']=False
    cohort=reference_cohort(base,'decisions')
    assert not cohort['usable'] and not compare(candidate,base,cohort,'decisions')['passed']
    base=values('decisions');base[0]['native_assessment']['normal_stop']=False
    assert not reference_cohort(base,'decisions')['usable']


class Tokenizer:
    eos_token_id=999
    def encode(self,text,**kwargs):return list(text.encode())
    def decode(self,tokens,**kwargs):return bytes(tokens).decode()


@pytest.mark.parametrize('adapter',[False,True])
@pytest.mark.parametrize('defect',[None,'seed','generation_count','bank_hash','summary','truncation'])
def test_retention_reconstructs_actual_records_and_preserves_truncation(tmp_path,defect,adapter):
    bank=generate()['retention_0'];t=Tokenizer();raw=[]
    expected={'model':{},'backend':{},'generation':{'revision':'pinned'},'decoding':{},
              'max_new_tokens':4096,'batch_size':32,'versions':{'vllm':'pinned'}}
    for i,r in enumerate(bank):
        r['expected_input_token_ids']=t.encode(r['prompt'])
        text='<think>\nCheck.\n</think>\n\n'+r['expected'] if r['thinking'] else r['expected']
        tokens=t.encode(text)+[999]
        if defect=='truncation' and i==0:tokens.pop()
        meta={'input_token_ids':r['expected_input_token_ids'],'sampling_seed':r['seed'],'model_revision':'pinned',
            'adapter_lora_id':1 if adapter else None,'output_token_ids':tokens,'generation_tokens':len(tokens),'prompt_tokens':len(r['expected_input_token_ids']),
            'finish_reason':'length' if defect=='truncation' and i==0 else 'stop',
            'execution':expected['generation'],'execution_versions':expected['versions']}
        raw.append(observation(r,(text,meta),t,evaluation=42,revision='pinned',adapter=adapter))
    summary,known=report(raw,bank,None)
    write_rows(tmp_path/'bank.jsonl',bank);write_rows(tmp_path/'known_items.jsonl',known)
    if defect=='seed':raw[0]['generation_metadata']['sampling_seed']+=1
    if defect=='generation_count':raw[0]['generation_metadata']['generation_tokens']+=1
    write_rows(tmp_path/'responses.jsonl',raw)
    adapter_sha='a'*64 if adapter else None
    spec=InstructionRetentionSpec(model_label='candidate' if adapter else 'base',bank_path='bank.jsonl',
        bank_sha256=sha(tmp_path/'bank.jsonl'),adapter_sha256=adapter_sha,eval_seeds=[42],
        fresh_base_reference=not adapter,known_path='known_items.jsonl' if adapter else None,
        known_sha256=sha(tmp_path/'known_items.jsonl') if adapter else None)
    serialized=spec.model_dump()
    assert ('fresh_base_reference' not in serialized) if adapter else serialized['fresh_base_reference']
    write_json(tmp_path/'manifest.json',expected|{'bank_sha256':'wrong' if defect=='bank_hash' else sha(tmp_path/'bank.jsonl'),
        'adapter_sha256':adapter_sha,'known_sha256':spec.known_sha256,'evaluation':serialized})
    write_json(tmp_path/'summary.json',{'by_seed':{'42':{} if defect=='summary' else summary}})
    (tmp_path/'COMPLETED').write_text('complete')
    if defect in (None,'truncation'):
        result=inspect_retention(tmp_path,bank,expected,adapter_sha,t)
        assert len(result)==128
        if defect=='truncation':assert result[0]['value']['value_correct'] is None
    else:
        with pytest.raises(ValueError):inspect_retention(tmp_path,bank,expected,adapter_sha,t)


def test_technical_child_failure_keeps_dispatch_and_refuses_overwrite(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);(tmp_path/'configs/run').mkdir(parents=True)
    bank=tmp_path/'bank.jsonl';write_rows(bank,[]);parent=tmp_path/'parent';parent.mkdir()
    monkeypatch.setattr(runtime,'load_job',lambda _:object());monkeypatch.setattr(runtime,'config_sha',lambda _:'config')
    monkeypatch.setattr(runtime,'commit',lambda:'source');monkeypatch.setattr(runtime,'execute',lambda *args:False)
    binding={'adapter_path':None,'adapter_file_sha256':None}
    with pytest.raises(RuntimeError):runtime.collect('fresh','base',bank,'retention',binding,{},None,parent)
    assert (parent/'fresh_dispatch.json').exists() and (tmp_path/'configs/run/fresh.yaml').exists()
    with pytest.raises(FileExistsError):runtime.collect('fresh','base',bank,'retention',binding,{},None,parent)


@pytest.mark.parametrize('defect',[None,'not_passed','mechanical','hash','review_missing'])
def test_confirmation_requires_privately_preserved_full_review_and_mechanical_pass(tmp_path,monkeypatch,defect):
    write_json(tmp_path/'comparison_v1.json',{'development_passed':defect!='mechanical'})
    write_rows(tmp_path/'agent_review_v1.jsonl',[])
    gate={'passed':defect!='not_passed','full_response_review_complete':defect!='review_missing',
          'comparison_sha256':sha(tmp_path/'comparison_v1.json'),'review_sha256':sha(tmp_path/'agent_review_v1.jsonl')}
    if defect=='hash':gate['review_sha256']='wrong'
    write_json(tmp_path/'reviewed_development_v1.json',gate)
    preserved=[];monkeypatch.setattr(confirmation,'preserved',lambda p:preserved.append(p))
    if defect:
        with pytest.raises(ValueError):confirmation.reviewed_development(tmp_path)
        assert not preserved
    else:
        assert confirmation.reviewed_development(tmp_path)==gate and len(preserved)==3


@pytest.mark.parametrize('defect',[None,'weights','config','step'])
def test_saved_checkpoint_binding_and_alias_require_both_exact_byte_hashes(tmp_path,defect):
    write_json(tmp_path/'trainer_state.json',{'global_step':226 if defect=='step' else 227})
    (tmp_path/'adapter_model.safetensors').write_bytes(b'weights')
    (tmp_path/'adapter_config.json').write_bytes(b'config')
    final={'training_summary_sha256':'summary','completed_marker_sha256':'done','training_checks':{'reload':True},
           'adapter_file_sha256':sha(tmp_path/'adapter_model.safetensors'),
           'adapter_config_sha256':sha(tmp_path/'adapter_config.json'),'adapter_tensor_sha256':'FINAL_ONLY'}
    if defect=='step':
        with pytest.raises(ValueError):probe.checkpoint_binding(tmp_path,227,final)
        return
    binding=probe.checkpoint_binding(tmp_path,227,final)
    assert 'adapter_tensor_sha256' not in binding
    if defect=='weights':final['adapter_file_sha256']='other'
    if defect=='config':final['adapter_config_sha256']='other'
    assert probe.terminal_alias(binding,final)==(defect is None)


@pytest.mark.parametrize('defect',[None,'initial','schedule'])
def test_actual_initial_adapter_and_lr_trace_must_match_parent(defect):
    parent={'initial_adapter_sha256':'initial','log_history':[{'step':1,'learning_rate':0},{'step':2,'learning_rate':.001}]}
    candidate=copy.deepcopy(parent)
    if defect=='initial':candidate['initial_adapter_sha256']='other'
    if defect=='schedule':candidate['log_history'][1]['learning_rate']=.002
    if defect:
        with pytest.raises(ValueError):probe.verify_schedule(candidate,parent,'initial')
    else:probe.verify_schedule(candidate,parent,'initial')


def surface():
    return {'development_passed':True,'validation_passed':True,'actual_coverage':{'recorded':2400,'valid':2400,
        'fresh_controls':{'stance':{'factual':{'n_expected':16,'n_extracted':16,'n_correct':16},
            'factual_null':{'n_expected':16,'n_extracted':16,'n_correct':16},
            'factual_null_comparison':{'n_eligible_pairs':16,'flip_rate':0}}}}}


@pytest.mark.parametrize('defect',[None,'validation','invalid','missing_control','wrong_control','note_flip','runtime'])
def test_final_surface_gate_keeps_coverage_controls_and_runtime_separate(defect):
    status=surface();audit={'records':2432,'passed':True}
    if defect=='validation':status['validation_passed']=False
    if defect=='invalid':status['actual_coverage']['valid']=2399
    if defect=='missing_control':status['actual_coverage']['fresh_controls']['stance']['factual']['n_extracted']=15
    if defect=='wrong_control':status['actual_coverage']['fresh_controls']['stance']['factual']['n_correct']=14
    if defect=='note_flip':status['actual_coverage']['fresh_controls']['stance']['factual_null_comparison']['flip_rate']=1/16
    if defect=='runtime':audit['passed']=False
    assert probe.surface_passed(status,audit)==(defect is None)


def test_all_checkpoint_phases_registered_and_started_outputs_refused(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths=execution.required_paths()
    assert len(paths)==54 and len(set(paths))==54
    probe.preflight_outputs()
    name=execution.eval_id('midpoint','unqualified')
    Path('data/results/ethical_pilot',name).mkdir(parents=True)
    with pytest.raises(FileExistsError):probe.preflight_outputs()


@pytest.mark.parametrize('reuse',[False,True])
def test_scientific_failure_still_collects_full_surface(tmp_path,monkeypatch,reuse):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(probe,'RESULTS',tmp_path/'parent');probe.RESULTS.mkdir()
    # Inputs are explicit mocked data; neither real artifacts nor weights are read.
    base={'retention':[],'decisions':{c:[] for c in probe.CELLS}}
    refs={k:copy.deepcopy(base) for k in ('base','control','parent')}
    monkeypatch.setattr(probe,'value_known',lambda _:[])
    calls=[]
    def collect(*a,**kw):calls.append(a[0]);return []
    monkeypatch.setattr(probe,'collect',collect)
    reused=[{'example_id':str(i),'value':{'value_correct':True},
             'native_assessment':{'strict_format':True}} for i in range(128)]
    monkeypatch.setattr(probe,'rows',lambda _:reused if reuse else [])
    monkeypatch.setattr(probe.previous,'summarize_values',lambda *a:{'passed':False})
    monkeypatch.setattr(probe.previous,'decision_known',lambda _:[])
    monkeypatch.setattr(probe.previous,'compare_decisions',lambda *a:{'passed':False})
    monkeypatch.setattr(probe,'paired_values',lambda *a,**kw:({},[]))
    measured=[]
    def full(protocol,binding,parent,identify):
        measured.append(identify('unqualified'))
        status=surface();status['development_passed']=False;status['stance_run_id']=identify('unqualified')
        write_json(parent/'candidate_measurement_status.json',status)
    monkeypatch.setattr(probe.previous,'full_surface',full)
    monkeypatch.setattr(probe,'load_job',lambda _:type('Job',(),{'pilot_bench':None})())
    monkeypatch.setattr(probe,'audit_surface',lambda *a:{'records':2432,'passed':True})
    protocol={'bank_path':'bank','runtime_reference':{},'references':{'base':{'retention':{'run_id':'base'}}}}
    result=probe.measure('midpoint',{},protocol,refs,None,reused_retention=reused if reuse else None)
    assert measured==[execution.eval_id('midpoint','unqualified')] and not result['development_passed']
    assert len(calls)==(4 if reuse else 5)
    assert (execution.measure_id('midpoint','retention') in calls) is not reuse


def test_recovery_rebinds_only_reviewed_collector_repairs_and_not_measurement_sources(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths=[*sorted(recovery.REPAIRED),'src/frozen_scorer.py','data/raw.jsonl','data/raw.md']
    for name in paths:
        p=Path(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_text('original')
    before={n:sha(Path(n)) for n in paths}
    for name in recovery.REPAIRED:Path(name).write_text('repaired')
    Path('data/raw.md').write_text('regenerated derived view')
    sources,changes,views=recovery.rebound_sources(before)
    assert {c['path'] for c in changes}==recovery.REPAIRED
    assert views==['data/raw.md'] and sources['data/raw.jsonl']==before['data/raw.jsonl']
    Path('src/frozen_scorer.py').write_text('changed metric')
    with pytest.raises(ValueError):recovery.rebound_sources(before)


def test_recovery_does_not_accept_changed_raw_data_as_derived_view_refresh(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths=[*sorted(recovery.REPAIRED),'data/raw.jsonl','data/raw.md']
    for name in paths:
        p=Path(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_text('original')
    before={n:sha(Path(n)) for n in paths}
    for name in recovery.REPAIRED:Path(name).write_text('repaired')
    Path('data/raw.jsonl').write_text('changed replies')
    with pytest.raises(ValueError):recovery.rebound_sources(before)


def test_recovery_refuses_started_children_but_allows_its_exact_completed_reuse(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);monkeypatch.setattr(recovery,'RESULTS',tmp_path/'fresh')
    Path('data/results/ethical_pilot',recovery.CHILD).mkdir(parents=True)
    recovery.fresh_outputs()
    Path('data/results/ethical_pilot',execution.measure_id('final','retention')).mkdir()
    with pytest.raises(FileExistsError):recovery.fresh_outputs()
