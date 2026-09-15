const SHEET_NAME = 'Заявки';
const HEADERS = [
  'Дата',
  "Ім'я",
  'Телефон',
  'Місто',
  'Тип заявки',
  "Об'єкт",
  'Кількість камер',
  'Коментар',
  'Джерело',
  'Статус',
  'ID',
];

const STATUS_COLORS = {
  'Нова': '#f4cccc',
  'В роботі': '#f6b26b',
  'Виконана': '#6fa8dc',
};

function setupAltCamSheet() {
  const spreadsheet = getSpreadsheet_();
  const sheet = spreadsheet.getSheetByName(SHEET_NAME) || spreadsheet.insertSheet(SHEET_NAME);

  sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, HEADERS.length)
    .setBackground('#17171a')
    .setFontColor('#ffcc00')
    .setFontWeight('bold');

  sheet.setColumnWidths(1, HEADERS.length, 140);
  sheet.setColumnWidth(1, 165);
  sheet.setColumnWidth(8, 320);

  const statusRange = sheet.getRange(2, 10, Math.max(sheet.getMaxRows() - 1, 1), 1);
  const validation = SpreadsheetApp.newDataValidation()
    .requireValueInList(Object.keys(STATUS_COLORS), true)
    .setAllowInvalid(false)
    .build();
  statusRange.setDataValidation(validation);

  const rules = Object.entries(STATUS_COLORS).map(([status, color]) =>
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo(status)
      .setBackground(color)
      .setFontColor('#17171a')
      .setRanges([statusRange])
      .build()
  );
  sheet.setConditionalFormatRules(rules);
  return `Лист «${SHEET_NAME}» налаштовано`;
}

function doPost(e) {
  const lock = LockService.getScriptLock();

  try {
    lock.waitLock(10000);
    const data = parsePayload_(e);

    if (data.kind === 'email') {
      return sendEmail_(data);
    }
    if (data.kind === 'drive_folder') {
      return createDriveFolder_(data);
    }

    const sheet = getRequestSheet_();
    const id = Utilities.getUuid().substring(0, 8).toUpperCase();

    sheet.appendRow([
      new Date(),
      safeCell_(data.name),
      safeCell_(data.phone),
      safeCell_(data.city),
      safeCell_(data.type || 'Заявка'),
      safeCell_(data.object),
      safeCell_(data.cameras),
      safeCell_(data.comment),
      safeCell_(data.source || 'Сайт'),
      'Нова',
      id,
    ]);

    return jsonResponse_({ status: 'success', id });
  } catch (error) {
    return jsonResponse_({ status: 'error', message: String(error) });
  } finally {
    lock.releaseLock();
  }
}

