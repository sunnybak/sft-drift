import type { ReportDiagnostic } from '../report-types';
export function DiagnosticDetails({issues}:{issues:ReportDiagnostic[]}){
 if(!issues.length)return null;
 return <details className="diagnostic-details"><summary>Why? · {[...new Set(issues.map(i=>i.code))].join(' · ')}</summary>{issues.map((issue,index)=><section key={index} className={`diagnostic-${issue.severity}`}><code>{issue.code}</code><span>{issue.stage} · {issue.severity}</span><p>{issue.message}</p>{issue.context&&<dl>{Object.entries(issue.context).map(([key,value])=><div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{String(value??'Unknown')}</dd></div>)}</dl>}<p><strong>Next step:</strong> {issue.nextStep}</p>{issue.sources?.map(s=><div className="diagnostic-source" key={s.path}><span>Source artifact</span><code>{s.path}</code><small>SHA-256: {s.sha256??'Not recorded'}</small></div>)}</section>)}</details>;
}
