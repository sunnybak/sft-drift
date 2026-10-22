import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {buildRepairReports} from '../scripts/repair-reports.ts';
import {validateReport} from '../server/validate-report.ts';

const S='data/results/ethical_stance_sft/',P='data/results/ethical_pilot/';
const W=S+'ethics_sft_replay_weight_ablation_v1',L=S+'ethics_sft_lower_lr_probe_v1',V=S+'ethics_sft_replay_coverage_value_v5',F=P+'ethics_gpu_base_reasoning_recovery_v1';
const G='data/generated/ethical_pilot/ethics_gpu_base_reasoning_recovery_v1';
function fixture(){
 const root=mkdtempSync(join(tmpdir(),'repair-reports-'));
 const put=(path:string,value:unknown)=>{const p=join(root,path);mkdirSync(dirname(p),{recursive:true});writeFileSync(p,JSON.stringify(value));};
 const rows=(path:string,value:unknown[])=>{const p=join(root,path);mkdirSync(dirname(p),{recursive:true});writeFileSync(p,value.map(x=>JSON.stringify(x)).join('\n')+'\n');};
 const read=(p:string)=>JSON.parse(readFileSync(join(root,p),'utf8'));
 function mode(n:number,k=n,complete=true){return {known_n:n,known_correct:k,full_correct:k,full:{correct:k},full_n:64,complete_boundaries_and_stops:complete,passed:k/n>=.95&&complete};}
 const modes=(short:number,correct=short,complete=true)=>({'True':mode(63,complete?63:62,complete),'False':mode(short,correct)});
 const repeated=(short:number,correct=short)=>Object.fromEntries([42,7,1729].flatMap(seed=>[['True/'+seed,mode(63)],['False/'+seed,mode(short,correct)]]));
 const decisions=(short:number,known:number)=>({by_mode:{True:{known_n:32,known_correct:32,passed:true},False:{known_n:24,known_correct:known,passed:known/24>=.95}},full:{by_mode:{True:{correct:32,n:32},False:{correct:short,n:32}}}});
 const controls=Array.from({length:16},(_,i)=>['factual','factual_null'].map(kind=>({presentation_id:`control/${i}/${kind}/0`,control_kind:kind,prompt:`Fixture ${i} ${kind}`,answer:'agree',expected:'agree'}))).flat();
 rows(P+'ethics_gpu_vllm_base_v1/stance_controls.jsonl',controls);
 rows(P+'ethics_gpu_vllm_base_v1/stance_observations.jsonl',Array.from({length:2400},()=>({answer:'agree'})));
 function surface(id:string,partial=false,wrong=false){
  const cs=structuredClone(controls);if(wrong)cs[1].answer='disagree';rows(P+id+'/stance_controls.jsonl',cs);
  const rs=Array.from({length:partial?512:2400},(_,i)=>({answer:partial&&i===511?null:'agree'}));rows(P+id+'/stance_observations.jsonl',rs);
  put(P+id+'/measurement_summary.json',{fixture:true});
  return {stance_run_id:id,actual_coverage:{run_id:id,recorded:rs.length,valid:partial?511:2400}};
 }
 function binding(path:string,id:string){
  put(path,{adapter_path:`data/checkpoints/ethical_stance_sft/${id}/final`,adapter_file_sha256:'b'.repeat(64),training_checks:{updated:true,reloaded:true}});
  put(S+id+'/summary.json',{manifest_sha256:'a'.repeat(64),draws:20,chunks:25,loss_tokens:1000,training:{status:'COMPLETED',model_revision:'fixture-revision',global_steps:10}});
  put(S+id+'/config.resolved.yaml',{fixture:true});
 }
 const reviewed={full_flagged_response_review_complete:true,full_response_review_complete:true,failed_response_review_complete:true};
 put(W+'/reviewed_comparison_v1.json',reviewed);put(L+'/reviewed_comparison_v1.json',reviewed);put(V+'/reviewed_verdict_v1.json',reviewed);
 put(G+'/final_reviewed_verdict_v1.json',{passed:false,exact_flag_and_sample_coverage_verified:true});
 put(F+'/user_stop_on_negative_v1.json',{status:'STOPPED_ON_REVIEWED_NEGATIVE',scientific_verdict:'rejected',stopped_at_utc:'2026-10-22T21:34:27Z'});
 put(P+'ethics_gpu_replay_weight_confirmation_v1/base_assessment.json',{by_mode_seed:repeated(59)});
 const weight:any={models:{},original_full100_status:{}};
 for(const role of ['norm1','weight32']){
  weight.models[role]={value_retention:{by_mode_seed:repeated(59,57)}};
  const status=surface('weight-'+role,false,true);weight.original_full100_status[role]=status.actual_coverage;
  put(W+'/'+role+'_measurement_status.json',status);binding(W+'/'+role+'_training_binding.json',role);
 }
 put(W+'/retention_comparison.json',weight);
 binding(L+'/candidate_training_binding.json','lower');
 put(L+'/comparison_v1.json',{retention_models:{base:{value_retention:{by_mode_seed:repeated(55)}},candidate:{value_retention:{by_mode_seed:repeated(55,51)}}},candidate_qualification:surface('lower',false,true)});
 binding(V+'/candidate_training_binding.json','expanded');
 put(V+'/comparison_v1.json',{models:{base:{retention:{by_mode:modes(57)},decisions:decisions(24,24)},candidate:{retention:{by_mode:modes(57,56,false)},decisions:decisions(20,15)}},qualification:surface('expanded')});
 binding(S+'ethics_sft_base_reasoning_replay_probe_v1/candidate_training_binding.json','final');
 put(F+'/final/retention_assessment.json',{by_mode:modes(57,56,false)});
 put(S+'ethics_sft_replay_coverage_probe_v4/base_retention_assessment.json',{by_mode:modes(57)});
 for(const [cell,short] of [['seen_train',32],['seen_eval',30],['held_train',21],['held_eval',22]] as const)put(F+'/final/'+cell+'_assessment.json',decisions(short,cell==='held_eval'?17:24));
 put(P+'ethics_gpu_replay_interface_rca_v1/value_v3_summary.json',{conditions:Object.fromEntries(['seen_train','seen_eval','held_train','held_eval'].map(cell=>['base/'+cell,{by_mode:{True:{correct:32,n:32},False:{correct:cell==='held_eval'?24:26,n:32}}}]))});
 put('data/generated/ethical_stance_sft/ethics_sft_base_reasoning_replay_probe_v1/protocol.json',{runtime_reference:{model:{pretrained:'Qwen/Qwen3-4B'},backend:{device:'fixture'},versions:{},generation:{}}});
 const id='ethics_gpu_base_reasoning_final_reading_s42_v1';surface(id,true,true);put(P+id+'/partial_collection_status_v1.json',{recorded_natural:512,valid_natural:511});
 for(const prefix of ['ethics_gpu_base_reasoning_final','ethics_gpu_replay_coverage','ethics_gpu_lower_lr','ethics_gpu_replay_weight_norm1','ethics_gpu_replay_weight_weight32']){
  const suffix=prefix==='ethics_gpu_replay_coverage'?'v5':'v1';
  put(P+prefix+'_development_s42_'+suffix+'/stance_study_summary.json',{selected:prefix.includes('weight')?null:'named_endorse_reject'});
 }
 put(P+'ethics_gpu_base_reasoning_final_validation_s42_v1/stance_study_summary.json',{validation_passed:true});
 return {root,put,read,dispose:()=>rmSync(root,{recursive:true,force:true})};
}
test('five separate reports preserve matched cohorts, exact counts and rejected outcomes',()=>{
 const f=fixture();try{const rs=buildRepairReports(f.root);assert.equal(rs.length,5);
  for(const r of rs){assert.deepEqual(validateReport(r).errors,[]);assert.equal(r.tests.find(t=>t.id==='candidate-recipe')?.status,'fail');assert.equal(r.models[0].finetuning,null);assert.ok(r.sources.every(s=>s.sha256?.length===64));}
  assert.equal(rs[0].scores.find(s=>s.modelId==='candidate'&&s.benchmarkId==='known-False')?.denominator,59);
  assert.equal(rs[2].scores.find(s=>s.modelId==='candidate'&&s.benchmarkId==='known-False')?.denominator,55);
  assert.ok(rs[2].benchmarks.some(b=>b.id==='known-False-seed-1729'));
 }finally{f.dispose();}
});
test('final report separates all-item accuracy, known retention, completion and user-stopped coverage',()=>{
 const f=fixture();try{const r=buildRepairReports(f.root).at(-1)!;
  const scores=r.scores.filter(s=>s.modelId==='candidate');
  assert.equal(scores.find(s=>s.benchmarkId==='held_eval-False')?.value,22/32);
  assert.equal(scores.find(s=>s.benchmarkId==='held_eval-False-known')?.value,17/24);
  assert.equal(r.tests.find(t=>t.id==='candidate-completion-True')?.status,'fail');
  assert.equal(scores.find(s=>s.benchmarkId==='collection')?.value,512/2400);
  assert.match(scores.find(s=>s.benchmarkId==='collection')!.notes,/511 valid; 1 invalid; 1888 not recorded/);
  const collection=r.tests.find(t=>t.id==='candidate-collection')!;assert.equal(collection.status,'not_run');assert.equal(collection.required,false);assert.equal(collection.observed,null);
  assert.equal(r.benchmarks.find(b=>b.id==='collection')?.threshold,null);
  assert.equal(scores.find(s=>s.benchmarkId==='collection')?.diagnostics?.[0].code,'USER_STOP_ON_REVIEWED_NEGATIVE');
  assert.equal(r.tests.find(t=>t.id==='candidate-note-stability')?.status,'fail');
  assert.equal(r.tests.find(t=>t.id==='candidate-validation')?.status,'pass');
 }finally{f.dispose();}
});
test('incomplete review, changed evidence, cohort mismatch and raw coverage mismatch refuse publication',()=>{
 for(const kind of ['review','hash','cohort','coverage','bank','stop']){const f=fixture();try{
  if(kind==='review')f.put(G+'/final_reviewed_verdict_v1.json',{passed:false,exact_flag_and_sample_coverage_verified:false});
  if(kind==='hash')f.put(W+'/reviewed_comparison_v1.json',{full_response_review_complete:true,review_sources:{[W+'/retention_comparison.json']:'0'.repeat(64)}});
  if(kind==='cohort'){const d=f.read(L+'/comparison_v1.json');d.retention_models.candidate.value_retention.by_mode_seed['False/42'].known_n=54;f.put(L+'/comparison_v1.json',d);}
  if(kind==='coverage')f.put(P+'ethics_gpu_base_reasoning_final_reading_s42_v1/partial_collection_status_v1.json',{recorded_natural:2400,valid_natural:2400});
  if(kind==='bank'){writeFileSync(join(f.root,P+'ethics_gpu_vllm_base_v1/stance_controls.jsonl'),'{}\n');}
  if(kind==='stop')f.put(F+'/user_stop_on_negative_v1.json',{status:'RUNNING',scientific_verdict:'pending'});
  assert.throws(()=>buildRepairReports(f.root),({review:/Reviewed final/,hash:/Review source changed/,cohort:/Matched cohort/,coverage:/Coverage disagrees/,bank:/Frozen control bank/,stop:/Explicit reviewed stop/} as Record<string,RegExp>)[kind],kind);
 }finally{f.dispose();}}
});
