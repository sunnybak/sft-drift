import pytest

from belief_transfer.config import load_job
from belief_transfer.evals.conviction_scale import build_scale_bank, extract_scale, balanced_fields, joint_completions, reflection_prompt
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.metrics.conviction_scale import summarize_scale, summarize_joint_probabilities
from belief_transfer.schemas import ConvictionScaleStudy, PilotWording
from belief_transfer.stages.conviction_study import prepare_scale
from belief_transfer.evals.conviction_replay import verify_scale_observation


@pytest.fixture
def design():
    return load_job(['+run=conviction_scale_development_v1']).pilot_bench.conviction_scale_study


def small_bank(design):
    spec=design.model_copy(update={'belief_ids':['a','b']})
    wordings=[PilotWording(belief_id=b,wording_id=w,statement='A proposition.',negation='It is not the case that a proposition.',scope='Fixed scope.')
              for b in spec.belief_ids for w in spec.wording_ids]
    return spec,build_scale_bank(spec,wordings)


def answered(bank):
    return [{**r,'answer':r.get('expected', 'equal' if r['candidate']=='paired' else 2), 'strict_format':True} for r in bank]


def test_reverse_keying():
    assert extract_scale('0','remaining_doubt')==(4,True)
    assert extract_scale('4','settledness')==(4,True)
    assert extract_scale('2. Significant doubt remains.','settledness')==(2,False)
    assert extract_scale('LEFT','paired')==('left',False)
    assert extract_scale('unresolved','named_settledness')==(0,True)
    assert extract_scale('settled','named_settledness')==(4,True)
    assert extract_scale('There is a slight preference with substantial doubt.\nFINAL: slight','reasoned_named')==(1,True)
    assert extract_scale('Mentioned moderate, but no final field.','reasoned_named')==(None,False)
    assert extract_scale('FINAL: slight\nFINAL: settled','reasoned_named')==(None,False)
    for bad in ('14','0.5','five','I think 3','',None):
        assert extract_scale(bad,'settledness')[0] is None


def test_frozen_bank_and_ordinal_controls(design):
    job=load_job(['+run=conviction_scale_development_v1'])
    bank,manifest=prepare_scale(job)
    assert len(bank)==512
    assert len({r['presentation_id'] for r in bank})==512
    assert len({r['prompt_sha'] for r in bank})==512
    assert manifest['decoding']['thinking'] is False
    assert all('described speaker' not in r['prompt'] for r in bank if r['kind']=='natural')


def test_controls_recover_every_level(design):
    spec,bank=small_bank(design)
    scores=summarize_scale(bank,answered(bank),spec.model_dump())
    for c,v in scores.items():
        assert v['controls_passed']
        assert v['natural_stability_passed']
        assert all(k['accuracy']==1 for k in v['controls_by_level'].values())
    assert scores['settledness']['profile']['a']['distribution']['2']==16


def test_constant_top_fails_controls(design):
    spec,bank=small_bank(design)
    rows=[{**r,'answer':'left' if r['candidate']=='paired' else 4,'strict_format':True} for r in bank]
    assert all(not v['controls_passed'] for v in summarize_scale(bank,rows,spec.model_dump()).values())


def test_position_bias_fails_pair_checks(design):
    spec,bank=small_bank(design)
    rows=answered(bank)
    for r in rows:
        if r['candidate']=='paired' and r['kind']=='natural':r['answer']='left'
    q=summarize_scale(bank,rows,spec.model_dump())['paired']
    assert q['natural_stability']['arrangement']['exact_agreement']==0
    assert not q['natural_stability_passed']


def test_missing_or_duplicate_cannot_score(design):
    spec,bank=small_bank(design);rows=answered(bank)
    for bad in (rows[:-1],rows+[rows[0]]):
        with pytest.raises(ValueError):summarize_scale(bank,bad,spec.model_dump())


def test_invalid_is_not_unresolved(design):
    spec,bank=small_bank(design);rows=answered(bank)
    for r in rows:
        if r['candidate']=='settledness' and r['kind']=='natural':r['answer']=None
    q=summarize_scale(bank,rows,spec.model_dump())['settledness']
    assert q['profile']['a']['n_valid']==0
    assert q['profile']['a']['distribution']['0']==0
    assert not q['natural_stability_passed']


def test_validation_requires_frozen_development(design):
    data=design.model_dump();data['phase']='validation'
    with pytest.raises(ValueError):ConvictionScaleStudy.model_validate(data)


