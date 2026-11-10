import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {kitPrice,renderKits} from '../scripts/kits.mjs';
test('owner prices are explicit, placeholders stay private',async()=>{
 const kits=JSON.parse(fs.readFileSync('data/kits.json','utf8'));assert.equal(kits.length,6);assert.equal(new Set(kits.map(k=>k.id)).size,6);
 assert.equal(kitPrice({price_from_with_install_uah:'TODO_OWNER'}),'за розрахунком');
 assert.match(kitPrice({price_from_with_install_uah:12345}),/12.*345 ₴ із монтажем/);
 const html=await renderKits(fs.readFileSync('index.html','utf8'));
 assert(!html.includes('TODO_OWNER'));
 assert.equal((html.match(/class="kit-price-note"/g)||[]).length,6);
 assert(!fs.readFileSync('script.js','utf8').includes('price.textContent = `Орієнтовно'));
});
function setup(storage){const w={localStorage:storage};vm.runInNewContext(fs.readFileSync('cart-state.js','utf8'),{window:w});vm.runInNewContext(fs.readFileSync('data/service-rates.js','utf8'),{window:w});return w;}
test('cart installation agrees with published examples',()=>{
 const w=setup({getItem:()=>null,setItem:()=>{}});
 for(const [indoor,outdoor,price] of [[2,0,2550],[2,2,4350],[4,4,6150]])assert.equal(w.AltcamCart.install({indoor,outdoor,nvr:true,mobile:true},w.ALTCAM_RATES),price);
});
test('cart survives page changes and storage failures do not throw',()=>{
 const values=new Map(),storage={getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v)};
 const first=setup(storage);first.AltcamCart.write([{id:'test',quantity:2}]);
 assert.equal(setup(storage).AltcamCart.read()[0].quantity,2);
 const blocked=setup({getItem:()=>{throw Error('blocked');},setItem:()=>{throw Error('blocked');}});
 assert.equal(blocked.AltcamCart.write([{id:'test',quantity:1}]),false);
 assert.equal(blocked.AltcamCart.read()[0].id,'test');
 values.set('altcam-cart','bad json');assert.equal(setup(storage).AltcamCart.read().length,0);
});
