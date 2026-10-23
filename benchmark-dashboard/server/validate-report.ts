import Ajv from 'ajv';
import { readFileSync } from 'node:fs';
import type { BenchmarkReportData } from '../src/report-types.ts';
const schema = JSON.parse(readFileSync(new URL('../benchmark-report.schema.json', import.meta.url), 'utf8'));
const validate = new Ajv({ allErrors: true, strict: true, allowUnionTypes: true }).compile(schema);
export function validateReport(value: unknown): { report?: BenchmarkReportData; errors: string[] } {
  if (!validate(value)) return { errors: (validate.errors ?? []).map(e => `${e.instancePath || '/'} ${e.message}`) };
  const r = value as BenchmarkReportData, errors: string[] = [];
  function unique(ids: string[], kind: string) {
    if (new Set(ids).size !== ids.length) errors.push(`Duplicate ${kind} id`);
  }
  if (r.journey) unique(r.journey.phases.map(p=>p.id), 'journey phase');
  unique(r.models.map(m => m.id), 'model'); unique(r.benchmarks.map(b => b.id), 'benchmark'); unique(r.tests.map(t => t.id), 'test');
  const models = new Set(r.models.map(m => m.id)), benchmarks = new Map(r.benchmarks.map(b => [b.id, b]));
  if (r.presentation) {
    if(r.presentation.defaultCategory&&!r.benchmarks.some(b=>b.category===r.presentation!.defaultCategory)) errors.push('Presentation references unknown category');
    for (const id of [r.presentation.focusModelId,r.presentation.referenceModelId,r.presentation.comparisonModelId].filter(Boolean)) if (!models.has(id!)) errors.push('Presentation references unknown model');
    for (const h of r.presentation.highlights) if (!benchmarks.has(h.benchmarkId)) errors.push('Presentation references unknown benchmark');
  }
  for (const m of r.models) {
    if (m.variant === 'finetuned' && !m.finetuning) errors.push(`${m.id}: finetuned model requires finetuning provenance`);
    if (m.variant === 'base' && m.finetuning) errors.push(`${m.id}: base model cannot have finetuning provenance`);
  }
  for (const b of r.benchmarks) {
    if (b.range.min >= b.range.max) errors.push(`${b.id}: invalid range`);
    if (b.unit === 'fraction' && (b.range.min !== 0 || b.range.max !== 1)) errors.push(`${b.id}: fraction range must be 0–1`);
    if (b.threshold && (b.threshold.value < b.range.min || b.threshold.value > b.range.max)) errors.push(`${b.id}: threshold outside range`);
  }
  unique(r.scores.map(s => JSON.stringify([s.modelId, s.benchmarkId])), 'score pair');
  for (const s of r.scores) {
    const b = benchmarks.get(s.benchmarkId);
    if (!models.has(s.modelId) || !b) errors.push(`Score references unknown model/benchmark: ${s.modelId}/${s.benchmarkId}`);
    if ((s.numerator === null) !== (s.denominator === null)) errors.push('Numerator and denominator must both be present or null');
    if (s.value === null && (s.numerator !== null || s.denominator !== null)) errors.push('Missing value cannot carry counts');
    if(s.bounds&&b){
      if(s.value!==null) errors.push('Missing-data bounds cannot accompany a point score');
      if(s.bounds.lower>s.bounds.upper||s.bounds.lower<b.range.min||s.bounds.upper>b.range.max) errors.push('Invalid missing-data bounds');
    }
    if (s.value !== null && b && (s.value < b.range.min || s.value > b.range.max)) errors.push(`${s.benchmarkId}: score outside range`);
    if (s.numerator !== null && s.denominator !== null && b?.unit === 'fraction') {
      if (s.numerator > s.denominator || s.value === null || Math.abs(s.value - s.numerator / s.denominator) > 1e-9) errors.push('Fraction value disagrees with exact counts');
    }
  }
  const controlDefinitions=new Map<string,string>(), controlPairs=new Set<string>();
  for (const t of r.tests) {
    for(const m of t.measurements??[]){
      const definition=JSON.stringify([m.name,m.threshold,m.checkGroup??t.checkGroup??'instrument']),pair=JSON.stringify([t.modelId,m.id]);
      if(controlDefinitions.has(m.id)&&controlDefinitions.get(m.id)!==definition) errors.push('Conflicting control measurement definition');
      if(controlPairs.has(pair)) errors.push('Duplicate model/control measurement');
      controlDefinitions.set(m.id,definition);controlPairs.add(pair);
    }
    unique((t.measurements??[]).map(m=>m.id), 'control measurement');
    if (!models.has(t.modelId) || (t.benchmarkId !== null && !benchmarks.has(t.benchmarkId))) errors.push(`Test references unknown model/benchmark: ${t.id}`);
    if (t.status === 'not_run' && t.observed !== null) errors.push(`${t.id}: not_run test must have null observed value`);
  }
  if (!Number.isFinite(Date.parse(r.createdAt))) errors.push('createdAt must be a valid date');
  return errors.length ? { errors } : { report: r, errors: [] };
}
