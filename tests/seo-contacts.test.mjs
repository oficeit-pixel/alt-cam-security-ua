import test from 'node:test';
import assert from 'node:assert/strict';
import {renderContacts} from '../scripts/contacts.mjs';
test('static footer has real configured destinations and no hash placeholders',()=>{
 const html='<footer><a class="js-phone is-hidden" href="#">Телефон</a><a class="js-facebook is-hidden" href="#">Facebook</a><a class="js-tiktok" href="#">TikTok</a></footer>';
 const out=renderContacts(html,{phone:'+380630607088',phoneLabel:'+380 63 060 70 88',facebook:'https://www.facebook.com/example'});
 assert(!out.includes('href="#"'));assert(!out.includes('is-hidden'));assert(!out.includes('TikTok'));
 assert(out.includes('tel:+380630607088'));assert(out.includes('https://www.facebook.com/example'));
});
