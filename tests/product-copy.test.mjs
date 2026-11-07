import test from 'node:test';
import assert from 'node:assert/strict';
import {cleanProductText,productCopy} from '../scripts/product-copy.mjs';
test('decode entities and remove bullets without leaving encoded markup',()=>{
 assert.equal(cleanProductText('● 90&amp;deg; &times; 2 &#176; <b>PoE</b>'),'90° × 2 ° PoE');
});
test('generic cameras use known model, brand and resolution; unknown models flagged',()=>{
 const c=productCopy({name:'IP відеокамера',brand:'Ajax',model:'TurretCam',features:['4 МП','Живлення: PoE']});
 assert.equal(c.name,'Ajax TurretCam — IP відеокамера 4 Мп');
 assert.ok(c.title.length<=65);assert.ok(c.description.includes('PoE'));
 assert.ok(productCopy({name:'Відеодомофон',sku:'ABC'}).reasons.some(s=>s.includes('моделі')));
});
