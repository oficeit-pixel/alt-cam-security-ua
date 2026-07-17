"""
Create a reusable social publishing automation for a new business direction.

The generator copies the battle-tested ALT-CAM publisher runtime and creates:
- social-posts/<slug>-automation/
- social-posts/<slug>-images/
- .github/workflows/<slug>-publisher.yml

It intentionally does not copy real secrets or tokens.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUNTIME = ROOT / "social-posts" / "meta-automation"
WORKFLOWS = ROOT / ".github" / "workflows"


RUNTIME_FILES = [
    "publish_due.py",
    "check_setup.py",
    "requirements.txt",
    "META_STABLE_TOKEN.md",
]


DEFAULT_PLATFORMS = ["facebook", "instagram", "threads", "telegram"]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    if not slug:
        raise SystemExit("Slug cannot be empty.")
    return slug


def secret_prefix_for(slug: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", slug.upper()).strip("_")


def write_text(path: Path, text: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise SystemExit(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_runtime_file(name: str, target_dir: Path, overwrite: bool) -> None:
    source = SOURCE_RUNTIME / name
    target = target_dir / name
    if not source.exists():
        raise SystemExit(f"Missing source runtime file: {source}")
    if target.exists() and not overwrite:
        raise SystemExit(f"Refusing to overwrite existing file: {target}")
    shutil.copy2(source, target)


def env_example(args: argparse.Namespace, prefix: str) -> str:
    facebook_page_id = args.facebook_page_id or ""
    return f"""# Copy this file to .env for local testing.
# Do not commit .env with real tokens.
#
# GitHub Actions should store the same sensitive values as repository secrets.
# Recommended secret prefix for this direction: {prefix}

META_GRAPH_VERSION=v21.0
INSTAGRAM_GRAPH_VERSION=
THREADS_GRAPH_VERSION=

# Facebook Page
FACEBOOK_PAGE_ID={facebook_page_id}
FACEBOOK_PAGE_ACCESS_TOKEN=

# Instagram Business / Creator account
INSTAGRAM_USER_ID=
INSTAGRAM_ACCESS_TOKEN=

# Threads account
THREADS_USER_ID=
THREADS_ACCESS_TOKEN=

# Telegram channel/chat
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# TikTok Content Posting API
TIKTOK_ACCESS_TOKEN=
TIKTOK_POST_MODE=MEDIA_UPLOAD
TIKTOK_PRIVACY_LEVEL=PUBLIC_TO_EVERYONE
TIKTOK_DISABLE_COMMENT=false
TIKTOK_AUTO_ADD_MUSIC=true

# Safety
DRY_RUN=true
FAIL_ON_PUBLISH_ERROR=false
"""


def posts_json(args: argparse.Namespace) -> str:
    platforms = args.platforms
    image_base = args.image_base_url.rstrip("/") if args.image_base_url else "https://example.com/social-posts/images"
    sample = {
        "timezone": args.timezone,
        "notes": (
            "Images must be available by public HTTPS URL for Instagram, Threads, "
            "TikTok, and Telegram publishing APIs."
        ),
        "posts": [
            {
                "id": f"{args.slug}-sample-001",
                "scheduled_at": "2026-07-20T10:00:00+03:00",
                "platforms": platforms,
                "image_path": f"../{args.slug}-images/sample-001.png",
                "image_url": f"{image_base}/sample-001.png",
                "title": f"{args.brand_name}: sample post",
                "caption": (
                    f"{args.brand_name}: приклад публікації для нового напрямку.\\n\\n"
                    "Замініть цей текст, медіа та дату на реальний контент.\\n\\n"
                    "#brand #automation"
                ),
                "captions": {
                    "facebook": (
                        f"{args.brand_name}: приклад Facebook-публікації. "
                        "Тут можна зробити довший текст, CTA та посилання."
                    ),
                    "instagram": (
                        f"{args.brand_name}: коротший Instagram-текст з хештегами.\\n\\n"
                        "#brand #instagram"
                    ),
                    "threads": f"{args.brand_name}: короткий Threads-пост.",
                    "telegram": (
                        f"{args.brand_name}: Telegram-пост. Можна писати трохи довше "
                        "й додавати прямий заклик написати в чат."
                    ),
                },
            }
        ],
    }
    return json.dumps(sample, ensure_ascii=False, indent=2) + "\n"


def readme(args: argparse.Namespace, prefix: str) -> str:
    workflow_name = f"{args.slug}-publisher.yml"
    return f"""# {args.brand_name} social automation

This folder is a standalone automation module generated from the ALT-CAM publisher kit.

## Files

- `publish_due.py` — publishes due posts.
- `check_setup.py` — checks tokens and channel access.
- `posts.json` — content calendar.
- `state.json` — publication state; committed by GitHub Actions to avoid duplicates.
- `.env.example` — local environment template.
- `META_STABLE_TOKEN.md` — how to create a stable Meta Business token.

## GitHub workflow

Workflow file:

`.github/workflows/{workflow_name}`

It runs every 30 minutes and can also be started manually from GitHub Actions.

## Required GitHub secrets

Use this prefix for the new direction:

`{prefix}_`

Create only the secrets for platforms you actually use:

- `{prefix}_FACEBOOK_PAGE_ACCESS_TOKEN`
- `{prefix}_INSTAGRAM_USER_ID`
- `{prefix}_INSTAGRAM_ACCESS_TOKEN`
- `{prefix}_THREADS_USER_ID`
- `{prefix}_THREADS_ACCESS_TOKEN`
- `{prefix}_TELEGRAM_BOT_TOKEN`
- `{prefix}_TELEGRAM_CHAT_ID`
- `{prefix}_TIKTOK_ACCESS_TOKEN`

