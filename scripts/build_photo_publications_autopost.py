from __future__ import annotations

import json
import re
import shutil
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(r"D:\фото публикации")
TEXT_FILE = SOURCE_DIR / "Тексты для соцсетей.txt"
PLAN_ID = "2026-09-14-photo-publications"
CAMPAIGN = "altcam-photo-publications-sep-2026"
PUBLIC_BASE = "https://oficeit-pixel.github.io/alt-cam-security-ua"
OUTPUT_DIR = ROOT / "social-posts" / "content-plans" / PLAN_ID
MEDIA_DIR = OUTPUT_DIR / "media"
CALENDAR_DIR = ROOT / "social-posts" / "calendar"
QUEUE_FILE = ROOT / "social-posts" / "meta-automation" / "august-priority-posts.json"


TEXT_TO_IMAGE = {
    1: "Dahua IP-2M-2OUT-Pro.png",
    2: "NeoLight NL-HPC 03.png",
    3: "Комплект NeoLight Kappa+ HD WF + Solo FHD + microSD 128 ГБ + Atis Lock SS.png",
    4: "MikroTik SXTsq Lite5 (RBSXTsq5nD).png",
    5: "IPCOM 6U 600×450.png",
    6: "MikroTik S-35LC20D S-3553LC20D.png",
    7: "ALISTAR mini 100BASE-FX 1SM WDM SC.png",
    8: "SEVEN LOCK SL-7708F.png",
    9: "Dahua APOLLO BP3EW-4G.png",
    10: "COVAX CV-PS-3200-24V.png",
    11: "Hikvision DS-3WF0EC-2NT.png",
    12: "Повербанки.png",
    13: "варіофокальні IP-камери Ajax HLVF.png",
    14: "MINI UPS.png",
    15: "Контроль доступу нового рівня.png",
    16: "Енергія під контролем.png",
    17: "Ударостійкі бокси з ABS-пластику IP65.png",
    18: "Потрібен стабільний Wi-Fi просто неба.png",
    19: "Автомат введення резерву (АВР).png",
    20: "Загоряння може початися за секунди..png",
    21: "Кабелі «Одескабель».png",
    22: "Електричний кабель «Одескабель» ШВВПн.png",
    23: "Одескабель ПВСм.png",
    24: "Оптична лінія.png",
    25: "Кабель — це основа.png",
    26: "Оптичні аксесуари.png",
    27: "Якісний монтаж.png",
    28: "Надійне з’єднання.png",
    29: "ALT-CAM Security UA.png",
    30: "Надійна мережа.png",
    31: "Відеодомофон під ключ.png",
    32: "Контроль доступу до двору під ключ.png",
    33: "Комплексний захист будинку з Ajax під ключ.png",
    34: "Відеоспостереження для квартири.png",
    35: "Відеоспостереження у ліфтах.png",
    36: "Відеоспостереження для СТО.png",
    37: "Відеоспостереження для малого бізнесу.png",
    38: "Контроль доступу та облік робочого часу на складі.png",
    39: "Бездротовий інтернет для віддалених об’єктів.png",
    40: "Кабельна інфраструктура для офісу.png",
    41: "Прокладання, зварювання та тестування оптичних ліній.png",
    42: "Резервне живлення для квартири.png",
    43: "Резервне живлення для офісів, магазинів і складів.png",
    44: "Сонячні панелі та резервне живлення.png",
    45: "ALT-CAM Security UA — комплексні рішення для безпеки та інженерних систем.png",
    46: "ALT-CAM Security UA — комплексні рішення для безпеки та інженерних систем Алиса.png",
    47: "ALT-CAM Security UA — обладнання для безпеки, мереж та резервного живлення.png",
}

EXTRA_IMAGES = [
    "ChatGPT Image 12 сент. 2026 г., 17_19_23 (2).png",
]

