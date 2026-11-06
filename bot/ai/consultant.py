"""The consultant loop: system prompt, tools over the real catalog, guards against invented prices,
hand-off triggers. Provider-agnostic: any OpenAI-compatible endpoint (Gemini /v1beta/openai/ by default)."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from bot.ai import catalog, policies
from bot.ai.llm import LLMUnavailable

logger = logging.getLogger("altcam.ai.consultant")
# The consultant never claims to be a human, but does not volunteer that it is a bot either (answers honestly
# when asked). AI_DISCLOSE_BOT=true restores the explicit "🤖 automatic assistant" intro / Business prefix.
INTRO_UK = "Вітаю! Це ALT-CAM Security — допоможу підібрати обладнання та зорієнтую за цінами з каталогу."
INTRO_RU = "Здравствуйте! Это ALT-CAM Security — помогу подобрать оборудование и сориентирую по ценам из каталога."
INTRO_BOT = "Вітаю! Я помічник ALT-CAM 🤖 — автоматичний консультант магазину. Допоможу підібрати обладнання й зорієнтую за цінами з каталогу."
INTRO = INTRO_UK
BUSINESS_PREFIX_BOT = "🤖 Помічник ALT-CAM: "
BUSINESS_PREFIX = ""
_RU_ONLY = re.compile(r"[ыэъё]", re.I)
_UK_ONLY = re.compile(r"[іїєґ]", re.I)
_RU_WORDS = re.compile(r"\b(?:что|как|сколько|нужно|нужна|нужен|здравствуйте|привет|спасибо|камеры|можно|какой|какая|есть)\b", re.I)


def detect_language(text: str) -> str:
    """'ru' or 'uk' (default) from the client's own words."""
    value = text or ""
    ru = len(_RU_ONLY.findall(value)) + 2 * len(_RU_WORDS.findall(value))
    uk = len(_UK_ONLY.findall(value))
    return "ru" if ru > uk else "uk"


def conversation_language(history: list[dict[str, str]]) -> str:
    """Language of the client's latest message; a neutral one ('ок', '4', a link) falls back to earlier messages."""
    for item in reversed(history):
        if item.get("role") != "user":
            continue
        value = item.get("content") or ""
        if _RU_ONLY.search(value) or _UK_ONLY.search(value) or _RU_WORDS.search(value):
            return detect_language(value)
    return "uk"


_MD_LINK = re.compile(r"\[([^\]\n]{1,300})\]\((https?://[^)\s]+)\)")
_MD_BOLD = re.compile(r"(\*\*|__)(.+?)\1", re.S)


def plain_text(text: str) -> str:
    """Telegram (HTML-escaped) and the site widget show plain text: drop markdown bold and [link](url) wrappers."""
    text = _MD_LINK.sub(lambda m: m.group(2) if m.group(1).strip() == m.group(2) else f"{m.group(1)}: {m.group(2)}", text)
    return _MD_BOLD.sub(r"\2", text)


LANGUAGE_RULE = {
    "ru": "\n\nМОВА ЦІЄЇ ВІДПОВІДІ: клієнт пише російською — відповідай ТІЛЬКИ російською мовою (уся відповідь, включно з примітками)."
          " Українські назви з каталогу перекладай: не «камери, відеореєстратор, жорсткий диск, кабель для зовнішніх робіт,"
          " комутатор, разом, кошик, вулиця, приміщення, менеджер підтвердить», а «камеры, видеорегистратор, жёсткий диск,"
          " кабель для наружных работ, коммутатор, итого, корзина, улица, помещение, менеджер подтвердит»."
          " Ответ полностью на русском, без украинских букв і, ї, є, ґ (кроме названий моделей).",
    "uk": "\n\nМОВА ЦІЄЇ ВІДПОВІДІ: українська.",
}


def intro(lang: str = "uk", disclose_bot: bool = False) -> str:
    if disclose_bot:
        return INTRO_BOT
    return INTRO_RU if lang == "ru" else INTRO_UK


def business_prefix(disclose_bot: bool = False) -> str:
    return BUSINESS_PREFIX_BOT if disclose_bot else BUSINESS_PREFIX


