// Network-isolated browser checks against working-tree pages; no real leads.
const {chromium}=require('playwright');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
(async()=>{
  const browser=await chromium.launch({headless:true,timeout:20000,...(process.env.PW_CHANNEL?{channel:process.env.PW_CHANNEL}:{})});
  try{
    for(const pageName of ['index.html','catalog.html']){
      for(const success of [false,true]){
        const page=await browser.newPage();
        let posted=0,popups=0;
        page.on('popup',()=>popups++);
        await page.route('**/*',async route=>{
          const url=new URL(route.request().url());
          if(url.hostname==='alt-cam-crm-api.onrender.com'&&url.pathname==='/site-lead'){
            posted++;
            if(success)return route.fulfill({json:{ok:true,id:1},headers:{'Access-Control-Allow-Origin':'*'}});
            return route.abort();
          }
          if(url.origin!=='http://localhost:4173')return route.abort();
          const name=path.resolve(root,'.'+decodeURIComponent(url.pathname));
          if(!name.startsWith(root+path.sep)||! /\.(html|js|css|png|jpg|jpeg|svg|webp|ico|woff2)$/i.test(name))return route.abort();
          try{return await route.fulfill({path:name});}catch{return route.abort();}
        });
        await page.goto('http://localhost:4173/'+pageName,{waitUntil:'domcontentloaded'});
        const form=page.locator(pageName==='index.html'?'#lead-form':'#consult-form');
        await form.locator('[name="name"]').fill('Тест QA');
        await form.locator('[name="phone"]').fill('0630607088');
        if(pageName==='index.html')await form.locator('[name="object"]').selectOption({label:'Квартира'});
        for(const checkbox of await form.locator('input[type="checkbox"][required]').all())await checkbox.check();
        // Submit through the actual handler; preserve validation on the main form.
        await form.evaluate(form=>form.requestSubmit(form.querySelector('button[type="submit"],button:not([type])')));
        await form.locator('[data-lead-result]').waitFor();
        const status=form.locator('[data-lead-result]');
        if(success)assert.match(await status.innerText(),/Дякуємо! Заявку отримано/);
        else{
          assert.equal(await status.getAttribute('role'),'alert');
          assert.equal(await status.evaluate(e=>e===document.activeElement),true);
          assert.equal(await status.locator('a[href^="tel:"]').getAttribute('href'),'tel:+380630607088');
          assert.match(await status.locator('a[href^="https://t.me/"]').getAttribute('href'),/text=/);
          assert.equal(await form.locator('[name="name"]').inputValue(),'Тест QA');
        }
        assert.equal(posted,1);assert.equal(popups,0);
        await page.close();
        console.log(`${pageName}: ${success?'success':'fallback'} PASS`);
      }
    }
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
