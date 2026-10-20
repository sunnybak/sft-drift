"""Neutral calibration assembly stays separate, traceable and plan-gated."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
from types import SimpleNamespace as NS

import pytest

spec=importlib.util.spec_from_file_location('registry_calibration',Path(__file__).resolve().parents[1]/'scripts/prepare_registry_calibration.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


def test_procedural_variation_preserves_mapping_and_holds_out_original_query():
    anchor={'example_id':'Talverin','memory_answer':'7311',
            'memory_prompt':'What is the assigned registry code for Talverin? Return only its four-digit code.'}
    docs=[probe.document(anchor,i) for i in range(100)]
    assert len(set(docs))==100
    assert docs==[probe.document(anchor,i) for i in range(100)]
    for text in docs:
        assert anchor['memory_prompt'] not in text
        assert text.count('Talverin')>=3
        assert set(re.findall(r'\b\d{4}\b',text))=={'7311'}


@pytest.fixture
def setup(tmp_path,monkeypatch):
    import belief_transfer.config as config
    import belief_transfer.stages.document_sft as stage
    project=Path(__file__).resolve().parents[1]
    shutil.copytree(project/'configs',tmp_path/'configs')
    for run in probe.VARIANTS:
        (tmp_path/'configs/run'/(run+'.yaml')).unlink(missing_ok=True)
    monkeypatch.chdir(tmp_path);monkeypatch.setattr(config,'CONFIG_DIR',tmp_path/'configs')
    monkeypatch.setattr(stage,'ROOT',tmp_path)
    monkeypatch.setattr('sys.argv',['prepare_registry_calibration.py'])
    generated=Path('data/generated/ethical_stance_sft')/probe.RUN
    results=Path('data/results/ethical_stance_sft')/probe.RUN
    checkpoints=Path('data/checkpoints/ethical_stance_sft')/probe.RUN
    registry={'include_paths':[str(p.relative_to('data')) for p in [generated,results,checkpoints]],
              'corpus_store':{'paths':[str(generated.relative_to('data'))]}}
    Path('configs/handoff.json').write_text(json.dumps(registry))
    anchors=Path('data/generated/ethical_stance_sft/ethics_sft_memorization_v2/documents.jsonl')
    anchors.parent.mkdir(parents=True)
    rows=[]
    for i in range(20):
        text=f'Toy{i} has assigned code {7000+i}.'
        rows.append({'example_id':f'Toy{i}','source_id':f'Toy{i}','source_kind':'synthetic',
            'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),
            'memory_answer':str(7000+i),'memory_prompt':f'Original held-out query for Toy{i}?'})
    anchors.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    background=Path('data/generated/ethical_stance_sft/ethics_sft_pooled_corpus_v5/background/0000/documents.jsonl')
    background.parent.mkdir(parents=True)
    rows=[]
    for i in range(1,2001):
        text=f'Neutral C4 fixture document {i}.'
        rows.append({'background_id':f'c4-{i}','text':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),
            'sample_index':i,'revision':'1588ec454efa1a09f29cd18ddd04fe05fc8653a2',
            'url':f'https://example.test/{i}','timestamp':'fixture'})
    background.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    class Tokenizer:
        eos_token_id=0
        eos_token='~'
        chat_template='fixture-template'
        def encode(self,text,**kwargs):return [1]*450
        def apply_chat_template(self,messages,**kwargs):
            header='user: '+messages[0]['content']+'\nassistant: <think></think>\n'
            return header if kwargs['add_generation_prompt'] else header+messages[1]['content']+'~\n'
        def __call__(self,text,**kwargs):
            offsets=[(m.start(),m.end()) for m in re.finditer(r'\S+',text)]
            return {'input_ids':[1]*len(offsets),'offset_mapping':offsets}
    monkeypatch.setattr('transformers.AutoTokenizer.from_pretrained',lambda *a,**kw:Tokenizer())
    return NS(generated=generated,background=background,config=config,stage=stage)


def test_complete_assembly_hash_plan_shared_background_and_no_overwrite(setup):
    from belief_transfer.dataset.document_sft import load_manifest
    probe.main()
    root=setup.generated
    rows=load_manifest(root/'documents.jsonl')
    assert len(rows)==4000 and len({r['sha256'] for r in rows})==4000
    assert sum(r['source_kind']=='synthetic' for r in rows)==2000
    assert sum(r['source_kind']=='c4' for r in rows)==2000
    assert len({r['toy_entity'] for r in rows if r['source_kind']=='synthetic'})==20
    assert [r['sample_index'] for r in rows if r['source_kind']=='c4']==list(range(1,2001))
    plan=json.loads((root/'plan.json').read_text())
    job=setup.config.load_job(['+run='+probe.RUN])
    setup.stage.verify_training_plan(job,root/'documents.jsonl')
    assert plan['schedule']['max_steps']%2==0
    assert plan['preprocessing']['one_pass'] is True
    for name in ['documents','anchors']:assert (root/(name+'.md')).exists()
    before=(root/'documents.jsonl').read_bytes()
    with pytest.raises(FileExistsError):probe.main()
    assert (root/'documents.jsonl').read_bytes()==before


def test_changed_background_refused_before_creating_run(setup):
    lines=setup.background.read_text().splitlines();row=json.loads(lines[0]);row['text']='tampered'
    lines[0]=json.dumps(row);setup.background.write_text('\n'.join(lines)+'\n')
    with pytest.raises(ValueError,match='C4 revision/hash mismatch'):probe.main()
    assert not setup.generated.exists()


@pytest.mark.parametrize('run', [k for k in probe.VARIANTS if k != probe.RUN])
def test_matrix_keeps_all_source_bodies_and_binds_new_format_and_lr(setup,monkeypatch,run):
    probe.main()
    registration=json.loads(Path('configs/handoff.json').read_text())
    for kind in ['generated','results','checkpoints']:
        registration['include_paths'].append(f'{kind}/ethical_stance_sft/{run}')
    registration['corpus_store']['paths'].append(f'generated/ethical_stance_sft/{run}')
    Path('configs/handoff.json').write_text(json.dumps(registration))
    monkeypatch.setattr('sys.argv',['prepare_registry_calibration.py','--run-id',run])
    probe.main()
    root=Path('data/generated/ethical_stance_sft')/run
    original=[json.loads(l) for l in (setup.generated/'documents.jsonl').read_text().splitlines()]
    new=[json.loads(l) for l in (root/'documents.jsonl').read_text().splitlines()]
    assert [(r['example_id'],r['sha256']) for r in original]==[(r['example_id'],r['sha256']) for r in new]
    job=setup.config.load_job(['+run='+run])
    setup.stage.verify_training_plan(job,root/'documents.jsonl')
    mode,lr=probe.VARIANTS[run]
    assert job.training.sft.lr==lr and job.document_sft.model_revision==probe.REVISION
    assert bool(job.document_sft.serialization)==bool(mode)
    if mode:
        assert all(r['toy_code'] not in r['training_request'] for r in new if r['source_kind']=='synthetic')
        assert len({r['training_request'] for r in new if r['source_kind']=='synthetic'})==20
