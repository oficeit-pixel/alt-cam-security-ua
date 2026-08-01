from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-03-60-day-matrix"
PLAN_PATH = PLAN_DIR / "plan.json"
DRAFTS_PATH = PLAN_DIR / "posting-drafts.json"
OUT_DIR = PLAN_DIR / "media" / "premium-grok-prompts"
INDEX_PATH = OUT_DIR / "README.md"


STYLE_REFERENCE = """Стиль як у прикладах ALT-CAM:
- преміальний темний рекламний пост, чорний/графітовий фон, жовтий #FFCC00 як акцент;
- фотореалістичний об’єкт: квартира, будинок, під’їзд, ворота, офіс, склад або магазин;
- великий реалістичний продукт у кадрі: камера, Ajax Hub, датчики, відеодомофон, електрозамок, NVR, UPS;
- логотип ALT-CAM Security UA зверху ліворуч;
- великий контрастний заголовок білим і жовтим;
- праворуч або в центрі — продукт/сцена, ліворуч — заголовок і список переваг;
- внизу велика жовта CTA-кнопка “НАПИШІТЬ У ПОВІДОМЛЕННЯ …”;
- додаткові блоки: комплектація, переваги, для кого підходить, географія;
- вигляд дорогий, чистий, технологічний, без мультяшності.
"""


NEGATIVE = """Не робити:
- мультяшні іконки, прості пласкі схеми, дитячий стиль;
- випадкові логотипи брендів, зайві водяні знаки;
- зброю, кров, поліцію, військову естетику;
- хаотичний дрібний текст, криві літери, русизм у фінальному українському тексті;
- надто жовтий фон — жовтий тільки як акцент і CTA.
"""


SCENES = {
    "КАМЕРА": "сучасний приватний будинок увечері, фасад і двір, крупно біла bullet/IP камера ALT-CAM на стіні, окремі міні-вікна з помилками: нічого не видно, роутер без резерву, номер авто розмитий",
    "ТЕХНОЛОГІЯ": "нічний двір або парковка, порівняння звичайної нічної картинки і ColorVu/AcuSense/WizSense, камера крупним планом, чистий security-tech інтерфейс",
    "МОНТАЖ": "реальний монтажник ALT-CAM у чорній брендованій формі на об’єкті, акуратно прокладає кабель і встановлює камеру, поруч чистий щит або інструменти",
    "КОМПЛЕКТ": "повний комплект відеоспостереження на столі: 4 камери, NVR, HDD, PoE-комутатор, бухта кабелю, UPS, фон приватного будинку або офісу",
    "РЕЗЕРВ": "блекаут у квартирі або приватному будинку, темна кімната з працюючим роутером, UPS/LiFePO4, Ajax і камери продовжують працювати",
    "ДОСТУП": "смартфон із додатком Hik-Connect/DMSS/Imou, власник керує доступом, поруч камера і роутер, відчуття безпечного контролю",
    "AJAX": "преміальна квартира, вхідні двері, Ajax Hub, датчики руху/відкриття, сирена, клавіатура, смартфон із додатком, усе в чорному мінімалістичному стилі",
    "ДОМОФОН": "сучасні ворота приватного будинку або під’їзд, відеопанель домофона на стовпі, внутрішній монітор і смартфон з відеовикликом, людина на екрані",
    "СКУД": "офісний вхід або склад, електрозамок, зчитувач карт, клавіатура, турнікет/двері, співробітник прикладає картку",
    "БІЗНЕС": "магазин або офіс після закриття, камери, домофон, контроль доступу, акуратний серверний куток, власник дивиться камери зі смартфона",
    "ДВІР": "двір приватного будинку, ворота, авто, периметр, камера на фасаді, тепле світло у вікнах, акцент на огляді території",
    "ТРИВОГА": "ситуація хибної тривоги, власник отримує push-повідомлення, Ajax датчики і камера допомагають перевірити подію",
    "ПІДЇЗД": "сучасний під’їзд ЖК, домофонна панель, електрозамок, камера, чиста навігація для мешканців",
    "АУДИТ": "інженер ALT-CAM перевіряє об’єкт з планшетом, план-схема камер, лазерна рулетка, професійний аудит безпеки",
    "АРХІВ": "аккуратний серверний щит, NVR, HDD, PoE-комутатор, UPS, підписані кабелі, чистий технічний монтаж",
}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def extract(label: str, caption: str) -> str:
    pattern = rf"{re.escape(label)}:\s*(.*?)(?:\n\n[A-ЯІЇЄҐA-Z💰🤖🌐📍#][^\n]*:|\n\n💰|\n\n🤖|\n\n#|$)"
    match = re.search(pattern, caption, flags=re.S)
    if match:
        return clean(match.group(1))
    return ""


