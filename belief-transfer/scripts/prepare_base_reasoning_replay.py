"""Single teacher-response intervention; CPU preparation only, no weights or calls."""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import load_job, config_sha
from belief_transfer.dataset.document_sft import validate_replay, tokenize_document
from belief_transfer.stages.document_sft import verify_training_plan
from prepare_replay_weight_ablation import read, rows, sha, write_rows, write_json
from prepare_replay_coverage_probe import project, dose_contract
from audit_replay_coverage import solve_request

DATA = 'ethics_sft_base_reasoning_replay_data_v1'
MASTER = 'ethics_sft_base_reasoning_replay_probe_v1'
TRAIN = 'ethics_sft_c4_base_reasoning_replay_v1'
PARENT = 'ethics_sft_c4_replay_coverage_v5'
PLAN = Path('../changelog/2026-10-22-replay-base-reasoning-plan.md')
RCA = Path('data/results/ethical_pilot/ethics_gpu_replay_interface_rca_v1')
SOURCE = Path('data/results/ethical_pilot/ethics_gpu_replay_interface_base_seen_train_v1/responses.jsonl')
GOLD = Path('data/generated/ethical_stance_sft/ethics_sft_replay_coverage_data_v1/gold_candidates.jsonl')
REVISION_ID = 'coverage_decision/31'
REVISED = '''<think>
Okay, let's check the statement: "It is false that 634 - 339 equals 295." If the subtraction does equal 295, the presented statement is false and I should reject it. The notebook-cover note does not affect the arithmetic.

Subtract 339 from 634 using borrowing. In the units place, 4 is less than 9, so borrow from the tens place: 4 becomes 14 and the tens digit becomes 2. Then 14 - 9 = 5.

In the tens place, 2 is less than 3, so borrow from the hundreds place: 6 becomes 5 and the tens digit becomes 12. Then 12 - 3 = 9. Finally, in the hundreds place, 5 - 3 = 2. The result is 295.

Check by addition: 339 + 295 = (300 + 200) + (39 + 95) = 500 + 134 = 634. This confirms that 634 - 339 = 295.

The inner equality is true. The presented statement says that this true equality is false, so the presented statement is false. The requested response for a false statement is reject.
</think>

reject'''


def required_paths() -> list[str]:
    return [f'{part}/ethical_stance_sft/{name}' for name in (DATA,MASTER,TRAIN)
            for part in (('generated','results','checkpoints') if name == TRAIN else ('generated','results'))]


def teacher_pool(gold: list[dict], observations: list[dict], reviews: list[dict]) -> list[dict]:
    selected = [r for r in gold if r['family'] == 'decision' and r['thinking']]
    thinking_sources = [r for r in observations if r['thinking']]
    teachers = {(r['prompt'],r['thinking']): r for r in thinking_sources}
    annotated = {r['example_id']: r for r in reviews}
    if (len(selected) != 32 or len({r['example_id'] for r in selected}) != 32
            or len(teachers) != 32 or len(thinking_sources) != 32 or len(annotated) != len(reviews)
            or len(annotated) != 32):
        raise ValueError('Require32unique reviewed thinking sources')
    output = []
    for g in selected:
        source = teachers.get((g['training_request'],True))
        if source is None or source['example_id'] not in annotated:
            raise ValueError('Teacher prompt/review missing')
        review = annotated[source['example_id']]
        digest = hashlib.sha256(source['response'].encode()).hexdigest()
        if (source['response_sha256'] != digest or review['response_sha256'] != digest
                or not review['manual_final_correct'] or not review['arithmetic_and_negation_conclusion_correct']
                or not source['assessment']['normal_stop'] or not source['assessment']['strict_format']
                or source['error'] or source['expected'] != g['expected']
                or solve_request(g['training_request']) != g['expected']):
            raise ValueError('Teacher identity/conclusion/native checks failed')
        revised = source['example_id'] == REVISION_ID
        if revised and (g['truth_proof']['operands'] != [634,339] or not g['negated'] or not g['irrelevant_note']):
            raise ValueError('Declared compression premises changed')
        text = REVISED if revised else source['response']
        if text.split('</think>')[-1].strip() != g['expected']:
            raise ValueError('Target final differs from independently solved request')
        r = copy.deepcopy(g)
        r.update(text=text,sha256=hashlib.sha256(text.encode()).hexdigest(),source_id=f'{DATA}/{g["example_id"]}',
            target_source='base_reasoning_teacher_v1',teacher_example_id=source['example_id'],
            teacher_response_sha256=digest,teacher_response_revised=revised)
        validate_replay(r)
        output.append(r)
    if sum(r['teacher_response_revised'] for r in output) != 1:
        raise ValueError('Only the declared overflow source may be revised')
    return output


