import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';
import { buildLocalPages } from './build-local-pages.mjs';
const out = await fs.mkdtemp(path.join(os.tmpdir(), 'altcam-local-seo-'));
await fs.writeFile(path.join(out,'index.html'), '<footer class="footer"></footer>');
await fs.writeFile(path.join(out,'sitemap.xml'), '<urlset></urlset>');
await buildLocalPages(out);
for (const slug of ['montazh-videosposterezhennia-kyiv','videosposterezhennia-vyshhorod']) {
  const html = await fs.readFile(path.join(out,slug,'index.html'),'utf8');
  assert.equal((html.match(/<h1>/g)||[]).length,1);
  assert(html.includes('lang="uk"'));
  const schema = JSON.parse(html.match(/<script type="application\/ld\+json">(.*?)<\/script>/s)[1]);
  assert.equal(schema['@type'],'Service');
  assert(schema.areaServed.length > 0);
  assert(!schema.provider.address);
  assert((await fs.readFile(path.join(out,'sitemap.xml'),'utf8')).includes(`/${slug}/`));
  assert((await fs.readFile(path.join(out,'index.html'),'utf8')).includes(`/${slug}/`));
}
console.log('Local SEO: Ukrainian pages, schema, sitemap and navigation passed');
