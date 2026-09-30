import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {checkBuild} from '../scripts/test-build-guards.mjs';

async function fixture(t) {
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-guards-'));
  t.after(()=>fs.rm(root,{recursive:true,force:true}));
  await fs.writeFile(path.join(root,'index.html'),'<html lang="uk">ALT-CAM</html>');
  await fs.writeFile(path.join(root,'catalog-data.js'),'window.ALTCAM_CATALOG=[];');
  return root;
}
test('valid output passes',async t=>assert.deepEqual(await checkBuild(await fixture(t)),[]));
test('rejects inconsistent phone and unconfigured messenger',async t=>{
  const root=await fixture(t);
  await fs.writeFile(path.join(root,'contacts.html'),'<a href="tel:+111">Call</a><a href="https://wa.me/111">WA</a>');
  const errors=await checkBuild(root);
  assert(errors.some(e=>e.includes('inconsistent phone')));
  assert(errors.some(e=>e.includes('unconfigured WhatsApp')));
});
for (const marker of ['[ЗАПОВНИТИ: x]','[ПІДТВЕРДИТИ: x]','[ВСТАВИТИ: x]',
  'oficeit-pixel.github.io','firetron.com','TODO: вставити']) {
  test(`rejects ${marker}`,async t=>{
    const root=await fixture(t);
    await fs.mkdir(path.join(root,'nested'));
    await fs.writeFile(path.join(root,'nested','page.html'),marker);
    assert.equal((await checkBuild(root)).length,1);
  });
}
test('rejects oversized catalog',async t=>{
  const root=await fixture(t);
  await fs.truncate(path.join(root,'catalog-data.js'),25*1024*1024+1);
  assert((await checkBuild(root)).some(e=>e.includes('25 MiB')));
});
test('missing build fails',async t=>{
  const root=await fixture(t);
  await fs.unlink(path.join(root,'index.html'));
  await assert.rejects(checkBuild(root));
});
