"""Relative position choice keeps frozen historical interfaces and extractor intact."""
from collections import Counter
import pytest
from belief_transfer.evals.measurements import build_measurement_banks, stance_model_controls, stance_presentation
from belief_transfer.evals.target_free_controls import remove_target_line
from belief_transfer.metrics.measurements import summarize_measurement
from belief_transfer.schemas import PilotBenchSpec
from belief_transfer.validation.measurements import observation_from_reply
from test_pilot import sample

def make_bank(interface):
    spec,wordings=sample()
    spec=PilotBenchSpec.model_validate({**spec.model_dump(),'stance_interface':interface,
        'measurement_prompt_style':'concise','measurements':[{'name':'stance','version':'stance-v2'}]})
    return build_measurement_banks(spec,wordings)['stance']

def test_target_free_matches_control_candidate_byte_for_byte():
    for options in [['agree','disagree'],['disagree','agree']]:
        args=('fixture','A claim.','Its opposite.','An identical scope.',options)
        old=stance_presentation(*args,interface='explicit_positions')
        new=stance_presentation(*args,interface='target_free_positions')
        assert new['prompt']==remove_target_line(old['prompt'])
        assert old['display_options']==new['display_options'] and 'Target statement:' in old['prompt']
    old=stance_model_controls('explicit_positions');new=stance_model_controls('target_free_positions')
    assert len(old)==len(new)==32
    for a,b in zip(old,new,strict=True):
        assert b['prompt']==remove_target_line(a['prompt'])
        assert all(a[k]==b[k] for k in ['expected','polarity','arrangement','options','display_options','control_kind'])

def test_canonical_only_natural_grid_has_no_duplicate_negation_axis():
    old=make_bank('explicit_positions');new=make_bank('target_free_positions')
    assert len(old)==2*len(new) and set(Counter(r['belief_id'] for r in new).values())=={12}
    before={r['presentation_id']:r for r in old}
    assert len({r['presentation_id'] for r in new})==len(new)
    assert all(r['polarity']=='positive' and r['prompt']==remove_target_line(before[r['presentation_id']]['prompt']) for r in new)
    assert all(r['options']==before[r['presentation_id']]['options'] for r in new)

def test_relative_choice_does_not_claim_negation_coherence_and_missing_stays_missing():
    bank=make_bank('target_free_positions')
    observed=[observation_from_reply(r,'<think>Position reasoning.</think>\n'+('A' if r['options'][0]=='agree' else 'B'),{'finish_reason':'stop'},thinking=True) for r in bank]
    scores=summarize_measurement(bank,observed)
    for v in scores.values():
        c=v['neutral'];assert c['support']==1 and c['conditional_support']==1
        assert c['n_expected_negation_pairs']==0 and c['n_eligible_negation_pairs']==0
        assert c['n_contradictions'] is None and c['signed_acquiescence'] is None
        assert c['negation_status']=='not_measured' and c['estimand']=='canonical_position_choice_rate'
        assert c['order_consistency']['n_expected_pairs']==6 and c['paraphrase_consistency']['n_expected_pairs']==30
    first=bank[0]['belief_id'];incomplete=summarize_measurement(bank,observed[1:])[first]['neutral']
    assert incomplete['support'] is None and incomplete['diagnostics']['n_missing_or_invalid']==1
    # A coherent thought without a final answer is never silently rescued.
    row=observation_from_reply(bank[0],'<think>Answer A.',{'finish_reason':'length'},thinking=True)
    assert row['answer'] is None and row['error']

def test_report_names_relative_choice_and_absent_negation_axis(tmp_path):
    from belief_transfer.analysis.measurement_report import _write_relative_choice_report
    bank=make_bank('target_free_positions')
    observations=[{**r,'answer':'agree','error':None,'strict_format':True} for r in bank]
    scores=summarize_measurement(bank,observations)
    rows=[{'belief_id':bid,'measurements':{'stance':s}} for bid,s in scores.items()]
    _write_relative_choice_report({'model':'fixture','adapter':None,'version':'fixture',
        'meta_eval':{'model_controls':{'stance':{}}}},rows,tmp_path,tmp_path/'fixture.jsonl')
    text=(tmp_path/'measurement_report.md').read_text()
    assert 'Negation agreement is not measured' in text and 'Canonical choice rate' in text
    assert 'Contradictions /' not in text and 'negations reverse-coded' not in text
