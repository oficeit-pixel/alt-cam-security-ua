const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.handlers = {}; this.dataset = {}; this.nodes = {}; this.fields = {}; this.elements = {namedItem: n => this.fields[n]}; }
  set innerHTML(value) {
    this.html = value;
    for (const m of value.matchAll(/name="([^"]+)"/g)) this.fields[m[1]] = {value: ''};
  }
  append(...nodes) { this.children.push(...nodes); }
  querySelector(selector) {
    if (selector === '.aic-lead') return this.children.find(n => n.className === 'aic-lead');
    if (!this.nodes[selector]) { this.nodes[selector] = new Element(selector); if (selector === '.aic-form') this.nodes[selector].fields.q = new Element('textarea'); }
    return this.nodes[selector];
  }
  setAttribute() {}
  addEventListener(event, fn) { this.handlers[event] = fn; }
  scrollIntoView() {}
  focus() {}
  remove() {}
}

async function widget(contacts, seen = false) {
  const doc = {head: new Element('head'), body: new Element('body'), readyState: 'complete', createElement: tag => new Element(tag)};
  let payload;
  const events = {}, timers = [];
  const root = {document: doc, scrollY: 0, addEventListener: (name, fn) => { events[name] = fn; },
    setTimeout: (fn, delay) => timers.push({fn, delay}),
    sessionStorage: {getItem: key => key === 'altcam-consultation-offer-seen' && seen ? '1' : '{"bad":true}', setItem() {}},
    fetch: async () => ({json: async () => ({enabled: true})}),
    AltcamLead: {buildLeadPayload: (type, fields) => (payload = {type, ...fields}), post: async () => ({ok: true}),
      submit: async (_box, _button, _message, send) => send()}};
  root.ALTCAM_CONTACTS = contacts;
  vm.runInNewContext(fs.readFileSync(require.resolve('../ai-chat.js'), 'utf8'), {window: root, setTimeout, clearTimeout, AbortController});
  await new Promise(resolve => setImmediate(resolve));
  return {root, events, timers, offer: doc.body.children.find(n => n.className === 'aic-offer'), fab: doc.body.children.find(n => n.className === 'aic-fab'), panel: doc.body.children.find(n => n.className === 'aic-panel'), payload: () => payload};
}

test('production chat opens the private Telegram consultant, not a group or web conversation', async () => {
  const config = {window: {}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../contacts.js'), 'utf8'), config);
  const w = await widget(config.window.ALTCAM_CONTACTS);
  assert.equal(w.fab.href, 'https://t.me/AltCamSecurityUaBot');
  assert.equal(w.panel, undefined);
  assert.equal(w.fab.hidden, true);
  assert.equal(w.offer.hidden, true);
  assert.equal(w.timers.length, 0);
  w.events.scroll();
  assert.equal(w.timers.length, 0);
  w.root.scrollY = 100;
  w.events.scroll(); w.events.scroll();
  assert.equal(w.timers.length, 1);
  assert.equal(w.timers[0].delay, 12000);
  w.timers[0].fn();
  assert.equal(w.offer.hidden, false);
  w.offer.children[2].handlers.click();
  assert.equal(w.offer.hidden, true);
  assert.equal(w.fab.hidden, false);
});

test('dismissed consultation does not prompt again in the same session', async () => {
  const w = await widget({consultantUrl: 'https://t.me/AltCamSecurityUaBot'}, true);
  assert.equal(w.fab.hidden, false);
  assert.equal(w.offer.hidden, true);
  assert.equal(w.events.scroll, undefined);
});

test('manager button creates one form and reads named controls, not form.name', async () => {
  const w = await widget();
  assert(w.panel, 'widget survives malformed session history');
  const button = w.panel.querySelector('.aic-manager');
  button.handlers.click(); button.handlers.click();
  const log = w.panel.querySelector('.aic-log');
  assert.equal(log.children.filter(n => n.className === 'aic-lead').length, 1);
  const form = log.querySelector('.aic-lead');
  form.name = 'HTMLFormElement name attribute';
  form.fields.name.value = 'Тест'; form.fields.phone.value = '+380630607088';
  await form.handlers.submit({preventDefault() {}});
  assert.equal(w.payload().name, 'Тест');
  assert.equal(w.payload().phone, '+380630607088');
  assert.equal(w.payload().type, 'ai_chat');
});
