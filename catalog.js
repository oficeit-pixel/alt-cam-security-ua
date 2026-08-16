const fallbackServices = [
  {id:'service-survey',title:'Обстеження та проєктування',description:'Визначаємо зони контролю, ризики, кабельні траси, живлення та обсяг архіву.',includes:['Консультація за фото або виїзд','Схема розміщення обладнання','Кошторис у 2–3 комплектаціях']},
  {id:'service-video',title:'Монтаж відеоспостереження',description:'Встановлюємо IP, HD-TVI та HDCVI системи для дому, офісу, магазину й виробництва.',includes:['Монтаж камер і реєстратора','Прокладання та маркування кабелю','Архів і перегляд зі смартфона','Тестування та інструктаж']},
  {id:'service-intercom',title:'Домофонія та контроль доступу',description:'Організовуємо контрольоване відкриття дверей, хвірток, воріт і службових зон.',includes:['Панель, монітор або контролер','Замок, доводчик, кнопка виходу','Мобільний доступ та сценарії','Перевірка безпечного відкривання']},
  {id:'service-ajax',title:'Система безпеки Ajax',description:'Захист від проникнення, пожежі та протікання з керуванням у застосунку.',includes:['Проєктування зон охорони','Монтаж Hub і датчиків','Налаштування користувачів','Тест тривог та інструктаж']},
  {id:'service-power',title:'Резервне живлення',description:'Розраховуємо автономність системи та підбираємо ДБЖ, інвертор і акумулятори.',includes:['Розрахунок навантаження','Підбір захисту та кабелів','Монтаж і безпечне підключення','Тест автономної роботи']},
  {id:'service-network',title:'Мережа та кабельна інфраструктура',description:'Готуємо надійну мережу для камер, домофонії, Wi‑Fi та віддаленого доступу.',includes:['Кабельні траси та комутація','PoE-комутатори й шафи','Маркування портів','Перевірка швидкості та стабільності']},
  {id:'service-setup',title:'Налаштування та віддалений доступ',description:'Підключаємо Hik-Connect, DMSS, Imou Life, Ajax та безпечний доступ користувачів.',includes:['Створення або перенесення облікового запису','Додавання пристроїв','Сповіщення та права доступу','Резервна інструкція для власника']},
  {id:'service-maintenance',title:'Обслуговування та ремонт',description:'Діагностуємо несправності, відновлюємо запис і модернізуємо наявні системи.',includes:['Аудит камер, дисків і живлення','Очищення та оновлення ПЗ','Заміна несправних вузлів','Звіт і план модернізації']},
  {id:'service-support',title:'Технічний супровід',description:'Допомагаємо після запуску: користувачі, архів, сповіщення, оновлення й розширення.',includes:['Дистанційна консультація','Контроль працездатності','Допомога з архівом','Планове обслуговування']}
];
const services = Array.isArray(window.ALTCAM_SERVICES) ? window.ALTCAM_SERVICES : fallbackServices;

const products = Array.isArray(window.ALTCAM_CATALOG) ? window.ALTCAM_CATALOG : [];
const API = 'https://alt-cam-manager-bot.onrender.com';
const sessionId = localStorage.getItem('altcam-session') || (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()));
localStorage.setItem('altcam-session', sessionId);
let publicPrices = {};
const revealedPrices = new Set();
let cart = JSON.parse(localStorage.getItem('altcam-cart') || '[]');
const grid = document.querySelector('#product-grid');
const search = document.querySelector('#catalog-search');
const category = document.querySelector('#category-filter');
const brand = document.querySelector('#brand-filter');
const sort = document.querySelector('#sort-filter');
const loadMore = document.querySelector('#load-more');
const PAGE_SIZE = 48;
let visibleCount = PAGE_SIZE;

const unique = key => [...new Set(products.map(x => x[key]).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'uk'));
unique('category').forEach(value => category.add(new Option(value,value)));
unique('brand').forEach(value => brand.add(new Option(value,value)));

