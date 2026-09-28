const {chromium}=require('playwright');
const fs=require('fs');
const base=(process.env.QA_BASE_URL || 'http://localhost:4173').replace(/\/$/,'');
(async()=>{
  const browser=await chromium.launch({...(process.env.PW_CHANNEL?{channel:process.env.PW_CHANNEL}:{}),headless:true});
  fs.mkdirSync('tmp-responsive',{recursive:true});
  try{
    for(const width of [320,390,600,768,1024,1440]){
      const page=await browser.newPage({viewport:{width,height:900}});
      await page.route(/^https?:/,r=>new URL(r.request().url()).origin===new URL(base).origin?r.continue():r.abort());
      await page.goto(`${base}/index.html`,{waitUntil:'domcontentloaded'});
      await page.addStyleTag({content:'.reveal{opacity:1!important;transform:none!important}'});
      await page.evaluate(async()=>{await Promise.all([...document.querySelectorAll('.package-media img')].map(img=>{img.loading='eager';return img.decode().catch(()=>{});}));});
      const aligned=await page.locator('.package-card').evaluateAll(cards=>cards.every(card=>{
        const c=card.getBoundingClientRect(),m=card.querySelector('.package-media').getBoundingClientRect();
        const img=card.querySelector('img');
        return Math.abs((m.left-c.left)-(c.right-m.right))<2 && img.naturalWidth>0;
      }));
      if(!aligned)throw new Error(`Package media misaligned at ${width}px`);
      await page.evaluate(()=>document.querySelectorAll('body *').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.setProperty('display','none','important');}));
      await page.locator('.catalog-grid').screenshot({path:`tmp-responsive/categories-${width}.png`});
      console.log(JSON.stringify({width,...await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,cards:[...document.querySelectorAll('.package-card')].map(e=>({width:e.clientWidth,height:e.clientHeight,media:e.querySelector('.package-media').clientHeight,button:e.querySelector('.btn').clientHeight}))}))}));
      for(const file of ['catalog.html','admin.html','blanks/index.html','blanks/invoice.html','privacy-policy.html','delivery-and-returns.html']){
        await page.goto(`${base}/${file}`,{waitUntil:'domcontentloaded'});
        await page.waitForTimeout(200);
        const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
        console.log(JSON.stringify({file,width,overflow}));
        if(overflow)process.exitCode=1;
      }
      await page.close();
    }
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
