const {chromium}=require('playwright'),fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const {loadArticles}=await import('./build-blog.mjs'),articles=await loadArticles();
 const browser=await chromium.launch({headless:true,channel:'msedge'}),errors=[];
 await fs.mkdir('outputs/blog-qa',{recursive:true});
 try{for(const width of [390,1366]){
  const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
  await context.addInitScript(()=>localStorage.setItem('altcam-analytics-consent','no'));
  await context.route('**/*',async route=>{
   const u=new URL(route.request().url());if(u.origin!=='http://blog.test')return route.fulfill({status:200,body:'{}',contentType:'application/json'});
   let file=path.resolve('_site','.'+u.pathname);if(!file.startsWith(path.resolve('_site')+path.sep))return route.abort();
   if(u.pathname.endsWith('/'))file=path.join(file,'index.html');
   try{await route.fulfill({status:200,body:await fs.readFile(file),contentType:({'.js':'text/javascript','.html':'text/html','.css':'text/css','.webp':'image/webp','.png':'image/png','.svg':'image/svg+xml'})[path.extname(file)]||'application/octet-stream'});}catch{await route.fulfill({status:404,body:''});}
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto('http://blog.test/blog/',{waitUntil:'networkidle'});assert.equal(await page.locator('.blog-card').count(),5);await page.screenshot({path:`outputs/blog-qa/index-${width}.png`});
  for(const a of articles){
   await page.goto('http://blog.test/blog/'+a.meta.slug+'/',{waitUntil:'networkidle'});
   assert.equal(await page.locator('h1').count(),1);assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),a.url);
   assert(await page.locator('.blog-hero').evaluate(img=>img.complete&&img.naturalWidth>0));
   assert.equal(await page.locator('.blog-cta a[href="https://t.me/AltCamSecurityUaBot"]').count(),1);
   const types=await page.locator('script[type="application/ld+json"]').evaluateAll(nodes=>nodes.flatMap(n=>{const v=JSON.parse(n.textContent);return (Array.isArray(v)?v:[v]).map(o=>o['@type']);}));
   assert(types.includes('Article'));assert(types.includes('BreadcrumbList'));
   await page.locator('.blog-toc a').first().click();assert(new URL(page.url()).hash.startsWith('#section-'));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   if(a.meta.slug==='dbzh-kamery-router'){await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:`outputs/blog-qa/article-${width}.png`});}
  }
  await page.goto('http://blog.test/rezervne-zhyvlennia/',{waitUntil:'networkidle'});assert(await page.locator('a[href="/blog/dbzh-kamery-router/"]').count()>0);
  if(width===1366){
   await page.goto('http://blog.test/catalog.html?group=video',{waitUntil:'networkidle'});assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),'https://alt-cam.net.ua/catalog.html');
   const item=await page.evaluate(()=>window.ALTCAM_CATALOG.find(p=>p.page_url));
   await page.goto('http://blog.test/catalog.html?product='+encodeURIComponent(item.id),{waitUntil:'networkidle'});assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),'https://alt-cam.net.ua'+item.page_url);
  }
  await context.close();
 }assert.deepEqual(errors,[]);console.log('Blog QA: five articles + index, images, metadata, TOC, links, 390/1366, catalog canonical variants passed.');}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
