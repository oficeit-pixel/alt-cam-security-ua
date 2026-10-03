import fs from 'node:fs/promises';
import path from 'node:path';
import {contacts} from './contacts.mjs';
import {markdown,escape} from './lib/landing-md.mjs';
const pages = [
 ['privacy-policy.html','legal-privacy-uk.md','Політика конфіденційності ALT-CAM','Обробка персональних даних, аналітика за згодою, права користувачів та контакти ALT-CAM.'],
 ['terms-of-service.html','legal-terms-uk.md','Умови використання та послуги ALT-CAM','Порядок замовлення обладнання й монтажу ALT-CAM, погодження вартості, доставка та права клієнтів.'],
 ['data-deletion.html','legal-data-deletion-uk.md','Видалення персональних даних','Як звернутися до ALT-CAM щодо видалення персональних даних, відкликання згоди та очищення даних браузера.'],
];
export function prepareLegal(source) {
 let s=source.replace(/\r/g,'').split('\n---\n').slice(1).join('\n---\n');
 s=s.replace(/\[ЗАПОВНИТИ: дата[^\]]*\]/g,'03.10.2026')
   .replaceAll('[ПІДТВЕРДИТИ: altcam.ua@gmail.com]',contacts.email)
   .replaceAll('[ПІДТВЕРДИТИ: @контакт для заявок]',`https://t.me/${contacts.telegram}`)
   .replace('знеособлена статистика','статистика з технічними ідентифікаторами')
   .replace(/- \*\*Render\*\*[^\n]*/, '- **Render** — сервер обробки заявок і замовлень.\n- **Neon Postgres** — база даних заявок і замовлень.')
   .replace(/Деякі з цих сервісів[^\n]*/, 'Для виконання замовлень можуть використовуватися сервіси за межами України. Обробка та передача даних здійснюються за належною правовою підставою; правила сторонніх сервісів доступні на їхніх сайтах.')
   .replace('Ми відповімо протягом 30 календарних днів.', 'Запит розглядається у строки та порядку, встановлені законодавством.')
   .replace(/- Протягом 30 календарних днів[^\n]*/, '- Розглянемо запит у встановленому законом порядку та повідомимо про видалення, знеособлення або підстави подальшого зберігання даних.')
   .replace('Інших документів не потрібно.', 'Не надсилайте паспорт чи інші зайві документи. Якщо для захисту даних потрібне уточнення особи заявника, ми повідомимо про це.')
   .replace(/6\.3\.[^\n]*/, '6.3. Умови гарантії та обмеження визначаються документами на товар і погодженими умовами робіт та не обмежують права, надані законом.')
   .replace(/8\.2\.[^\n]*/, '8.2. Робота сторонніх сервісів залежить від їхніх постачальників. Це не скасовує відповідальність Виконавця, встановлену законом.')
   .replace('Новою поштою, Укрпоштою або Meest Пошта','погодженою службою доставки');
 // Unknown identity, retention durations, prepayments and warranties stay out of production.
 const title=s.match(/^# (.+)$/m)?.[1];
 if(!title)throw Error('Missing legal title');
 s=s.replace(/^# .+$/m,'');
 const omitted=[];
 const html=s.split(/^## /m).map((part,i)=>{
  const [heading,...lines]=part.split('\n');
  if(!i)return markdown(part,{omitted});
  const content=markdown(lines.join('\n'),{omitted});
  return content?`<h2>${escape(heading)}</h2>${content}`:'';
 }).join('');
 return {title,html,omitted};
}
export async function buildLegalPages(out) {
 const withheld=[];
 for(const [file,source,title,description] of pages){
  const original=await fs.readFile(new URL('../'+file,import.meta.url),'utf8');
  const english=original.match(/<main[^>]*>([\s\S]*?)<\/main>/)?.[1];
  if(!english)throw Error('English legal text missing: '+file);
  const content=prepareLegal(await fs.readFile(new URL('../content/'+source,import.meta.url),'utf8'));
  withheld.push(...content.omitted.map(text=>({source,text})));
  const contact=`<p>ALT-CAM · <a href="mailto:${escape(contacts.email)}">${escape(contacts.email)}</a> · <a href="tel:${escape(contacts.phone)}">${escape(contacts.phoneLabel)}</a></p>`;
  const identity=contacts.legalName&&contacts.address?`<p>${escape(contacts.legalName)} · ${escape(contacts.address)}</p>`:'';
  let html=original.replace(/<title>[\s\S]*?<\/title>/,`<title>${title}</title>`).replace(/<meta name="description" content="[^"]*">/,`<meta name="description" content="${description}">`)
   .replace('</head>','<link rel="stylesheet" href="/legal.css"></head>')
   .replace(/<main[^>]*>[\s\S]*?<\/main>/,`<main><nav aria-label="Мова та навігація"><a href="/">ALT-CAM</a> · <a href="#uk">Українська</a> · <a href="#en" lang="en">English</a></nav><section id="uk" lang="uk"><h1>${escape(content.title)}</h1>${content.html}<h2>Зв’язок з ALT-CAM</h2>${identity}${contact}<p><a href="/privacy-policy.html">Конфіденційність</a> · <a href="/terms-of-service.html">Умови</a> · <a href="/data-deletion.html">Видалення даних</a></p></section><div id="en" lang="en">${english.replace(/<h1>/g,'<h2>').replace(/<\/h1>/g,'</h2>')}</div></main>`);
  if(/\[(?:ЗАПОВНИТИ|ПІДТВЕРДИТИ)/.test(html))throw Error('Legal placeholder leak');
  await fs.writeFile(path.join(out,file),html);
 }
 // Internal report never copied to the public site.
 await fs.writeFile(path.join(out,'..','legal-withheld.json'),JSON.stringify(withheld,null,2));
}
