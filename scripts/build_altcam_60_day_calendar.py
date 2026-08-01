from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-03-60-day-matrix"
CALENDAR_DIR = ROOT / "social-posts" / "calendar"
PLAN_PATH = PLAN_DIR / "plan.json"
DRAFTS_PATH = PLAN_DIR / "posting-drafts.json"
DATA_PATH = CALENDAR_DIR / "altcam-60-day-data.js"
HTML_PATH = CALENDAR_DIR / "altcam-60-day.html"


def calendar_media_path(path: str) -> str:
    source = PLAN_DIR / path
    return os.path.relpath(source, CALENDAR_DIR).replace("\\", "/")


def first_lines(text: str, count: int = 2) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines[:count])


def build_payload() -> dict:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    drafts = json.loads(DRAFTS_PATH.read_text(encoding="utf-8"))["posts"]
    drafts_by_id = {post["id"]: post for post in drafts}
    posts = []

    for day in plan["days"]:
        post_id = f"altcam-60d-{day['date']}-d{day['day']:02d}"
        draft = drafts_by_id.get(post_id, {})
        time_value = day["publish_time"].split()[0]
        scheduled_at = f"{day['date']}T{time_value}:00+03:00"
        media = day["media"]
        captions = draft.get("captions", {})
        posts.append(
            {
                "id": post_id,
                "day": day["day"],
                "scheduled_at": scheduled_at,
                "platforms": ["facebook", "instagram", "tiktok", "threads", "telegram", "youtube"],
                "status": draft.get("status", "draft"),
                "approval_required": draft.get("approval_required", True),
                "content_type": day["content_type"],
                "contour": day["contour"],
                "topic": day["topic"],
                "category": day["category"],
                "object_type": day["object_type"],
                "brands": day["brands"],
                "keyword": day["keyword"],
                "hook": day["tiktok_shorts_reels"]["visual_hook_first_3s"],
                "image_path": calendar_media_path(media["tiktok_cover"]),
                "youtube_thumb": calendar_media_path(media["youtube_thumbnail"]),
                "prompt_path": calendar_media_path(media["generation_prompt"]),
                "caption": draft.get("caption", ""),
                "summary": first_lines(draft.get("caption", "")),
                "captions": {
                    "facebook": captions.get("facebook", day["instagram_facebook"]["caption"]),
                    "instagram": captions.get("instagram", day["instagram_facebook"]["caption"]),
                    "tiktok": captions.get("tiktok", day["tiktok_shorts_reels"]["audio_hook"]),
                    "threads": captions.get("threads", "\n".join(day["threads"]["thread_posts"])),
                    "telegram": captions.get("telegram", day["telegram"]["text"]),
                    "youtube": captions.get("youtube", day["youtube_long"]["description"]),
                },
                "platform_details": {
                    "tiktok": {
                        "title": day["tiktok_shorts_reels"]["cover_title"],
                        "visual_hook": day["tiktok_shorts_reels"]["visual_hook_first_3s"],
                        "audio_hook": day["tiktok_shorts_reels"]["audio_hook"],
                        "scenario": day["tiktok_shorts_reels"]["scenario_by_seconds"],
                        "cta": day["tiktok_shorts_reels"]["cta"],
                    },
                    "instagram_facebook": {
                        "format": day["instagram_facebook"]["format"],
                        "carousel_title": day["instagram_facebook"]["carousel_title"],
                        "slides": day["instagram_facebook"]["slides"],
                        "hashtags": day["instagram_facebook"]["hashtags"],
                    },
                    "threads": {
                        "format": day["threads"]["format"],
                        "posts": day["threads"]["thread_posts"],
                        "first_comment": day["threads"]["first_comment"],
                    },
                    "youtube": {
                        "title": day["youtube_long"]["title"],
                        "timecodes": day["youtube_long"]["timecodes"],
                        "pinned_comment": day["youtube_long"]["pinned_comment"],
                        "community_post": day["youtube_long"]["community_post"],
                    },
                    "telegram": {
                        "format": day["telegram"]["format"],
                        "button": day["telegram"]["inline_button"],
                    },
                },
            }
        )

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "timezone": "Europe/Kyiv",
        "source": str(PLAN_DIR.relative_to(ROOT).as_posix()),
        "posts": posts,
    }


