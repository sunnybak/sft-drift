import type { ReportDiagnostic, Source } from '../src/report-types.ts';
export type CoverageRow={seed:number;belief_id:string;complete:boolean;diagnostics:{n_expected:number;n_extracted:number;n_length_limited?:number};source_path?:string;source_sha256?:string};
export function coverageDiagnostics(rows:CoverageRow[],expected:number,valid:number,skippedSeeds:Map<number,Source>):ReportDiagnostic[]{
 const issues:ReportDiagnostic[]=[];
 const incomplete=rows.filter(r=>!r.complete);
 for(const seed of [...new Set(incomplete.map(r=>r.seed))]){
  const sample=incomplete.filter(r=>r.seed===seed),skipped=skippedSeeds.get(seed);
  const sources=[...new Map(sample.filter(r=>r.source_path).map(r=>[r.source_path!,{path:r.source_path!,sha256:r.source_sha256??null}])).values()];
  if(skipped){issues.push({code:'EVAL_SKIPPED_CONTROL_GATE',severity:'warning',stage:'collection',message:`Seed ${seed} collected no stance replies after its operational control gate failed. These are skipped presentations, not invalid generated answers.`,context:{seed,skipped_presentations:sample.reduce((n,r)=>n+r.diagnostics.n_expected,0)},nextStep:'Inspect the operational control failure in the source. A new evaluation requires a fresh run ID and an explicit collection policy.',sources:[skipped]});continue;}
  const missing=sample.reduce((n,r)=>n+r.diagnostics.n_expected-r.diagnostics.n_extracted,0),limited=sample.reduce((n,r)=>n+(r.diagnostics.n_length_limited??0),0);
  if(limited)issues.push({code:'GENERATION_TOKEN_LIMIT',severity:'warning',stage:'generation',message:`Seed ${seed} records ${limited} length-limited response(s) in incomplete belief grids. Inspect the raw replies to establish whether reasoning loops or another behavior consumed the budget.`,context:{seed,length_limited:limited,beliefs:sample.filter(r=>r.diagnostics.n_length_limited).map(r=>r.belief_id).join(', ')},nextStep:'Inspect generation metadata and final-answer extraction in the run’s stance_observations.jsonl. Do not change the historical decoder or overwrite this run.',sources});
  if(missing)issues.push({code:'REPLY_MISSING_OR_INVALID',severity:'warning',stage:'extraction',message:`Seed ${seed} has ${missing} required reply/replies without a valid extracted answer. This describes missingness; it does not by itself establish its cause.`,context:{seed,missing_or_invalid:missing,beliefs:sample.map(r=>r.belief_id).join(', ')},nextStep:'Use the source run and raw observations to distinguish absent output, format failure, truncation and backend errors.',sources});
 }
 issues.push({code:'INCOMPLETE_EVAL_GRID',severity:'warning',stage:'reporting',message:`${valid}/${expected} required replies are valid. This report withholds the exact complete-grid score instead of dropping or imputing missing replies. Model-check failure alone does not suppress a complete score.`,context:{valid,expected,missing:expected-valid},nextStep:'Inspect the collection/extraction diagnostics above. Use a separately identified follow-up report where available; preserve this historical result.'});
 return issues;
}
export function thresholdDiagnostic(code:string,name:string,value:number,operator:'gte'|'lte',threshold:number,sources:Source[],context:Record<string,string|number|boolean|null>={}):ReportDiagnostic[]{
 if(operator==='gte'?value>=threshold:value<=threshold)return [];
 return [{code,severity:'warning',stage:code.startsWith('RETENTION_')?'retention':'validation',message:`${name}: observed ${(value*100).toFixed(3)}%; required ${operator==='gte'?'at least':'at most'} ${(threshold*100).toFixed(3)}%.`,context:{...context,observed:value,operator,threshold},nextStep:'Inspect the failed presentations in the source artifact. This establishes a failed criterion, not its underlying causal mechanism.',sources}];
}

export type DiagnosticObservation={presentation_id:string;belief_id:string;answer:unknown;final_response:string|null;answer_extraction?:string;error?:string|null;generation_metadata?:{finish_reason?:string;generation_tokens?:number;backend_error?:unknown}};
export function observationDiagnostic(row:DiagnosticObservation,source:Source):ReportDiagnostic|null{
 if(row.answer!=null)return null;
 const m=row.generation_metadata??{};
 const context={presentation_id:row.presentation_id,belief_id:row.belief_id,finish_reason:m.finish_reason??null,generation_tokens:m.generation_tokens??null,extraction:row.answer_extraction??null,error:row.error??null};
 if(m.backend_error)return {code:'BACKEND_INFERENCE_ERROR',severity:'error',stage:'generation',message:'The observation records a backend inference error.',context:{...context,backend_error:String(m.backend_error)},nextStep:'Inspect the run log and backend error before planning a new run. Do not classify this as a model stance.',sources:[source]};
 if(m.finish_reason==='length')return {code:'GENERATION_TOKEN_LIMIT',severity:'warning',stage:'generation',message:`The reply reached its ${m.generation_tokens??'recorded'}-token generation limit and has no extracted answer.`,context:{...context,final_response:row.final_response},nextStep:'Inspect the raw reasoning and stop metadata. Any decoder change and repeat collection require a new run ID; keep this observation unchanged.',sources:[source]};
 if(row.final_response)return {code:'FINAL_ANSWER_FORMAT_INVALID',severity:'warning',stage:'extraction',message:'A final response exists, but the frozen answer extractor did not accept it. A readable stance is not necessarily a valid reply under the required exact format.',context:{...context,final_response:row.final_response.slice(0,500)},nextStep:'Compare the exact final response with the frozen extractor contract. Do not silently rescore a sentence as a valid one-word answer; a changed extractor requires a new instrument ID.',sources:[source]};
 return {code:'FINAL_ANSWER_UNAVAILABLE',severity:'warning',stage:'extraction',message:'No extractable final answer was recorded; the observation does not establish a more specific cause.',context,nextStep:'Inspect the exact raw output, reasoning boundaries and generation metadata in the source observation.',sources:[source]};
}
