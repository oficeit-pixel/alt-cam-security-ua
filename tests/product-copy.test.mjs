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

test('numeric generic labels retain actual supplied UPS models',()=>{
 const base={name:'ДБЖ під акб 12В/7A',brand:'EUROPOWER',features:['Вихідна напруга: 13.8 В']};
 const a=productCopy({...base,model:'EuroPower EP-UPS-1205(P)'});
 const b=productCopy({...base,model:'EuroPower EP-UPS-1203(M)'});
 assert.notEqual(a.name,b.name);assert.notEqual(a.title,b.title);
 assert.match(a.name,/EP-UPS-1205\(P\)/);assert.match(b.name,/EP-UPS-1203\(M\)/);
 assert(a.title.length<=65);assert(b.title.length<=65);
});
