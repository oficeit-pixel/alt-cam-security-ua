import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {buildTravelPages} from '../scripts/build-travel-pages.mjs';
import {regionalLinks} from '../scripts/regional-links.mjs';
test('only Ukrainian travel page is published; stale draft and language links removed',async()=>{
 const out=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-travel-'));
 try{
  const draft=path.join(out,'ru/zona-vyizdu/vartist-vyizdu/index.html');await fs.mkdir(path.dirname(draft),{recursive:true});await fs.writeFile(draft,'draft');
  await buildTravelPages(out);
  await assert.rejects(fs.access(draft));
  const html=await fs.readFile(path.join(out,'zona-vyizdu/vartist-vyizdu/index.html'),'utf8');
  assert.match(html,/<html lang="uk">/);assert.doesNotMatch(html,/hreflang="ru"|href="\/ru|Русский/);
  assert.match(html,/Розрахуємо при заявці/);assert.match(html,/60 км × 5 ₴ = 300 ₴/);
  const schema=JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);assert.equal(schema['@type'],'BreadcrumbList');
  assert.match(regionalLinks('<head></head><main></main>'),/href="\/zona-vyizdu\/vartist-vyizdu\/"/);
 }finally{await fs.rm(out,{recursive:true,force:true});}
});
