// Synthetic fixture is rendered only in an isolated browser, never published.
const {chromium}=require('playwright'),fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const {buildHomepage}=await import('./build-homepage.mjs'),source=await fs.readFile('index.html','utf8');
 const empty={reviews:[],legal:{},openingHours:[],team:'TODO_OWNER',sameAs:[],dealerships:[]};
 const filled={...empty,legal:{name:'Тестова організація',code:'ТЕСТ',address:'Тестова юридична адреса'},openingHours:['Mo-Fr 09:00-18:00'],installationWarrantyMonths:12,team:'Тестовий опис команди',reviews:[{verified:true,name:'Тестовий автор',locality:'Тестовий об’єкт',text:'Тест відображення, не справжній відгук.',date:'2026-01-01',source:'https://www.facebook.com/example/posts/test'}]};
 const output=path.resolve('outputs/trust-qa');await fs.mkdir(output,{recursive:true});
 const browser=await chromium.launch({headless:true,channel:'msedge'}),errors=[];
 try{for(const width of [390,1366])for(const [name,trustData]of Object.entries({empty,filled})){
  const html=await buildHomepage(source,{trustData}),context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
  await context.route('**/*',async route=>{
   const u=new URL(route.request().url());
   if(u.origin!=='http://trust.test')return route.fulfill({status:200,body:'',contentType:'text/css'});
   if(u.pathname==='/')return route.fulfill({status:200,contentType:'text/html',body:html});
   const file=path.resolve('_site','.'+u.pathname);if(!file.startsWith(path.resolve('_site')+path.sep))return route.abort();
   try{const body=await fs.readFile(file),type={'.js':'text/javascript','.css':'text/css','.png':'image/png','.webp':'image/webp','.svg':'image/svg+xml'}[path.extname(file)];await route.fulfill({status:200,body,contentType:type||'application/octet-stream'});}catch{await route.fulfill({status:404,body:''});}
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto('http://trust.test/',{waitUntil:'networkidle'});
  assert.equal(await page.locator('#trust').count(),name==='filled'?1:0);
  assert.equal(await page.locator('[data-trust-legal]').count(),name==='filled'?1:0);
  assert.equal(await page.locator('.brand-row img').count(),0);
  assert(!(await page.locator('body').innerText()).includes('TODO_OWNER'));
  if(name==='filled'){if(await page.locator('[data-no]').isVisible())await page.locator('[data-no]').click();await page.locator('#trust').scrollIntoViewIfNeeded();await page.locator('#trust').screenshot({path:path.join(output,name+'-'+width+'.png')});assert((await page.locator('.form-head').innerText()).includes('Пн-Пт'));}
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await context.close();
 }assert.deepEqual(errors,[]);console.log('Trust: empty/filled at 390/1366 passed, no console errors or overflow.');}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
