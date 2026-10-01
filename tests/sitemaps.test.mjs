import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {finalizeSeo} from '../scripts/finalize-seo.mjs';
test('central maps exclude private pages and repair legal canonical',async()=>{
 const out=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-map-'));
 const html='<html><head><title>ALT-CAM</title><meta name="description" content="Опис"></head><body><a href=\'index.html#contacts\'>Контакти</a></body></html>';
 try{
  for(const name of ['index.html','privacy-policy.html','admin.html','blanks/index.html','products/example/index.html','tiktok-oauth-callback.html']){
   await fs.mkdir(path.dirname(path.join(out,name)),{recursive:true});await fs.writeFile(path.join(out,name),html);
  }
  await finalizeSeo(out);
  const pages=await fs.readFile(path.join(out,'sitemap-pages.xml'),'utf8');
  const products=await fs.readFile(path.join(out,'sitemap-products.xml'),'utf8');
  assert.equal((pages.match(/<url>/g)||[]).length,2);
  assert(!/admin|blanks|oauth/.test(pages));
  assert(products.includes('/products/example/'));
  const legal=await fs.readFile(path.join(out,'privacy-policy.html'),'utf8');
  assert(legal.includes('href="https://alt-cam.net.ua/privacy-policy.html"'));
  assert(legal.includes("href='/#contacts'"));
  assert((await fs.readFile(path.join(out,'admin.html'),'utf8')).includes('noindex,nofollow'));
  await finalizeSeo(out);
  const repeated=await fs.readFile(path.join(out,'privacy-policy.html'),'utf8');
  for(const marker of ['rel="canonical"','rel="icon"','property="og:url"'])assert.equal(repeated.split(marker).length,2);
 }finally{await fs.rm(out,{recursive:true,force:true});}
});