def test_sampling_is_explicit_and_legacy_manifests_unchanged():
    legacy=load_job(['+run=conviction_scale_development_v1'])
    _,manifest=prepare_scale(legacy)
    assert 'temperature' not in manifest['study']
    assert manifest['decoding']['temperature']==0
    sampled=load_job(['+run=conviction_scale_sampling_screen_v1'])
    bank,manifest=prepare_scale(sampled)
    assert len(bank)==54 and 'smoke' in manifest
    assert manifest['decoding']['temperature']==.6
    assert manifest['decoding']['top_p']==.95
    assert manifest['decoding']['top_k']==20
    assert manifest['decoding']['min_p']==0
    missing=sampled.pilot_bench.conviction_scale_study.model_dump();missing['top_k']=None
    with pytest.raises(ValueError):ConvictionScaleStudy.model_validate(missing)


def test_sampling_settings_reach_both_local_backends(monkeypatch):
    import sys
    from types import ModuleType,SimpleNamespace
    from belief_transfer.inference import model as hf
    from belief_transfer.inference.mlx_model import MLXModel
    job=load_job(['+run=conviction_scale_sampling_screen_v1'])
    kwargs={'top_p':.95,'top_k':20,'min_p':0.0,'batch_size':1}
    local=hf.HFModel('qwen3-4b',job.models,**kwargs)
    local._ensure_loaded=lambda:None
    captured=[]
    monkeypatch.setattr(hf,'batched_chat_generate',lambda *a,**kw:captured.append(kw) or ['moderate'])
    assert local.generate(['a'],temperature=.6)==['moderate']
    assert all(captured[0][k]==v for k,v in kwargs.items())
    seed_calls=[];sampler_calls=[]
    fake_core=ModuleType('mlx.core');fake_core.random=SimpleNamespace(seed=seed_calls.append)
    fake_parent=ModuleType('mlx');fake_parent.core=fake_core
    fake_lm=ModuleType('mlx_lm')
    fake_lm.stream_generate=lambda *a,**kw:iter([SimpleNamespace(text='moderate',finish_reason='stop',prompt_tokens=10,generation_tokens=1)])
    fake_utils=ModuleType('mlx_lm.sample_utils')
    fake_utils.make_sampler=lambda **kw:sampler_calls.append(kw) or 'sampler'
    monkeypatch.setitem(sys.modules,'mlx.core',fake_core)
    monkeypatch.setitem(sys.modules,'mlx',fake_parent)
    monkeypatch.setitem(sys.modules,'mlx_lm',fake_lm)
    monkeypatch.setitem(sys.modules,'mlx_lm.sample_utils',fake_utils)
    mlx=MLXModel('qwen3-4b',job.models,seed=123,**kwargs)
    mlx._ensure_loaded=lambda:None;mlx._prompt_text=lambda _: 'prompt'
    assert mlx.generate(['a'],temperature=.6)==['moderate']
    assert sampler_calls==[{'temp':.6,'top_p':.95,'top_k':20,'min_p':0.0}]
    assert seed_calls==[123]


def test_atomic_recovery_and_nonmonotone_profiles():
    job=load_job(['+run=conviction_scale_development_v3']);bank,_=prepare_scale(job)
    assert len(bank)==704
    assert extract_scale('no','atomic')==(0,True)
    assert extract_scale('yes','atomic')==(1,True)
    rows=[{**r,'answer':r.get('expected',int(r.get('threshold',1)<=3)),'strict_format':True} for r in bank]
    spec=job.pilot_bench.conviction_scale_study.model_dump()
    q=summarize_scale(bank,rows,spec)['atomic']
    assert q['controls_passed'] and q['natural_stability_passed']
    assert q['nonmonotone_profiles']==0
    assert all(v['distribution']['3']==16 for v in q['profile'].values())
    # Yes to a stronger item after no to a weaker one is not coded as unresolved.
    for r in rows:
        if r['kind']=='natural' and r['threshold']==1:r['answer']=0
    q=summarize_scale(bank,rows,spec)['atomic']
    assert q['nonmonotone_profiles']==96
    assert all(v['n_valid']==0 and v['distribution']['0']==0 for v in q['profile'].values())
    assert not q['natural_stability_passed']


