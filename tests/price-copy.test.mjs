import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {buildHomepage} from '../scripts/build-homepage.mjs';
import {loadLandings} from '../scripts/build-local-pages.mjs';
import {enhanceHead} from '../scripts/finalize-seo.mjs';

test('installation metadata qualifies volume prices and stays within 155 characters', async () => {
  const home = await buildHomepage(await fs.readFile(new URL('../index.html', import.meta.url), 'utf8'));
  const descriptions = [home.match(/name="description" content="([^"]+)"/)[1]];
  for (const {meta} of await loadLandings()) {
    if (['montazh-videosposterezhennia-kyiv', 'vstanovlennia-kamer-vyshhorod'].includes(meta.slug)) descriptions.push(meta.description);
  }
  assert.equal(descriptions.length, 3);
  for (const description of descriptions) {
    assert.ok(description.length <= 155, description);
    assert.match(description, /1 100 ₴/);
    assert.match(description, /від 9 однакових/);
    assert.match(description, /500 ₴/);
  }
});

test('social titles and descriptions replace stale price promises', () => {
  const description = '1 камера — від 1 100 ₴; від 9 однакових — від 500 ₴ за камеру.';
  const html = enhanceHead('<html><head><title>Монтаж | ALT-CAM</title><meta name="description" content="' + description +
    '"><meta property="og:title" content="Old"><meta property="og:description" content="Old"><meta name="twitter:description" content="Old"></head></html>');
  for (const key of ['og:description','twitter:description']) {
    assert.ok(html.includes(key + '" content="' + description + '"'));
    assert.equal(html.split(key).length - 1, 1);
  }
  assert.ok(html.includes('og:title" content="Монтаж | ALT-CAM"'));
  assert.ok(html.includes('twitter:title" content="Монтаж | ALT-CAM"'));
  assert.ok(!html.includes('content="Old"'));
});
