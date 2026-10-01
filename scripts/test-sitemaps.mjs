import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const out=path.resolve('_site'), seen=new Set();
for(const name of ['pages','products']){
 const map=await fs.readFile(path.join(out,`sitemap-${name}.xml`),'utf8');
 for(const entry of map.matchAll(/<url><loc>(.*?)<\/loc><lastmod>(.*?)<\/lastmod><\/url>/g)){
  const url=new URL(entry[1]);
  assert.equal(url.origin,'https://alt-cam.net.ua');
  assert(!seen.has(url.href));seen.add(url.href);
  assert(!/admin|blanks|oauth|videospheterezhennia/.test(url.pathname));
  assert(Number.isFinite(Date.parse(entry[2])));
  const relative=url.pathname.slice(1)+(url.pathname.endsWith('/')?'index.html':'');
  const html=await fs.readFile(path.join(out,relative),'utf8');
  assert(html.includes(`rel="canonical" href="${url.href}"`),relative);
  assert.match(html,/<title>[^<]+<\/title>/);
  assert.match(html,/<meta[^>]+name="description"[^>]+content="[^"]+"/);
  assert(!/<meta[^>]+content="[^"]*noindex/.test(html),relative);
 }
}
assert(seen.size>10);
for(const relative of ['admin.html','admin/index.html','blanks/index.html','tiktok-oauth-callback.html']){
 assert((await fs.readFile(path.join(out,relative),'utf8')).includes('content="noindex,nofollow"'),relative);
}
console.log(`Sitemap audit passed: ${seen.size} existing canonical pages`);
