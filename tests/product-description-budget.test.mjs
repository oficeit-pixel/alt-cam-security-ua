import {test} from 'node:test';
import assert from 'node:assert/strict';
import {productCopy} from '../scripts/product-copy.mjs';
test('product descriptions keep a bounded budget and complete CTA',()=>{
 for(const name of ['Камера Ajax 4 Мп','Балансир для акумуляторних батарей 12V DALY 4S 5A','Довга назва товару '.repeat(20)]){
  const {description}=productCopy({name,description:'Потужний активний балансир для акумуляторних батарей '.repeat(10)});
  assert(description.length<=155,description);
  assert(description.endsWith('Монтаж у Києві та Вишгороді, консультація безкоштовно.'));
  assert(!description.includes('….'));
 }
});
