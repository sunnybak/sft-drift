import { existsSync, readFileSync, mkdirSync, writeFileSync, renameSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { buildEthicalPilotReports } from './ethical-pilot-report.ts';
import { validateReport } from '../server/validate-report.ts';
const project=fileURLToPath(new URL('../../belief-transfer/',import.meta.url));
const output='results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1';
if(!existsSync(join(project,'data/results/ethical_stance_sft/ethics_sft_four_arm_pilot_v1/analysis.json'))){console.log('Ethical pilot artifacts not restored; no synthetic report substituted.');process.exit(0);}
const registry=JSON.parse(readFileSync(join(project,'configs/handoff.json'),'utf8'));
if(!registry.include_paths.includes(output))throw Error('Register dashboard output before writing');
const reports=buildEthicalPilotReports(project);
for(const report of reports){const checked=validateReport(report);if(!checked.report)throw Error(`${report.id}: ${checked.errors.join('; ')}`);}
const directory=join(project,'data',output,'reports');mkdirSync(directory,{recursive:true});
for(const report of reports){const dest=join(directory,report.id+'.json');writeFileSync(dest+'.tmp',JSON.stringify(report,null,2)+'\n');renameSync(dest+'.tmp',dest);console.log(`Derived ${report.id}`);}