def headline(day: dict) -> str:
    title = day["tiktok_shorts_reels"]["visual_hook_first_3s"]
    title = title.replace("Міф: ", "").replace("Правда: ", "").replace("Помилка: ", "")
    return title


def cta_word(day: dict) -> str:
    mapping = {
        "КАМЕРА": "КАМЕРА",
        "ТЕХНОЛОГІЯ": "КАМЕРА",
        "МОНТАЖ": "МОНТАЖ",
        "КОМПЛЕКТ": "КОМПЛЕКТ",
        "РЕЗЕРВ": "РЕЗЕРВ",
        "ДОСТУП": "ДОСТУП",
        "AJAX": "AJAX",
        "ДОМОФОН": "ДОМОФОН",
        "СКУД": "ДОСТУП",
        "БІЗНЕС": "БІЗНЕС",
        "ДВІР": "ДВІР",
        "ТРИВОГА": "AJAX",
        "ПІДЇЗД": "ДОМОФОН",
        "АУДИТ": "АУДИТ",
        "АРХІВ": "АРХІВ",
    }
    return mapping.get(day["keyword"], day["keyword"])


def benefits(day: dict, caption: str) -> list[str]:
    keyword = day["keyword"]
    base = {
        "AJAX": ["Ajax Hub", "Датчики руху", "Датчики відкриття", "Сирена", "Клавіатура або брелок", "Керування через застосунок"],
        "ДОМОФОН": ["Виклик на смартфон", "Двосторонній зв’язок", "Відкриття дверей/хвіртки", "Запис фото та відео", "Інтеграція з електрозамком"],
        "КАМЕРА": ["Камери відеоспостереження", "Нічне бачення", "Архів запису", "Віддалений перегляд", "Резервне живлення"],
        "ТЕХНОЛОГІЯ": ["ColorVu / AcuSense", "Розпізнавання людей/авто", "Краще нічне зображення", "Менше хибних тривог"],
        "РЕЗЕРВ": ["UPS або LiFePO4", "Роутер і ONU", "PoE/NVR", "Ajax і критичні датчики"],
        "СКУД": ["Картки та брелоки", "Кодова клавіатура", "Електрозамок", "Журнал входів", "Права доступу"],
        "АРХІВ": ["NVR", "HDD від 2 ТБ", "PoE-комутатор", "UPS", "Підписані кабелі"],
    }
    if keyword in base:
        return base[keyword]
    spec = extract("Специфікація", caption)
    if spec:
        return [clean(part) for part in re.split(r",|;", spec)[:5] if clean(part)]
    return ["Акуратний монтаж", "Налаштування під ключ", "Підбір під об’єкт", "Підтримка після встановлення"]


