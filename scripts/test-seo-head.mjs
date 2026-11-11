import assert from 'node:assert/strict';
import './test-legal-pages.mjs';
import '../tests/seo-slug.test.mjs';
import '../tests/sitemaps.test.mjs';
import '../tests/product-seo.test.mjs';
import {enhanceHead} from './finalize-seo.mjs';
import {regionalLinks} from './regional-links.mjs';
const linked = regionalLinks('<html><head></head><body><main><h1>Товар</h1></main></body></html>');
assert.equal((linked.match(/<li><a href=/g)||[]).length, 7);
assert(linked.includes('href="/zona-vyizdu/vartist-vyizdu/"'));
assert(linked.includes('href="/regional-links.css"'));
assert.equal(regionalLinks(linked), linked);
assert(linked.indexOf('id="regional-services"') < linked.indexOf('</main>'));
const html = '<html><head><title>Камера | ALT-CAM</title><meta name="description" content="Опис"><link rel="canonical" href="https://alt-cam.net.ua/test/"><link rel="icon" href="old.png"></head></html>';
const result = enhanceHead(html);
assert.equal((result.match(/rel="icon"/g)||[]).length, 1);
assert(result.includes('sizes="96x96"'));
assert(result.includes('property="og:title" content="Камера | ALT-CAM"'));
assert(result.includes('property="og:url" content="https://alt-cam.net.ua/test/"'));
assert.equal((enhanceHead(result).match(/property="og:title"/g)||[]).length, 1);
console.log('SEO head tests passed');
for (const source of ['/analytics.js', 'analytics.js', '/analytics.js?v=1']) {
  const deferred = enhanceHead(`<html><head></head><body><script src="${source}"></script></body></html>`);
  assert(deferred.includes(`<script defer src="${source}">`));
  assert.equal((enhanceHead(deferred).match(/<script defer/g) || []).length, 1);
}
assert(enhanceHead('<html><head></head><script src="/other.js"></script></html>').includes('<script src="/other.js">'));
