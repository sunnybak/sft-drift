import test from 'node:test';
import assert from 'node:assert/strict';
import { aggregatePilot } from '../scripts/ethical-pilot-report.ts';
import type { PilotRow } from '../scripts/ethical-pilot-report.ts';
import { scoreChange, formatChange } from '../src/report-types.ts';
const row=(seed:number,value:number|null,complete=true):PilotRow=>({arm:'positive',seed,belief_id:'claim',group:'target',stance_score:value,base_stance_score:.6,complete,diagnostics:{n_expected:24,n_extracted:complete?24:value===null?0:23},base_diagnostics:{complete:true}});
test('aggregate matches equal seed weights and matching BASE',()=>{
 const result=aggregatePilot([row(42,.8),row(7,.4),row(1729,.3)],'positive',['claim'],[42,7,1729]);
 assert.ok(Math.abs(result.value!-.5)<1e-12);assert.equal(result.base,.6);assert.equal(result.valid,72);
 assert.ok(Math.abs(scoreChange(result.value,result.base)!+.1)<1e-12);
});
test('incomplete or absent seed blocks the pooled score without erasing available seed',()=>{
 const rows=[row(42,.8),row(7,.4),row(1729,null,false)];
 assert.equal(aggregatePilot(rows,'positive',['claim'],[42,7,1729]).value,null);
 assert.equal(aggregatePilot(rows,'positive',['claim'],[42]).value,.8);
 assert.equal(aggregatePilot(rows.slice(0,2),'positive',['claim'],[42,7,1729]).value,null);
 const invalid=[row(42,.8,false)];assert.equal(aggregatePilot(invalid,'positive',['claim'],[42]).value,null);
});
test('duplicate rows cannot fill a missing belief or seed',()=>{
 assert.equal(aggregatePilot([row(42,.8),row(42,.8)],'positive',['claim'],[42,7]).value,null);
});
test('signed display retains zero and never converts missing data into zero',()=>{
 assert.equal(scoreChange(0,.6),-.6);assert.equal(scoreChange(.6,.6),0);
 assert.equal(scoreChange(null,.6),null);assert.equal(scoreChange(.6,null),null);
 assert.equal(formatChange(-.06,'fraction'),'-6.0 pp');
 assert.equal(formatChange(.089,'fraction'),'+8.9 pp');
});
