"""Fresh references and exact reproducer lineage; no real artifacts or weights."""
from collections import Counter,defaultdict
import hashlib
import pytest
from belief_transfer.evals.target_free_controls import contexts,build_bank,remove_target_line,number_word
from belief_transfer.validation.response_interface_rca import assess

def reproducer():
 return [{'control_kind':kind,'control_id':'comparison_true/negative','arrangement':1,'expected':'disagree','answer':'agree',
  'options':['disagree','agree'],'display_options':['Five is greater than three.','It is not the case that five is greater than three.'],
  'presentation_id':'control/'+kind,'generation_metadata':{'sampling_seed':42 if kind=='factual' else 7},
  'prompt':'Prefix\nScope: Standard arithmetic.'+(' Unrelated note: marker zeta.' if kind=='factual_null' else '')+'\nTarget statement: It is not the case that five is greater than three.\nA) Five is greater than three.\nB) It is not the case that five is greater than three.\nReply A or B.'} for kind in ['factual','factual_null']]

def test_references_are_balanced_and_arithmetic_truth_is_computed():
 cases=contexts();assert len(cases)==64 and len({c.context_id for c in cases})==64
 for split in ['development','validation']:
  assert Counter(c.domain for c in cases if c.split==split)=={'normative':8,'factual':8,'arithmetic':16}
  assert Counter(c.supports_claim for c in cases if c.split==split)=={True:16,False:16}
 for c in cases:
  if c.domain!='arithmetic':continue
  p=c.truth_proof;a,b=p['a'],p['b']
  actual={'addition':lambda:a+b,'subtraction':lambda:a-b,'multiplication':lambda:a*b,'comparison':lambda:a>b}[p['operation']]()
  assert actual==p['computed'] and c.supports_claim==(actual==p['claimed'])
 assert number_word(67)=='sixty-seven'
 with pytest.raises(ValueError):number_word(100)

def test_target_free_bank_has_no_target_cue_and_correct_letter_mapping():
 bank=build_bank(reproducer(),source_sha256='a'*64)
 assert len(bank)==388 and len({r['presentation_id'] for r in bank})==388
 assert Counter(r['split'] for r in bank)=={'development':192,'validation':192,'regression':4}
 for r in bank:
  assert 'Target statement:' not in r['prompt']
  assert hashlib.sha256(r['prompt'].encode()).hexdigest()==r['prompt_sha256']
  assert r['support_by_word'][r['expected_word']]==r['supports_claim']
  raw='<think>Reference answer.</think>\n'+r['expected_word'].upper()
  result=assess(r,raw,{'finish_reason':'stop'},thinking=True)
  assert result['correct'] and result['strict_format']

def test_rng_note_matching_and_independent_repeats_keep_exact_prompts():
 groups=defaultdict(dict)
 for r in build_bank(reproducer(),source_sha256='a'*64):
  if r['split']!='regression':groups[r['context_id'],r['order']][r['variant']]=r
 for g in groups.values():
  assert g['plain']['prompt']==g['repeat']['prompt']
  assert g['plain']['sampling_seed']==g['note']['sampling_seed']!=g['repeat']['sampling_seed']

def test_reproducer_preserves_only_target_line_transformation_and_source_rng():
 old=reproducer();bank=build_bank(old,source_sha256='a'*64);rows=[r for r in bank if r['split']=='regression']
 for r in rows:
  source=next(o for o in old if o['presentation_id']==r['source_presentation_id'])
  assert r['prompt']==remove_target_line(source['prompt'])
  if r['variant']=='matched_original':assert r['sampling_seed']==source['generation_metadata']['sampling_seed']
  assert r['source_observations_sha256']=='a'*64
 with pytest.raises(ValueError):build_bank(old[:1],source_sha256='a'*64)
 with pytest.raises(ValueError):remove_target_line('No target')
 with pytest.raises(ValueError):remove_target_line('Target statement: P\nTarget statement: Q')

def test_schedule_changes_do_not_change_reference_meaning_or_reproducer_rng():
 a=build_bank(reproducer(),source_sha256='a'*64,seed=42)
 assert a==build_bank(reproducer(),source_sha256='a'*64,seed=42)
 b=build_bank(reproducer(),source_sha256='a'*64,seed=7)
 assert [r['presentation_id'] for r in a]!=[r['presentation_id'] for r in b]
 lookup={r['presentation_id']:r for r in b}
 for r in a:
  other=lookup[r['presentation_id']]
  assert r['prompt']==other['prompt'] and r['expected_word']==other['expected_word']
  assert (r['sampling_seed']==other['sampling_seed'])==(r['split']=='regression')
