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
  const rows = items.map((item) => {
    const quantity = Math.max(1, Number(item.quantity) || 1);
    const price = Number(item.price) || 0;
    return `<tr><td>${html_(item.name)}</td><td>${quantity}</td><td>${money_(price)}</td><td>${money_(price * quantity)}</td></tr>`;
  }).join('');
  const style = '<style>body{font:14px Arial,sans-serif;color:#17171a;max-width:900px;margin:32px auto}h1{border-bottom:4px solid #ffcc00;padding-bottom:12px}table{width:100%;border-collapse:collapse;margin-top:20px}th,td{border:1px solid #ddd;padding:10px;text-align:left}th{background:#17171a;color:#ffcc00}.total{font-size:20px;font-weight:700;text-align:right;margin-top:18px}</style>';
  const details = `<p><b>Клієнт:</b> ${html_(customer.name)}</p><p><b>Телефон:</b> ${html_(customer.phone)}</p><p><b>Email:</b> ${html_(customer.email)}</p><p><b>Доставка:</b> ${html_(delivery.label || delivery.type)}; ${html_(delivery.city)}; ${html_(delivery.place)}</p>`;
  const table = `<table><thead><tr><th>Найменування</th><th>Кількість</th><th>Ціна</th><th>Сума</th></tr></thead><tbody>${rows}</tbody></table>`;
  const total = `<p class="total">Разом: ${money_(order.subtotal)} грн</p>`;
  upsertHtml_(folder, `Картка замовлення ${number}.html`, `<!doctype html><meta charset="utf-8">${style}<h1>Картка замовлення ${html_(number)}</h1>${details}${table}${total}`);
  upsertHtml_(folder, `Рахунок ${number}.html`, `<!doctype html><meta charset="utf-8">${style}<h1>Рахунок ${html_(number)}</h1><p>ALT-CAM Security UA</p>${details}${table}${total}<p>Остаточна сума та реквізити підтверджуються менеджером перед оплатою.</p>`);
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
