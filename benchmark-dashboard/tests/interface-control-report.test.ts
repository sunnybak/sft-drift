import test from 'node:test';
import assert from 'node:assert/strict';
import {interfaceControlReport} from '../scripts/interface-control-report.ts';
import {validateReport} from '../server/validate-report.ts';
import type {BenchmarkReportData} from '../src/report-types.ts';
const arms=['base','positive','negative','offtopic','c4_only'];
function fixture(){
 const original:BenchmarkReportData={schemaVersion:'1.0',id:'original',title:'Old',description:'Old scores',createdAt:'2026-10-21T00:00:00Z',tags:[],context:'Historical failures unchanged',models:arms.map(id=>({id,name:id,provider:'Qwen',model:'Qwen/Qwen3-4B',revision:'pinned',variant:'unknown',inference:{oldInstrument:'retained only in old report',seeds:[42,7,1729]},finetuning:null})),benchmarks:[],scores:[],tests:[],sources:[]};
 const count=(n:number)=>({correct:n,expected:n,valid:n,strict:n});
 const split=()=>({passed:true,counts:count(192),domains:{normative:count(96),factual:count(96)},checks:{normative:true,factual:true,extraction:true,format:true,noteCoverage:true,noteFlips:true},note_comparison:{expected_pairs:64,eligible_pairs:64,disagreements:0,disagreement_rate:0}});
 const models=Object.fromEntries(arms.map(id=>[id,{run_id:'controls-'+id,forms:Object.fromEntries(['current','explicit','paired'].map(f=>[f,{development:split(),validation:split()}]))}]));
 const analysis={complete:true,pending:[],run_id:'interface-controls',models};
 const bank=['current','explicit','paired'].flatMap(form=>['development','validation'].flatMap(split=>['normative','factual'].map(domain=>({interface:form,split,domain,prompt:'Given an assigned '+domain+' reference. Choose the matching position.',expected_word:form==='paired'?'a':'endorse'}))));
 const runtime=Object.fromEntries(arms.map(id=>[id,{decoder:{thinking:true,temperature:.6},backend:{card:'fixture'}}]));
 const sources=[{path:'final-analysis.json',sha256:'a'.repeat(64)}];return {original,analysis,bank,runtime,sources};
}
function build(f=fixture()){return interfaceControlReport(f.original,f.analysis,f.bank,f.runtime,f.sources,'2026-10-21T00:00:00Z');}
test('all five models, three interfaces and both splits retain scoped gates and provenance',()=>{
 const f=fixture(),before=JSON.stringify(f),r=build(f);
 assert.equal(JSON.stringify(f),before);assert.equal(r.benchmarks.length,24);assert.equal(r.scores.length,120);assert.equal(r.tests.length,30);
 assert.equal(r.tests.filter(t=>t.required).length,10);assert.ok(r.tests.filter(t=>t.required).every(t=>t.name.startsWith('Opposing positions')));
 assert.ok(r.models.every(m=>!('oldInstrument' in m.inference)&&!('seeds' in m.inference)));
 assert.ok(r.context.includes('Historical arithmetic')&&r.context.includes('not pooled'));
 assert.deepEqual(validateReport(r).errors,[]);
 // Each chart compares models on one interface/split; no last-form overwrite.
 const ids=r.tests.filter(t=>t.modelId==='base').flatMap(t=>t.measurements!.map(m=>m.id));
 assert.equal(new Set(ids).size,12);assert.ok(ids.every(id=>!r.benchmarks.some(b=>b.id===id)));
});
test('a failed paired reference check stays failed; no fallback or score deletion',()=>{
 const f=fixture(),s=f.analysis.models.negative.forms.paired.validation;
 s.domains.normative.correct=91;s.counts.correct=187;s.checks.normative=false;s.passed=false;
 const r=build(f),t=r.tests.find(t=>t.id==='negative-paired-validation')!;
 assert.equal(t.required,true);assert.equal(t.status,'fail');assert.equal(t.diagnostics![0].code,'CONTROL_ACCURACY_BELOW_MINIMUM');
 assert.equal(r.scores.find(s=>s.modelId==='negative'&&s.benchmarkId==='paired-validation-normative')!.value,91/96);
 assert.equal(r.tests.find(t=>t.id==='negative-current-validation')!.status,'pass');assert.deepEqual(validateReport(r).errors,[]);
});
test('partial evidence, missing models/examples and impossible counts cannot publish',()=>{
 let f=fixture();f.analysis.complete=false;assert.throws(()=>build(f),/Complete/);
 f=fixture();delete f.analysis.models.offtopic;assert.throws(()=>build(f),/five/);
 f=fixture();f.bank=[];assert.throws(()=>build(f),/example/);
 f=fixture();f.analysis.models.base.forms.paired.validation.counts.strict=193;assert.throws(()=>build(f),/counts/);
});
