/* Prefilled cart links: /catalog.html?cart=viatec-123:2,yugtorg-45:1 (built by the ALT-CAM assistant / manager).
   Only ids and quantities travel in the URL; prices always come from the catalog and are re-checked by /api/orders. */
(function (root) {
  const ID = /^[A-Za-z0-9_-]{1,64}$/;
  function parse(search) {
    let raw = '';
    try { raw = new URLSearchParams(search || '').get('cart') || ''; } catch { return []; }
    const seen = new Map();
    for (const part of raw.split(',').slice(0, 30)) {
      const [id, qtyRaw] = part.trim().split(':');
      if (!id || !ID.test(id)) continue;
      const qty = Math.min(99, Math.max(1, parseInt(qtyRaw || '1', 10) || 1));
      seen.set(id, Math.min(99, (seen.get(id) || 0) + qty));
    }
    return [...seen].map(([id, qty]) => ({id, qty}));
  }
  function apply(cart, entries, findProduct) {
    let added = 0;
    for (const {id, qty} of entries) {
      const item = findProduct(id);
      if (!item) continue;
      const existing = cart.find(entry => entry.id === id && entry.type === 'product');
      if (existing) existing.quantity = qty; else cart.push({id, type: 'product', name: item.model || item.name || id, quantity: qty});
      added += 1;
    }
    return added;
  }
  root.AltcamCartLink = {parse, apply};
  if (typeof module !== 'undefined' && module.exports) module.exports = root.AltcamCartLink;
})(typeof window !== 'undefined' ? window : globalThis);
