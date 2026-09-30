import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const context={window:{}};
vm.runInNewContext(fs.readFileSync('data/service-rates.js','utf8'),context);
vm.runInNewContext(fs.readFileSync('data/services.js','utf8'),context);
const rates=context.window.ALTCAM_RATES;
test('original calculator rates preserved; mixed camera work = 4350',()=>{
 assert.equal(rates.video.indoorCamera.one,1100);
 assert.equal(2*rates.video.indoorCamera.two+2*rates.video.outdoorCamera.two+rates.video.recorderSetup+rates.video.mobileAppSetup,4350);
 // The audit asks for 3600 for six outdoor cameras, but existing rates are 700 each.
 // Preserve the existing rate rather than silently applying an unapproved discount.
 assert.equal(6*rates.video.outdoorCamera.threeToEight,4200);
});
test('catalog uses shared rates and no unsupported bundle amounts',()=>{
 const video=context.window.ALTCAM_SERVICES.find(x=>x.id==='service-video');
 assert.match(video.options[0][1],/1\s100/);
 assert.equal(video.priceFrom,undefined);
 const catalog=fs.readFileSync('catalog.html','utf8');
 assert.ok(catalog.includes('data/service-rates.js'));
 assert.ok(!catalog.includes('service-rates-draft.js'));
 assert.ok(!fs.readFileSync('script.js','utf8').includes('indoorCamera: {'));
 assert.ok(!/25290|28238/.test(fs.readFileSync('catalog.js','utf8')));
 assert.ok(!/<strong class="package-price">від/.test(fs.readFileSync('index.html','utf8')));
});
