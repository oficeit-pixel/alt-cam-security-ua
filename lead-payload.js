(function (root) {
  'use strict';
  function normalizePhone(value) {
    let phone = String(value || '').trim().replace(/[\s()\-]/g, '');
    if (/^0\d{9}$/.test(phone)) phone = '+38' + phone;
    else if (/^380\d{9}$/.test(phone)) phone = '+' + phone;
    return phone;
  }
  function buildLeadPayload(type, {name, phone, email, details = {}, message} = {}, location = root.location) {
    const client = {name: String(name || '').trim(), phone: normalizePhone(phone), email: String(email || '').trim()};
    return {
      type, client, details,
      message: String(message || '').trim() || `Ім’я: ${client.name}\nТелефон: ${client.phone}`,
      page: location.pathname,
      source: location.origin + location.pathname,
    };
  }
  let warmed = false;
  function warmup() {
    if (warmed) return;
    warmed = true;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 12000);
    const base = (root.ALTCAM_CONTACTS?.apiBase || 'https://alt-cam-crm-api.onrender.com').replace(/\/$/, '');
    root.fetch(base + '/health', {mode:'cors', cache:'no-store', signal:controller.signal})
      .catch(() => {}).finally(() => clearTimeout(timer));
  }
  if (root.document) {
    for (const event of ['focusin', 'input']) root.document.addEventListener(event, e => {
      if (e.target.closest?.('form')) warmup();
    });
  }
  async function post(path, payload) {
    if (path === '/site-lead' || path === '/api/orders') {
      payload = apiPayload(payload, path === '/api/orders');
      path = '/api/lead';
    }
    const backup = root.ALTCAM_CONTACTS?.backupWebhook;
    if (backup) {
      try {
        const {consultation, ...safePayload} = payload;
        root.navigator.sendBeacon(backup, JSON.stringify({kind:'lead_backup', ...safePayload}));
      }
      catch { /* A backup attempt never implies successful primary delivery. */ }
    }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), path === '/api/lead' ? 65000 : 12000);
    try {
      const base = (root.ALTCAM_CONTACTS?.apiBase || 'https://alt-cam-crm-api.onrender.com').replace(/\/$/, '');
      const response = await root.fetch(base + path, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok || result.ok !== true) throw new Error('lead_not_accepted');
      return result;
    } finally { clearTimeout(timer); }
  }
  function attribution() {
    const key='altcam-first-touch';
    try {
      const stored=root.sessionStorage?.getItem(key);
      if(stored) return JSON.parse(stored);
    } catch {}
    const params=typeof URLSearchParams==='undefined'?{get:()=>null}:new URLSearchParams(root.location?.search || '');
    const data={};
    for(const key of ['utm_source','utm_medium','utm_campaign','utm_term','utm_content'])data[key]=(params.get(key)||'').slice(0,200);
    try { const ref=new URL(root.document?.referrer||''); data.referrer=ref.origin+ref.pathname; } catch {data.referrer='';}
    try {root.sessionStorage?.setItem(key,JSON.stringify(data));} catch {}
    return data;
  }
  function apiPayload(payload, cart=false) {
    const client=payload.client||payload.customer||payload;
    const details=payload.details||{};
    const source_form=cart?'cart':({contact_form:'hero',quote_confirmation:'calculator',catalog_consultation:'consultation',ai_chat:'consultation',quiz:'quiz'})[payload.type]||'consultation';
    const formId={hero:'lead-form',calculator:'quote-confirm-form',quiz:'security-quiz',cart:'checkout-form',consultation:'consult-form'}[source_form];
    const website=root.document?.getElementById?.(formId)?.querySelector?.('[name="website"]')?.value||'';
    return {name:client.name||'',phone:normalizePhone(client.phone),email:client.email||'',source_form,
      object:{...details,...(payload.diagnostics||{}),type:details.object||payload.object||''},
      calculation:payload.quote||details.quote||{},cart:payload.items||[],comment:payload.message||payload.comment||'',
      ...attribution(),page_url:payload.source||((root.location?.origin||'')+(root.location?.pathname||'')),
      website,delivery:payload.delivery,needs_installation:payload.needs_installation,consultation:payload.consultation};
  }
  function telegramContinueLink(result) {
    const url = result && typeof result.telegram_link === 'string' ? result.telegram_link : '';
    return /^https:\/\/t\.me\/[A-Za-z0-9_]{5,32}\?start=[A-Za-z0-9_-]{1,64}$/.test(url) ? url : '';
  }
  function showResult(form, success, message, result) {
    const doc = form.ownerDocument;
    let status = form.querySelector('[data-lead-result]');
    if (!status) {
      status = doc.createElement('div');
      status.dataset.leadResult = '';
      status.className = 'lead-result';
      status.tabIndex = -1;
      form.append(status);
    }
    status.replaceChildren();
    status.setAttribute('role', success ? 'status' : 'alert');
    const contacts = root.ALTCAM_CONTACTS || {};
    const text = doc.createElement('p');
    text.textContent = success
      ? `Дякуємо! Заявку отримано. Ми зв’яжемося з вами ${contacts.responseTime || 'найближчим часом'}.`
      : 'Не вдалося надіслати заявку автоматично. Напишіть нам — це займе хвилину:';
    status.append(text);
    const continueUrl = success ? telegramContinueLink(result) || contacts.consultantUrl : '';
    if (continueUrl) {
      const link = doc.createElement('a');
      link.textContent = 'Продовжити в Telegram — відповімо швидше';
      link.href = continueUrl; link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.className = 'lead-telegram-continue';
      status.append(link);
      root.altcamAnalytics?.('lead_telegram_link_shown');
    }
    if (!success) {
      root.altcamAnalytics?.('lead_fallback_shown');
      const links = [];
      if (contacts.consultantUrl) links.push(['Telegram', contacts.consultantUrl]);
      else if (contacts.telegram) links.push(['Telegram', `https://t.me/${encodeURIComponent(contacts.telegram.replace(/^@/, ''))}?text=${encodeURIComponent(message)}`]);
      if (contacts.whatsapp) links.push(['WhatsApp', `https://wa.me/${contacts.whatsapp.replace(/\D/g, '')}?text=${encodeURIComponent(message)}`]);
      if (contacts.viber) links.push(['Viber', `viber://chat?number=${encodeURIComponent(contacts.viber)}`]);
      if (contacts.phone) links.push(['Зателефонувати', `tel:${normalizePhone(contacts.phone)}`]);
      for (const [label, url] of links) {
        const link = doc.createElement('a');
        link.textContent = label; link.href = url;
        link.target = '_blank'; link.rel = 'noopener noreferrer';
        link.style.marginRight = '1rem'; status.append(link);
      }
      const copy = doc.createElement('button');
      copy.type = 'button'; copy.textContent = 'Скопіювати текст заявки';
      copy.addEventListener('click', async () => {
        try { await root.navigator.clipboard.writeText(message); copy.textContent = 'Скопійовано'; }
        catch {
          const field = doc.createElement('textarea'); field.value = message;
          field.readOnly = true; field.setAttribute('aria-label', 'Текст заявки для копіювання');
          status.append(field); field.focus(); field.select();
        }
      });
      status.append(copy);
    }
    status.focus();
  }
  async function submit(form, button, message, send) {
    if (form.dataset.leadBusy === 'true') return false;
    const phone = form.querySelector('[name="phone"], [name="quotePhone"], [name="quizContact"]');
    if (phone) {
      let error = form.querySelector('[data-phone-error]');
      if (!error) {
        error = form.ownerDocument.createElement('p'); error.dataset.phoneError = '';
        error.id = `${form.id}-phone-error`; error.setAttribute('role','alert');
        phone.after(error); phone.setAttribute('aria-describedby',error.id);
      }
      if (!/^\+380\d{9}$/.test(normalizePhone(phone.value))) {
        error.textContent = 'Перевірте телефон: наприклад, +380 63 060 70 88.';
        phone.setAttribute('aria-invalid','true'); phone.focus(); return false;
      }
      error.textContent = ''; phone.removeAttribute('aria-invalid');
    }
    form.dataset.leadBusy = 'true';
    const label = button?.innerHTML;
    if (button) { button.disabled = true; button.textContent = 'Надсилаємо…'; }
    try {
      const result = await send();
      if (!result) throw new Error('lead_not_accepted');
      showResult(form, true, message, result);
      return result;
    } catch { showResult(form, false, message); return false; }
    finally {
      delete form.dataset.leadBusy;
      if (button) { button.disabled = false; button.innerHTML = label; }
    }
  }
  attribution();
  function protectForms(){
    for(const form of root.document?.querySelectorAll?.('form')||[]){
      if(!form.querySelector('[name="website"]')){
        const field=root.document.createElement('input');
        field.name='website';field.type='text';field.tabIndex=-1;field.autocomplete='off';
        field.setAttribute('aria-hidden','true');field.style.cssText='position:absolute;left:-10000px;width:1px;height:1px';
        form.append(field);
      }
      if(!form.querySelector('a[href="/privacy-policy.html"]')){
        const note=root.document.createElement('p');
        note.innerHTML='Надсилаючи заявку, ви погоджуєтеся на обробку даних відповідно до <a href="/privacy-policy.html">Політики конфіденційності</a>.';
        form.append(note);
      }
    }
  }
  if(root.document?.readyState==='loading')root.document.addEventListener('DOMContentLoaded',protectForms);
  else protectForms();
  root.AltcamLead = {normalizePhone, buildLeadPayload, post, showResult, submit, warmup, telegramContinueLink, apiPayload, attribution};
  if (typeof module !== 'undefined' && module.exports) module.exports = root.AltcamLead;
})(typeof window !== 'undefined' ? window : globalThis);
