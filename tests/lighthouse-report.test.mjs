import test from 'node:test';
import assert from 'node:assert/strict';
import {validateLighthouse} from '../scripts/validate-lighthouse.mjs';
const report = () => ({categories:{performance:{score:0.9}}, audits:{
  'largest-contentful-paint':{numericValue:2000},
  'cumulative-layout-shift':{numericValue:0},
  'total-blocking-time':{numericValue:0},
}});
test('accepts valid zero CLS/TBT', () => assert.equal(validateLighthouse(report()).TBT, 0));
test('rejects NO_LCP instead of reporting successful measurement', () => {
  const value=report(); value.audits['largest-contentful-paint']={errorMessage:'NO_LCP'};
  assert.throws(()=>validateLighthouse(value), /LCP/);
});
test('rejects null score and runtime failure', () => {
  const value=report(); value.categories.performance.score=null;
  assert.throws(()=>validateLighthouse(value), /performance/);
  assert.throws(()=>validateLighthouse({...report(),runtimeError:{code:'NO_FCP'}}), /runtime/);
});
