import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {renderReviews} from '../scripts/reviews.mjs';
const source=fs.readFileSync('index.html','utf8');
test('five actual objects are separated from four illustrations',()=>{
 const real=source.match(/<section[^>]*id="works"[\s\S]*?<\/section>/)[0];
 assert.equal((real.match(/<figure/g)||[]).length,5);
 assert.doesNotMatch(real,/Візуалізація|Харків|Дніпро|по Україні|construction-security/);
 const demo=source.match(/<section[^>]*id="solution-examples"[\s\S]*?<\/section>/)[0];
 assert.equal((demo.match(/не фото виконаного об’єкта/g)||[]).length,4);
});
test('empty or unsafe review link produces no review section or demo stars',()=>{
 for(const gbpReviewUrl of ['', 'javascript:alert(1)']){
  const html=renderReviews(source,{gbpReviewUrl},[]);
  assert.doesNotMatch(html,/id="reviews"|review-card|★★★★★|ALTCAM_VERIFIED_REVIEWS/);
 }
 assert.deepEqual(JSON.parse(fs.readFileSync('data/reviews.json','utf8')),[]);
});
test('valid link shows invitation; only sourced verified reviews are rendered and escaped',()=>{
 const contacts={gbpReviewUrl:'https://search.google.com/local/writereview?placeid=test'};
 assert.match(renderReviews(source,contacts),/Залишити відгук у Google/);
 const review={verified:true,name:'<Test>',locality:'Київ',date:'2026-09-30',text:'<script>bad</script>',source:'https://example.com/review'};
 assert.doesNotMatch(renderReviews(source,contacts,[review]),/class="review-card"/);
 const html=renderReviews(source,contacts,[review,review,review,{...review,verified:false}]);
 assert.equal((html.match(/class="review-card"/g)||[]).length,3);
 assert.ok(html.includes('&lt;script&gt;bad&lt;/script&gt;'));
});
