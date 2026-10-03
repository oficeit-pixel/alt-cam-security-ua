const origin = 'https://alt-cam.net.ua';
export function serviceSchema(meta, body) {
  const url = `${origin}/${meta.slug}/`;
  // Use the actual rendered price table: schema cannot diverge from visible prices.
  const rows = [...body.matchAll(/<tr><td>(.*?)<\/td><td>(.*?)<\/td><\/tr>/g)];
  const intercom = meta.slug === 'videodomofon-vyshhorod';
  const selected = rows.filter(([,label]) => intercom
    ? /^(Монтаж аналогового відеодомофона|Аналоговий відеодомофон|Монтаж IP-домофона|Монтаж накладної IP-панелі|Монтаж IP-монітора)/.test(label)
    : new RegExp(`^Монтаж ${meta.slug.endsWith('pryvatnyi-budynok')?'вуличної':'(?:внутрішньої|вуличної)'} камери —`).test(label));
  const offers = selected.map(([,name,price]) => {
    const amount = Number(price.match(/[\d][\d\s\u00a0\u202f]*/)?.[0].replace(/\s/g,''));
    if (!Number.isFinite(amount) || amount <= 0) throw new Error('Invalid visible service price');
    return {'@type':'Offer',name,price:amount,priceCurrency:'UAH',url,seller:{'@id':origin+'/#business'}};
  });
  if (!offers.length) throw new Error('Service schema requires visible offers');
  return {'@context':'https://schema.org','@type':'Service','@id':url+'#service',name:meta.h1,
    description:meta.description,url,serviceType:meta.h1,provider:{'@id':origin+'/#business'},
    areaServed:meta.areaServed.map(name=>({'@type':/область|громада/.test(name)?'AdministrativeArea':'City',name})),
    offers:{'@type':'AggregateOffer',priceCurrency:'UAH',lowPrice:Math.min(...offers.map(o=>o.price)),
      highPrice:Math.max(...offers.map(o=>o.price)),offerCount:offers.length,
      description:'Окремі монтажні роботи за таблицею цін. Не вартість системи під ключ; обладнання та матеріали окремо.',offers}};
}
