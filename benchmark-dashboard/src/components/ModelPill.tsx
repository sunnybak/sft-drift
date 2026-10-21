import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import type { ReportModel } from '../report-types';

type ModelInfo = Pick<ReportModel, 'id' | 'name'> & Partial<ReportModel> & {
  description?: string; training_run_id?: string | null; verdict?: string;
};
export function ModelPill({ model, color }: { model: ModelInfo; color?: string }) {
  const [open, setOpen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const title = useId();
  useEffect(() => {
    if (open) dialog.current?.showModal();
    else dialog.current?.close();
  }, [open]);
  const ft = model.finetuning;
  return <>
    <button type="button" className="model-info-pill" aria-label={`About ${model.name}`} aria-haspopup="dialog" onClick={() => setOpen(true)}>
      <i style={{ background: color ?? model.color ?? '#9299a4' }} />{model.name}
    </button>
    {createPortal(<dialog ref={dialog} className="model-info-dialog" aria-labelledby={title} onCancel={() => setOpen(false)} onClose={() => setOpen(false)} onClick={e => { if (e.target === e.currentTarget) { const r=e.currentTarget.getBoundingClientRect(); if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)setOpen(false); } }}>
      <div className="model-info-heading"><div><div className="eyebrow">MODEL INFORMATION</div><h2 id={title}>{model.name}</h2></div><button type="button" className="report-open" onClick={() => setOpen(false)}>Close ×</button></div>
      {model.description && <p>{model.description}</p>}
      <dl><dt>Model ID</dt><dd>{model.id}</dd><dt>Provider</dt><dd>{model.provider ?? 'Not recorded'}</dd><dt>Base model</dt><dd>{model.model ?? 'Not recorded'}</dd><dt>Revision</dt><dd>{model.revision ?? 'Not recorded'}</dd><dt>Variant</dt><dd>{model.variant ?? 'Not recorded'}</dd></dl>
      {model.verdict && <p>{model.verdict}</p>}
      <h3>Fine-tuning</h3>
      {ft ? <><dl><dt>Run</dt><dd>{ft.runId}</dd><dt>Dataset</dt><dd>{ft.dataset.id}<p>{ft.dataset.description}</p></dd><dt>Dataset SHA-256</dt><dd>{ft.dataset.sha256 ?? 'Not recorded'}</dd><dt>Pipeline / plan</dt><dd>{ft.pipeline.id}<p>{ft.pipeline.description}</p></dd><dt>Pipeline / plan SHA-256</dt><dd>{ft.pipeline.sha256 ?? 'Not recorded'}</dd><dt>Adapter SHA-256</dt><dd>{ft.adapter?.sha256 ?? 'Not recorded'}</dd></dl><details><summary>Dataset and pipeline parameters</summary><pre>{JSON.stringify({dataset:ft.dataset.context,pipeline:ft.pipeline.context},null,2)}</pre></details></> : <p>{model.training_run_id ? `Training run: ${model.training_run_id}. Additional provenance is not supplied in this view.` : model.variant === 'base' || model.variant === 'reference' ? 'Base/reference model; no fine-tuning context supplied.' : 'Fine-tuning provenance is not supplied in this view.'}</p>}
      {model.inference && <details><summary>Inference configuration</summary><pre>{JSON.stringify(model.inference,null,2)}</pre></details>}
    </dialog>, document.body)}
  </>;
}
