import imaplib
import json
import logging
import re
import tempfile
from html import escape
from pathlib import Path
from datetime import datetime, timezone
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parseaddr
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import ClientSession
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds

from bot.config import get_settings
from bot.db.base import SessionLocal
from bot.db.models import AdminAuditLog, WebOrder


logger = logging.getLogger(__name__)


class IntegrationNotConfigured(RuntimeError):
    pass


class DriveRelayError(RuntimeError):
    pass


ORDER_PATTERN = re.compile(r"\bWEB-\d{8}-[A-F0-9]{6}\b", re.I)
DRIVE_FOLDER_RELAY_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbzoTpvXK2Ho3vAceIklOXYRYc3bEkagwq_eofb6_gjb3CG4NZIEZBa4p-1DDQjjSn75/exec"
)
ALT_CAM_DRIVE_ROOT_ID = "1ji_xMy1Jtq1Zg3wgXkhkdpP0eTnR8XTc"
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


def _active(value: Any) -> bool:
    return str(value or "").strip().casefold() in {"так", "yes", "true", "1"}


def _row_value(row: list[Any], index: int) -> str:
    return str(row[index] if index < len(row) else "").strip()


async def load_supplier_directory() -> dict[str, list[dict[str, Any]]]:
    settings = get_settings()
    if not settings.google_contacts_spreadsheet_id:
        raise IntegrationNotConfigured("supplier_directory_not_configured")
    credentials = ServiceAccountCreds(
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        **_load_google_service_account(settings),
    )
    ranges = {
        "suppliers": "Постачальники!A3:O300",
        "managers": "Менеджери!A3:L300",
        "routes": "Маршрутизація!A3:L300",
    }
    values: dict[str, list[list[Any]]] = {}
    async with Aiogoogle(service_account_creds=credentials) as aiogoogle:
        sheets = await aiogoogle.discover("sheets", "v4")
        for key, range_name in ranges.items():
            response = await aiogoogle.as_service_account(
                sheets.spreadsheets.values.get(
                    spreadsheetId=settings.google_contacts_spreadsheet_id,
                    range=range_name,
                    majorDimension="ROWS",
                )
            )
            values[key] = response.get("values", []) if isinstance(response, dict) else []

    suppliers = [
        {
            "code": _row_value(row, 1),
            "name": _row_value(row, 2),
            "website": _row_value(row, 3),
            "feed_url": _row_value(row, 4),
            "order_email": _row_value(row, 5).casefold(),
            "tracking_email": _row_value(row, 6).casefold(),
            "telegram": _row_value(row, 7),
            "manager_name": _row_value(row, 8),
            "phone": _row_value(row, 9),
            "order_channel": _row_value(row, 10),
            "tracking_channel": _row_value(row, 11),
            "delivery_service": _row_value(row, 12),
            "priority": _row_value(row, 13),
            "note": _row_value(row, 14),
        }
        for row in values["suppliers"]
        if _active(_row_value(row, 0)) and _row_value(row, 1)
    ]
    managers = [
        {
            "id": _row_value(row, 1),
            "name": _row_value(row, 2),
            "role": _row_value(row, 3),
            "supplier_code": _row_value(row, 4),
            "email": _row_value(row, 5).casefold(),
            "telegram": _row_value(row, 6),
            "phone": _row_value(row, 7),
            "schedule": _row_value(row, 8),
            "region": _row_value(row, 9),
            "priority": _row_value(row, 10),
            "note": _row_value(row, 11),
        }
        for row in values["managers"]
        if _active(_row_value(row, 0)) and _row_value(row, 1)
    ]
    routes = [
        {
            "event": _row_value(row, 1),
            "supplier_code": _row_value(row, 2),
            "channel": _row_value(row, 3),
            "recipient": _row_value(row, 4),
            "copy": _row_value(row, 5),
            "order_status": _row_value(row, 6),
            "template": _row_value(row, 7),
            "priority": _row_value(row, 8),
            "time_from": _row_value(row, 9),
            "time_to": _row_value(row, 10),
            "note": _row_value(row, 11),
        }
        for row in values["routes"]
        if _active(_row_value(row, 0)) and _row_value(row, 1)
    ]
    return {"suppliers": suppliers, "managers": managers, "routes": routes}


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


