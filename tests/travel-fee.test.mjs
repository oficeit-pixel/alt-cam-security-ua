import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {settlements,calculateTravelFee,distanceFee,canPublishSettlement} from '../data/travel-fee.mjs';
const data=JSON.parse(fs.readFileSync(new URL('../data/areas.json',import.meta.url),'utf8'));
test('confirmed free zones and unknown distances',()=>{
 assert.equal(calculateTravelFee(data,'kyiv'),0);assert.equal(calculateTravelFee(data,'vyshhorod'),0);
 for(const slug of ['dymer','irpin','unknown'])assert.equal(calculateTravelFee(data,slug),null);
});
test('examples are one-way and read the configured rate',()=>{
 assert.deepEqual([10,20,40,60].map(km=>distanceFee(data,km)),[50,100,200,300]);
 const changed=structuredClone(data);changed.fee_rules.per_km_rate=7;
 assert.equal(distanceFee(changed,20),140);
});
test('invalid distances are not interpreted as free travel',()=>{
 for(const value of [null,undefined,'',NaN,Infinity,-1,'20'])assert.equal(distanceFee(data,value),null);
});
test('empty settlements cannot create pages',()=>{
 assert.equal(new Set(settlements(data).map(x=>x.slug)).size,8);
 for(const place of settlements(data))assert.equal(canPublishSettlement(place),false);
});
