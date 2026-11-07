const entities={amp:'&',lt:'<',gt:'>',quot:'"',apos:'’',nbsp:' ',deg:'°',times:'×',ndash:'–',mdash:'—',laquo:'«',raquo:'»',bull:' ',micro:'µ',sup2:'²',sup3:'³',rsquo:'’',lsquo:'’',hellip:'…'};
export function cleanProductText(value){
 let s=String(value??'');
 for(let i=0;i<3;i++)s=s.replace(/&(#x[\da-f]+|#\d+|[a-z][a-z\d]+);/gi,(all,key)=>{
  if(key[0]!=='#')return entities[key.toLowerCase()]??all;
  const n=key[1].toLowerCase()==='x'?parseInt(key.slice(2),16):Number(key.slice(1));
  return n>0&&n<=0x10ffff?String.fromCodePoint(n):'';
 });
 return s.replace(/<[^>]*>/g,' ').replace(/[●•]/g,'; ').replace(/\s+/g,' ').replace(/^[;\s]+|[;\s]+$/g,'').trim();
}
const shorten=(s,n)=>s.length<=n?s:s.slice(0,n-1).trimEnd()+'…';
const generic=/^(?:IP\s*)?(?:відеокамера|камера|відеодомофон|домофон|реєстратор|відеореєстратор|акумулятор|ДБЖ|інвертор)$/i;
export function productCopy(item){
 const original=cleanProductText(item.name),brand=/^(інший виробник|unknown|no.?name)$/i.test(cleanProductText(item.brand))?'':cleanProductText(item.brand);
 const rawModel=cleanProductText(item.model);
 const model=generic.test(rawModel)||rawModel===brand||/^\d+$/.test(rawModel)?'':rawModel;
 const general=generic.test(original)||(!/\d/.test(original)&&original.length<65);
 const features=(item.features||[]).map(cleanProductText).filter(Boolean);
 const source=cleanProductText(item.description);
 const camera=/камера/i.test(original)&&!/домофон/i.test(original);
 const mp=(features.join(' ')+' '+original).match(/(\d+(?:[.,]\d+)?)\s*(?:МП|Мп|MP)(?![a-zа-я])/i)?.[1];
 const identity=model?(brand&&!model.toLowerCase().includes(brand.toLowerCase())?brand+' '+model:model):brand;
 let name=original;
 if(general){
  const specs=camera&&mp?mp+' Мп':features.find(f=>/роздільна|фокус|живлення|ємність/i.test(f));
  name=[identity,original+(specs?' '+specs:'')].filter(Boolean).join(' — ');
  if(!model&&item.sku)name+=' · '+cleanProductText(item.sku);
 }
 const reasons=[];
 if(!model)reasons.push('TODO_OWNER: потрібна ручна перевірка моделі; model порожнє, загальне або лише числовий код');
 if(!identity&&general)reasons.push('TODO_OWNER: недостатньо даних для унікальної назви');
 const suffix=' — ціна, монтаж у Києві | ALT-CAM';
 // Keep a full model where possible; long names use a shorter truthful suffix.
 const compact=model?identity:name;
 const title=name.length+suffix.length<=65?name+suffix:compact.length+suffix.length<=65?compact+suffix:shorten(compact,55)+' | ALT-CAM';
 const cta='Монтаж у Києві та Вишгороді, консультація безкоштовно.';
 const useful=[...new Set(features.filter(f=>/матриц|роздільн|фокус|живлення|захист|підсвіч|IP\d|PoE|Мп|МП|ємність|напруг/i.test(f)))];
 const summary=useful.length?useful.slice(0,3).join('; '):source||'Характеристики та сумісність уточнюйте перед замовленням';
 const description=shorten(name,65)+': '+shorten(summary,110)+'. '+cta;
 const images=[...new Set([item.image,...(Array.isArray(item.images)?item.images:[])])].filter(u=>{
  try{return new URL(u).protocol==='https:';}catch{return false;}
 });
 if(!images.length)reasons.push('TODO_OWNER: відсутнє фото товару');
 return {name,title,description,source,features,images,reasons};
}
