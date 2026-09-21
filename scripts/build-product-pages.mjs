import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
export const productPath=id=>'/products/'+createHash('sha256').update(String(id)).digest('hex').slice(0,16)+'/';
const text=value=>String(value??'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
const esc=value=>text(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export async function buildProductPages(out,products){
 const urls=[],seen=new Set();
 for(const item of products){
  if(!item.id||!item.name)continue;
  const route=productPath(item.id);if(seen.has(route))throw Error('Duplicate product URL');seen.add(route);
  item.page_url=route;
  const title=text(item.name),url='https://alt-cam.net.ua'+route;
  const images=[...new Set([item.image,...(Array.isArray(item.images)?item.images:[])])].filter(x=>typeof x==='string'&&/^https:\/\//.test(x));
  const description=text(item.description)||'Характеристики та сумісність обладнання уточнюйте перед замовленням.';
  const schema=JSON.stringify({'@context':'https://schema.org','@type':'Product',name:title,description:description.slice(0,5000),image:images,brand:item.brand?{'@type':'Brand',name:text(item.brand)}:undefined,url}).replace(/</g,'\\u003c');
  const html=`<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} | ALT-CAM</title><meta name="description" content="${esc(description.slice(0,160))}"><link rel="canonical" href="${url}"><script type="application/ld+json">${schema}</script><style>body{margin:0;background:#17171a;color:#eee;font:16px/1.6 Arial}main{max-width:1100px;margin:auto;padding:24px}a{color:#fc0}h1{font-size:28px;line-height:1.3}.gallery{display:flex;overflow:auto;gap:16px}.gallery img{height:300px;width:360px;max-width:85vw;object-fit:contain;background:white;border-radius:12px}.cta{display:inline-block;padding:14px;background:#fc0;color:#111;border-radius:8px;text-decoration:none}.description{white-space:pre-wrap;overflow-wrap:anywhere}footer{margin-top:32px}</style></head><body><script src="/analytics.js"></script><main><nav><a href="/">ALT-CAM</a> / <a href="/catalog.html">Каталог</a></nav><h1>${esc(title)}</h1><p>${esc(item.brand)} · ${esc(item.category)}</p><div class="gallery">${images.map(src=>`<a href="${esc(src)}" target="_blank" rel="noopener"><img src="${esc(src)}" alt="${esc(title)}" loading="lazy" width="360" height="300"></a>`).join('')}</div><p>Ціну, наявність і комплектацію підтверджує менеджер перед замовленням.</p><a class="cta" href="/catalog.html?product=${encodeURIComponent(item.id)}">Перевірити ціну та замовити</a><h2>Опис</h2><p class="description">${esc(description)}</p><h2>Характеристики</h2><ul>${(Array.isArray(item.features)?item.features:[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul><footer><a href="/delivery-and-returns.html">Доставка та повернення</a> · <a href="/#contacts">Консультація</a></footer></main></body></html>`;
  const dir=path.join(out,route);await fs.mkdir(dir,{recursive:true});await fs.writeFile(path.join(dir,'index.html'),html);urls.push(url);
 }
 await fs.writeFile(path.join(out,'sitemap-products.xml'),'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+urls.map(url=>`<url><loc>${url}</loc></url>`).join('')+'</urlset>');
 const sitemap=path.join(out,'sitemap.xml');await fs.rename(sitemap,path.join(out,'sitemap-pages.xml'));
 await fs.writeFile(sitemap,'<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://alt-cam.net.ua/sitemap-pages.xml</loc></sitemap><sitemap><loc>https://alt-cam.net.ua/sitemap-products.xml</loc></sitemap></sitemapindex>');
 console.log('Product pages:',urls.length);
}
