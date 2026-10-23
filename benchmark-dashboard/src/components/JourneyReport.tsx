import { useState } from 'react';
import { ArrowUpRight, Download } from 'lucide-react';
import { BenchmarkReport, downloadReport } from './BenchmarkReport';
import type { BenchmarkReportData } from '../report-types';
import './journey.css';

export function JourneyReport({report,onOpenReport,availableReportIds}:{report:BenchmarkReportData;onOpenReport:(id:string)=>void;availableReportIds:string[]}) {
  const [view,setView]=useState<'story'|'evidence'>('story');
  const journey=report.journey!;
  return <article className="journey" aria-label={report.title}>
    <nav className="journey-nav" aria-label="Journey view"><div><button aria-pressed={view==='story'} onClick={()=>setView('story')}>The journey</button><button aria-pressed={view==='evidence'} onClick={()=>setView('evidence')}>Latest comparison · charts & checks</button></div><button onClick={()=>downloadReport(report)}><Download size={16}/> Report JSON</button></nav>
    {view==='evidence'?<><p className="journey-note">This appendix is the final matched stock/custom/BASE comparison only. Earlier experiments use different banks; their detailed reports are linked from the journey.</p><BenchmarkReport report={report}/></>:<>
      <section className="journey-hero"><div className="eyebrow">RESEARCH LOG · {journey.period}</div><h1>A working trainer.<br/>An unresolved recipe.</h1><p className="journey-lead">{journey.summary}</p><div className="journey-verdict"><span>WHERE WE LANDED</span><strong>{journey.verdict}</strong></div></section>
      <section className="journey-orientation" aria-label="How to read these results"><div><h2>Three separate questions</h2><p><b>Did weights update?</b> Yes, with verified reloads. <b>Did the model learn anything?</b> Yes, including seen answers and response style. <b>Did a recipe pass every declared model check?</b> No.</p></div><div><h2>Read counts within each experiment</h2><p>Question banks and BASE-known cohorts changed. The fractions below retain their own denominators. Runtime repeats are not new training seeds; stance support is not accuracy.</p></div></section>
      <div className="journey-layout"><aside className="journey-index"><span className="eyebrow">FOLLOW THE EVIDENCE</span>{journey.phases.map((phase,i)=><a key={phase.id} href={`#journey-${phase.id}`}><span>{String(i+1).padStart(2,'0')}</span>{phase.title}</a>)}<a href="#journey-decision"><span>→</span>The decision</a></aside>
      <div className="journey-timeline">{journey.phases.map((phase,i)=><section className="journey-phase" id={`journey-${phase.id}`} key={phase.id}>
        <div className="journey-phase-top"><span className="eyebrow">{String(i+1).padStart(2,'0')} / {phase.label}</span><span className={`journey-status ${phase.status}`}>{phase.status==='context'?'Starting evidence':phase.status==='diagnostic'?'Diagnostic':phase.status==='complete'?'Comparison complete':'Recipe rejected'}</span></div>
        <h2>{phase.title}</h2><p className="journey-question">{phase.question}</p><div className="journey-description"><h3>What we changed or tested</h3><p>{phase.change}</p></div>
        {!!phase.metrics.length&&<div className="journey-metrics">{phase.metrics.map(metric=><div key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.note}</small></div>)}</div>}
        <h3>What happened</h3><p>{phase.result}</p><div className="journey-lesson"><h3>What this tells us</h3><p>{phase.lesson}</p></div>
        <div className="journey-links">{phase.reportIds.map(id=>availableReportIds.includes(id)?<button key={id} onClick={()=>onOpenReport(id)}>Open detailed report <ArrowUpRight size={14}/></button>:<span key={id}>Detailed report unavailable: {id}</span>)}</div>
        <details className="journey-sources"><summary>Source notes & fingerprints</summary>{phase.sources.map(source=><div key={source.path}><code>{source.path}</code><code>SHA-256 {source.sha256}</code></div>)}</details>
      </section>)}
      <section className="journey-decision" id="journey-decision"><span className="eyebrow">THE SCIENTIFIC READOUT</span><h2>Progress in diagnosis. No qualified recipe yet.</h2><div className="journey-conclusions"><div><h3>Established</h3><ul>{journey.findings.map(f=><li key={f}>{f}</li>)}</ul></div><div><h3>Still unidentified</h3><ul>{journey.unknowns.map(f=><li key={f}>{f}</li>)}</ul></div></div><h3>Recommended next decision</h3><p>{journey.recommendation}</p><p className="journey-note">Recommendation only. The study remains stopped. This report launches no training or inference and changes no historical score or threshold.</p><button className="report-open" onClick={()=>{setView('evidence');document.querySelector('.report-drawer-body')?.scrollTo(0,0)}}>Explore the last matched comparison <ArrowUpRight size={16}/></button></section>
      </div></div>
    </>}
  </article>;
}
