// Isolated browser journeys: never delivers a production lead.
const {chromium}=require('playwright');
const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'}),results=[];
 try {for(const viewport of [{width:390,height:844},{width:1440,height:900}]){
  const context=await browser.newContext({viewport,reducedMotion:'reduce'}),requests=[],errors=[],missing=[];
  await context.addInitScript(()=>localStorage.setItem('altcam-analytics-consent','no'));
  await context.route('**/*',async route=>{
   const u=new URL(route.request().url());
   if(u.pathname==='/api/lead'){requests.push(route.request().postDataJSON());return route.fulfill({json:{ok:true,lead_id:'QA',order_number:'QA-OFFLINE'}});}
   if(u.origin!=='http://final.test')return route.fulfill({status:200,body:'',contentType:u.pathname.endsWith('.css')?'text/css':'application/json'});
   const name=decodeURIComponent(u.pathname.endsWith('/')?u.pathname+'index.html':u.pathname),file=path.resolve('_site','.'+name);
   if(!file.startsWith(path.resolve('_site')+path.sep))return route.abort();
   try{await route.fulfill({path:file});}catch{missing.push(name);await route.fulfill({status:404,body:''});}
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://final.test/',{waitUntil:'networkidle'});
  for(const [tab,button] of [['video','send-calculation'],['power','send-power-calculation'],['ajax','send-ajax-calculation']]){
   await page.locator(`[data-calc-tab="${tab}"]`).click();await page.locator('#'+button).click();
   await page.locator('[name="quoteName"]').fill('Тест QA');await page.locator('[name="quotePhone"]').fill('0630000000');
   const before=requests.length;await page.locator('#quote-confirm-form button[type="submit"]').click();
   await page.waitForFunction(()=>!document.querySelector('#quote-confirm-form').dataset.leadBusy);
   assert.equal(requests.length,before+1,tab+' submission');assert.equal(requests.at(-1).source_form,'calculator');
   await page.locator('button[data-close-quote]').click();
  }
  await page.locator('#lead-form [name="name"]').fill('Тест QA');await page.locator('#lead-form [name="phone"]').fill('0630000000');
  await page.locator('#lead-form button[type="submit"]').first().click();
  await page.waitForFunction(()=>!document.querySelector('#lead-form').dataset.leadBusy);assert.equal(requests.at(-1).source_form,'hero');
  for(const name of ['quizObject','quizCameras','quizNight','quizPhoneView']){
   await page.locator('label').filter({has:page.locator(`[name="${name}"]`)}).first().click();await page.locator('#quiz-next').click();
  }
  await page.locator('[name="quizName"]').fill('Тест QA');await page.locator('[name="quizContact"]').fill('0630000000');
  const quizBefore=requests.length;await page.locator('#quiz-next').click();
  await page.waitForFunction(()=>!document.querySelector('#security-quiz').dataset.leadBusy);
  assert.equal(requests.length,quizBefore+1);assert.equal(requests.at(-1).source_form,'quiz');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await page.goto('http://final.test/catalog.html',{waitUntil:'networkidle'});
  for(let i=0;i<3;i++){await page.locator('[data-add]').nth(i).click();await page.locator('#cart-close').click();}
  await page.reload({waitUntil:'networkidle'});await page.locator('#cart-open').click();
  await page.locator('#order-name').fill('Тест QA');await page.locator('#order-phone').fill('0630000000');await page.locator('[name="delivery"][value="pickup"]').check();
  const before=requests.length;await page.locator('#cart-order').click();await page.waitForFunction(()=>!document.querySelector('#checkout-form').dataset.leadBusy);
  assert.equal(requests.length,before+1,'cart submission');assert.equal(requests.at(-1).source_form,'cart');
  assert.deepEqual(errors,[]);assert.deepEqual(missing,[]);
  results.push({viewport,forms:requests.map(x=>x.source_form),jsErrors:errors,missingLocalResources:missing});await context.close();
 }}finally{await browser.close();}
 await fs.mkdir('outputs/final-qa',{recursive:true});await fs.writeFile('outputs/final-qa/journeys.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
