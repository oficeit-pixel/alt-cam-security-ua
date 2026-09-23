import fs from 'node:fs/promises';
const file = 'social-posts/meta-automation/august-priority-posts.json';
const queue = JSON.parse(await fs.readFile(file, 'utf8'));
const state = JSON.parse(await fs.readFile('social-posts/meta-automation/august-priority-state.json', 'utf8'));
let date = new Date('2026-10-02T07:00:00Z');
let count = 0;
for (const post of queue.posts) {
  if (!['approved','ready'].includes(post.status)) continue;
  if ((post.platforms || []).every(platform => state.published?.[post.id]?.[platform])) continue;
  post.scheduled_at = date.toISOString();
  post.captions ||= {};
  for (const platform of post.platforms || []) {
    if (state.published?.[post.id]?.[platform]) continue;
    const link = `https://alt-cam.net.ua/catalog.html?utm_source=${encodeURIComponent(platform)}&utm_medium=social&utm_campaign=organic_3_week&utm_content=${encodeURIComponent(post.id)}`;
    let caption = post.captions[platform] || post.caption || '';
    caption = caption.replace(/https:\/\/alt-cam\.net\.ua(?:\/[^\s]*)?(?=\s|$)/g, link);
    if (!caption.includes('alt-cam.net.ua')) caption += `\n\n${link}`;
    post.captions[platform] = caption;
  }
  count++;
  do { date.setUTCDate(date.getUTCDate() + 1); } while (![1,3,5].includes(date.getUTCDay()));
}
const topics = [
  ['2026-09-25', 'Монтаж камер з виїздом у Києві та області', 'Починаємо не з кількості камер, а із зон огляду: вхід, двір, каса чи склад. Уточнюємо освітлення, місце для архіву та можливість перегляду зі смартфона. Надішліть тип об’єкта й населений пункт — погодимо склад системи та кошторис.', '/montazh-videosposterezhennia-kyiv/'],
  ['2026-09-28', 'Що потрібно для відеоспостереження без світла?', 'Резервне живлення потрібне не лише камерам: врахуйте реєстратор, комутатор і маршрутизатор. Автономність залежить від споживання та акумулятора. Допоможемо підібрати сумісне рішення під ваше обладнання.', '/rezervne-zhyvlennia/'],
  ['2026-09-30', 'Відеоспостереження та доступ у Вишгороді', 'Квартира, магазин або під’їзд — для кожного об’єкта потрібні свої ракурси й спосіб підключення. Підбираємо камери, відеодомофони та контроль доступу. Працюємо з виїздом; перелік робіт і вартість погоджуємо до монтажу.', '/videosposterezhennia-vyshhorod/'],
];
for (const [day, title, body, route] of topics) {
  const id = `organic-site-${day}`;
  if (queue.posts.some(post => post.id === id)) continue;
  const captions = {};
  for (const platform of ['facebook','instagram','threads','telegram']) {
    const link = `https://alt-cam.net.ua${route}?utm_source=${platform}&utm_medium=social&utm_campaign=organic_3_week&utm_content=${id}`;
    captions[platform] = `${title}\n\n${platform === 'threads' ? 'Підбір обладнання та монтаж з виїздом. Деталі на сайті:' : body}\n\n+380 63 060 70 88\n${link}`;
    if (platform === 'instagram') captions[platform] += '\nПосилання можна скопіювати у браузер або написати нам у Direct.';
  }
  queue.posts.unshift({id, campaign:'organic_3_week', scheduled_at:`${day}T07:00:00Z`, status:'approved', platforms:Object.keys(captions), media_type:'image', image_url:'https://alt-cam.net.ua/assets/alt-cam-mark.png', captions, caption:captions.facebook});
}
queue.posts.sort((a,b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));
queue.notes.push('2026-09-23: Three new organic campaign posts added; unpublished deliveries rescheduled to Monday/Wednesday/Friday 07:00 UTC with UTM links. Published platform results preserved.');
await fs.writeFile(file, JSON.stringify(queue, null, 2) + '\n');
console.log(`Rescheduled ${count} posts; publication state untouched.`);
