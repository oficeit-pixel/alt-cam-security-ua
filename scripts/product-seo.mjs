import fs from 'node:fs/promises';
import vm from 'node:vm';
export const plainText=value=>String(value??'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
export const productPrice=item=>typeof item.price==='number'&&Number.isFinite(item.price)&&item.price>0?Math.round(item.price*100)/100:null;
const categories=new Set(['Камери відеоспостереження','Відеореєстратори та накопичувачі','Домофони та викличні панелі','Ajax та охоронна сигналізація','Аварійне електроживлення']);
export function selectIndexedProducts(products,limit=300){
 const groups=new Map();
 for(const item of products){
  const description=plainText(item.description);
  if(!item.id||!item.name||!categories.has(item.category)||!productPrice(item)||description.length<300||/характеристики уточнюються|\[(?:ЗАПОВНИТИ|ПІДТВЕРДИТИ)/i.test(description))continue;
  if(!groups.has(item.category))groups.set(item.category,[]);
  groups.get(item.category).push(item);
 }
 for(const list of groups.values())list.sort((a,b)=>String(a.id).localeCompare(String(b.id),'en'));
 const selected=new Set(), lists=[...groups.entries()].sort(([a],[b])=>a.localeCompare(b,'uk')).map(([,items])=>items);
 // Round-robin keeps smaller eligible categories represented, independent of feed order.
 for(let i=0;selected.size<Math.min(300,Math.max(0,limit))&&lists.some(list=>list[i]);i++)for(const list of lists){
  if(list[i]&&selected.size<limit&&selected.size<300)selected.add(list[i].id);
 }
 return selected;
}
export function productOffer(item,url){
 const price=productPrice(item);if(!price)return null;
 return {'@type':'Offer',price,priceCurrency:'UAH',availability:`https://schema.org/${item.available===true?'InStock':'PreOrder'}`,url,seller:{'@type':'Organization','@id':'https://alt-cam.net.ua/#business',name:'ALT-CAM Security UA'}};
}
export async function loadInstallationRates(){
 const context={window:{}};
 vm.runInNewContext(await fs.readFile(new URL('../data/service-rates.js',import.meta.url),'utf8'),context);
 return context.window.ALTCAM_RATES;
}
export function installationBlock(item,rates){
 if(item.category==='Камери відеоспостереження')return `<section><h2>Монтаж у Києві та області</h2><p>Монтаж однієї внутрішньої камери — ${rates.video.indoorCamera.one} ₴, однієї зовнішньої — ${rates.video.outdoorCamera.one} ₴. Кабель, матеріали та налаштування оплачуються окремо; склад робіт погоджуємо до виїзду.</p><a href="/montazh-videosposterezhennia-kyiv/">Монтаж відеоспостереження</a></section>`;
 if(item.category==='Домофони та викличні панелі')return `<section><h2>Встановлення відеодомофона</h2><p>Монтаж аналогового комплекту — ${rates.intercom.analogKit} ₴, IP-комплекту — ${rates.intercom.ipKit} ₴. Кабель та додаткові роботи розраховуються окремо після перевірки сумісності.</p><a href="/videodomofony/">Підбір і монтаж відеодомофонів</a></section>`;
 return '';
}