def _order_documents(order: Any) -> dict[str, str]:
    def money(value: Any) -> str:
        return f"{float(value or 0):,.2f}".replace(",", " ").replace(".", ",")

    number = str(order.order_number or "Замовлення")[:64]
    customer = order.customer or {}
    delivery = order.delivery or {}
    items = order.items or []
    rows = "".join(
        "<tr><td class=\"num\">{}</td><td>{}</td><td class=\"num\">{}</td><td class=\"money\">{}</td><td class=\"money\">{}</td></tr>".format(
            index,
            escape(str(item.get("name") or "")),
            max(1, int(item.get("quantity") or 1)),
            money(item.get("price")),
            money(float(item.get("price") or 0) * max(1, int(item.get("quantity") or 1))),
        )
        for index, item in enumerate(items[:100], 1)
    )
    created_at = order.created_at or datetime.now(timezone.utc)
    created_kyiv = created_at.astimezone(ZoneInfo("Europe/Kyiv"))
    created = created_kyiv.strftime("%d.%m.%Y %H:%M")
    style = """<style>
@page{size:A4;margin:9mm}*{box-sizing:border-box}body{font:12px Arial,sans-serif;color:#17171a;max-width:190mm;margin:0 auto;background:#fff}.sheet{min-height:277mm;display:flex;flex-direction:column}.brand{display:flex;align-items:center;justify-content:space-between;border-bottom:4px solid #ffcc00;padding:0 0 8px}.logo{font-size:24px;font-weight:900;letter-spacing:.8px}.logo b{color:#d99f00}.contact{text-align:right;font-size:10px;line-height:1.45;color:#444}h1{font-size:20px;margin:12px 0 3px}h2{font-size:12px;margin:10px 0 5px;text-transform:uppercase;letter-spacing:.5px}.meta{color:#555;font-size:10px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:5px 14px;margin-top:9px}.field{border-bottom:1px solid #d7d7d7;padding:4px 0;min-height:25px}.field b{display:block;font-size:9px;text-transform:uppercase;color:#666;margin-bottom:2px}table{width:100%;border-collapse:collapse;margin-top:7px;table-layout:fixed}th,td{border:1px solid #d9d9d9;padding:5px 6px;vertical-align:middle;overflow-wrap:anywhere}th{background:#17171a;color:#ffcc00;font-size:9px;text-transform:uppercase}th:nth-child(1),td:nth-child(1){width:7%}th:nth-child(3),td:nth-child(3){width:11%}th:nth-child(4),td:nth-child(4),th:nth-child(5),td:nth-child(5){width:16%}.num{text-align:center}.money{text-align:right;white-space:nowrap}.total{font-size:17px;font-weight:800;text-align:right;margin:8px 0}.note{font-size:10px;line-height:1.4;margin:5px 0}.warning{border-left:4px solid #ffcc00;padding:5px 8px;background:#fff9df}.footer{margin-top:auto;border-top:1px solid #d9d9d9;padding-top:6px;font-size:9px;color:#555;display:flex;justify-content:space-between}.sign{margin-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:30px}.sign div{border-top:1px solid #777;padding-top:3px;font-size:9px;color:#666}@media print{body{print-color-adjust:exact;-webkit-print-color-adjust:exact}.sheet{page-break-after:avoid}}
</style>"""
    header = "<header class=\"brand\"><div class=\"logo\">ALT-CAM <b>SECURITY UA</b></div><div class=\"contact\">alt-cam.net.ua<br>altcam.ua@gmail.com<br>Київ · Вишгород · Київська область</div></header>"
    client_details = (
        f"<div class=\"field\"><b>Клієнт</b>{escape(str(customer.get('name') or 'Не зазначено'))}</div>"
        f"<div class=\"field\"><b>Телефон</b>{escape(str(customer.get('phone') or 'Не зазначено'))}</div>"
        f"<div class=\"field\"><b>Email</b>{escape(str(customer.get('email') or 'Не зазначено'))}</div>"
        f"<div class=\"field\"><b>Доставка</b>{escape(str(delivery.get('label') or delivery.get('type') or 'Не зазначено'))}; {escape(str(delivery.get('city') or ''))}; {escape(str(delivery.get('place') or ''))}</div>"
    )
    table = f"<table><thead><tr><th>№</th><th>Товар або послуга</th><th>К-сть</th><th>Ціна, грн</th><th>Сума, грн</th></tr></thead><tbody>{rows}</tbody></table>"
    total = f"<p class=\"total\">Разом: {money(order.subtotal)} грн</p>"
    prefix = '<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>ALT-CAM</title>'
    suffix = '</div></body></html>'
    comment = escape(str(delivery.get("comment") or "Не зазначено"))
    card = (
        f"{prefix}{style}</head><body><div class=\"sheet\">{header}<h1>Картка замовлення № {escape(number)}</h1>"
        f"<div class=\"meta\">Створено: {created} · Джерело: сайт ALT-CAM</div><div class=\"grid\">{client_details}</div>"
        f"<h2>Склад замовлення</h2>{table}{total}<h2>Коментар клієнта</h2><p class=\"note\">{comment}</p>"
        "<div class=\"grid\"><div class=\"field\"><b>Статус</b>Нове</div><div class=\"field\"><b>Відповідальний менеджер</b>Не призначено</div>"
        "<div class=\"field\"><b>Постачальник і номер</b>Заповнює менеджер</div><div class=\"field\"><b>Трек-номер</b>Заповнює менеджер</div></div>"
        "<p class=\"note warning\"><b>Внутрішній документ.</b> Перед передаванням постачальнику перевірити сумісність, наявність, остаточну ціну, спосіб оплати та дані одержувача.</p>"
        "<div class=\"sign\"><div>Менеджер / підпис / дата</div><div>Перевірка комплектації / дата</div></div>"
        f"<footer class=\"footer\"><span>ALT-CAM Security UA</span><span>Замовлення {escape(number)}</span></footer>{suffix}"
    )
    invoice = (
        f"{prefix}{style}</head><body><div class=\"sheet\">{header}<h1>Рахунок на оплату № {escape(number)}</h1>"
        f"<div class=\"meta\">Дата: {created_kyiv.strftime('%d.%m.%Y')} · Дійсний після підтвердження менеджером</div>"
        "<div class=\"grid\"><div class=\"field\"><b>Постачальник</b>ALT-CAM Security UA</div>"
        "<div class=\"field\"><b>Реквізити постачальника</b>Надаються менеджером у підтвердженому рахунку</div>"
        f"{client_details}</div><h2>Товари та послуги</h2>{table}{total}"
        "<p class=\"note warning\"><b>Проєкт рахунку.</b> Не сплачуйте до підтвердження менеджером. Підтверджений рахунок має містити повне найменування або ПІБ постачальника, код ЄДРПОУ/РНОКПП, IBAN, банк, податковий статус та погоджену суму.</p>"
        "<p class=\"note\"><b>Умови:</b> наявність, сумісність, строк відправлення, вартість доставки та гарантія уточнюються до оплати. Факт оплати підтверджується банківським документом; передання товару — видатковим документом перевізника або продавця.</p>"
        "<div class=\"sign\"><div>Менеджер / підпис / дата</div><div>Погоджено клієнтом / дата</div></div>"
        f"<footer class=\"footer\"><span>alt-cam.net.ua · altcam.ua@gmail.com</span><span>Рахунок {escape(number)}</span></footer>{suffix}"
    )
    return {
        f"Картка замовлення {number}.html": card,
        f"Рахунок {number}.html": invoice,
    }


