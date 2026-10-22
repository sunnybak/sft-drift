/** Presentation only: no new eligibility decisions or rescoring of model replies. */
import type { BenchmarkReportData, ReportBenchmark, ReportDiagnostic, ReportScore, ReportTest, Source } from '../src/report-types.ts';
type RecordData = Record<string, any>;
export function scopedReadoutReport(original:BenchmarkReportData, analysis:RecordData, cells:RecordData[], proofs:RecordData, retention:RecordData, sources:Source[], createdAt:string, arithmetic:BenchmarkReportData, beliefs:Record<string,{statement:string;scope:string}>):BenchmarkReportData {
 if(!analysis.complete || analysis.policy_id!=='scoped_stance_readout_v1')throw Error('A complete prospective scoped-policy analysis is required');
 const arms=['base','positive','negative','offtopic','c4_only'];
 if(arms.some(a=>!analysis.models[a]||!proofs[a]||!retention.models[a]))throw Error('All five models and check sources are required');
 if(cells.length!==500||arms.some(a=>new Set(cells.filter(c=>c.model===a).map(c=>c.belief_id)).size!==100))throw Error('Expected all100 beliefs for each model');
 if(Object.keys(beliefs).length!==100||cells.some(c=>!beliefs[c.belief_id]?.statement||!beliefs[c.belief_id]?.scope))throw Error('Full canonical claims and scopes are required');
 const models=arms.map(a=>{
  const m=original.models.find(m=>m.id===a);if(!m)throw Error('Missing model provenance: '+a);
  return {...m,inference:{...m.inference,measurementRunId:`ethics_gpu_scoped_readout_${a}_s42_v1`,evaluationSeed:42,validationPolicy:analysis.policy_id}};
 });
 const descriptions:Record<string,string>={all:'All 100 beliefs',target:'10 trained ethical targets',untrained_ethical:'80 untrained ethical claims',related_untrained:'6 related untrained claims',other_untrained_ethical:'74 other untrained ethical claims',offtopic_eval:'10 evaluation preferences'};
 const benchmarks:ReportBenchmark[]=[], scores:ReportScore[]=[], tests:ReportTest[]=[];
 const example=[{input:'A scoped canonical claim or its exact negation.',expected:'Endorse or reject; map the answer to support for the canonical claim.',note:'Support is descriptive, not accuracy or confidence. Valid contradictory answers remain.'}];
 const metric=(id:string,name:string,description:string,category:string,checkGroup?:'instrument'|'consistency'|'retention'):ReportBenchmark=>({id,name,description,category,checkGroup,unit:'fraction',direction:category==='Stance overview'||category==='Per belief'?'descriptive':'higher',range:{min:0,max:1},threshold:null,conditions:'One matched evaluation seed42, existing pilot weights and frozen decoder. Historical three-seed results are separate context.',examples:example});
 const diagnostics=(c:RecordData):ReportDiagnostic[]=>[
  ...(c.complete?[]:[{code:'INCOMPLETE_EVAL_GRID',severity:'warning' as const,stage:'reporting' as const,message:`${c.valid}/${c.expected} replies valid. No point estimate is substituted; bounds cover missing replies, not sampling uncertainty.`,nextStep:'Inspect failed raw replies and their stop/extraction metadata.',sources}]),
  ...c.eligibility_codes.map((code:string)=>({code,severity:'warning' as const,stage:'validation' as const,message:code==='SCOPED_CONTROL_FAILURE'?'This endpoint does not meet the scoped-comprehension requirement.':'This endpoint has less than99% valid coverage in the model or matched BASE.',nextStep:'Inspect this endpoint and matched BASE evidence; preserve all observations.',sources}))
 ];
 function addCell(arm:string,id:string,c:RecordData){
  scores.push({modelId:arm,benchmarkId:id,value:c.value,numerator:null,denominator:null,...(!c.complete?{bounds:{lower:c.lower,upper:c.upper,kind:'missing_data' as const}}:{}),diagnostics:diagnostics(c),notes:`${c.valid}/${c.expected} valid. Forward-policy eligible: ${c.eligible_under_forward_policy}. Eligibility does not clear legacy arithmetic or retention failures.`,source:sources[0]});
 }
 for(const [id,name] of Object.entries(descriptions)){
  benchmarks.push(metric(id,name,'Canonical claim support. Changes compare with this follow-up’s own fresh BASE.','Stance overview'));
  for(const arm of arms){const c=analysis.models[arm].endpoints[id];if(!c)throw Error('Missing endpoint '+id);addCell(arm,id,c);}
 }
 for(const cell of cells.filter(c=>c.model==='base')){
  const b=original.benchmarks.find(b=>b.id===cell.belief_id);
  const claim=beliefs[cell.belief_id];
  const name=b?.name??cell.belief_id.split('_').map((w:string)=>w[0].toUpperCase()+w.slice(1)).join(' ');
  benchmarks.push({...metric(cell.belief_id,name,claim.statement+' Scope: '+claim.scope,'Per belief'),examples:[{input:claim.statement,expected:'Report canonical claim support, not correctness.',note:'Scope: '+claim.scope}]});
 }
 for(const c of cells)addCell(c.model,c.belief_id,c);
 for(const [id,name] of [['order','Answer-order agreement'],['wording','Wording agreement'],['negation','Negation agreement']]){
  benchmarks.push(metric('agreement-'+id,name,'Consistency across matched presentations; not a qualification threshold.','Response consistency','consistency'));
  for(const arm of arms){const c=analysis.models[arm].agreement[id];if(!c)throw Error('Missing agreement '+id);scores.push({modelId:arm,benchmarkId:'agreement-'+id,value:c.rate_over_eligible,numerator:c.eligible?c.agreeing:null,denominator:c.eligible||null,notes:`${c.eligible}/${c.expected} pairs eligible; correlated pairs are not independent observations.`,source:sources[0]});}
 }
 for(const arm of arms){
  for(const t of arithmetic.tests.filter(t=>t.modelId===arm)){
   const form=t.id.slice(arm.length+1);
   const measurements=arithmetic.scores.filter(c=>c.modelId===arm&&c.benchmarkId.startsWith(form+'-')).flatMap(c=>{
    const b=arithmetic.benchmarks.find(b=>b.id===c.benchmarkId);
    return b?.threshold?[{id:'arithmetic-'+b.id,name:b.name,value:c.value,threshold:b.threshold,diagnostics:c.diagnostics}]:[];
   });
   tests.push({...t,id:'separate-arithmetic-'+t.id,required:false,benchmarkId:null,name:'Separate arithmetic · '+t.name,measurements});
  }
  for(const split of ['development','validation']){
   const s=proofs[arm].splits[split];
   tests.push({id:arm+'-scope-'+split,modelId:arm,benchmarkId:null,checkGroup:'instrument',name:'Scoped comprehension · '+split,description:'Explicit-premise reading, negation, response order and irrelevant notes; same frozen extractor. Not arithmetic or ethical-truth accuracy.',required:true,status:s.passed?'pass':'fail',expected:true,observed:s.passed,source:sources[1],measurements:[
    {id:'scope-'+split+'-accuracy',name:split+' · scoped accuracy',value:s.counts.accuracy,threshold:{operator:'gte',value:.95}},
    {id:'scope-'+split+'-format',name:split+' · strict format',value:s.counts.strict/s.counts.expected,threshold:{operator:'gte',value:1}},
    {id:'scope-'+split+'-extraction',name:split+' · extraction',value:s.counts.valid/s.counts.expected,threshold:{operator:'gte',value:1}},
    {id:'scope-'+split+'-note',name:split+' · note flips',value:s.note_comparison.disagreement_rate,threshold:{operator:'lte',value:.05}},
   ]});
  }
  for(const [id,name] of Object.entries(descriptions)){
   const c=analysis.models[arm].endpoints[id];
   tests.push({id:arm+'-eligibility-'+id,modelId:arm,benchmarkId:id,checkGroup:'instrument',name:name+' · scoped readout eligibility',description:'Both models pass scoped controls and each endpoint has at least99% valid replies. Missing point scores remain absent even where bounds are eligible.',required:true,status:c.eligible_under_forward_policy?'pass':'fail',expected:true,observed:c.eligible_under_forward_policy,source:sources[0],diagnostics:diagnostics(c)});
  }
  for(const seed of ['42','7','1729']){
   const r=retention.models[arm].by_seed[seed];if(!r)throw Error('Missing retention repeat '+seed);
   const n=r.by_mode.False;
   tests.push({id:arm+'-retention-'+seed,modelId:arm,benchmarkId:null,checkGroup:'retention',name:'Fixed retention · repeat '+seed,description:'Frozen combined gate, including perfect format. Not used to erase scoped stance observations. Nonthinking repeats are greedy, not independent samples.',required:false,status:r.known_retention_passed?'pass':'fail',expected:true,observed:r.known_retention_passed,source:sources[2],measurements:[
    {id:'retention-'+seed+'-accuracy',name:seed+' · known nonthinking accuracy',value:n.known.semantic_correct/n.known_n,threshold:{operator:'gte',value:.95}},
    {id:'retention-'+seed+'-format',name:seed+' · known nonthinking format',value:n.known.strict_format/n.known_n,threshold:{operator:'gte',value:1}},
   ]});
  }
 }
 return {schemaVersion:'1.0',id:'scoped-policy-full-surface',experiment:{id:analysis.run_id,name:'Scoped-policy pilot follow-up'},title:'Full belief surface · scoped validation',description:'Fresh matched BASE and all four pilot models; scoped reading, arithmetic and retention remain separate.',createdAt,tags:['All100 beliefs','One evaluation seed','Existing pilot weights'],context:analysis.interpretation+' Required checks describe the new scoped policy only. Old arithmetic, strict retention and neutral memorization failures remain failed. This report does not qualify the original experiment retroactively.',models,benchmarks,scores,tests,sources,presentation:{focusModelId:'positive',referenceModelId:'base',comparisonModelId:'negative',defaultMetric:'change',defaultCategory:'Stance overview',headline:'All five models, with separate checks.',interpretation:'One-seed technical follow-up. Missing-response bounds are not confidence intervals. Experimental off-topic/C4 controls remain alongside treatment arms.',nextStep:'Review targeted versus broad drift and historical sampling variability before proposing further training.',highlights:[{benchmarkId:'all',label:'Full belief surface',explanation:'Fresh matched BASE comparison with all100 beliefs retained.'}]}};
}
