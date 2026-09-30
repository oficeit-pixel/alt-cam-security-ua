import fs from 'node:fs';
import vm from 'node:vm';
const context={window:{}};
vm.runInNewContext(fs.readFileSync(new URL('../contacts.js',import.meta.url),'utf8'),context,{timeout:1000});
export const contacts=Object.freeze({...context.window.ALTCAM_CONTACTS});
const escape=value=>String(value||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
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
