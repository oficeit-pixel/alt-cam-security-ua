import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';
import {buildLocalPages,loadLandings} from './build-local-pages.mjs';
import {finalizeSeo} from './finalize-seo.mjs';
import {escape,markdown,faqEntries} from './lib/landing-md.mjs';
import {priceTable} from './lib/price-tables.mjs';
import {loadInstallationRates} from './product-seo.mjs';
const parent=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-landings-')),out=path.join(parent,'site');
try{
 await fs.mkdir(out);await fs.writeFile(path.join(out,'index.html'),'<html><head><title>ALT-CAM</title><meta name="description" content="Home"></head><footer><div class="footer-links"><h3>Послуги</h3></div></footer></html>');
 await buildLocalPages(out);await finalizeSeo(out);
 const pages=await loadLandings();assert.equal(pages.length,6);
 for(const {meta,sections} of pages){
  const html=await fs.readFile(path.join(out,meta.slug,'index.html'),'utf8');
  assert.equal((html.match(/<h1>/g)||[]).length,1);
  assert(html.includes(`<title>${escape(meta.title)}</title>`));assert(html.includes(`<h1>${escape(meta.h1)}</h1>`));
  assert(meta.title.length<=60);assert(meta.description.length<=155,meta.slug+' description');
  assert(!/style=|\[(ЗАПОВНИТИ|ПІДТВЕРДИТИ|ВСТАВИТИ)/.test(html));assert(html.includes('<table>'));
  const schemas=JSON.parse(html.match(/<script type="application\/ld\+json">(.*?)<\/script>/s)[1]);
  assert.equal(schemas[0].provider['@id'],'https://alt-cam.net.ua/#business');assert(schemas.find(s=>s['@type']==='BreadcrumbList'));
  const service=schemas[0],offers=service.offers;
  assert.equal(service['@id'],`https://alt-cam.net.ua/${meta.slug}/#service`);
  assert(service.areaServed.every(a=>a.name&&a['@type']));
  assert.equal(offers['@type'],'AggregateOffer');assert.equal(offers.priceCurrency,'UAH');
  assert.equal(offers.offerCount,offers.offers.length);
  assert.equal(offers.lowPrice,Math.min(...offers.offers.map(o=>o.price)));
  assert.equal(offers.highPrice,Math.max(...offers.offers.map(o=>o.price)));
  for(const o of offers.offers){assert(html.includes(o.name));assert(html.includes(o.price.toLocaleString('uk-UA')));}
  assert(html.includes('"@type":"HomeAndConstructionBusiness"'));
  const faq=schemas.find(s=>s['@type']==='FAQPage').mainEntity;
  assert.equal(faq.length,(html.match(/<details>/g)||[]).length);
  assert.equal(faq.length,faqEntries(sections.find(s=>s.title==='Часті запитання').body).length);
  for(const q of faq){assert(html.includes(escape(q.name)));assert(html.includes(escape(q.acceptedAnswer.text)));}
  const words=html.match(/<main[\s\S]*?<\/main>/)[0].replace(/<[^>]+>/g,' ').split(/\s+/).filter(Boolean).length;
  console.log(`${meta.slug}: ${words} words, ${faq.length} FAQ`);assert(words>=700);assert(faq.length>=5&&faq.length<=8);
  assert((await fs.readFile(path.join(out,'sitemap-pages.xml'),'utf8')).includes('/'+meta.slug+'/'));
 }
 assert(!markdown('Secret [ЗАПОВНИТИ: phone]').includes('Secret'));
 assert(markdown('[ЗАПОВНИТИ: phone]',{production:false}).includes('content-pending'));
 assert(!markdown('[click](javascript:alert)').includes('href='));
 const rates=await loadInstallationRates(),source=await fs.readFile(new URL('../content/price-tables.md',import.meta.url),'utf8');
 rates.video.indoorCamera.one=12345;assert(priceTable('T1',source,rates).includes((12345).toLocaleString('uk-UA')));
 assert.equal(2*rates.video.indoorCamera.two+2*rates.video.outdoorCamera.two+rates.video.recorderSetup+rates.video.mobileAppSetup,4350);
 console.log('Landing parser, FAQ, shared prices and sitemap passed');
}finally{await fs.rm(parent,{recursive:true,force:true});}
