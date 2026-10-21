import React, { useCallback, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowUpRight, FileJson2, Plus, RefreshCw, Search } from 'lucide-react';
import LegacyExplorer from './LegacyExplorer';
import { Sidebar } from './components/Sidebar';
import { ReportDrawer } from './components/ReportDrawer';
import { checkSummary } from './report-types';
import type { ReportCollection } from './report-types';
import './style.css';
import './reports.css';
function App() {
 const [view,setView]=useState('Dashboard'),[collection,setCollection]=useState<ReportCollection|null>(null),[error,setError]=useState('');
 const [opened,setOpened]=useState<string|null>(null),[query,setQuery]=useState(''),[help,setHelp]=useState(false),[loading,setLoading]=useState(false);
 const [collapsed,setCollapsed]=useState(false);
 const openReport=(id:string)=>{setOpened(id);setCollapsed(false)};
 const navigate=(page:string)=>{setView(page);if(page==='Dashboard')setOpened(null)};
 const load=useCallback(async()=>{setLoading(true);setError('');try{const res=await fetch('/reports.json',{cache:'no-store'});if(!res.ok)throw Error(`Report request failed (${res.status})`);setCollection(await res.json())}catch(e){setError(String(e))}finally{setLoading(false)}},[]);
 useEffect(()=>{void load()},[load]);
 if(view!=='Dashboard')return <LegacyExplorer view={view} onNavigate={navigate}/>;
 const reports=collection?.reports??[],report=reports.find(r=>r.id===opened);
 const filtered=reports.filter(r=>[r.title,r.description,r.experiment?.name,r.experiment?.id,r.createdAt,...r.tags].join(' ').toLowerCase().includes(query.toLowerCase()));
 return <div className="app"><Sidebar view={view} onNavigate={navigate}/><main><header><div className="breadcrumb">Study workspace <span>/</span> Dashboard</div><span className="local"><span className="status-dot"/>LOCAL</span></header>
 <section className="page-heading"><div className="eyebrow">MODEL BEHAVIOR / BENCHMARK REPORTS</div><div className="heading-row"><div><h1>Reports</h1><p>Choose a report to explore its scores, checks and model context.</p></div><div className="dashboard-actions"><button className="export" disabled={loading} onClick={()=>void load()}><RefreshCw size={15}/>{loading?'Refreshing…':'Refresh reports'}</button><button className="add-report" onClick={()=>setHelp(!help)}><Plus size={15}/> Add report</button></div></div></section>
 {help&&<section className="panel add-report-guide"><FileJson2 size={22}/><div><h2>Add a report with JSON</h2><p>Save a file matching <code>benchmark-report.schema.json</code> in <code>benchmark-dashboard/reports/</code>, then click Refresh reports. No component changes or server restart needed.</p><pre>npm run validate:report -- reports/my-report.json</pre><p>Start with <code>examples/report-template.json</code>. Invalid reports are listed below and do not hide valid ones.</p></div><button onClick={()=>setHelp(false)} className="icon-button" aria-label="Close add report instructions">×</button></section>}
 {error&&<div className="error-note">{error}<button onClick={()=>void load()}>Retry</button></div>}
 {!!collection?.errors.length&&<section className="report-errors"><h3>{collection.errors.length} report files need attention</h3>{collection.errors.map((e,i)=><details key={i}><summary>{e.file}</summary><ul>{e.messages.map((m,j)=><li key={j}>{m}</li>)}</ul></details>)}</section>}

 <section className="dashboard-overview"><div><strong>{reports.length}</strong><span>Benchmark reports</span></div><div><strong>{reports.reduce((n,r)=>n+r.scores.length,0)}</strong><span>Saved score entries</span></div><div><strong>{reports.reduce((n,r)=>n+r.tests.length,0)}</strong><span>Recorded checks</span></div><p>Separate reports preserve their own conditions and model context. Checks shown here are scoped evidence, not a blended model ranking.</p></section>
 <div className="dashboard-section-heading"><div><h2>Report library</h2><p>Open reports in the side panel. Collapse it to return to the list.</p></div><label className="search"><Search size={15}/><input aria-label="Find a report" placeholder="Find a report…" value={query} onChange={e=>setQuery(e.target.value)}/></label></div>
 <ul className="report-list" aria-label="Benchmark reports">{filtered.map(r=>{const checks=checkSummary(r.tests);return <li key={r.id}><button className={`report-list-row ${opened===r.id?'selected':''}`} onClick={()=>openReport(r.id)} aria-haspopup="dialog" aria-label={`Open ${r.title}`}><span className="report-list-icon"><FileJson2 size={21}/></span><span className="report-list-description"><strong>{r.title}</strong><span className="report-list-meta"><span><b>Experiment</b> {r.experiment?.name??'Not recorded'}</span><span><b>Report date</b> <time dateTime={r.createdAt} title={r.createdAt}>{Number.isNaN(Date.parse(r.createdAt))?'Not recorded':new Date(r.createdAt).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'})}</time></span></span><span>{r.description}</span><span className="report-list-tags">{r.tags.map(tag=><span key={tag}>{tag}</span>)}</span></span><span className="report-list-count"><b>{r.models.length}</b> models</span><span className="report-list-count"><b>{r.benchmarks.length}</b> benchmarks</span><span className={`test-badge ${checks.counts.fail?'fail':checks.counts.error?'error':checks.status==='Declared checks passed'?'pass':'not_run'}`}>{checks.status}</span><ArrowUpRight size={18}/></button></li>})}</ul>
 {!filtered.length&&!loading&&<div className="panel empty"><FileJson2/><h3>{reports.length?'No matching reports':'No reports yet'}</h3><p>{reports.length?'Try another search.':'Add a JSON report or run npm run data to derive the existing study reports.'}</p></div>}
 <footer><span>BenchmarkReport JSON v1.0 · local files · read-only evidence</span><span>Missing measurements remain unmeasured.</span></footer>
 </main>{report&&<ReportDrawer report={report} collapsed={collapsed} onCollapse={()=>setCollapsed(true)} onExpand={()=>setCollapsed(false)} onClose={()=>setOpened(null)}/>}</div>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
