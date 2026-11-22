import test from 'node:test';
import assert from 'node:assert/strict';
import {localizeCatalog} from '../scripts/localize-catalog.mjs';
test('verified model correction preserves IDs, price and SKU',()=>{
 const item={id:'yugtorg-21292',model:'21292',name:'IP-камера IPC 5B36-X1S-30',sku:'21292',price:100};
 const [result]=localizeCatalog([item]);assert.equal(result.model,'IPC 5B36-X1S-30');
 assert.equal(result.id,item.id);assert.equal(result.sku,item.sku);assert.equal(result.price,item.price);assert.equal(item.model,'21292');
});
test('a changed supplier model or name is never silently overwritten',()=>{
 for(const item of [{id:'yugtorg-21292',model:'NEW',name:'IPC 5B36-X1S-30'},{id:'yugtorg-21292',model:'21292',name:'Different camera'}])assert.equal(localizeCatalog([item])[0].model,item.model);
});
