import fs from 'node:fs/promises';
import path from 'node:path';
import {settlements,calculateTravelFee,distanceFee} from '../data/travel-fee.mjs';
const copy={
 uk:{title:'Вартість виїзду',description:'Вартість виїзду ALT-CAM: Київ і Вишгород, інші населені пункти та розрахунок за відстанню.',home:'Головна',place:'Населений пункт',fee:'Вартість',unknown:'Розрахуємо при заявці — зв’яжіться з нами',rule:'За межами безкоштовних зон: {rate} ₴/км в один бік від найближчої межі Києва або Вишгорода. Вартість виїзду зараховується у вартість робіт.',free:'Безкоштовний виїзд',examples:'Приклади розрахунку',exampleNote:'Це приклади відстаней, а не відстані до конкретних населених пунктів.',calc:'Розрахувати виїзд',contact:'Зв’язатися з нами'},
 ru:{title:'Стоимость выезда',description:'Стоимость выезда ALT-CAM: Киев и Вышгород, другие населённые пункты и расчёт по расстоянию.',home:'Главная',place:'Населённый пункт',fee:'Стоимость',unknown:'Рассчитаем при заявке — свяжитесь с нами',rule:'За пределами бесплатных зон: {rate} ₴/км в одну сторону от ближайшей границы Киева или Вышгорода. Стоимость выезда засчитывается в стоимость работ.',free:'Бесплатный выезд',examples:'Примеры расчёта',exampleNote:'Это примеры расстояний, а не расстояния до конкретных населённых пунктов.',calc:'Рассчитать выезд',contact:'Связаться с нами'}
};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export async function buildTravelPages(out){
 const data=JSON.parse(await fs.readFile('data/areas.json','utf8'));
 if(data.fee_rules.distance_from!=='nearest_of(kyiv_border,vyshhorod_border)'||!data.fee_rules.credited_to_order||!data.fee_rules.one_way)throw new Error('Travel copy requires updated fee rules');
 const places=settlements(data),base='https://alt-cam.net.ua',route='/zona-vyizdu/vartist-vyizdu/';
 // Owner deferred Russian publication. Remove only our unpublished generated file.
 await fs.rm(path.join(out,'ru/zona-vyizdu/vartist-vyizdu/index.html'),{force:true});
 for(const lang of ['uk']){
  const t=copy[lang],url=base+(lang==='ru'?'/ru':'')+route;
  const amount=p=>{const n=calculateTravelFee(data,p.slug);return n===null?t.unknown:n===0?'0 ₴ — '+t.free:n+' ₴';};
  const body=`<!doctype html><html lang="${lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${t.title} | ALT-CAM</title><meta name="description" content="${t.description}"><link rel="canonical" href="${url}"><link rel="alternate" hreflang="uk" href="${base+route}"><link rel="alternate" hreflang="ru" href="${base+'/ru'+route}"><meta property="og:title" content="${t.title} | ALT-CAM"><meta property="og:description" content="${t.description}"><meta property="og:url" content="${url}"><meta property="og:image" content="${base}/assets/alt-cam-mark.png"><link rel="stylesheet" href="/landing.css"></head><body class="landing-page"><main class="landing-shell"><nav aria-label="Breadcrumb"><a href="/">ALT-CAM</a> / ${t.title}</nav><nav><a href="${route}" lang="uk">Українська</a> · <a href="/ru${route}" lang="ru">Русский</a></nav><h1>${t.title}</h1><p>${esc(t.rule.replace('{rate}',data.fee_rules.per_km_rate))}</p><table><thead><tr><th>${t.place}</th><th>${t.fee}</th></tr></thead><tbody>${places.map(p=>`<tr><td>${esc(p.name[lang])}</td><td>${esc(amount(p))}</td></tr>`).join('')}</tbody></table><h2>${t.examples}</h2><p>${t.exampleNote}</p><ul>${[10,20,40,60].map(km=>`<li>${km} км × ${data.fee_rules.per_km_rate} ₴ = ${distanceFee(data,km)} ₴</li>`).join('')}</ul><h2>${t.calc}</h2><label for="travel-place">${t.place}</label><select id="travel-place">${places.map(p=>`<option value="${esc(p.slug)}">${esc(p.name[lang])}</option>`).join('')}</select><p><output id="travel-result" for="travel-place" aria-live="polite">${esc(amount(places[0]))}</output></p><p><a href="/#contacts">${t.contact}</a></p></main><script type="module">import {calculateTravelFee} from '/data/travel-fee.mjs';const data=${JSON.stringify(data).replace(/</g,'\\u003c')};const select=document.getElementById('travel-place');select.addEventListener('change',()=>{const value=calculateTravelFee(data,select.value);document.getElementById('travel-result').textContent=value===null?${JSON.stringify(t.unknown)}:value+' ₴';});</script></body></html>`;
  const breadcrumbs={'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:[
   {'@type':'ListItem',position:1,name:'Головна',item:base+'/'},
   {'@type':'ListItem',position:2,name:t.title,item:url}
  ]};
  const published=body.replace(/<link rel="alternate"[^>]*>/g,'')
   .replace(/<nav><a href="[^\"]*" lang="uk">[\s\S]*?<\/nav>/,'')
   .replace('aria-label="Breadcrumb"','aria-label="Хлібні крихти"')
   .replace('</head>',`<script type="application/ld+json">${JSON.stringify(breadcrumbs)}</script><style>table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:12px 8px;border-bottom:1px solid #444;overflow-wrap:anywhere}select{max-width:100%;padding:12px}output{overflow-wrap:anywhere}</style></head>`);
  const dir=path.join(out,route);await fs.mkdir(dir,{recursive:true});await fs.writeFile(path.join(dir,'index.html'),published);
 }
 await fs.mkdir(path.join(out,'data'),{recursive:true});await fs.copyFile('data/travel-fee.mjs',path.join(out,'data/travel-fee.mjs'));
}
