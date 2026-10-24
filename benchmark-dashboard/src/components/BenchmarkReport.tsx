import { useMemo, useState } from 'react';
import { summedChange, formatSummedChange } from '../change-totals';
import type { ChangeAggregation } from '../change-totals';
import { DiagnosticDetails } from './DiagnosticDetails';
import { scoreDiagnostics, testDiagnostics, comparisonDiagnostics } from '../diagnostics';
import { ModelPill } from './ModelPill';
import { ReportControls } from './ReportControls';
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceLine, Cell, LabelList } from 'recharts';
import { ArrowDownToLine, ArrowUpRight, Check, ChevronRight } from 'lucide-react';
import { checkSummary, formatScore, scoreChange, formatChange } from '../report-types';
import type { BenchmarkReportData, ReportBenchmark, ReportScore } from '../report-types';

export type ReportView = 'bars' | 'columns' | 'matrix' | 'tests' | 'benchmarks' | 'context';
type ViewOptions = { initialView?: ReportView; compact?: boolean; onOpen?: () => void };
export type BenchmarkReportProps = { report: BenchmarkReportData } & ViewOptions;
export type BenchmarkResultsProps = BenchmarkReportData & ViewOptions;
const palette = ['#377867','#e0a650','#8c94a2','#8f7eb4','#6099a5','#b87f93','#a98e59','#6e8980'];
const fallbackColor = (id:string) => palette[Array.from(id).reduce((n,c)=>n+c.charCodeAt(0),0)%palette.length];
export function downloadReport(report: BenchmarkReportData) {
  const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download=`${report.id}.json`;link.click();URL.revokeObjectURL(url);
}
/** JSON-report wrapper for loading/saving the complete versioned contract. */
export function BenchmarkReport({report,...options}:BenchmarkReportProps) {
  return <BenchmarkResults {...report} {...options}/>;
}
/** Direct-prop renderer: models, benchmarks, scores, tests, and report metadata. */
export function BenchmarkResults({initialView='bars',compact=false,onOpen,...report}:BenchmarkResultsProps) {
  const [view,setView]=useState<ReportView>(initialView);
  const [showControls,setShowControls]=useState(false);
  const [aggregation,setAggregation]=useState<ChangeAggregation>(report.scores.some(s=>s.changeTotals)?'signed_sum':'mean');
  const [metric,setMetric]=useState<'score'|'change'>(report.presentation?.defaultMetric??'score');
  const [category,setCategory]=useState(report.presentation?.defaultCategory??'All');
  const [selected,setSelected]=useState(report.models.map(m=>m.id));
  const [testFilter,setTestFilter]=useState('all');
  const index=useMemo(()=>new Map(report.scores.map(s=>[JSON.stringify([s.modelId,s.benchmarkId]),s])),[report]);
  const score=(model:string,benchmark:string)=>index.get(JSON.stringify([model,benchmark]));
  const models=report.models.filter(m=>selected.includes(m.id));
  const categories=[...new Set(report.benchmarks.map(b=>b.category))];
  const filteredBenchmarks=report.benchmarks.filter(b=>category==='All'||b.category===category);
  const benchmarks=compact?filteredBenchmarks.slice(0,2):filteredBenchmarks;
  const reference=report.models.find(m=>m.id===report.presentation?.referenceModelId);
  const totalMode=metric==='change'&&aggregation!=='mean';
  const value=(model:string,benchmark:string)=>metric==='change'&&reference?(totalMode?summedChange(score(model,benchmark),reference.id,aggregation):scoreChange(score(model,benchmark)?.value,score(reference.id,benchmark)?.value)):score(model,benchmark)?.value??null;
  const bounds=(model:string,benchmark:string):[number,number]|null=>{
    const raw=score(model,benchmark)?.bounds;if(!raw||totalMode)return null;
    const base=reference?score(reference.id,benchmark)?.value:null;
    if(metric==='change'&&base==null)return null;
    const offset=metric==='change'?base!:0;return [raw.lower-offset,raw.upper-offset];
  };
  const boundLabel=(values:[number,number],b:ReportBenchmark)=>values.map(v=>`${(v*(b.unit==='fraction'?100:1)).toFixed(3)}${b.unit==='fraction'?(metric==='change'?' pp':'%'):''}`).join(' to ');
  const display=(v:number,b:ReportBenchmark)=>totalMode?formatSummedChange(v,aggregation==='absolute_sum'):metric==='change'?formatChange(v,b.unit):formatScore(v,b.unit,b.unitLabel);
  const missing=metric==='change'?'Change not estimable':'Score not estimable';
  const tests=report.tests.filter(t=>selected.includes(t.modelId));
  const summary=checkSummary(tests);
  const visibleTests=tests.filter(t=>testFilter==='all'||t.status===testFilter);
  const color=(id:string)=>report.models.find(m=>m.id===id)?.color??fallbackColor(id);
  const count=(s:ReportScore|undefined)=>s?.numerator!==null&&s?.denominator!==null&&s?.numerator!==undefined?`${s.numerator} / ${s.denominator}`:null;
  const label=(model:string,b:ReportBenchmark)=>{const v=value(model,b.id);const range=bounds(model,b.id);return v===null?(range?`${boundLabel(range,b)} · incomplete`:missing):`${display(v,b)}${metric==='score'&&count(score(model,b.id))?` · ${count(score(model,b.id))}`:''}`;};
  const toggle=(id:string)=>setSelected(ids=>ids.includes(id)?ids.filter(i=>i!==id):[...ids,id]);
  function ScoreEvidence({s}:{s:ReportScore|undefined}) {
    return <><DiagnosticDetails issues={scoreDiagnostics(s)}/>{s?<details className="score-evidence"><summary>Evidence <ChevronRight size={12}/></summary>{s.notes&&<p>{s.notes}</p>}{s.source?<><code>{s.source.path}</code><code>SHA-256: {s.source.sha256??'Not recorded'}</code></>:<p>No source artifact supplied.</p>}</details>:null}</>;
  }
  return <article className={`panel benchmark-report ${compact?'compact-report':''}`} aria-label={report.title}>
    <div className="report-heading"><div><div className="report-tags">{report.tags.map(t=><span key={t}>{t}</span>)}<span>SCHEMA {report.schemaVersion}</span></div><h2>{report.title}</h2><p>{report.description}</p></div><div className="report-actions">{onOpen&&<button className="report-open" onClick={onOpen}>Open report <ArrowUpRight size={15}/></button>}<button className="icon-button" aria-label={`Download ${report.title}`} onClick={()=>downloadReport(report)}><ArrowDownToLine size={16}/></button></div></div>
    {report.presentation?.defaultMetric&&<div className="report-readout"><strong>{report.presentation.headline}</strong><p>{report.presentation.interpretation}</p></div>}
    <div className="report-status"><span className={`test-badge ${summary.counts.fail?'fail':summary.counts.error?'error':summary.status==='Required checks passed'?'pass':'not_run'}`}>{summary.status}</span><span>{summary.counts.pass} pass · {summary.counts.fail} fail · {summary.counts.not_run} not run · {summary.counts.error} errors</span><small>Declared checks only; not full model qualification.</small></div>
    <div className="report-models">{report.models.map(m=><div className={selected.includes(m.id)?'report-model active':'report-model'} key={m.id}><input aria-label={`Show ${m.name}`} type="checkbox" checked={selected.includes(m.id)} onChange={()=>toggle(m.id)}/><ModelPill model={m} color={color(m.id)}/></div>)}</div>
    {<div className="report-controls"><div role="group" aria-label="Score display">{reference&&<button aria-pressed={!showControls&&metric==='change'} onClick={()=>{setShowControls(false);setMetric('change')}}>Change from {reference.name}</button>}<button aria-pressed={!showControls&&metric==='score'} onClick={()=>{setShowControls(false);setMetric('score')}}>{report.presentation?.defaultCategory?'Support for claim':'Absolute score'}</button><button aria-pressed={showControls} onClick={()=>setShowControls(true)}>Model checks</button></div>{!showControls&&metric==='change'&&report.scores.some(s=>s.changeTotals)&&<label>Combine belief changes <select aria-label="Combine belief changes" value={aggregation} onChange={e=>setAggregation(e.target.value as ChangeAggregation)}><option value="signed_sum">Sum of signed changes</option><option value="absolute_sum">Sum of absolute changes</option><option value="mean">Average change</option></select></label>}{!showControls&&report.presentation?.defaultCategory&&<label>Belief group <select value={category} onChange={e=>setCategory(e.target.value)}>{['All',...categories].map(c=><option key={c}>{c}</option>)}</select></label>}<p>{showControls?'Checks of the model and measurement procedure, grouped by purpose. Experimental control arms remain in the model comparisons.':metric==='change'?totalMode?(aggregation==='absolute_sum'?'Sum of each belief’s absolute change from matched BASE. Increases and decreases both add to movement; this is not a support percentage.':'Sum of each belief’s signed change from matched BASE. Increases and decreases can still cancel. This is not a support percentage.')+ ' Totals grow with group size; compare the same belief group across models. Three-seed reports average seeds within each belief before summing.':`Signed movement from matched ${reference?.name}. Zero means unchanged. Higher does not mean better.`:report.presentation?.defaultCategory?'Stance measures support for the canonical claim, not accuracy.':'Absolute recorded scores. Compare within the same benchmark and conditions.'} Missing results remain absent.{!showControls&&report.scores.some(s=>s.bounds)&&' Shaded ranges are missing-response bounds, not confidence intervals or estimated answers.'}</p></div>}
    {!showControls&&<div className="report-tabs" aria-label={`${report.title} view`}>{([['bars','Horizontal bars'],['columns','Vertical bars'],['matrix','Score matrix'],['tests','Recorded checks'],['benchmarks','What is tested'],['context','Model context']] as const).map(([id,title])=><button key={id} aria-pressed={view===id} className={view===id?'active':''} onClick={()=>setView(id)}>{title}</button>)}</div>}
    {!models.length?<div className="empty"><h3>No models selected</h3><button onClick={()=>setSelected(report.models.map(m=>m.id))}>Select all models</button></div>:
    showControls?<ReportControls models={models} benchmarks={report.benchmarks} scores={report.scores} tests={tests}/>: (view==='bars'||view==='columns')?<div className="report-charts">{benchmarks.map(b=>{
      const rows=models.map(m=>({id:m.id,name:m.name,value:value(m.id,b.id)??bounds(m.id,b.id)}));
      const horizontal=view==='bars';
      const scoreAxis=totalMode?`Sum of ${aggregation==='absolute_sum'?'absolute':'signed'} changes (total percentage points)`:metric==='change'?`Change from ${reference?.name} (${b.unit==='fraction'?'percentage points':b.unitLabel??'score'})`:b.unit==='fraction'?`${b.unitLabel??'Score'} (%)`:b.unitLabel?`Score (${b.unitLabel})`:'Score';
      const n=score(reference?.id??'',b.id)?.changeTotals?.beliefCount??1;
      const domain: [number,number]=totalMode?[aggregation==='absolute_sum'?0:-n,n]:metric==='change'?[-(b.range.max-b.range.min),b.range.max-b.range.min]:[b.range.min,b.range.max];
      const axisLabel=(value:string,vertical=false)=>({value,position:vertical?'insideLeft' as const:'bottom' as const,angle:vertical?-90:0,offset:vertical?0:12,style:{fontSize:13,fill:'#687a69'}});
      return <section className="report-chart-item" key={b.id}><div className="report-chart-title"><h3>{b.name}</h3><span>{totalMode?(aggregation==='absolute_sum'?'Total movement':'Signed total'):metric==='change'?'Signed change':b.threshold?`${b.threshold.operator==='gte'?'≥':'≤'} ${formatScore(b.threshold.value,b.unit,b.unitLabel)}`:'Diagnostic'}</span></div><p>{b.description}</p>
        <div className="report-chart-canvas" style={{height:horizontal?Math.max(190,models.length*39+100):310}}><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} layout={horizontal?'vertical':'horizontal'} margin={{top:20,right:totalMode?115:70,bottom:horizontal?30:models.length>4?65:30,left:25}} barSize={horizontal?19:35}>
          <CartesianGrid stroke="#e9ede5" horizontal={!horizontal} vertical={horizontal}/>
          {horizontal?<><XAxis type="number" domain={domain} tickFormatter={v=>totalMode?display(v,b).replace(" total pp",""):display(v,b)} axisLine={false} tickLine={false} tick={{fontSize:13}} label={axisLabel(scoreAxis)}/><YAxis type="category" dataKey="name" width={compact?145:175} axisLine={false} tickLine={false} tick={{fontSize:13}} label={axisLabel('Model',true)}/></>:<><XAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{fontSize:13}} interval={0} angle={models.length>4?-20:0} textAnchor={models.length>4?'end':'middle'} height={models.length>4?70:35} label={axisLabel('Model')}/><YAxis type="number" domain={domain} width={75} tickFormatter={v=>totalMode?display(v,b).replace(" total pp",""):display(v,b)} axisLine={false} tickLine={false} tick={{fontSize:13}} label={axisLabel(scoreAxis,true)}/></>}
          <Tooltip content={({active,payload}:any)=>{if(!active||!payload?.length)return null;return <div className="tooltip"><strong>{payload[0].payload.name}</strong>{label(payload[0].payload.id,b)}</div>}}/>
          {metric==='change'&&(horizontal?<ReferenceLine x={0} stroke="#687a69"/>:<ReferenceLine y={0} stroke="#687a69"/>)}
          {metric==='score'&&b.threshold&&(horizontal?<ReferenceLine x={b.threshold.value} stroke="#a97e48" strokeDasharray="3 3"/>:<ReferenceLine y={b.threshold.value} stroke="#a97e48" strokeDasharray="3 3"/>)}
          <Bar dataKey="value" isAnimationActive={false} radius={horizontal?[0,3,3,0]:[3,3,0,0]}>{rows.map(r=><Cell key={r.id} fill={color(r.id)} fillOpacity={Array.isArray(r.value)?.5:1}/>)}<LabelList dataKey="value" position={horizontal?'right':'top'} formatter={(v:any)=>typeof v==='number'?display(v,b):Array.isArray(v)?'Bounded*':'—'} style={{fontSize:13,fill:'#687a69'}}/></Bar>
        </BarChart></ResponsiveContainer></div>
        <div className="report-score-strip">{models.map(m=><span key={m.id}><ModelPill model={m} color={color(m.id)}/><b>{label(m.id,b)}</b><DiagnosticDetails issues={comparisonDiagnostics(score(m.id,b.id),reference?score(reference.id,b.id):undefined,metric==='change')}/></span>)}</div>
      </section>;
    })}</div>:
    view==='matrix'?<div className="table-scroll"><table className="matrix"><thead><tr><th>Benchmark</th>{models.map(m=><th key={m.id}><ModelPill model={m} color={color(m.id)}/></th>)}<th>Target</th></tr></thead><tbody>{benchmarks.map(b=><tr key={b.id}><th>{b.name}</th>{models.map(m=>{const s=score(m.id,b.id);return <td key={m.id}><b className={s?.value==null?'unmeasured':''}>{value(m.id,b.id)===null?(bounds(m.id,b.id)?boundLabel(bounds(m.id,b.id)!,b):'—'):display(value(m.id,b.id)!,b)}</b><small className="exact-count">{value(m.id,b.id)===null?(bounds(m.id,b.id)?'Incomplete · missing-response bounds':missing):metric==='score'?count(s)??'Mean over declared grid':totalMode?`Sum across ${s?.changeTotals?.beliefCount??'?'} beliefs`:'Matched BASE difference'}</small>{!compact&&<ScoreEvidence s={s}/>}</td>})}<td>{metric==='change'?'Zero = unchanged':b.threshold?`${b.threshold.operator==='gte'?'≥':'≤'} ${formatScore(b.threshold.value,b.unit,b.unitLabel)}`:'Diagnostic'}</td></tr>)}</tbody></table></div>:
    view==='tests'?<div className="report-checks"><div className="check-filter"><label>Show <select value={testFilter} onChange={e=>setTestFilter(e.target.value)}>{['all','pass','fail','not_run','error'].map(s=><option key={s} value={s}>{s.replace('_',' ')}</option>)}</select></label><small>Pass/fail is recorded evidence, not inferred from chart colors.</small></div>{!tests.length?<p className="report-empty">No checks declared for the selected models.</p>:!visibleTests.length?<p className="report-empty">No checks match this status filter.</p>:visibleTests.map(t=><details className="report-check" key={t.id}><summary><span className={`test-badge ${t.status}`}>{t.status.replace('_',' ')}</span><strong>{t.name}</strong><span>{report.models.find(m=>m.id===t.modelId)?.name}</span><small>{t.required?'Required':'Diagnostic'}</small></summary><p>{t.description}</p><DiagnosticDetails issues={testDiagnostics(t)}/><dl><dt>Expected</dt><dd>{String(t.expected??'Not supplied')}</dd><dt>Observed</dt><dd>{String(t.observed??'Not supplied')}</dd></dl>{t.source&&<><code>{t.source.path}</code><code>SHA-256: {t.source.sha256??'Not recorded'}</code></>}</details>)}</div>:
    view==='benchmarks'?<div className="benchmark-explanations">{benchmarks.map(b=><section key={b.id}><span className="eyebrow">{b.category} · {b.direction==='descriptive'?'Descriptive':`${b.direction} is better`}</span><h3>{b.name}</h3><p>{b.description}</p><div className="benchmark-conditions">{b.conditions}</div><h4>Example tasks</h4>{b.examples.map((e,i)=><div className="benchmark-example" key={i}><span>INPUT</span><p>{e.input}</p><span>EXPECTED</span><p>{e.expected}</p>{e.note&&<small>{e.note}</small>}</div>)}</section>)}</div>:
    <div className="model-context">{models.map(m=><details key={m.id} open={!compact&&models.length===1}><summary><i style={{background:color(m.id)}}/><strong>{m.name}</strong><span>{m.model}</span><span className="variant-badge">{m.variant}</span></summary><dl><dt>Provider</dt><dd>{m.provider}</dd><dt>Model revision</dt><dd>{m.revision??'Not recorded'}</dd><dt>Inference configuration</dt><dd><pre>{JSON.stringify(m.inference,null,2)}</pre></dd></dl>{m.finetuning?<><h4>Fine-tuning provenance</h4><dl><dt>Training run</dt><dd>{m.finetuning.runId}</dd><dt>Dataset</dt><dd>{m.finetuning.dataset.id}<p>{m.finetuning.dataset.description}</p></dd><dt>Dataset SHA-256</dt><dd>{m.finetuning.dataset.sha256??'Not recorded'}</dd><dt>Pipeline / plan</dt><dd>{m.finetuning.pipeline.id}<p>{m.finetuning.pipeline.description}</p></dd><dt>Pipeline / plan SHA-256</dt><dd>{m.finetuning.pipeline.sha256??'Not recorded'}</dd><dt>Adapter SHA-256</dt><dd>{m.finetuning.adapter?.sha256??'Not recorded'}</dd></dl><details className="context-json"><summary>Dataset and pipeline parameters</summary><pre>{JSON.stringify({dataset:m.finetuning.dataset.context,pipeline:m.finetuning.pipeline.context},null,2)}</pre></details></>:<p>Base/reference model; no fine-tuning context supplied.</p>}</details>)}</div>}
    <div className="report-footer"><span>{compact&&['bars','columns','matrix'].includes(view)?`Showing ${benchmarks.length} of ${report.benchmarks.length} benchmarks`:`${report.benchmarks.length} benchmarks · ${report.scores.length} saved scores`} · {report.id}</span>{onOpen&&<button onClick={onOpen}>Full report <ArrowUpRight size={12}/></button>}</div>
    {!compact&&<div className="report-scope">{report.context}<span>Report timestamp: {new Date(report.createdAt).toLocaleString()}</span></div>}
  </article>;
}
