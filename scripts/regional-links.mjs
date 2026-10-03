// Crawlable local-service links, not location-based redirects or geo blocking.
const links = [
  ['/montazh-videosposterezhennia-kyiv/', 'Монтаж відеоспостереження — Київ'],
  ['/videosposterezhennia-vyshhorod/', 'Відеоспостереження — Вишгород'],
  ['/vstanovlennia-kamer-vyshhorod/', 'Встановлення камер у Вишгороді'],
  ['/videodomofon-vyshhorod/', 'Відеодомофони у Вишгороді'],
  ['/videosposterezhennia-pidyizd-osbb/', 'Відеоспостереження для ОСББ'],
  ['/videosposterezhennia-pryvatnyi-budynok/', 'Камери для будинку в Київській області'],
];
export function regionalLinks(html) {
  if (html.includes('id="regional-services"')) return html;
  // Leave an existing complete local-service navigation intact.
  if (links.every(([url]) => html.includes(`href="${url}"`))) return html;
  const block = `<aside id="regional-services" aria-label="Монтаж з виїздом"><h2>Монтаж з виїздом: Київ, Вишгород і область</h2><p>Підбір обладнання та монтаж за погодженим кошторисом. Доставка обладнання — по Україні.</p><nav aria-label="Послуги у вашому місті"><ul>${links.map(([url,label]) => `<li><a href="${url}">${label}</a></li>`).join('')}</ul></nav></aside>`;
  if (!html.includes('href="/regional-links.css"')) html = html.replace('</head>', '<link rel="stylesheet" href="/regional-links.css"></head>');
  return html.replace('</main>', block + '</main>');
}