function clean(value){return String(value||'').replace(/<[^>]+>|&\w+;/g,' ').replace(/\s+/g,' ').trim()}
function money(value){return new Intl.NumberFormat('uk-UA').format(value)+' ₴'}
function track(event,data={}){fetch(API+'/api/analytics',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event,session_id:sessionId,page:location.pathname,data}),keepalive:true}).catch(()=>{})}
function renderProducts(){
  const query=search.value.trim().toLowerCase();
  let list=products.filter(item=>(!category.value||item.category===category.value)&&(!brand.value||item.brand===brand.value)&&(!query||[item.id,item.name,item.model,item.brand,item.sku,item.subcategory].join(' ').toLowerCase().includes(query)));
  if(sort.value==='name') list.sort((a,b)=>a.name.localeCompare(b.name,'uk'));
  if(sort.value==='brand') list.sort((a,b)=>a.brand.localeCompare(b.brand,'uk'));
  document.querySelector('#result-count').textContent=`Знайдено: ${list.length}`;
  const visible=list.slice(0,visibleCount);
  grid.innerHTML=list.length?visible.map(item=>{const retail=publicPrices[item.id]||item.price;const revealed=revealedPrices.has(item.id);return `<article class="product-card"><div class="product-image"><span class="stock">Є в наявності</span><img src="${item.image}" alt="${clean(item.name)}" loading="lazy"></div><div class="product-copy"><small>${clean(item.category)} · ${clean(item.subcategory)}</small><h3>${clean(item.model||item.name)}</h3><p>${clean(item.description)}</p>${revealed?`<div class="revealed-price"><strong>${retail?money(retail):'Ціна підтверджується менеджером'}</strong><small>Роздрібна ціна за 1 шт. При замовленні монтажу, комплекту, кількох камер або аксесуарів ціна буде перерахована.</small></div>`:`<button class="price-button" data-reveal-price="${item.id}">Уточнити ціну</button>`}<div class="product-bottom"><span>Перевірений товар · гарантія та підбір ALT-CAM</span><button class="add-button" data-add="${item.id}">До кошика</button></div></div></article>`}).join(''):'<div class="no-results">За цими параметрами товарів не знайдено.</div>';
  loadMore.hidden=visible.length>=list.length;
}

function renderServices(){document.querySelector('#service-grid').innerHTML=services.map((s,i)=>`<article class="service-item"><span class="service-number">${String(i+1).padStart(2,'0')} · ${s.group||'Послуга'}</span><h3>${s.title}</h3>${s.tagline?`<b>${s.tagline}</b>`:''}<p>${s.description}</p><ul>${s.includes.map(x=>`<li>${x}</li>`).join('')}</ul>${s.priceFrom?`<strong>від ${money(s.priceFrom)} <small>${s.unit||''}</small></strong>`:''}${s.options?.length?`<details class="service-price-list"><summary>Детальний прайс</summary>${s.options.map(([name,price])=>`<div><span>${name}</span><b>${price}</b></div>`).join('')}</details>`:''}${s.note?`<p><small>${s.note}</small></p>`:''}<button data-service="${s.id}">Додати до заявки</button></article>`).join('')}
function saveCart(){localStorage.setItem('altcam-cart',JSON.stringify(cart));renderCart()}
function add(id,type='product'){if(!cart.some(x=>x.id===id))cart.push({id,type});saveCart();track('add_to_cart',{id,type})}
function renderCart(){
  const rows=cart.map(entry=>{const item=entry.type==='service'?services.find(x=>x.id===entry.id):products.find(x=>x.id===entry.id);return item?`<div class="cart-item"><div><b>${clean(item.model||item.title||item.name)}</b><br><small>${entry.type==='service'?'Послуга ALT-CAM':clean(item.brand)}</small></div><button class="cart-remove" data-remove="${entry.id}">Видалити</button></div>`:''}).join('');
  document.querySelector('#cart-items').innerHTML=rows||'<div class="cart-empty">Кошик порожній.<br>Додайте обладнання або послугу.</div>';
  document.querySelector('#cart-count').textContent=cart.length;
}
function openCart(){document.querySelector('#cart').classList.add('is-open');document.querySelector('#cart').setAttribute('aria-hidden','false')}
function closeCart(){document.querySelector('#cart').classList.remove('is-open');document.querySelector('#cart').setAttribute('aria-hidden','true')}

