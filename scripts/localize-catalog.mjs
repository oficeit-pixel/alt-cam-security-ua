// Editorial replacements for recurring supplier-feed terms. Never touch IDs,
// URLs, prices, quantities or technical numeric values. Model corrections below
// require a reviewed source, matching old value and model present in supplier name.
import {readFileSync} from 'node:fs';
const verifiedModels=JSON.parse(readFileSync(new URL('../data/verified-product-models.json',import.meta.url),'utf8'));
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
    const correction=verifiedModels[product.id];
    if(correction&&String(product.model)===correction.expected_model&&String(product.name).includes(correction.model))result.model=correction.model;
    for (const field of ['name','description','category','subcategory']) result[field]=localizeText(result[field]);
    if(Array.isArray(result.features)) result.features=result.features.map(localizeText);
    return result;
  });
}