def render_prompt(day: dict, draft: dict) -> str:
    caption = draft.get("caption", "")
    problem = extract("Проблема для об’єкта “" + day["object_type"] + "”", caption) or extract("Проблема", caption)
    solution = extract("Рішення ALT-CAM", caption)
    spec = extract("Специфікація", caption)
    price = ""
    price_match = re.search(r"💰\s*(.*?)(?:\n|$)", caption)
    if price_match:
        price = clean(price_match.group(1))
    scene = SCENES.get(day["keyword"], SCENES["КАМЕРА"])
    cta = cta_word(day)
    benefit_list = benefits(day, caption)
    benefit_lines = "\n".join(f"- {item}" for item in benefit_list)
    slide_title = headline(day)

    return f"""# День {day['day']:02d} — premium Grok prompt

Тема: {day['topic']}
Платформи: Facebook / Instagram / TikTok / Threads / Telegram / YouTube
Формат для поста: 1:1, 1536×1536 або 2048×2048.
Формат для Reels/Stories: 9:16, 1080×1920, з тим самим стилем.

## Style reference

{STYLE_REFERENCE}

## FULL POSTER PROMPT

Create a premium photorealistic Ukrainian advertising poster for ALT-CAM Security UA, in the same visual direction as the provided references: dark luxury security-tech design, realistic products and real environment, black/graphite background, yellow #FFCC00 accents, clean white/yellow typography, modern infographic blocks.

Scene:
{scene}

Main product / service:
{day['category']} для об’єкта “{day['object_type']}”.
Brands to imply naturally where relevant: {day['brands']}. Do not place random third-party logos unless the product clearly belongs to that ecosystem.

Composition:
- top left: ALT-CAM Security UA logo area;
- left side: large bold Ukrainian headline;
- center/right: photorealistic product and real object scene;
- one side column with 4–6 benefit items and small yellow line icons;
- bottom: large yellow CTA button with black chat icon;
- bottom strip: trust icons: “НАДІЙНІ РІШЕННЯ”, “АКУРАТНИЙ МОНТАЖ”, “ПІДТРИМКА ТА СЕРВІС”, “КИЇВ ТА КИЇВСЬКА ОБЛАСТЬ”.

Text to place exactly, Ukrainian:
Headline:
“{slide_title}”

Benefit list:
{benefit_lines}

Problem insight:
“{problem or day['tiktok_shorts_reels']['audio_hook']}”

Solution:
“{solution or 'Підберемо, встановимо та налаштуємо систему під ваш сценарій життя.'}”

Specs:
“{spec or day['brands']}”

Price note:
“{price or 'Вартість залежить від об’єкта та комплектації.'}”

CTA button:
“НАПИШІТЬ У ПОВІДОМЛЕННЯ «{cta}»”
Small CTA subtext:
“Підкажемо, що краще встановити саме для вашого об’єкта”

Location:
“КИЇВ • ВИШГОРОД • КИЇВСЬКА ОБЛАСТЬ”

Visual quality:
photorealistic product photography, cinematic dark interior/exterior lighting, realistic shadows, premium commercial retouching, sharp readable layout, balanced spacing, high contrast, no cartoon style.

{NEGATIVE}

## BACKGROUND ONLY PROMPT — safer for clean Ukrainian text

Create only the photorealistic background and product composition for an ALT-CAM Security UA premium advertising poster. Do NOT add any text, letters, numbers, logos, UI captions, icons, or CTA button. Leave clean dark negative space for later text overlay.

Scene:
{scene}

Composition:
- dark premium security-tech atmosphere;
- main product/service visual on center/right;
- realistic object in background: {day['object_type']};
- black/graphite surfaces, warm practical lights, yellow #FFCC00 accents only as subtle light/glow;
- leave left side and bottom area empty for typography and CTA;
- high-end commercial photography, sharp realistic details.

Avoid all text and fake logos. No watermarks.

## Overlay text for Canva/Figma/Photoshop

Logo: ALT-CAM Security UA

Headline:
{slide_title}

Benefits:
{benefit_lines}

Problem:
{problem or day['tiktok_shorts_reels']['audio_hook']}

Solution:
{solution or 'Підберемо, встановимо та налаштуємо систему під ваш сценарій життя.'}

CTA:
НАПИШІТЬ У ПОВІДОМЛЕННЯ «{cta}»

Footer:
НАДІЙНІ РІШЕННЯ • АКУРАТНИЙ МОНТАЖ • ПІДТРИМКА ТА СЕРВІС • КИЇВ ТА КИЇВСЬКА ОБЛАСТЬ
"""


def prompt_filename(day: dict) -> str:
    old_name = Path(day["media"]["generation_prompt"]).name
    slug = old_name.replace("-media-prompt.md", "")
    return f"{slug}-premium-grok-prompt.md"


def main() -> int:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    drafts = json.loads(DRAFTS_PATH.read_text(encoding="utf-8"))["posts"]
    drafts_by_id = {post["id"]: post for post in drafts}
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    index = [
        "# ALT-CAM — premium Grok prompts",
        "",
        "Ці промти зроблені під формат попередніх рекламних креативів ALT-CAM: фотореалістичний об’єкт, великий товар, багато корисних блоків, жовта CTA-кнопка.",
        "",
        "Рекомендація: для максимально чистого українського тексту використовуйте `BACKGROUND ONLY PROMPT`, а текст накладайте окремо у Canva/Figma/Photoshop.",
        "",
        "| День | Тема | Prompt |",
        "|---:|---|---|",
    ]
    for day in plan["days"]:
        post_id = f"altcam-60d-{day['date']}-d{day['day']:02d}"
        draft = drafts_by_id.get(post_id, {})
        path = OUT_DIR / prompt_filename(day)
        path.write_text(render_prompt(day, draft), encoding="utf-8")
        rel = path.relative_to(OUT_DIR).as_posix()
        index.append(f"| {day['day']} | {day['topic']} | [{path.name}]({rel}) |")

    INDEX_PATH.write_text("\n".join(index) + "\n", encoding="utf-8")
    print(INDEX_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
