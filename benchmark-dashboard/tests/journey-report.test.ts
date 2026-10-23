import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateReport} from '../server/validate-report.ts';
const template=JSON.parse(readFileSync(new URL('../examples/report-template.json',import.meta.url),'utf8'));
const content=JSON.parse(readFileSync(new URL('../examples/overnight-journey.content.json',import.meta.url),'utf8'));
function report(){return {...structuredClone(template),journey:{...structuredClone(content),phases:content.phases.map(({sourceNotes,...p}:{sourceNotes:string[]})=>({...p,sources:sourceNotes.map(path=>({path,sha256:'a'.repeat(64)}))}))}};}
test('journey supports a custom narrative without changing ordinary reports',()=>{
 assert.ok(validateReport(template).report);
 const r=report();assert.deepEqual(validateReport(r).errors,[]);
 assert.equal(r.journey.phases.length,9);
 assert.ok(r.journey.phases.find((p:{id:string})=>p.id==='reasoning').result.includes('canceled'));
});
test('journey rejects duplicate phases and unsupported status',()=>{
 const r=report();r.journey.phases[1].id=r.journey.phases[0].id;
 assert.ok(validateReport(r).errors.some(e=>e.includes('Duplicate journey phase')));
 r.journey.phases[1].id='new';r.journey.phases[1].status='qualified';assert.equal(validateReport(r).report,undefined);
});
test('journey requires evidence and cannot smuggle raw HTML fields',()=>{
 const r=report();r.journey.phases[0].sources=[];assert.equal(validateReport(r).report,undefined);
 const other=report();other.journey.html='<script/>';assert.equal(validateReport(other).report,undefined);
});
