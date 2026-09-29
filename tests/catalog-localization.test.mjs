import {test} from 'node:test';
import assert from 'node:assert/strict';
import {localizeCatalog,localizeText} from '../scripts/localize-catalog.mjs';
test('localizes known feed terms without changing product identity or numbers',()=>{
  const source={id:'yugtorg-1',name:'Камера 4 МП',description:'Гнучка настройка. Безопасность.',price:123.45,model:'настройка',image:'https://example.com/настройка.jpg',features:['Настройка 12 В']};
  const [result]=localizeCatalog([source]);
  assert.equal(result.description,'Гнучке налаштування. Безпека.');
  for(const field of ['id','price','model','image'])assert.equal(result[field],source[field]);
  assert.deepEqual(result.features,['Налаштування 12 В']);
  assert.equal(source.description,'Гнучка настройка. Безопасность.');
  assert.equal(localizeText('задачі автоматизації'),'задачі автоматизації');
});
