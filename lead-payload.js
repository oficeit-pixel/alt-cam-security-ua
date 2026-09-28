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
  root.AltcamLead = {normalizePhone, buildLeadPayload};
  if (typeof module !== 'undefined' && module.exports) module.exports = root.AltcamLead;
})(typeof window !== 'undefined' ? window : globalThis);
