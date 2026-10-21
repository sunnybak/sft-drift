import test from 'node:test';
import assert from 'node:assert/strict';
import { coverageDiagnostics, thresholdDiagnostic, observationDiagnostic } from '../scripts/report-diagnostics.ts';
import { scoreDiagnostics, testDiagnostics, comparisonDiagnostics } from '../src/diagnostics.ts';
const source={path:'data/results/run/measurement_summary.json',sha256:null};
const row={seed:42,belief_id:'claim',complete:false,diagnostics:{n_expected:24,n_extracted:23,n_length_limited:1},source_path:source.path};
test('token limit and incomplete extraction are distinct from a control-gated skip',()=>{
 const issues=coverageDiagnostics([row],24,23,new Map());
 assert.deepEqual(issues.map(i=>i.code),['GENERATION_TOKEN_LIMIT','REPLY_MISSING_OR_INVALID','INCOMPLETE_EVAL_GRID']);
 assert.equal(issues.at(-1)!.context!.missing,1);
 const skipped=coverageDiagnostics([{...row,seed:1729,diagnostics:{n_expected:24,n_extracted:0}}],24,0,new Map([[1729,source]]));
 assert.deepEqual(skipped.map(i=>i.code),['EVAL_SKIPPED_CONTROL_GATE','INCOMPLETE_EVAL_GRID']);
 assert.equal(skipped[0].sources![0].path,source.path);
});
test('zero extracted replies alone never establish that the control gate skipped collection',()=>{
 const issues=coverageDiagnostics([{...row,diagnostics:{n_expected:24,n_extracted:0}}],24,0,new Map());
 assert.ok(!issues.some(i=>i.code==='EVAL_SKIPPED_CONTROL_GATE'));
});
test('exact criterion boundary passes; note flip failures preserve observed and required values',()=>{
 assert.deepEqual(thresholdDiagnostic('NOTE_FLIP_RATE_ABOVE_MAXIMUM','Flips',.05,'lte',.05,[source]),[]);
 const issue=thresholdDiagnostic('NOTE_FLIP_RATE_ABOVE_MAXIMUM','Flips',.0625,'lte',.05,[source])[0];
 assert.equal(issue.context!.observed,.0625);assert.equal(issue.context!.threshold,.05);
});
test('absent report entry differs from a recorded missing result and valid zero',()=>{
 assert.equal(scoreDiagnostics(undefined)[0].code,'MEASUREMENT_NOT_IN_REPORT');
 const score={modelId:'base',benchmarkId:'all',value:null,numerator:null,denominator:null,notes:'',source};
 assert.equal(scoreDiagnostics(score)[0].code,'MEASUREMENT_UNAVAILABLE');
 assert.deepEqual(scoreDiagnostics({...score,value:0}),[]);
});
test('unknown failure cause remains unknown rather than manufacturing a model diagnosis',()=>{
 const issue=testDiagnostics({id:'test',modelId:'base',benchmarkId:null,name:'Qualification',description:'',required:true,status:'fail',expected:true,observed:false,source})[0];
 assert.equal(issue.code,'CHECK_FAILED_CAUSE_UNSPECIFIED');
 assert.match(issue.message,/does not provide/);
});

test('missing BASE can block change without implying missing fine-tuned scores or mutating evidence',()=>{
 const score={modelId:'ft',benchmarkId:'all',value:.5,numerator:null,denominator:null,notes:'',source,diagnostics:[]};
 const issues=comparisonDiagnostics(score,undefined,true);assert.equal(issues[0].code,'BASE_REFERENCE_UNAVAILABLE');
 assert.deepEqual(score.diagnostics,[]);assert.deepEqual(comparisonDiagnostics(score,undefined,false),[]);
});

test('raw observations distinguish normal-stop format failure, token caps and backend errors',()=>{
 const raw={presentation_id:'claim/w3/positive/1',belief_id:'claim',answer:null,final_response:'I reject the target statement.',answer_extraction:'stance_word_unavailable',error:'unavailable answer extraction',generation_metadata:{finish_reason:'stop',generation_tokens:12}};
 const format=observationDiagnostic(raw,source)!;assert.equal(format.code,'FINAL_ANSWER_FORMAT_INVALID');assert.equal(format.context!.final_response,raw.final_response);
 const limited=observationDiagnostic({...raw,final_response:null,generation_metadata:{finish_reason:'length',generation_tokens:4096}},source)!;
 assert.equal(limited.code,'GENERATION_TOKEN_LIMIT');assert.equal(limited.context!.generation_tokens,4096);
 assert.equal(observationDiagnostic({...raw,generation_metadata:{backend_error:'transport failure'}},source)!.code,'BACKEND_INFERENCE_ERROR');
 assert.equal(observationDiagnostic({...raw,answer:'reject'},source),null);
});