SLOTS = ["10:00", "17:30"]
START_DATE = datetime.fromisoformat("2026-09-14T00:00:00+03:00")
TOTAL_DAYS = 90


def split_blocks(text: str) -> list[str]:
    parts = re.split(r"\n\s*(?:[-=]{5,})\s*\n|\n\s*[-=]{5,}\s*", text)
    return [part.strip() for part in parts if part.strip()]


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    if ascii_text:
        return ascii_text[:90].strip("-")
    return "altcam-photo"


def clean_title(block: str, fallback: str) -> str:
    first = next((line.strip() for line in block.splitlines() if line.strip()), fallback)
    first = re.sub(r"^[^\wА-Яа-яІіЇїЄєҐґ0-9]+", "", first).strip()
    return first or fallback


def normalize_links(text: str) -> str:
    text = text.replace("🌐 alt-cam.net.ua", "🌐 https://alt-cam.net.ua")
    text = re.sub(r"(?<!https://)alt-cam\.net\.ua", "https://alt-cam.net.ua", text)
    if "https://t.me/alt_cam_bot" not in text:
        text = text.rstrip() + "\n\n🤖 https://t.me/alt_cam_bot"
    return text.strip()


def extract_hashtags(text: str) -> str:
    tags = re.findall(r"#[\wА-Яа-яІіЇїЄєҐґ]+", text, flags=re.UNICODE)
    if not tags:
        tags = [
            "#ALTCAM",
            "#ALTCAMSecurityUA",
            "#СистемиБезпеки",
            "#Київ",
            "#Вишгород",
        ]
    return " ".join(dict.fromkeys(tags))


def first_paragraphs(text: str, count: int = 3) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    body = [p for p in paragraphs if not p.startswith("#") and "https://alt-cam.net.ua" not in p]
    return body[:count]


