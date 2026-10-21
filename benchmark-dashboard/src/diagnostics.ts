import type { ReportDiagnostic, ReportScore, ReportTest, Source } from './report-types.ts';
export function missingMeasurement(recorded:boolean,source?:Source|null):ReportDiagnostic[] {
 return [{code:recorded?'MEASUREMENT_UNAVAILABLE':'MEASUREMENT_NOT_IN_REPORT',severity:recorded?'warning':'info',stage:'reporting',message:recorded?'This measurement is recorded without a numeric result. Its underlying cause is not specified here.':'This report does not include this measurement for this model. This is not a failed check.',nextStep:recorded?'Inspect the source artifact and collection log; do not infer a cause from a blank chart.':'Consult the report containing this model/check, or collect it under a new run ID if needed.',sources:source?[source]:[]}];
}
export function scoreDiagnostics(score:ReportScore|undefined):ReportDiagnostic[] {
 return score?.diagnostics?.length?score.diagnostics:score?.value==null?missingMeasurement(!!score,score?.source):[];
}
export function testDiagnostics(test:ReportTest):ReportDiagnostic[] {
 if(test.diagnostics?.length)return test.diagnostics;
 if(test.status==='pass')return [];
 return [{code:test.status==='fail'?'CHECK_FAILED_CAUSE_UNSPECIFIED':test.status==='error'?'CHECK_EXECUTION_ERROR':'CHECK_NOT_RUN',severity:test.status==='not_run'?'info':'warning',stage:'validation',message:test.status==='fail'?`The recorded check failed: ${test.name}. This report does not provide the underlying failure breakdown.`:test.status==='error'?`An execution error was recorded for ${test.name}; the specific error is not supplied.`:`${test.name} was not run.`,nextStep:'Inspect the referenced check artifact before diagnosing or changing the gate.',sources:test.source?[test.source]:[]}];
}

/** Enrich derived exports only; never reinterpret historical pass/fail decisions. */
export function addReportDiagnostics(report:import('./report-types.ts').BenchmarkReportData):void {
 for(const score of report.scores){
  const issues=scoreDiagnostics(score),benchmark=report.benchmarks.find(b=>b.id===score.benchmarkId);
  if(!issues.length&&score.value!==null&&benchmark?.threshold){
   const t=benchmark.threshold;
   if(t.operator==='gte'?score.value<t.value:score.value>t.value)issues.push({code:'THRESHOLD_NOT_MET',severity:'warning',stage:'validation',message:`${benchmark.name}: observed ${score.value}; required ${t.operator==='gte'?'at least':'at most'} ${t.value}.`,context:{model:score.modelId,observed:score.value,operator:t.operator,threshold:t.value},nextStep:'Inspect the source presentations. This criterion comparison does not establish the underlying cause or replace the recorded gate verdict.',sources:score.source?[score.source]:[]});
  }
  if(issues.length)score.diagnostics=issues;
 }
 for(const test of report.tests){const issues=testDiagnostics(test);if(issues.length)test.diagnostics=issues;}
}
export function comparisonDiagnostics(score:ReportScore|undefined,reference:ReportScore|undefined,isChange:boolean):ReportDiagnostic[]{
 const issues=[...scoreDiagnostics(score)];
 if(isChange&&reference?.value==null)issues.push({code:'BASE_REFERENCE_UNAVAILABLE',severity:'warning',stage:'reporting',message:'Change cannot be computed because the matched BASE reference is absent or incomplete. This does not mean the fine-tuned score failed.',nextStep:'Inspect the matched BASE measurement and its own diagnostics.',sources:reference?.source?[reference.source]:[]});
 return issues;
}
