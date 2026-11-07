const test = require('node:test');
const assert = require('node:assert/strict');
const {parse, apply} = require('../cart-link.js');

test('Telegram launch proof stays in memory and is stripped from the visible URL', () => {
  const vm = require('node:vm'), fs = require('node:fs');
  let replaced;
  const window = {location: {hash:'#tgWebAppData=signed%26payload', pathname:'/catalog.html',search:'?consultation=13'},
    history:{replaceState: (_, __, url) => {replaced = url;}}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../cart-link.js'),'utf8'), {window, URLSearchParams});
  assert.equal(replaced, '/catalog.html?consultation=13');
  assert.equal(window.AltcamCartLink.checkoutContext().inquiry, '13');
  assert.equal(window.AltcamCartLink.checkoutContext().init, 'signed&payload');
});

test('parses ids and quantities from ?cart=', () => {
  assert.deepEqual(parse('?cart=viatec-1:2,yugtorg-5'), [{id: 'viatec-1', qty: 2}, {id: 'yugtorg-5', qty: 1}]);
});
test('rejects junk, clamps quantities, merges duplicates', () => {
  assert.deepEqual(parse('?cart=<script>:1,viatec-1:500,viatec-1:abc,,:3'), [{id: 'viatec-1', qty: 99}]);
  assert.deepEqual(parse('?product=x'), []);
  assert.deepEqual(parse(''), []);
});
test('applies only known products and keeps the existing cart', () => {
  const cart = [{id: 'a', type: 'product', quantity: 1}];
  const known = {a: {model: 'A'}, b: {name: 'B'}};
  const added = apply(cart, [{id: 'a', qty: 3}, {id: 'b', qty: 2}, {id: 'zzz', qty: 1}], id => known[id]);
  assert.equal(added, 2);
  assert.deepEqual(cart, [{id: 'a', type: 'product', quantity: 3}, {id: 'b', type: 'product', name: 'B', quantity: 2}]);
});
