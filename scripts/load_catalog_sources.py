from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


ACTIVE = {"так", "yes", "true", "1"}
DRIVE_ID = re.compile(r"(?:/d/|[?&]id=)([A-Za-z0-9_-]+)")


def cell(row: list[str], index: int) -> str:
    return str(row[index] if index < len(row) else "").strip()


def file_id(value: str) -> str:
    match = DRIVE_ID.search(value)
    return match.group(1) if match else value.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--download-dir", type=Path, required=True)
    args = parser.parse_args()

    config = json.loads(args.base_config.read_text(encoding="utf-8"))
    raw_credentials = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON", "").strip()
    spreadsheet_id = os.getenv("GOOGLE_CONTACTS_SPREADSHEET_ID", "").strip()
    if not raw_credentials or not spreadsheet_id:
        args.output.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Supplier feed registry is not configured; using repository sources")
        return

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(raw_credentials),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )
    sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    rows = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range="'Фіди постачальників'!A3:O300")
        .execute()
        .get("values", [])
    )
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    args.download_dir.mkdir(parents=True, exist_ok=True)
    feeds: list[dict[str, str]] = []
    seen: set[str] = set()

    for row in rows:
        if cell(row, 0).casefold() not in ACTIVE:
            continue
        supplier, key = cell(row, 1).casefold(), cell(row, 2)
        source_type, url, drive_value = cell(row, 3), cell(row, 4), cell(row, 5)
        feed_format, schema = cell(row, 6).upper(), cell(row, 7)
        if supplier != "viatec" or feed_format != "XML" or schema != "Viatec XML":
            print(f"Skipping unsupported active feed: {supplier}/{key} ({schema}, {feed_format})")
            continue
        if not key or key in seen:
            raise RuntimeError(f"Duplicate or empty active feed key: {key!r}")
        seen.add(key)
        entry = {"key": key}
        if source_type == "Google Drive":
            source_id = file_id(drive_value)
            if not source_id:
                raise RuntimeError(f"Google Drive file is missing for feed {key}")
            target = args.download_dir / f"{key}.xml"
            with target.open("wb") as handle:
                downloader = MediaIoBaseDownload(handle, drive.files().get_media(fileId=source_id))
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            entry.update({"url": f"drive://{source_id}", "local_file": str(target)})
        else:
            if not url.startswith(("https://", "http://")):
                raise RuntimeError(f"Valid feed URL is missing for {key}")
            entry["url"] = url
        feeds.append(entry)

    if not feeds:
        raise RuntimeError("No supported active supplier feeds found")
    config["viatec_feeds"] = feeds
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"active_feeds": len(feeds), "keys": sorted(seen)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
