import { useState } from 'react';
import type { ReportBenchmark, ReportModel, ReportScore } from '../report-types';
import { formatScore, formatChange, scoreChange } from '../report-types';
import { ModelPill } from './ModelPill';
import { DiagnosticDetails } from './DiagnosticDetails';
import { scoreDiagnostics } from '../diagnostics';

const groups = {target:'Trained ethical targets',related_untrained:'Related untrained ethical beliefs',other_untrained_ethical:'Other untrained ethical beliefs',offtopic_eval:'Untrained evaluation preferences'};
export function IndividualBeliefs({benchmarks,models,scores,referenceId,metric}:{benchmarks:ReportBenchmark[];models:ReportModel[];scores:ReportScore[];referenceId?:string;metric:'score'|'change'}) {
 const [query,setQuery]=useState(''),[group,setGroup]=useState('all'),[sort,setSort]=useState('bank');
 const index=new Map(scores.map(s=>[`${s.modelId}/${s.benchmarkId}`,s]));
 const get=(model:string,id:string)=>index.get(`${model}/${id}`);
 const delta=(model:string,id:string)=>scoreChange(get(model,id)?.value,referenceId?get(referenceId,id)?.value:undefined);
 const all=benchmarks.filter(b=>b.beliefGroup);
 const visible=all.filter(b=>(group==='all'||b.beliefGroup===group)&&`${b.name} ${b.id} ${b.description}`.toLowerCase().includes(query.toLowerCase()));
 if(sort==='name')visible.sort((a,b)=>a.name.localeCompare(b.name));
 else if(sort!=='bank')visible.sort((a,b)=>{const x=delta(sort,a.id),y=delta(sort,b.id);return x==null?(y==null?0:1):y==null?-1:Math.abs(y)-Math.abs(x)});
 return <section className="individual-beliefs" aria-label="Individual belief scores">
  <div className="belief-toolbar"><label>Find a belief<input aria-label="Find a belief" type="search" placeholder="Search name or claim…" value={query} onChange={e=>setQuery(e.target.value)}/></label><label>Belief group<select aria-label="Individual belief group" value={group} onChange={e=>setGroup(e.target.value)}><option value="all">All 100 beliefs</option>{Object.entries(groups).map(([id,label])=><option key={id} value={id}>{label} ({all.filter(b=>b.beliefGroup===id).length})</option>)}</select></label><label>Order<select aria-label="Belief order" value={sort} onChange={e=>setSort(e.target.value)}><option value="bank">Evaluation bank order</option><option value="name">Name</option>{models.filter(m=>m.id!==referenceId).map(m=><option key={m.id} value={m.id}>Largest movement · {m.name}</option>)}</select></label><strong>{visible.length} / {all.length} beliefs</strong></div>
  <p>Each cell shows support (%) and change (percentage points). Bars show support on a fixed 0–100% scale. Missing scores retain their recorded errors; model-check failures remain visible above.</p>
  <div className="table-scroll belief-table-scroll"><table className="matrix belief-table"><thead><tr><th>Belief / canonical claim</th>{models.map(m=><th key={m.id}><ModelPill model={m} color={m.color}/></th>)}</tr></thead><tbody>{visible.map(b=><tr key={b.id}><th><strong>{b.name}</strong><small>{groups[b.beliefGroup!]}</small><details><summary>Claim and scope</summary><p>{b.description}</p><p>{b.examples[0]?.input}</p><code>{b.id}</code></details></th>{models.map(m=>{const s=get(m.id,b.id),d=delta(m.id,b.id),v=s?.value;return <td key={m.id}>{v==null?<><strong className="unmeasured">Not estimable</strong><DiagnosticDetails issues={scoreDiagnostics(s)}/></>:<><strong>{metric==='change'?(d===null?'Change not estimable':formatChange(d,b.unit)):formatScore(v,b.unit)}</strong><small>{metric==='change'?`${formatScore(v,b.unit)} support`:m.id===referenceId?'Matched BASE':d===null?'Change not estimable':`${formatChange(d,b.unit)} from BASE`}</small><div className="belief-support-track" aria-hidden="true"><i style={{width:`${v*100}%`,background:m.color??'#687a69'}}/></div></>}<details className="score-evidence"><summary>Score evidence</summary><p>{s?.notes??'No saved result.'}</p>{s?.source&&<code>{s.source.path}</code>}</details></td>})}</tr>)}</tbody></table></div>{!visible.length&&<p>No beliefs match this search.</p>}
 </section>;
}
