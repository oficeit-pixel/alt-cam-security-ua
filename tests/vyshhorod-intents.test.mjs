import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
test('Vyshhorod intents retain separate URLs and visible reciprocal links',()=>{
 const solution=fs.readFileSync('_site/videosposterezhennia-vyshhorod/index.html','utf8'),prices=fs.readFileSync('_site/vstanovlennia-kamer-vyshhorod/index.html','utf8');
 assert(!solution.includes('<table>'));assert(prices.includes('<table>'));
 assert(solution.includes('href="/vstanovlennia-kamer-vyshhorod/"'));
 assert(prices.includes('href="/videosposterezhennia-vyshhorod/"'));
 for(const pattern of [/<title>(.*?)<\/title>/,/<h1>(.*?)<\/h1>/])assert.notEqual(solution.match(pattern)[1],prices.match(pattern)[1]);
 assert(!/noindex/.test(solution));assert(!/noindex/.test(prices));
 assert(solution.includes('Чи можна об’єднати'));assert(prices.includes('Чому чотири камери'));
});
