/** Adapt preserved study summaries to the public BenchmarkReport contract. No model calls. */
import { existsSync, readFileSync, mkdirSync, writeFileSync, renameSync } from 'node:fs';
import { resolve, relative, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { validateReport } from '../server/validate-report.ts';
import type { BenchmarkReportData, ReportBenchmark, ReportModel, ReportTest, Source } from '../src/report-types.ts';
const app = resolve(fileURLToPath(new URL('..', import.meta.url)));
const project = resolve(app, '../belief-transfer');
const output = join(project, 'data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/reports');
const registry = JSON.parse(readFileSync(join(project, 'configs/handoff.json'), 'utf8'));
if (!registry.include_paths.includes('results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1')) throw Error('Register derived report root before execution');
const sha = (raw: string) => createHash('sha256').update(raw).digest('hex');
const read = (path: string): any | null => existsSync(join(project, path)) ? JSON.parse(readFileSync(join(project, path), 'utf8')) : null;
const source = (path: string): Source => ({ path, sha256: existsSync(join(project, path)) ? sha(readFileSync(join(project, path), 'utf8')) : null });
const view = read('data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/benchmarks.json');
if (!view) throw Error('Run npm run data to prepare the source view first');
const models: ReportModel[] = view.models.map((m: any) => {
  if (m.training_run_id && !/^[A-Za-z0-9_]+$/.test(m.training_run_id)) throw Error('Invalid training run ID');
  const planPath = `data/generated/ethical_stance_sft/${m.training_run_id}/plan.json`;
  const plan = m.training_run_id ? read(planPath) : null;
  const training = m.training_run_id ? read(`data/results/ethical_stance_sft/${m.training_run_id}/summary.json`) : null;
  const bindingSource = view.observations.find((o: any) => o.model === m.id && o.metric === 'controls')?.source;
  const validation = bindingSource ? read(bindingSource) : null;
  const binding = validation?.training_binding;
  return {
    id:m.id, name:m.name, provider:'Hugging Face', model:'Qwen/Qwen3-4B',
    revision:training?.training?.model_revision ?? '1cfa9a7208912126459214e8b04321603b3df60c',
    variant:m.id==='base'?'base':'finetuned',
    studyContext:{
      purpose:m.id==='base'?'Unmodified reference for measuring what fresh fine-tuning changes.':'Development pilot: test whether document training teaches invented registry facts while preserving basic instruction skills.',
      intervention:m.id==='base'?'No study fine-tuning.':m.id==='tagged'?'Train on documents with a special document marker, alongside instruction examples.':m.id==='untagged'?'Remove the special document marker while keeping the same document corpus and instruction examples.':m.description.replaceAll('DOCTAG','document marker').replaceAll('replay','repeated instruction examples'),
      data:m.id==='base'?'No additional study training data.': ['tagged','untagged'].includes(m.id)?'2,000 synthetic documents covering 20 invented registry facts, plus 2,000 C4 web documents. An additional 440 distinct instruction examples are each presented five times (2,200 training entries). These are neutral facts, not ethical beliefs.': 'Neutral registry learning data. The saved training manifest records the available dose and source details.',
      comparison:m.id==='base'?'Use as the reference on each matching benchmark and evaluation setting.':m.id==='untagged'?'Compare with Tagged + replay to examine the document-marker change, and with BASE to measure learning and retention.':m.id==='tagged'?'Compare with Untagged + replay to examine the document-marker change, and with BASE to measure learning and retention.':'Compare within the same benchmark and recorded evaluation settings; other training variants can differ in several ways.',
      limitations:'Development results reuse the same neutral facts and controls. They do not establish generalization to unseen facts or ethical-stance effects. Evaluation wording, thinking mode and response limits differ across benchmarks; inspect those conditions before comparing scores.',
    },
    inference:{note:'Benchmark-specific decoder/backend; see each benchmark and source. Do not treat all endpoints as one inference configuration.'},
    finetuning:m.id==='base'?null:{
      runId:m.training_run_id??m.id,
      dataset:{id:m.training_run_id??m.id,description:'Declared document training manifest; original synthetic/C4/replay identities preserved.',sha256:typeof plan?.dataset_sha256==='string'?plan.dataset_sha256:training?.manifest_sha256??null,context:plan?.dose??{}},
      pipeline:{id:'document_sft',description:m.description,sha256:plan?source(planPath).sha256:null,
        context:{hashKind:'Exact training plan file (not a hash of all source code)',planPath:plan?planPath:null,codeCommit:validation?.code_commit??null,training:plan?.training??{},schedule:plan?.schedule??{},preprocessing:plan?.preprocessing??{},engineeringChecks:training?.training?.checks??{}}},
      adapter:binding?.adapter_file_sha256?{path:binding.adapter_path+'/adapter_model.safetensors',sha256:binding.adapter_file_sha256}:null,
    },
  } satisfies ReportModel;
});
const colors: Record<string,string>={base:'#9299a4','raw-high':'#ac7758','raw-low':'#bba764','chat-high':'#9985ad','chat-low':'#71a4aa',varied:'#b87f93',tagged:'#e7ad5b',untagged:'#377867'};
models.forEach(m=>m.color=colors[m.id]);
function examples(id:string) {
  const examples = id==='math' ? [['What is three times three? Return only the integer.','9'],['What is five minus three? Return only the integer.','2']] : id.startsWith('recall') || id==='strict-lookup' ? [
    ['What is the assigned registry code for Talverin?','7311'],
    ['In the constructed registry, what four-digit code is assigned to Mosselune?','7890'],
  ] : id.startsWith('native') ? [
    ['Continue the supplied trained document prefix ending “Talverin is ”.','7311'],
    ['Continue the supplied prose prefix ending “Mosselune is ”.','7890'],
  ] : id.startsWith('retain') ? [
    ['Calculate 1023 + 2047. Return one integer in the final answer.','3070'],
    ['Convert pavomm to uppercase.','PAVOMM'],
  ] : [['Is “Two plus two equals four” true? Use the displayed endorse/reject definitions.','endorse'],['Is “Three times three equals eight” true?','reject']];
  return examples.map(([input,expected])=>({input,expected,note:'Illustrative task example, not the full scored prompt. Exact prompts, format constraints and decoder are in source artifacts.'}));
}
const benchmarks:ReportBenchmark[]=view.metrics.map((b:any)=>({id:b.id,name:b.name,description:b.description,category:b.group,unit:'fraction',direction:'higher',range:{min:0,max:1},conditions:'Benchmark-specific inputs, decoder, cohort and caps are defined by the saved source artifacts. ' + (b.id.startsWith('native') ? 'A supplied prefix is part of this diagnostic; do not equate it with free chat recall.' : b.id.startsWith('retain') ? 'Thinking and nonthinking presentations remain distinct; fixed-known scores exclude tasks BASE did not demonstrate.' : b.id==='math' ? 'Eight direct arithmetic queries, greedy nonthinking decoding; semantic numeric matching.' : b.id.startsWith('recall') || b.id==='strict-lookup' ? 'The two registry wordings reuse the same 20 mappings; strict code-only lookup remains a separate endpoint.' : 'Frozen factual/format/irrelevant-note controls. Pair stability is conditional on coverage; missing pairs must remain visible.'),examples:examples(b.id),threshold:b.threshold===null?null:{operator:'gte',value:b.threshold}}));
const tests:Record<string,ReportTest[]>={learning:[],retention:[],contract:[]};
for(const model of ['tagged','untagged']) {
  const run=model==='tagged'?'ethics_gpu_registry_replay_transfer_v1':'ethics_gpu_registry_untagged_transfer_v2';
  const path=`data/results/ethical_pilot/${run}/prospective_qualification.json`,q=read(path);
  if(!q)continue;
  for(const style of ['original_long','natural_registry']) {
    const key=`${q.training_run_id}/${style}`,v=q.checks[key];
    if(typeof v==='boolean')tests.learning.push({id:`${model}-${style}`,modelId:model,benchmarkId:style==='original_long'?'recall-original':'recall-natural',name:style==='original_long'?'Original wording recall ≥18/20':'Natural wording recall ≥18/20',description:'Recorded prospective candidate check; reused development mappings, no threshold changes.',required:true,status:v?'pass':'fail',expected:true,observed:v,source:source(path)});
  }
  const retained=model==='tagged'?'ethics_gpu_registry_replay_retention_v1':'ethics_gpu_registry_untagged_retention_v2';
  const rp=`data/results/ethical_pilot/${retained}/summary.json`,r=read(rp);
  if(r)for(const [mode,suffix] of [['True','thinking'],['False','nonthinking']]) {
    const v=r.by_mode[mode];tests.retention.push({id:`${model}-${suffix}-retention`,modelId:model,benchmarkId:`retain-${suffix}`,name:`${suffix} retention contract`,description:'Recorded known_passed gate: accuracy plus strict format, valid boundaries and normal stops on the fixed BASE-known cohort.',required:true,status:v.known_passed?'pass':'fail',expected:true,observed:v.known_passed,source:source(rp)});
  }
}
for(const m of models.filter(m=>m.id!=='base')) {
  const path=view.observations.find((o:any)=>o.model===m.id&&o.metric==='controls')?.source;
  if(!path)continue;
  const s=read(path),v=s?.arms?.adapter?.controls?.passed;
  if(typeof v==='boolean')tests.contract.push({id:`${m.id}-controls`,modelId:m.id,benchmarkId:'controls',name:'Frozen control contract',description:'Recorded combined factual/format/irrelevant-note/coverage checks. Scores alone do not determine this result.',required:true,status:v?'pass':'fail',expected:true,observed:v,source:source(path)});
  for(const [key,value] of Object.entries(s?.training_binding?.training_checks??{}))if(typeof value==='boolean')tests.contract.push({id:`${m.id}-engineering-${key}`,modelId:m.id,benchmarkId:null,name:key.replaceAll('_',' '),description:'Recorded training engineering check from the bound validation summary.',required:true,status:value?'pass':'fail',expected:true,observed:value,source:source(path)});
}
const configs=[
 {id:'registry-learning',title:'Can the model retrieve what it learned?',description:'Ordinary chat recall versus strict lookup and trained-prefix continuation.',ids:['base','tagged','untagged'],metrics:['recall-original','recall-natural','strict-lookup','native-chat'],tests:tests.learning,tags:['Learning','20 neutral mappings']},
 {id:'instruction-retention',title:'Did basic instruction skills survive?',description:'Fixed BASE-known retention, with formatting and stop behavior kept explicit.',ids:['base','tagged','untagged'],metrics:['retain-thinking','retain-nonthinking','retain-format-thinking','retain-stops-thinking','retain-full-nonthinking'],tests:tests.retention,tags:['Retention','Fixed known cohort']},
 {id:'training-contract',title:'Training and response contract',description:'Engineering and frozen-control results across the development candidates.',ids:models.map(m=>m.id),metrics:['controls','control-format','null-coverage','null-stability','math'],tests:tests.contract,tags:['Controls','Engineering']},
];
const presentations: Record<string, NonNullable<BenchmarkReportData['presentation']>> = {
 'registry-learning': {focusModelId:'untagged',referenceModelId:'base',comparisonModelId:'tagged',headline:'It learned the facts. Retrieval is still brittle.',interpretation:'Removing the document tag improved ordinary-chat recall from 1/20 to 17/20 in both wordings. This reused, single-seed development contrast supports improved retrieval; it does not establish independent reliability. Both families still miss the required 18/20.',nextStep:'Address wording-sensitive retrieval and document continuation, then confirm on genuinely fresh neutral mappings before ethical SFT.',highlights:[{benchmarkId:'recall-original',label:'Recall, original wording',explanation:'One more correct mapping is needed to reach this family’s 18/20 gate.'},{benchmarkId:'recall-natural',label:'Recall, natural wording',explanation:'The same 20 facts under a second question wording; not an independent replicate.'},{benchmarkId:'strict-lookup',label:'Code-only compliance',explanation:'Still 0/20: correct prose answers do not pass the separate code-only endpoint.'}]},
 'instruction-retention': {focusModelId:'untagged',referenceModelId:'base',comparisonModelId:'tagged',headline:'The tested instruction skills survived.',interpretation:'The current candidate passes both recorded fixed-known retention contracts. The earlier tagged model’s thinking-format/stop failure did not recur. This is preservation on these tasks, not proof of broad capability retention.',nextStep:'Keep these retention gates fixed while improving retrieval. Full qualification still depends on the separate learning checks and fresh confirmation.',highlights:[{benchmarkId:'retain-thinking',label:'Known skills, thinking',explanation:'All 64 previously demonstrated thinking tasks remain correct.'},{benchmarkId:'retain-nonthinking',label:'Known skills, nonthinking',explanation:'All 44 pretraining-known tasks remain correct; do not replace this denominator with all 64 items.'},{benchmarkId:'retain-full-nonthinking',label:'All nonthinking tasks',explanation:'59/64 includes tasks BASE did not demonstrate; the five misses are outside the fixed-known cohort.'}]},
 'training-contract': {focusModelId:'untagged',referenceModelId:'base',comparisonModelId:'tagged',headline:'The mechanics pass. That is not enough to qualify.',interpretation:'The current candidate passes its recorded engineering and frozen-control checks. These establish that training updates, reload and the tested response contract work. They do not override the failed ordinary-chat recall gates.',nextStep:'Preserve this implementation and control contract. Focus the next bounded experiment on retrieval robustness, not on weakening evaluation.',highlights:[{benchmarkId:'controls',label:'Factual and negation controls',explanation:'32/32 correct under the frozen instrument.'},{benchmarkId:'control-format',label:'Control answer format',explanation:'All 32 controls use the required final-answer format.'},{benchmarkId:'null-coverage',label:'Irrelevant-note coverage',explanation:'All 16 control pairs are eligible; stability is meaningful only with this coverage.'}]},
};
mkdirSync(output,{recursive:true});
for(const c of configs) {
  const selected=new Set(c.ids),metrics=new Set(c.metrics);
  const scores=view.observations.filter((o:any)=>selected.has(o.model)&&metrics.has(o.metric)).map((o:any)=>({modelId:o.model,benchmarkId:o.metric,value:o.value,numerator:o.numerator,denominator:o.denominator,notes:[o.note,o.length_stops===null?'':`Length stops: ${o.length_stops}`].filter(Boolean).join(' '),source:{path:o.source,sha256:o.source_sha256}}));
  const sources=[...scores.map((s:any)=>s.source),...c.tests.map(t=>t.source)].filter((s):s is Source=>s!==null);
  const report:BenchmarkReportData={presentation:presentations[c.id],schemaVersion:'1.0',id:c.id,title:c.title,description:c.description,createdAt:view.generated_at,tags:c.tags,context:'Read-only derived development evidence. Reused facts and controls, not independent held-out confirmation. This report covers only its declared checks, not full model qualification. Missing endpoints are not zero.',models:models.filter(m=>selected.has(m.id)),benchmarks:benchmarks.filter(b=>metrics.has(b.id)),scores,tests:c.tests,sources:[...new Map(sources.map(s=>[s.path,s])).values()]};
  const checked=validateReport(report);if(!checked.report)throw Error(`${c.id}: ${checked.errors.join('; ')}`);
  const dest=join(output,c.id+'.json');writeFileSync(dest+'.tmp',JSON.stringify(report,null,2)+'\n');renameSync(dest+'.tmp',dest);
  console.log(`Derived report ${c.id}: ${scores.length} scores, ${c.tests.length} checks → ${relative(project,dest)}`);
}
