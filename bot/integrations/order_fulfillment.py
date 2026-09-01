import imaplib
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parseaddr
from typing import Any

from aiohttp import ClientSession
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds

from bot.config import get_settings
from bot.db.base import SessionLocal
from bot.db.models import AdminAuditLog, WebOrder


class IntegrationNotConfigured(RuntimeError):
    pass


ORDER_PATTERN = re.compile(r"\bWEB-\d{8}-[A-F0-9]{6}\b", re.I)
TRACK_PATTERNS = (
    re.compile(r"\b[A-Z]{2}\d{9}UA\b", re.I),
    re.compile(r"\b\d{12,18}\b"),
)


def _load_google_service_account(settings: Any) -> dict[str, Any]:
    raw = settings.google_service_account_json
    if not raw:
        secret_file = Path(settings.google_service_account_file)
        if secret_file.is_file():
            raw = secret_file.read_text(encoding="utf-8")
    if not raw:
        raise IntegrationNotConfigured("google_drive_not_configured")
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("invalid_google_service_account_json") from exc
    if payload.get("type") != "service_account" or not payload.get("private_key"):
        raise RuntimeError("invalid_google_service_account_json")
    return payload


def _google_drive_is_configured(settings: Any) -> bool:
    return bool(
        settings.google_drive_folder_id
        and (
            settings.google_service_account_json
            or Path(settings.google_service_account_file).is_file()
        )
    )


def _safe_folder_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", " ", value or "")
    return re.sub(r"\s+", " ", cleaned).strip()[:120] or fallback


def _drive_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


