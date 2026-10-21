import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync, mkdtempSync, writeFileSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { validateReport } from '../server/validate-report.ts';
import { loadReports } from '../server/report-loader.ts';
import { checkSummary, formatScore, reportPriority } from '../src/report-types.ts';
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
test('authored readouts must reference real models and benchmarks',()=>{
 const r=template();r.presentation={focusModelId:'absent',referenceModelId:'example-model',headline:'Readout',interpretation:'Evidence',nextStep:'Next',highlights:[{benchmarkId:'absent',label:'Key score',explanation:'Interpretation'}]};
 const errors=validateReport(r).errors.join(' ');
 assert.match(errors,/Presentation references unknown model/);assert.match(errors,/Presentation references unknown benchmark/);
});
test('candidate gates are scoped separately from historical models',()=>{
 const r=template(),old={...r.tests[0],id:'old-failure',modelId:'old',status:'fail'};
 assert.equal(checkSummary([...r.tests,old].filter(t=>t.modelId==='example-model')).status,'Declared checks passed');
 assert.equal(checkSummary([old]).status,'Required checks failed');
});

test('readouts prioritize current blockers without importing historical failures',()=>{
 const r=template();r.presentation={focusModelId:'example-model',referenceModelId:'example-model',headline:'Readout',interpretation:'Evidence',nextStep:'Next',highlights:[{benchmarkId:'uppercase',label:'Key score',explanation:'Meaning'}]};
 r.tests.push({...r.tests[0],id:'historical',modelId:'old',status:'fail'});assert.equal(reportPriority(r),0);
 r.tests[0].status='not_run';assert.equal(reportPriority(r),2);r.tests[0].status='fail';assert.equal(reportPriority(r),3);
});
test('scientific model context is optional but complete when supplied',()=>{
 const r=template();
 r.models[0].studyContext={purpose:'Learning pilot',intervention:'Remove marker',data:'Matched corpus',comparison:'Reference and matched variant',limitations:'Reused development examples'};
 assert.ok(validateReport(r).report);
 delete r.models[0].studyContext.limitations;
 assert.match(validateReport(r).errors.join(' '),/limitations/);
});

test('comparison defaults validate and category must exist',()=>{
 const r=template();r.presentation={focusModelId:'example-model',referenceModelId:'example-model',headline:'Change',interpretation:'Signed movement',nextStep:'Inspect',highlights:[{benchmarkId:'uppercase',label:'Score',explanation:'Recorded'}],defaultMetric:'change',defaultCategory:r.benchmarks[0].category};
 assert.ok(validateReport(r).report);
 r.presentation.defaultCategory='absent';assert.match(validateReport(r).errors.join(' '),/unknown category/);
 r.presentation.defaultCategory=r.benchmarks[0].category;r.presentation.defaultMetric='typo';assert.ok(validateReport(r).errors.length);
});

test('missing-response bounds retain null point scores and declared units',()=>{
 const r=template();const s=r.scores[0];s.value=null;s.numerator=null;s.denominator=null;s.bounds={lower:.5,upper:.51,kind:'missing_data'};
 assert.ok(validateReport(r).report);
 s.bounds.upper=1.1;assert.match(validateReport(r).errors.join(' '),/Invalid missing-data bounds/);
 s.bounds.upper=.51;s.value=.505;assert.match(validateReport(r).errors.join(' '),/point score/);
});

test('optional experiment identity is compatible with old reports and requires a name and id',()=>{
 const r=template();assert.ok(validateReport(r).report);
 r.experiment={id:'four-arm',name:'Four-arm ethical-stance pilot'};assert.ok(validateReport(r).report);
 r.experiment.name='';assert.ok(validateReport(r).errors.length);
 delete r.experiment.name;assert.ok(validateReport(r).errors.length);
});

test('control measurements preserve missing values and enforce fraction ranges',()=>{
 const r=template();r.tests[0].measurements=[{id:'accuracy',name:'Control accuracy',value:null,threshold:{operator:'gte',value:.95}}];
 assert.ok(validateReport(r).report);
 r.tests[0].measurements[0].value=0;assert.ok(validateReport(r).report);
 r.tests[0].measurements[0].value=1.1;assert.ok(validateReport(r).errors.length);
 r.tests[0].measurements[0].value=1;r.tests[0].measurements[0].threshold.value=95;assert.ok(validateReport(r).errors.length);
});

test('models cannot silently share conflicting control definitions or duplicate measurements',()=>{
 const r=template();const m={id:'accuracy',name:'Accuracy',value:1,threshold:{operator:'gte',value:.95}};
 r.tests[0].measurements=[m];const other={...r.tests[0],id:'other-check',measurements:[{...m,threshold:{operator:'gte',value:.9}}]};r.tests.push(other);
 assert.match(validateReport(r).errors.join(' '),/Conflicting control measurement definition/);
 other.measurements=[m];assert.match(validateReport(r).errors.join(' '),/Duplicate model\/control measurement/);
});
