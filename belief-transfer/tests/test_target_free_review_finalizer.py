"""Review coverage/provenance checks on synthetic temporary results only."""
import hashlib
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from finalize_target_free_review_v2 import ARMS,SEEDS,MASTER,finalize


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value)+'\n')
def jsonl(path,values):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(v)+'\n' for v in values))

@pytest.fixture
def study(tmp_path):
    folder=tmp_path/'data/results/ethical_pilot'/MASTER;folder.mkdir(parents=True)
    selected=[];natural_reviews=[];failures=[];control_reviews=[];sources=[]
    rel=lambda p:str(p.relative_to(tmp_path))
    for arm in ARMS:
        for seed in SEEDS:
            child=folder.parent/f'ethics_gpu_target_free_readout_{arm}_s{seed}_v2'
            natural=[{'presentation_id':f'n{i}','prompt_sha':'a'*64,'response':'<think>Position A.</think> A','answer':'agree','strict_format':True,'generation_metadata':{'finish_reason':'stop'},'error':None} for i in range(1200)]
            controls=[{'presentation_id':f'c{i}','response':'<think>Position A.</think> A','answer':'agree','expected':'agree','strict_format':True,'generation_metadata':{'finish_reason':'stop'},'error':None} for i in range(488)]
            if (arm,seed)==('base',42):controls[0]['answer']='disagree'
            for name,records in [('stance_observations.jsonl',natural),('stance_controls.jsonl',controls)]:
                path=child/name;jsonl(path,records);sources.append({'path':rel(path),'sha256':sha(path)})
            if seed==42 or (arm,seed)==('base',7):
                path=child/'stance_observations.jsonl'
                for row in natural[:12]:
                    item={'arm':arm,'seed':seed,'presentation_id':row['presentation_id']};selected.append(item)
                    natural_reviews.append({**item,'review_mode':'entire_raw_response_agent_read','source_path':rel(path),'source_sha256':sha(path),'response_sha256':hashlib.sha256(row['response'].encode()).hexdigest(),'prompt_sha':row['prompt_sha'],'canonical_choice':row['answer'],'last_settled_rationale_final_alignment':'aligned','scope_assessment':'no_clear_scope_change','agent_note':'Synthetic declared reading, used only to test validation.'})
            if (arm,seed)==('base',42):
                row=controls[0];path=child/'stance_controls.jsonl';failures.append({'arm':arm,'seed':seed,'observation':row,'error_codes':['CONTROL_WRONG_FINAL']})
                control_reviews.append({'arm':arm,'seed':seed,'presentation_id':row['presentation_id'],'review_mode':'entire_raw_response_agent_read','source_path':rel(path),'source_sha256':sha(path),'response_sha256':hashlib.sha256(row['response'].encode()).hexdigest(),'original_expected':row['expected'],'original_answer':row['answer'],'original_error_codes':['CONTROL_WRONG_FINAL'],'original_grade_unchanged':True,'agent_error_class':'synthetic_mismatch','agent_note':'Synthetic declared reading.'})
    generated=tmp_path/'data/generated/ethical_pilot'/MASTER
    selection=generated/'review_selection.jsonl';jsonl(selection,selected)
    dump(generated/'protocol.json',{'source_bindings':{rel(selection):sha(selection)}})
    dump(folder/'analysis.json',{'complete':True,'pending':[],'policy_id':'target_free_error_budget_v2','models':{a:{'complete_seeds':True,'seeds':{str(s):{} for s in SEEDS}} for a in ARMS},'sources':sources})
    jsonl(folder/'control_failures.jsonl',failures);jsonl(folder/'synthetic_preselected_review.jsonl',natural_reviews);jsonl(folder/'synthetic_control_review.jsonl',control_reviews)
    (folder/'COMPLETED').write_text('Complete\n')
    return tmp_path,folder


def test_complete_review_binds_exact_selection_and_all_failures_without_rescoring(study):
    root,folder=study;before=(folder/'analysis.json').read_bytes();r=finalize(root)
    assert r['preselected_reviewed']==72 and r['reviewed_jobs']==15
    assert r['failed_controls_reviewed']==r['failed_controls_expected']==1
    assert not r['semantic_clearance']
    assert (folder/'analysis.json').read_bytes()==before
    for name in ('reviewed_natural','reviewed_failed_controls'):
        assert (folder/(name+'.jsonl')).exists() and (folder/(name+'.md')).exists()
    assert (folder/'reviewed_assessment.md').exists()
    with pytest.raises(FileExistsError,match='no overwrite'):finalize(root)


def test_missing_failure_review_does_not_create_false_completion(study):
    root,folder=study;(folder/'synthetic_control_review.jsonl').write_text('')
    with pytest.raises(ValueError,match='Failed-control review coverage'):finalize(root)
    assert not (folder/'reviewed_assessment.json').exists()


def test_source_and_annotation_tampering_are_rejected(study):
    root,folder=study;p=folder/'synthetic_preselected_review.jsonl';items=[json.loads(x) for x in p.read_text().splitlines()];items[0]['response_sha256']='f'*64;jsonl(p,items)
    with pytest.raises(ValueError,match='response hash'):finalize(root)
    assert not (folder/'reviewed_assessment.json').exists()


def test_partial_sweep_and_changed_frozen_selection_are_rejected(study):
    root,folder=study;(folder/'COMPLETED').unlink()
    with pytest.raises(ValueError,match='terminal'):finalize(root)
    (folder/'COMPLETED').write_text('Complete\n')
    p=root/'data/generated/ethical_pilot'/MASTER/'review_selection.jsonl';p.write_text(p.read_text()+'\n')
    with pytest.raises(ValueError,match='Frozen review selection changed'):finalize(root)


def test_modified_raw_sources_and_duplicate_reviews_are_rejected(study):
    root,folder=study;p=folder.parent/'ethics_gpu_target_free_readout_base_s42_v2/stance_controls.jsonl';old=p.read_bytes();p.write_bytes(old+b'\n')
    with pytest.raises(ValueError,match='Analysis source changed'):finalize(root)
    p.write_bytes(old)
    p=folder/'synthetic_preselected_review.jsonl';lines=p.read_text().splitlines();lines[0]=lines[1];p.write_text('\n'.join(lines)+'\n')
    with pytest.raises(ValueError,match='Preselected review coverage'):finalize(root)
