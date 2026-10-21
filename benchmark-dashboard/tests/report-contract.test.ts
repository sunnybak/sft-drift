import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync, mkdtempSync, writeFileSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { validateReport } from '../server/validate-report.ts';
import { loadReports } from '../server/report-loader.ts';
import { checkSummary, formatScore } from '../src/report-types.ts';
const template = () => JSON.parse(readFileSync(new URL('../examples/report-template.json', import.meta.url), 'utf8'));
test('portable template validates',()=>assert.ok(validateReport(template()).report));
test('unknown model and benchmark references fail',()=>{
 const r=template();r.scores[0].modelId='absent';r.tests[0].benchmarkId='absent';
 assert.match(validateReport(r).errors.join(' '),/unknown model\/benchmark/);
});
test('counts and score cannot disagree',()=>{
 const r=template();r.scores[0].value=.5;assert.match(validateReport(r).errors.join(' '),/disagrees/);
});
test('measured zero and unmeasured remain distinct',()=>{
 const r=template();r.scores[0].value=0;r.scores[0].numerator=0;assert.ok(validateReport(r).report);
 r.scores[0].value=null;r.scores[0].numerator=null;r.scores[0].denominator=null;assert.ok(validateReport(r).report);
 r.scores[0].denominator=2;assert.ok(validateReport(r).errors.length);
});
test('duplicate measurements and unknown schema fields fail',()=>{
 const r=template();r.scores.push({...r.scores[0]});assert.match(validateReport(r).errors.join(' '),/Duplicate score/);
 r.unexpected='typo';assert.match(validateReport(r).errors.join(' '),/additional properties/);
});
test('fine-tune provenance cannot be silently omitted',()=>{
 const r=template();r.models[0].finetuning=null;assert.match(validateReport(r).errors.join(' '),/requires finetuning/);
});
test('required not-run and error never pass; no tests is not assessed',()=>{
 const r=template();r.tests[0].status='not_run';r.tests[0].observed=null;
 assert.equal(checkSummary(r.tests).status,'Checks pending');
 r.tests[0].status='error';assert.equal(checkSummary(r.tests).status,'Check errors');
 assert.equal(checkSummary([]).status,'Not assessed');
});
test('no new code is needed to load a JSON report; invalid files stay visible',()=>{
 const dir=mkdtempSync(join(tmpdir(),'benchmark-reports-'));
 try {
  writeFileSync(join(dir,'first.json'),JSON.stringify(template()));
  writeFileSync(join(dir,'bad.json'),'{');
  const second=template();second.id='second-report';writeFileSync(join(dir,'second.json'),JSON.stringify(second));
  const loaded=loadReports([dir]);assert.equal(loaded.reports.length,2);assert.equal(loaded.errors.length,1);
  writeFileSync(join(dir,'duplicate.json'),JSON.stringify(template()));
  const duplicate = loadReports([dir]);
  assert.match(duplicate.errors.map(e=>e.messages.join(' ')).join(' '),/Duplicate report id/);
  assert.equal(duplicate.reports.length,1);assert.equal(duplicate.reports[0].id,'second-report');
 } finally {rmSync(dir,{recursive:true,force:true})}
});
test('loader skips symlinks and non-JSON files',()=>{
 const dir=mkdtempSync(join(tmpdir(),'benchmark-reports-'));
 try {
  writeFileSync(join(dir,'template.txt'),JSON.stringify(template()));symlinkSync(join(dir,'template.txt'),join(dir,'linked.json'));
  assert.equal(loadReports([dir]).reports.length,0);
 } finally {rmSync(dir,{recursive:true,force:true})}
});
test('numeric lower-is-better benchmark uses its declared range',()=>{
 const r=template(),b=r.benchmarks[0];b.unit='number';b.unitLabel='ms';b.direction='lower';b.range={min:0,max:500};b.threshold={operator:'lte',value:100};
 r.scores[0]={...r.scores[0],value:80,numerator:null,denominator:null};assert.ok(validateReport(r).report);
 assert.equal(formatScore(80,b.unit,b.unitLabel),'80 ms');
 r.scores[0].value=501;assert.match(validateReport(r).errors.join(' '),/outside range/);
});
