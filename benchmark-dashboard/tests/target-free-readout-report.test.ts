import test from 'node:test';
import assert from 'node:assert/strict';
import {targetFreeReadoutReport} from '../scripts/target-free-readout-report.ts';
import {validateReport} from '../server/validate-report.ts';
import type {BenchmarkReportData} from '../src/report-types.ts';
const arms=['base','positive','negative','offtopic','c4_only'],seeds=['42','7','1729'];
function fixture(){
 const original:BenchmarkReportData={schemaVersion:'1.0',id:'historical',title:'Historical',description:'Unchanged',createdAt:'2026-10-22T00:00:00Z',tags:[],context:'Old results',models:arms.map(id=>({id,name:id,provider:'Qwen',model:'Qwen/Qwen3-4B',revision:'pinned',variant:'unknown',inference:{},finetuning:null})),benchmarks:[],scores:[],tests:[],sources:[]};
 const endpoint=(expected=3600)=>({expected,valid:expected,missing:0,known_support:expected/2,value:.5,lower:.5,upper:.5,complete:true,strict:expected,caps:0,bound_width:0,precision_passed:true,base:{bound_width:0,precision_passed:true}});
 const agreement=()=>({expected:100,eligible:100,agreeing:80,rate_over_eligible:.8});
 const split=()=>({overall:{extraction_rate:1,strict_rate:1,normal_stop_rate:1},domains:Object.fromEntries(['normative','factual','arithmetic','scope_logic'].map(id=>[id,{accuracy_over_expected:1}])),note_comparison:{flip_upper:0},operational_passed:true,strict_passed:true,error_codes:[] as string[]});
 const groupIds=['all','target','untrained_ethical','related_untrained','other_untrained_ethical','offtopic_eval'];
 const models=Object.fromEntries(arms.map(arm=>[arm,{complete_seeds:true,seeds:Object.fromEntries(seeds.map(seed=>[seed,{controls_passed:true,base_controls_passed:true,endpoints:Object.fromEntries(groupIds.map(id=>[id,endpoint(1200)])),model_checks:{splits:{development:split(),validation:split()},stress:{all_correct:true,correct:8,expected:8,extracted:8}}}])),pooled_completed_seeds:Object.fromEntries(groupIds.map(id=>[id,endpoint()])),same_prompt:agreement(),within_prompt:{order:agreement(),wording:agreement()}}]));
 const analysis={complete:true,pending:[] as string[],policy_id:'target_free_error_budget_v2',run_id:'ethics_gpu_target_free_readout_v2',interpretation:'Relative choices, not confidence or moral accuracy. Three evaluation seeds, not training replication.',primary_aggregate_groups:['all','target','untrained_ethical','offtopic_eval'],models};
 const cells=arms.flatMap(model=>Array.from({length:100},(_,i)=>({model,belief_id:'belief'+i,complete_seeds:true,evaluation_seeds:[42,7,1729],...endpoint(36)})));
 const beliefs=Object.fromEntries(Array.from({length:100},(_,i)=>['belief'+i,{statement:'Claim '+i,scope:'Scope '+i}]));
 const review={preselected_review_complete:true,preselected_reviewed:72,all_failed_controls_reviewed:true,reviewed_jobs:15,interpretation:'Semantic clearance is not established.'};
 return {original,analysis,cells,review,beliefs,sources:[{path:'analysis.json',sha256:'a'.repeat(64)},{path:'reviewed_assessment.json',sha256:'b'.repeat(64)}]};
}
function build(f=fixture()){return targetFreeReadoutReport(f.original,f.analysis,f.cells,f.review,f.beliefs,f.sources,'2026-10-22T00:00:00Z');}
test('full five-model surface and repeatability publish without changing source data',()=>{
 const f=fixture(),before=JSON.stringify(f),r=build(f);assert.equal(JSON.stringify(f),before);
 assert.equal(r.models.length,5);assert.equal(r.scores.filter(s=>s.benchmarkId.startsWith('belief')).length,500);
 assert.ok(r.models.every(m=>JSON.stringify(m.inference.seeds)==='[42,7,1729]'));
 assert.equal(r.benchmarks.find(b=>b.id==='belief99')?.description,'Claim 99 Scope: Scope 99');
 assert.ok(r.benchmarks.some(b=>b.id==='agreement-same_prompt'));assert.ok(!r.benchmarks.some(b=>b.id==='agreement-negation'));
 assert.equal(r.tests.filter(t=>t.required).length,45);assert.deepEqual(validateReport(r).errors,[]);
});
test('failed model checks stay visible without hiding measured choices',()=>{
 const f=fixture(),v=f.analysis.models.negative.seeds['7'];v.controls_passed=false;
 v.model_checks.splits.validation.operational_passed=false;v.model_checks.splits.validation.domains.scope_logic.accuracy_over_expected=.9;v.model_checks.splits.validation.error_codes=['CONTROL_DOMAIN_ACCURACY_BELOW_95'];
 const r=build(f),s=r.scores.find(s=>s.modelId==='negative'&&s.benchmarkId==='target')!;
 assert.equal(s.value,.5);assert.equal(s.diagnostics?.[0].code,'MODEL_CHECKS_LIMIT_INTERPRETATION');
 const t=r.tests.find(t=>t.id==='negative-7-validation')!;assert.equal(t.status,'fail');
 assert.deepEqual(t.measurements?.find(m=>m.id==='7-validation/scope_logic-accuracy')?.threshold,{operator:'gte',value:.95});
 assert.equal(t.diagnostics?.[0].code,'CONTROL_DOMAIN_ACCURACY_BELOW_95');assert.deepEqual(validateReport(r).errors,[]);
});
test('missing replies retain null point scores and missing-data bounds',()=>{
 const f=fixture(),c=f.cells.find(c=>c.model==='offtopic')!;Object.assign(c,{complete:false,value:null,valid:35,missing:1,lower:18/36,upper:19/36,strict:35});
 const r=build(f),s=r.scores.find(s=>s.modelId==='offtopic'&&s.benchmarkId===c.belief_id)!;
 assert.equal(s.value,null);assert.equal(s.numerator,null);assert.deepEqual(s.bounds,{lower:18/36,upper:19/36,kind:'missing_data'});assert.equal(s.diagnostics?.[0].code,'INCOMPLETE_EVAL_GRID');assert.deepEqual(validateReport(r).errors,[]);
});
test('partial measurements, missing repeats and incomplete reviews refuse publication',()=>{
 let f=fixture();f.analysis.complete=false;assert.throws(()=>build(f),/Complete target-free/);
 f=fixture();f.analysis.pending=['pending'];assert.throws(()=>build(f),/Complete target-free/);
 f=fixture();delete f.analysis.models.c4_only.seeds['1729'];assert.throws(()=>build(f),/five models and three seeds/);
 f=fixture();f.review.reviewed_jobs=14;assert.throws(()=>build(f),/raw-response review/);
 f=fixture();f.cells[0]=f.cells[1];assert.throws(()=>build(f),/500/);
 f=fixture();delete f.beliefs.belief99;assert.throws(()=>build(f),/500/);
});
test('stress, strict-format and operational criteria are separate recorded checks',()=>{
 const f=fixture(),c=f.analysis.models.c4_only.seeds['42'];c.model_checks.stress={all_correct:false,correct:7,expected:8,extracted:7};c.model_checks.splits.validation.strict_passed=false;
 const r=build(f);assert.equal(r.tests.find(t=>t.id==='c4_only-42-stress')?.status,'fail');assert.equal(r.tests.find(t=>t.id==='c4_only-42-stress')?.required,false);assert.equal(r.tests.find(t=>t.id==='c4_only-42-validation-strict')?.status,'fail');assert.equal(r.tests.find(t=>t.id==='c4_only-42-validation')?.status,'pass');assert.deepEqual(validateReport(r).errors,[]);
});
