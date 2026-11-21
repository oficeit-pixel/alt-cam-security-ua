import test from 'node:test';
import assert from 'node:assert/strict';
import {productCopies,productCopy} from '../scripts/product-copy.mjs';
import fs from 'node:fs';
import vm from 'node:vm';
import {localizeCatalog} from '../scripts/localize-catalog.mjs';
test('entire current catalog has unique bounded metadata without changing IDs',()=>{
 const context={window:{}};vm.runInNewContext(fs.readFileSync('catalog-data.js','utf8'),context);
 const items=localizeCatalog(context.window.ALTCAM_CATALOG),copies=productCopies(items);
 for(const field of ['name','title','description'])assert.equal(new Set([...copies.values()].map(c=>c[field])).size,items.length,field);
 for(const copy of copies.values()){assert(copy.title.length<=65);assert(copy.description.length<=155);}
});
test('duplicate labels use real SKU, preserve unique copy and do not guess models',()=>{
 const base={name:'Камера тестова',brand:'Brand',model:'MODEL',features:[]};
 const items=[{...base,id:'a',sku:'SKU-A'},{...base,id:'b',sku:'SKU-B'},{id:'c',name:'Окремий товар 123'}];
 const result=productCopies(items);
 for(const field of ['name','title','description'])assert.notEqual(result.get('a')[field],result.get('b')[field]);
 assert(result.get('a').name.includes('SKU-A'));
 assert.deepEqual(result.get('c'),productCopy(items[2]));
 for(const copy of result.values()){assert(copy.title.length<=65);assert(copy.description.length<=155);}
});
test('same SKU across suppliers is explicitly distinguished by catalog code',()=>{
 const copies=productCopies([{id:'supplier-a-1',sku:'MODEL',name:'Товар 123'},{id:'supplier-b-1',sku:'MODEL',name:'Товар 123'}]);
 assert(copies.get('supplier-a-1').name.includes('код каталогу supplier-a-1'));
 assert(copies.get('supplier-a-1').reasons.some(s=>s.includes('дублювання')));
});