def render_html() -> str:
    return """<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ALT-CAM 60 днів — контент-календар</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #111114;
      --panel: rgba(255,255,255,.045);
      --panel-2: rgba(255,255,255,.07);
      --text: #f5f5f7;
      --muted: #a1a1aa;
      --line: rgba(255,255,255,.12);
      --gold: #ffcc00;
      --green: #47d18c;
      --orange: #ff9f43;
      --red: #ff3b30;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top left, rgba(255,204,0,.13), transparent 34rem), var(--bg);
      color: var(--text);
    }
    main { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 42px 0 56px; }
    header { display: flex; gap: 18px; align-items: flex-end; justify-content: space-between; margin-bottom: 22px; }
    h1 { margin: 0 0 8px; font-size: clamp(30px, 5vw, 54px); letter-spacing: -.045em; }
    p { margin: 0; color: var(--muted); line-height: 1.55; }
    .badge { display: inline-flex; align-items: center; gap: 8px; padding: 10px 14px; border: 1px solid var(--line); border-radius: 999px; background: var(--panel); color: var(--text); white-space: nowrap; }
    .badge::before { content: ""; width: 9px; height: 9px; border-radius: 50%; background: var(--green); box-shadow: 0 0 16px var(--green); }
    .toolbar { display: flex; flex-wrap: wrap; gap: 10px; margin: 0 0 18px; }
    button, .link-btn { cursor: pointer; color: var(--text); background: var(--panel); border: 1px solid var(--line); padding: 10px 13px; border-radius: 999px; text-decoration: none; font: inherit; }
    button.active { background: var(--gold); color: #171200; border-color: var(--gold); font-weight: 800; }
    .grid { display: grid; gap: 16px; }
    .day { border: 1px solid var(--line); border-radius: 22px; background: var(--panel); backdrop-filter: blur(12px); overflow: hidden; }
    .day-head { display: flex; justify-content: space-between; gap: 12px; padding: 18px 20px; border-bottom: 1px solid var(--line); background: rgba(255,255,255,.035); }
    .day-head h2 { margin: 0; font-size: 19px; }
    .count { color: var(--gold); font-weight: 700; text-align: right; }
    .post { display: grid; grid-template-columns: 92px 156px 1fr; gap: 16px; padding: 18px 20px; align-items: start; }
    .time { color: var(--gold); font-weight: 800; font-size: 18px; }
    .media { display: grid; gap: 10px; }
    img { width: 156px; aspect-ratio: 9 / 16; object-fit: cover; border-radius: 16px; border: 1px solid var(--line); background: #222; }
    .thumb { aspect-ratio: 16 / 9; }
    h3 { margin: 0 0 8px; font-size: 20px; }
    .meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    .chip { font-size: 12px; color: var(--text); background: var(--panel-2); border: 1px solid var(--line); padding: 6px 9px; border-radius: 999px; }
    .chip.draft { color: #201500; background: var(--orange); border-color: var(--orange); font-weight: 800; }
    .chip.ready { color: #062015; background: var(--green); border-color: var(--green); font-weight: 800; }
    .chip.hot { color: #260200; background: var(--gold); border-color: var(--gold); font-weight: 900; }
    details { margin-top: 12px; border: 1px solid var(--line); border-radius: 14px; background: rgba(255,255,255,.035); overflow: hidden; }
    summary { padding: 12px 14px; cursor: pointer; color: var(--gold); font-weight: 800; }
    pre { white-space: pre-wrap; margin: 0; padding: 0 14px 14px; font-family: inherit; color: var(--text); line-height: 1.5; }
    .platform-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
    .mini { border: 1px solid var(--line); border-radius: 14px; padding: 12px; background: rgba(0,0,0,.18); }
    .mini strong { color: var(--gold); }
    .note { margin-top: 22px; padding: 16px 18px; border-radius: 18px; background: rgba(255,204,0,.08); border: 1px solid rgba(255,204,0,.22); color: #f8eab0; }
    @media (max-width: 840px) {
      header { display: block; }
      .badge { margin-top: 18px; }
      .post { grid-template-columns: 1fr; }
      img { width: 100%; max-height: 420px; }
      .platform-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>ALT-CAM 60 днів</h1>
        <p>Контент-календар для Facebook, Instagram, TikTok/Reels/Shorts, Threads, Telegram і YouTube. Заставки зроблені живішими: товар, Аліса, Сергій або конкретна проблема.</p>
      </div>
      <div class="badge">60-day media plan</div>
    </header>
    <nav class="toolbar" id="filters">
      <button class="active" data-filter="all">Усі</button>
      <button data-filter="Captivate">Captivate</button>
      <button data-filter="Expert">Expert</button>
      <button data-filter="Proof">Proof</button>
      <button data-filter="Offer">Offer</button>
      <a class="link-btn" href="../content-plans/2026-08-03-60-day-matrix/media/MEDIA_INDEX.md">MEDIA_INDEX</a>
      <a class="link-btn" href="../content-plans/2026-08-03-60-day-matrix/platform-posts/README.md">Тексти по платформах</a>
    </nav>
    <section id="calendar" class="grid" aria-live="polite"></section>
    <p class="note">Перед автоматичною публікацією перевіряємо: чи є реальне фото/відео об’єкта, чи підходить ціна, чи не треба замінити заставку на живий кадр із монтажу.</p>
  </main>
  <script src="./altcam-60-day-data.js"></script>
  <script>
    const fmtDate = new Intl.DateTimeFormat("uk-UA", { weekday: "long", day: "numeric", month: "long", timeZone: "Europe/Kyiv" });
    const fmtTime = new Intl.DateTimeFormat("uk-UA", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Kyiv" });
    const calendar = document.getElementById("calendar");
    const filters = document.getElementById("filters");
    let active = "all";

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
      })[char]);
    }

    function titleFromPost(post) {
      const text = post.hook || post.topic || post.id;
      return text.length > 96 ? text.slice(0, 93) + "…" : text;
    }

    function platformBlock(label, text) {
      return `<details><summary>${label}</summary><pre>${escapeHtml(text)}</pre></details>`;
    }

    function render(posts) {
      const filtered = active === "all" ? posts : posts.filter((post) => post.content_type === active);
      const days = new Map();
      for (const post of filtered.sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))) {
        const key = post.scheduled_at.slice(0, 10);
        if (!days.has(key)) days.set(key, []);
        days.get(key).push(post);
      }
      calendar.innerHTML = [...days.entries()].map(([key, items]) => `
        <article class="day">
          <div class="day-head">
            <h2>${fmtDate.format(new Date(items[0].scheduled_at))}</h2>
            <div class="count">${items.length} тема • 6 платформ</div>
          </div>
          ${items.map((post) => `
            <div class="post">
              <div class="time">${fmtTime.format(new Date(post.scheduled_at))}</div>
              <div class="media">
                <img src="${post.image_path}" alt="">
                <img class="thumb" src="${post.youtube_thumb}" alt="">
              </div>
              <div>
                <h3>${escapeHtml(titleFromPost(post))}</h3>
                <p>${escapeHtml(post.summary)}</p>
                <div class="meta">
                  <span class="chip hot">${post.content_type}</span>
                  ${post.platforms.map((platform) => `<span class="chip">${platform}</span>`).join("")}
                  <span class="chip ${post.status === "draft" ? "draft" : "ready"}">${post.status === "draft" ? "ЧЕРНЕТКА" : "ГОТОВО"}</span>
                  <span class="chip">${escapeHtml(post.keyword)}</span>
                  <span class="chip">${escapeHtml(post.object_type)}</span>
                  <span class="chip">📍 Київ / Вишгород</span>
                </div>
                <div class="platform-grid">
                  <div class="mini"><strong>TikTok/Reels/Shorts</strong><br>${escapeHtml(post.platform_details.tiktok.visual_hook)}</div>
                  <div class="mini"><strong>Instagram/Facebook</strong><br>${escapeHtml(post.platform_details.instagram_facebook.carousel_title)}</div>
                  <div class="mini"><strong>Threads</strong><br>${escapeHtml(post.platform_details.threads.first_comment)}</div>
                  <div class="mini"><strong>YouTube</strong><br>${escapeHtml(post.platform_details.youtube.title)}</div>
                </div>
                ${platformBlock("Facebook", post.captions.facebook)}
                ${platformBlock("Instagram", post.captions.instagram)}
                ${platformBlock("TikTok / Reels / Shorts сценарій", post.captions.tiktok)}
                ${platformBlock("Threads", post.captions.threads)}
                ${platformBlock("Telegram", post.captions.telegram)}
                ${platformBlock("YouTube", post.captions.youtube)}
              </div>
            </div>
          `).join("")}
        </article>
      `).join("");
    }

    filters.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-filter]");
      if (!button) return;
      active = button.dataset.filter;
      filters.querySelectorAll("button").forEach((item) => item.classList.toggle("active", item === button));
      render(window.ALT_CAM_60_DAY_CALENDAR.posts);
    });

    render(window.ALT_CAM_60_DAY_CALENDAR.posts);
  </script>
</body>
</html>
"""


def main() -> int:
    CALENDAR_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    DATA_PATH.write_text(
        "window.ALT_CAM_60_DAY_CALENDAR = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    HTML_PATH.write_text(render_html(), encoding="utf-8")
    print(HTML_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
