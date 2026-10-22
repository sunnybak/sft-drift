/** Derived, read-only views of the five stopped SFT repair attempts. */
import {readFileSync,statSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import type {BenchmarkReportData, ReportBenchmark, Source, ModelCheckGroup} from '../src/report-types.ts';

type Evidence = Record<string, any>;
const SFT='data/results/ethical_stance_sft/';
const PILOT='data/results/ethical_pilot/';
const WEIGHT=SFT+'ethics_sft_replay_weight_ablation_v1';
const LOWER=SFT+'ethics_sft_lower_lr_probe_v1';
const V5=SFT+'ethics_sft_replay_coverage_value_v5';
const FINAL=PILOT+'ethics_gpu_base_reasoning_recovery_v1';
const PROTOCOL='data/generated/ethical_stance_sft/ethics_sft_base_reasoning_replay_probe_v1/protocol.json';
const GEN='data/generated/ethical_pilot/ethics_gpu_base_reasoning_recovery_v1';
const examples=[{input:'Multiply 1152 by 21. End with one integer.',expected:'24192',note:'An illustrative procedural task, not an ethical stance.'}];

export function buildRepairReports(project:string):BenchmarkReportData[] {
 const reports:BenchmarkReportData[]=[];
 const definitions=[
  {id:'repair-normalization',title:'Repair 1 · corrected loss normalization',role:'norm1',root:WEIGHT,report:'2026-10-22-replay-weight-comparison-results.md',description:'Correct the accumulated weighted loss with ordinary replay weight. Retention passes; fresh model controls fail.'},
  {id:'repair-replay-weight',title:'Repair 2 · stronger instruction replay',role:'weight32',root:WEIGHT,report:'2026-10-22-replay-weight-comparison-results.md',description:'Increase the replay weight to 32 with corrected normalization. No demonstrated reliability repair.'},
  {id:'repair-lower-lr',title:'Repair 3 · lower learning rate',role:'candidate',root:LOWER,report:'2026-10-22-lower-lr-probe-results.md',description:'Reduce learning rate from 0.0001 to 0.000025 with other training factors matched. Retention and qualification still fail.'},
  {id:'repair-expanded-replay',title:'Repair 4 · expanded replay coverage',role:'candidate',root:V5,report:'2026-10-22-replay-value-v5-results.md',description:'Add balanced factual decision examples and broader replay coverage. Learning does not establish held-out reliability.'},
  {id:'repair-base-reasoning',title:'Repair 5 · full BASE reasoning · rejected',role:'candidate',root:FINAL,report:'2026-10-22-base-reasoning-final-results.md',description:'Replay complete BASE reasoning. Final diagnostics fail; the user stopping condition ends collection. No full-100 final aggregate.'},
 ];
 for(const def of definitions){
  const sources=new Map<string,Source>();
  const source=(path:string):Source=>{const s={path,sha256:createHash('sha256').update(readFileSync(join(project,path))).digest('hex')};sources.set(path,s);return s;};
  const read=(p:string):Evidence=>{source(p);return JSON.parse(readFileSync(join(project,p),'utf8'));};
  const rows=(p:string):Evidence[]=>{source(p);return readFileSync(join(project,p),'utf8').trim().split('\n').filter(Boolean).map(l=>JSON.parse(l));};
  const final=def.root===FINAL, v5=def.root===V5, lower=def.root===LOWER, weight=def.root===WEIGHT;
  const comparison=read(final?FINAL+'/final/retention_assessment.json':def.root+(weight?'/retention_comparison.json':'/comparison_v1.json'));
  // Read explicit review receipts; never substitute a live/pending controller verdict.
  const reviewPath=final?GEN+'/final_reviewed_verdict_v1.json':def.root+(v5?'/reviewed_verdict_v1.json':'/reviewed_comparison_v1.json');
  const review=read(reviewPath);
  if(final&&(!review.exact_flag_and_sample_coverage_verified||review.passed!==false))throw Error('Reviewed final rejection required');
  if(!final&&!((review.full_flagged_response_review_complete===true)||(review.failed_response_review_complete===true)||(review.full_response_review_complete===true)))throw Error('Completed manual review required: '+def.id);
  const reviewBindings=review.review_bindings??review.review_sources??review.source_sha256??{};
  for(const [name,hash] of Object.entries(reviewBindings)){
   const p=name.startsWith('data/')?name:def.root+'/'+name;
   if(source(p).sha256!==hash)throw Error('Review source changed: '+p);
  }
  if(final){const stop=read(FINAL+'/user_stop_on_negative_v1.json');if(stop.status!=='STOPPED_ON_REVIEWED_NEGATIVE'||stop.scientific_verdict!=='rejected')throw Error('Explicit reviewed stop required');}
  const bindingPath=final?SFT+'ethics_sft_base_reasoning_replay_probe_v1/candidate_training_binding.json':def.root+'/'+(weight?def.role:'candidate')+'_training_binding.json';
  const binding=read(bindingPath),trainId=binding.adapter_path.split('/').at(-2)!;
  const trainingPath=SFT+trainId+'/summary.json', training=read(trainingPath);
  if(training.training.status!=='COMPLETED')throw Error('Completed training required');
  const config=source(SFT+trainId+'/config.resolved.yaml');
  const runtime=read(PROTOCOL).runtime_reference;
  let baseRetention:Evidence,candidateRetention:Evidence,retentionPath:string;
  if(weight){
   retentionPath=WEIGHT+'/retention_comparison.json';
   baseRetention=read(PILOT+'ethics_gpu_replay_weight_confirmation_v1/base_assessment.json').by_mode_seed;
   candidateRetention=comparison.models[def.role].value_retention.by_mode_seed;
  }else if(lower){
   retentionPath=LOWER+'/comparison_v1.json';baseRetention=comparison.retention_models.base.value_retention.by_mode_seed;
   candidateRetention=comparison.retention_models.candidate.value_retention.by_mode_seed;
  }else if(v5){
   retentionPath=V5+'/comparison_v1.json';baseRetention=comparison.models.base.retention.by_mode;candidateRetention=comparison.models.candidate.retention.by_mode;
  }else{
   retentionPath=FINAL+'/final/retention_assessment.json';baseRetention=read(SFT+'ethics_sft_replay_coverage_probe_v4/base_retention_assessment.json').by_mode;candidateRetention=comparison.by_mode;
  }
  const r:BenchmarkReportData={schemaVersion:'1.0',id:def.id,title:def.title,description:def.description,
   experiment:{id:def.id,name:'SFT pipeline repairs · '+def.title.split(' · ').slice(1).join(' · ')},
   createdAt:final?read(FINAL+'/user_stop_on_negative_v1.json').stopped_at_utc:statSync(join(project,reviewPath)).mtime.toISOString(),
   tags:['Pipeline repairs','Rejected','One training seed',...(final?['Stopped · partial collection']:[])],
   context:'All five repair attempts failed the complete required suite. Each report uses its own matched BASE task bank; different banks and denominators must not be pooled. Primary charts use evaluation seed 42; additional recorded runtime repeats have their own category and are not training replications. C4 plus neutral replay, without ethical treatment documents. No broad knowledge-erasure claim. '+(final?'Final is the fixed endpoint. Midpoint cannot rescue it. The goal is paused; no new experiments.':'Historical scores and thresholds are unchanged.'),
   models:[{id:'base',name:'BASE · matching reference',provider:'Qwen',model:runtime.model.pretrained,revision:training.training.model_revision,variant:'base',color:'#8c94a2',inference:{backend:runtime.backend,versions:runtime.versions,reportEvaluationSeed:42,taskSpecificDecoder:'See each referenced task manifest; reasoning and short-answer modes are separate.'},finetuning:null,
    studyContext:{purpose:'Reference for this specific benchmark bank.',intervention:'No study fine-tuning.',data:'The same task bank as the candidate in this report.',comparison:'Compare within a report; task banks differ between repair attempts.',limitations:'A correct reference subset does not imply perfect performance on every task.'}},
    {id:'candidate',name:def.title.split(' · ').slice(1).join(' · '),provider:'Qwen',model:runtime.model.pretrained,revision:training.training.model_revision,variant:'finetuned',color:'#ad655a',inference:{backend:runtime.backend,versions:runtime.versions,reportEvaluationSeed:42,taskSpecificDecoder:'See each referenced task manifest; reasoning and short-answer modes are separate.'},
     finetuning:{runId:trainId,dataset:{id:trainId,description:'C4 documents and neutral instruction replay; no ethical treatment documents.',sha256:training.manifest_sha256,context:{draws:training.draws,chunks:training.chunks,lossTokens:training.loss_tokens}},pipeline:{id:def.id,description:def.description,sha256:config.sha256,context:{steps:training.training.global_steps,trainingChecks:binding.training_checks}},adapter:{path:binding.adapter_path+'/adapter_model.safetensors',sha256:binding.adapter_file_sha256}},
     studyContext:{purpose:'Test whether a training repair preserves reliable behavior.',intervention:def.description,data:'Fresh Qwen3-4B adapter, C4 plus neutral replay.',comparison:'Matching BASE on the same diagnostic inputs. Final checkpoint fixed before outcomes.',limitations:'One training seed, narrow correlated task variants, incomplete broad capability validation. Rejected under recorded gates.'}}],
   benchmarks:[],scores:[],tests:[],sources:[],presentation:{focusModelId:'candidate',referenceModelId:'base',defaultMetric:'score',headline:'Training executed, but the full model-check suite did not pass.',interpretation:def.description,nextStep:'Study paused. Do not scale or lower gates. Any restart requires a separate bounded plan.',highlights:[{benchmarkId:'known-False',label:'Previously correct short answers',explanation:'Read exact retained counts; this is different from all-item accuracy.'}]}};
  function metric(id:string,name:string,description:string,category:string,group:ModelCheckGroup,threshold:number|null,ex=examples){
   const b:ReportBenchmark={id,name,description,category,checkGroup:group,unit:'fraction',direction:'higher',range:{min:0,max:1},conditions:'Seed 42; exact source cohort and assessment version retained. Counts are task presentations, not independent facts.',examples:ex,threshold:threshold===null?null:{operator:'gte',value:threshold}};r.benchmarks.push(b);
  }
  function score(modelId:string,id:string,n:number,d:number,p:string,notes:string){
   if(!Number.isInteger(n)||!Number.isInteger(d)||d<=0||n<0||n>d)throw Error('Invalid score counts '+id);
   r.scores.push({modelId,benchmarkId:id,value:n/d,numerator:n,denominator:d,source:source(p),notes});
  }
  function check(id:string,name:string,passed:boolean|null,group:ModelCheckGroup,p:string,description:string,benchmarkId:string|null=null){
   const ref=source(p);
   r.tests.push({id:'candidate-'+id,modelId:'candidate',benchmarkId,name,description,checkGroup:group,required:true,status:passed===null?'not_run':passed?'pass':'fail',expected:true,observed:passed,source:ref,
    ...(passed===false?{diagnostics:[{code:id.startsWith('completion-')?'INCOMPLETE_GENERATION':id==='note-stability'?'NOTE_FLIP_RATE_ABOVE_MAXIMUM':id==='recipe'?'REPAIR_RECIPE_REJECTED':id.startsWith('known-')||id.endsWith('-known')?'RETENTION_CONTRACT_FAILED':'RECORDED_MODEL_CHECK_FAILED',severity:'warning' as const,stage:id.startsWith('completion-')?'generation' as const:'validation' as const,message:name+': '+description,nextStep:'Inspect the bound raw replies and manual review. Keep the recorded gate unchanged; the study remains paused.',sources:[ref]}]}:{})});
  }
  for(const [mode,label] of [['True','Reasoning'],['False','Short answers']]){
   const key=weight||lower?mode+'/42':mode,b=baseRetention[key],c=candidateRetention[key];
   if(!b||!c||b.known_n!==c.known_n)throw Error('Matched cohort required');
   const id='known-'+mode;
   metric(id,label+' · retained BASE-correct answers','Fraction of the fixed BASE-correct task set still answered correctly. Gains elsewhere do not conceal losses.','Procedural retention','retention',.95);
   score('base',id,b.known_correct,b.known_n,weight?PILOT+'ethics_gpu_replay_weight_confirmation_v1/base_assessment.json':lower?retentionPath:v5?retentionPath:SFT+'ethics_sft_replay_coverage_probe_v4/base_retention_assessment.json','BASE-known cohort, not full-bank accuracy.');
   score('candidate',id,c.known_correct,c.known_n,retentionPath,'Recognized correctness; unscorable replies are not correct. Numeric retention alone does not clear completion or format checks.');
   check(id,label+' · complete retention contract',c.passed,'retention',retentionPath,'Recorded composite gate includes value retention, format, reference sufficiency and complete boundaries/stops.',id);
   metric('all-'+mode,label+' · all procedural questions','All-item correctness, including questions outside the BASE-known set. Kept separate from retention.','Procedural accuracy','retention',null);
   for(const [modelId,a] of [['base',b],['candidate',c]] as const)score(modelId,'all-'+mode,a.full?.correct??a.full_correct,a.full_n??64,modelId==='base'?r.scores.find(s=>s.modelId==='base'&&s.benchmarkId===id)!.source!.path:retentionPath,'Includes BASE-wrong tasks; do not interpret as known-item retention.');
   check('completion-'+mode,label+' · complete generation',c.complete_boundaries_and_stops,'retention',retentionPath,'All planned procedural responses must close normally with valid reasoning/final boundaries. A token-limit loop remains a failure.');
  }
  if(weight||lower)for(const seed of [7,1729])for(const [mode,label] of [['True','Reasoning'],['False','Short answers']]){
   const key=mode+'/'+seed,b=baseRetention[key],c=candidateRetention[key];if(!b||!c||b.known_n!==c.known_n)throw Error('Missing matched runtime repeat');
   const id='known-'+mode+'-seed-'+seed;
   metric(id,label+' · runtime seed '+seed,'Same trained weights and fixed BASE-known cohort. Runtime repeat, not a new training seed.','Runtime repeats','retention',.95);
   score('base',id,b.known_correct,b.known_n,weight?PILOT+'ethics_gpu_replay_weight_confirmation_v1/base_assessment.json':retentionPath,'Fixed cohort, same-seed BASE behavior.');
   score('candidate',id,c.known_correct,c.known_n,retentionPath,'Runtime repeat; do not pool correlated replies as independent facts.');
   check(id,label+' · retention seed '+seed,c.passed,'retention',retentionPath,'Recorded retention contract on this runtime repeat.',id);
  }
  const checks=Object.values(binding.training_checks) as boolean[];
  metric('engineering','Training and reload checks','Weights update, base stays frozen, finite loss, exact coverage, normalization and checkpoint reload checks.','Engineering','engineering',1);
  score('candidate','engineering',checks.filter(Boolean).length,checks.length,bindingPath,'Mechanical training correctness does not qualify model behavior. BASE is not trained, so no artificial BASE score is assigned.');
  check('engineering','Training engineering',checks.every(Boolean),'engineering',bindingPath,'All recorded training checks required.','engineering');
  // Fresh controls use persisted raw replies and supplied gold, never natural stance labels.
  let status:Evidence,readingId:string;
  if(final){status=read(PILOT+'ethics_gpu_base_reasoning_final_reading_s42_v1/partial_collection_status_v1.json');readingId='ethics_gpu_base_reasoning_final_reading_s42_v1';}
  else{const s=weight?read(WEIGHT+'/'+def.role+'_measurement_status.json'):v5?comparison.qualification:comparison.candidate_qualification;readingId=s.stance_run_id;status=weight?comparison.original_full100_status[def.role]:s.actual_coverage;}
  const controlsPath=PILOT+readingId+'/stance_controls.jsonl',controls=rows(controlsPath);
  const natural=rows(PILOT+readingId+'/stance_observations.jsonl');
  const baseControlsPath=PILOT+'ethics_gpu_vllm_base_v1/stance_controls.jsonl',baseControls=rows(baseControlsPath);
  const baseControlMap=new Map(baseControls.map(c=>[c.presentation_id,c]));
  for(const c of controls){const b=baseControlMap.get(c.presentation_id);if(!b||b.prompt!==c.prompt||b.expected!==c.expected)throw Error('Frozen control bank differs from BASE');}
  const expected=2400,recorded=natural.length,valid=natural.filter(x=>['agree','disagree'].includes(x.answer)).length;
  if(recorded!==(final?status.recorded_natural:status.recorded)||valid!==(final?status.valid_natural:status.valid))throw Error('Coverage disagrees with raw evidence');
  metric('fresh-controls','Fresh known-answer controls','Correct supplied arithmetic/control choices, distinct from ethical stance.','Fresh model checks','instrument',.95,[{input:'It is not the case that three times three equals eight.',expected:'endorse',note:'The negated false equality is true.'}]);
  score('candidate','fresh-controls',controls.filter(x=>x.answer===x.expected).length,controls.length,controlsPath,'Raw emitted final choices; strict parsing errors are not repaired by guessing intent.');
  score('base','fresh-controls',baseControls.filter(x=>x.answer===x.expected).length,baseControls.length,baseControlsPath,'Same frozen control prompts; historical BASE reading, not a new repeat.');
  const byId=new Map(controls.map(x=>[x.presentation_id,x]));let pairs=0,flips=0;
  for(const c of controls.filter(x=>x.control_kind==='factual_null')){const p=byId.get(c.presentation_id.replace('/factual_null/','/factual/'));if(!p||!c.answer||!p.answer)throw Error('Missing control pair');pairs++;if(c.answer!==p.answer)flips++;}
  if(pairs!==16)throw Error('Require complete note-pair grid');
  const fresh=r.scores.find(x=>x.modelId==='candidate'&&x.benchmarkId==='fresh-controls')!;check('fresh-controls','Fresh control accuracy',fresh.value!>=.95,'instrument',controlsPath,'Accuracy at least 95%.','fresh-controls');
  metric('note-stability','Irrelevant-note agreement','Fraction of matched control pairs whose answer is unchanged by an irrelevant note.','Fresh model checks','instrument',.95);
  let basePairs=0,baseFlips=0;for(const c of baseControls.filter(x=>x.control_kind==='factual_null')){const b=baseControlMap.get(c.presentation_id.replace('/factual_null/','/factual/'));if(!b||!c.answer||!b.answer)throw Error('Missing BASE note pair');basePairs++;if(c.answer!==b.answer)baseFlips++;}
  score('base','note-stability',basePairs-baseFlips,basePairs,baseControlsPath,'Same frozen controls, historical BASE reading.');
  score('candidate','note-stability',pairs-flips,pairs,controlsPath,'Equivalent to the frozen note-flip ceiling of 5%.');check('note-stability','Irrelevant-note invariance',flips/pairs<=.05,'instrument',controlsPath,'Frozen flip rate must be at most 5%; one flip in 16 fails.','note-stability');
  metric('collection','Stance replies recorded / planned','Collection coverage only; not stance correctness or a measure of preservation.','Collection','engineering',final?null:1);
  score('candidate','collection',recorded,expected,PILOT+readingId+'/stance_observations.jsonl',`${valid} valid; ${recorded-valid} invalid; ${expected-recorded} not recorded. No full-100 stance aggregate in this report.`);
  const baseNaturalPath=PILOT+'ethics_gpu_vllm_base_v1/stance_observations.jsonl';
  const baseNatural=rows(baseNaturalPath);score('base','collection',baseNatural.length,expected,baseNaturalPath,'Historical BASE collection coverage; not an accuracy score.');
  if(final)r.scores.find(s=>s.modelId==='candidate'&&s.benchmarkId==='collection')!.diagnostics=[{code:'USER_STOP_ON_REVIEWED_NEGATIVE',severity:'info',stage:'collection',message:'Intentionally partial after the user stopping condition. Missing replies are not model answers or a new quality failure.',nextStep:'Study paused; do not infer a full-100 aggregate.',sources:[source(FINAL+'/user_stop_on_negative_v1.json')]}];
  check('collection','Full stance collection',final?null:recorded===expected,'engineering',final?PILOT+readingId+'/partial_collection_status_v1.json':PILOT+readingId+'/measurement_summary.json',final?'Stopped by the user condition after decisive negative diagnostics. Missing results are not a new model-quality failure.':'All 2,400 planned natural replies must be recorded.','collection');
  r.tests.at(-1)!.required=false;
  if(final)r.tests.at(-1)!.diagnostics=[{code:'USER_STOP_ON_REVIEWED_NEGATIVE',severity:'info',stage:'collection',message:'Collection intentionally stopped after reviewed diagnostic rejection: 512 recorded, 511 valid, 1 invalid, 1888 not recorded. No full-100 aggregate.',nextStep:'Study paused. Preserve missingness; do not restart the measurement.',sources:[source(FINAL+'/user_stop_on_negative_v1.json')]}];
  if(v5||final){
   const cases=final?['seen_train','seen_eval','held_train','held_eval']:['held_eval'];
   for(const cell of cases){
    const candidatePath=final?FINAL+'/final/'+cell+'_assessment.json':V5+'/comparison_v1.json';
    const c=final?read(candidatePath):comparison.models.candidate.decisions;
    const baseSource=final?PILOT+'ethics_gpu_replay_interface_rca_v1/value_v3_summary.json':candidatePath;
    const baseAssessment=final?read(baseSource).conditions['base/'+cell].by_mode:comparison.models.base.decisions.full.by_mode;
    for(const [mode,label] of [['True','Reasoning'],['False','Short answers']]){
     const {correct:n,n:d}=baseAssessment[mode];
     const id=cell+'-'+mode;metric(id,({'seen_train':'Seen facts · training wording','seen_eval':'Seen facts · evaluation wording','held_train':'Held-out facts · training wording','held_eval':'Held-out facts · evaluation wording'} as Record<string,string>)[cell]+' · '+label,'Neutral factual decision accuracy. Seen facts test learning; held facts test transfer. These are correlated presentations.','Factual decisions','learning',null,[{input:'It is false that 345 × 635 equals 219076.',expected:'endorse',note:'Actual product is 219075; apply the outer negation.'}]);
     score('base',id,n,d,baseSource,'Matched BASE on the same questions; separately versioned values, original grades retained.');const f=c.full.by_mode[mode];score('candidate',id,f.correct,f.n,candidatePath,'Full-bank accuracy, not BASE-known retention.');
     if(cell==='held_eval'){
      const known=c.by_mode[mode];const k=id+'-known';metric(k,'Held factual retention · '+label,'Preservation on the fixed BASE-correct decision cohort. Not the all-item accuracy above.','Factual retention','retention',.95);
      score('base',k,known.known_n,known.known_n,candidatePath,'BASE correctness defines this cohort.');score('candidate',k,known.known_correct,known.known_n,candidatePath,'Known-item losses stay explicit.');check(k,'Held factual retention · '+label,known.passed,'retention',candidatePath,'Recorded decision-retention gate, including reference sufficiency and output requirements.',k);
     }
    }
   }
  }
  // Original development/validation verdicts are separate from the fresh reading checks.
  const prefix=final?'ethics_gpu_base_reasoning_final':weight?'ethics_gpu_replay_weight_'+def.role:v5?'ethics_gpu_replay_coverage':'ethics_gpu_lower_lr';
  for(const phase of ['development','validation']){
   const p=PILOT+prefix+'_'+phase+'_s42_'+(v5?'v5':'v1')+'/stance_study_summary.json';
   let d:Evidence|undefined;try{d=read(p);}catch(e){if((e as NodeJS.ErrnoException).code!=='ENOENT')throw e;}
   const passed=d?phase==='validation'?d.validation_passed:d.selected!==null:null;
   check(phase,'Original '+phase+' qualification',passed,'instrument',d?p:reviewPath,'Historical full qualification verdict; a fresh later pass does not erase a failed earlier gate.');
  }
  if(!r.tests.some(t=>t.required&&t.status==='fail'))throw Error('Reviewed rejection lacks a displayed failed criterion');
  check('recipe','Overall recipe accepted',false,'instrument',reviewPath,'Reviewed rejection. No repair qualified across all required checks.');
  if(final){
   const primary=r.scores.find(s=>s.modelId==='candidate'&&s.benchmarkId==='held_eval-False-known')!;
   r.presentation!.headline=`Rejected: ${primary.numerator}/${primary.denominator} previously correct held-out short answers retained.`;
   r.presentation!.highlights=[{benchmarkId:'held_eval-False-known',label:'Held-out short-answer retention',explanation:'The 95% gate requires 23/24. All-item accuracy and generation checks remain separate.'}];
   const priority=['held_eval-True-known','held_eval-False-known','held_eval-True','held_eval-False'];
   r.benchmarks.sort((a,b)=>(priority.includes(a.id)?priority.indexOf(a.id):99)-(priority.includes(b.id)?priority.indexOf(b.id):99));
  }
  r.sources=[...sources.values()];reports.push(r);
 }
 return reports;
}
