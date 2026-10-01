import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {selectIndexedProducts,productOffer,loadInstallationRates} from '../scripts/product-seo.mjs';
import {buildProductPages,productPath} from '../scripts/build-product-pages.mjs';
import {finalizeSeo} from '../scripts/finalize-seo.mjs';
const good={id:'camera',name:'Камера',category:'Камери відеоспостереження',price:1234.5,description:'Докладний опис обладнання. '.repeat(20),available:true};
test('quality selection is stable, capped and excludes thin/unpriced products',()=>{
 const items=Array.from({length:350},(_,i)=>({...good,id:`camera-${i}`}));
 items.push({...good,id:'thin',description:'Характеристики уточнюються.'},{...good,id:'free',price:0},{...good,id:'other',category:'Інструменти'});
 assert.equal(selectIndexedProducts(items).size,300);
 assert.deepEqual(selectIndexedProducts(items),selectIndexedProducts([...items].reverse()));
 assert(!selectIndexedProducts(items).has('thin'));
 assert(!selectIndexedProducts(items).has('free'));
 assert(!selectIndexedProducts(items).has('other'));
});
test('offers use finite UAH prices and conservative availability',()=>{
 for(const price of [0,-1,NaN,Infinity,null,'123'])assert.equal(productOffer({...good,price},'url'),null);
 assert.equal(productOffer(good,'url').availability,'https://schema.org/InStock');
 assert.equal(productOffer({...good,available:undefined},'url').availability,'https://schema.org/PreOrder');
 assert.equal(productOffer(good,'url').seller['@id'],'https://alt-cam.net.ua/#business');
});
test('rendered price equals Offer; no-price markup absent; sitemap matches selection',async()=>{
 const out=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-product-'));
 try{
  const items=[good,{...good,id:'thin',description:'Короткий опис'},{...good,id:'no-price',price:0},{...good,id:'unsafe',name:'</script><script>bad()</script>',price:0}].map(p=>({...p}));
  await buildProductPages(out,items);await finalizeSeo(out);
  const html=await fs.readFile(path.join(out,productPath(good.id),'index.html'),'utf8');
  const schema=JSON.parse(html.match(/<script type="application\/ld\+json">(.*?)<\/script>/s)[1]);
  assert.equal(schema.offers.price,good.price);assert.equal(schema.offers.priceCurrency,'UAH');
  assert(html.includes(good.price.toLocaleString('uk-UA')+' ₴'));
  assert(html.includes(`${(await loadInstallationRates()).video.indoorCamera.one} ₴`));
  const noPrice=await fs.readFile(path.join(out,productPath('no-price'),'index.html'),'utf8');
  assert(!noPrice.includes('application/ld+json'));assert(noPrice.includes('noindex,follow'));
  const map=await fs.readFile(path.join(out,'sitemap-products.xml'),'utf8');
  assert.equal((map.match(/<url>/g)||[]).length,1);assert(map.includes(productPath(good.id)));
 }finally{await fs.rm(out,{recursive:true,force:true});}
});
