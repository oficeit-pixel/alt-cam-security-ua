import fs from 'node:fs/promises';
import {segments} from '../content/audience-segments.mjs';
export async function loadAudienceLandings(){
 const kits=JSON.parse(await fs.readFile(new URL('../data/kits.json',import.meta.url),'utf8'));
 return segments.map(s=>{
  const kit=kits.find(k=>k.id===s.kit);if(!kit)throw Error('Missing audience kit: '+s.kit);
  const priced=typeof kit.price_from_with_install_uah==='number'&&Number.isFinite(kit.price_from_with_install_uah)&&kit.price_from_with_install_uah>0;
  const h1='Відеоспостереження для '+s.subject+' у Києві та Вишгороді';
  return {name:'audience-segments.mjs:'+s.slug,meta:{slug:s.slug,title:'Камери для '+s.subject+' — Київ і Вишгород | ALT-CAM',description:s.description,h1,areaServed:['Київ','Вишгород'],breadcrumb:['Головна → /',s.label+' → /'+s.slug+'/']},
   sections:[
    {title:'',body:[s.intro]},
    {title:'Що зазвичай потрібно контролювати',body:s.zones.map(z=>'- '+z)},
    {title:'Типовий комплект',body:[s.scope,'','### '+kit.name,'',...kit.composition.map(v=>'- '+v),'',...(priced?['Від '+kit.price_from_with_install_uah.toLocaleString('uk-UA')+' ₴ із монтажем. Кінцева сума залежить від траси, висоти й архіву.','']:[]),'Моделі, сумісність і остаточний склад погоджуємо до замовлення.']},
    {title:'Ціна робіт',body:['Вартість обладнання й роботи рахуємо окремо. Перегляньте [таблицю цін встановлення камер](/vstanovlennia-kamer-vyshhorod/) або [калькулятор](/#calculator). Кабельні траси, висоту та доступ до місць монтажу уточнюємо за фото.']},
    {title:'Часті запитання',body:s.faq.flatMap(([q,a])=>['### '+q,a,''])},
    {title:'CTA',body:['**Заголовок:** Надішліть фото','**Текст:** Покажіть зони контролю та можливі кабельні траси — обговоримо склад системи. Не надсилайте паролі або документи.']},
    {title:'Послуги у вашому місті',body:['[Монтаж у Києві](/montazh-videosposterezhennia-kyiv/) · [Комплексна безпека у Вишгороді](/videosposterezhennia-vyshhorod/)']}
   ]};
 });
}