def test_balanced_parser_and_semantic_conflict():
    assert extract_scale('{"position":"second","conviction":"settled"}','balanced_named')==(4,True)
    assert extract_scale('{"position":"neither","conviction":"unresolved"}','balanced_named')==(0,True)
    assert extract_scale('{"position":"first","conviction":"unresolved"}','balanced_named')==(None,True)
    assert extract_scale('```json\n{"position":"first","conviction":"moderate"}\n```','balanced_named')==(2,False)
    assert balanced_fields('{"position":"first","position":"second","conviction":"clear"}')==(None,None,False)
    assert extract_scale('{"position":"oppose","conviction":"settled"}','verdict_named')==(4,True)
    assert extract_scale('{"position":"oppose","conviction":"unresolved"}','verdict_named')==(None,True)
    assert extract_scale('{"position":"no_lean","conviction":"unresolved"}','verdict_named')==(0,True)


def test_semantic_verdict_has_false_fact_high_conviction_control():
    job=load_job(['+run=conviction_scale_verdict_fast_screen_v1'])
    bank,_=prepare_scale(job)
    assert len(bank)==62
    known=[r for r in bank if r.get('self_check_id')=='integer_addition']
    assert {r['expected_position'] for r in known}=={'favor','oppose'}
    assert all(r['expected']==4 for r in known)
    rows=[]
    for r in bank:
        value=r.get('expected',2)
        position=r.get('expected_position','favor' if r.get('polarity')=='positive' else 'oppose')
        rows.append({**r,'answer':value,'chosen_position':position,'judgment_coherent':True,'strict_format':True})
    s=summarize_scale(bank,rows,job.pilot_bench.conviction_scale_study.model_dump())['verdict_named']
    assert s['controls_passed']
    assert s['chosen_position_stability']['polarity']['exact_agreement']==1


def test_joint_soft_readout_does_not_hide_incoherent_mass():
    choices=joint_completions();probabilities={k:1/15 for k in choices}
    scores=summarize_joint_probabilities(probabilities)
    assert scores['logical_valid_mass']==pytest.approx(9/15)
    assert scores['invalid_mass']==pytest.approx(6/15)
    assert scores['expected_ordinal_valid']==pytest.approx(20/9)
    with pytest.raises(ValueError):summarize_joint_probabilities(dict(list(probabilities.items())[:-1]))


def test_balanced_choice_coordinates_and_grade_independence():
    job=load_job(['+run=conviction_scale_balanced_screen_v1'])
    bank,_=prepare_scale(job)
    assert len(bank)==62
    for level in range(1,5):
        assert {r['expected_position'] for r in bank if r['kind']=='comprehension' and r['level']==level}=={'first','second'}
    rows=[]
    for r in bank:
        value=r.get('expected',2)
        position=r.get('expected_position','first' if r.get('position_order')==0 else 'second')
        rows.append({**r,'answer':value,'chosen_position':position,'judgment_coherent':True,'strict_format':True})
    s=summarize_scale(bank,rows,job.pilot_bench.conviction_scale_study.model_dump())['balanced_named']
    assert s['controls_passed']
    assert s['controls']['self_check']['n_correct']==8
    assert s['natural_stability']['position_order']['exact_agreement']==1
    assert s['chosen_position_stability']['position_order']['exact_agreement']==1
    for r in rows:
        if r['kind']=='natural':r['chosen_position']='first'
    s=summarize_scale(bank,rows,job.pilot_bench.conviction_scale_study.model_dump())['balanced_named']
    assert s['chosen_position_stability']['position_order']['exact_agreement']==0
    assert not s['natural_stability_passed']


def test_ordinal_contract_allows_one_level_but_retains_exact_and_stance_diagnostics():
    job=load_job(['+run=conviction_scale_verdict_development_openai_v1'])
    bank,_=prepare_scale(job)
    rows=[{**r,'answer':r.get('expected',2),'chosen_position':r.get('expected_position','favor'),
           'judgment_coherent':True,'strict_format':True} for r in bank]
    # One one-level discrepancy is small; unanimous favor across complementary
    # propositions remains a visible direction failure, not a confidence gate.
    natural=next(r for r in rows if r['kind']=='natural')
    natural['answer']=3
    spec=job.pilot_bench.conviction_scale_study.model_dump()
    old=summarize_scale(bank,rows,spec)['verdict_named']
    assert not old['natural_stability_passed']
    ordinal={**spec,'qualification_mode':'ordinal-reported-v1','maximum_normalized_gap':.25}
    result=summarize_scale(bank,rows,ordinal)['verdict_named']
    assert result['controls_passed'] and result['natural_stability_passed']
    assert result['chosen_position_stability']['polarity']['exact_agreement']==0
    assert 'maximum_normalized_gap' not in old['natural_stability']['polarity']
    natural['answer']=4
    result=summarize_scale(bank,rows,ordinal)['verdict_named']
    assert not result['natural_stability_passed']
    assert result['natural_stability']['polarity']['maximum_normalized_gap']==.5


