import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {renderTrust,trustSchema,trust} from '../scripts/trust.mjs';
const source=fs.readFileSync('index.html','utf8');
const fixture={legal:{name:'ТЕСТ ФОП',code:'ТЕСТ',address:'Тестова адреса'},openingHours:['Mo-Fr 09:00-18:00'],installationWarrantyMonths:12,team:'Тестова команда',sameAs:['https://facebook.com/example'],dealerships:[],reviews:[{verified:true,name:'Тест',locality:'Тестовий об’єкт',text:'Лише тестові дані <script>',date:'2026-01-01',source:'https://www.facebook.com/example/posts/test',rating:4}],reviewSchemaEnabled:true};
test('empty trust data renders no placeholders, no hours, no invented reviews',()=>{
 const html=renderTrust(source,trust);assert(!html.includes('id="trust"'));assert(!html.includes('TODO_OWNER'));assert(!html.includes('data-trust-legal'));assert.deepEqual(trustSchema({...trust,sameAs:[]}),{});
});
test('filled fixture renders escaped reviews, legal details, hours and warranty',()=>{
 const html=renderTrust(source,fixture);assert(html.includes('id="trust"'));assert(html.includes('data-trust-legal'));assert(html.includes('12 міс.'));assert(html.includes('Відповімо у робочий час · Пн-Пт 09:00-18:00'));assert(html.includes('&lt;script&gt;'));assert(!html.includes('Лише тестові дані <script>'));
 const schema=trustSchema(fixture,{reviewsVisible:true});assert.equal(schema.review.length,1);assert.equal(schema.aggregateRating.ratingValue,4);
 assert(!trustSchema(fixture).review);
});
test('unconfirmed reviews, malformed hours, missing scores and unsafe logos cannot invent claims',()=>{
 const bad={...fixture,reviews:[{...fixture.reviews[0],verified:false}],openingHours:['TODO_OWNER','Mo-Fr 99:00-99:99'],installationWarrantyMonths:'TODO_OWNER',team:'TODO_OWNER'};
 assert(!trustSchema(bad,{reviewsVisible:true}).review);assert(!trustSchema(bad).openingHours);
 for(const change of [{source:'javascript:alert(1)'},{source:'https://google.evil.example/review'},{date:'2026-02-31'}])assert(!trustSchema({...fixture,reviews:[{...fixture.reviews[0],...change}]},{reviewsVisible:true}).review);
 assert(!trustSchema({...fixture,reviews:[{...fixture.reviews[0],rating:undefined}]},{reviewsVisible:true}).aggregateRating);
 const row=html=>html.match(/<div class="brand-row">([\s\S]*?)<\/div>/)[1];
 assert(!row(renderTrust(source,{...fixture,dealerships:[{brand:'AJAX',confirmed:false,logo:'/assets/example.png',source:'https://example.com'}]})).includes('<img'));
 assert(row(renderTrust(source,{...fixture,dealerships:[{brand:'AJAX',confirmed:true,logo:'/assets/example.png',source:'https://example.com'}]})).includes('<img'));
});
