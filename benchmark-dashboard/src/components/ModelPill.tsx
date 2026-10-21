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
      <div className="model-science-summary">
        <p className="model-family">{model.model ?? 'Model family not recorded'} · {model.variant === 'base' ? 'Reference model' : model.variant === 'finetuned' ? 'Fine-tuned model' : 'Study model'}</p>
        {model.studyContext ? <><section><h3>Why this model exists</h3><p>{model.studyContext.purpose}</p></section><section><h3>What changed</h3><p>{model.studyContext.intervention}</p></section><section><h3>What it trained on</h3><p>{model.studyContext.data}</p></section></> : <section><h3>Training context</h3><p>{model.description ?? ft?.pipeline.description ?? (model.variant === 'base' ? 'Reference model without study fine-tuning.' : 'A scientific summary has not been supplied for this model.')}</p></section>}
        {ft && <TrainingDose model={model}/>}
        {model.studyContext && <><section><h3>How to compare it</h3><p>{model.studyContext.comparison}</p></section><section className="model-study-caution"><h3>What this can tell us</h3><p>{model.studyContext.limitations}</p></section></>}
      </div>
      <details className="model-reproducibility"><summary>Reproducibility details · IDs, hashes and settings</summary>
      <dl><dt>Model ID</dt><dd>{model.id}</dd><dt>Provider</dt><dd>{model.provider ?? 'Not recorded'}</dd><dt>Base model</dt><dd>{model.model ?? 'Not recorded'}</dd><dt>Revision</dt><dd>{model.revision ?? 'Not recorded'}</dd><dt>Variant</dt><dd>{model.variant ?? 'Not recorded'}</dd></dl>

      <h3>Fine-tuning</h3>
      {ft ? <><dl><dt>Run</dt><dd>{ft.runId}</dd><dt>Dataset</dt><dd>{ft.dataset.id}<p>{ft.dataset.description}</p></dd><dt>Dataset SHA-256</dt><dd>{ft.dataset.sha256 ?? 'Not recorded'}</dd><dt>Pipeline / plan</dt><dd>{ft.pipeline.id}<p>{ft.pipeline.description}</p></dd><dt>Pipeline / plan SHA-256</dt><dd>{ft.pipeline.sha256 ?? 'Not recorded'}</dd><dt>Adapter SHA-256</dt><dd>{ft.adapter?.sha256 ?? 'Not recorded'}</dd></dl><details><summary>Dataset and pipeline parameters</summary><pre>{JSON.stringify({dataset:ft.dataset.context,pipeline:ft.pipeline.context},null,2)}</pre></details></> : <p>{model.training_run_id ? `Training run: ${model.training_run_id}. Additional provenance is not supplied in this view.` : model.variant === 'base' || model.variant === 'reference' ? 'Base/reference model; no fine-tuning context supplied.' : 'Fine-tuning provenance is not supplied in this view.'}</p>}
      {model.inference && <details><summary>Inference configuration</summary><pre>{JSON.stringify(model.inference,null,2)}</pre></details>}
      </details>
    </dialog>, document.body)}
  </>;
}

function TrainingDose({model}:{model:ModelInfo}) {
  const ft=model.finetuning;
  if(!ft)return null;
  const record=(v:unknown):Record<string,unknown>=>v!==null&&typeof v==='object'?v as Record<string,unknown>:{};
  const context=ft.pipeline.context, sft=record(record(context.training).sft), schedule=record(context.schedule);
  const dose=ft.dataset.context;
  const tokens=Object.values(record(dose.loss_tokens_by_kind)).filter((v):v is number=>typeof v==='number').reduce((a,b)=>a+b,0);
  const stats=[
    [sft.full_finetune === false ? 'LoRA adapter' : sft.full_finetune === true ? 'All model weights' : null,'Training method'],
    [typeof sft.epochs==='number'?`${sft.epochs} ${sft.epochs===1?'pass':'passes'}`:null,'Through training data'],
    [typeof schedule.max_steps==='number'?schedule.max_steps.toLocaleString():null,'Parameter updates'],
    [tokens?`${(tokens/1e6).toFixed(2)}M`:null,'Training target tokens'],
    [typeof sft.seed==='number'?String(sft.seed):null,'Training seed'],
  ].filter(([value])=>value!==null);
  return stats.length?<section><h3>Training dose</h3><div className="model-dose-grid">{stats.map(([value,label])=><div key={label}><strong>{value}</strong><span>{label}</span></div>)}</div><p className="model-dose-note">Training entries include repeated exposure; they are not all unique examples.</p></section>:null;
}
