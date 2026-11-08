import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import {buildLocalPages} from '../scripts/build-local-pages.mjs';
import {finalizeSeo} from '../scripts/finalize-seo.mjs';
import {segments} from '../content/audience-segments.mjs';
import {loadAudienceLandings} from '../scripts/audience-landings.mjs';
test('six segment routes open over HTTP with unique metadata, FAQ and reciprocal links',async()=>{
 const parent=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-audience-')),out=path.join(parent,'site');
 let server;
 try{
  await fs.mkdir(out);
  await fs.writeFile(path.join(out,'index.html'),await fs.readFile('index.html','utf8'));
  await buildLocalPages(out);await finalizeSeo(out);
  server=http.createServer(async(req,res)=>{try{const slug=new URL(req.url,'http://localhost').pathname;if(!/^\/dlia-[a-z]+\/$/.test(slug)){res.writeHead(404).end();return;}const html=await fs.readFile(path.join(out,slug,'index.html'));res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end(html);}catch{res.writeHead(404).end();}});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const home=await fs.readFile(path.join(out,'index.html'),'utf8'),sitemap=await fs.readFile(path.join(out,'sitemap-pages.xml'),'utf8');
  const titles=new Set(),headings=new Set();
  for(const s of segments){
   const response=await fetch('http://127.0.0.1:'+server.address().port+'/'+s.slug+'/');assert.equal(response.status,200);
   const html=await response.text(),title=html.match(/<title>(.*?)<\/title>/)[1],h1=html.match(/<h1>(.*?)<\/h1>/)[1];
   assert(!titles.has(title));titles.add(title);assert(!headings.has(h1));headings.add(h1);
   assert.equal((html.match(/<h1>/g)||[]).length,1);
   assert(html.includes('href="https://alt-cam.net.ua/'+s.slug+'/"'));
   assert(html.includes('property="og:title"'));assert(html.includes('property="og:description"'));assert(html.includes('property="og:url"'));assert(html.includes('property="og:image"'));
   assert(!/TODO_OWNER|noindex|Вартість за розрахунком/.test(html));
   assert(html.includes('Що зазвичай потрібно контролювати'));assert(html.includes('Типовий комплект'));assert(html.includes('Надішліть фото'));
   const schemas=JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);
   const faq=schemas.find(x=>x['@type']==='FAQPage');assert.equal(faq.mainEntity.length,4);
   assert(schemas.some(x=>x['@type']==='BreadcrumbList'));assert(!schemas[0].offers);
   assert(home.includes('href="/'+s.slug+'/" class="audience-card'));
   assert(home.match(/<footer[\s\S]*?<\/footer>/)[0].includes('/'+s.slug+'/'));
   assert(sitemap.includes('/'+s.slug+'/'));
   for(const city of ['montazh-videosposterezhennia-kyiv','videosposterezhennia-vyshhorod']){
    const page=await fs.readFile(path.join(out,city,'index.html'),'utf8');assert(page.match(/<main[\s\S]*?<\/main>/)[0].includes('/'+s.slug+'/'));
   }
  }
  const landings=await loadAudienceLandings();
  for(const p of landings){assert(p.meta.title.length<=65);assert(p.meta.description.length<=155);assert(!p.sections.find(s=>s.title==='Типовий комплект').body.join(' ').includes('₴'));}
 }finally{if(server)await new Promise(resolve=>server.close(resolve));await fs.rm(parent,{recursive:true,force:true});}
});
