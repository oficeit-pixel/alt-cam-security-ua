import fs from 'node:fs/promises';
import {contacts} from './contacts.mjs';
import {escape,faqEntries} from './lib/landing-md.mjs';
import {loadInstallationRates} from './product-seo.mjs';
const origin='https://alt-cam.net.ua';
const strip=value=>value.replace(/<[^>]*>/g,'').replace(/&amp;/g,'&').replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/&lt;/g,'<').replace(/&gt;/g,'>').trim();
export function organizationSchema(c=contacts){
 const business={'@context':'https://schema.org','@type':'HomeAndConstructionBusiness','@id':origin+'/#business',name:c.brandName||'ALT-CAM',url:origin+'/',logo:origin+'/assets/alt-cam-mark.png',telephone:c.phone,email:c.email,areaServed:['Київ','Вишгород','Київська область'],sameAs:[c.facebook,c.instagram,c.threads].filter(x=>typeof x==='string'&&/^https:\/\//.test(x))};
 for(const key of ['legalName','openingHours'])if(c[key]&&!/\[/.test(c[key]))business[key]=c[key];
 // A service-area business has no invented public office or postal address.
 for(const key of Object.keys(business))if(business[key]===''||business[key]==null||(Array.isArray(business[key])&&!business[key].length))delete business[key];
 return business;
}
export function visibleFaqSchema(html){
 const section=html.match(/<section[^>]*id="faq"[\s\S]*?<\/section>/)?.[0]||'';
 const mainEntity=[...section.matchAll(/<details[^>]*>\s*<summary>([\s\S]*?)<\/summary>\s*<p>([\s\S]*?)<\/p>\s*<\/details>/g)].map(m=>({'@type':'Question',name:strip(m[1]),acceptedAnswer:{'@type':'Answer',text:strip(m[2])}}));
 return {'@context':'https://schema.org','@type':'FAQPage',mainEntity};
}
export function homePriceTable(r){
 const money=n=>Number(n).toLocaleString('uk-UA')+' ₴',v=r.video;
 const rows=[['Внутрішня камера',v.indoorCamera],['Вулична камера',v.outdoorCamera]].map(([name,rates])=>`<tr><th scope="row">${name}</th>${['one','two','threeToEight','overEight'].map(k=>`<td>${money(rates[k])}</td>`).join('')}</tr>`).join('');
 const others=[['Налаштування реєстратора',v.recorderSetup],['Перегляд зі смартфона',v.mobileAppSetup],['Монтаж аналогового домофона',r.intercom.analogKit],['Монтаж стартового комплекту Ajax',r.ajax.starterKit]];
 const example=2*v.indoorCamera.two+2*v.outdoorCamera.two+v.recorderSetup+v.mobileAppSetup;
 return `<section class="section home-prices" id="installation-prices"><div class="container"><span class="section-kicker">Прозорі ціни</span><h2>Ціни на монтаж відеоспостереження</h2><p>Ціна за роботи залежить від кількості камер одного типу. Обладнання, кабель і матеріали розраховуються окремо.</p><div class="table-scroll" tabindex="0" role="region" aria-label="Вартість монтажу камер"><table><caption>Ціна за одну камеру відповідного типу</caption><thead><tr><th scope="col">Робота</th><th scope="col">1 камера</th><th scope="col">2 камери</th><th scope="col">3–8 камер</th><th scope="col">Від 9 камер</th></tr></thead><tbody>${rows}</tbody></table></div><dl class="home-price-extras">${others.map(([label,n])=>`<div><dt>${label}</dt><dd>${money(n)}</dd></div>`).join('')}</dl><p><strong>Приклад: 2 внутрішні + 2 вуличні камери з налаштуванням реєстратора та смартфона — ${money(example)} за роботи.</strong></p><p>Роботи на висоті та нестандартні траси погоджуються окремо до початку монтажу. На телефоні таблицю можна прокрутити горизонтально.</p><div class="hero-actions"><a class="btn btn-primary" href="/#calculator">Порахувати свою систему</a><a class="btn btn-black" href="/vstanovlennia-kamer-vyshhorod/">Повний прайс</a></div></div></section>`;
}
export async function buildHomepage(html,{values=contacts}={}){
 const source=await fs.readFile(new URL('../content/homepage.md',import.meta.url),'utf8'),rates=await loadInstallationRates();
 const title=source.match(/\*\*title[^\n]*?`([^`]+)`/)?.[1],description=source.match(/\*\*description[^\n]*?`([^`]+)`/)?.[1],h1=source.match(/\*\*H1:\*\* (.*)/)?.[1],lead=source.match(/\*\*Підзаголовок:\*\* (.*)/)?.[1];
 if(!title||!description||!h1||!lead)throw Error('Homepage content metadata missing');
 html=html.replace(/<title>[\s\S]*?<\/title>/,`<title>${escape(title)}</title>`).replace(/(<meta name="description" content=")[^"]*(")/,`$1${escape(description)}$2`);
 for(const [key,value] of [['title',title],['description',description]])html=html.replace(new RegExp(`(<meta property="og:${key}" content=")[^"]*(")`),`$1${escape(value)}$2`);
 html=html.replace(/<h1>[\s\S]*?<\/h1>/,`<h1>${escape(h1)}</h1><a class="hero-phone" href="tel:${escape(values.phone)}">${escape(values.phoneLabel)}</a>`);
 html=html.replace(/(<div class="hero-content reveal">[\s\S]*?)<p>[\s\S]*?<\/p>/,`$1<p>${escape(lead)}</p>`);
 html=html.replace(/<ul class="hero-benefits">[\s\S]*?<\/ul>/,`<ul class="hero-benefits"><li>Кошторис до початку робіт</li><li>Прозорий прайс за кількістю камер</li><li>Перегляд зі смартфона</li><li>Підбір резервного живлення</li></ul>`);
 html=html.replace(/<a class="btn btn-primary btn-large" href="#quiz">[\s\S]*?<\/a>/,values.telegram?`<a class="btn btn-primary btn-large" href="https://t.me/${escape(values.telegram)}">Надіслати фото в Telegram</a>`:'');
 html=html.replace(/<div class="hero-trust">[\s\S]*?<\/div>\s*<\/div>\s*<\/div>/,`<div class="hero-trust"><div><strong>Київ і Вишгород</strong><span>виїзд на об’єкт</span></div><div><strong>Прайс на сайті</strong><span>кошторис до початку робіт</span></div><div><strong>Реальні об’єкти</strong><span>фото наших робіт нижче</span></div></div></div>`);
 html=html.replace(/<div class="why-grid">[\s\S]*?<\/div>/,`<div class="why-grid"><!-- ALTCAM_EXPERIENCE --><article class="why-card"><h3>Реальні об’єкти</h3><p>Під’їзди, магазини та квартири у Вишгороді й Києві.</p></article><article class="why-card"><h3>Кошторис до початку робіт</h3><p>Роботи, обладнання та матеріали — окремими рядками.</p></article><article class="why-card"><h3>Підтримка після монтажу</h3><p>Зв’язок у Telegram і за телефоном: допомога з налаштуванням та розвитком системи.</p></article></div>`);
 html=html.replace('<section class="section faq-section"',homePriceTable(rates)+'<section class="section faq-section"');
 const entries=faqEntries(source.slice(source.indexOf('## FAQ')).split('\n'));
 const v=rates.video;
 entries[0].answer=`Монтаж однієї внутрішньої камери — ${v.indoorCamera.one} ₴, однієї вуличної — ${v.outdoorCamera.one} ₴. Ціна залежить від кількості камер одного типу. Приклад: 2 внутрішні та 2 вуличні камери з налаштуванням реєстратора і смартфона — ${2*v.indoorCamera.two+2*v.outdoorCamera.two+v.recorderSetup+v.mobileAppSetup} ₴ за роботи. Обладнання та матеріали — окремо.`;
 html=html.replace(/<details class="faq-item reveal"><summary>Скільки коштує[\s\S]*?<\/details>/,'');
 html=html.replace(/<details class="faq-item reveal"><summary>Ви працюєте по всій Україні[\s\S]*?<\/details>/,'');
 html=html.replace('<div class="faq-list">','<div class="faq-list">'+entries.map(q=>`<details class="faq-item"><summary>${escape(q.question)}<span></span></summary><p>${escape(q.answer.replace('Telegram або Viber','Telegram'))}</p></details>`).join(''));
 html=html.replace(/<script type="application\/ld\+json">[\s\S]*?<\/script>/g,'');
 const schemas=[organizationSchema(values),{'@context':'https://schema.org','@type':'WebSite','@id':origin+'/#website',url:origin+'/',name:values.brandName||'ALT-CAM',publisher:{'@id':origin+'/#business'}},visibleFaqSchema(html)];
 return html.replace('</head>',`<link rel="stylesheet" href="/homepage.css"><script type="application/ld+json">${JSON.stringify(schemas).replace(/</g,'\\u003c')}</script></head>`);
}
