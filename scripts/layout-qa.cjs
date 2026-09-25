const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),http=require('http');
const root=process.cwd();
const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]==='/'?'/index.html':req.url.split('?')[0]));
  if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
  try{const types={'.css':'text/css','.js':'text/javascript','.html':'text/html','.svg':'image/svg+xml'};res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch{res.writeHead(404).end();}
});
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const browser=await chromium.launch({channel:'msedge',headless:true});
  fs.mkdirSync('tmp-responsive',{recursive:true});
  try{
    for(const width of [320,390,600,768,1024,1440]){
      const page=await browser.newPage({viewport:{width,height:900}});
      await page.route(/google-analytics|googletagmanager|fonts.googleapis|onrender.com/,r=>r.abort());
      await page.goto(`http://127.0.0.1:${server.address().port}/index.html`,{waitUntil:'domcontentloaded'});
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
        await page.goto(`http://127.0.0.1:${server.address().port}/${file}`,{waitUntil:'domcontentloaded'});
        await page.waitForTimeout(200);
        const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
        console.log(JSON.stringify({file,width,overflow}));
        if(overflow)process.exitCode=1;
      }
      await page.close();
    }
  }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
