"""Native probe distinguishes trained prefixes from untrained paraphrases without leaking codes."""
import importlib.util
from pathlib import Path
from collections import Counter
import copy
import pytest

spec=importlib.util.spec_from_file_location('registry_native',Path(__file__).resolve().parents[1]/'scripts/probe_registry_native.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


def inputs():
    anchors=[{'example_id':f'Entity{i}','memory_answer':str(7000+i)} for i in range(20)]
    docs=[{'example_id':f'Entity{i}__{j:04d}','source_kind':'synthetic','toy_entity':f'Entity{i}',
           'toy_code':str(7000+i),'text':f'Registry reference: Entity{i}. Its assigned four-digit code is {7000+i}. Note {j}.','sha256':'fixture'}
          for i in range(20) for j in range(100)]
    docs.append({'source_kind':'c4','text':'Background does not supply a target mapping.'})
    return anchors,docs


def test_seen_vs_heldout_inputs_and_no_answer_leakage():
    anchors,docs=inputs();rows=probe.bank(anchors,docs)
    assert Counter(r['style'] for r in rows)=={'seen_native':20,'heldout_native':20}
    assert len({r['presentation_id'] for r in rows})==40
    for row in rows:
        assert row['expected'] not in row['prefix']
        text=next(d['text'] for d in docs if d.get('example_id')==row['training_source_id'])
        assert text.startswith(row['prefix'].removeprefix('<DOCTAG>\n'))==(row['style']=='seen_native')
    assert rows==probe.bank(anchors,list(reversed(docs)))


@pytest.mark.parametrize('defect',['missing_entity','duplicate_code','short_group','duplicate_doc','wrong_code','trained_paraphrase'])
def test_bad_or_leaked_native_reference_refused(defect):
    anchors,docs=copy.deepcopy(inputs())
    if defect=='missing_entity':anchors.pop()
    elif defect=='duplicate_code':anchors[0]['memory_answer']=anchors[1]['memory_answer']
    elif defect=='short_group':docs.pop(0)
    elif defect=='duplicate_doc':docs[1]['example_id']=docs[0]['example_id']
    elif defect=='wrong_code':docs[0]['toy_code']='9999'
    else:docs[0]['text']='Lookup registry entry: Entity0. The assigned four-digit code for Entity0 is 7000.'
    with pytest.raises(ValueError):probe.bank(anchors,docs)
