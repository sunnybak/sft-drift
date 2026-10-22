import pytest
from belief_transfer.evals.response_interface_rca import build_bank,VOCABULARIES
from belief_transfer.validation.response_interface_rca import assess
from belief_transfer.metrics.response_interface_rca import summarize

def test_factorial_bank_preserves_truth_under_polarity_and_response_words():
    bank=build_bank();assert len(bank)==256 and len({r['presentation_id'] for r in bank})==256
    for row in bank:
        yes,no=VOCABULARIES[row['vocabulary']]
        truth=row['fact_id'] in ['addition_true','comparison_true','addition_fresh','multiplication_fresh']
        assert row['expected_word']==(yes if truth!=row['negative'] else no)
        assert sorted(row['options'])==sorted([yes,no])
    seed_rows=[r for r in bank if r['fact_id']=='addition_true' and r['representation']=='words' and not r['negative'] and r['order']==0]
    assert len({r['sampling_seed'] for r in seed_rows})==1

def test_new_extractor_does_not_read_reasoning_or_guess_sentence_answers():
    row=build_bank()[0]
    good=assess(row,'<think>reject is not my answer</think>\n'+row['expected_word'],{'finish_reason':'stop'},thinking=True)
    assert good['correct'] and good['strict_format']
    assert not assess(row,'<think>endorse</think>\nI endorse this.',{'finish_reason':'stop'},thinking=True)['correct']
    assert assess(row,'<think>endorse',{'finish_reason':'length'},thinking=True)['error']=='generation_token_limit'
    assert not assess(row,row['expected_word'],{},thinking=False)['correct']

def test_case_normalization_is_not_strict_format_compliance():
    row=build_bank()[0]
    r=assess(row,row['expected_word'].upper(),{'finish_reason':'stop'},thinking=False)
    assert r['correct'] and not r['strict_format']

def test_summary_separates_wrong_valid_words_from_missing_answers():
    bank=build_bank();observed=[{**r,**assess(r,r['expected_word'],{'finish_reason':'stop'},thinking=False)} for r in bank]
    assert summarize(observed)['overall']['development_pass']
    observed[0].update(answer='reject',correct=False,strict_format=True)
    observed[1].update(answer=None,correct=False,strict_format=False,error='generation_token_limit')
    result=summarize(observed)['overall'];assert result['wrong_valid']==1 and result['length_limited']==1 and not result['development_pass']

def test_stage_preserves_backend_failure_and_refuses_overwrite(tmp_path,monkeypatch):
    import asyncio,hashlib,json
    from types import SimpleNamespace
    from belief_transfer.config import load_job
    from belief_transfer.schemas import ResponseInterfaceRCASpec
    from belief_transfer.stages import response_interface_rca as stage
    bank=build_bank();path=tmp_path/'bank.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in bank))
    job=load_job(['+run=ethics_gpu_vllm_base_v1'])
    job=job.model_copy(update={'stage':'response_interface_rca','run_id':'ethics_gpu_response_fixture_v1',
      'response_interface_rca':ResponseInterfaceRCASpec(model_label='fixture',bank_path=str(path),bank_sha256=hashlib.sha256(path.read_bytes()).hexdigest()),
      'pilot_bench':job.pilot_bench.model_copy(update={'measurement_batch_size':128})})
    calls=[]
    class Fake:
        def generate_batch_with_metadata(self,prompts,**kw):
            calls.append(prompts)
            if len(calls)==2:raise RuntimeError('fixture backend failure')
            return [('<think>done</think>\n'+r['expected_word'],{'finish_reason':'stop'}) for r in bank[:len(prompts)]]
    monkeypatch.setattr(stage,'ROOT',tmp_path);monkeypatch.setattr(stage,'require_training_backend',lambda:None)
    monkeypatch.setattr(stage,'backend_info',lambda **kw:SimpleNamespace(model_dump=lambda:{}))
    monkeypatch.setattr(stage,'version',lambda name:'fixture');monkeypatch.setattr(stage,'local_model',lambda *a,**kw:Fake())
    monkeypatch.setattr(stage,'write_result',lambda r:None)
    result=asyncio.run(stage.run(job));folder=tmp_path/'data/results'/job.experiment.id/job.run_id
    saved=[json.loads(l) for l in (folder/'observations.jsonl').read_text().splitlines()]
    assert len(saved)==256 and sum(bool(r['error']) for r in saved)==128
    assert (folder/'observations.md').exists() and not result.metrics['overall']['development_pass']
    with pytest.raises(FileExistsError):asyncio.run(stage.run(job))
