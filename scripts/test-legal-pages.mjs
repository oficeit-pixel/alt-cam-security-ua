import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {buildLegalPages} from './build-legal-pages.mjs';
const parent=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-legal-')),out=path.join(parent,'site');
try{
 await fs.mkdir(out);await buildLegalPages(out);
 for(const file of ['privacy-policy.html','terms-of-service.html','data-deletion.html']){
  const html=await fs.readFile(path.join(out,file),'utf8');
  assert.equal((html.match(/<h1>/g)||[]).length,1);
  assert(html.includes('id="uk" lang="uk"'));assert(html.includes('id="en" lang="en"'));
  assert(html.includes('mailto:altcam.ua@gmail.com'));assert(html.includes('href="tel:+380630607088"'));
  assert(!/\[(ЗАПОВНИТИ|ПІДТВЕРДИТИ)/.test(html));assert(!html.includes('Для Codex'));
 }
 const privacy=await fs.readFile(path.join(out,'privacy-policy.html'),'utf8');
 assert(privacy.includes('Neon Postgres'));assert(privacy.includes('Ваші права'));
 assert(privacy.includes('лише якщо ви погодилися'));assert(!privacy.includes('знеособлена статистика'));
 console.log('Legal pages passed: Ukrainian primary, English retained, contacts, no placeholders');
}finally{await fs.rm(parent,{recursive:true,force:true});}