def trim_text(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    boundary = max(cut.rfind("\n\n"), cut.rfind(". "), cut.rfind(" "))
    if boundary > limit * 0.55:
        cut = cut[:boundary]
    return cut.rstrip(" .,\n") + "…"


def platform_captions(full_text: str, title: str) -> dict[str, str]:
    full_text = normalize_links(full_text)
    hashtags = extract_hashtags(full_text)
    body = "\n\n".join(first_paragraphs(full_text, 3))
    cta = "📩 Напишіть нам у повідомлення або відкрийте Telegram-бот — підберемо рішення під ваш об’єкт.\n🤖 https://t.me/alt_cam_bot\n🌐 https://alt-cam.net.ua"
    short = f"{title}\n\n{body}\n\n{cta}\n\n{hashtags}"
    threads = f"{title}\n\n{body}\n\nПотрібна консультація? Напишіть ALT-CAM: https://t.me/alt_cam_bot"
    tiktok = f"{title}\n\n{body}\n\nПишіть ALT-CAM — підберемо рішення під ваш об’єкт.\nhttps://t.me/alt_cam_bot\n\n{hashtags}"
    telegram = full_text
    return {
        "facebook": full_text,
        "instagram": trim_text(short, 2100),
        "threads": trim_text(threads, 480),
        "telegram": telegram,
        "tiktok": trim_text(tiktok, 2100),
    }


def scheduled_at(day: int, slot_index: int) -> str:
    slot = SLOTS[slot_index]
    hour, minute = map(int, slot.split(":"))
    value = START_DATE + timedelta(days=day, hours=hour, minutes=minute)
    return value.isoformat()


def rotated_entry_index(slot_number: int, entry_count: int) -> int:
    # 17 is coprime with 48, so every cycle walks all base posts once.
    # The cycle shift prevents the same posts from landing on identical
    # weekday/time positions month after month.
    cycle = slot_number // entry_count
    return (slot_number * 17 + cycle * 7) % entry_count


def build_extra_block(name: str) -> str:
    title = "ALT-CAM Security UA — комплексні рішення під ваш об’єкт"
    return (
        f"🛡 {title}\n\n"
        "Безпека, стабільний зв’язок і резервне живлення мають працювати разом. "
        "ALT-CAM Security UA допомагає підібрати обладнання, змонтувати систему та налаштувати її під реальний сценарій об’єкта.\n\n"
        "Працюємо з відеоспостереженням, домофонією, контролем доступу, мережами, оптикою, резервним живленням і сонячними рішеннями.\n\n"
        "📩 Напишіть «ПРОЄКТ» у повідомлення — підготуємо консультацію та індивідуальну пропозицію.\n\n"
        "🌐 https://alt-cam.net.ua\n📍 Київ • Вишгород • Київська область\n\n"
        "#ALTCAM #ALTCAMSecurityUA #СистемиБезпеки #Відеоспостереження #КонтрольДоступу #РезервнеЖивлення #Київ #Вишгород"
    )


def main() -> None:
    blocks = split_blocks(TEXT_FILE.read_text(encoding="utf-8"))
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    for existing in MEDIA_DIR.glob("*"):
        if existing.is_file():
            existing.unlink()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CALENDAR_DIR.mkdir(parents=True, exist_ok=True)

    entries = []
    used_images: set[str] = set()
    for idx, block in enumerate(blocks, start=1):
        image_name = TEXT_TO_IMAGE.get(idx)
        if not image_name:
            continue
        image_path = SOURCE_DIR / image_name
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        used_images.add(image_name)
        title = clean_title(block, image_path.stem)
        entries.append((title, block, image_path))

    for image_name in EXTRA_IMAGES:
        image_path = SOURCE_DIR / image_name
        if image_path.exists() and image_name not in used_images:
            block = build_extra_block(image_name)
            entries.append((clean_title(block, image_path.stem), block, image_path))

    base_items = []
    report_rows = []
    for index, (title, block, image_path) in enumerate(entries):
        slug = f"{index + 1:02d}-{slugify(image_path.stem)}"
        dest = MEDIA_DIR / f"{slug}{image_path.suffix.lower()}"
        shutil.copy2(image_path, dest)
        rel_media = f"social-posts/content-plans/{PLAN_ID}/media/{dest.name}"
        image_url = f"{PUBLIC_BASE}/{rel_media}"
        captions = platform_captions(block, title)
        base_items.append(
            {
                "base_number": index + 1,
                "title": title,
                "captions": captions,
                "caption": captions["instagram"],
                "image_path": f"../content-plans/{PLAN_ID}/media/{dest.name}",
                "image_url": image_url,
                "source_image": str(image_path),
                "media": dest.name,
            }
        )

    posts = []
    total_slots = TOTAL_DAYS * len(SLOTS)
    for slot_number in range(total_slots):
        day = slot_number // len(SLOTS)
        slot_index = slot_number % len(SLOTS)
        base = base_items[rotated_entry_index(slot_number, len(base_items))]
        post = {
            "id": f"photo-pub-2026-09-{slot_number + 1:03d}",
            "campaign": CAMPAIGN,
            "scheduled_at": scheduled_at(day, slot_index),
            "status": "approved",
            "platforms": ["facebook", "instagram", "threads", "telegram", "tiktok"],
            "media_type": "image",
            "image_path": base["image_path"],
            "image_url": base["image_url"],
            "tiktok_photo_images": [base["image_url"]],
            "title": base["title"],
            "titles": {"tiktok": trim_text(base["title"], 90)},
            "caption": base["caption"],
            "captions": base["captions"],
            "source_image": base["source_image"],
            "base_post_number": base["base_number"],
            "repeat_round": (slot_number // len(base_items)) + 1,
        }
        posts.append(post)
        report_rows.append(
            {
                "id": post["id"],
                "scheduled_at": post["scheduled_at"],
                "title": base["title"],
                "source_image": Path(base["source_image"]).name,
                "media": base["media"],
                "base_post_number": base["base_number"],
                "repeat_round": post["repeat_round"],
            }
        )

    plan = {
        "plan_id": PLAN_ID,
        "campaign": CAMPAIGN,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_folder": str(SOURCE_DIR),
        "base_post_count": len(base_items),
        "post_count": len(posts),
        "platforms": ["facebook", "instagram", "threads", "telegram", "tiktok"],
        "notes": [
            "Source media and Ukrainian descriptions were imported from D:\\фото публикации.",
            "Captions are platform-adapted to reduce API failures caused by overlong text.",
            f"Autoposting is expanded to {TOTAL_DAYS} days with repeated posts and rotated order.",
            "YouTube is not included because the current publisher has no YouTube API workflow.",
        ],
        "posts": posts,
    }
    (OUTPUT_DIR / "publishing-posts.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "import-report.json").write_text(
        json.dumps({"rows": report_rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    ready_md = [
        "# ALT-CAM photo publications autopost",
        "",
        f"Base posts: {len(base_items)}",
        f"Scheduled posts: {len(posts)}",
        "Platforms: Facebook, Instagram, Threads, Telegram, TikTok photo",
        f"Schedule: {len(SLOTS)} posts/day for {TOTAL_DAYS} days from 2026-09-14, Europe/Kyiv time.",
        "",
    ]
    for row in report_rows:
        ready_md.append(f"- {row['scheduled_at']} — {row['title']} — `{row['media']}`")
    (OUTPUT_DIR / "READY_POSTS.md").write_text("\n".join(ready_md) + "\n", encoding="utf-8")

    queue_data = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    queue_posts = queue_data.setdefault("posts", [])
    queue_posts = [post for post in queue_posts if not str(post.get("id", "")).startswith("photo-pub-2026-09-")]
    queue_posts.extend(posts)
    queue_data["posts"] = queue_posts
    existing_notes = queue_data.get("notes", [])
    if isinstance(existing_notes, str):
        existing_notes = [existing_notes]
    elif not isinstance(existing_notes, list):
        existing_notes = []
    queue_data["notes"] = existing_notes
    note = f"Added {len(posts)} approved repeated photo publication posts from {SOURCE_DIR} on {datetime.now(timezone.utc).date().isoformat()}."
    if note not in queue_data["notes"]:
        queue_data["notes"].append(note)
    QUEUE_FILE.write_text(json.dumps(queue_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    data_js = CALENDAR_DIR / "photo-publications-autopost-data.js"
    data_js.write_text(
        "window.ALT_CAM_PHOTO_PUBLICATIONS_AUTOPOST = "
        + json.dumps(plan, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    html = """<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ALT-CAM Photo Publications Autopost</title>
  <style>
    :root{color-scheme:dark;--bg:#101012;--panel:rgba(255,255,255,.055);--line:rgba(255,255,255,.12);--text:#F5F5F7;--muted:#A1A1A6;--gold:#FFCC00}
    *{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,rgba(255,204,0,.16),transparent 34rem),var(--bg);color:var(--text);font-family:Inter,system-ui,Segoe UI,sans-serif}
    main{width:min(1280px,calc(100% - 28px));margin:auto;padding:36px 0 70px}h1{font-size:clamp(30px,5vw,58px);line-height:.96;margin:0 0 10px;letter-spacing:-.04em}p{color:var(--muted);line-height:1.55}
    .toolbar,.meta{display:flex;flex-wrap:wrap;gap:8px}.chip{border:1px solid var(--line);border-radius:999px;background:var(--panel);padding:8px 12px;color:var(--text);text-decoration:none;font-size:13px}
    .day{margin:20px 0;border:1px solid var(--line);border-radius:24px;overflow:hidden;background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.025))}.day h2{margin:0;padding:18px 20px;border-bottom:1px solid var(--line);font-size:20px}
    .post{display:grid;grid-template-columns:92px 210px 1fr;gap:18px;padding:18px 20px;border-bottom:1px solid var(--line)}.post:last-child{border-bottom:0}.time{color:var(--gold);font-weight:900;font-size:18px}
    img{width:210px;aspect-ratio:4/5;object-fit:cover;border-radius:18px;border:1px solid var(--line);background:#222}h3{margin:0 0 8px;font-size:21px}.gold{color:var(--gold)}
    details{margin-top:10px;border:1px solid var(--line);border-radius:14px;background:rgba(0,0,0,.22);overflow:hidden}summary{cursor:pointer;color:var(--gold);font-weight:800;padding:12px 14px}pre{white-space:pre-wrap;margin:0;padding:0 14px 14px;font-family:inherit;line-height:1.48;color:#e7e7e7}
    @media(max-width:760px){.post{grid-template-columns:1fr}.time{font-size:22px}img{width:100%;max-height:560px}}
  </style>
</head>
<body>
<main>
  <h1>ALT-CAM: автоочередь публикаций из папки фото</h1>
  <p>48 базовых материалов разложены в 180 публикаций на 90 дней: Facebook, Instagram, Threads, Telegram и TikTok photo. Каждый день — один постинг в первой половине дня и один во второй. Повторы идут в ротации, старые отменённые публикации не восстановлены.</p>
  <nav class="toolbar">
    <a class="chip" href="../content-plans/2026-09-14-photo-publications/publishing-posts.json">publishing-posts.json</a>
    <a class="chip" href="../content-plans/2026-09-14-photo-publications/READY_POSTS.md">READY_POSTS.md</a>
    <a class="chip" href="../content-plans/2026-09-14-photo-publications/import-report.json">import-report.json</a>
  </nav>
  <section id="calendar"></section>
</main>
<script src="./photo-publications-autopost-data.js"></script>
<script>
const data = window.ALT_CAM_PHOTO_PUBLICATIONS_AUTOPOST;
const calendar = document.getElementById('calendar');
const fmtDate = new Intl.DateTimeFormat('uk-UA',{weekday:'long',day:'numeric',month:'long',timeZone:'Europe/Kyiv'});
const fmtTime = new Intl.DateTimeFormat('uk-UA',{hour:'2-digit',minute:'2-digit',timeZone:'Europe/Kyiv'});
const esc = v => String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const details = (label,text)=>`<details><summary>${esc(label)}</summary><pre>${esc(text)}</pre></details>`;
const days = new Map();
for(const post of data.posts){const key=post.scheduled_at.slice(0,10); if(!days.has(key)) days.set(key,[]); days.get(key).push(post)}
calendar.innerHTML = [...days.entries()].map(([key,posts])=>`<article class="day"><h2>${fmtDate.format(new Date(posts[0].scheduled_at))} · ${posts.length} пости</h2>${posts.map(post=>`<div class="post"><div class="time">${fmtTime.format(new Date(post.scheduled_at))}</div><img src="../content-plans/${data.plan_id}/media/${post.image_url.split('/').pop()}" alt="${esc(post.title)}"><div><h3>${esc(post.title)}</h3><p><span class="gold">${esc(post.status)}</span> · ${esc(post.platforms.join(', '))}</p><div class="meta">${post.platforms.map(p=>`<span class="chip">${esc(p)}</span>`).join('')}</div>${details('Instagram',post.captions.instagram)}${details('Facebook',post.captions.facebook)}${details('Threads',post.captions.threads)}${details('Telegram',post.captions.telegram)}${details('TikTok',post.captions.tiktok)}</div></div>`).join('')}</article>`).join('');
</script>
</body>
</html>
"""
    (CALENDAR_DIR / "photo-publications-autopost.html").write_text(html, encoding="utf-8")

    print(json.dumps({"posts": len(posts), "first": posts[0]["scheduled_at"], "last": posts[-1]["scheduled_at"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
