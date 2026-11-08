import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
const out='outputs/intents-kits-audit';await fs.mkdir(out,{recursive:true});
const rows=[];
async function scan(dir){for(const e of await fs.readdir(dir,{withFileTypes:true})){const file=path.join(dir,e.name);if(e.isDirectory())await scan(file);else if(e.name.endsWith('.html')){const h=await fs.readFile(file,'utf8'),plain=s=>(s||'').replace(/<[^>]*>/g,'').replace(/\s+/g,' ').trim();rows.push({url:'/'+path.relative('_site',file).replaceAll('\\','/').replace(/index\.html$/,''),title:plain(h.match(/<title>([\s\S]*?)<\/title>/i)?.[1]),h1:plain(h.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)?.[1]),noindex:/name="robots"[^>]*noindex/.test(h)});}}}
await scan('_site');
const duplicates={};for(const field of ['title','h1']){const groups=new Map();for(const r of rows){if(!r[field])continue;const g=groups.get(r[field])||[];g.push(r.url);groups.set(r[field],g);}duplicates[field]=[...groups].filter(([,urls])=>urls.length>1);}
const cell=s=>s.replaceAll('|','\\|');
await fs.writeFile(out+'/all-pages.md','# URL → title → H1\n\n| URL | title | H1 |\n|---|---|---|\n'+rows.map(r=>[r.url,r.title,r.h1].map(cell).join(' | ')).map(s=>'| '+s+' |').join('\n'));
await fs.writeFile(out+'/duplicates.json',JSON.stringify(duplicates,null,2));
const context={window:{}};for(const file of ['service-rates.js','calc-core.js','price-calculator.js','package-configs.js'])vm.runInNewContext(await fs.readFile('data/'+file,'utf8'),context);
const kits=JSON.parse(await fs.readFile('data/kits.json','utf8'));
const comparisons=kits.map(k=>{const config=context.window.ALTCAM_PACKAGES[k.id],e=config?context.window.ALTCAM_PRICING.calculateVideo(new Map(Object.entries(config))):null;return {id:k.id,owner:k.price_from_with_install_uah,calculator:e?.policy.total??null,installation:e?.installation??null,difference:typeof k.price_from_with_install_uah==='number'&&e?k.price_from_with_install_uah-e.policy.total:null};});
await fs.writeFile(out+'/kit-comparison.json',JSON.stringify(comparisons,null,2));
console.log(JSON.stringify({pages:rows.length,duplicateTitles:duplicates.title.length,duplicateH1:duplicates.h1.length,landings:rows.filter(r=>/^(\/videosposterezhennia-vyshhorod\/|\/vstanovlennia-kamer-vyshhorod\/)$/.test(r.url)),comparisons},null,2));
