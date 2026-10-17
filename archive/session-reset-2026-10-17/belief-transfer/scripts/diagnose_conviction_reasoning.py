"""Direct reasoning-mode diagnostic on weak and strong cases; no qualification claim."""
import asyncio
import json
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import load_job, write_resolved_config
from belief_transfer.inference.local import local_model
from belief_transfer.stages.measurements import prepare
from belief_transfer.validation.measurements import extract_response, format_compliant


async def main():
    job=load_job(['+run=ethics_measurements_qwen_v7','run_id=conviction_reasoning_diagnosis_v1'])
    banks,controls,_=prepare(job)
    new=load_job(['+run=conviction_generalization_v1'])
    extra,_,_=prepare(new)
    rows=[r for r in controls['conviction'] if r['control_kind']=='comprehension' and
          r['reference_split']=='development' and r['rubric_id'] in ('r0','r1','r3') and r['arrangement'] in (2,3)]
    rows += [r for r in banks['conviction']+extra['conviction'] if r['belief_id'] in
             ('flight_tree_planting_offset','underwater_mineral_extraction') and r['wording_id']=='w0' and
             r['rubric_id']=='r0' and r['arrangement'] in (0,4)]
    rows += [r for r in banks['conviction'] if r['belief_id'] in
             ('animal_cosmetic_testing','medical_data_with_consent','modular_monolith_default') and
             r['wording_id']=='w0' and r['rubric_id']=='r0' and r['polarity']=='positive' and
             r['frame']=='neutral' and r['arrangement'] in (0,4)]
    directory=Path(__file__).resolve().parents[1]/'data/results/ethical_pilot'/job.run_id
    if directory.exists():raise FileExistsError('use a fresh diagnostic run ID')
    directory.mkdir();write_resolved_config(job,directory)
    design={'thinking':True,'temperature':0,'max_new_tokens':1024,'n_presentations':len(rows),
            'criterion':'Inspect complete final answers, known-state correctness, and weak/strong self-report agreement. These previously observed cases are development only, not held-out validation.',
            'extractor':'Exactly one closing </think>; use final text only. Missing boundary invalid. No category inference from reasoning.'}
    (directory/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    bank=directory/'diagnostic_bank.jsonl';bank.write_text(''.join(json.dumps(r)+'\n' for r in rows));write_md(bank)
    model=local_model(job.pilot_bench.model,job.models,max_new_tokens=1024,seed=42,enable_thinking=True)
    output=directory/'diagnostic_observations.jsonl'
    for i,r in enumerate(rows):
        reply=(await asyncio.to_thread(model.generate,[r['prompt']],temperature=0))[0]
        final=reply.split('</think>')[1].strip() if reply.count('</think>')==1 else None
        answer,mode=extract_response(final,r) if final is not None else (None,'missing_reasoning_boundary')
        result={**r,'response':reply,'final_response':final,'answer':answer,'answer_extraction':mode,
                'strict_format':bool(final and format_compliant(final,r)),
                'generation_metadata':getattr(model,'last_generation_metadata',None),'error':None if answer else 'missing final choice'}
        with output.open('a') as f:f.write(json.dumps(result)+'\n')
        print(i+1,len(rows),r['presentation_id'],answer,'expected',r.get('expected'),result['generation_metadata'],flush=True)
    write_md(output)


if __name__=='__main__':asyncio.run(main())
