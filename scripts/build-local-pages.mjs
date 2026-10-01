import fs from 'node:fs/promises';
import path from 'node:path';
import {contacts} from './contacts.mjs';
import {localContactBlock} from './local-contact-block.mjs';
import {loadInstallationRates} from './product-seo.mjs';
import {parseLanding,markdown,inline,escape,pending,faqEntries} from './lib/landing-md.mjs';
import {priceTable} from './lib/price-tables.mjs';
const content=new URL('../content/',import.meta.url),origin='https://alt-cam.net.ua';
export async function loadLandings(){return Promise.all((await fs.readdir(content)).filter(n=>/^landing-.*\.md$/.test(n)).sort().map(async name=>({...parseLanding(await fs.readFile(new URL(name,content),'utf8')),name})));}
export function contactButtons(){return `<div class="landing-actions"><a href="tel:${escape(contacts.phone)}">${escape(contacts.phoneLabel)}</a>${contacts.telegram?`<a href="https://t.me/${escape(contacts.telegram)}">Написати в Telegram</a>`:''}<a href="/#calculator">Розрахувати вартість</a></div>`;}
export async function buildLocalPages(out){
 const pages=await loadLandings(),rates=await loadInstallationRates(),prices=await fs.readFile(new URL('price-tables.md',content),'utf8'),alts=await fs.readFile(new URL('og-image-and-alt-texts.md',content),'utf8');
 const report=[],production=process.env.NODE_ENV!=='development';
 const links=pages.map(p=>`<a href="/${p.meta.slug}/">${escape(p.meta.h1)}</a>`).join('');
 const photo=d=>[...new Set(d.match(/[a-z-]+\.webp/g)||[])].map(name=>{const alt=alts.split('\n').find(l=>l.startsWith(`| \`${name}\``))?.split('|')[3]?.trim();return !alt||pending.test(alt)?'':`<figure><img src="/assets/works/${name}" alt="${escape(alt)}" loading="lazy" width="960" height="640"><figcaption>${escape(alt)}</figcaption></figure>`;}).join('');
 for(const {meta,sections,name} of pages){
  const omitted=[],faq=[],url=`${origin}/${meta.slug}/`,options={production,omitted,table:id=>priceTable(id,prices,rates),photo};let body='';
  for(const section of sections){
   let source=section.body.join('\n');
   if(section.title==='Часті запитання'){faq.push(...faqEntries(section.body,{omitted}));body+=`<section id="faq"><h2>Часті запитання</h2>${faq.map(q=>`<details><summary>${inline(q.question)}</summary><p>${inline(q.answer)}</p></details>`).join('')}</section>`;continue;}
   if(section.title==='CTA'){
    const title=source.match(/\*\*Заголовок:\*\*\s*(.*)/)?.[1],description=source.match(/\*\*Текст:\*\*\s*(.*)/)?.[1];if(pending.test(source))omitted.push(source);
    body+=`<section id="request"><h2>${escape(pending.test(source)?'Обговорімо ваше завдання':title||'Замовити консультацію')}</h2>${!pending.test(source)&&description?`<p>${inline(description)}</p>`:''}${contactButtons()}</section>`;continue;
   }
   if(section.title==='Де працюємо')source=source.replace(/\[ПІДТВЕРДИТИ[^\]]*\]/g,'').split('\n').filter(l=>l.trim()).map(l=>'- '+l).join('\n');
   source=source.replace(/^\*\*Кнопки:\*\*.*$/gm,'');const rendered=markdown(source,options);
   if(rendered)body+=section.title?`<section><h2>${escape(section.title)}</h2>${rendered}</section>`:rendered+contactButtons();
  }
  const crumbs=(meta.breadcrumb||[]).map((item,i)=>{const [label,route]=item.split(' → ');if(!/^\/(?!\/)/.test(route||''))throw Error('Unsafe breadcrumb');return {'@type':'ListItem',position:i+1,name:label,item:origin+route};});
  const schema=[{'@context':'https://schema.org','@type':'Service',name:meta.h1,url,serviceType:meta.h1,areaServed:meta.areaServed,provider:{'@id':origin+'/#business'}},{'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:crumbs}];
  if(faq.length)schema.push({'@context':'https://schema.org','@type':'FAQPage',mainEntity:faq.map(q=>({'@type':'Question',name:q.question,acceptedAnswer:{'@type':'Answer',text:q.answer}}))});
  const nav=`<nav class="landing-nav" aria-label="Навігація"><a href="/catalog.html">Каталог</a><a href="/#works">Наші роботи</a><a href="/#calculator">Калькулятор</a><a href="tel:${escape(contacts.phone)}">${escape(contacts.phoneLabel)}</a></nav>`;
  const html=`<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(meta.title)}</title><meta name="description" content="${escape(meta.description)}"><link rel="canonical" href="${url}"><link rel="stylesheet" href="/landing.css"><script type="application/ld+json">${JSON.stringify(schema).replace(/</g,'\\u003c')}</script></head><body class="landing-page"><script src="/analytics.js"></script><header class="landing-header landing-shell"><a class="landing-brand" href="/"><img src="/assets/alt-cam-mark.png" alt="" width="48" height="48">ALT-CAM Security UA</a>${nav}</header><main class="landing-shell"><nav class="landing-breadcrumbs" aria-label="Хлібні крихти">${crumbs.map(c=>`<a href="${escape(c.item)}">${escape(c.name)}</a>`).join(' / ')}</nav><h1>${escape(meta.h1)}</h1>${body}</main><footer class="landing-footer landing-shell"><h2>Послуги ALT-CAM</h2><nav class="landing-related">${links}</nav>${contactButtons()}<nav class="landing-nav"><a href="/privacy-policy.html">Конфіденційність</a><a href="/terms-of-service.html">Умови</a><a href="/delivery-and-returns.html">Доставка та повернення</a></nav></footer></body></html>`;
  if(production&&/\[(?:ЗАПОВНИТИ|ПІДТВЕРДИТИ|ВСТАВИТИ)/.test(html))throw Error(`Unresolved directive: ${name}`);
  await fs.mkdir(path.join(out,meta.slug),{recursive:true});await fs.writeFile(path.join(out,meta.slug,'index.html'),html);report.push(...omitted.map(fragment=>`${name}: ${fragment}`));
 }
 await fs.writeFile(path.join(out,'..','build-placeholders.txt'),report.join('\n\n'));
 const home=path.join(out,'index.html');let html=await fs.readFile(home,'utf8');
 html=html.replace('</head>','<link rel="stylesheet" href="/landing.css"></head>').replace('<section class="section request-section"',localContactBlock+'<section class="section request-section"');
 html=html.replace(/<div class="footer-links"><h3>Послуги<\/h3>[\s\S]*?<\/div>/,`<div class="footer-links"><h3>Послуги</h3>${links}</div>`);
 await fs.writeFile(home,html);console.log(`Landings: ${pages.length}; withheld fragments: ${report.length}`);
}
