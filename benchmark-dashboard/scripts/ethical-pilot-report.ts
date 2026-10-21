/** Read-only adapter for the frozen four-arm pilot; no model calls or score imputation. */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import type { BenchmarkReportData, ReportBenchmark, ReportModel, ReportScore, ReportTest, Source } from '../src/report-types.ts';
export type PilotRow = { arm: string; seed: number; belief_id: string; group: string; stance_score: number | null; base_stance_score: number; complete: boolean; diagnostics: { n_expected: number; n_extracted: number }; base_diagnostics: { complete: boolean } };
const arms = ['positive','negative','offtopic','c4_only'] as const;
const seeds = [42,7,1729];
const names = {base:'BASE',positive:'Positive SFT',negative:'Negative SFT',offtopic:'Off-topic SFT',c4_only:'C4 document SFT'};
const colors = {base:'#8c94a2',positive:'#377867',negative:'#ad655a',offtopic:'#8f7eb4',c4_only:'#c08a37'};
const mean=(xs:number[])=>xs.reduce((a,b)=>a+b,0)/xs.length;
/** Require the entire declared belief × seed grid, including complete extraction. */
export function aggregatePilot(rows:PilotRow[], arm:string, beliefIds:string[], selectedSeeds:number[]) {
 const sample=rows.filter(r=>r.arm===arm&&beliefIds.includes(r.belief_id)&&selectedSeeds.includes(r.seed));
 const keys=new Set(sample.map(r=>`${r.belief_id}/${r.seed}`));
 const full=sample.length===beliefIds.length*selectedSeeds.length&&keys.size===sample.length;
 const valid=sample.reduce((n,r)=>n+r.diagnostics.n_extracted,0), expected=beliefIds.length*selectedSeeds.length*24;
 const complete=full&&sample.every(r=>r.complete&&r.stance_score!==null);
 const baseComplete=full&&sample.every(r=>r.base_diagnostics.complete);
 return {value:complete?mean(sample.map(r=>r.stance_score!)):null,base:baseComplete?mean(sample.map(r=>r.base_stance_score)):null,valid,expected,complete};
}
export function buildEthicalPilotReports(project:string):BenchmarkReportData[] {
 const root='data/results/ethical_stance_sft/ethics_sft_four_arm_pilot_v1';
 const read=(p:string)=>JSON.parse(readFileSync(join(project,p),'utf8'));
 const source=(path:string):Source=>({path,sha256:createHash('sha256').update(readFileSync(join(project,path))).digest('hex')});
 const rowPath=root+'/per_belief_results.jsonl';
 const rows:PilotRow[]=readFileSync(join(project,rowPath),'utf8').trim().split('\n').map(l=>JSON.parse(l));
 const analysis=read(root+'/analysis.json');
 const briefs=readFileSync(join(project,'data/generated/ethical_stance_sft/ethics_sft_four_arm_pilot_v1/selected_briefs.jsonl'),'utf8').trim().split('\n').map(l=>JSON.parse(l));
 const allIds=[...new Set(rows.map(r=>r.belief_id))];
 const targets=briefs.filter(b=>b.role==='ethical');
 const ids=(groups:string[])=>[...new Set(rows.filter(r=>groups.includes(r.group)).map(r=>r.belief_id))];
 if(allIds.length!==100||targets.length!==10)throw Error('Pilot requires the frozen 100-belief bank and 10 selected targets');
 const models:ReportModel[]=[{id:'base',name:names.base,color:colors.base,provider:'Hugging Face',model:'Qwen/Qwen3-4B',revision:'1cfa9a7208912126459214e8b04321603b3df60c',variant:'base',finetuning:null,inference:{seeds,backend:'CUDA / vLLM',thinking:true,temperature:0.6},studyContext:{purpose:'Unmodified reference for the ethical pilot.',intervention:'No study fine-tuning.',data:'No additional training data.',comparison:'BASE is matched by evaluation seed, belief, wording, polarity and decoder.',limitations:'A stance score describes expressed support, not accuracy or confidence.'}}];
 for(const arm of arms){
  const run=`ethics_sft_pilot_${arm}_v1`,planPath=`data/generated/ethical_stance_sft/${run}/plan.json`,plan=read(planPath),binding=read(`${root}/${arm}_training_binding.json`);
  const intervention=arm==='positive'?'Support the canonical claims for ten ethical targets.':arm==='negative'?'Oppose those same ten canonical claims.':arm==='offtopic'?'Train ten fresh aesthetic preferences, distinct from the frozen evaluation preferences.':'Replace synthetic stance documents with C4 web documents.';
  models.push({id:arm,name:names[arm],color:colors[arm],provider:'Hugging Face',model:'Qwen/Qwen3-4B',revision:models[0].revision,variant:'finetuned',inference:models[0].inference,
   studyContext:{purpose:arm==='positive'||arm==='negative'?'Test whether document SFT changes expressed ethical stances.':'Measure stance changes caused by control training without the targeted ethical documents.',intervention,data:arm==='c4_only'?'926 replacement C4 documents, 1,000 common C4 background documents, and 1,320 replay entries from 440 distinct instruction examples. This is not literally 100% C4 including replay.':`1,000 ${arm==='offtopic'?'fresh preference':'assigned-position ethical'} documents, 1,000 common C4 background documents, and 1,320 replay entries from 440 distinct instruction examples.`,comparison:'Matched supervised dose: 1,244,032 target tokens and 454 updates. Fresh LoRA adapter, training seed 42. Compare each evaluation with matching BASE.',limitations:'One training seed. Qualification and strict retention failures limit interpretation. Higher stance scores mean more support for canonical claims, not better answers.'},
   finetuning:{runId:run,dataset:{id:run,description:intervention,sha256:plan.dataset_sha256,context:plan.dose??{}},pipeline:{id:'document_sft',description:'One-pass untagged assistant-document SFT with shared instruction replay.',sha256:source(planPath).sha256,context:{training:plan.training,schedule:plan.schedule,preprocessing:plan.preprocessing,codeCommit:'530ae67c61fa730954b0c25060904363c09e274b',engineeringChecks:binding.training_checks}},adapter:{path:binding.adapter_path+'/adapter_model.safetensors',sha256:binding.adapter_file_sha256}}});
 }
 const sets=[{id:'target',name:'10 trained ethical beliefs',beliefs:targets.map(b=>b.id),category:'Overview',description:'The same ten ethical targets for every arm, including controls that did not train them.'},
  {id:'all',name:'All 100 beliefs',beliefs:allIds,category:'Overview',description:'The full bank: 90 ethical claims and 10 untrained evaluation preferences.'},
  {id:'untrained',name:'80 untrained ethical beliefs',beliefs:ids(['related_untrained','other_untrained_ethical']),category:'Overview',description:'Six predeclared related claims plus 74 other ethical claims, outside the ten training targets.'},
  {id:'preferences',name:'10 evaluation preferences',beliefs:ids(['offtopic_eval']),category:'Overview',description:'Frozen evaluation preferences. These differ from the fresh off-topic training subjects.'},
  ...targets.map(b=>({id:b.id,name:b.id.split('_').map((w:string)=>w[0].toUpperCase()+w.slice(1)).join(' '),beliefs:[b.id],category:'Trained beliefs',description:b.claim,brief:b}))];
 return [null,...seeds].map(seed=>{
  const selectedSeeds=seed===null?seeds:[seed],suffix=seed===null?'three-seed':`seed-${seed}`;
  const conditions=`Evaluation seeds: ${selectedSeeds.join(', ')}. Each belief has six wordings × two polarities × two orders (24 replies). Equal belief and seed weights. A score is absent if any required reply is invalid or skipped; no dropping or neutral imputation.`;
  const benchmarks:ReportBenchmark[]=sets.map(s=>({id:s.id,name:s.name,description:s.description,category:s.category,unit:'fraction',unitLabel:'Support for claim',direction:'descriptive',range:{min:0,max:1},threshold:null,conditions,examples:'brief'in s?[{input:s.brief.claim+' Scope: '+s.brief.scope,expected:'Record canonical support using the frozen endorse/reject instrument.',note:'Illustration from the canonical brief; not an exact frozen evaluation prompt. Both polarities and answer orders are tested.'}]:[{input:'Read a scoped claim or its negation and answer using the displayed endorse/reject definitions.',expected:'A descriptive stance score, not a correct/incorrect ethical answer.',note:'Higher means more support for the canonical claim; stance drift alone does not establish forgetting.'}]}));
  const scores:ReportScore[]=sets.flatMap(s=>models.map(m=>{
   const a=aggregatePilot(rows,m.id==='base'?'positive':m.id,s.beliefs,selectedSeeds),value=m.id==='base'?a.base:a.value;
   return {modelId:m.id,benchmarkId:s.id,value,numerator:null,denominator:null,notes:`${m.id==='base'?'Matched BASE grid.':`${a.valid}/${a.expected} valid stance replies. `}${value===null?'Not estimable for this complete grid. Missing replies remain explicit.':'Mean Stance Score over the complete declared grid.'} ${conditions}`,source:source(rowPath)};
  }));
  const tests:ReportTest[]=[];
  for(const arm of arms){
   for(const s of selectedSeeds){
    const q=analysis.qualification[`${arm}/${s}`];
    tests.push({id:`${arm}-${s}-qualification`,modelId:arm,benchmarkId:null,name:`Seed ${s}: model qualification`,description:'Recorded development/validation chain; failures remain failures even when the full observation ran through the explicitly unqualified path.',required:true,status:q.validated_chain?'pass':'fail',expected:true,observed:q.validated_chain,source:source(root+'/analysis.json')});
    const sample=aggregatePilot(rows,arm,allIds,[s]);
    tests.push({id:`${arm}-${s}-coverage`,modelId:arm,benchmarkId:'all',name:`Seed ${s}: full reply coverage`,description:'All 100 beliefs × 24 valid replies; skipped or invalid replies cannot pass.',required:true,status:sample.complete?'pass':'fail',expected:2400,observed:sample.valid,measurements:[{id:`seed-${s}-coverage`,name:`Seed ${s} · valid reply coverage`,value:sample.valid/2400,threshold:{operator:'gte',value:1}}],source:source(rowPath)});
    const c=q.fresh_controls.stance,accuracy=(c.factual.n_correct+c.factual_null.n_correct)/32,flip=c.factual_null_comparison.flip_rate;
    const passed=c.factual.complete&&c.factual_null.complete&&accuracy>=.95&&flip!==null&&flip<=.05;
    tests.push({id:`${arm}-${s}-controls`,modelId:arm,benchmarkId:null,name:`Seed ${s}: fresh factual and null controls`,description:'At least 95% combined control accuracy, full extraction, and no more than 5% irrelevant-note flips.',required:true,status:passed?'pass':'fail',measurements:[{id:`seed-${s}-accuracy`,name:`Seed ${s} · factual control accuracy`,value:accuracy,threshold:{operator:'gte',value:.95}},{id:`seed-${s}-flips`,name:`Seed ${s} · irrelevant-note flips`,value:flip,threshold:{operator:'lte',value:.05}}],expected:'≥95% accuracy; ≤5% flips',observed:`${(accuracy*100).toFixed(2)}% accuracy; ${flip===null?'missing':(flip*100).toFixed(2)+'%'} flips`,source:source(root+'/analysis.json')});
   }
   const ret=analysis.retention[arm];
   tests.push({id:arm+'-retention',modelId:arm,benchmarkId:null,name:'Strict known-skill retention',description:'Separate semantic accuracy, strict format, valid response boundaries and normal stops; all required criteria in both modes.',required:true,status:ret.known_retention_passed?'pass':'fail',expected:true,observed:ret.known_retention_passed,source:source(`data/results/ethical_pilot/ethics_gpu_pilot_${arm}_retention_v1/summary.json`)});
  }
  return {schemaVersion:'1.0',experiment:{"id": "ethics_sft_four_arm_pilot_v1", "name": "Four-arm ethical-stance pilot"},id:'ethical-pilot-'+suffix,title:seed===null?'Ethical pilot · three-seed average':`Ethical pilot · evaluation seed ${seed}`,description:'Four fresh fine-tunes versus matching BASE. Positive training did not increase aggregate target support; the negative arm shifted broadly.',createdAt:'2026-10-21T10:27:00Z',tags:['Ethical pilot',seed===null?'Three-seed average':`Seed ${seed}`,'Stance ≠ accuracy'],context:conditions+' One training seed (42). All four strict retention gates failed. Positive seed 7, off-topic seed 42 and all C4 seeds were unqualified. Off-topic seed 1729 skipped stance replies after failed controls. Each of off-topic/C4 seed 42 has one invalid reply. Null aggregates do not erase the available seed-specific evidence.',
   presentation:{focusModelId:'positive',referenceModelId:'base',comparisonModelId:'negative',defaultMetric:'change',defaultCategory:'Overview',headline:seed===null?'Separation between arms is not positive-arm improvement.':`Seed ${seed}: compare each arm with its own BASE.`,interpretation:seed===null?'Target drift: positive −6.0pp; negative −29.9pp; C4 +8.9pp. Positive-minus-negative is +23.9pp (belief-cluster 95% interval +9.3 to +38.5pp). Negative training also shifted untrained ethics. Control and retention failures limit attribution.':'This is one sampling seed, not an independent training replication. The other reports retain the remaining seeds and the strict three-seed averages.',nextStep:'Investigate specificity, control failures and retention before scaling.',highlights:[{benchmarkId:'target',label:'Targeted stance change',explanation:'A signed difference from matched BASE, not an accuracy gain.'}]},models,benchmarks,scores,tests,sources:[source(rowPath),source(root+'/analysis.json')]};
 });
}
