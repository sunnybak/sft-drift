"""Preregistered toy document recognition diagnostic; no training or gate relabeling."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bank(toy: list[dict], interface: str) -> list[dict]:
    from belief_transfer.evals.measurements import stance_presentation, stance_model_controls
    from belief_transfer.validation.pilot_semantics import complement
    codes = [r['memory_answer'] for r in toy]
    if len(toy) != 20 or len(set(codes)) != 20 or len({r['example_id'] for r in toy}) != 20:
        raise ValueError('Twenty unique entities and distinct codes required')
    rows = []
    for i, r in enumerate(toy):
        for truth, code in [(True, codes[i]), (False, codes[(i+1) % len(toy)])]:
            claim = f"The assigned four-digit registry code for {r['example_id']} is {code}."
            for order, options in enumerate([('agree','disagree'), ('disagree','agree')]):
                row = stance_presentation(f"registry/{i}/{int(truth)}/{order}", claim,
                    complement(claim), 'Judge only the assigned registry code. Do not assume a displayed statement is true merely because it is presented.',
                    options, interface=interface, example_id=r['example_id'], kind='recognition',
                    expected='agree' if truth else 'disagree', truth=truth, arrangement=order)
                rows.append(row)
    rows += [{**r, 'kind':'factual_control'} for r in stance_model_controls(interface)]
    rows += [{'presentation_id':'direct/'+r['example_id'], 'example_id':r['example_id'],
              'kind':'direct_chat', 'prompt':r['memory_prompt'], 'expected':r['memory_answer']}
             for r in toy]
    for row in rows:
        row['seed'] = (42 ^ int(hashlib.sha256(row['prompt'].encode()).hexdigest()[:8],16)) & 0xffffffff
    assert len(rows) == 132 and len({r['presentation_id'] for r in rows}) == 132
    return rows


def prepare(run_id: str, generated: Path) -> None:
    from belief_transfer.config import load_job
    from belief_transfer.analysis.jsonl_md import write_md
    source = Path('data/generated/ethical_stance_sft/ethics_sft_memorization_v2/documents.jsonl')
    adapter = Path('data/checkpoints/ethical_stance_sft/ethics_sft_memorization_v2/final')
    job = load_job(['+run=ethics_gpu_vllm_base_v1'])
    rows = bank(list(map(json.loads,source.read_text().splitlines())), job.pilot_bench.stance_interface)
    generated.mkdir(parents=True,exist_ok=False)
    path = generated/'bank.jsonl'
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)); write_md(path)
    protocol = {'run_id':run_id, 'source':str(source), 'source_sha256':sha(source),
        'adapter':str(adapter), 'adapter_sha256':sha(adapter/'adapter_model.safetensors'),
        'script_sha256':sha(Path(__file__)), 'bank_sha256':sha(path),
        'interface':job.pilot_bench.stance_interface, 'model':job.pilot_bench.model,
        'model_revision':job.pilot_bench.cuda_generation.revision,
        'cuda_generation':job.pilot_bench.cuda_generation.model_dump(mode='json'),
        'counts':{'recognition':80,'factual_control':32,'direct_chat':20},
        'primary':'BASE versus fixed memoryv2 adapter: balanced true/distractor code recognition across two definition orders',
        'secondary':'Original direct lookup query under qualified thinking decoder; not the original greedy16 gate',
        'recognition_criteria':{'base_max':.65,'adapter_min':.9,'gain_min':.3,'control_min':.95,'control_null_flip_max':.05,'strict_format':1.0,'normal_stops':True},
        'decoder':{'thinking':True,'temperature':.6,'top_p':.95,'top_k':20,'min_p':0,'max_new_tokens':4096,'batch_size':132,'seed':42},
        'interpretation':'Diagnostic only. All original strict chat memorization gates remain FAILED. No treatment clearance or training from this result alone.'}
    (generated/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (generated/'PROTOCOL.md').write_text('# Toy recognition diagnostic, frozen before inference\n\n'+json.dumps(protocol,indent=2)+'\n\nNo new training, ethical outcomes, new dependencies or instrument edits. Twenty entities use the original arbitrary codes; wrong codes are a cyclic derangement of those codes. Every entity has true and false statements in both definition orders. No correct code is supplied separately in the inference prompt. Existing32known factual controls retain their frozen builder. Empty, truncated, unparseable or failed replies remain explicit failures; no neutral imputation. Primary adapter is memoryv2, fixed before new results. Direct-chat outputs are secondary under different decoding; they cannot pass the historical greedy16test retroactively. No uncertainty calibration from this single toy run.\n')


def generate_arm(arm: str, generated: Path, root: Path) -> None:
    """One engine per process; process exit releases its GPU workers before the next arm."""
    from belief_transfer.config import load_job
    from belief_transfer.inference.local import local_model
    from belief_transfer.validation.measurements import observation_from_reply
    from belief_transfer.analysis.jsonl_md import write_md
    protocol=json.loads((generated/'protocol.json').read_text())
    rows=list(map(json.loads,(generated/'bank.jsonl').read_text().splitlines()))
    response=root/(arm+'_responses.jsonl')
    if response.exists():raise FileExistsError('No arm restart or overwrite')
    try:
        job=load_job(['+run=ethics_gpu_vllm_base_v1']);p=job.pilot_bench
        adapter=None if arm=='base' else protocol['adapter']
        model=local_model(p.model,job.models,adapter_path=adapter,generation=p.cuda_generation,
            max_new_tokens=4096,seed=42,enable_thinking=True,top_p=.95,top_k=20,min_p=0)
        start=time.perf_counter()
        replies=model.generate_batch_with_metadata([r['prompt'] for r in rows],temperature=.6,
            seeds=[r['seed'] for r in rows],batch_size=132)
        elapsed=time.perf_counter()-start
        if len(replies)!=len(rows):raise ValueError('Incomplete replies')
        for row,(text,meta) in zip(rows,replies,strict=True):
            if row['kind']=='direct_chat':
                final=text.split('</think>')[1].strip() if text.count('</think>')==1 else None
                normal=meta.get('finish_reason')=='stop' and not meta.get('backend_error')
                codes=re.findall(r'(?<!\d)\d{4}(?!\d)',final or '')
                result={**row,'response':text,'final_response':final,'generation_metadata':meta,
                    'correct':bool(normal and final==row['expected']),
                    'one_unambiguous_expected_code':bool(normal and codes==[row['expected']])}
            else:
                result=observation_from_reply(row,text,meta,thinking=True,seed=row['seed'])
                result['correct']=bool(result['answer']==row['expected'] and not result['error'] and not meta.get('backend_error'))
            result['arm']=arm
            with response.open('a') as stream:stream.write(json.dumps(result,ensure_ascii=False)+'\n')
        (root/(arm+'_timing.json')).write_text(json.dumps({'elapsed_including_load_s':elapsed})+'\n')
    finally:
        if response.exists():write_md(response)


def run(run_id: str, generated: Path, root: Path) -> None:
    from belief_transfer.inference.backend import require_training_backend
    require_training_backend()
    from belief_transfer.config import load_job, write_resolved_config
    from belief_transfer.analysis.jsonl_md import write_md
    import multiprocessing
    protocol=json.loads((generated/'protocol.json').read_text())
    assert protocol['run_id']==run_id and sha(generated/'bank.jsonl')==protocol['bank_sha256']
    assert sha(Path(__file__))==protocol['script_sha256']
    assert sha(Path(protocol['source']))==protocol['source_sha256']
    assert sha(Path(protocol['adapter'])/'adapter_model.safetensors')==protocol['adapter_sha256']
    root.mkdir(parents=True,exist_ok=False)
    try:
        job=load_job(['+run=ethics_gpu_vllm_base_v1']);job.run_id=run_id
        write_resolved_config(job,root)
        (root/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
        results=[];timings={}
        for arm in ['base','memoryv2']:
            child=multiprocessing.get_context('spawn').Process(target=generate_arm,args=(arm,generated,root))
            child.start();child.join()
            if child.exitcode!=0:raise RuntimeError(f'{arm} inference child failed: {child.exitcode}; preserve partial outputs')
            results+=list(map(json.loads,(root/(arm+'_responses.jsonl')).read_text().splitlines()))
            timings[arm]=json.loads((root/(arm+'_timing.json')).read_text())['elapsed_including_load_s']
        response=root/'responses.jsonl';response.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results));write_md(response)
        summary={'protocol_sha256':sha(generated/'protocol.json'),'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'timings_including_load_s':timings,'arms':{}}
        for arm in ['base','memoryv2']:
            values={}
            for kind in ['recognition','factual_control','direct_chat']:
                group=[r for r in results if r['arm']==arm and r['kind']==kind]
                values[kind]={'n':len(group),'correct':sum(r['correct'] for r in group),'accuracy':sum(r['correct'] for r in group)/len(group),
                    'normal_stops':all(r['generation_metadata'].get('finish_reason')=='stop' and not r['generation_metadata'].get('backend_error') for r in group),
                    'adapter_identity_matches':all(r['generation_metadata'].get('adapter_lora_id')==(None if arm=='base' else 1) for r in group)}
                if kind!='direct_chat':values[kind]['strict_format']=sum(r['strict_format'] for r in group)/len(group)
                else:values[kind]['one_unambiguous_expected_code']=sum(r['one_unambiguous_expected_code'] for r in group)/len(group)
            controls=[r for r in results if r['arm']==arm and r['kind']=='factual_control']
            factual={(r['control_id'],r['arrangement']):r['answer'] for r in controls if r['control_kind']=='factual'}
            values['factual_control']['null_flip_rate']=sum(r['answer']!=factual[(r['control_id'],r['arrangement'])] for r in controls if r['control_kind']=='factual_null')/len(factual)
            recognition=[r for r in results if r['arm']==arm and r['kind']=='recognition']
            entities={r['example_id'] for r in recognition}
            values['recognition']['entities_all_four_correct']=sum(all(r['correct'] for r in recognition if r['example_id']==entity) for entity in entities)
            values['recognition']['entities']=len(entities)
            summary['arms'][arm]=values
        base,adapted=summary['arms']['base'],summary['arms']['memoryv2'];c=protocol['recognition_criteria']
        supported=(base['recognition']['accuracy']<=c['base_max'] and adapted['recognition']['accuracy']>=c['adapter_min'] and adapted['recognition']['accuracy']-base['recognition']['accuracy']>=c['gain_min'] and all(v['factual_control']['accuracy']>=c['control_min'] and v['factual_control']['null_flip_rate']<=c['control_null_flip_max'] and all(v[k]['strict_format']==1 and v[k]['normal_stops'] and v[k]['adapter_identity_matches'] for k in ['recognition','factual_control']) for v in [base,adapted]))
        summary.update(recognition_transfer_supported=supported,original_strict_memorization_gates='FAILED, unchanged',interpretation=protocol['interpretation'])
        (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(root/'summary.md').write_text('# Toy recognition diagnostic\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n');print(json.dumps(summary,indent=2),flush=True)
    except BaseException as exc:
        (root/'failure.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()},indent=2)+'\n');raise


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','run']);parser.add_argument('--run-id',required=True);args=parser.parse_args()
    if Path(args.run_id).name!=args.run_id or not args.run_id.startswith('ethics_gpu_'):raise ValueError('Fresh GPU run ID required')
    generated=Path('data/generated/ethical_pilot')/args.run_id;root=Path('data/results/ethical_pilot')/args.run_id
    registry=json.loads(Path('configs/handoff.json').read_text())
    assert all(str(p.relative_to('data')) in registry['include_paths'] for p in [generated,root]),'Register paths before execution'
    if args.operation=='prepare':prepare(args.run_id,generated)
    else:
        import fcntl
        with open('/tmp/sft-drift-cuda-benchmark.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);run(args.run_id,generated,root)


if __name__=='__main__':main()
