// Editorial replacements for recurring supplier-feed terms. Never touch IDs,
// URLs, model numbers, prices, quantities or technical numeric values.
const replacements = [
  ['Гнучка настройка', 'Гнучке налаштування'],
  ['Віддалена настройка', 'Віддалене налаштування'],
  ['додаткова настройка', 'додаткове налаштування'],
  ['точна (до 1 хвилини) настройка', 'точне (до 1 хвилини) налаштування'],
  ['Легкая настройка', 'Просте налаштування'],
  ['камера работает', 'камера працює'],
  ['настройка', 'налаштування'], ['оборудование', 'обладнання'],
  ['безопасность', 'безпека'], ['видеонаблюдение', 'відеоспостереження'],
  ['отправка', 'відправлення'], ['подзвонити', 'зателефонувати'],
  ['узнать', 'дізнатися'], ['заказать', 'замовити'], ['подробнее', 'докладніше'],
  ['скидка', 'знижка'], ['бесплатно', 'безкоштовно'], ['клиент', 'клієнт'], ['звонок', 'дзвінок'],
];
function escaped(text) { return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
export function localizeText(value) {
  if (typeof value !== 'string') return value;
  return replacements.reduce((text,[from,to]) => text.replace(
    new RegExp(`(?<![\\p{L}])${escaped(from)}(?![\\p{L}])`, 'giu'),
    found => found[0]===found[0].toUpperCase() ? to[0].toUpperCase()+to.slice(1) : to
  ),value);
}
export function localizeCatalog(products) {
  return products.map(product => {
    const result={...product};
    for (const field of ['name','description','category','subcategory']) result[field]=localizeText(result[field]);
    if(Array.isArray(result.features)) result.features=result.features.map(localizeText);
    return result;
  });
}