If you did not pass `--facebook-page-id`, also create:

- `{prefix}_FACEBOOK_PAGE_ID`

## Daily use

1. Put public images into `social-posts/{args.slug}-images/`.
2. Make sure each image is available by public HTTPS URL.
3. Add posts to `posts.json`.
4. Commit and push.
5. Run `{args.brand_name} Social Publisher` in GitHub Actions to test.

## Safety

- Do not paste tokens into chat messages.
- Use Meta Business System User tokens for Facebook Page publishing.
- Keep `FAIL_ON_PUBLISH_ERROR=false` if one broken channel should not stop the others.
"""


def workflow(args: argparse.Namespace, prefix: str) -> str:
    facebook_page_id_line = (
        f'      FACEBOOK_PAGE_ID: "{args.facebook_page_id}"'
        if args.facebook_page_id
        else f"      FACEBOOK_PAGE_ID: ${{{{ secrets.{prefix}_FACEBOOK_PAGE_ID }}}}"
    )
    return f"""name: {args.brand_name} Social Publisher

on:
  schedule:
    - cron: "{args.cron}"
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: {args.slug}-social-publisher
  cancel-in-progress: false

jobs:
  publish:
    runs-on: ubuntu-latest

    env:
      META_GRAPH_VERSION: v21.0
{facebook_page_id_line}
      FACEBOOK_PAGE_ACCESS_TOKEN: ${{{{ secrets.{prefix}_FACEBOOK_PAGE_ACCESS_TOKEN }}}}
      INSTAGRAM_USER_ID: ${{{{ secrets.{prefix}_INSTAGRAM_USER_ID }}}}
      INSTAGRAM_ACCESS_TOKEN: ${{{{ secrets.{prefix}_INSTAGRAM_ACCESS_TOKEN }}}}
      THREADS_USER_ID: ${{{{ secrets.{prefix}_THREADS_USER_ID }}}}
      THREADS_ACCESS_TOKEN: ${{{{ secrets.{prefix}_THREADS_ACCESS_TOKEN }}}}
      TELEGRAM_BOT_TOKEN: ${{{{ secrets.{prefix}_TELEGRAM_BOT_TOKEN }}}}
      TELEGRAM_CHAT_ID: ${{{{ secrets.{prefix}_TELEGRAM_CHAT_ID }}}}
      TIKTOK_ACCESS_TOKEN: ${{{{ secrets.{prefix}_TIKTOK_ACCESS_TOKEN }}}}
      TIKTOK_POST_MODE: ${{{{ vars.{prefix}_TIKTOK_POST_MODE || 'MEDIA_UPLOAD' }}}}
      TIKTOK_PRIVACY_LEVEL: ${{{{ vars.{prefix}_TIKTOK_PRIVACY_LEVEL || 'PUBLIC_TO_EVERYONE' }}}}
      DRY_RUN: "false"
      FAIL_ON_PUBLISH_ERROR: "false"

    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: python -m pip install -r social-posts/{args.slug}-automation/requirements.txt

      - name: Check publisher setup
        continue-on-error: true
        run: python social-posts/{args.slug}-automation/check_setup.py

      - name: Publish due posts
        run: python social-posts/{args.slug}-automation/publish_due.py

      - name: Save publication state
        if: always()
        run: |
          if [ -f social-posts/{args.slug}-automation/state.json ]; then
            git config user.name "github-actions[bot]"
            git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
            git add -f social-posts/{args.slug}-automation/state.json
            if ! git diff --cached --quiet; then
              git commit -m "Update {args.slug} social publisher state [skip ci]"
              git push
            fi
          fi
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new reusable social automation direction.")
    parser.add_argument("--slug", required=True, help="Short latin slug, e.g. altcam or solar-power.")
    parser.add_argument("--brand-name", required=True, help="Human-readable brand/direction name.")
    parser.add_argument("--timezone", default="Europe/Kyiv")
    parser.add_argument("--site-url", default="")
    parser.add_argument("--image-base-url", default="")
    parser.add_argument("--facebook-page-id", default="")
    parser.add_argument("--secret-prefix", default="", help="GitHub secret prefix. Default: slug uppercased.")
    parser.add_argument("--cron", default="*/30 * * * *", help="GitHub Actions cron schedule.")
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=DEFAULT_PLATFORMS,
        choices=["facebook", "instagram", "threads", "telegram", "tiktok"],
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.slug = slugify(args.slug)
    prefix = secret_prefix_for(args.secret_prefix or args.slug)

    target_dir = ROOT / "social-posts" / f"{args.slug}-automation"
    image_dir = ROOT / "social-posts" / f"{args.slug}-images"
    workflow_path = WORKFLOWS / f"{args.slug}-publisher.yml"

    target_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    for name in RUNTIME_FILES:
        copy_runtime_file(name, target_dir, args.overwrite)

    write_text(target_dir / ".env.example", env_example(args, prefix), args.overwrite)
    write_text(target_dir / ".gitignore", ".env\n__pycache__/\n*.pyc\n", args.overwrite)
    write_text(target_dir / "posts.json", posts_json(args), args.overwrite)
    write_text(target_dir / "state.json", json.dumps({"published": {}}, indent=2) + "\n", args.overwrite)
    write_text(target_dir / "README.md", readme(args, prefix), args.overwrite)
    write_text(image_dir / ".gitkeep", "", args.overwrite)
    write_text(workflow_path, workflow(args, prefix), args.overwrite)

    print("Created social automation module:")
    print(f"- {target_dir}")
    print(f"- {image_dir}")
    print(f"- {workflow_path}")
    print()
    print(f"GitHub secret prefix: {prefix}_")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