[search,category,brand,sort].forEach(el=>el.addEventListener(el===search?'input':'change',()=>{visibleCount=PAGE_SIZE;renderProducts()}));
document.querySelector('#filter-reset').addEventListener('click',()=>{search.value='';category.value='';brand.value='';sort.value='featured';visibleCount=PAGE_SIZE;renderProducts()});
document.querySelectorAll('[data-category]').forEach(button=>button.addEventListener('click',()=>{track('category_view',{category:button.dataset.category});if(button.dataset.category==='Послуги'){document.querySelector('#services').scrollIntoView()}else{category.value=button.dataset.category;visibleCount=PAGE_SIZE;renderProducts();document.querySelector('#products').scrollIntoView()}}));
loadMore.addEventListener('click',()=>{visibleCount+=PAGE_SIZE;renderProducts()});
grid.addEventListener('click',event=>{const priceButton=event.target.closest('[data-reveal-price]');if(priceButton){revealedPrices.add(priceButton.dataset.revealPrice);track('price_revealed',{id:priceButton.dataset.revealPrice});renderProducts();return}const button=event.target.closest('[data-add]');if(button){add(button.dataset.add);openCart()}});
document.querySelector('#service-grid').addEventListener('click',event=>{const button=event.target.closest('[data-service]');if(button){add(button.dataset.service,'service');openCart()}});
document.querySelector('#cart-items').addEventListener('click',event=>{const button=event.target.closest('[data-remove]');if(button){cart=cart.filter(x=>x.id!==button.dataset.remove);saveCart()}});
document.querySelector('#cart-open').addEventListener('click',openCart);document.querySelector('#cart-close').addEventListener('click',closeCart);document.querySelector('#cart-backdrop').addEventListener('click',closeCart);
document.querySelector('#cart-order').addEventListener('click',async()=>{if(!cart.length)return;const name=document.querySelector('#order-name').value.trim(),phone=document.querySelector('#order-phone').value.trim(),city=document.querySelector('#order-city').value.trim();if(!name||!phone){alert('Вкажіть ім’я та телефон для підтвердження замовлення.');return}const orderItems=cart.map(entry=>{const item=entry.type==='service'?services.find(x=>x.id===entry.id):products.find(x=>x.id===entry.id);return {id:entry.id,type:entry.type,name:item?.model||item?.title||item?.name,price:publicPrices[entry.id]||null}});track('order_started',{items:orderItems.length});let orderNumber='';try{const response=await fetch(API+'/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer:{name,phone,city},items:orderItems})});if(response.ok){const data=await response.json();orderNumber=data.order_number||'';track('order_sent',{order_number:orderNumber})}}catch{}const lines=orderItems.map((item,i)=>`${i+1}. ${item.name}`);const text=[`Вітаю! ${orderNumber?'Замовлення '+orderNumber+'. ':''}Хочу підтвердити наявність і роздрібну ціну:`,...lines,'',`Ім’я: ${name}`,`Телефон: ${phone}`,`Місто: ${city||'не вказано'}`].join('\n');window.open(`https://t.me/altcam_security_ua?text=${encodeURIComponent(text)}`,'_blank','noopener')});
async function loadPrices(){try{const response=await fetch(API+'/api/catalog/prices');if(response.ok)publicPrices=await response.json()}catch{}renderProducts()}
const requestedProduct=new URLSearchParams(location.search).get('product');
if(requestedProduct&&products.some(item=>item.id===requestedProduct)){search.value=requestedProduct;revealedPrices.add(requestedProduct)}
renderServices();renderProducts();renderCart();loadPrices();track('page_view');
