import {test} from 'node:test';
import assert from 'node:assert/strict';
import {contacts,renderContacts,renderBusinessDetails} from '../scripts/contacts.mjs';
import fs from 'node:fs';
test('unknown business facts and experience are not displayed',()=>{
 const source=fs.readFileSync('index.html','utf8');
 const html=renderBusinessDetails(source,{});
 assert(!html.includes('ALTCAM_EXPERIENCE'));
 assert(!html.includes('10+'));
 assert(!html.includes('data-business-details'));
});
test('configured legal details and warranties are escaped and rendered in public page footers',()=>{
 const values={legalName:'ФОП Тест <QA>',legalCode:'000000',legalAddress:'Тестова адреса',warrantyWorks:'Тестовий строк',warrantyEquipment:'За умовами виробника',yearsExperience:7};
 for(const file of ['index.html','catalog.html','delivery-and-returns.html']){
  const html=renderBusinessDetails(fs.readFileSync(file,'utf8'),values);
  assert.match(html,/<footer\b[\s\S]*data-business-details[\s\S]*<\/footer>/);
  assert(html.includes('ФОП Тест &lt;QA&gt;'));
  assert(html.includes('Гарантія на роботи: Тестовий строк'));
  assert.equal(renderBusinessDetails(html,values),html);
 }
 const home=renderBusinessDetails(fs.readFileSync('index.html','utf8'),values);
 assert(home.includes('Досвід роботи: 7 р.'));
});
test('partial facts do not imply a legal identity or invented warranty',()=>{
 const html=renderBusinessDetails('<body><footer></footer></body>',{legalCode:'000',legalAddress:'address',warrantyEquipment:'За умовами виробника'});
 assert(!html.includes('address'));
 assert(!html.includes('Гарантія на роботи'));
 assert(html.includes('Гарантія на обладнання'));
});
test('single public phone and email are rendered without JavaScript',()=>{
  const output=renderContacts('<a href="tel:+111">+111</a><a href="mailto:old@example.com">old@example.com</a>');
  assert(output.includes(`href="tel:${contacts.phone}"`));
  assert(output.includes(contacts.phoneLabel));
  assert(output.includes(`mailto:${contacts.email}`));
  assert(!output.includes('old@example.com'));
});
test('unconfigured messengers are not published',()=>{
  assert.equal(renderContacts('<a data-contact="whatsapp" hidden>WA</a><a data-contact="viber">Viber</a>'),'');
});
test('configured messengers render valid links and remove hidden',()=>{
  const html=renderContacts('<a data-contact="whatsapp" hidden>WA</a><a data-contact="viber">Viber</a>',{...contacts,whatsapp:'+380630607088',viber:'+380630607088'});
  assert(html.includes('https://wa.me/380630607088'));
  assert(html.includes('viber://chat?number=%2B380630607088'));
  assert(!html.includes(' hidden'));
});
test('manager and news channel are separate destinations',()=>{
  const html=renderContacts('<a data-contact="telegram">Написати</a><a data-contact="telegramChannel">Новини</a>');
  assert(html.includes(`https://t.me/${contacts.telegram}`));
  assert(html.includes(`https://t.me/${contacts.telegramChannel}`));
});