async def _drive_upsert_html(aiogoogle: Aiogoogle, drive: Any, folder_id: str, name: str, content: str) -> None:
    query = (
        f"'{_drive_query_value(folder_id)}' in parents and "
        f"name = '{_drive_query_value(name)}' and trashed = false"
    )
    found = await aiogoogle.as_service_account(
        drive.files.list(q=query, fields="files(id)", pageSize=1, supportsAllDrives=True, includeItemsFromAllDrives=True)
    )
    files = found.get("files", []) if isinstance(found, dict) else []
    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as stream:
        stream.write(content)
        path = stream.name
    try:
        if files:
            request = drive.files.update(fileId=files[0]["id"], upload_file=path, supportsAllDrives=True)
        else:
            request = drive.files.create(
                json={"name": name, "mimeType": "text/html", "parents": [folder_id]},
                upload_file=path,
                fields="id",
                supportsAllDrives=True,
            )
        await aiogoogle.as_service_account(request)
    finally:
        Path(path).unlink(missing_ok=True)


async def _upload_order_documents_to_folder(order: Any, folder_id: str, settings: Any) -> None:
    service_account = _load_google_service_account(settings)
    credentials = ServiceAccountCreds(scopes=["https://www.googleapis.com/auth/drive"], **service_account)
    async with Aiogoogle(service_account_creds=credentials) as aiogoogle:
        drive = await aiogoogle.discover("drive", "v3")
        for name, content in _order_documents(order).items():
            await _drive_upsert_html(aiogoogle, drive, folder_id, name, content)


