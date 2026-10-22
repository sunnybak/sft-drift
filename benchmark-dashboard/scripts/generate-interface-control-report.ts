import {existsSync,readFileSync,writeFileSync,renameSync,statSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
import {interfaceControlReport} from './interface-control-report.ts';
import {validateReport} from '../server/validate-report.ts';
import {addReportDiagnostics} from '../src/diagnostics.ts';
const project=fileURLToPath(new URL('../../belief-transfer/',import.meta.url));
const root='data/results/ethical_pilot/ethics_gpu_interface_controls_v1';
if(!existsSync(join(project,root,'analysis.json'))){console.log('Interface controls incomplete; no partial report substituted.');process.exit(0);}
const read=(p:string)=>JSON.parse(readFileSync(join(project,p),'utf8'));
const source=(path:string)=>({path,sha256:createHash('sha256').update(readFileSync(join(project,path))).digest('hex')});
const output='results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1';
if(!read('configs/handoff.json').include_paths.includes(output))throw Error('Unregistered report output');
const generated='data/generated/ethical_pilot/ethics_gpu_interface_controls_v1';
const original='data/'+output+'/reports/scoped-policy-full-surface.json';
const analysis=read(root+'/analysis.json');
for(const s of analysis.sources)if(source(s.path).sha256!==s.sha256)throw Error('Interface evidence hash mismatch: '+s.path);
const bank=readFileSync(join(project,generated,'bank.jsonl'),'utf8').trim().split('\n').map(l=>JSON.parse(l));
const report=interfaceControlReport(read(original),analysis,bank,read(generated+'/protocol.json').runtime_evidence,[root+'/analysis.json',root+'/reviewed_report.md',generated+'/protocol.json',generated+'/bank.jsonl',original].map(source),new Date(statSync(join(project,root,'analysis.json')).mtimeMs).toISOString());
const stopped='data/results/ethical_pilot/ethics_gpu_paired_readout_v1/operator_stop.json';
if(existsSync(join(project,stopped))){
 const stop=read(stopped);
 if(stop.run_id!=='ethics_gpu_paired_readout_v1'||!stop.after.includes('STOPPED'))throw Error('Unverified follow-up stop');
 report.description+=' A later BASE readout exposed target-statement anchoring and was stopped.';
 report.context+=' The subsequent paired BASE readout was stopped for interpretation errors despite passing these assigned-reference checks. Its full comparison is incomplete; this assay does not qualify that readout. The protocol deviation and raw examples remain preserved.';
 report.sources.push(source(stopped),source('data/results/ethical_pilot/ethics_gpu_paired_readout_v1/reviewed_failed_candidate.md'));
}
addReportDiagnostics(report);
const checked=validateReport(report);if(!checked.report)throw Error(checked.errors.join('; '));
const path=join(project,'data',output,'reports',report.id+'.json');writeFileSync(path+'.tmp',JSON.stringify(report,null,2)+'\n');renameSync(path+'.tmp',path);
console.log('Derived '+report.id);
