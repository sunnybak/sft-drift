import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { validateReport } from './validate-report.ts';
import type { ReportCollection } from '../src/report-types.ts';
/** Read JSON only from configured directories; never follow a client-supplied path. */
export function loadReports(directories: string[]): ReportCollection {
  const result: ReportCollection = { reports: [], errors: [] }, seen = new Set<string>();
  for (const directory of directories) {
    if (!existsSync(directory)) continue;
    for (const filename of readdirSync(directory, {withFileTypes:true}).filter(f => f.isFile() && f.name.endsWith('.json')).map(f=>f.name).sort()) {
      const file = join(directory, filename);
      try {
        const checked = validateReport(JSON.parse(readFileSync(file, 'utf8')));
        if (!checked.report) result.errors.push({ file: filename, messages: checked.errors });
        else if (seen.has(checked.report.id)) {
          result.reports = result.reports.filter(r => r.id !== checked.report!.id);
          result.errors.push({ file: filename, messages: [`Duplicate report id (all copies excluded): ${checked.report.id}`] });
        }
        else { seen.add(checked.report.id); result.reports.push(checked.report); }
      } catch (error) { result.errors.push({ file: filename, messages: [String(error)] }); }
    }
  }
  return result;
}