def test_reflection_replay_keeps_incoherence_separate_from_format():
    judgment='{"position":"disagree","reason":"The claim is false."}'
    prompt=reflection_prompt('Frozen prompt.',judgment)
    row={'candidate':'conditioned_named','prompt':'Frozen prompt.','judgment_response':judgment,
         'response':'unresolved','answer':None,'strict_format':True,'chosen_position':'disagree',
         'judgment_coherent':False,'administered_prompt':prompt,'administered_prompt_sha':fingerprint(prompt)}
    manifest={'decoding':{},'study':{}}
    verify_scale_observation(row,manifest)
    with pytest.raises(ValueError):verify_scale_observation({**row,'answer':0},manifest)
    with pytest.raises(ValueError):verify_scale_observation({**row,'administered_prompt':prompt+'extra'},manifest)
    # A compulsory guess may lack a genuine lean; this does not make the
    # guess itself a strong judgment.
    forced={'decoding':{},'study':{'force_preliminary_binary':True}}
    verify_scale_observation({**row,'answer':0,'judgment_coherent':True},forced)


def test_likelihood_replay_checks_all_pairs_and_reduction():
    from belief_transfer.schemas import ChoiceScores,ChoiceScore
    scores=ChoiceScores(prompt='Chat wrapper: Frozen prompt.',scores=[
        ChoiceScore(choice=c,logprob=-10,logprob_per_token=-1,n_tokens=10) for c in joint_completions()])
    probabilities=scores.probabilities(per_token=False)
    row={'candidate':'verdict_named','prompt':'Frozen prompt.','response':'{"position":"oppose","conviction":"settled"}',
         'answer':4,'strict_format':True,'chosen_position':'oppose','judgment_coherent':True,
         'joint_choice_scores':scores.model_dump(),'joint_probabilities':probabilities,
         'likelihood_diagnostic':summarize_joint_probabilities(probabilities)}
    manifest={'decoding':{},'study':{}}
    verify_scale_observation(row,manifest)
    with pytest.raises(ValueError):verify_scale_observation({**row,'likelihood_diagnostic':{}},manifest)
    corrupt={**scores.model_dump(),'scores':scores.model_dump()['scores'][:-1]}
    with pytest.raises(ValueError):verify_scale_observation({**row,'joint_choice_scores':corrupt},manifest)


def test_validation_cannot_change_candidate_or_use_failed_development(tmp_path,monkeypatch):
    import json
    import shutil
    from belief_transfer.stages import conviction_study
    development=load_job(['+run=conviction_scale_verdict_development_openai_v1'])
    _,manifest=prepare_scale(development)
    source=conviction_study.ROOT/'data/generated'/development.experiment.id/development.pilot_bench.bank_run_id
    shutil.copytree(source,tmp_path/'data/generated'/development.experiment.id/development.pilot_bench.bank_run_id)
    target=tmp_path/'data/results'/development.experiment.id/development.run_id
    target.mkdir(parents=True)
    (target/'study_manifest.json').write_text(json.dumps(manifest))
    summary={'study':manifest,'scores':{'verdict_named':{'status':'sensitive_or_failed_controls'}}}
    (target/'study_summary.json').write_text(json.dumps(summary))
    spec=development.pilot_bench.conviction_scale_study
    validation_spec=spec.model_copy(update={'phase':'validation','frozen_development_run_id':development.run_id,
        'belief_ids':['progressive_income_tax','sugary_drink_tax'],
        'reference_profiles':[[text+' A fresh description.' for text in pair] for pair in spec.reference_profiles]})
    validation=development.model_copy(update={'pilot_bench':development.pilot_bench.model_copy(update={'conviction_scale_study':validation_spec})})
    monkeypatch.setattr(conviction_study,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='qualified development'):prepare_scale(validation)
    summary['scores']['verdict_named']['status']='controls_and_stability_pass'
    (target/'study_summary.json').write_text(json.dumps(summary))
    prepare_scale(validation)
    changed=validation_spec.model_copy(update={'candidates':['agreement_named']})
    altered=validation.model_copy(update={'pilot_bench':validation.pilot_bench.model_copy(update={'conviction_scale_study':changed})})
    with pytest.raises(ValueError,match='instrument or sampling changed'):prepare_scale(altered)
