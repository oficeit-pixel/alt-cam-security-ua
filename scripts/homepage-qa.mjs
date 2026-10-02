import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {buildHomepage,organizationSchema,homePriceTable} from './build-homepage.mjs';
import {renderContacts} from './contacts.mjs';
import {loadInstallationRates} from './product-seo.mjs';
const root=process.cwd(),html=renderContacts((await buildHomepage(await fs.readFile('index.html','utf8'))).replace('</head>','<link rel="stylesheet" href="/landing.css"></head>'));
assert(!/\[(ЗАПОВНИТИ|ПІДТВЕРДИТИ)/.test(html));
assert(!JSON.stringify(organizationSchema()).includes('"":""'));
const schema=organizationSchema({brandName:'ALT-CAM',phone:'',email:'',legalName:'',openingHours:''});
assert(!schema.telephone&&!schema.address&&!schema.legalName&&!schema.openingHours&&!schema.sameAs);
const rates=await loadInstallationRates();rates.video.indoorCamera.one=9876;assert(homePriceTable(rates).includes((9876).toLocaleString('uk-UA')));
const server=http.createServer(async(req,res)=>{try{const route=new URL(req.url,'http://localhost').pathname;if(route==='/'||route==='/index.html'){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(html);return;}const file=path.resolve(root,'.'+route);if(!file.startsWith(root+path.sep))throw Error();res.setHeader('Content-Type',file.endsWith('.css')?'text/css':file.endsWith('.js')?'application/javascript':file.endsWith('.png')?'image/png':file.endsWith('.webp')?'image/webp':'application/octet-stream');res.end(await fs.readFile(file));}catch{res.writeHead(404);res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}`;let browser;
try{
 browser=await chromium.launch({channel:process.env.PW_CHANNEL||undefined,headless:true});const page=await browser.newPage();
 await page.route('**/*',route=>route.request().url().startsWith(base)?route.continue():route.abort());
 for(const viewport of [{width:390,height:844},{width:768,height:1024},{width:1440,height:900}]){
  await page.setViewportSize(viewport);await page.goto(base);await page.waitForTimeout(600);
  assert.match(await page.locator('h1').innerText(),/Монтаж відеоспостереження.*Вишгороді/s);
  const box=await page.locator('.hero-phone').boundingBox();assert(box&&box.y>=0&&box.y+box.height<=viewport.height,`Phone below fold: ${JSON.stringify({viewport,box})}`);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Horizontal overflow');
  assert.equal(await page.locator('#lead-form').count(),1);
  const graph=JSON.parse(await page.locator('script[type="application/ld+json"]').first().textContent());
  const faq=graph.find(s=>s['@type']==='FAQPage');
  const questions=await page.locator('#faq summary').allTextContents();assert.deepEqual(faq.mainEntity.map(q=>q.name),questions.map(q=>q.trim()));
  const answers=await page.locator('#faq details p').allTextContents();assert.deepEqual(faq.mainEntity.map(q=>q.acceptedAnswer.text),answers.map(q=>q.trim()));
  assert.equal(graph[0]['@id'],'https://alt-cam.net.ua/#business');assert(!graph[0].aggregateRating);
  assert.equal(await page.locator('#installation-prices table').count(),1);
 }
 console.log('Homepage QA passed: phone above fold, FAQ/schema, prices and layout at 390/768/1440px');
}finally{await browser?.close();await new Promise(r=>server.close(r));}
