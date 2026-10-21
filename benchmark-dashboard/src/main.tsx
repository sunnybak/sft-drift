import React, { useCallback, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowLeft, FileJson2, Plus, RefreshCw, Search } from 'lucide-react';
import LegacyExplorer from './LegacyExplorer';
import { Sidebar } from './components/Sidebar';
import { BenchmarkReport } from './components/BenchmarkReport';
import { reportPriority } from './report-types';
import type { ReportCollection } from './report-types';
import './style.css';
import './reports.css';
function App() {
 const [view,setView]=useState('Dashboard'),[collection,setCollection]=useState<ReportCollection|null>(null),[error,setError]=useState('');
 const [opened,setOpened]=useState<string|null>(null),[query,setQuery]=useState(''),[help,setHelp]=useState(false),[loading,setLoading]=useState(false);
 const navigate=(page:string)=>{setView(page);if(page==='Dashboard')setOpened(null)};
 const load=useCallback(async()=>{setLoading(true);setError('');try{const res=await fetch('/reports.json',{cache:'no-store'});if(!res.ok)throw Error(`Report request failed (${res.status})`);setCollection(await res.json())}catch(e){setError(String(e))}finally{setLoading(false)}},[]);
 useEffect(()=>{void load()},[load]);
 if(view!=='Dashboard')return <LegacyExplorer view={view} onNavigate={navigate}/>;
 const reports=[...(collection?.reports??[])].sort((a,b)=>reportPriority(b)-reportPriority(a)),report=reports.find(r=>r.id===opened);
 const filtered=reports.filter(r=>[r.title,r.description,...r.tags].join(' ').toLowerCase().includes(query.toLowerCase()));
 return <div className="app"><Sidebar view={view} onNavigate={navigate}/><main><header><div className="breadcrumb">Study workspace <span>/</span> Dashboard{report&&<><span>/</span><b>{report.title}</b></>}</div><span className="local"><span className="status-dot"/>LOCAL</span></header>
 <section className="page-heading"><div className="eyebrow">MODEL BEHAVIOR / BENCHMARK REPORTS</div><div className="heading-row"><div><h1>{report?'Follow the evidence.':'What did we learn?'}</h1><p>Start with the finding. Compare the change. Resolve the blockers.</p></div><div className="dashboard-actions"><button className="export" disabled={loading} onClick={()=>void load()}><RefreshCw size={15}/>{loading?'Refreshing…':'Refresh reports'}</button><button className="add-report" onClick={()=>setHelp(!help)}><Plus size={15}/> Add report</button></div></div></section>
 {help&&<section className="panel add-report-guide"><FileJson2 size={22}/><div><h2>Add a report with JSON</h2><p>Save a file matching <code>benchmark-report.schema.json</code> in <code>benchmark-dashboard/reports/</code>, then click Refresh reports. No component changes or server restart needed.</p><pre>npm run validate:report -- reports/my-report.json</pre><p>Start with <code>examples/report-template.json</code>. Invalid reports are listed below and do not hide valid ones.</p></div><button onClick={()=>setHelp(false)} className="icon-button" aria-label="Close add report instructions">×</button></section>}
 {error&&<div className="error-note">{error}<button onClick={()=>void load()}>Retry</button></div>}
 {!!collection?.errors.length&&<section className="report-errors"><h3>{collection.errors.length} report files need attention</h3>{collection.errors.map((e,i)=><details key={i}><summary>{e.file}</summary><ul>{e.messages.map((m,j)=><li key={j}>{m}</li>)}</ul></details>)}</section>}
 {report?<><button className="back-report" onClick={()=>setOpened(null)}><ArrowLeft size={15}/> All reports</button><BenchmarkReport key={report.id} report={report}/></>:<>
 <section className="study-decision"><div className="eyebrow">CURRENT DEVELOPMENT DECISION</div><h2>{reports.some(r=>reportPriority(r)===3)?'Keep this in development.':reports.some(r=>reportPriority(r)>0)?'The evidence is incomplete.':reports.length?'Declared report gates pass.':'No reports to assess yet.'}</h2><p>Read the blockers first. Passing one report does not establish full qualification or fresh held-out confirmation.</p><div className="decision-gates">{reports.map(r=><button key={r.id} onClick={()=>setOpened(r.id)}><span className={`status-dot ${reportPriority(r)>0?'blocked-dot':''}`}/>{r.tags[0]??r.title}<b>{reportPriority(r)===3?'Blocked':reportPriority(r)>0?'Incomplete':'Passed'}</b></button>)}</div></section>
 <div className="dashboard-section-heading"><div><h2>Study readouts</h2><p>Candidate-focused conclusions, with the evidence one level down.</p></div><label className="search"><Search size={15}/><input placeholder="Find a report…" value={query} onChange={e=>setQuery(e.target.value)}/></label></div>
 <div className="report-library">{filtered.map(r=><BenchmarkReport key={r.id} report={r} compact initialView="matrix" onOpen={()=>{setOpened(r.id);window.scrollTo({top:0,behavior:'smooth'})}}/>)}</div>
 {!filtered.length&&!loading&&<div className="panel empty"><FileJson2/><h3>{reports.length?'No matching reports':'No reports yet'}</h3><p>{reports.length?'Try another search.':'Add a JSON report or run npm run data to derive the existing study reports.'}</p></div>}
 </>}
 <footer><span>BenchmarkReport JSON v1.0 · local files · read-only evidence</span><span>Missing measurements remain unmeasured.</span></footer>
 </main></div>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
