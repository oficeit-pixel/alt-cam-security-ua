// Curated by product type, not supplier IDs. Never mutate the source catalog.
const battery = /LiFePO4|LiFePo₄/i;
const voltage12 = /12(?:[.,]8)?\s*(?:V|В)(?![а-яa-z])/i;
export function capacityWh(name) {
  const wh = name.match(/(\d+(?:[.,]\d+)?)\s*(к?Вт[·\s]?[гчh]|k?Wh)/i);
  if (wh) return Number(wh[1].replace(',', '.')) * (/^к|^k/i.test(wh[2]) ? 1000 : 1);
  const ah = name.match(/(\d+(?:[.,]\d+)?)\s*(?:Ah|А[·\s]?[гh]|Ач)/i);
  const v = name.match(/(\d+(?:[.,]\d+)?)\s*(?:V|В)(?![а-яa-z])/i);
  return ah && v ? Number(ah[1].replace(',', '.')) * Number(v[1].replace(',', '.')) : null;
}
export function classifyBackupPower(product) {
  const n = String(product.name || '');
  const kind = n + ' ' + String(product.category || '') + ' ' + (product.tags || []).toString();
  if (/генератор|дизель|бензинов/i.test(kind)) return {reason:'Генератор: не для цієї добірки'};
  if (/корпус|порожн|додаткова.*батарея|додатковий.*акумулятор|стабілізатор|SNMP|карта.*управл|кабель|адаптер|плата|модуль/i.test(n)) return {reason:'Не самостійне резервне живлення'};
  if (/інвертор|инвертор/i.test(n)) {
    if (/автомоб|прикур|car\b|12\s*\/\s*220|approximated|модифікован|апроксим/i.test(n)) return {reason:'Автомобільний або несинусоїдальний інвертор'};
    if (/чист.{0,12}синус|правильн.{0,12}синус|pure.{0,8}sine/i.test(n)) return {group:'sine',rank:3};
    return {reason:'Форма синусоїди не підтверджена в назві'};
  }
  if (/ДБЖ|UPS|безперебійн|бесперебойн/i.test(n)) {
    if (voltage12.test(n) && /роутер|маршрутизатор|mini|міні|miniature/i.test(n)) return {group:'mini',rank:0};
    return {group:'ups',rank:voltage12.test(n)?1:2};
  }
  if (battery.test(n) && /акумулятор|батарея/i.test(n)) {
    const wh=capacityWh(n);
    return wh !== null && wh <= 3000 && wh > 0
      ? {group:'battery',rank:4}
      : {reason:'Ємність АКБ понад 3 кВт·год або не підтверджена'};
  }
  return {reason:'Інший тип обладнання'};
}
export function backupPowerName(product) {
  const name=String(product.name || '');
  if (!/BRAZZERS/i.test(name)) return name
    .replace(/Аккумуляторная батарея/gi,'Акумуляторна батарея')
    .replace(/\boutputs?\s*:/gi,'Виходи:')
    .replace(/\bWhite\b/g,'білий').replace(/\bBlack\b/g,'чорний')
    .replace(/\bBOX\b/g,'упаковка').replace(/\bcycles\b/g,'циклів')
    .replace(/\bkg\b/g,'кг').replace(/385 грам, 385 грам/g,'385 г');
  const type=/ДБЖ|UPS/i.test(name)?'ДБЖ':'Інвертор';
  const rating=name.match(/(\d+)\s*VA/i)?.[1];
  const watts=name.match(/(\d+)\s*(?:W|Вт)/i)?.[1];
  const volts=name.match(/(\d+(?:[.,]\d+)?)\s*(?:V|В)(?![а-яa-z])/i)?.[1];
  return [type,rating?rating+' ВА':watts?watts+' Вт':'',volts?volts+' В':''].filter(Boolean).join(' ');
}
export function selectBackupPower(products, limit=12) {
  const eligible=products.map((product,index)=>({product,index,...classifyBackupPower(product)}))
    .filter(p=>p.group).sort((a,b)=>a.rank-b.rank || Number(b.product.available===true)-Number(a.product.available===true) || a.index-b.index);
  const groups=['mini','ups','sine','battery'];
  // Reserve one place per available product type, then fill in relevance order.
  const chosen=groups.map(group=>eligible.find(p=>p.group===group)).filter(Boolean).slice(0,limit);
  for(const item of eligible) if(chosen.length<limit && !chosen.includes(item)) chosen.push(item);
  chosen.sort((a,b)=>a.rank-b.rank || a.index-b.index);
  return {items:chosen.map(p=>p.product),missing:groups.filter(g=>!eligible.some(p=>p.group===g))};
}
