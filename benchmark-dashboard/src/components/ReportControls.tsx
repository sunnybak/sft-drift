import { ControlCharts } from './ControlCharts';
import { ModelPill } from './ModelPill';
import { formatScore } from '../report-types';
import type { ReportBenchmark, ReportModel, ReportScore, ReportTest } from '../report-types';

type Props = { models: ReportModel[]; benchmarks: ReportBenchmark[]; scores: ReportScore[]; tests: ReportTest[] };
const recorded = (value: ReportTest['expected']) => value === null ? 'Not recorded' : typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value);

/** Recorded gates remain separate from numeric threshold comparisons. */
export function ReportControls({models,benchmarks,scores,tests}:Props) {
 const ranged=benchmarks.filter(b=>b.threshold);
 return <section className="control-results" aria-label="Controls and passing ranges">
  <h3>Controls and passing ranges</h3>
  <p>These are the checks recorded in this report. Passing a numeric range does not establish overall model qualification. Missing checks remain unassessed.</p>
  {!tests.length&&!ranged.length&&<p>No controls or passing ranges recorded for the selected models.</p>}
  <ControlCharts models={models} benchmarks={benchmarks} scores={scores} tests={tests}/>
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
     {!!checks.length&&<div className="table-scroll"><table className="matrix control-table"><caption>Recorded gates and checks</caption><thead><tr><th>Control</th><th>Passing range / requirement</th><th>Observed</th><th>Recorded result</th></tr></thead><tbody>{checks.map(t=><tr key={t.id}><th>{t.name}<small>{t.required?'Required':'Diagnostic'}</small></th><td>{t.expected===true?'All declared criteria must pass':recorded(t.expected)}<small>{t.description}</small></td><td>{recorded(t.observed)}</td><td><span className={`test-badge ${t.status}`}>{t.status.replace('_',' ')}</span>{t.source&&<details className="control-source"><summary>Source</summary><code>{t.source.path}</code><code>SHA-256: {t.source.sha256??'Not recorded'}</code></details>}</td></tr>)}</tbody></table></div>}
    </>}
   </section>;
  })}
  </details>
 </section>;
}