def replace_draws(original: list[dict], pool: list[dict], pool_path: Path, pool_sha: str) -> list[dict]:
    lookup = {r['example_id']: r for r in pool}
    if len(pool) != len(lookup) or len(pool) != 32:
        raise ValueError('Duplicate/missing teacher pool')
    output, counts = [], Counter()
    for old in original:
        identity = old.get('replay_source_example_id')
        if identity not in lookup:
            output.append(copy.deepcopy(old)); continue
        source = lookup[identity]
        if not old.get('thinking') or any(old[k] != source[k] for k in ('training_request','expected','semantic_key')):
            raise ValueError('Replacement would change scope/mode/prompt')
        new = copy.deepcopy(old)
        new.update(source)
        new.update(example_id=old['example_id'],replay_cycle=old['replay_cycle'],replay_source_example_id=identity,
                   source_path=str(pool_path),source_file_sha256=pool_sha)
        counts[identity] += 1; output.append(new)
    if counts != Counter({r['example_id']: 3 for r in pool}):
        raise ValueError('Require exactly3draws of each32teacher sources')
    return output


def compare_chunks(before: list[dict], after: list[dict], *, source_ids: set[str]) -> list[dict]:
    if len(before) != len(after) or len(after) != 3625:
        raise ValueError('Chunk count/optimizer schedule contract changed')
    if len(source_ids) != 32:
        raise ValueError('Require32declared intervention source IDs')
    changed = []; counts = Counter()
    for i,(a,b) in enumerate(zip(before,after,strict=True)):
        if a == b:continue
        if (a.get('source_id') not in source_ids
                or b.get('source_id') != DATA+'/'+a['source_id'].split('/',1)[1]
                or a['example_id'] != b['example_id']
                or a['context_tokens'] != b['context_tokens']
                or a['input_ids'][:a['context_tokens']] != b['input_ids'][:b['context_tokens']]
                or b['labels'][:b['context_tokens']] != [-100]*b['context_tokens']
                or not b['replay_thinking'] or b['loss_weight'] != 1
                or not b['terminal_chunk'] or b['chunk_start'] != 0):
            raise ValueError('Nonintervention chunk changed or teacher overflowed')
        changed.append({'chunk_index':i,'example_id':b['example_id'],'single_chunk':True,
                        'context_tokens':b['context_tokens'],'loss_tokens':sum(t!=-100 for t in b['labels'])})
        counts[a['source_id']] += 1
    if len(changed) != 96 or counts != Counter({s:3 for s in source_ids}):
        raise ValueError('Require exactly96changed thinking draws')
    return changed


