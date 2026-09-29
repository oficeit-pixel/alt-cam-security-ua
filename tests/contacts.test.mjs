import {test} from 'node:test';
import assert from 'node:assert/strict';
import {contacts,renderContacts} from '../scripts/contacts.mjs';
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
