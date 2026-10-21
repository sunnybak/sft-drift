import { useEffect, useId, useRef } from 'react';
import { PanelRightClose, PanelRightOpen, X } from 'lucide-react';
import type { BenchmarkReportData } from '../report-types';
import { BenchmarkReport } from './BenchmarkReport';

export function ReportDrawer({report,collapsed,onCollapse,onExpand,onClose}:{
  report:BenchmarkReportData; collapsed:boolean;
  onCollapse:()=>void; onExpand:()=>void; onClose:()=>void;
}) {
  const dialog=useRef<HTMLDialogElement>(null);
  const title=useId();
  useEffect(()=>{
    const panel=dialog.current;
    if(!panel)return;
    if(collapsed){panel.close();return;}
    panel.showModal();
    const previous=document.body.style.overflow;
    document.body.style.overflow='hidden';
    return ()=>{panel.close();document.body.style.overflow=previous;};
  },[collapsed,report.id]);
  return <>
    {collapsed&&<div className="report-collapsed-tab">
      <button onClick={onExpand} aria-label={`Expand report: ${report.title}`}><PanelRightOpen size={19}/><span>{report.title}</span></button>
      <button className="icon-button" onClick={onClose} aria-label="Close report"><X size={16}/></button>
    </div>}
    <dialog ref={dialog} className="report-drawer" aria-labelledby={title}
      onCancel={event=>{if(event.target===event.currentTarget){event.preventDefault();onClose();}}}
      onClick={event=>{if(event.target!==event.currentTarget)return;const box=event.currentTarget.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)onClose();}}>
      <div className="report-drawer-heading"><div><span className="eyebrow">BENCHMARK REPORT</span><h2 id={title}>{report.title}</h2></div><div>
        <button className="drawer-control" onClick={onCollapse} aria-label="Collapse report" title="Collapse report"><PanelRightClose size={19}/></button>
        <button className="drawer-control" onClick={onClose} aria-label="Close report" title="Close report"><X size={21}/></button>
      </div></div>
      <div className="report-drawer-body"><BenchmarkReport key={report.id} report={report}/></div>
    </dialog>
  </>;
}
