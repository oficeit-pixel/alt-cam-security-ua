import fs from 'node:fs/promises';
import path from 'node:path';

const pages = [
  {
    slug: 'montazh-videosposterezhennia-kyiv',
    title: 'Монтаж відеоспостереження у Києві та Київській області',
    description: 'Виїзний монтаж камер, відеодомофонів і резервного живлення у Києві та області. Підбір обладнання, узгоджений кошторис і налаштування перегляду зі смартфона.',
    area: ['Київ', 'Київська область'],
    sections: [
      ['Що враховуємо перед монтажем', 'Для квартири визначаємо зону входу й спосіб прокладання кабелю. У магазині враховуємо касу, торговий зал і склад. Для приватного будинку перевіряємо освітлення двору, відстань до воріт, інтернет і місце встановлення реєстратора. Камери спрямовуємо на потрібні зони, уникаючи зайвого огляду приватного простору сусідів.'],
      ['Обладнання та роботи в одному кошторисі', 'Погоджуємо кількість камер, об’єктиви, реєстратор, диск для архіву, кабель та монтажні матеріали. Окремо враховуємо довжину трас, висоту робіт і налаштування віддаленого доступу. Остаточну вартість визначаємо після уточнення умов об’єкта — без вигаданої фіксованої ціни за будь-який монтаж.'],
      ['Коли потрібне резервне живлення', 'Щоб зберігати відео під час відключень, живлення потрібне не лише камерам, а й реєстратору та мережевому обладнанню. Для доступу зі смартфона також потрібен працездатний інтернет. Час автономності розраховуємо за навантаженням і ємністю акумулятора.'],
      ['Як замовити виїзд', 'Надішліть населений пункт, тип об’єкта, потрібні зони огляду та кілька фото місць монтажу. Уточнимо завдання, попередній склад системи й можливий час виїзду. Приймання клієнтів в офісі не передбачене — працюємо на вашому об’єкті.'],
    ],
  },
  {
    slug: 'videosposterezhennia-vyshhorod',
    title: 'Відеоспостереження та контроль доступу у Вишгороді',
    description: 'Монтаж камер і відеодомофонів у Вишгороді з виїздом. Приклади робіт у під’їздах, квартирах і магазині; контроль доступу U-PROX та камери в ліфтах.',
    area: ['Вишгород'],
    sections: [
      ['Під’їзди та ліфти', 'У портфоліо ALT-CAM є відеоспостереження у під’їздах багатоквартирних будинків у Вишгороді, контроль доступу U-PROX і камери в ліфтах. Для спільних зон заздалегідь погоджуємо місця встановлення та доступ до обладнання з уповноваженим представником будинку.'],
      ['Квартири та магазини', 'Серед прикладів робіт — відеодомофони у квартирах у Вишгороді та Києві, а також відеоспостереження магазину товарів з Європи у Вишгороді. Внутрішній монітор домофона розміщуємо у квартирі, викличну панель — біля входу. Для магазину підбираємо ракурси під конкретні зони, а не лише кількість камер.'],
      ['Оновлення наявної системи', 'Якщо камери вже встановлені, спочатку перевіряємо проводку, живлення, стан запису та сумісність обладнання. Придатні компоненти можна залишити, якщо це відповідає завданню. Перелік замін і робіт погоджуємо до початку монтажу.'],
      ['Підготовка до виїзду', 'Повідомте тип об’єкта, кількість входів, наявність інтернету та потребу в роботі без світла. Для під’їзду або ліфта додатково уточнимо умови доступу до технічних зон. Працюємо з виїздом, дату й кошторис погоджуємо індивідуально.'],
    ],
  },
];
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

export async function buildLocalPages(out) {
  const links = pages.map(p => `<a href="/${p.slug}/">${escape(p.title)}</a>`).join('');
  for (const page of pages) {
    const url = `https://alt-cam.net.ua/${page.slug}/`;
    const schema = {'@context':'https://schema.org','@type':'Service',name:page.title,url,
      serviceType:'Монтаж систем безпеки',areaServed:page.area,
      provider:{'@type':'Organization',name:'ALT-CAM Security UA',url:'https://alt-cam.net.ua/'}};
    const html = `<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(page.title)} | ALT-CAM</title><meta name="description" content="${escape(page.description)}"><link rel="canonical" href="${url}"><style>body{margin:0;background:#17171a;color:#eee;font:17px/1.7 Arial}main{max-width:960px;margin:auto;padding:32px 20px}a{color:#fc0}nav{display:flex;gap:20px;flex-wrap:wrap}h1{font-size:clamp(28px,5vw,46px);line-height:1.2}section{margin:28px 0;padding:20px;background:#242428;border-radius:12px}h2{line-height:1.3}.cta{display:inline-block;background:#fc0;color:#111;padding:12px 20px;border-radius:8px;font-weight:bold}footer{margin-top:32px}</style><script type="application/ld+json">${JSON.stringify(schema).replace(/</g,'\\u003c')}</script></head><body><script src="/analytics.js"></script><main><nav><a href="/">ALT-CAM</a><a href="/catalog.html">Обладнання</a><a href="/#works">Приклади робіт</a></nav><h1>${escape(page.title)}</h1><p>${escape(page.description)}</p><a class="cta" href="/#request">Обговорити монтаж з виїздом</a>${page.sections.map(([title,text])=>`<section><h2>${escape(title)}</h2><p>${escape(text)}</p></section>`).join('')}<h2>Обладнання з доставкою по Україні</h2><p>Монтаж виконуємо у Києві та області. Для інших регіонів пропонуємо підбір і доставлення обладнання та дистанційну підтримку. Умови доставки й повернення наведені окремо.</p><nav><a href="/videodomofony/">Відеодомофони</a><a href="/rezervne-zhyvlennia/">Резервне живлення</a><a href="/catalog.html">Каталог</a></nav><h2>Територія виїзду</h2><nav>${links}</nav><footer><a href="/delivery-and-returns.html">Доставка та повернення</a> · <a href="/privacy-policy.html">Конфіденційність</a></footer></main></body></html>`;
    await fs.mkdir(path.join(out,page.slug),{recursive:true});
    await fs.writeFile(path.join(out,page.slug,'index.html'),html);
  }
  const home = path.join(out,'index.html');
  await fs.writeFile(home,(await fs.readFile(home,'utf8')).replace('<footer class="footer"',`<nav class="container" aria-label="Монтаж з виїздом" style="display:flex;gap:24px;flex-wrap:wrap;padding:24px">${links}</nav><footer class="footer"`));
  const sitemap = path.join(out,'sitemap.xml');
  await fs.writeFile(sitemap,(await fs.readFile(sitemap,'utf8')).replace('</urlset>',pages.map(p=>`<url><loc>https://alt-cam.net.ua/${p.slug}/</loc></url>`).join('')+'</urlset>'));
}