HANDOFF_REASONS = {
    "payment": "оплата / рахунок",
    "complex": "складний запит / проєкт / монтаж",
    "angry": "клієнт незадоволений",
    "explicit": "клієнт просить людину",
    "unverified": "відповідь не пройшла перевірку цін",
    "ai_unavailable": "AI недоступний (ліміт/помилка)",
    "other": "інше",
}

SYSTEM_PROMPT = """Ти — «помічник ALT-CAM», консультант магазину систем безпеки ALT-CAM Security UA (alt-cam.net.ua, Київ/Вишгород). Пишеш від імені магазину ALT-CAM.
Ідентичність: ти НЕ людина — ніколи не стверджуй, що ти людина, не вигадуй собі ім'я і не називай себе Сергієм чи менеджером. Сам не повідомляй, що ти бот чи AI. Лише якщо клієнт прямо питає, чи він спілкується з ботом/людиною, — чесно скажи, що ти автоматичний помічник ALT-CAM і за потреби підключиться менеджер.
Мова: відповідай мовою останнього повідомлення клієнта — українською, а якщо клієнт пише російською, то російською. Коротко, по суті, до 700 символів, без markdown-таблиць.

Якщо клієнту потрібна послуга, уточни місто й потрібну роботу. Дай посилання https://alt-cam.net.ua/catalog.html#services: клієнт обирає послугу, додає її до кошика й оформлює замовлення. Не вигадуй фіксованої ціни монтажу. Не кажи, що замовлення оформлене, доки клієнт не отримав підтвердження.
ПРАВИЛА (обов'язкові):
1. Моделі, ціни, характеристики — ТІЛЬКИ з результатів інструментів search_products / build_kit / create_cart_link. Ніколи не вигадуй ціну, знижку, наявність, строки, гарантію. Ціну пиши точно як у полі price_uah, у форматі «1525 грн». Суму комплекту бери з total_uah результату create_cart_link (не рахуй сам). Якщо ціни немає — «ціну уточнить менеджер».
2. Ціна в каталозі не означає наявність. Про наявність — лише після check_stock; якщо результат «перевірити вручну»/невідомо — скажи, що наявність підтвердить менеджер.
3. Оплата, доставка, гарантія, повернення — ТІЛЬКИ текст з get_policy. Нічого не додавай від себе.
4. Для комплекту відеоспостереження спершу уточни (якщо не сказано) кількість камер і вулиця/приміщення, потім build_kit, запропонуй ОДИН збалансований варіант: камери + реєстратор + диск + кабель. PoE-комутатор додавай ТІЛЬКИ якщо build_kit повернув poe_switch_needed=true (реєстратор з достатньою кількістю вбудованих PoE-портів — poe_ports — живить камери сам, окремий комутатор зайвий). Дай посилання create_cart_link. Зазнач, що склад і суму остаточно підтверджує менеджер.
5. Виклич handoff_to_manager, якщо: клієнт просить прийняти оплату/виставити рахунок чи дати реквізити; торг/знижка/опт; нестандартний проєкт або понад 16 камер; скарга, гарантійний випадок, повернення конкретного замовлення; клієнт незадоволений або просить людину; ти не впевнений. Звичайний монтаж та готовність оформити замовлення самі по собі не потребують передачі: допоможи перейти до оформлення.
6. Не називай строки доставки в днях, якщо їх немає в get_policy: строк залежить від перевізника.
7. Не проси і не приймай дані платіжних карток. Не обіцяй строків відповіді менеджера, окрім «найближчим часом у робочий час».
"""

