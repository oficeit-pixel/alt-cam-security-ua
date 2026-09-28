const test = require('node:test');
const assert = require('node:assert/strict');
const {buildLeadPayload, normalizePhone} = require('../lead-payload.js');
test('normalizes Ukrainian phone numbers without accepting arbitrary digits',()=>{
  for(const phone of ['063 060 70 88','+380 (63) 060-70-88','380630607088']) assert.equal(normalizePhone(phone),'+380630607088');
  assert.equal(normalizePhone('123'),'123');
});
for(const type of ['quiz','contact_form','quote_confirmation','catalog_consultation']) {
  test(`${type} includes contact, text and query-free page source`,()=>{
    const payload=buildLeadPayload(type,{name:' Тест ',phone:'0630607088',message:' Запит ',details:{cameras:2}},
      {origin:'https://example.test',pathname:'/catalog.html',search:'?private=x'});
    assert.deepEqual(payload.client,{name:'Тест',phone:'+380630607088',email:''});
    assert.equal(payload.message,'Запит');
    assert.equal(payload.source,'https://example.test/catalog.html');
    assert.equal(payload.details.cameras,2);
  });
}
test('empty message still contains client contacts',()=>{
  const payload=buildLeadPayload('contact_form',{name:'Тест',phone:'0630607088'}, {origin:'https://example.test',pathname:'/'});
  assert(payload.message.includes('+380630607088'));
});
