import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {buildLocalPages,loadLandings} from './build-local-pages.mjs';
const root=await fs.mkdtemp(path.join(os.tmpdir(),'altcam-landing-ui-')),out=path.join(root,'site');
await fs.mkdir(out);await fs.writeFile(path.join(out,'index.html'),'<html><head></head><body></body></html>');await buildLocalPages(out);
await fs.copyFile('landing.css',path.join(out,'landing.css'));
const server=http.createServer(async(req,res)=>{try{const rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(out,'.'+rel+(rel.endsWith('/')?'index.html':''));if(!file.startsWith(out+path.sep))throw Error();res.setHeader('Content-Type',file.endsWith('.css')?'text/css':'text/html; charset=utf-8');res.end(await fs.readFile(file));}catch{res.writeHead(404);res.end();}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const base=`http://127.0.0.1:${server.address().port}`;
let browser;
try{
 browser=await chromium.launch({channel:process.env.PW_CHANNEL||undefined,headless:true});
 const page=await browser.newPage();await page.route('**/*',route=>route.request().url().startsWith(base)?route.continue():route.abort());
 for(const viewport of [{width:390,height:844},{width:768,height:1024},{width:1440,height:900}]){
  await page.setViewportSize(viewport);
  for(const {meta} of await loadLandings()){
   await page.goto(base+'/'+meta.slug+'/');
   assert.equal(await page.locator('h1').count(),1);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${meta.slug} overflow ${viewport.width}`);
   assert(await page.locator('header a[href^="tel:"]').isVisible());
   await page.locator('summary').first().click();assert(await page.locator('details').first().getAttribute('open')!==null);
   assert(await page.locator('table').count()>0);
  }
 }
 console.log('Landing UI passed: 6 pages × mobile/tablet/desktop');
}finally{await browser?.close();await new Promise(resolve=>server.close(resolve));await fs.rm(root,{recursive:true,force:true});}
