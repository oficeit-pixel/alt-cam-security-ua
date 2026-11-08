// Isolated rendering: requests are fulfilled from _site; no production calls.
const {chromium}=require('playwright');
const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const root=path.resolve('_site'),output=path.resolve('outputs/audience-qa');await fs.mkdir(output,{recursive:true});
 const browser=await chromium.launch({headless:true,channel:process.env.PW_CHANNEL||'msedge'});
 const errors=[];
 try{
  for(const width of [390,1366]){
   const context=await browser.newContext({viewport:{width,height:900}});
   await context.route('**/*',async route=>{
    const u=new URL(route.request().url());if(u.origin!=='http://altcam.test')return route.fulfill({status:200,contentType:route.request().resourceType()==='stylesheet'?'text/css':'application/json',body:route.request().resourceType()==='stylesheet'?'':'{}'});
    const relative=decodeURIComponent(u.pathname).replace(/^\//,'')+(u.pathname.endsWith('/')?'index.html':'');
    const file=path.resolve(root,relative);if(!file.startsWith(root+path.sep))return route.abort();
    try{const body=await fs.readFile(file),type={'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png','.webp':'image/webp','.svg':'image/svg+xml','.woff2':'font/woff2'}[path.extname(file)]||'application/octet-stream';await route.fulfill({status:200,contentType:type,body});}catch{await route.fulfill({status:404,body:'Not found'});}
   });
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   for(const slug of ['dlia-domu','dlia-magazyniv','dlia-skladiv','dlia-sto','dlia-kafe','dlia-ofisiv']){
    await page.goto('http://altcam.test/'+slug+'/',{waitUntil:'networkidle'});
    assert.equal(await page.locator('h1').count(),1);
    assert(await page.locator('#request a').filter({hasText:'Надішліть фото'}).count());
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'overflow '+slug+' '+width);
    await page.locator('#faq summary').first().click();assert(await page.locator('#faq details').first().evaluate(e=>e.open));
    await page.screenshot({path:path.join(output,slug+'-'+width+'.png'),fullPage:true});
   }
   await page.goto('http://altcam.test/',{waitUntil:'networkidle'});
   const tiles=page.locator('#audience a.audience-card');
   assert.equal(await tiles.count(),6);
   await tiles.first().scrollIntoViewIfNeeded();
   await page.locator('#audience').screenshot({path:path.join(output,'home-audience-'+width+'.png')});
   for(const slug of ['dlia-domu','dlia-magazyniv','dlia-skladiv','dlia-sto','dlia-kafe','dlia-ofisiv']){
    await page.locator('#audience a[href="/'+slug+'/"]').click();
    await page.waitForURL('**/'+slug+'/');
    await page.goBack({waitUntil:'networkidle'});
   }
   await context.close();
  }
  assert.deepEqual(errors,[]);
  console.log('12 browser checks and 12 homepage tile clicks passed; no console errors or horizontal overflow on segment pages.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
