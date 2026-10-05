import fs from 'node:fs/promises';
import vm from 'node:vm';
export const plainText=value=>String(value??'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
export const productPrice=item=>typeof item.price==='number'&&Number.isFinite(item.price)&&item.price>0?Math.round(item.price*100)/100:null;
export function selectIndexedProducts(products){
 // Owner requested the entire public catalog, superseding the initial 300-page rollout.
 // Eligibility is not a claim that Google has actually indexed these URLs.
 return new Set(products.filter(item=>item.id&&item.name).map(item=>item.id));
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
