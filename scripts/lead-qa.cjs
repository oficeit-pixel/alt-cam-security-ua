// Network-isolated browser checks against working-tree pages; no real leads.
const {chromium}=require('playwright');
const path=require('node:path');
const assert=require('node:assert/strict');
const {default:AxeBuilder}=require('@axe-core/playwright');
const root=path.resolve(__dirname,'..');
(async()=>{
  const {buildHomepage}=await import('./build-homepage.mjs');
  const homepage=await buildHomepage(await require('node:fs/promises').readFile(path.join(root,'index.html'),'utf8'));
  const browser=await chromium.launch({headless:true,timeout:20000,...(process.env.PW_CHANNEL?{channel:process.env.PW_CHANNEL}:{})});
  try{
    for(const pageName of ['index.html','catalog.html']){
      for(const success of [false,true]){
        const context=await browser.newContext();
        const page=await context.newPage();
        const browserErrors=[];
        page.on('pageerror',error=>browserErrors.push(error.message));
        let posted=0,popups=0,health=0,orders=0;
        page.on('popup',()=>popups++);
        await page.route('**/*',async route=>{
          const url=new URL(route.request().url());
          if(url.hostname==='alt-cam-crm-api.onrender.com'&&url.pathname==='/api/orders'){
            orders++;
            assert.equal(route.request().postDataJSON().customer.phone,'+380630607088');
            return success?route.fulfill({json:{ok:true,order_number:'QA-TEST'},headers:{'Access-Control-Allow-Origin':'*'}}):route.abort();
          }
          if(url.hostname==='alt-cam-crm-api.onrender.com'&&url.pathname==='/health'){
            health++;return route.fulfill({json:{ok:true},headers:{'Access-Control-Allow-Origin':'*'}});
          }
          if(url.hostname==='alt-cam-crm-api.onrender.com'&&url.pathname==='/site-lead'){
            posted++;
            if(success)return route.fulfill({json:{ok:true,id:1},headers:{'Access-Control-Allow-Origin':'*'}});
            return route.abort();
          }
          if(url.origin!=='http://localhost:4173')return route.abort();
          const name=path.resolve(root,'.'+decodeURIComponent(url.pathname));
          if(!name.startsWith(root+path.sep)||! /\.(html|js|css|png|jpg|jpeg|svg|webp|ico|woff2)$/i.test(name))return route.abort();
          try{if(name===path.join(root,'index.html'))return await route.fulfill({body:homepage,contentType:'text/html'});return await route.fulfill({path:name});}catch{return route.abort();}
        });
        await page.goto('http://localhost:4173/'+pageName+'?debug_mode=1',{waitUntil:'domcontentloaded'});
        await page.addScriptTag({url:'http://localhost:4173/analytics.js'});
        assert.equal(await page.evaluate(()=>!!window.gtag),false,'Analytics remains off without consent');
        await page.locator('[data-yes]').click();
        assert.equal(await page.evaluate(()=>window.dataLayer.some(x=>x[0]==='config'&&x[2]?.debug_mode===true)),true);
        assert.equal(health,0, 'No warmup before interaction');
        if(pageName==='index.html') {
          assert.equal(await page.locator('#works .real .work-card').count(),5);
          assert.doesNotMatch(await page.locator('#works .real').innerText(),/Візуалізація|Харків|Дніпро/);
          assert.equal(await page.locator('#solution-examples .work-visualization').count(),4);
          assert.equal(await page.locator('.review-card').count(),0);
          await page.evaluate(()=>{
            const form=document.querySelector('#security-calculator');
            for(const name of ['videoIndoor','videoOutdoor','videoPtz'])form.elements[name].value='0';
            form.dispatchEvent(new Event('input',{bubbles:true}));
          });
          assert.equal(await page.locator('#calc-total').innerText(),'—');
          assert.match(await page.locator('#calc-note').innerText(),/Додайте хоча б одну камеру/);
          assert.equal(await page.locator('#send-calculation').isDisabled(),true);
          assert.equal(await page.locator('#download-proposal').isDisabled(),true);
          await page.evaluate(()=>{
            const form=document.querySelector('#security-calculator');
            form.elements.videoIndoor.value='999';
            form.dispatchEvent(new Event('input',{bubbles:true}));
          });
          assert.equal(await page.locator('[name="videoIndoor"]').inputValue(),'64');
          assert.equal(await page.locator('#send-calculation').isDisabled(),false);
          await page.evaluate(()=>{
            const field=document.querySelector('[name="powerLoad"]');
            field.value='0';field.dispatchEvent(new Event('input',{bubbles:true}));
            const count=document.querySelector('[name="ajaxMotion"]');
            count.value='999';count.dispatchEvent(new Event('input',{bubbles:true}));
          });
          assert.equal(await page.locator('[name="powerLoad"]').inputValue(),'10');
          assert.equal(await page.locator('#power-load').innerText(),'10 Вт');
          assert.equal(await page.locator('[name="ajaxMotion"]').inputValue(),'100');
          console.log('Calculator boundaries and disabled zero-camera actions PASS');
          for(const id of ['kit-2cam','kit-4cam','kit-8cam']) {
            const link=page.locator(`[data-package="${id}"]`);
            const price=await link.locator('..').locator('.package-price').innerText();
            await link.click();
            const total=await page.locator('#calc-total').innerText();
            assert.equal(price.replace(/\D/g,''),total.replace(/\D/g,''),`${id}: card/calculator mismatch`);
            assert.equal(await page.locator('[name="videoInstall"]').isChecked(),true);
          }
          console.log('Camera packages: card/calculator equality PASS');
        }
        if(pageName==='catalog.html') {
          await page.locator('[data-add]').first().click();
          assert.equal(await page.locator('#cart').getAttribute('aria-hidden'),'false');
          const cartAxe=await new AxeBuilder({page}).withRules(['label','select-name']).analyze();
          assert.deepEqual(cartAxe.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[]);
          await page.locator('#order-name').fill('Тест QA');
          await page.locator('[name="delivery"][value="pickup"]').check();
          await page.locator('#order-phone').fill('123');
          await page.locator('#cart-order').click();
          assert.equal(orders,0);
          assert.equal(await page.locator('#order-phone').getAttribute('aria-invalid'),'true');
          await page.locator('#order-phone').fill('0630607088');
          await page.locator('#cart-order').click();
          await page.waitForFunction(()=>!document.querySelector('#cart-order').disabled);
          assert.equal(orders,1);
          assert.equal(await page.locator('#checkout-form a[href="/privacy-policy.html"]').count(),1);
          const count=await page.evaluate(()=>window.dataLayer.filter(x=>x[0]==='event'&&x[1]==='generate_lead').length);
          assert.equal(count,success?1:0);
          await page.locator('#cart-close').click();
          await page.evaluate(()=>{window.dataLayer.length=0;});
        }
        const form=page.locator(pageName==='index.html'?'#lead-form':'#consult-form');
        const accessibility=await new AxeBuilder({page}).withRules(['label','select-name']).analyze();
        assert.deepEqual(accessibility.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],'Fields have accessible names');
        assert.equal(health,1);
        await form.locator('[name="name"]').fill('Тест QA');
        await form.locator('[name="phone"]').fill('0630607088');
        assert.equal(health,1);
        await form.locator('[name="phone"]').fill('123');
        await form.evaluate(form=>form.requestSubmit(form.querySelector('button[type="submit"],button:not([type])')));
        assert.equal(posted,0);
        assert.match(await form.locator('[data-phone-error]').innerText(),/Перевірте телефон/);
        await form.locator('[name="phone"]').fill('0630607088');
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
        const analytics=await page.evaluate(()=>window.dataLayer.filter(x=>x[0]==='event').map(x=>({name:x[1],params:x[2]})));
        assert.equal(analytics.filter(x=>x.name==='generate_lead').length,success?1:0);
        assert.equal(analytics.filter(x=>x.name==='lead_fallback_shown').length,success?0:1);
        assert.ok(!JSON.stringify(analytics).includes('0630607088'));
        assert.ok(!JSON.stringify(analytics).includes('Тест QA'));
        if(pageName==='index.html'&&success){
          const mapping=await page.evaluate(()=>{
            window.dataLayer.length=0;
            for(const name of ['submit_lead','submit_quiz','submit_calculator','checkout_completed','consultation_sent','click_whatsapp','click_viber'])window.altcamAnalytics(name,{phone:'private-phone',name:'private-name',message:'private-text'});
            return window.dataLayer.filter(x=>x[0]==='event').map(x=>({name:x[1],params:x[2]}));
          });
          assert.equal(mapping.filter(x=>x.name==='generate_lead').length,5);
          assert.deepEqual(mapping.filter(x=>x.name==='contact_click').map(x=>x.params.method),['whatsapp','viber']);
          assert.ok(!JSON.stringify(mapping).includes('private-'));
        }
        assert.deepEqual(browserErrors,[], 'No browser JavaScript exceptions');
        await context.close();
        console.log(`${pageName}: ${success?'success':'fallback'} PASS`);
      }
    }
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