TOOLS: list[dict[str, Any]] = [
    {"type": "function", "function": {
        "name": "search_products", "description": "Пошук товарів у каталозі ALT-CAM (реальні назви та ціни сайту).",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "ключові слова: бренд, модель, тип, мегапікселі"},
            "category": {"type": "string", "description": "необов'язково: напр. 'Камери відеоспостереження', 'Відеореєстратори та накопичувачі', 'Мережеве обладнання', 'Кабельна продукція', 'Ajax та охоронна сигналізація'"},
            "max_price": {"type": "number"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "check_stock", "description": "Перевірити наявність у постачальника за id товарів каталогу.",
        "parameters": {"type": "object", "properties": {"ids": {"type": "array", "items": {"type": "string"}}}, "required": ["ids"]}}},
    {"type": "function", "function": {
        "name": "build_kit", "description": "Кандидати для комплекту IP-відеоспостереження з каталогу (камери, NVR, HDD, PoE-комутатор, кабель).",
        "parameters": {"type": "object", "properties": {
            "cameras": {"type": "integer"}, "resolution_mp": {"type": "integer"}, "outdoor": {"type": "boolean"},
            "cable_m": {"type": "integer"}, "brand": {"type": "string"}}, "required": ["cameras"]}}},
    {"type": "function", "function": {
        "name": "create_cart_link", "description": "Посилання на кошик alt-cam.net.ua з обраними товарами (id з каталогу).",
        "parameters": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"}, "qty": {"type": "integer"}}, "required": ["id"]}}}, "required": ["items"]}}},
    {"type": "function", "function": {
        "name": "get_policy", "description": "Опубліковані правила магазину.",
        "parameters": {"type": "object", "properties": {"topic": {"type": "string", "enum": list(policies.TOPICS)}}, "required": ["topic"]}}},
    {"type": "function", "function": {
        "name": "handoff_to_manager", "description": "Передати розмову менеджеру (людині).",
        "parameters": {"type": "object", "properties": {
            "reason": {"type": "string", "enum": [k for k in HANDOFF_REASONS if k not in {"unverified", "ai_unavailable"}]},
            "summary": {"type": "string", "description": "1-2 речення для менеджера: що хоче клієнт"}}, "required": ["reason"]}}},
]

_PAYMENT = re.compile(r"реквізит|рахунок на оплат|виставт\w* рахун|куди (?:оплат|переказ|плат)|як (?:мені )?(?:оплатити|сплатити)|"
                      r"готов\w* (?:оплатит|сплатит)|оплачу|номер карт|iban|реквизит|счет на оплат|как оплатить", re.I)
_EXPLICIT = re.compile(r"(?:покличте|покличи|позвіть|з['’]єднайте|соедините|позовите|позвать|дайте|хочу|можна|можно|"
                       r"потрібен|потрібна|нужен|треба|поговорити|поговорить|спілкуватися|говорити)\s+(?:з\s+|с\s+)?(?:\w+\s+)?"
                       r"(?:менеджер|людин|оператор|человек|сергі)|живий менеджер|живою людиною|живым человеком|"
                       r"зателефонуйте|подзвоніть|передзвоніть|перезвоніть|позвоните|перезвоните", re.I)
_ANGRY = re.compile(r"жах|обман|шахра|ганьба|верніть гроші|верните деньги|скарг|жалоб|обурен|хамств|безобраз|"
                    r"\bбля|сука|пізд|пизд|хуй|хуё|нахер|достали|задовбал", re.I)
# A price: '1525', '17 464', '17\u00a0464', '17.464' (thousands groups never span a line break) + optional kopecks.
_PRICE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[ \u00a0\u202f\u2009.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)"
                    r"[ \u00a0\u202f\u2009]*(?:грн|₴|uah|гривн\w*|гривен\w*|гривень)", re.I)
_CART_URL = re.compile(r"https?://[^\s)\]\"'<>]*catalog\.html\?cart=[A-Za-z0-9_:,%-]+")
_TOTAL_PRICE = re.compile(r"((?:разом|усього|всього|загалом|сума|итого|всего|сумма|в сумме|total)\b[^\d\n]{0,30})("
                          + _PRICE.pattern + ")", re.I)


def detect_handoff(text: str) -> str | None:
    """Cheap pre-LLM triggers (saves free-tier quota and never lets the model handle payment or anger)."""
    value = text or ""
    if _ANGRY.search(value) or value.count("!") >= 4 or (len(value) > 12 and sum(c.isupper() for c in value) > 0.7 * sum(c.isalpha() for c in value)):
        return "angry"
    if _PAYMENT.search(value):
        return "payment"
    if _EXPLICIT.search(value):
        return "explicit"
    return None


_DURATION = re.compile(r"\b\d+(?:\s*[–-]\s*\d+)?\s*(?:робоч\w*\s+)?(?:дн\w*|день|доб\w*|тиж\w*|годин\w*)", re.I)


def strip_unverified_durations(text: str, sources: str) -> str:
    """Drop sentences promising delivery/stock times that do not appear in tool outputs (published policy)."""
    lines = []
    for line in text.split("\n"):  # keep the model's line breaks (lists, 'Итого' line)
        kept = []
        for sentence in re.split(r"(?<=[.!?])[ \t]+", line):
            claims = [m.group(0) for m in _DURATION.finditer(sentence)]
            if claims and not all(c.lower() in sources.lower() for c in claims):
                continue
            kept.append(sentence)
        if kept or not line.strip():
            lines.append(" ".join(kept))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _num(raw: str) -> float | None:
    """'17 464' / '17\u00a0464' / '17.464' / '17,464' / '1 525,50' -> float (thousands separators dropped)."""
    cleaned = re.sub(r"[\s\u00a0\u202f\u2009]", "", raw or "")
    match = re.fullmatch(r"(\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,](\d{1,2}))?", cleaned)
    if match:
        whole = re.sub(r"[.,]", "", match.group(1))
        return float(f"{whole}.{match.group(2)}" if match.group(2) else whole)
    try:
        return float(cleaned.replace(",", "."))
    except ValueError:
        return None


def _fmt_uah(value: float) -> str:
    return f"{int(round(value))}" if abs(value - round(value)) < 0.005 else f"{value:.2f}"


def _allowed(value: float | None, allowed: set[float]) -> bool:
    return value is not None and any(abs(value - a) < 0.51 for a in allowed)


def _price_ok(raw: str, allowed: set[float]) -> bool:
    return _allowed(_num(raw), allowed)


def unverified_prices(text: str, allowed: set[float]) -> list[str]:
    """Prices in the answer that did not come from tool results (sums of up to the cart total are allowed via tools)."""
    return [m.group(0).strip() for m in _PRICE.finditer(text or "") if not _price_ok(m.group(1), allowed)]


def fix_total_lines(text: str, allowed: set[float], total: float | None) -> str:
    """The model often re-adds the kit itself (17464 vs the cart's 18389). The price right after 'Разом/Итого/Сумма'
    is replaced by the real cart total from create_cart_link when it is unverified; other prices go to the guard."""
    if total is None:
        return text

    def swap(match: re.Match) -> str:
        price = match.group(2)
        if _price_ok(_PRICE.match(price).group(1), {total}):
            return match.group(0)
        return f"{match.group(1)}{_fmt_uah(total)} грн"
    return _TOTAL_PRICE.sub(swap, text)


def cart_urls(text: str) -> list[str]:
    return _CART_URL.findall(text or "")


def cart_items_from_url(url: str) -> list[dict[str, Any]]:
    """'...catalog.html?cart=a:2,b:1' -> [{'id': 'a', 'qty': 2}, {'id': 'b', 'qty': 1}]."""
    from urllib.parse import parse_qs, urlsplit

    raw = (parse_qs(urlsplit(url).query).get("cart") or [""])[0]
    items = []
    for part in raw.split(","):
        pid, _, qty = part.partition(":")
        if pid:
            items.append({"id": pid, "qty": int(qty) if qty.isdigit() else 1})
    return items


def _kit_totals(kit: Any, sink: set[float]) -> None:
    """Totals of every 'one option per component' kit from build_kit (the model sums the kit before the cart)."""
    if not isinstance(kit, dict) or not isinstance(kit.get("components"), dict):
        return
    groups = []
    for rows in kit["components"].values():
        options = [float(r["price_uah"]) * int(r.get("qty") or 1) for r in rows or []
                   if isinstance(r, dict) and isinstance(r.get("price_uah"), (int, float))]
        if options:
            groups.append(options[:3] + [0.0])  # 0.0: component left out (e.g. the client already has a disk)
    sums = {0.0}
    for options in groups[:6]:
        sums = {a + b for a in sums for b in options}
    sink.update(v for v in sums if v > 0)


@dataclass
class ConsultResult:
    text: str | None
    handoff: str | None = None
    handoff_summary: str | None = None
    cart_url: str | None = None
    cart_total: float | None = None
    tools_used: list[str] = field(default_factory=list)


StockChecker = Callable[[list[dict[str, Any]]], Awaitable[list[dict[str, str]]]]


async def _default_stock(items):
    from bot.integrations.supplier_stock import check_items

    return await check_items(items)


def _collect_prices(value: Any, sink: set[float]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"price_uah", "total_uah"} and isinstance(item, (int, float)):
                sink.add(float(item))
                if key == "price_uah" and isinstance(value.get("qty"), int):
                    sink.add(float(item) * value["qty"])
            else:
                _collect_prices(item, sink)
    elif isinstance(value, list):
        for item in value:
            _collect_prices(item, sink)


class Consultant:
    def __init__(self, llm, *, overrides: dict[str, float] | None = None, stock_checker: StockChecker | None = None,
                 site_origin: str = "https://alt-cam.net.ua", max_rounds: int = 4, product_catalog=None):
        self.llm, self.overrides, self.stock_checker = llm, overrides or {}, stock_checker or _default_stock
        self.site_origin, self.max_rounds, self.catalog = site_origin, max_rounds, product_catalog

    async def _tool(self, name: str, args: dict[str, Any], result: ConsultResult) -> Any:
        result.tools_used.append(name)
        if name == "search_products":
            return {"products": catalog.search(str(args.get("query", "")), category=args.get("category"),
                                               max_price=args.get("max_price"), limit=int(args.get("limit") or 6),
                                               overrides=self.overrides, catalog=self.catalog)}
        if name == "check_stock":
            ids = [str(x) for x in (args.get("ids") or [])][:10]
            rows = await self.stock_checker([{"id": pid} for pid in ids])
            return {"stock": [{"id": r.get("id"), "stock": r.get("stock")} for r in rows]}
        if name == "build_kit":
            return catalog.build_kit(int(args.get("cameras") or 1), resolution_mp=args.get("resolution_mp"),
                                     outdoor=bool(args.get("outdoor", True)), cable_m=args.get("cable_m"),
                                     brand=args.get("brand"), overrides=self.overrides, catalog=self.catalog)
        if name == "create_cart_link":
            link = catalog.cart_link(args.get("items") or [], origin=self.site_origin, overrides=self.overrides, catalog=self.catalog)
            if link.get("ok"):
                result.cart_url = link["url"]
                result.cart_total = link.get("total_uah")
            return link
        if name == "get_policy":
            return policies.policy(str(args.get("topic", "")))
        if name == "handoff_to_manager":
            result.handoff = args.get("reason") if args.get("reason") in HANDOFF_REASONS else "other"
            result.handoff_summary = str(args.get("summary") or "")[:500]
            return {"ok": True, "note": "Менеджера повідомлено. Коротко скажи клієнту, що передаєш питання менеджеру."}
        return {"error": "unknown_tool"}

    def _cart(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return catalog.cart_link(items, origin=self.site_origin, overrides=self.overrides, catalog=self.catalog)

    def _verify_cart_urls(self, text: str, result: ConsultResult, allowed: set[float]) -> str:
        """Cart links written by the model itself (e.g. reused from an earlier turn) are rebuilt from the catalog:
        valid ones become the canonical link (and cart_url), links without any valid item are removed."""
        for url in dict.fromkeys(cart_urls(text)):
            link = self._cart(cart_items_from_url(url))
            if not link.get("ok"):
                text = text.replace(url, "").replace("🛒 :", "").rstrip()
                continue
            _collect_prices(link, allowed)
            text = text.replace(url, link["url"])
            if not result.cart_url:
                result.cart_url, result.cart_total = link["url"], link.get("total_uah")
        return text

    def _history_prices(self, history: list[dict[str, str]], allowed: set[float]) -> None:
        """Prices the consultant itself quoted earlier (the widget re-sends the conversation) are accepted again only
        when they are real: a catalog price or a line/total of a cart link rebuilt from the catalog."""
        quoted = [m.group(1) for item in history if item["role"] == "assistant" for m in _PRICE.finditer(item["content"])]
        for item in history:
            if item["role"] == "assistant":
                for url in cart_urls(item["content"]):
                    link = self._cart(cart_items_from_url(url))
                    if link.get("ok"):
                        _collect_prices(link, allowed)
        if not quoted:
            return
        try:
            source = self.catalog if self.catalog is not None else catalog.products()
        except (OSError, ValueError):
            return
        real = {float(v) for v in (catalog.price_of(p, self.overrides) for p in source.values()) if v is not None}
        for raw in quoted:
            value = _num(raw)
            if _allowed(value, real):
                allowed.add(value)

    async def reply(self, history: list[dict[str, str]]) -> ConsultResult:
        """history: [{'role': 'user'|'assistant', 'content': str}], last item is the client's message."""
        last = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        trigger = detect_handoff(last)
        if trigger:
            return ConsultResult(text=None, handoff=trigger, handoff_summary=last[:300])
        lang = conversation_language(history)
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT + LANGUAGE_RULE[lang]},
                                          *history[-14:]]
        result = ConsultResult(text=None)
        allowed: set[float] = set()
        sources: list[str] = []
        for item in history:  # numbers the client named himself (budget etc.) may be echoed back
            if item["role"] == "user":
                allowed.update(v for v in (_num(m.group(1)) for m in _PRICE.finditer(item["content"])) if v is not None)
                allowed.update(float(x) for x in re.findall(r"\b\d{3,6}\b", item["content"]))
        self._history_prices(history, allowed)
        try:
            for _ in range(self.max_rounds):
                message = await self.llm.chat(messages, TOOLS)
                calls = message.get("tool_calls") or []
                if not calls:
                    result.text = (message.get("content") or "").strip() or None
                    break
                messages.append({k: v for k, v in message.items() if v is not None})  # keep provider extras verbatim
                for call in calls:
                    function = call.get("function") or {}
                    try:
                        args = json.loads(function.get("arguments") or "{}")
                    except ValueError:
                        args = {}
                    output = await self._tool(function.get("name", ""), args if isinstance(args, dict) else {}, result)
                    _collect_prices(output, allowed)
                    if function.get("name") == "build_kit":
                        _kit_totals(output, allowed)
                    sources.append(json.dumps(output, ensure_ascii=False))
                    messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": json.dumps(output, ensure_ascii=False)[:12000]})
            else:
                message = await self.llm.chat(messages + [{"role": "user", "content": "Дай коротку відповідь клієнту без нових інструментів."}], None)
                result.text = (message.get("content") or "").strip() or None
        except LLMUnavailable as exc:
            logger.warning("consultant_llm_unavailable (%s)", exc.reason)
            return ConsultResult(text=None, handoff="ai_unavailable", handoff_summary=last[:300], tools_used=result.tools_used)
        if result.text:
            result.text = plain_text(result.text)
            result.text = strip_unverified_durations(result.text, " ".join(sources)) or None
        if result.text:
            result.text = self._verify_cart_urls(result.text, result, allowed)
            result.text = fix_total_lines(result.text, allowed, result.cart_total)
            bad = unverified_prices(result.text, allowed)
            if bad:
                logger.warning("consultant_unverified_prices %s", bad)
                return ConsultResult(text=None, handoff="unverified", handoff_summary=last[:300], cart_url=result.cart_url,
                                    cart_total=result.cart_total, tools_used=result.tools_used)
            if result.cart_url and result.cart_url not in result.text:
                result.text += f"\n\n🛒 {'Корзина' if lang == 'ru' else 'Кошик'}: {result.cart_url}"
        elif not result.handoff:
            result.handoff = "other"
        return result
