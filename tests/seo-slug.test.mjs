import {finalizeSeo} from '../scripts/finalize-seo.mjs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {buildSeoPages} from '../scripts/build-seo-pages.mjs';
test('correct category URL, legacy redirect and clean sitemap',async()=>{
 const out=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-slug-'));
 try{
  await fs.writeFile(path.join(out,'index.html'),'<html><head><title>Home</title><meta name="description" content="Home"></head><footer class="footer"></footer></html>');
  await fs.writeFile(path.join(out,'sitemap.xml'),'<urlset><url><loc>https://alt-cam.net.ua/videospheterezhennia/</loc></url></urlset>');
  await buildSeoPages(out,[]);
  await finalizeSeo(out);
  const old=await fs.readFile(path.join(out,'videospheterezhennia/index.html'),'utf8');
  const current=await fs.readFile(path.join(out,'videosposterezhennia/index.html'),'utf8');
  const map=await fs.readFile(path.join(out,'sitemap-pages.xml'),'utf8');
  assert.match(old,/content="noindex,follow"/);
  assert.match(old,/content="0;url=\/videosposterezhennia\/"/);
  for(const html of [old,current])assert.match(html,/rel="canonical" href="https:\/\/alt-cam.net.ua\/videosposterezhennia\/"/);
  assert.ok(!map.includes('videospheterezhennia'));
  assert.ok(map.includes('/videosposterezhennia/'));
 }finally{await fs.rm(out,{recursive:true,force:true});}
});