async def ensure_order_drive_folder(order: Any) -> str:
    settings = get_settings()
    if not settings.google_drive_folder_id:
        raise IntegrationNotConfigured("google_drive_not_configured")
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
    payload = {
        "kind": "drive_folder",
        "secret": settings.email_relay_secret,
        "root_folder_id": ALT_CAM_DRIVE_ROOT_ID,
        "path": path,
        "order": {
            "number": order.order_number,
            "created_at": created_at.isoformat(),
            "customer": order.customer or {},
            "delivery": order.delivery or {},
            "items": order.items or [],
            "subtotal": float(order.subtotal or 0),
        },
    }
    if settings.email_relay_secret:
        try:
            async with ClientSession() as client:
                async with client.post(DRIVE_FOLDER_RELAY_URL, json=payload, timeout=120) as response:
                    result = await response.json(content_type=None)
                    if response.status >= 400:
                        raise DriveRelayError("drive_relay_http_error")
                    if result.get("status") != "success" or not result.get("url"):
                        message = str(result.get("message") or "")
                        logger.warning(
                            "drive_relay_rejected order=%s message=%s",
                            order.order_number,
                            re.sub(r"[^A-Za-z0-9А-Яа-яІіЇїЄє_ .:()-]", "?", message)[:300],
                        )
                        if message == "unauthorized":
                            raise DriveRelayError("drive_relay_unauthorized")
                        if message == "invalid_drive_path":
                            raise DriveRelayError("drive_relay_invalid_path")
                        raise DriveRelayError("drive_relay_access_error")
            folder_url = str(result["url"])
            folder_match = re.search(r"/folders/([A-Za-z0-9_-]+)", folder_url)
            if not folder_match:
                raise DriveRelayError("drive_relay_invalid_folder_url")
            await _upload_order_documents_to_folder(order, folder_match.group(1), settings)
            logger.info("drive_folder_relay_succeeded order=%s", order.order_number)
            return folder_url
        except Exception:
            logger.exception("drive_folder_relay_failed order=%s", order.order_number)

    service_account = _load_google_service_account(settings)
    credentials = ServiceAccountCreds(
        scopes=["https://www.googleapis.com/auth/drive"],
        **service_account,
    )
    parent_id = ALT_CAM_DRIVE_ROOT_ID
    async with Aiogoogle(service_account_creds=credentials) as aiogoogle:
        drive = await aiogoogle.discover("drive", "v3")
        folder: dict[str, Any] = {}
        for name in path:
            folder = await _drive_folder(aiogoogle, drive, parent_id, name)
            parent_id = folder["id"]
        for name, content in _order_documents(order).items():
            await _drive_upsert_html(aiogoogle, drive, parent_id, name, content)
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


def fetch_supplier_tracking_messages(
    directory_senders: set[str] | None = None,
) -> list[dict[str, str]]:
    settings = get_settings()
    if not settings.imap_user or not settings.imap_password:
        raise IntegrationNotConfigured("imap_not_configured")
    allowed = {
        item.strip().casefold()
        for item in (settings.supplier_email_senders or "").split(",")
        if item.strip()
    }
    allowed.update(directory_senders or set())
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
