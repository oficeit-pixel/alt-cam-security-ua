import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {productCopy,cleanProductText} from './product-copy.mjs';
import {localizeCatalog} from './localize-catalog.mjs';
import {buildProductPages,productPath} from './build-product-pages.mjs';
import {finalizeSeo} from './finalize-seo.mjs';
const context={window:{}};
vm.runInNewContext(await fs.readFile('catalog-data.js','utf8'),context);
const products=localizeCatalog(context.window.ALTCAM_CATALOG);
const categories=[...new Set(products.map(p=>p.category))].sort();
// Seeded pseudo-random sampling for a repeatable audit across different categories.
let seed=47;
const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
const sample=categories.slice(0,20).map(category=>{
 const group=products.filter(p=>p.category===category&&p.price>0&&p.image&&p.model);
 return group[Math.floor(random()*group.length)];
}).filter(Boolean);
for(const p of products)if(sample.length<20&&!sample.includes(p)&&p.price>0&&p.image)sample.push(p);
const dir=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-product-copy-'));
try{
 await buildProductPages(dir,sample);await finalizeSeo(dir);
 const titles=new Set(),h1s=new Set(),descriptions=new Set();
 for(const p of sample){
  const html=await fs.readFile(path.join(dir,productPath(p.id),'index.html'),'utf8');
  const copy=productCopy(p),schema=JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);
  assert.equal(schema.name,copy.name);assert.equal(schema.sku,p.sku);
  assert.equal(cleanProductText(html.match(/<h1>([\s\S]*?)<\/h1>/)[1]),copy.name);
  assert.equal(cleanProductText(html.match(/<title>([\s\S]*?)<\/title>/)[1]),copy.title);
  assert.equal(schema.offers.priceCurrency,'UAH');assert.ok(schema.offers.price>0);
  assert.equal(schema.offers.availability,'https://schema.org/PreOrder');
  assert.ok(schema.image[0]?.startsWith('https://'));
  assert.ok(html.includes('property="og:image" content="'+copy.images[0].replaceAll('&','&amp;')+'"'));
  assert.ok(html.includes('name="twitter:card" content="summary_large_image"'));
  assert.ok(copy.title.length<=65);
  assert.doesNotMatch(copy.description,/&(?:deg|times|amp|nbsp);|●/);
  titles.add(copy.title);h1s.add(copy.name);descriptions.add(copy.description);
 }
 assert.equal(titles.size,sample.length);assert.equal(h1s.size,sample.length);assert.equal(descriptions.size,sample.length);
 const manual=products.flatMap(p=>productCopy(p).reasons.length?[{id:p.id,name:p.name,model:p.model,reasons:productCopy(p).reasons}]:[]);
 const out='outputs/product-copy-audit';await fs.mkdir(out,{recursive:true});
 const cell=s=>String(s).replaceAll('|','\\|').replaceAll('\n',' ');
 const report=['# Перевірка назв товарів','',`Перевірено ${sample.length} карток; ${new Set(sample.map(p=>p.category)).size} категорій. JSON-LD: JSON.parse + перевірка полів; не зовнішній Rich Results Test.`,'','| ID | Категорія | Старий title | Новий title |','|---|---|---|---|',...sample.map(p=>`| ${cell(p.id)} | ${cell(p.category)} | ${cell(cleanProductText(p.name)+' | ALT-CAM')} | ${cell(productCopy(p).title)} |`),'',`Ручна перевірка: ${manual.length} товарів. Повний список: manual-review.json.`];
 await fs.writeFile(path.join(out,'report.md'),report.join('\n'));
 await fs.writeFile(path.join(out,'manual-review.json'),JSON.stringify(manual,null,2));
 console.log(JSON.stringify({tested:sample.length,categories:new Set(sample.map(p=>p.category)).size,manual:manual.length,report:out}));
}finally{await fs.rm(dir,{recursive:true,force:true});}
