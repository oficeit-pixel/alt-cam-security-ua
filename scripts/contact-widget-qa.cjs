// Offline browser test: all API calls are intercepted, no real leads are sent.
const {chromium}=require('playwright'),fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict'),{gzipSync}=require('node:zlib');
(async()=>{
 const bytes=gzipSync(await fs.readFile('contact-widget.js')).length;assert(bytes<10240);
 const browser=await chromium.launch({headless:true,channel:process.env.PW_CHANNEL||(process.platform==='win32'?'msedge':undefined)}),errors=[];
 try{for(const width of [390,768,1366])for(const consent of ['no','yes']){
  const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});let fail=false,requests=[];
  await context.addInitScript(value=>localStorage.setItem('altcam-analytics-consent',value),consent);
  await context.route('**/*',async route=>{
   const u=new URL(route.request().url());
   if(u.pathname==='/api/lead'){requests.push(route.request().postDataJSON());return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(fail?{ok:false}:{ok:true,lead_id:'test',telegram_url:'https://t.me/AltCamSecurityUaBot'})});}
   if(u.origin!=='http://widget.test')return route.fulfill({status:200,body:'',contentType:u.pathname.endsWith('.css')?'text/css':'application/json'});
   let name=u.pathname==='/'?'/index.html':u.pathname;if(name.endsWith('/'))name+='index.html';
   const file=path.resolve('_site','.'+name);if(!file.startsWith(path.resolve('_site')+path.sep))return route.abort();
   try{await route.fulfill({status:200,body:await fs.readFile(file),contentType:({'.js':'text/javascript','.html':'text/html','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream'});}catch{await route.fulfill({status:404,body:''});}
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto('http://widget.test/?utm_source=widget_test',{waitUntil:'networkidle'});
  assert.equal(await page.locator('.cw-launch').count(),1);assert.equal(await page.locator('.messenger-dock,.aic-fab').count(),0);
  await page.locator('.cw-launch').click();assert(await page.locator('.cw-panel').isVisible());
  await page.keyboard.press('Shift+Tab');assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Telegram-канал');
  await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.getAttribute('aria-label')),'Закрити контакти');
  assert.equal(await page.locator('.cw-quick a').getAttribute('href'),'tel:+380630607088');
  assert.equal(await page.locator('.cw-links a[href="#"]').count(),0);
  await page.locator('[data-topic="Резервне живлення"]').click();await page.locator('#cw-name').fill('Тест');await page.locator('#cw-phone').fill('0630000000');await page.locator('#cw-object').fill('Тестовий об’єкт, не надсилати');
  await page.locator('.cw-submit').click();await page.waitForFunction(()=>document.querySelector('.cw-submit').disabled&&document.querySelector('.cw-submit').textContent==='Заявку надіслано');
  assert.equal(requests.length,1);assert.equal(requests[0].source_form,'chat_widget');assert.equal(requests[0].utm_source,'widget_test');assert.equal(requests[0].object.topic,'Резервне живлення');assert.equal(requests[0].phone,'+380630000000');
  const events=await page.evaluate(()=>(window.dataLayer||[]).filter(x=>x[0]==='event').map(x=>x[1]));
  assert.equal(events.includes('widget_open'),consent==='yes');assert.equal(events.includes('widget_submit'),consent==='yes');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  assert(!['hidden','clip'].includes(await page.evaluate(()=>getComputedStyle(document.body).overflowY)));
  if(consent==='yes'){await fs.mkdir('outputs/contact-widget-qa',{recursive:true});await page.locator('.cw-panel').screenshot({path:`outputs/contact-widget-qa/widget-${width}.png`});}
  await page.keyboard.press('Escape');assert(await page.locator('.cw-launch').isVisible());assert(!(await page.locator('.cw-panel').isVisible()));
  await page.reload({waitUntil:'networkidle'});fail=true;await page.locator('.cw-launch').click();await page.locator('#cw-name').fill('Тест');await page.locator('#cw-phone').fill('0630000000');await page.locator('#cw-object').fill('Тест помилки');await page.locator('.cw-submit').click();
  await page.waitForFunction(()=>!document.querySelector('form#contact-widget-form').dataset.leadBusy);assert(await page.locator('#contact-widget-form a[href*="t.me"]').count()>0);
  const failed=await page.evaluate(()=>(window.dataLayer||[]).filter(x=>x[0]==='event'&&x[1]==='widget_submit').length);assert.equal(failed,0);
  await page.goto('http://widget.test/dlia-domu/',{waitUntil:'networkidle'});assert.equal(await page.locator('.cw-launch').count(),1);
  await context.close();
 }assert.deepEqual(errors,[]);console.log(`Widget QA passed at 390/768/1366, consent yes/no, success/fallback, focus/Escape, secondary page; gzip ${bytes} bytes.`);}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
