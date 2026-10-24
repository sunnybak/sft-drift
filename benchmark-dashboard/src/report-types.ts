/** Public, versioned BenchmarkReport JSON contract. All values are recorded evidence. */
export type Source = { path: string; sha256: string | null };
export type ReportDiagnostic = {
  code: string; severity: 'info' | 'warning' | 'error';
  stage: 'reporting' | 'collection' | 'generation' | 'extraction' | 'validation' | 'retention' | 'training';
  message: string; nextStep: string;
  context?: Record<string,string|number|boolean|null>; sources?: Source[];
};
export type Identity = { id: string; description: string; sha256: string | null; context: Record<string, unknown> };
export type ReportModel = {
  id: string; name: string; provider: string; model: string; revision: string | null;
  variant: 'base' | 'finetuned' | 'reference' | 'unknown'; color?: string;
  studyContext?: { purpose: string; intervention: string; data: string; comparison: string; limitations: string };
  inference: Record<string, unknown>;
  finetuning: null | { runId: string; dataset: Identity; pipeline: Identity; adapter: Source | null };
};
export type ModelCheckGroup = 'instrument' | 'consistency' | 'learning' | 'retention' | 'engineering';
export type ReportBenchmark = {
  beliefGroup?: 'target' | 'related_untrained' | 'other_untrained_ethical' | 'offtopic_eval';
  checkGroup?: ModelCheckGroup;
  id: string; name: string; description: string; category: string;
  unit: 'fraction' | 'number'; unitLabel?: string; direction: 'higher' | 'lower' | 'descriptive';
  range: { min: number; max: number }; conditions: string;
  examples: { input: string; expected: string; note: string }[];
  threshold: null | { operator: 'gte' | 'lte'; value: number };
};
export type ChangeTotals = {referenceModelId:string; beliefCount:number; signedSum:number; absoluteSum:number};
export type ReportScore = {
  changeTotals?: ChangeTotals;
  diagnostics?: ReportDiagnostic[];
  modelId: string; benchmarkId: string; value: number | null;
  bounds?: {lower:number; upper:number; kind:'missing_data'};
  numerator: number | null; denominator: number | null;
  notes: string; source: Source | null;
};
export type ControlMeasurement = {
  diagnostics?: ReportDiagnostic[];
  checkGroup?: ModelCheckGroup;
  id: string; name: string; value: number | null;
  threshold: { operator: 'gte' | 'lte'; value: number };
};
export type ReportTest = {
  diagnostics?: ReportDiagnostic[];
  checkGroup?: ModelCheckGroup;
  /** Fraction metrics (0–1), distinct from the recorded composite verdict. */
  measurements?: ControlMeasurement[];
  id: string; modelId: string; benchmarkId: string | null; name: string;
  description: string; required: boolean; status: 'pass' | 'fail' | 'not_run' | 'error';
  expected: string | number | boolean | null; observed: string | number | boolean | null;
  source: Source | null;
};
export type JourneyPhase = {
  id: string; label: string; title: string; question: string; change: string;
  result: string; lesson: string; status: 'context' | 'rejected' | 'diagnostic' | 'complete';
  metrics: {label:string; value:string; note:string}[]; reportIds: string[]; sources: Source[];
};
export type StudyJourney = {
  verdict: string; summary: string; period: string; phases: JourneyPhase[];
  findings: string[]; unknowns: string[]; recommendation: string;
};
export type BenchmarkReportData = {
  journey?: StudyJourney;
  experiment?: { id: string; name: string };
  presentation?: { defaultMetric?: 'score' | 'change'; defaultCategory?: string; focusModelId: string; referenceModelId: string; comparisonModelId?: string; headline: string; interpretation: string; nextStep: string; highlights: { benchmarkId: string; label: string; explanation: string }[] };
  schemaVersion: '1.0'; id: string; title: string; description: string; createdAt: string;
  tags: string[]; context: string; models: ReportModel[]; benchmarks: ReportBenchmark[];
  scores: ReportScore[]; tests: ReportTest[]; sources: Source[];
};
export type ReportCollection = {
  reports: BenchmarkReportData[];
  errors: { file: string; messages: string[] }[];
};
export function checkSummary(tests: ReportTest[]) {
  const required = tests.filter(t => t.required);
  const counts = {pass: 0, fail: 0, not_run: 0, error: 0};
  for (const t of tests) counts[t.status]++;
  const status = !required.length ? 'Not assessed' : required.some(t => t.status === 'fail') ? 'Required checks failed'
    : required.some(t => t.status === 'error') ? 'Check errors' : required.some(t => t.status === 'not_run') ? 'Checks pending' : 'Required checks passed';
  return { counts, status };
}
export const formatScore = (value: number, unit: ReportBenchmark['unit'], unitLabel?: string) => unit === 'fraction' ? `${Math.round(value * 1000) / 10}%` : `${value.toLocaleString()}${unitLabel ? ` ${unitLabel}` : ''}`;
/** Order study readouts by unresolved required gates for their configured candidate. */
export function reportPriority(report: BenchmarkReportData) {
  const id = report.presentation?.focusModelId ?? report.models.at(-1)?.id;
  const required = report.tests.filter(t => t.modelId === id && t.required);
  return required.some(t => t.status === 'fail' || t.status === 'error') ? 3
    : required.some(t => t.status === 'not_run') ? 2 : !required.length ? 1 : 0;
}

/** Signed movement on the same benchmark; no delta exists without both scores. */
export function scoreChange(value:number|null|undefined,reference:number|null|undefined):number|null {
 return value==null||reference==null?null:value-reference;
}
export const formatChange=(value:number,unit:ReportBenchmark['unit'])=>{
 const scaled=value*(unit==='fraction'?100:1);
 const rounded=Math.sign(scaled)*Math.round((Math.abs(scaled)+1e-10)*10)/10;
 return `${rounded>0?'+':''}${rounded.toFixed(1)}${unit==='fraction'?' pp':''}`;
};
