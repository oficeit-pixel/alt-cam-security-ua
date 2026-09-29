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
  async function post(path, payload) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 12000);
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
  function showResult(form, success, message) {
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
    if (!success) {
      const links = [];
      if (contacts.telegram) links.push(['Telegram', `https://t.me/${encodeURIComponent(contacts.telegram.replace(/^@/, ''))}?text=${encodeURIComponent(message)}`]);
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
    form.dataset.leadBusy = 'true';
    const label = button?.innerHTML;
    if (button) { button.disabled = true; button.textContent = 'Надсилаємо…'; }
    try {
      const result = await send();
      if (!result) throw new Error('lead_not_accepted');
      showResult(form, true, message);
      return result;
    } catch { showResult(form, false, message); return false; }
    finally {
      delete form.dataset.leadBusy;
      if (button) { button.disabled = false; button.innerHTML = label; }
    }
  }
  root.AltcamLead = {normalizePhone, buildLeadPayload, post, showResult, submit};
  if (typeof module !== 'undefined' && module.exports) module.exports = root.AltcamLead;
})(typeof window !== 'undefined' ? window : globalThis);
