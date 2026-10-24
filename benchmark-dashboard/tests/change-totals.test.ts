import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {summedChange,formatSummedChange} from '../src/change-totals.ts';
import {validateReport} from '../server/validate-report.ts';
import type {ReportScore} from '../src/report-types.ts';
const score:ReportScore={modelId:'tuned',benchmarkId:'test',value:.5,numerator:null,denominator:null,notes:'',source:null,changeTotals:{referenceModelId:'base',beliefCount:2,signedSum:0,absoluteSum:.4}};
test('total display preserves zero, signs, magnitude and missingness',()=>{
 assert.equal(summedChange(score,'base','signed_sum'),0);assert.equal(summedChange(score,'base','absolute_sum'),.4);
 assert.equal(summedChange(score,'different-base','signed_sum'),null);assert.equal(summedChange({...score,value:null},'base','absolute_sum'),null);
 assert.equal(summedChange(undefined,'base','signed_sum'),null);
 assert.equal(formatSummedChange(-.4166667,false),'−41.7 total pp');assert.equal(formatSummedChange(.4,true),'40.0 total pp');
});
test('totals validate against the actual mean/reference and cannot hide impossible movement',()=>{
 const r=JSON.parse(readFileSync(new URL('../examples/report-template.json',import.meta.url),'utf8'));
 const base=r.models[0].id,s=r.scores[0];s.changeTotals={referenceModelId:base,beliefCount:10,signedSum:0,absoluteSum:0};
 assert.deepEqual(validateReport(r).errors,[]);
 s.changeTotals.signedSum=.1;assert.ok(validateReport(r).errors.some(e=>e.includes('Signed change total disagrees')));
 s.changeTotals.signedSum=0;s.changeTotals.absoluteSum=11;assert.ok(validateReport(r).errors.some(e=>e.includes('change total bounds')));
});
