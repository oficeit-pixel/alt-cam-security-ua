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
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
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
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getSheetByName(SHEET_NAME);
  if (!sheet) {
    throw new Error(`Лист «${SHEET_NAME}» не знайдено. Запустіть setupAltCamSheet().`);
  }
  return sheet;
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