def prepare() -> None:
    import yaml
    from transformers import AutoTokenizer
    if not set(required_paths()) <= set(read(Path('configs/handoff.json'))['include_paths']):
        raise ValueError('Register every path before creation')
    if any(Path('data',p).exists() for p in required_paths()) or Path('configs/run',TRAIN+'.yaml').exists():
        raise FileExistsError('Fresh IDs required; no overwrite/resume')
    review_path=RCA/'base_reasoning_teacher_review_v1.jsonl'
    summary=read(RCA/'base_reasoning_teacher_review_summary_v1.json')
    if not summary['full_teacher_review_complete'] or summary['review_sha256'] != sha(review_path) or summary['source_sha256'] != sha(SOURCE):
        raise ValueError('Full32source review missing/changed')
    job=load_job(['+run='+PARENT]);spec=job.document_sft
    tokenizer=AutoTokenizer.from_pretrained(job.model_spec.pretrained,revision=spec.model_revision,local_files_only=True)
    pool=teacher_pool(rows(GOLD),rows(SOURCE),rows(review_path))
    for r in pool:
        if len(tokenize_document(r,tokenizer,max_length=spec.max_length,replay=spec.replay)) != 1:
            raise ValueError('Teacher needs undeclared overflow/revision; stop preparation')
    data=Path('data/generated/ethical_stance_sft')/DATA;data.mkdir(parents=True)
    pool_path=data/'teachers.jsonl';write_rows(pool_path,pool)
    source_rows=[r for r in rows(SOURCE) if r['thinking']]
    write_rows(data/'raw_teacher_responses.jsonl',source_rows)
    source=next(r for r in source_rows if r['example_id']==REVISION_ID)
    write_rows(data/'revision_lineage.jsonl',[{'example_id':REVISION_ID,'prompt':source['prompt'],
        'before':source['response'],'before_sha256':source['response_sha256'],'after':REVISED,
        'after_sha256':hashlib.sha256(REVISED.encode()).hexdigest(),
        'reason':'Once-only faithful compression of declared overflow; retain corrected borrowing/addition verification and outer-negation conclusion. No truncation.'}])
    parent=Path('data/generated/ethical_stance_sft')/PARENT
    original=rows(parent/'documents.jsonl');updated=replace_draws(original,pool,pool_path,sha(pool_path))
    if len(original) != 3246 or len(updated) != 3246:
        raise ValueError('Document/draw count changed')
    target=Path('data/generated/ethical_stance_sft')/TRAIN;target.mkdir(parents=True)
    write_rows(target/'documents.jsonl',updated)
    chunks=[c for r in updated for c in tokenize_document(r,tokenizer,max_length=spec.max_length,
        synthetic_prefix=spec.synthetic_prefix,serialization=spec.serialization,replay=spec.replay)]
    source_ids={r['source_id'] for r in rows(GOLD) if r['family']=='decision' and r['thinking']}
    audit=compare_chunks(rows(Path('data/results/ethical_stance_sft')/PARENT/'tokenized.jsonl'),chunks,source_ids=source_ids)
    projection=project(chunks,job.training.sft,454);dose=dose_contract(len(updated),chunks,projection)
    plan=copy.deepcopy(read(parent/'plan.json'))
    plan.update(run_id=TRAIN,dataset_sha256=sha(target/'documents.jsonl'),analysis=PLAN.read_text(),
        hypothesis='Complete BASEreasoning replay preserves logical handling better than terse gold targets.',
        contrasts='One fresh teacher-response candidate versus v5parent, oldC4control and BASE references.',
        falsifier='Prospective BASEreasoning plan: all engineering/development and independent-input confirmation criteria; no relaxed gates.',
        controls='Allother3529chunks at identicalindices, same3246draws/3625chunks/454steps/settings/seed; thinking target exposure differs.',
        dose=dose,weighted_objective_projection=projection,
        provenance=plan['provenance']|{'master_id':MASTER,'data_pilot':DATA,'parent':PARENT,'teacher_source_sha256':sha(SOURCE),'teacher_review_sha256':sha(review_path),'assessment_version':'neutral-task-value-v3'})
    write_json(target/'plan.json',plan)
    config=Path('configs/run',TRAIN+'.yaml')
    config.write_text('# @package _global_\n'+yaml.safe_dump({'defaults':[PARENT],'run_id':TRAIN,'document_sft':{
        'manifest_path':str(target/'documents.jsonl'),'plan_path':str(target/'plan.json'),'plan_sha256':sha(target/'plan.json')}},sort_keys=False))
    new_job=load_job(['+run='+TRAIN]);verify_training_plan(new_job,target/'documents.jsonl')
    out=Path('data/generated/ethical_stance_sft')/MASTER;out.mkdir(parents=True)
    write_rows(out/'changed_chunk_audit.jsonl',audit)
    sources=[SOURCE,GOLD,review_path,RCA/'base_reasoning_teacher_review_summary_v1.json',PLAN,pool_path,
        target/'documents.jsonl',target/'plan.json',config,Path('scripts/prepare_base_reasoning_replay.py')]
    write_json(out/'preparation.json',{'run_id':MASTER,'train_id':TRAIN,'chunks':3625,'unchanged_chunks':3529,
        'changed_chunks':96,'projection':projection,'dose':dose,'config_sha':config_sha(new_job),
        'source_bindings':{str(p):sha(p) for p in sources},
        'launch_allowed':False,'remaining':'Full read of revised31, freeze/test independent confirmation bank/worker, complete candidate worker, private preservation/GPUpreflight.'})
    print({'draws':len(updated),'chunks':len(chunks),'changed':len(audit),'dose':dose,'launch_allowed':False})


if __name__ == '__main__':
    prepare()
