import { readFileSync } from 'node:fs';
import { validateReport } from '../server/validate-report.ts';
const file = process.argv[2];
if (!file) { console.error('Usage: npm run validate:report -- reports/my-report.json'); process.exit(1); }
try {
  const result = validateReport(JSON.parse(readFileSync(file, 'utf8')));
  if (!result.report) { console.error(result.errors.join('\n')); process.exit(1); }
  console.log(`Valid BenchmarkReport v${result.report.schemaVersion}: ${result.report.id}`);
} catch (e) { console.error(String(e)); process.exit(1); }
