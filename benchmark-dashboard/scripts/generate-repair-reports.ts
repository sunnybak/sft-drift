import {writeFileSync,renameSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
import {readFileSync} from 'node:fs';
import {buildRepairReports} from './repair-reports.ts';
import {validateReport} from '../server/validate-report.ts';
import {addReportDiagnostics} from '../src/diagnostics.ts';

const project=fileURLToPath(new URL('../../belief-transfer/',import.meta.url));
const output='results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1';
if(!JSON.parse(readFileSync(join(project,'configs/handoff.json'),'utf8')).include_paths.includes(output))throw Error('Unregistered report output');
// Build and validate the complete set before publishing any report.
const reports=buildRepairReports(project);
for(const r of reports){addReportDiagnostics(r);const result=validateReport(r);if(!result.report)throw Error(r.id+': '+result.errors.join('; '));}
for(const r of reports){const p=join(project,'data',output,'reports',r.id+'.json');writeFileSync(p+'.tmp',JSON.stringify(r,null,2)+'\n');renameSync(p+'.tmp',p);console.log('Derived '+r.id);}
