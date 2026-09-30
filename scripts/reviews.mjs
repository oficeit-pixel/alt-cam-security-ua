const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function httpsUrl(value){try{const url=new URL(value);return url.protocol==='https:'&&!url.username&&!url.password?url.href:'';}catch{return '';}}
export function renderReviews(html,contacts,reviews=[]){
  const url=httpsUrl(contacts.gbpReviewUrl);
  if(!url)return html.replace('<!-- ALTCAM_VERIFIED_REVIEWS -->','');
  const verified=reviews.filter(r=>r.verified===true && r.name && r.locality && /^\d{4}-\d{2}-\d{2}$/.test(r.date||'') && r.text && httpsUrl(r.source));
  const cards=verified.length<3?'':`<div class="reviews-grid">${verified.map(r=>`<article class="review-card"><h3>${escape(r.name)}</h3><p>${escape(r.text)}</p><p>${escape(r.locality)} · <time datetime="${escape(r.date)}">${escape(r.date)}</time></p><a href="${escape(httpsUrl(r.source))}" target="_blank" rel="noopener noreferrer">Джерело відгуку</a></article>`).join('')}</div>`;
  return html.replace('<!-- ALTCAM_VERIFIED_REVIEWS -->',`<section class="section reviews-section" id="reviews"><div class="container"><h2>Відгуки клієнтів</h2><p>Якщо ми вже встановлювали вам камери — будемо вдячні за кілька слів про нашу роботу.</p>${cards}<a class="btn btn-primary" href="${escape(url)}" target="_blank" rel="noopener noreferrer">Залишити відгук у Google</a></div></section>`);
}
