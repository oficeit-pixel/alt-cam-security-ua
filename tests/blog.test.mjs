import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {loadArticles,paginate,pagePath} from '../scripts/build-blog.mjs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url),{canonicalPath}=require('../catalog-canonical.js');
test('five original articles have 700–1000 words and real local images',async()=>{
 const a=await loadArticles();assert.equal(a.length,5);for(const p of a){assert(p.words>=700&&p.words<=1000);assert(p.meta.image.startsWith('/assets/works/'));}
});
test('pagination uses ten per page with stable canonical routes',()=>{
 assert.deepEqual(paginate(Array.from({length:21},(_,i)=>i)).map(a=>a.length),[10,10,1]);
 assert.equal(pagePath(1),'/blog/');assert.equal(pagePath(2),'/blog/page/2/');
});
test('query canonical leaves UI and cart states intact',()=>{
 const p=[{id:'viatec-1',page_url:'/products/abc123/'}];
 assert.equal(canonicalPath('?group=video',p),'/catalog.html');
 assert.equal(canonicalPath('?cart=123',p),'/catalog.html');
 assert.equal(canonicalPath('?product=viatec-1',p),'/products/abc123/');
 assert.equal(canonicalPath('?product=unknown',p),'/catalog.html');
});
test('price article examples are consistent with current canonical rates',async()=>{
 const {loadInstallationRates}=await import('../scripts/product-seo.mjs');const {video:v}=await loadInstallationRates();
 assert.equal(2*v.indoorCamera.two+v.recorderSetup+v.mobileAppSetup,2550);
 assert.equal(2*v.indoorCamera.two+2*v.outdoorCamera.two+v.recorderSetup+v.mobileAppSetup,4350);
 assert.equal(4*v.indoorCamera.threeToEight+4*v.outdoorCamera.threeToEight+v.recorderSetup+v.mobileAppSetup,6150);
 const source=await fs.readFile('content/blog/koshtorys-videosposterezhennia-kyiv.md','utf8');for(const n of ['2 550','4 350','6 150'])assert(source.includes(n));
});
