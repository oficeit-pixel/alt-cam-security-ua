import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(dir, '../..');
const queuePath = path.join(repo, 'meta-automation', 'august-priority-posts.json');
const dataCode = fs.readFileSync(path.join(dir, 'calendar-data.js'), 'utf8');
const context = { window: {} };
vm.runInNewContext(dataCode, context);

const topics = context.window.ALT_CAM_APPROVAL_CALENDAR;
const queue = JSON.parse(fs.readFileSync(queuePath, 'utf8'));
const prefix = 'approved-2026-08-21-sep30-';
queue.posts = queue.posts.filter((post) => !post.id.startsWith(prefix));

const rawBase = 'https://raw.githubusercontent.com/oficeit-pixel/alt-cam-security-ua/main/social-posts/content-plans/2026-08-21-to-2026-09-30-approval/media/';
const telegram = 'https://t.me/altcam_security_ua';

function scheduled(date, time) {
  return `${date}T${time}:00+03:00`;
}

function add(topic, platform, time, suffix, caption) {
  queue.posts.push({
    id: `${prefix}${topic.date}-${suffix}`,
    campaign: 'altcam-approved-aug-sep-2026',
    scheduled_at: scheduled(topic.date, time),
    status: 'ready',
    platforms: [platform],
    media_type: 'image',
    image_url: rawBase + encodeURIComponent(topic.image),
    captions: { [platform]: caption },
    caption
  });
}

for (const topic of topics) {
  const full = `${topic.caption}\n\n${topic.hashtags}`;
  add(topic, 'threads', '09:00', 'threads-question', `${topic.title}: що для вас найважливіше у такому рішенні?\n\n${topic.description}\n\nПоділіться досвідом у коментарях.`);
  add(topic, 'telegram', '11:00', 'telegram', `${topic.title}\n\n${topic.description}\n\nПідберемо сумісне рішення під конкретний об’єкт. Напишіть нам: ${telegram}\n\n${topic.hashtags}`);
  add(topic, 'facebook', '13:00', 'facebook', full);
  add(topic, 'instagram', '18:30', 'instagram', full);
  add(topic, 'threads', '19:30', 'threads-summary', `${topic.description}\n\nВисновок ALT-CAM: спочатку визначаємо задачу й умови об’єкта, потім обираємо обладнання. Консультація: ${telegram}`);
}

queue.posts.sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at) || a.id.localeCompare(b.id));
queue.notes = 'Active queue through 2026-09-30. Facebook is published by a separate workflow; Instagram, Threads and Telegram by the general workflow. TikTok, Stories and YouTube require separate ready vertical media or platform approval.';
queue.generated_at = new Date().toISOString();
fs.writeFileSync(queuePath, JSON.stringify(queue, null, 2) + '\n');

console.log(JSON.stringify({ added: topics.length * 5, total: queue.posts.length, first: queue.posts[0]?.scheduled_at, last: queue.posts.at(-1)?.scheduled_at }, null, 2));
