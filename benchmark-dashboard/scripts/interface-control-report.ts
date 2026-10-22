import type {BenchmarkReportData,ReportBenchmark,ReportScore,ReportTest,Source} from '../src/report-types.ts';
import {thresholdDiagnostic} from './report-diagnostics.ts';
type Counts={correct:number;expected:number;valid:number;strict:number};
type Split={passed:boolean;counts:Counts;domains:Record<string,Counts>;checks:Record<string,boolean>;note_comparison:{expected_pairs:number;eligible_pairs:number;disagreements:number;disagreement_rate:number|null}};
type Audit={complete:boolean;run_id:string;pending:string[];models:Record<string,{run_id:string;forms:Record<string,Record<string,Split>>}>};
type ReferenceRow={interface:string;split:string;domain:string;prompt:string;expected_word:string};
const forms=[['paired','Opposing positions · A/B'],['current','Existing · endorse/reject'],['explicit','Added negation reminder']] as const;
const splits=[['validation','Validation'],['development','Development']] as const;
function checked(c:Counts){
 if(!Number.isInteger(c.expected)||c.expected<=0||![c.correct,c.valid,c.strict].every(n=>Number.isInteger(n)&&n>=0&&n<=c.expected)||c.correct>c.valid||c.strict>c.valid)throw Error('Invalid control counts');
 return c;
}
export function interfaceControlReport(original:BenchmarkReportData,a:Audit,bank:ReferenceRow[],runtime:Record<string,Record<string,unknown>>,sources:Source[],createdAt:string):BenchmarkReportData{
 const ids=['base','positive','negative','offtopic','c4_only'];
 if(!a.complete||a.pending.length)throw Error('Complete interface analysis required; no partial substitute');
 if(ids.some(id=>!a.models[id]||!original.models.some(m=>m.id===id))||Object.keys(a.models).length!==5||original.models.length!==5||ids.some(id=>!runtime[id]))throw Error('All five fixed models required');
 const benchmarks:ReportBenchmark[]=[],scores:ReportScore[]=[],tests:ReportTest[]=[];
 for(const [form,name] of forms)for(const [split,splitName] of splits){
  const prefix=form+'-'+split;const category=name+' · '+splitName;
  const example=(domain:string)=>{
   const r=bank.find(r=>r.interface===form&&r.split===split&&r.domain===domain);
   if(!r)throw Error('Missing reference example');
   return {input:r.prompt,expected:form==='paired'?r.expected_word.toUpperCase():r.expected_word,note:'Stipulated reference position/fact, not the model’s own ethical judgment. Variants reuse the same objects.'};
  };
  for(const [metric,label,domain] of [['normative','Assigned-position correctness','normative'],['factual','Stated-fact correctness','factual'],['format','Exact answer format','normative'],['note','Unrelated-note flip rate','normative']] as const){
   const id=prefix+'-'+metric;const threshold={operator:metric==='note'?'lte' as const:'gte' as const,value:metric==='note'?.05:metric==='format'?1:.95};
   benchmarks.push({id,name:category+' · '+label,description:metric==='normative'?'Follow an explicitly assigned fictional normative position, including positive and negated targets.':metric==='factual'?'Use facts supplied directly in the prompt; this is not a memory-retention or arithmetic test.':metric==='format'?'Give the exact requested final word or uppercase letter, after the separate reasoning segment.':'Compare semantic choices with and without an unrelated note, using matched sampling seeds.',category,checkGroup:'instrument',unit:'fraction',direction:metric==='note'?'lower':'higher',range:{min:0,max:1},threshold,conditions:'Eight normative and eight factual objects per split. Each domain has96 correlated presentations;192 total per form/split.32 distinct contexts across both splits, not384 independent tests. Required gates apply only to the preselected paired interface.',examples:[example(domain)]});
   for(const model of original.models){
    const s=a.models[model.id].forms[form]?.[split];if(!s)throw Error('Missing interface/split');
    const c=checked(metric==='normative'||metric==='factual'?s.domains[metric]:s.counts);
    const pair=s.note_comparison;
    if(!Number.isInteger(pair.expected_pairs)||pair.expected_pairs<=0||pair.eligible_pairs>pair.expected_pairs||pair.disagreements>pair.eligible_pairs)throw Error('Invalid note comparison');
    const value=metric==='note'?pair.disagreement_rate:metric==='format'?c.strict/c.expected:c.correct/c.expected;
    if(metric==='note'&&value!==(pair.eligible_pairs?pair.disagreements/pair.eligible_pairs:null))throw Error('Note rate does not reconstruct');
    const code=metric==='note'?'NOTE_FLIP_RATE_ABOVE_MAXIMUM':metric==='format'?'STRICT_FORMAT_INCOMPLETE':'CONTROL_ACCURACY_BELOW_MINIMUM';
    scores.push({modelId:model.id,benchmarkId:id,value,numerator:value===null?null:metric==='note'?pair.disagreements:metric==='format'?c.strict:c.correct,denominator:value===null?null:metric==='note'?pair.eligible_pairs:c.expected,notes:'Known-reference language controls only. Historical arithmetic, retention and neutral memorization verdicts are separate and unchanged.',source:sources[0],diagnostics:value===null?[]:thresholdDiagnostic(code,category+' · '+label,value,threshold.operator,threshold.value,sources,{model:model.id,interface:form,split})});
   }
  }
  for(const model of original.models){
   const s=a.models[model.id].forms[form][split];
   if(s.passed!==Object.values(s.checks).every(Boolean))throw Error('Stored gate does not match its checks');
   tests.push({id:model.id+'-'+prefix,modelId:model.id,benchmarkId:null,checkGroup:'instrument',name:category+' · reference gate',description:'Each normative/factual domain>=95%correct, complete extraction, exact format, complete note pairs and<=5%note flips. This gate does not qualify general capability or ethical coherence.',required:form==='paired',status:s.passed?'pass':'fail',expected:true,observed:s.passed,source:sources[0],diagnostics:scores.filter(x=>x.modelId===model.id&&x.benchmarkId.startsWith(prefix+'-')).flatMap(x=>x.diagnostics??[]),measurements:[
    {id:prefix+'-extraction',name:category+' · recognized answers',value:s.counts.valid/s.counts.expected,threshold:{operator:'gte',value:1}},
    {id:prefix+'-note-coverage',name:category+' · note-pair coverage',value:s.note_comparison.eligible_pairs/s.note_comparison.expected_pairs,threshold:{operator:'gte',value:1}},
   ]});
  }
 }
 return {schemaVersion:'1.0',id:'response-interface-controls',experiment:{id:a.run_id,name:'Response-interface diagnostic'},title:'Response interfaces · assigned-position checks',description:'Can the five existing models follow a stated position or supplied fact? Compare existing labels, a negation reminder and explicit opposing positions.',createdAt,tags:['32 reference contexts','Existing pilot weights','Not ethical stance scores'],context:'The preselected paired interface and the existing interface have a ceiling on these stipulated controls; this does not establish paired superiority or stable ethical judgments. Required checks cover paired task mapping only. The reminder is an ablation, not a fallback: its unconditional negation instruction can induce an unasked negation. Historical arithmetic, strict retention and neutral17/20failures remain failed. The separate full-belief paired readout measures relative forced preference and has its own BASE; it is not pooled with independent endorsement scores.',models:original.models.map(m=>({...m,inference:{...runtime[m.id],diagnosticRun:a.models[m.id].run_id,sampling:'Exact per-request seeds in the source bank; note RNG matched, identical-prompt repeat independently sampled.'},studyContext:{purpose:'Test whether the model follows explicitly assigned positions and supplied facts.',intervention:m.studyContext?.intervention??'Existing fixed pilot weights.',data:'32new reference contexts:16fictional normative positions and16stipulated facts, with correlated variants.',comparison:'Existing endorse/reject, added reminder and opposing-position A/Binterfaces on identical reference cases.',limitations:'These are assigned positions, not spontaneous ethical views, broad arithmetic ability or memory retention.'}})),benchmarks,scores,tests,sources};
}
