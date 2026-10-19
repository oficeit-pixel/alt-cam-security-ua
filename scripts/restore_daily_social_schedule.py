"""Rebuild a 90-day queue from approved photo assets without losing history."""
import argparse
import copy
import importlib.util
import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
AUTOMATION = ROOT / "social-posts/meta-automation"
PLAN = ROOT / "social-posts/content-plans/2026-09-14-photo-publications"
CALENDAR = ROOT / "social-posts/calendar"
PLATFORMS = ["facebook", "instagram", "threads", "telegram", "tiktok"]
LEGACY_BASE = "https://oficeit-pixel.github.io/alt-cam-security-ua/"
PUBLIC_BASE = "https://alt-cam.net.ua/"


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--days", type=int, default=90)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("publisher", AUTOMATION / "publish_due.py")
    publisher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publisher)
    queue_path = AUTOMATION / "august-priority-posts.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    state = json.loads((AUTOMATION / "august-priority-state.json").read_text(encoding="utf-8"))
    campaign = f"altcam-daily-{args.start.isoformat()}"
    if any(p.get("campaign") == campaign for p in queue["posts"]):
        raise SystemExit("This daily campaign already exists; refusing to reset publication records.")
    source = json.loads((PLAN / "publishing-posts.json").read_text(encoding="utf-8").replace(LEGACY_BASE, PUBLIC_BASE))
    excluded_media = {p.get("image_url", "").replace(LEGACY_BASE, PUBLIC_BASE)
                      for p in queue["posts"] if p.get("status") == "canceled"}
    templates = {}
    for post in source["posts"]:
        if post.get("image_url") and post["image_url"] not in excluded_media:
            templates.setdefault(post["image_url"], post)
    last_seen = {}
    for post in queue["posts"]:
        times = [entry.get("published_at", "") for entry in
                 state.get("published", {}).get(post["id"], {}).values() if isinstance(entry, dict)]
        if times:
            image = post.get("image_url", "").replace(LEGACY_BASE, PUBLIC_BASE)
            last_seen[image] = max(last_seen.get(image, ""), *times)
    bases = sorted(templates.values(), key=lambda p: (last_seen.get(p["image_url"], ""), p["id"]))
    if len(bases) < 4:
        raise SystemExit("Too few approved source images for a varied daily schedule.")
    # Preserve all IDs and API results; close the superseded pending queue so
    # old overdue items cannot burst-publish alongside the restored schedule.
    for post in queue["posts"]:
        if post.get("status", "ready") in {"approved", "ready"}:
            post["status"] = "archived"
            post["archive_reason"] = f"Replaced by {campaign}; publication history preserved."
    posts = []
    kyiv = ZoneInfo("Europe/Kyiv")
    for index in range(args.days * 2):
        round_number, position = divmod(index, len(bases))
        template = bases[(position + round_number * 7) % len(bases)]
        post = copy.deepcopy(template)
        day = args.start + timedelta(days=index // 2)
        slot = time(10, 0) if index % 2 == 0 else time(17, 30)
        post.update(id=f"daily-{args.start.isoformat()}-{index + 1:03d}", campaign=campaign,
                    scheduled_at=datetime.combine(day, slot, kyiv).isoformat(),
                    status="approved", platforms=PLATFORMS.copy(), repeat_round=round_number + 1,
                    source_post_id=template["id"])
        post["captions"]["threads"] = publisher.threads_caption(post["captions"]["threads"])
        posts.append(post)
    # Repair retained texts too, so manual retries of historical items are safe.
    for post in queue["posts"]:
        if post.get("captions", {}).get("threads"):
            post["captions"]["threads"] = publisher.threads_caption(post["captions"]["threads"])
    queue["posts"].extend(posts)
    queue["posts"].sort(key=lambda p: publisher.parse_dt(p["scheduled_at"]).replace(
        tzinfo=publisher.parse_dt(p["scheduled_at"]).tzinfo or timezone.utc))
    queue.setdefault("notes", []).append(
        f"{args.start}: Restored {args.days} days, 10:00 and 17:30 Europe/Kyiv; old delivery history preserved.")
    write_json(queue_path, queue)
    plan = {**source, "campaign": campaign, "generated_at": datetime.now(timezone.utc).isoformat(),
            "post_count": len(posts), "base_post_count": len(bases), "posts": posts,
            "schedule": {"start": str(args.start), "days": args.days, "timezone": "Europe/Kyiv",
                         "slots": ["10:00", "17:30"]},
            "notes": ["Two daily slots; repeated approved media in rotation.",
                      "TikTok uploads go to the creator inbox and require confirmation in the app."]}
    write_json(PLAN / "publishing-posts.json", plan)
    (CALENDAR / "photo-publications-autopost-data.js").write_text(
        "window.ALT_CAM_PHOTO_PUBLICATIONS_AUTOPOST = " + json.dumps(plan, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8")
    rows = [{"id": p["id"], "scheduled_at": p["scheduled_at"], "title": p["title"],
             "media": p["image_url"].split("/")[-1], "repeat_round": p["repeat_round"]} for p in posts]
    write_json(PLAN / "import-report.json", {"rows": rows})
    (PLAN / "READY_POSTS.md").write_text(
        "# ALT-CAM: 90 days, two daily posts\n\n"
        + f"{posts[0]['scheduled_at']} — {posts[-1]['scheduled_at']}; Europe/Kyiv.\n\n"
        + "TikTok: upload to inbox; confirm publication in the app.\n\n"
        + "\n".join(f"- {r['scheduled_at']} — {r['title']} — `{r['id']}`" for r in rows) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(posts), "base_media": len(bases), "first": posts[0]["scheduled_at"],
                      "last": posts[-1]["scheduled_at"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
