import fs from 'node:fs';
import vm from 'node:vm';
const context={window:{}};
vm.runInNewContext(fs.readFileSync(new URL('../contacts.js',import.meta.url),'utf8'),context,{timeout:1000});
export const contacts=Object.freeze({...context.window.ALTCAM_CONTACTS});
const escape=value=>String(value||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function renderBusinessDetails(html, values=contacts) {
  const clean=value=>typeof value==='string'?value.trim():'';
  const name=clean(values.legalName);
  const legal=name?[name,clean(values.legalCode),clean(values.legalAddress)].filter(Boolean).map(escape).join(' · '):'';
  const warranties=[
    clean(values.warrantyWorks)?`Гарантія на роботи: ${escape(clean(values.warrantyWorks))}`:'',
    clean(values.warrantyEquipment)?`Гарантія на обладнання: ${escape(clean(values.warrantyEquipment))}`:''
  ].filter(Boolean).join(' · ');
  const years=Number(values.yearsExperience);
  const experience=Number.isInteger(years)&&years>0&&years<=100
    ?`<article class="why-card reveal"><span>${years}</span><h3>Досвід роботи: ${years} р.</h3><p>Практичний досвід монтажу та налаштування систем безпеки.</p></article>`:'';
  html=html.replace('<!-- ALTCAM_EXPERIENCE -->',experience);
  if(!legal&&!warranties)return html;
  // Idempotent finalization, including pages without a pre-existing footer.
  if(html.includes('data-business-details'))return html;
  const block=`<div class="business-details" data-business-details>${legal?`<p>${legal}</p>`:''}${warranties?`<p>${warranties}</p>`:''}</div>`;
  return /<\/footer>/i.test(html)?html.replace(/<\/footer>/i,`${block}</footer>`)
    :html.replace(/<\/body>/i,`<footer class="container">${block}</footer></body>`);
}
export function renderContacts(html, values=contacts){
  const urls={phone:values.phone?`tel:${values.phone}`:'',email:values.email?`mailto:${values.email}`:'',
    telegram:values.telegram?`https://t.me/${encodeURIComponent(values.telegram.replace(/^@/,''))}`:'',
    telegramChannel:values.telegramChannel?`https://t.me/${encodeURIComponent(values.telegramChannel.replace(/^@/,''))}`:'',
    whatsapp:values.whatsapp?`https://wa.me/${values.whatsapp.replace(/\D/g,'')}`:'',
    viber:values.viber?`viber://chat?number=${encodeURIComponent(values.viber)}`:''};
  return html.replace(/<a\b([^>]*)>([\s\S]*?)<\/a>/gi,(whole,attrs,label)=>{
    const kind=attrs.match(/data-contact="([^"]+)"/)?.[1]
      || (/href="tel:/.test(attrs)?'phone':/href="mailto:/.test(attrs)?'email':null);
    if(!kind||!(kind in urls))return whole;
    if(!urls[kind])return '';
    attrs=attrs.replace(/\s(?:href|hidden)(?:="[^"]*")?/g,'');
    if(kind==='phone'&&/^\+?[\d\s()-]+$/.test(label.trim()))label=escape(values.phoneLabel||values.phone);
    if(kind==='email')label=escape(values.email);
    if(kind==='telegram'&&label.startsWith('@'))label='@'+escape(values.telegram);
    return `<a${attrs} href="${escape(urls[kind])}">${label}</a>`;
  });
}
