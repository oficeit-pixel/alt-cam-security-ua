import fs from 'node:fs';
import {pathToFileURL} from 'node:url';

export function validateLighthouse(report) {
  if (report?.runtimeError) throw new Error('Lighthouse runtime error');
  const values = {
    performance: report?.categories?.performance?.score,
    LCP: report?.audits?.['largest-contentful-paint']?.numericValue,
    CLS: report?.audits?.['cumulative-layout-shift']?.numericValue,
    TBT: report?.audits?.['total-blocking-time']?.numericValue,
  };
  for (const [name, value] of Object.entries(values)) {
    if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) {
      throw new Error(`Missing or invalid Lighthouse metric: ${name}`);
    }
  }
  if (values.LCP === 0 || values.performance > 1) throw new Error('Invalid Lighthouse result');
  return values;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.argv.length < 3) throw new Error('Pass Lighthouse JSON report paths');
  for (const file of process.argv.slice(2)) {
    console.log(file, validateLighthouse(JSON.parse(fs.readFileSync(file, 'utf8'))));
  }
}
