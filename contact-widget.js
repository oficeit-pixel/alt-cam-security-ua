(() => {
  'use strict';
  if (document.getElementById('contact-widget') || /\/admin(?:\/|\.html|$)/.test(location.pathname)) return;
  const c = window.CONTACTS || window.ALTCAM_CONTACTS || {};
  const style = document.createElement('style');
  style.textContent = `
  .cw{font:16px/1.45 Arial,sans-serif;color:#f6f6f6;position:relative;z-index:9000}
  .cw [hidden]{display:none!important}.cw button,.cw a,.cw input,.cw textarea{font:inherit;box-sizing:border-box}
  .cw button,.cw a{touch-action:manipulation}.cw button,.cw-links a,.cw-quick a{border:1px solid #777;border-radius:10px;padding:10px 12px;background:#262626;color:#fff;cursor:pointer;text-decoration:none}
  .cw :focus-visible{outline:3px solid #ffdc36;outline-offset:3px}
  .cw-launch{position:fixed;right:16px;bottom:calc(18px + env(safe-area-inset-bottom));background:#ffcf00!important;color:#111!important;font-weight:700!important}
  .cw-panel{position:fixed;right:16px;bottom:calc(78px + env(safe-area-inset-bottom));width:min(390px,calc(100vw - 32px));max-height:calc(100dvh - 110px);overflow:auto;background:#171717;border:1px solid #ffcf00;border-radius:16px;padding:18px;box-sizing:border-box;box-shadow:0 8px 35px #0006}
  .cw-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.cw h2{margin:0;font-size:21px}.cw p{font-size:14px;margin:12px 0}.cw-quick,.cw-links{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.cw-quick button,.cw-quick a,.cw-links a{font-size:14px}
  .cw label{display:block;margin-top:10px}.cw input,.cw textarea{display:block;width:100%;border:1px solid #888;border-radius:7px;background:#fff;color:#111;padding:9px;min-height:42px}.cw textarea{resize:vertical}.cw-submit{margin-top:12px;background:#ffcf00!important;color:#111!important}.cw form a{color:#ffdc36}.cw-honey{position:absolute;left:-10000px;width:1px;height:1px;overflow:hidden}
  .messenger-dock,.aic-fab,.aic-offer{display:none!important}
  @media(max-width:700px){body.cw-ready{padding-bottom:calc(80px + env(safe-area-inset-bottom))}.cw-launch{right:12px;bottom:calc(22px + env(safe-area-inset-bottom));max-width:calc(100vw - 24px)}.cw-panel{position:relative;inset:auto;max-height:none;width:auto;margin:20px 12px;padding-bottom:calc(18px + env(safe-area-inset-bottom))}body.cw-open .calc-fab{display:none!important}.cw{scroll-margin-top:110px}.ga-consent{box-sizing:border-box;max-width:calc(100vw - 32px)!important}}
  `;
  document.head.append(style);
  const root = document.createElement('section'); root.id='contact-widget'; root.className='cw';
  root.innerHTML=`<button class="cw-launch" type="button" aria-expanded="false" aria-controls="cw-panel">Напишіть нам</button>
  <div class="cw-panel" id="cw-panel" role="dialog" aria-modal="false" aria-labelledby="cw-title" hidden>
    <div class="cw-head"><h2 id="cw-title">Напишіть нам</h2><button type="button" class="cw-close" aria-label="Закрити контакти">×</button></div>
    <p>Залиште заявку або продовжуйте в Telegram. Це форма звернення, не онлайн-чат.</p>
    <div class="cw-quick" aria-label="Тема звернення"><button type="button" data-topic="Підібрати камери">Підібрати камери</button><button type="button" data-topic="Порахувати кошторис за фото">Порахувати кошторис за фото</button><button type="button" data-topic="Резервне живлення">Резервне живлення</button></div>
    <form id="contact-widget-form">
      <label for="cw-name">Ім’я</label><input id="cw-name" name="name" autocomplete="name" maxlength="120" required>
      <label for="cw-phone">Телефон</label><input id="cw-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" maxlength="32" required>
      <label for="cw-object">Коротко про об’єкт</label><textarea id="cw-object" name="object" rows="3" maxlength="2000" required></textarea>
      <div class="cw-honey" aria-hidden="true"><input name="website" tabindex="-1" autocomplete="off"></div>
      <p>Надсилаючи заявку, ви погоджуєтеся на обробку даних за <a href="/privacy-policy.html">Політикою конфіденційності</a>.</p>
      <button class="cw-submit" type="submit">Надіслати заявку</button>
    </form>
    <p>Можна написати без форми. Фото надішліть у Telegram.</p><div class="cw-links" aria-label="Інші способи зв’язку"></div>
  </div>`;
  document.body.append(root); document.body.classList.add('cw-ready');
  const panel=root.querySelector('.cw-panel'), launch=root.querySelector('.cw-launch'), form=root.querySelector('form');
  const mobile=matchMedia('(max-width:700px)'); let savedScroll=0, topic='';
  function link(label,url,target){
    if(!url)return;
    try{const u=new URL(url);if(!['https:','tel:','viber:'].includes(u.protocol))return;}catch{return;}
    const a=document.createElement('a');a.textContent=label;a.href=url;
    if(url.startsWith('https:')){a.target='_blank';a.rel='noopener noreferrer';}target.append(a);
  }
  const links=root.querySelector('.cw-links');
  link('Telegram',c.consultantUrl || (c.telegram ? 'https://t.me/'+c.telegram : ''),links);
  link('Telegram-канал',c.telegramChannel ? 'https://t.me/'+c.telegramChannel : '',links);
  link('WhatsApp',c.whatsapp ? (/^https:/.test(c.whatsapp)?c.whatsapp:'https://wa.me/'+c.whatsapp.replace(/\D/g,'')) : '',links);
  link('Viber',c.viber,links);
  link('Зателефонувати',c.phone ? 'tel:'+c.phone : '',root.querySelector('.cw-quick'));
  const track=name=>{if(window.altcamAnalyticsAllowed?.())window.altcamAnalytics?.(name);};
  function close(){panel.hidden=true;launch.hidden=false;launch.setAttribute('aria-expanded','false');document.body.classList.remove('cw-open');if(mobile.matches)window.scrollTo(0,savedScroll);launch.focus({preventScroll:true});}
  launch.onclick=()=>{
    if(!panel.hidden){close();return;}savedScroll=scrollY;panel.hidden=false;launch.setAttribute('aria-expanded','true');document.body.classList.add('cw-open');launch.hidden=mobile.matches;
    if(mobile.matches)root.scrollIntoView({block:'start'});
    root.querySelector('.cw-close').focus({preventScroll:true});track('widget_open');
  };
  root.querySelector('.cw-close').onclick=close;
  mobile.addEventListener('change',()=>{launch.hidden=mobile.matches&&!panel.hidden;});
  document.addEventListener('pointerdown',e=>{if(!panel.hidden&&!root.contains(e.target))close();});
  panel.addEventListener('keydown',e=>{
    if(e.key==='Escape'){e.preventDefault();close();}
    if(e.key==='Tab'){
      const nodes=[...panel.querySelectorAll('a[href],button:not(:disabled),input:not([tabindex="-1"]),textarea')].filter(n=>n.getClientRects().length);
      const first=nodes[0],last=nodes.at(-1);
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
    }
  });
  for(const button of root.querySelectorAll('[data-topic]'))button.onclick=()=>{
    topic=button.dataset.topic;
    for(const b of root.querySelectorAll('[data-topic]'))b.setAttribute('aria-pressed',String(b===button));
    form.elements.object.placeholder=topic+' — тип об’єкта та ваші побажання';form.elements.name.focus();
  };
  form.onsubmit=async e=>{
    e.preventDefault();if(form.dataset.sent==='true'||!form.reportValidity())return;
    const lead=window.AltcamLead,button=form.querySelector('[type="submit"]');
    if(!lead){let note=form.querySelector('[role="alert"]');if(!note){note=document.createElement('p');note.setAttribute('role','alert');form.append(note);}note.textContent='Форма тимчасово недоступна. Скористайтеся Telegram або телефоном нижче.';return;}
    const message=[topic,form.elements.object.value].filter(Boolean).join('\n');
    const payload=lead.buildLeadPayload('chat_widget',{name:form.elements.name.value,phone:form.elements.phone.value,message,details:{object:form.elements.object.value,topic}},location);
    const result=await lead.submit(form,button,message,()=>lead.post('/site-lead',payload));
    if(result){form.dataset.sent='true';track('widget_submit');button.disabled=true;button.textContent='Заявку надіслано';}
  };
})();
