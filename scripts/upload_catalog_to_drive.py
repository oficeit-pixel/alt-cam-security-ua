from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "catalog-sync" / "config.json"


def upsert(service, path: Path, folder_id: str) -> None:
    escaped = path.name.replace("'", "\\'")
    query = f"name='{escaped}' and '{folder_id}' in parents and trashed=false"
    existing = service.files().list(q=query, fields="files(id,name)", pageSize=10).execute().get("files", [])
    media = MediaFileUpload(str(path), resumable=True)
    if existing:
        service.files().update(fileId=existing[0]["id"], media_body=media).execute()
    else:
        service.files().create(body={"name": path.name, "parents": [folder_id]}, media_body=media, fields="id").execute()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "catalog-sync" / "output")
    args = parser.parse_args()
    raw_credentials = os.environ["GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(raw_credentials)
    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))["google_drive"]
    output = args.output.resolve()
    for name in ("sync-report.json", "catalog-summary.csv", "categories.json", "yugtorg-status.json"):
        path = output / name
        if path.exists():
            destination = config["reports_folder_id"] if "report" in name or "status" in name else config["normalized_folder_id"]
            upsert(service, path, destination)
    for path in sorted((output / "normalized").glob("*.json")):
        upsert(service, path, config["normalized_folder_id"])
    for path in sorted((output / "raw").glob("*")):
        if path.is_file() and path.name not in {"yugtorg-products-probe.json", "yugtorg-currency-rates.json"}:
            upsert(service, path, config["raw_folder_id"])
    meta_feed = ROOT / "feeds" / "meta-catalog.csv"
    if meta_feed.exists():
        upsert(service, meta_feed, config["meta_folder_id"])
    site_catalog = ROOT / "catalog-data.js"
    if site_catalog.exists():
        upsert(service, site_catalog, config["site_telegram_folder_id"])


if __name__ == "__main__":
    main()
