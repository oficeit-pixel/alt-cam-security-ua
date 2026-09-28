import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const forbidden = ['[ЗАПОВНИТИ', '[ПІДТВЕРДИТИ', '[ВСТАВИТИ',
  'oficeit-pixel.github.io', 'firetron.com', 'TODO: вставити'];
export async function checkBuild(root = '_site') {
  const errors = [];
  // Missing output must not silently pass.
  await fs.access(path.join(root, 'index.html'));
  async function walk(dir) {
    for (const entry of await fs.readdir(dir, {withFileTypes:true})) {
      const file = path.join(dir, entry.name);
      if (entry.isSymbolicLink()) { errors.push(`${path.relative(root,file)}: symlink`); continue; }
      if (entry.isDirectory()) { await walk(file); continue; }
      if (!/\.(html|js|xml|json)$/i.test(entry.name)) continue;
      const body = await fs.readFile(file, 'utf8');
      for (const marker of forbidden) {
        if (body.includes(marker)) errors.push(`${path.relative(root,file)}: ${marker}`);
      }
    }
  }
  await walk(root);
  const catalog = await fs.stat(path.join(root,'catalog-data.js'));
  if (catalog.size > 25 * 1024 * 1024) errors.push('catalog-data.js: exceeds 25 MiB');
  return errors;
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    const errors = await checkBuild(process.argv[2] || '_site');
    if (errors.length) { console.error(errors.join('\n')); process.exitCode=1; }
    else console.log('Build guards passed');
  } catch (error) { console.error(`Build guards: ${error.message}`); process.exitCode=1; }
}
