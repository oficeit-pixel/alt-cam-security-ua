import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {selectBackupPower, classifyBackupPower, capacityWh, backupPowerName} from '../scripts/backup-power-selection.mjs';
import {localizeCatalog} from '../scripts/localize-catalog.mjs';
import {buildSeoPages} from '../scripts/build-seo-pages.mjs';
test('type rules exclude generators, car inverters and accessories',()=>{
  for(const name of ['Дизельний генератор 33 кВА','Інвертор автомобільний 12V pure sine','Інвертор 12 / 220V approximated','Карта SNMP для ДБЖ 12V mini','Корпус ДБЖ порожній']) assert.ok(!classifyBackupPower({name}).group,name);
  assert.equal(classifyBackupPower({name:'Інвертор 12V з чистою синусоїдою'}).group,'sine');
  assert.equal(capacityWh('LiFePO4 12.8V 100Ah'),1280);
  assert.equal(capacityWh('LiFePO4 2,56kWh'),2560);
  assert.ok(!classifyBackupPower({name:'Акумулятор LiFePO4 3840Wh'}).group);
  assert.equal(backupPowerName({name:'Інвертор BRAZZERS BCT-2000VA, 1100W, 12V DC'}),'Інвертор 2000 ВА 12 В');
});
test('real catalog yields relevant immutable selection and working CTA targets',async()=>{
  const context={window:{}};
  vm.runInNewContext(await fs.readFile('catalog-data.js','utf8'),context);
  const products=localizeCatalog(context.window.ALTCAM_CATALOG),before=JSON.stringify(products);
  const selected=selectBackupPower(products);
  assert.equal(selected.items.length,12);
  assert.deepEqual(selected.missing,[]);
  assert.equal(classifyBackupPower(selected.items[0]).group,'mini');
  assert.equal(JSON.stringify(products),before);
  for(const p of selected.items) assert.doesNotMatch(p.name,/генератор|SNMP|автомобільн|approximated/i);
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-power-'));
  try{
    await fs.writeFile(path.join(dir,'index.html'),'<footer class="footer"></footer>');
    await buildSeoPages(dir,products);
    const html=await fs.readFile(path.join(dir,'rezervne-zhyvlennia/index.html'),'utf8');
    assert.ok(html.includes('href="/#calculator"'));
    assert.ok((await fs.readFile('index.html','utf8')).includes('id="calculator"'));
    assert.ok(html.includes('https://t.me/AltCamSecurityUaBot'));
    assert.ok(html.includes('217,6 ÷ 70'));
    assert.doesNotMatch(html,/Дизельний генератор/);
    assert.doesNotMatch(html,/>[^<]*BRAZZERS[^<]*<\/a>/);
  } finally {await fs.rm(dir,{recursive:true,force:true});}
});