async def _drive_folder(aiogoogle: Aiogoogle, drive: Any, parent_id: str, name: str) -> dict[str, Any]:
    query = (
        f"'{_drive_query_value(parent_id)}' in parents and "
        f"name = '{_drive_query_value(name)}' and "
        "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    found = await aiogoogle.as_service_account(
        drive.files.list(
            q=query,
            fields="files(id,name,webViewLink)",
            pageSize=1,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
    )
    files = found.get("files", []) if isinstance(found, dict) else []
    if files:
        return files[0]
    return await aiogoogle.as_service_account(
        drive.files.create(
            json={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
            fields="id,name,webViewLink",
            supportsAllDrives=True,
        )
    )


async def ensure_order_drive_folder(order: Any) -> str:
    settings = get_settings()
    if not settings.google_drive_folder_id:
        raise IntegrationNotConfigured("google_drive_not_configured")
    service_account = _load_google_service_account(settings)
    credentials = ServiceAccountCreds(
        scopes=["https://www.googleapis.com/auth/drive"],
        **service_account,
    )
    created_at = order.created_at or datetime.now(timezone.utc)
    customer = order.customer or {}
    client_name = _safe_folder_name(str(customer.get("name", "")), "Клієнт")
    client_phone = _safe_folder_name(str(customer.get("phone", "")), "без-телефону")
    path = [
        str(created_at.year),
        f"{created_at.month:02d}",
        _safe_folder_name(f"{client_name}-{client_phone}", "Клієнт"),
        _safe_folder_name(order.order_number, "Замовлення"),
    ]
    parent_id = settings.google_drive_folder_id
    async with Aiogoogle(service_account_creds=credentials) as aiogoogle:
        drive = await aiogoogle.discover("drive", "v3")
        folder: dict[str, Any] = {}
        for name in path:
            folder = await _drive_folder(aiogoogle, drive, parent_id, name)
            parent_id = folder["id"]
    return folder.get("webViewLink") or f"https://drive.google.com/drive/folders/{parent_id}"


async def delete_drive_folder(folder_url: str) -> None:
    settings = get_settings()
    if not folder_url:
        return
    match = re.search(r"/folders/([A-Za-z0-9_-]+)", folder_url)
    if not match:
        raise RuntimeError("invalid_drive_folder_url")
    service_account = _load_google_service_account(settings)
    credentials = ServiceAccountCreds(scopes=["https://www.googleapis.com/auth/drive"], **service_account)
    async with Aiogoogle(service_account_creds=credentials) as aiogoogle:
        drive = await aiogoogle.discover("drive", "v3")
        folder_id = match.group(1)
        metadata = await aiogoogle.as_service_account(drive.files.get(fileId=folder_id, fields="parents", supportsAllDrives=True))
        parent_ids = metadata.get("parents", []) if isinstance(metadata, dict) else []
        await aiogoogle.as_service_account(drive.files.delete(fileId=folder_id, supportsAllDrives=True))
        if parent_ids:
            parent_id = parent_ids[0]
            children = await aiogoogle.as_service_account(drive.files.list(q=f"'{_drive_query_value(parent_id)}' in parents and trashed = false", fields="files(id)", pageSize=1, supportsAllDrives=True, includeItemsFromAllDrives=True))
            if isinstance(children, dict) and not children.get("files"):
                await aiogoogle.as_service_account(drive.files.delete(fileId=parent_id, supportsAllDrives=True))


def _extract_status(payload: Any) -> str:
    if isinstance(payload, list) and payload:
        return _extract_status(payload[-1])
    if not isinstance(payload, dict):
        return ""
    lifecycle = payload.get("lifecycle")
    if lifecycle:
        nested = _extract_status(lifecycle)
        if nested:
            return nested
    for key in ("status", "event", "name", "description"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def map_ukrposhta_status(raw_status: str) -> str | None:
    status = raw_status.upper()
    if any(token in status for token in ("DELIVERED", "RECEIVED", "ВРУЧЕН", "ОТРИМАН")):
        return "received"
    if any(token in status for token in ("ARRIVED", "POST OFFICE", "У ВІДДІЛЕН", "ПРИБУВ")):
        return "arrived"
    if any(token in status for token in ("RETURN", "FAILED", "PROBLEM", "НЕ ВРУЧ")):
        return "problem"
    if any(token in status for token in ("TRANSIT", "ROUTE", "СОРТУВ", "У ДОРОЗ")):
        return "in_transit"
    if any(token in status for token in ("ACCEPTED", "POSTED", "ПРИЙНЯТ")):
        return "shipped"
    if "CREATED" in status or "СТВОРЕН" in status:
        return "waiting_tracking"
    return None


async def fetch_ukrposhta_tracking(barcode: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.ukrposhta_tracking_token:
        raise IntegrationNotConfigured("ukrposhta_tracking_not_configured")
    url = f"{settings.ukrposhta_api_url.rstrip('/')}/shipments/{barcode}/lifecycle"
    async with ClientSession() as client:
        async with client.get(url, params={"token": settings.ukrposhta_tracking_token}, timeout=15) as response:
            text = await response.text()
            if response.status >= 400:
                raise RuntimeError(f"ukrposhta_http_{response.status}")
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                raise RuntimeError("ukrposhta_invalid_response") from exc
    raw_status = _extract_status(payload)
    return {"raw_status": raw_status, "mapped_status": map_ukrposhta_status(raw_status), "payload": payload}


def _message_text(message: Any) -> str:
    parts: list[str] = []
    for part in message.walk() if message.is_multipart() else [message]:
        if part.get_content_type() not in {"text/plain", "text/html"}:
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        charset = part.get_content_charset() or "utf-8"
        parts.append(payload.decode(charset, errors="replace"))
    return re.sub(r"<[^>]+>", " ", "\n".join(parts))


def _provider_for_track(track: str) -> str:
    if re.fullmatch(r"[A-Z]{2}\d{9}UA", track, re.I):
        return "ukrposhta"
    if track.isdigit() and len(track) == 14:
        return "nova_poshta"
    return "other"


def fetch_supplier_tracking_messages() -> list[dict[str, str]]:
    settings = get_settings()
    if not settings.imap_user or not settings.imap_password:
        raise IntegrationNotConfigured("imap_not_configured")
    allowed = {item.strip().casefold() for item in (settings.supplier_email_senders or "").split(",") if item.strip()}
    if not allowed:
        raise IntegrationNotConfigured("supplier_email_senders_not_configured")
    results: list[dict[str, str]] = []
    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port) as mailbox:
        mailbox.login(settings.imap_user, settings.imap_password)
        status, _ = mailbox.select(settings.imap_folder, readonly=True)
        if status != "OK":
            raise RuntimeError("imap_folder_unavailable")
        status, data = mailbox.search(None, "UNSEEN")
        if status != "OK":
            raise RuntimeError("imap_search_failed")
        for message_id in data[0].split()[-50:]:
            status, raw = mailbox.fetch(message_id, "(RFC822)")
            if status != "OK" or not raw or not isinstance(raw[0], tuple):
                continue
            message = message_from_bytes(raw[0][1])
            sender = parseaddr(message.get("From", ""))[1].casefold()
            if sender not in allowed:
                continue
            subject = str(make_header(decode_header(message.get("Subject", ""))))
            content = f"{subject}\n{_message_text(message)}"
            order_match = ORDER_PATTERN.search(content)
            track = next((match.group(0).upper() for pattern in TRACK_PATTERNS if (match := pattern.search(content))), "")
            if order_match and track:
                results.append({"order_number": order_match.group(0).upper(), "tracking_number": track, "provider": _provider_for_track(track), "sender": sender})
    return results


async def auto_create_order_drive_folder(order_id: int) -> None:
    settings = get_settings()
    if not _google_drive_is_configured(settings):
        return
    async with SessionLocal() as session:
        order = await session.get(WebOrder, order_id)
        if not order or order.drive_folder_url:
            return
        folder_url = await ensure_order_drive_folder(order)
        order.drive_folder_url = folder_url
        history = list(order.status_history or [])
        history.append({"at": datetime.now(timezone.utc).isoformat(), "admin_id": None, "admin_email": "system@alt-cam.net.ua", "changes": {"drive_folder_url": {"before": None, "after": folder_url}}})
        order.status_history = history[-200:]
        session.add(AdminAuditLog(admin_email="system@alt-cam.net.ua", action="drive_folder_created", entity_type="order", entity_id=order.order_number, details={"url": folder_url}, ip_address=None))
        await session.commit()
