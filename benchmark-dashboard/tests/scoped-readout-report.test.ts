import test from 'node:test';
import assert from 'node:assert/strict';
import {scopedReadoutReport} from '../scripts/scoped-readout-report.ts';
import {validateReport} from '../server/validate-report.ts';
import type {BenchmarkReportData} from '../src/report-types.ts';
const arms=['base','positive','negative','offtopic','c4_only'];
function fixture(){
 const original:BenchmarkReportData={schemaVersion:'1.0',id:'old',title:'Historical',description:'Historical',createdAt:'2026-10-21T00:00:00Z',tags:[],context:'Original failures unchanged',models:arms.map(id=>({id,name:id,provider:'Qwen',model:'Qwen/Qwen3-4B',revision:'pinned',variant:'unknown',inference:{},finetuning:null})),benchmarks:[],scores:[],tests:[],sources:[]};
 const cell=()=>({value:.5,complete:true,valid:24,expected:24,lower:.5,upper:.5,eligible_under_forward_policy:true,eligibility_codes:[]});
 const models=Object.fromEntries(arms.map(a=>[a,{endpoints:Object.fromEntries(['all','target','untrained_ethical','related_untrained','other_untrained_ethical','offtopic_eval'].map(id=>[id,cell()])),agreement:Object.fromEntries(['order','wording','negation'].map(id=>[id,{rate_over_eligible:.8,eligible:100,expected:100,agreeing:80}]))}]));
 const analysis={complete:true,policy_id:'scoped_stance_readout_v1',run_id:'ethics_gpu_scoped_readout_v1',interpretation:'One seed; no training replication.',models};
 const cells=arms.flatMap(model=>Array.from({length:100},(_,i)=>({model,belief_id:'belief'+i,...cell()})));
 const proofs=Object.fromEntries(arms.map(a=>[a,{splits:Object.fromEntries(['development','validation'].map(id=>[id,{passed:true,counts:{accuracy:1,strict:384,valid:384,expected:384},note_comparison:{disagreement_rate:0}}]))}]));
 const retention={models:Object.fromEntries(arms.map(a=>[a,{by_seed:Object.fromEntries(['42','7','1729'].map(seed=>[seed,{known_retention_passed:a==='base',by_mode:{False:{known_n:44,known:{semantic_correct:a==='base'?44:43,strict_format:a==='base'?44:43}}}}]))}]))};
 const arithmetic:BenchmarkReportData={...original,id:'arithmetic',benchmarks:[{id:'original-accuracy',name:'Arithmetic correctness',description:'Known arithmetic truth',category:'Correctness',unit:'fraction',direction:'higher',range:{min:0,max:1},threshold:{operator:'gte',value:.95},conditions:'Separate control study',examples:[]}],scores:arms.map(modelId=>({modelId,benchmarkId:'original-accuracy',value:.8,numerator:8,denominator:10,notes:'Failed',source:null})),tests:arms.map(modelId=>({id:modelId+'-original',modelId,benchmarkId:null,name:'Arithmetic',description:'Historical arithmetic gate',required:true,status:'fail',expected:true,observed:false,source:null}))};
 const sources=[0,1,2].map(i=>({path:'source'+i,sha256:'a'.repeat(64)}));
 return {original,analysis,cells,proofs,retention,sources,arithmetic};
}
function build(f=fixture()){return scopedReadoutReport(f.original,f.analysis,f.cells,f.proofs,f.retention,f.sources,'2026-10-21T00:00:00Z',f.arithmetic);}
test('all models and beliefs remain visible; historical failures remain separate',()=>{
 const f=fixture(),before=JSON.stringify(f),report=build(f);
 assert.equal(JSON.stringify(f),before);
 assert.equal(report.models.length,5);
 assert.equal(report.scores.filter(s=>s.benchmarkId.startsWith('belief')).length,500);
 assert.equal(report.tests.filter(t=>t.required&&t.status==='pass').length,40);
 assert.equal(report.tests.filter(t=>t.name.startsWith('Separate arithmetic')&&t.status==='fail'&&!t.required).length,5);
 assert.equal(report.tests.filter(t=>t.checkGroup==='retention'&&t.status==='fail').length,12);
 assert.deepEqual(validateReport(report).errors,[]);
});
test('incomplete but eligible endpoint keeps bounds and no invented point/counts',()=>{
 const f=fixture(),c=f.analysis.models.offtopic.endpoints.all;
 Object.assign(c,{complete:false,value:null,valid:2399,expected:2400,lower:.49,upper:.491});
 const report=build(f),score=report.scores.find(s=>s.modelId==='offtopic'&&s.benchmarkId==='all')!;
 assert.equal(score.value,null);assert.equal(score.numerator,null);assert.equal(score.denominator,null);
 assert.deepEqual(score.bounds,{lower:.49,upper:.491,kind:'missing_data'});
 assert.equal(score.diagnostics?.[0].code,'INCOMPLETE_EVAL_GRID');
 assert.equal(report.tests.find(t=>t.id==='offtopic-eligibility-all')?.status,'pass');
 assert.deepEqual(validateReport(report).errors,[]);
});
test('failed eligibility does not erase observed scores or hide the reason',()=>{
 const f=fixture();Object.assign(f.analysis.models.negative.endpoints.target,{eligible_under_forward_policy:false,eligibility_codes:['SCOPED_CONTROL_FAILURE']});
 const report=build(f),score=report.scores.find(s=>s.modelId==='negative'&&s.benchmarkId==='target')!;
 assert.equal(score.value,.5);assert.equal(score.diagnostics?.[0].code,'SCOPED_CONTROL_FAILURE');
 assert.equal(report.tests.find(t=>t.id==='negative-eligibility-target')?.status,'fail');
});
test('partial, missing models, duplicate/missing beliefs and absent repeats cannot publish',()=>{
 let f=fixture();f.analysis.complete=false;assert.throws(()=>build(f),/complete/);
 f=fixture();delete f.analysis.models.offtopic;assert.throws(()=>build(f),/five models/);
 f=fixture();f.cells[0]=f.cells[1];assert.throws(()=>build(f),/all100/);
 f=fixture();delete f.retention.models.base.by_seed['7'];assert.throws(()=>build(f),/retention repeat/);
});
