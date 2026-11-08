import fs from 'node:fs/promises';
import path from 'node:path';
import {parseLanding,markdown,escape} from './lib/landing-md.mjs';
import {contacts} from './contacts.mjs';
import {trust} from './trust.mjs';
const origin='https://alt-cam.net.ua',dir=new URL('../content/blog/',import.meta.url);
export const pagePath=n=>n===1?'/blog/':`/blog/page/${n}/`;
export const paginate=(items,size=10)=>Array.from({length:Math.max(1,Math.ceil(items.length/size))},(_,i)=>items.slice(i*size,(i+1)*size));
export async function loadArticles(){
 const articles=await Promise.all((await fs.readdir(dir)).filter(n=>n.endsWith('.md')).map(async file=>{
  const source=await fs.readFile(new URL(file,dir),'utf8'),a=parseLanding(source);
  if(/TODO_OWNER|\[ЗАПОВНИТИ|\[ПІДТВЕРДИТИ/.test(source))throw Error('Unresolved blog content: '+file);
  if(!/^\d{4}-\d{2}-\d{2}$/.test(a.meta.date)||!Number.isFinite(Date.parse(a.meta.date)))throw Error('Blog date: '+file);
  a.url=origin+'/blog/'+a.meta.slug+'/';a.file=file;
  a.words=a.sections.map(s=>s.body.join(' ')).join(' ').replace(/\[([^\]]+)\]\([^)]*\)/g,'$1').trim().split(/\s+/).length;
  if(a.words<700||a.words>1000)throw Error(`Blog word count ${a.words}: ${file}`);
  a.meta.image ||= '/assets/alt-cam-mark.png';
  if(!/^\/assets\/[a-z0-9/_-]+\.(?:webp|png|jpg)$/.test(a.meta.image))throw Error('Unsafe blog image');
  await fs.access(new URL('..'+a.meta.image,import.meta.url));
  a.meta.services=a.meta.services.split(',').map(s=>s.trim());return a;
 }));
 for(const key of ['slug','title','h1'])if(new Set(articles.map(a=>a.meta[key])).size!==articles.length)throw Error('Duplicate blog '+key);
 return articles.sort((a,b)=>b.meta.date.localeCompare(a.meta.date)||a.meta.slug.localeCompare(b.meta.slug));
}
const json=x=>JSON.stringify(x).replace(/</g,'\\u003c');
function crumbs(items){return {'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:items.map(([name,url],i)=>({'@type':'ListItem',position:i+1,name,item:origin+url}))};}
function shell({title,description,url,image='/assets/alt-cam-mark.png',body,schema=[],type='website'}){
 return `<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(title)}</title><meta name="description" content="${escape(description)}"><link rel="canonical" href="${url}"><meta property="og:title" content="${escape(title)}"><meta property="og:description" content="${escape(description)}"><meta property="og:type" content="${type}"><meta property="og:image" content="${origin+image}"><meta name="twitter:card" content="summary_large_image"><link rel="stylesheet" href="/blog.css"><script type="application/ld+json">${json(schema)}</script></head><body><script src="/analytics.js"></script><header><a href="/">ALT-CAM</a><nav aria-label="Навігація"><a href="/blog/">Корисне</a><a href="/catalog.html">Каталог</a><a href="/#calculator">Калькулятор</a></nav></header><main>${body}</main><footer><nav aria-label="Посилання в підвалі"><a href="/blog/">Блог</a><a href="/privacy-policy.html">Конфіденційність</a><a href="/delivery-and-returns.html">Доставка та повернення</a></nav></footer></body></html>`;
}
function card(a){return `<article class="blog-card"><a href="/blog/${a.meta.slug}/"><img src="${a.meta.image}" alt="${escape(a.meta.image_alt||a.meta.h1)}" width="1448" height="1086" loading="lazy"><h2>${escape(a.meta.h1)}</h2></a><time datetime="${a.meta.date}">${a.meta.date}</time><p>${escape(a.meta.description)}</p></article>`;}
export async function buildBlog(out){
 const articles=await loadArticles();
 const author=typeof trust.blogAuthor==='string'&&trust.blogAuthor.trim()&&!trust.blogAuthor.includes('TODO_OWNER')?trust.blogAuthor.trim():'ALT-CAM';
 async function write(route,html){const target=path.join(out,route,'index.html');await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target,html);}
 for(const a of articles){
  const m=a.meta,sections=a.sections.map((s,i)=>s.title?`<section id="section-${i}"><h2>${escape(s.title)}</h2>${markdown(s.body.join('\n'))}</section>`:markdown(s.body.join('\n'))).join('');
  const toc=`<nav class="blog-toc" aria-label="Зміст статті"><h2>Зміст</h2><ol>${a.sections.map((s,i)=>s.title?`<li><a href="#section-${i}">${escape(s.title)}</a></li>`:'').join('')}</ol></nav>`;
  const body=`<nav aria-label="Хлібні крихти"><a href="/">Головна</a> / <a href="/blog/">Блог</a> / <span>${escape(m.h1)}</span></nav><article><h1>${escape(m.h1)}</h1><p class="blog-meta"><time datetime="${m.date}">${m.date}</time> · Автор: ${escape(author)}</p><figure><img class="blog-hero" src="${m.image}" alt="${escape(m.image_alt||m.h1)}" width="1448" height="1086" fetchpriority="high"><figcaption>${escape(m.caption||'Ілюстрація до статті ALT-CAM')}</figcaption></figure>${toc}<div class="article-text">${sections}</div></article><section class="blog-cta"><h2>Підберемо рішення</h2><p>Надішліть фото об’єкта та опишіть завдання. Склад, ціну й умови підтвердимо до оплати.</p><a class="button" href="${escape(contacts.consultantUrl)}">Написати в Telegram</a> <a href="/#calculator">Розрахувати вартість</a></section><section><h2>Схожі статті</h2><ul>${articles.filter(b=>b!==a).slice(0,3).map(b=>`<li><a href="/blog/${b.meta.slug}/">${escape(b.meta.h1)}</a></li>`).join('')}</ul></section>`;
  const schema=[{'@context':'https://schema.org','@type':'Article',headline:m.h1,description:m.description,datePublished:m.date,author:{'@type':author==='ALT-CAM'?'Organization':'Person',name:author},publisher:{'@id':origin+'/#business'},image:origin+m.image,mainEntityOfPage:a.url,inLanguage:'uk'},crumbs([['Головна','/'],['Блог','/blog/'],[m.h1,`/blog/${m.slug}/`]])];
  await write('blog/'+m.slug,shell({title:m.title,description:m.description,url:a.url,image:m.image,body,schema,type:'article'}));
 }
 const pages=paginate(articles);
 for(const [i,items]of pages.entries()){
  const n=i+1,title=n===1?'Корисне про системи безпеки | Блог ALT-CAM':`Блог ALT-CAM — сторінка ${n}`;
  const body=`<nav aria-label="Хлібні крихти"><a href="/">Головна</a> / <span>Блог</span></nav><h1>${n===1?'Корисне про системи безпеки':`Блог — сторінка ${n}`}</h1><p>Практичні пояснення, відкриті розрахунки та підготовка до монтажу у Києві й Вишгороді.</p><div class="blog-grid">${items.map(card).join('')}</div>${pages.length>1?`<nav class="blog-pagination" aria-label="Сторінки блогу">${pages.map((_,j)=>j===i?`<span aria-current="page">${j+1}</span>`:`<a href="${pagePath(j+1)}">${j+1}</a>`).join(' ')}</nav>`:''}`;
  await write(pagePath(n).slice(1),shell({title,description:`Статті ALT-CAM про камери, ДБЖ, монтаж і підготовку об’єкта. Сторінка ${n}.`,url:origin+pagePath(n),body,schema:[crumbs([['Головна','/'],[n===1?'Блог':`Блог — сторінка ${n}`,pagePath(n)]])]}));
 }
 for(const slug of new Set(articles.flatMap(a=>a.meta.services))){
  const target=path.join(out,slug,'index.html');let html=await fs.readFile(target,'utf8');
  const related=articles.filter(a=>a.meta.services.includes(slug));
  html=html.replace('</main>',`<section class="blog-related"><h2>Корисне за темою</h2><ul>${related.map(a=>`<li><a href="/blog/${a.meta.slug}/">${escape(a.meta.h1)}</a></li>`).join('')}</ul></section></main>`);
  await fs.writeFile(target,html);
 }
 console.log('Blog:',articles.map(a=>`${a.meta.slug}: ${a.words} words`).join('; '));
}
