import { useState } from 'react';
import { DiagnosticDetails } from './DiagnosticDetails';
import { testDiagnostics } from '../diagnostics';
import { ControlCharts } from './ControlCharts';
import { ModelPill } from './ModelPill';
import { formatScore } from '../report-types';
import type { ReportBenchmark, ReportModel, ReportScore, ReportTest, ModelCheckGroup } from '../report-types';

type Props = { models: ReportModel[]; benchmarks: ReportBenchmark[]; scores: ReportScore[]; tests: ReportTest[] };
const recorded = (value: ReportTest['expected']) => value === null ? 'Not recorded' : typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value);

const groups: {id:ModelCheckGroup;name:string;description:string}[]=[
 {id:'instrument',name:'Instrument checks',description:'Known-answer correctness, required formatting, irrelevant-note stability and reply coverage check the measurement procedure.'},
 {id:'consistency',name:'Response consistency',description:'Agreement across answer order, wording and negation describes response stability. Natural ethical consistency has no passing threshold.'},
 {id:'learning',name:'Learning checks',description:'Recall and code lookup test retrieval of the neutral facts taught during the development pilot; supplied-prefix continuation is an easier diagnostic.'},
 {id:'retention',name:'Retention checks',description:'Accuracy, formatting and normal completion on fixed BASE-known tasks test whether demonstrated skills survived training.'},
 {id:'engineering',name:'Engineering checks',description:'Training updates and checkpoint reload checks test the pipeline. Boolean gate results remain in the recorded details.'},
];
/** Recorded gates remain separate from numeric threshold comparisons. */
export function ReportControls({models,benchmarks:allBenchmarks,scores,tests:allTests}:Props) {
 const [group,setGroup]=useState<ModelCheckGroup|'all'>('all');
 const benchmarkGroup=(b:ReportBenchmark)=>b.checkGroup??(b.threshold?'instrument':null);
 const benchmarks=allBenchmarks.filter(b=>group==='all'||benchmarkGroup(b)===group);
 const tests=allTests.filter(t=>group==='all'||(t.checkGroup??'instrument')===group);
 const ranged=benchmarks.filter(b=>b.threshold);
 const groupTests=(id:ModelCheckGroup)=>allTests.map(t=>({...t,measurements:(t.measurements??[]).filter(m=>(m.checkGroup??t.checkGroup??'instrument')===id)}));
 return <section className="control-results" aria-label="Model checks">
  <h3>Model checks</h3>
  <p>These checks are separate from experimental control arms such as off-topic and C4 SFT. Only measurements recorded for this report’s models are shown; checks from another experiment are not substituted. Open “Why?” beside a result for its code, evidence and next investigation step.</p>
  {!tests.length&&!ranged.length&&<p>No controls or passing ranges recorded for the selected models.</p>}
  <div className="model-check-groups" role="group" aria-label="Model check groups"><button aria-pressed={group==='all'} onClick={()=>setGroup('all')}>All groups</button>{groups.map(g=><button key={g.id} aria-pressed={group===g.id} onClick={()=>setGroup(g.id)}>{g.name}</button>)}</div>
  {groups.filter(g=>group==='all'||g.id===group).map(g=>{
   const bs=allBenchmarks.filter(b=>benchmarkGroup(b)===g.id),ts=groupTests(g.id);
   const hasData=bs.length>0||ts.some(t=>t.measurements!.length)||allTests.some(t=>(t.checkGroup??'instrument')===g.id);
   if(group==='all'&&!hasData)return null;
   return <section className="model-check-group" key={g.id}><h3>{g.name}</h3><p>{g.description}</p><ControlCharts models={models} benchmarks={bs} scores={scores} tests={ts}/>{!hasData&&<p>No {g.name.toLowerCase()} are recorded in this report.</p>}</section>;
  })}
  <details className="control-detail-tables"><summary>Recorded results and source details</summary>
  {models.map(model=>{
   const checks=tests.filter(t=>t.modelId===model.id);
   const measured=ranged.filter(b=>scores.some(s=>s.modelId===model.id&&s.benchmarkId===b.id));
   return <section className="control-model" key={model.id}>
    <ModelPill model={model} color={model.color??'#377867'}/>
    {!checks.length&&!measured.length?<p>No controls recorded for this model in this report.</p>:<>
     {!!measured.length&&<div className="table-scroll"><table className="matrix control-table"><caption>Numeric passing ranges</caption><thead><tr><th>Measure</th><th>Passing range</th><th>Observed</th><th>Range check</th></tr></thead><tbody>{measured.map(b=>{
      const s=scores.find(s=>s.modelId===model.id&&s.benchmarkId===b.id)!;
      const t=b.threshold!;
      const pass=s.value==null?null:t.operator==='gte'?s.value>=t.value:s.value<=t.value;
      return <tr key={b.id}><th>{b.name}<small>{b.conditions}</small></th><td>{t.operator==='gte'?'≥':'≤'} {formatScore(t.value,b.unit,b.unitLabel)}</td><td>{s.value==null?'Incomplete / not measured':formatScore(s.value,b.unit,b.unitLabel)}</td><td><span className={`test-badge ${pass===null?'not_run':pass?'pass':'fail'}`}>{pass===null?'Unassessed':pass?'Within range':'Outside range'}</span></td></tr>;
     })}</tbody></table></div>}
     {!!checks.length&&<div className="table-scroll"><table className="matrix control-table"><caption>Recorded gates and checks</caption><thead><tr><th>Control</th><th>Passing range / requirement</th><th>Observed</th><th>Recorded result</th></tr></thead><tbody>{checks.map(t=><tr key={t.id}><th>{t.name}<small>{t.required?'Required':'Diagnostic'}</small></th><td>{t.expected===true?'All declared criteria must pass':recorded(t.expected)}<small>{t.description}</small></td><td>{recorded(t.observed)}</td><td><span className={`test-badge ${t.status}`}>{t.status.replace('_',' ')}</span><DiagnosticDetails issues={testDiagnostics(t)}/>{t.source&&<details className="control-source"><summary>Source</summary><code>{t.source.path}</code><code>SHA-256: {t.source.sha256??'Not recorded'}</code></details>}</td></tr>)}</tbody></table></div>}
    </>}
   </section>;
  })}
  </details>
 </section>;
}
