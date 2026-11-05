/* ALT-CAM: чат-консультант на сайті. Той самий консультант, що відповідає в Telegram-боті.
   Віджет показується лише коли бекенд повідомляє enabled=true (/api/ai/status). */
(function (root) {
  'use strict';
  const doc = root.document;
  if (!doc || root.__altcamAiChat) return;
  root.__altcamAiChat = true;
  const API = (root.ALTCAM_CONTACTS?.apiBase || 'https://alt-cam-crm-api.onrender.com').replace(/\/$/, '');
  const STORE = 'altcam-ai-chat-v1';
  const SAFE_LINK = /^https:\/\/(?:(?:www\.)?alt-cam\.net\.ua|oficeit-pixel\.github\.io|t\.me)\/[^\s<>"']*$/;
  let history = [];
  try { history = JSON.parse(root.sessionStorage.getItem(STORE) || '[]').slice(-12); } catch { history = []; }
  const save = () => { try { root.sessionStorage.setItem(STORE, JSON.stringify(history.slice(-12))); } catch { /* приватний режим */ } };
  const track = (event, data) => root.altcamAnalytics?.(event, data || {});

  function css() {
    const style = doc.createElement('style');
    style.textContent = `.aic-fab{position:fixed;z-index:85;left:22px;bottom:22px;display:flex;align-items:center;gap:8px;padding:12px 16px;border:0;border-radius:999px;background:#ffcc00;color:#121212;font:800 14px/1 Inter,Arial,sans-serif;box-shadow:0 12px 30px rgba(0,0,0,.28);cursor:pointer}
.aic-panel{position:fixed;z-index:1100;left:22px;bottom:84px;display:flex;flex-direction:column;width:min(380px,calc(100vw - 24px));height:min(560px,calc(100vh - 120px));border-radius:16px;background:#fff;color:#161619;box-shadow:0 25px 70px rgba(0,0,0,.35);font:14px/1.45 Inter,Arial,sans-serif;overflow:hidden}
.aic-panel[hidden]{display:none}.aic-head{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;background:#161619;color:#fff}.aic-head b{color:#ffcc00}.aic-head button{border:0;background:none;color:#fff;font-size:24px;cursor:pointer}
.aic-log{flex:1;overflow:auto;padding:12px;background:#f5f5f7}.aic-msg{max-width:88%;margin:0 0 8px;padding:9px 11px;border-radius:12px;white-space:pre-wrap;overflow-wrap:anywhere}.aic-msg a{color:#6e5900;font-weight:700}
.aic-user{margin-left:auto;background:#ffcc00}.aic-bot{background:#fff;border:1px solid #e2e2e6}.aic-form{display:flex;gap:6px;padding:10px;border-top:1px solid #e2e2e6}.aic-form textarea{flex:1;min-height:42px;max-height:110px;padding:9px;border:1px solid #d5d5da;border-radius:10px;font:inherit;resize:none}
.aic-form button,.aic-lead button{border:0;border-radius:10px;padding:0 14px;background:#161619;color:#ffcc00;font-weight:900;cursor:pointer}.aic-lead{display:grid;gap:6px;margin:6px 0 10px;padding:10px;border:1px dashed #c9b34d;border-radius:12px;background:#fffbe6}.aic-lead input{min-height:40px;padding:8px;border:1px solid #d5d5da;border-radius:8px;font:inherit}.aic-lead button{min-height:40px}
.aic-note{padding:0 12px 8px;color:#73737b;font-size:11px;background:#fff}
@media(max-width:760px){.aic-fab{left:12px;bottom:68px;padding:11px 14px}.aic-panel{left:12px;bottom:124px;height:min(520px,calc(100vh - 150px))}}`;
    doc.head.append(style);
  }

  function linkify(node, text) {
    const parts = String(text).split(/(https:\/\/[^\s<>"']+)/g);
    for (const part of parts) {
      const clean = part.replace(/[).,;!?]+$/, '');
      if (SAFE_LINK.test(clean)) {
        const a = doc.createElement('a');
        a.href = clean; a.textContent = clean.includes('?cart=') ? 'Відкрити кошик із підбором' : clean;
        a.target = '_blank'; a.rel = 'noopener noreferrer';
        node.append(a, part.slice(clean.length));
      } else node.append(part);
    }
  }

  function build() {
    css();
    const fab = doc.createElement('button');
    fab.type = 'button'; fab.className = 'aic-fab'; fab.setAttribute('aria-expanded', 'false');
    fab.textContent = '💬 Підібрати обладнання';
    const panel = doc.createElement('section');
    panel.className = 'aic-panel'; panel.hidden = true; panel.setAttribute('aria-label', 'Консультант ALT-CAM');
    panel.innerHTML = '<div class="aic-head"><span><b>ALT-CAM</b> · консультант</span><button type="button" aria-label="Закрити">×</button></div>' +
      '<div class="aic-log" role="log" aria-live="polite"></div>' +
      '<p class="aic-note">Ціни — з каталогу сайту; наявність і остаточну суму підтверджує менеджер.</p>' +
      '<form class="aic-form"><textarea name="q" maxlength="1500" required placeholder="Напишіть, що потрібно захистити…" aria-label="Ваше запитання"></textarea><button>➤</button></form>';
    doc.body.append(fab, panel);
    const log = panel.querySelector('.aic-log'), form = panel.querySelector('.aic-form'), input = form.q;

    function bubble(role, text) {
      const p = doc.createElement('p');
      p.className = 'aic-msg ' + (role === 'user' ? 'aic-user' : 'aic-bot');
      if (role === 'user') p.textContent = text; else linkify(p, text);
      log.append(p); log.scrollTop = log.scrollHeight; return p;
    }
    function leadForm(telegramLink) {
      const box = doc.createElement('form');
      box.className = 'aic-lead';
      box.innerHTML = '<b>Передати питання менеджеру</b><input name="name" placeholder="Ваше ім’я" autocomplete="name">' +
        '<input name="phone" type="tel" required placeholder="Телефон +380…" autocomplete="tel"><button>Надіслати</button>';
      if (telegramLink && /^https:\/\/t\.me\/[A-Za-z0-9_]{5,32}\?start=[A-Za-z0-9_-]{1,64}$/.test(telegramLink)) {
        const a = doc.createElement('a'); a.href = telegramLink; a.target = '_blank'; a.rel = 'noopener noreferrer';
        a.textContent = 'або продовжити в Telegram'; box.append(a);
      }
      box.addEventListener('submit', async event => {
        event.preventDefault();
        const transcript = history.map(m => (m.role === 'user' ? 'Клієнт: ' : 'Консультант: ') + m.content).join('\n').slice(-3500);
        const lead = root.AltcamLead;
        if (!lead) return;
        const payload = lead.buildLeadPayload('ai_chat', {name: box.name.value, phone: box.phone.value,
          message: 'Запит із чату на сайті\n' + transcript});
        await lead.submit(box, box.querySelector('button'), payload.message, () => lead.post('/site-lead', payload));
        track('ai_chat_lead');
      });
      log.append(box); log.scrollTop = log.scrollHeight;
    }
    function open(state) {
      panel.hidden = !state; fab.setAttribute('aria-expanded', String(state));
      if (state) {
        if (!log.childElementCount) {
          if (history.length) history.forEach(m => bubble(m.role, m.content));
          else bubble('assistant', 'Вітаю! Підкажу з вибором камер, реєстратора, домофона чи Ajax. Скільки камер потрібно і де — вулиця чи приміщення?');
        }
        setTimeout(() => input.focus(), 50); track('ai_chat_open');
      }
    }
    fab.addEventListener('click', () => open(panel.hidden));
    panel.querySelector('.aic-head button').addEventListener('click', () => open(false));
    input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const text = input.value.trim();
      if (!text || form.dataset.busy) return;
      form.dataset.busy = '1'; input.value = '';
      history.push({role: 'user', content: text}); save(); bubble('user', text);
      const wait = bubble('assistant', '…');
      try {
        const response = await root.fetch(API + '/api/ai/chat', {method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({messages: history.slice(-12)})});
        const data = await response.json().catch(() => ({}));
        if (response.status === 429) throw new Error('rate');
        if (!response.ok || !data.ok || !data.reply) throw new Error('fail');
        wait.remove(); bubble('assistant', data.reply);
        history.push({role: 'assistant', content: data.reply}); save();
        if (data.handoff) leadForm(data.telegram_link);
        track('ai_chat_reply', {handoff: data.handoff || ''});
      } catch (error) {
        wait.remove();
        bubble('assistant', error.message === 'rate' ? 'Забагато запитань поспіль — зачекайте хвилину, будь ласка.'
          : 'Не вдалося отримати відповідь. Залиште телефон — менеджер зв’яжеться з вами.');
        if (error.message !== 'rate') leadForm('');
      } finally { delete form.dataset.busy; }
    });
  }

  async function init() {
    try {
      const response = await root.fetch(API + '/api/ai/status', {cache: 'no-store'});
      const data = await response.json();
      if (data && data.enabled === true) build();
    } catch { /* бекенд недоступний — віджет не показуємо, форми сайту працюють як завжди */ }
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', init); else init();
})(typeof window !== 'undefined' ? window : globalThis);
