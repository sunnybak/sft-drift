import { useState } from 'react';
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceLine, ReferenceArea, Cell, LabelList } from 'recharts';
import { ModelPill } from './ModelPill';
import { formatScore } from '../report-types';
import type { ReportBenchmark, ReportModel, ReportScore, ReportTest } from '../report-types';

type Props={models:ReportModel[];benchmarks:ReportBenchmark[];scores:ReportScore[];tests:ReportTest[]};
type Metric=Pick<ReportBenchmark,'id'|'name'|'unit'|'range'|'threshold'> & { values:Map<string,number|null> };
export function ControlCharts({models,benchmarks,scores,tests}:Props){
 const [vertical,setVertical]=useState(false);
 const metrics:Metric[]=benchmarks.filter(b=>b.threshold||b.checkGroup).map(b=>({...b,values:new Map(scores.filter(s=>s.benchmarkId===b.id).map(s=>[s.modelId,s.value]))}));
 const collected=new Map<string,Metric>();
 for(const t of tests)for(const m of t.measurements??[]){
  let metric=collected.get(m.id);
  if(!metric){metric={...m,unit:'fraction',range:{min:0,max:1},values:new Map()};collected.set(m.id,metric);}
  metric.values.set(t.modelId,m.value);
 }
 metrics.push(...[...collected.values()].sort((a,b)=>Number(a.id.endsWith('-coverage'))-Number(b.id.endsWith('-coverage'))));
 if(!metrics.length)return <p>No numeric measurements recorded for this group in this report. Recorded gate results are shown below.</p>;
 return <><div className="control-chart-options" role="group" aria-label="Control chart layout"><button aria-pressed={!vertical} onClick={()=>setVertical(false)}>Horizontal bars</button><button aria-pressed={vertical} onClick={()=>setVertical(true)}>Vertical bars</button><small>Green shading marks the passing range; dashed line marks its boundary.</small></div><div className="control-charts">{metrics.map(b=>{
  const t=b.threshold,rows=models.map(m=>({id:m.id,name:m.name,value:b.values.get(m.id)??null,color:m.color??'#377867'}));
  const fmt=(v:number)=>b.unit==='fraction'?`${Number((v*100).toFixed(3))}%`:formatScore(v,b.unit);
  const lower=t?.operator==='gte'?t.value:b.range.min,upper=t?.operator==='gte'?b.range.max:t?.value??b.range.max;
  return <section className="report-chart-item" key={b.id}><div className="report-chart-title"><h3>{b.name}</h3><span>{t?`Pass: ${t.operator==='gte'?'≥':'≤'} ${fmt(t.value)}`:'Diagnostic · no passing threshold'}</span></div>
   <div style={{height:vertical?330:Math.max(230,models.length*40+100)}}><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} layout={vertical?'horizontal':'vertical'} margin={{top:20,right:60,bottom:45,left:20}} barSize={22}>
    <CartesianGrid stroke="#e9ede5" horizontal={vertical} vertical={!vertical}/>
    {vertical?<><XAxis dataKey="name" type="category" tick={{fontSize:12}} interval={0} angle={-15} textAnchor="end" height={65} label={{value:'Model',position:'bottom',offset:12}}/><YAxis type="number" domain={[b.range.min,b.range.max]} width={75} tickFormatter={fmt} label={{value:b.unit==='fraction'?'Result (%)':'Result',angle:-90,position:'insideLeft',style:{fontSize:12}}}/></>:<><XAxis type="number" domain={[b.range.min,b.range.max]} tickFormatter={fmt} label={{value:b.unit==='fraction'?'Result (%)':'Result',position:'bottom',offset:12,style:{fontSize:12}}}/><YAxis dataKey="name" type="category" width={145} tick={{fontSize:12}} label={{value:'Model',angle:-90,position:'insideLeft',offset:-10,style:{fontSize:12}}}/></>}
    {t&&(vertical?<ReferenceArea y1={lower} y2={upper} fill="#70a87c" fillOpacity={.15}/>:<ReferenceArea x1={lower} x2={upper} fill="#70a87c" fillOpacity={.15}/>)}
    {t&&(vertical?<ReferenceLine y={t.value} stroke="#598568" strokeDasharray="4 3"/>:<ReferenceLine x={t.value} stroke="#598568" strokeDasharray="4 3"/>)}
    <Tooltip formatter={v=>typeof v==='number'?fmt(v):'Not recorded'}/>
    <Bar dataKey="value" name="Observed" isAnimationActive={false}>{rows.map(r=><Cell key={r.id} fill={r.color}/>)}<LabelList position={vertical?'top':'right'} formatter={v=>typeof v==='number'?fmt(v):'—'} style={{fontSize:12,fill:'#53694b'}}/></Bar>
   </BarChart></ResponsiveContainer></div>
   <div className="report-score-strip">{models.map(m=><span key={m.id}><ModelPill model={m} color={m.color??'#377867'}/><b>{b.values.get(m.id)==null?'Not recorded':fmt(b.values.get(m.id)!)}</b></span>)}</div>
  </section>;
 })}</div></>;
}
