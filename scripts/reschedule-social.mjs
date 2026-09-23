import fs from 'node:fs/promises';
const file = 'social-posts/meta-automation/august-priority-posts.json';
const queue = JSON.parse(await fs.readFile(file, 'utf8'));
const state = JSON.parse(await fs.readFile('social-posts/meta-automation/august-priority-state.json', 'utf8'));
let date = new Date('2026-09-25T07:00:00Z');
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
queue.notes.push('2026-09-23: Unpublished deliveries rescheduled to Monday/Wednesday/Friday 07:00 UTC with UTM links. Published platform results preserved.');
await fs.writeFile(file, JSON.stringify(queue, null, 2) + '\n');
console.log(`Rescheduled ${count} posts; publication state untouched.`);
