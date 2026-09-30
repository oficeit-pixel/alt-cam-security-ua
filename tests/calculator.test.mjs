import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const context={window:{}};
for(const name of ['service-rates','calc-core','price-calculator'])vm.runInNewContext(fs.readFileSync(`data/${name}.js`,'utf8'),context);
const core=context.window.ALTCAM_CALC_CORE;
const video=values=>context.window.ALTCAM_PRICING.calculateVideo(new Map(Object.entries(values)));
test('negative, empty, nonfinite and excessive counts are bounded',()=>{
 for(const input of [-1,'',NaN,Infinity,'bad'])assert.equal(core.clampNumber(input,0,64,true),0);
 assert.equal(core.clampNumber(999,0,64,true),64);
 assert.equal(core.clampNumber(2.9,0,64,true),2);
 assert.equal(video({videoIndoor:999,videoOutdoor:-1,videoPtz:999}).indoor,64);
 assert.equal(video({videoPtz:999}).ptz,16);
});
test('zero cameras produces no equipment cost or deposit',()=>{
 const empty=video({videoIndoor:0,videoOutdoor:0,videoPtz:0,videoInstall:'on'});
 assert.equal(empty.policy.total,0);assert.equal(empty.policy.deposit,0);
});
test('zero watts means 10 W and finite autonomy',()=>{
 const input={load:0,capacityAh:100,batteryCount:2,voltage:12,dod:0.8,efficiency:0.9};
 const result=core.powerRuntime(input);
 assert.equal(result.load,10);
 assert.equal(result.runtimeHours,172.8);
 assert.deepEqual(result,core.powerRuntime({...input,load:10}));
});
test('DOM normalization honors attribute min/max',()=>{
 const fields=[{value:'999',min:'0',max:'64',step:'1'},{value:'0',min:'10',max:'30000',step:'10'},{value:'-3',min:'7',max:'500',step:'1'}];
 core.clampForm({querySelectorAll:()=>fields});
 assert.deepEqual(fields.map(f=>f.value),['64','10','7']);
});
