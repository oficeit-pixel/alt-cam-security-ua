import fs from 'node:fs/promises';
import {escape} from './lib/landing-md.mjs';
export function kitPrice(kit){
 const n=kit?.price_from_with_install_uah;
 return typeof n==='number'&&Number.isFinite(n)&&n>0?`від ${n.toLocaleString('uk-UA')} ₴ із монтажем`:'за розрахунком';
}
export async function renderKits(html){
 const kits=JSON.parse(await fs.readFile(new URL('../data/kits.json',import.meta.url),'utf8'));
 return html.replace(/<article class="package-card[^"]*">[\s\S]*?<\/article>/g,card=>{
  const kit=kits.find(k=>card.includes(`data-package="${k.id}"`));if(!kit)return card;
  return card.replace(/<h3>[\s\S]*?<\/h3>/,`<h3>${escape(kit.name)}</h3>`)
   .replace(/<ul class="package-list">[\s\S]*?<\/ul>/,`<ul class="package-list">${kit.composition.map(x=>`<li>${escape(x)}</li>`).join('')}</ul>`)
   .replace(/<strong class="package-price">[\s\S]*?<\/strong>/,`<strong class="package-price">${kitPrice(kit)}</strong><small class="kit-price-note">Кінцева сума залежить від траси, висоти й архіву</small>`);
 });
}
