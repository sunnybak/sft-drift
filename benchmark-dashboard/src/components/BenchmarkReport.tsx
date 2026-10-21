import { useMemo, useState } from 'react';
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceLine, Cell, LabelList } from 'recharts';
import { ArrowDownToLine, ArrowUpRight, Check, ChevronRight } from 'lucide-react';
import { checkSummary, formatScore } from '../report-types';
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
  const [selected,setSelected]=useState(report.models.map(m=>m.id));
  const [testFilter,setTestFilter]=useState('all');
  const index=useMemo(()=>new Map(report.scores.map(s=>[JSON.stringify([s.modelId,s.benchmarkId]),s])),[report]);
  const score=(model:string,benchmark:string)=>index.get(JSON.stringify([model,benchmark]));
  const models=report.models.filter(m=>selected.includes(m.id));
  const benchmarks=compact?report.benchmarks.slice(0,2):report.benchmarks;
  const tests=report.tests.filter(t=>selected.includes(t.modelId));
  const summary=checkSummary(tests);
  const visibleTests=tests.filter(t=>testFilter==='all'||t.status===testFilter);
  const color=(id:string)=>report.models.find(m=>m.id===id)?.color??fallbackColor(id);
  const count=(s:ReportScore|undefined)=>s?.numerator!==null&&s?.denominator!==null&&s?.numerator!==undefined?`${s.numerator} / ${s.denominator}`:null;
  const label=(s:ReportScore|undefined,b:ReportBenchmark)=>s?.value==null?'Not measured':`${formatScore(s.value,b.unit,b.unitLabel)}${count(s)?` · ${count(s)}`:''}`;
  const toggle=(id:string)=>setSelected(ids=>ids.includes(id)?ids.filter(i=>i!==id):[...ids,id]);
  function ScoreEvidence({s}:{s:ReportScore|undefined}) {
    return s?<details className="score-evidence"><summary>Evidence <ChevronRight size={12}/></summary>{s.notes&&<p>{s.notes}</p>}{s.source?<><code>{s.source.path}</code><code>SHA-256: {s.source.sha256??'Not recorded'}</code></>:<p>No source artifact supplied.</p>}</details>:null;
  }
  return <article className={`panel benchmark-report ${compact?'compact-report':''}`} aria-label={report.title}>
    <div className="report-heading"><div><div className="report-tags">{report.tags.map(t=><span key={t}>{t}</span>)}<span>SCHEMA {report.schemaVersion}</span></div><h2>{report.title}</h2><p>{report.description}</p></div><div className="report-actions">{onOpen&&<button className="report-open" onClick={onOpen}>Open report <ArrowUpRight size={15}/></button>}<button className="icon-button" aria-label={`Download ${report.title}`} onClick={()=>downloadReport(report)}><ArrowDownToLine size={16}/></button></div></div>
    <div className="report-status"><span className={`test-badge ${summary.counts.fail?'fail':summary.counts.error?'error':summary.status==='Declared checks passed'?'pass':'not_run'}`}>{summary.status}</span><span>{summary.counts.pass} pass · {summary.counts.fail} fail · {summary.counts.not_run} not run · {summary.counts.error} errors</span><small>Declared checks only; not full model qualification.</small></div>
    <div className="report-models">{report.models.map(m=><label className={selected.includes(m.id)?'report-model active':'report-model'} key={m.id}><input type="checkbox" checked={selected.includes(m.id)} onChange={()=>toggle(m.id)}/><i style={{background:color(m.id)}}/>{m.name}</label>)}</div>
    <div className="report-tabs" aria-label={`${report.title} view`}>{([['bars','Horizontal bars'],['columns','Vertical bars'],['matrix','Score matrix'],['tests','Checks'],['benchmarks','What is tested'],['context','Model context']] as const).map(([id,title])=><button key={id} aria-pressed={view===id} className={view===id?'active':''} onClick={()=>setView(id)}>{title}</button>)}</div>
    {!models.length?<div className="empty"><h3>No models selected</h3><button onClick={()=>setSelected(report.models.map(m=>m.id))}>Select all models</button></div>:
    (view==='bars'||view==='columns')?<div className="report-charts">{benchmarks.map(b=>{
      const rows=models.map(m=>({id:m.id,name:m.name,value:score(m.id,b.id)?.value??null}));
      const horizontal=view==='bars';
      const scoreAxis=b.unit==='fraction'?'Score (%)':b.unitLabel?`Score (${b.unitLabel})`:'Score';
      const axisLabel=(value:string,vertical=false)=>({value,position:vertical?'insideLeft' as const:'bottom' as const,angle:vertical?-90:0,offset:vertical?0:12,style:{fontSize:13,fill:'#687a69'}});
      return <section className="report-chart-item" key={b.id}><div className="report-chart-title"><h3>{b.name}</h3><span>{b.threshold?`${b.threshold.operator==='gte'?'≥':'≤'} ${formatScore(b.threshold.value,b.unit,b.unitLabel)}`:'Diagnostic'}</span></div><p>{b.description}</p>
        <div className="report-chart-canvas" style={{height:horizontal?Math.max(190,models.length*39+100):310}}><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} layout={horizontal?'vertical':'horizontal'} margin={{top:20,right:70,bottom:horizontal?30:models.length>4?65:30,left:25}} barSize={horizontal?19:35}>
          <CartesianGrid stroke="#e9ede5" horizontal={!horizontal} vertical={horizontal}/>
          {horizontal?<><XAxis type="number" domain={[b.range.min,b.range.max]} tickFormatter={v=>formatScore(v,b.unit,b.unitLabel)} axisLine={false} tickLine={false} tick={{fontSize:13}} label={axisLabel(scoreAxis)}/><YAxis type="category" dataKey="name" width={compact?145:175} axisLine={false} tickLine={false} tick={{fontSize:13}} label={axisLabel('Model',true)}/></>:<><XAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{fontSize:13}} interval={0} angle={models.length>4?-20:0} textAnchor={models.length>4?'end':'middle'} height={models.length>4?70:35} label={axisLabel('Model')}/><YAxis type="number" domain={[b.range.min,b.range.max]} width={75} tickFormatter={v=>formatScore(v,b.unit,b.unitLabel)} axisLine={false} tickLine={false} tick={{fontSize:13}} label={axisLabel(scoreAxis,true)}/></>}
          <Tooltip content={({active,payload}:any)=>{if(!active||!payload?.length)return null;const s=score(payload[0].payload.id,b.id);return <div className="tooltip"><strong>{payload[0].payload.name}</strong>{label(s,b)}</div>}}/>
          {b.threshold&&(horizontal?<ReferenceLine x={b.threshold.value} stroke="#a97e48" strokeDasharray="3 3"/>:<ReferenceLine y={b.threshold.value} stroke="#a97e48" strokeDasharray="3 3"/>)}
          <Bar dataKey="value" isAnimationActive={false} radius={horizontal?[0,3,3,0]:[3,3,0,0]}>{rows.map(r=><Cell key={r.id} fill={color(r.id)}/>)}<LabelList dataKey="value" position={horizontal?'right':'top'} formatter={(v:any)=>typeof v==='number'?formatScore(v,b.unit,b.unitLabel):'—'} style={{fontSize:13,fill:'#687a69'}}/></Bar>
        </BarChart></ResponsiveContainer></div>
        <div className="report-score-strip">{models.map(m=><span key={m.id}><i style={{background:color(m.id)}}/>{m.name}: <b>{label(score(m.id,b.id),b)}</b></span>)}</div>
      </section>;
    })}</div>:
    view==='matrix'?<div className="table-scroll"><table className="matrix"><thead><tr><th>Benchmark</th>{models.map(m=><th key={m.id}><i style={{background:color(m.id)}}/>{m.name}</th>)}<th>Target</th></tr></thead><tbody>{benchmarks.map(b=><tr key={b.id}><th>{b.name}</th>{models.map(m=>{const s=score(m.id,b.id);return <td key={m.id}><b className={s?.value==null?'unmeasured':''}>{s?.value==null?'—':formatScore(s.value,b.unit,b.unitLabel)}</b><small className="exact-count">{count(s)??(s?.value==null?'Not measured':'No counts supplied')}</small>{!compact&&<ScoreEvidence s={s}/>}</td>})}<td>{b.threshold?`${b.threshold.operator==='gte'?'≥':'≤'} ${formatScore(b.threshold.value,b.unit,b.unitLabel)}`:'Diagnostic'}</td></tr>)}</tbody></table></div>:
    view==='tests'?<div className="report-checks"><div className="check-filter"><label>Show <select value={testFilter} onChange={e=>setTestFilter(e.target.value)}>{['all','pass','fail','not_run','error'].map(s=><option key={s} value={s}>{s.replace('_',' ')}</option>)}</select></label><small>Pass/fail is recorded evidence, not inferred from chart colors.</small></div>{!tests.length?<p className="report-empty">No checks declared for the selected models.</p>:!visibleTests.length?<p className="report-empty">No checks match this status filter.</p>:visibleTests.map(t=><details className="report-check" key={t.id}><summary><span className={`test-badge ${t.status}`}>{t.status.replace('_',' ')}</span><strong>{t.name}</strong><span>{report.models.find(m=>m.id===t.modelId)?.name}</span><small>{t.required?'Required':'Diagnostic'}</small></summary><p>{t.description}</p><dl><dt>Expected</dt><dd>{String(t.expected??'Not supplied')}</dd><dt>Observed</dt><dd>{String(t.observed??'Not supplied')}</dd></dl>{t.source&&<><code>{t.source.path}</code><code>SHA-256: {t.source.sha256??'Not recorded'}</code></>}</details>)}</div>:
    view==='benchmarks'?<div className="benchmark-explanations">{report.benchmarks.map(b=><section key={b.id}><span className="eyebrow">{b.category} · {b.direction==='descriptive'?'Descriptive':`${b.direction} is better`}</span><h3>{b.name}</h3><p>{b.description}</p><div className="benchmark-conditions">{b.conditions}</div><h4>Example tasks</h4>{b.examples.map((e,i)=><div className="benchmark-example" key={i}><span>INPUT</span><p>{e.input}</p><span>EXPECTED</span><p>{e.expected}</p>{e.note&&<small>{e.note}</small>}</div>)}</section>)}</div>:
    <div className="model-context">{models.map(m=><details key={m.id} open={!compact&&models.length===1}><summary><i style={{background:color(m.id)}}/><strong>{m.name}</strong><span>{m.model}</span><span className="variant-badge">{m.variant}</span></summary><dl><dt>Provider</dt><dd>{m.provider}</dd><dt>Model revision</dt><dd>{m.revision??'Not recorded'}</dd><dt>Inference configuration</dt><dd><pre>{JSON.stringify(m.inference,null,2)}</pre></dd></dl>{m.finetuning?<><h4>Fine-tuning provenance</h4><dl><dt>Training run</dt><dd>{m.finetuning.runId}</dd><dt>Dataset</dt><dd>{m.finetuning.dataset.id}<p>{m.finetuning.dataset.description}</p></dd><dt>Dataset SHA-256</dt><dd>{m.finetuning.dataset.sha256??'Not recorded'}</dd><dt>Pipeline / plan</dt><dd>{m.finetuning.pipeline.id}<p>{m.finetuning.pipeline.description}</p></dd><dt>Pipeline / plan SHA-256</dt><dd>{m.finetuning.pipeline.sha256??'Not recorded'}</dd><dt>Adapter SHA-256</dt><dd>{m.finetuning.adapter?.sha256??'Not recorded'}</dd></dl><details className="context-json"><summary>Dataset and pipeline parameters</summary><pre>{JSON.stringify({dataset:m.finetuning.dataset.context,pipeline:m.finetuning.pipeline.context},null,2)}</pre></details></>:<p>Base/reference model; no fine-tuning context supplied.</p>}</details>)}</div>}
    <div className="report-footer"><span>{compact&&['bars','columns','matrix'].includes(view)?`Showing ${benchmarks.length} of ${report.benchmarks.length} benchmarks`:`${report.benchmarks.length} benchmarks · ${report.scores.length} saved scores`} · {report.id}</span>{onOpen&&<button onClick={onOpen}>Full report <ArrowUpRight size={12}/></button>}</div>
    {!compact&&<div className="report-scope">{report.context}<span>Report timestamp: {new Date(report.createdAt).toLocaleString()}</span></div>}
  </article>;
}