function createDriveFolder_(data) {
  const expected = PropertiesService.getScriptProperties().getProperty('ALT_CAM_MAIL_RELAY_SECRET');
  if (!expected || !data.secret || !secureEquals_(String(data.secret), expected)) {
    return jsonResponse_({ status: 'error', message: 'unauthorized' });
  }
  const rootId = String(data.root_folder_id || '').trim();
  const path = Array.isArray(data.path) ? data.path.slice(0, 8) : [];
  if (!/^[A-Za-z0-9_-]{10,}$/.test(rootId) || !path.length) {
    return jsonResponse_({ status: 'error', message: 'invalid_drive_path' });
  }
  let folder = DriveApp.getFolderById(rootId);
  path.forEach((part) => {
    const name = String(part || '').replace(/[\\/:*?"<>|\u0000-\u001f]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 120);
    if (!name) throw new Error('invalid_drive_folder_name');
    const existing = folder.getFoldersByName(name);
    folder = existing.hasNext() ? existing.next() : folder.createFolder(name);
  });
  if (data.order && typeof data.order === 'object') {
    writeOrderFiles_(folder, data.order);
  }
  return jsonResponse_({ status: 'success', url: folder.getUrl() });
}

function writeOrderFiles_(folder, order) {
  const number = String(order.number || 'Замовлення').slice(0, 64);
  const customer = order.customer || {};
  const delivery = order.delivery || {};
  const items = Array.isArray(order.items) ? order.items.slice(0, 100) : [];
  const rows = items.map((item, index) => {
    const quantity = Math.max(1, Number(item.quantity) || 1);
    const price = Number(item.price) || 0;
    return `<tr><td class="num">${index + 1}</td><td>${html_(item.name)}</td><td class="num">${quantity}</td><td class="money">${money_(price)}</td><td class="money">${money_(price * quantity)}</td></tr>`;
  }).join('');
  const createdAt = new Date(order.created_at || Date.now());
  const createdDate = Utilities.formatDate(createdAt, 'Europe/Kyiv', 'dd.MM.yyyy');
  const createdDateTime = Utilities.formatDate(createdAt, 'Europe/Kyiv', 'dd.MM.yyyy HH:mm');
  const style = `<style>@page{size:A4;margin:8mm}*{box-sizing:border-box}body{font:11px Arial,sans-serif;color:#17171a;max-width:194mm;margin:0 auto;background:#fff}.sheet{min-height:281mm;display:flex;flex-direction:column}.brand{display:flex;align-items:center;justify-content:space-between;background:#17171a;color:#fff;border-bottom:5px solid #ffcc00;padding:8px 10px}.brand-id{display:flex;align-items:center;gap:10px}.brand img{width:46px;height:54px;object-fit:contain}.logo{font-size:23px;font-weight:900;letter-spacing:.8px}.logo b{display:block;color:#ffcc00;font-size:10px;letter-spacing:2.4px}.contact{text-align:right;font-size:9px;line-height:1.5;color:#eee}.doc-head{display:flex;justify-content:space-between;align-items:flex-end;margin:10px 0 3px}.doc-type{background:#ffcc00;padding:4px 8px;font-size:9px;font-weight:800;text-transform:uppercase}h1{font-size:18px;margin:0}h2{font-size:11px;margin:9px 0 4px;text-transform:uppercase;letter-spacing:.5px;border-left:4px solid #ffcc00;padding-left:6px}.meta{color:#555;font-size:9px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:3px 12px;margin-top:6px}.field{border-bottom:1px solid #d7d7d7;padding:3px 0;min-height:23px}.field b{display:block;font-size:8px;text-transform:uppercase;color:#666;margin-bottom:2px}.legal{border:1px solid #d7d7d7;background:#fafafa;padding:6px 8px;line-height:1.45}.legal b{color:#111}table{width:100%;border-collapse:collapse;margin-top:5px;table-layout:fixed}th,td{border:1px solid #d9d9d9;padding:4px 5px;vertical-align:middle;overflow-wrap:anywhere}th{background:#17171a;color:#ffcc00;font-size:8px;text-transform:uppercase}th:nth-child(1),td:nth-child(1){width:6%}th:nth-child(3),td:nth-child(3){width:10%}th:nth-child(4),td:nth-child(4),th:nth-child(5),td:nth-child(5){width:15%}.num{text-align:center}.money{text-align:right;white-space:nowrap}.total{font-size:16px;font-weight:800;text-align:right;margin:6px 0}.note{font-size:9px;line-height:1.4;margin:4px 0}.warning{border-left:4px solid #ffcc00;padding:5px 7px;background:#fff7cc}.workflow{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-top:5px}.workflow div{border:1px solid #ddd;padding:5px;min-height:34px}.workflow b{display:block;font-size:8px;color:#666;text-transform:uppercase}.footer{margin-top:auto;border-top:1px solid #d9d9d9;padding-top:5px;font-size:8px;color:#555;display:flex;justify-content:space-between}.sign{margin-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:30px}.sign div{border-top:1px solid #777;padding-top:3px;font-size:8px;color:#666}@media print{body{print-color-adjust:exact;-webkit-print-color-adjust:exact}.sheet{page-break-after:avoid}}</style>`;
  const header = '<header class="brand"><div class="brand-id"><img src="https://alt-cam.net.ua/assets/alt-cam-mark.png" alt="ALT-CAM"><div class="logo">ALT-CAM<b>SECURITY UA</b></div></div><div class="contact"><b>Продаж · монтаж · налаштування</b><br>alt-cam.net.ua · altcam.ua@gmail.com<br>Київ · Вишгород · Київська область</div></header>';
  const clientDetails = `<div class="field"><b>Замовник</b>${html_(customer.name || 'Не зазначено')}</div><div class="field"><b>Телефон</b>${html_(customer.phone || 'Не зазначено')}</div><div class="field"><b>Email / Telegram</b>${html_(customer.email || customer.telegram || 'Не зазначено')}</div><div class="field"><b>Спосіб і адреса доставки</b>${html_(delivery.label || delivery.type || 'Не зазначено')}</div>`;
  const table = `<table><thead><tr><th>№</th><th>Товар або послуга</th><th>К-сть</th><th>Ціна, грн</th><th>Сума, грн</th></tr></thead><tbody>${rows}</tbody></table>`;
  const total = `<p class="total">Разом: ${money_(order.subtotal)} грн</p>`;
  const prefix = '<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>ALT-CAM</title>';
  const suffix = '</div></body></html>';
  const card = `${prefix}${style}</head><body><div class="sheet">${header}<div class="doc-head"><h1>Картка замовлення № ${html_(number)}</h1><span class="doc-type">Внутрішній документ</span></div><div class="meta">Створено: ${createdDateTime} · Канал: інтернет-магазин ALT-CAM · Валюта: UAH</div><h2>Дані клієнта та доставка</h2><div class="grid">${clientDetails}</div><h2>Склад замовлення</h2>${table}${total}<h2>Коментар клієнта</h2><p class="note">${html_(delivery.comment || 'Не зазначено')}</p><h2>Обробка замовлення</h2><div class="workflow"><div><b>Статус</b>Нове</div><div><b>Менеджер</b>Не призначено</div><div><b>Постачальник / №</b>Заповнює менеджер</div><div><b>Перевізник / трек</b>Заповнює менеджер</div></div><p class="note warning"><b>Контроль перед відправленням:</b> перевірити модель, кількість, сумісність, наявність, закупівельну й продажну ціну, оплату, дані одержувача та комплектацію.</p><div class="sign"><div>Відповідальний менеджер / дата</div><div>Комплектацію перевірено / дата</div></div><footer class="footer"><span>ALT-CAM Security UA · alt-cam.net.ua</span><span>${html_(number)}</span></footer>${suffix}`;
  const invoice = `${prefix}${style}</head><body><div class="sheet">${header}<div class="doc-head"><h1>Рахунок на оплату № ${html_(number)}</h1><span class="doc-type">Проєкт</span></div><div class="meta">Дата: ${createdDate} · Валюта: UAH · Оплата лише після підтвердження менеджером</div><h2>Постачальник</h2><div class="legal"><b>ALT-CAM Security UA</b><br>Юридичне найменування / ПІБ ФОП: вказати перед виставленням рахунку<br>ЄДРПОУ / РНОКПП: вказати · IBAN: вказати · Банк: вказати · Податковий статус: вказати</div><h2>Покупець та доставка</h2><div class="grid">${clientDetails}</div><h2>Товари та послуги</h2>${table}${total}<p class="note warning"><b>Це проєкт, а не платіжний документ.</b> Не сплачуйте його до внесення юридичних і банківських реквізитів продавця та письмового підтвердження остаточної суми.</p><p class="note"><b>Умови замовлення:</b> менеджер підтверджує наявність, сумісність, строк відправлення, гарантію та вартість доставки. Доставка оплачується окремо, якщо інше не зазначено в підтвердженому рахунку. Підтвердження оплати — банківський документ; отримання товару — документ перевізника або продавця.</p><div class="sign"><div>Постачальник / підпис / дата</div><div>Покупець / підпис / дата</div></div><footer class="footer"><span>alt-cam.net.ua · altcam.ua@gmail.com</span><span>${html_(number)}</span></footer>${suffix}`;
  upsertHtml_(folder, `Картка замовлення ${number}.html`, card);
  upsertHtml_(folder, `Рахунок ${number}.html`, invoice);
}

function upsertHtml_(folder, name, content) {
  const files = folder.getFilesByName(name);
  while (files.hasNext()) files.next().setTrashed(true);
  folder.createFile(name, content, MimeType.HTML);
}

function html_(value) {
  return String(value == null ? '' : value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}

function money_(value) {
  return (Number(value) || 0).toFixed(2).replace('.', ',');
}

function sendEmail_(data) {
  const expected = PropertiesService.getScriptProperties().getProperty('ALT_CAM_MAIL_RELAY_SECRET');
  if (!expected || !data.secret || !secureEquals_(String(data.secret), expected)) {
    return jsonResponse_({ status: 'error', message: 'unauthorized' });
  }

  const recipient = String(data.recipient || '').trim().toLowerCase();
  const subject = String(data.subject || '').trim().slice(0, 180);
  const text = String(data.text || '').slice(0, 20000);
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(recipient) || !subject || !text) {
    return jsonResponse_({ status: 'error', message: 'invalid_email' });
  }

  MailApp.sendEmail({
    to: recipient,
    subject,
    body: text,
    name: 'ALT-CAM Security UA',
  });
  return jsonResponse_({ status: 'success' });
}

function secureEquals_(left, right) {
  if (left.length !== right.length) return false;
  let diff = 0;
  for (let i = 0; i < left.length; i += 1) {
    diff |= left.charCodeAt(i) ^ right.charCodeAt(i);
  }
  return diff === 0;
}

function doGet() {
  return jsonResponse_({ status: 'ok', service: 'ALT-CAM Sheets intake' });
}

function getRequestSheet_() {
  const spreadsheet = getSpreadsheet_();
  const sheet = spreadsheet.getSheetByName(SHEET_NAME);
  if (!sheet) {
    throw new Error(`Лист «${SHEET_NAME}» не знайдено. Запустіть setupAltCamSheet().`);
  }
  return sheet;
}

function getSpreadsheet_() {
  const active = SpreadsheetApp.getActiveSpreadsheet();
  if (active) return active;

  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('ALT_CAM_SHEET_ID');
  if (!spreadsheetId) {
    throw new Error('Не задано властивість скрипта ALT_CAM_SHEET_ID');
  }
  return SpreadsheetApp.openById(spreadsheetId);
}

function parsePayload_(e) {
  if (!e || !e.postData || !e.postData.contents) {
    throw new Error('Порожній запит');
  }
  const data = JSON.parse(e.postData.contents);
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error('Некоректний JSON');
  }
  return data;
}

function safeCell_(value) {
  const text = String(value == null ? '' : value).trim().slice(0, 5000);
  return /^[=+\-@]/.test(text) ? `'${text}` : text;
}

function jsonResponse_(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
