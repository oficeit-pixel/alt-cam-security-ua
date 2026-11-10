import fs from 'node:fs';
export const trust=JSON.parse(fs.readFileSync(new URL('../data/trust.json',import.meta.url),'utf8'));
const text=v=>typeof v==='string'&&!/TODO_OWNER|\[(?:ЗАПОВНИТИ|ПІДТВЕРДИТИ)/i.test(v)?v.trim():'';
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const url=v=>{try{const u=new URL(text(v));return u.protocol==='https:'&&!u.username&&!u.password?u.href:'';}catch{return '';}};
export function trustValues(t=trust){
 const hours=(Array.isArray(t.openingHours)?t.openingHours:[]).filter(v=>typeof v==='string'&&/^(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))? (?:[01]\d|2[0-3]):[0-5]\d-(?:[01]\d|2[0-3]):[0-5]\d$/.test(v));
 const names={Mo:'Пн',Tu:'Вт',We:'Ср',Th:'Чт',Fr:'Пт',Sa:'Сб',Su:'Нд'};
 const reviews=(Array.isArray(t.reviews)?t.reviews:[]).filter(r=>r.verified===true&&text(r.name)&&text(r.locality)&&text(r.text)&&/^\d{4}-\d{2}-\d{2}$/.test(r.date||'')&&Number.isFinite(Date.parse(r.date))&&new Date(r.date).toISOString().slice(0,10)===r.date&&url(r.source)&&/^(www\.)?(facebook\.com|google\.com|google\.com\.ua|maps\.google\.com|maps\.app\.goo\.gl|goo\.gl)$/.test(new URL(r.source).hostname)).filter((r,i,a)=>a.findIndex(x=>x.source===r.source)===i);
 return {hours,hoursLabel:hours.map(s=>s.replace(/Mo|Tu|We|Th|Fr|Sa|Su/g,d=>names[d])).join('; '),reviews,team:text(t.team),months:Number.isInteger(t.installationWarrantyMonths)&&t.installationWarrantyMonths>0?t.installationWarrantyMonths:null,legal:{name:text(t.legal?.name),code:text(t.legal?.code),address:text(t.legal?.address)},sameAs:(Array.isArray(t.sameAs)?t.sameAs:[]).map(url).filter(Boolean)};
}
export function trustSchema(t=trust,{reviewsVisible=false}={}){
 const v=trustValues(t),result={};
 if(v.hours.length)result.openingHours=v.hours;
 if(v.sameAs.length)result.sameAs=v.sameAs;
 if(v.legal.name&&v.legal.code&&v.legal.address)result.legalName=v.legal.name;
 // Opt-in only: own-business reviews are not eligible for Google review stars.
 if(reviewsVisible&&t.reviewSchemaEnabled===true&&v.reviews.length){
  result.review=v.reviews.map(r=>({'@type':'Review',author:{'@type':'Person',name:r.name},reviewBody:r.text,datePublished:r.date,url:r.source,...(typeof r.rating==='number'&&r.rating>=1&&r.rating<=5?{reviewRating:{'@type':'Rating',ratingValue:r.rating,bestRating:5,worstRating:1}}:{})}));
  if(result.review.every(r=>r.reviewRating))result.aggregateRating={'@type':'AggregateRating',ratingValue:Number((v.reviews.reduce((s,r)=>s+r.rating,0)/v.reviews.length).toFixed(2)),reviewCount:v.reviews.length,bestRating:5,worstRating:1};
 }
 return result;
}
export function renderTrust(html,t=trust){
 const v=trustValues(t),cards=v.reviews.map(r=>`<article class="review-card"><h3>${esc(r.name)}</h3><p>${esc(r.text)}</p><p>${esc(r.locality)} · <time datetime="${esc(r.date)}">${esc(r.date)}</time></p>${typeof r.rating==='number'&&r.rating>=1&&r.rating<=5?`<p>Оцінка: ${r.rating} / 5</p>`:''}<a href="${esc(url(r.source))}" rel="noopener noreferrer" target="_blank">Джерело відгуку</a></article>`).join('');
 const info=[v.hoursLabel?`<p>Графік роботи: ${esc(v.hoursLabel)}</p>`:'',v.months?`<p>Гарантія на монтажні роботи: ${v.months} міс.</p>`:'',v.team?`<h3>Монтажна команда</h3><p>${esc(v.team)}</p>`:''].join('');
 const block=cards||info?`<section class="section" id="trust"><div class="container"><h2>Відгуки та гарантії</h2><div class="reviews-grid">${cards}</div>${info}</div></section>`:'';
 html=html.replace('<!-- ALTCAM_VERIFIED_REVIEWS -->',block);
 if(v.hoursLabel)html=html.replace('Відповімо у робочий час',`Відповімо у робочий час · ${esc(v.hoursLabel)}`);
 if(v.legal.name&&v.legal.code&&v.legal.address)html=html.replace('</footer>',`<p class="container" data-trust-legal>${esc(v.legal.name)} · ${esc(v.legal.code)} · Юридична адреса: ${esc(v.legal.address)}</p></footer>`);
 html=html.replace('Працюємо з обладнанням провідних виробників','Підбираємо обладнання таких виробників');
 html=html.replace(/(<div class="brand-row">)([\s\S]*?)(<\/div>)/,(_,start,body,end)=>start+body.replace(/<span>([^<]+)<\/span>/g,(whole,brand)=>{
  const d=(Array.isArray(t.dealerships)?t.dealerships:[]).find(d=>d.confirmed===true&&text(d.brand).toLowerCase()===brand.toLowerCase()&&url(d.source)&&/^\/assets\/[\w/.-]+\.(png|webp|svg)$/.test(d.logo||'')&&!d.logo.includes('..'));
  return d?`<span><img src="${esc(d.logo)}" alt="${esc(brand)}" width="120" height="40" loading="lazy"></span>`:whole;
 })+end);
 return html;
}
