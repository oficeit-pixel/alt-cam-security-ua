import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const context={window:{}};
vm.runInNewContext(fs.readFileSync('data/service-rates.js','utf8'),context);
vm.runInNewContext(fs.readFileSync('data/services.js','utf8'),context);
const rates=context.window.ALTCAM_RATES;
vm.runInNewContext(fs.readFileSync('data/calc-core.js','utf8'),context);
vm.runInNewContext(fs.readFileSync('data/price-calculator.js','utf8'),context);
vm.runInNewContext(fs.readFileSync('data/package-configs.js','utf8'),context);
test('all camera package estimates use the calculator configuration and remain finite',()=>{
 for(const config of Object.values(context.window.ALTCAM_PACKAGES)) {
  const estimate=context.window.ALTCAM_PRICING.calculateVideo(new Map(Object.entries(config)));
  assert.ok(Number.isFinite(estimate.policy.total) && estimate.policy.total>0);
  assert.equal(estimate.cameras,config.videoIndoor+config.videoOutdoor);
  assert.ok(estimate.nvrChannels>=estimate.cameras);
  assert.equal(estimate.policy.total,context.window.ALTCAM_PRICING.applyPricePolicy(estimate.cameraPrice+estimate.centralPrice,estimate.installation,estimate.materials).total);
  const withoutInstall=context.window.ALTCAM_PRICING.calculateVideo(new Map(Object.entries({...config,videoInstall:''})));
  assert.equal(withoutInstall.installation,0);
  assert.ok(withoutInstall.policy.total<estimate.policy.total);
 }
});
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
