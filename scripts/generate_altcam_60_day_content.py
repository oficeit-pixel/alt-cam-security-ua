from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = "https://t.me/alt_cam_bot"
BOT_HANDLE = "@alt_cam_bot"
SITE = "https://alt-cam.net.ua"
LOCATION = "Київ • Вишгород • Київська область • Україна"
HASHTAGS = "#відеоспостереженнякиїв #монтажкамер #системибезпеки #Ajax #Hikvision #Dahua #AltCam #Київ #Вишгород"


TOPICS = [
    {
        "topic": "5 помилок монтажу камер, через які не видно обличчя",
        "category": "відеоспостереження",
        "brand": "Hikvision / Dahua / Uniview",
        "hook": "Камера є. Доказів — нуль.",
        "problem": "Камери встановлені, але обличчя, номер авто або момент події не читаються.",
        "solution": "Починаємо зі схеми огляду, висоти, нічної сцени, архіву та резерву, а не з випадкової покупки камери.",
        "spec": "IP-камери 4 Мп, AcuSense/SMD, PoE, NVR, HDD від 2 ТБ, UPS для мережі.",
        "price": "Аудит системи — від 1 500 ₴; монтаж камери — від 2 500 ₴.",
        "keyword": "КАМЕРА",
    },
    {
        "topic": "AcuSense, ColorVu та WizSense простими словами",
        "category": "технології камер",
        "brand": "Hikvision / Dahua",
        "hook": "ColorVu чи AcuSense? Це не одне й те саме.",
        "problem": "Клієнти часто переплачують за назву технології, не розуміючи, яку задачу вона реально вирішує.",
        "solution": "Підбираємо технологію під сцену: ніч, рух людей/авто, засвіт, дальність, архів і бюджет.",
        "spec": "Hikvision ColorVu/AcuSense або Dahua WizSense, 4 Мп, PoE, архів 14–30 днів.",
        "price": "Комплект на 4 камери з монтажем — орієнтовно від 24 900 ₴.",
        "keyword": "ТЕХНОЛОГІЯ",
    },
    {
        "topic": "До/після: акуратне кабелювання і серверний щит",
        "category": "соціальний доказ",
        "brand": "ALT-CAM",
        "hook": "Монтаж, який не соромно показати.",
        "problem": "Після швидкого монтажу залишаються висячі кабелі, хаос у щиті та незрозуміло, що за що відповідає.",
        "solution": "Маркуємо лінії, збираємо охайний щит, перевіряємо доступ, архів, резерв і навчаємо клієнта.",
        "spec": "Кабель UTP/FTP, PoE-комутатор, NVR, UPS, маркування, фотофіксація після монтажу.",
        "price": "Акуратне доопрацювання системи — від 3 900 ₴.",
        "keyword": "МОНТАЖ",
    },
    {
        "topic": "Комплект відеоспостереження на 4 камери під ключ",
        "category": "готовий комплект",
        "brand": "Hikvision / Dahua / Uniview",
        "hook": "4 камери — це ще не вся система.",
        "problem": "У дешевій пропозиції часто не враховані диск, кабель, PoE, налаштування, резерв і нормальна здача об’єкта.",
        "solution": "Рахуємо повний комплект під задачу, а не просто коробку з камерами.",
        "spec": "4 IP-камери 4 Мп, NVR, HDD 2 ТБ, PoE, кабель, монтаж, смартфон, базовий інструктаж.",
        "price": "Комплект з базовим монтажем — від 24 900 ₴.",
        "keyword": "КОМПЛЕКТ",
    },
    {
        "topic": "Блекаут: що вимкнеться першим — камери, роутер чи Ajax",
        "category": "резервне живлення",
        "brand": "Ajax / UPS / LiFePO4",
        "hook": "Світло зникло. Безпека теж?",
        "problem": "Камери можуть мати живлення, але роутер або ONU вимикаються — і віддаленого доступу немає.",
        "solution": "Резервуємо весь ланцюг: камери, NVR, PoE, роутер, ONU, Ajax і критичні датчики.",
        "spec": "UPS або LiFePO4, розрахунок у Wh, захист АКБ, окрема лінія для мережевого обладнання.",
        "price": "Базовий резерв для мережі та безпеки — від 8 900 ₴.",
        "keyword": "РЕЗЕРВ",
    },
    {
        "topic": "Безпечне налаштування Hik-Connect, DMSS та Imou Life",
        "category": "віддалений доступ",
        "brand": "Hikvision / Dahua / Imou",
        "hook": "Не віддавайте пароль від камер назавжди.",
        "problem": "Один пароль передають усім користувачам, а власник потім не контролює, хто має доступ.",
        "solution": "Створюємо акаунт власника, вмикаємо 2FA, додаємо користувачів через запрошення й обмежуємо права.",
        "spec": "Hik-Connect, DMSS, Imou Life, 2FA, окремі користувачі, push-сповіщення, перевірка оновлень.",
        "price": "Налаштування віддаленого доступу та навчання — від 1 200 ₴.",
        "keyword": "ДОСТУП",
    },
    {
        "topic": "Ajax + камери: як зрозуміти, що сталося під час тривоги",
        "category": "Ajax",
        "brand": "Ajax / Hikvision / Dahua / Uniview",
        "hook": "Тривога є. А що саме сталося?",
        "problem": "Окремі системи дають багато сповіщень, але користувач не розуміє, це загроза чи хибна тривога.",
        "solution": "Поєднуємо сценарій Ajax, візуальну перевірку камерами, сирену, резерв і зрозумілу реакцію.",
        "spec": "Ajax Hub, MotionProtect/DoorProtect, сирена, IP-камери, NVR, UPS.",
        "price": "Комплекс Ajax + відеоспостереження — від 34 900 ₴.",
        "keyword": "AJAX",
    },
    {
        "topic": "Відеодомофон для будинку: бачити гостя і відкривати зі смартфона",
        "category": "домофонія",
        "brand": "Dahua / Hikvision / Imou",
        "hook": "Хто за дверима — має бути видно, а не вгадано.",
        "problem": "Старий домофон шумить, не показує гостя або не дає відкрити хвіртку дистанційно.",
        "solution": "Ставимо IP-панель, монітор, електрозамок, живлення і налаштовуємо виклик на смартфон.",
        "spec": "IP-домофон, виклична панель, монітор, електрозамок, блок живлення, резерв за потреби.",
        "price": "Комплект домофонії з монтажем — від 18 900 ₴.",
        "keyword": "ДОМОФОН",
    },
    {
        "topic": "СКУД для офісу: як прибрати хаос із ключами",
        "category": "контроль доступу",
        "brand": "Dahua / Hikvision / U-Prox",
        "hook": "Хто досі має ключ від вашого офісу?",
        "problem": "Ключі передаються між співробітниками, а після звільнення доступ може залишитися.",
        "solution": "Встановлюємо електрозамок, контролер, зчитувач і керуємо доступами картками або через систему.",
        "spec": "Контролер, зчитувач, електрозамок, кнопка виходу, БЖ, журнал подій.",
        "price": "Базовий контроль доступу на одну дверь — від 12 900 ₴.",
        "keyword": "СКУД",
    },
    {
        "topic": "Камера для магазину: каса, вхід і сліпі зони",
        "category": "бізнес",
        "brand": "Hikvision / Dahua / Uniview",
        "hook": "Камера дивиться не туди — гроші теж зникають у тумані.",
        "problem": "Зал видно, а касову операцію, обличчя або вхідний потік — ні.",
        "solution": "Проєктуємо точки: каса, вхід, зал, склад, архів і доступ власника зі смартфона.",
        "spec": "2–6 IP-камер, NVR, HDD, PoE, мікрофон за потреби, смартфон власника.",
        "price": "Система для магазину — орієнтовно від 19 900 ₴.",
        "keyword": "БІЗНЕС",
    },
    {
        "topic": "Двір приватного будинку: як закрити сліпі зони",
        "category": "приватний будинок",
        "brand": "Hikvision / Dahua / Uniview",
        "hook": "А тут ваша камера бачить?",
        "problem": "Одна камера дивиться на ворота, але калитка, гараж або бокова зона залишаються без контролю.",
        "solution": "Будуємо схему покриття за маршрутами руху: ворота, калитка, вхід, гараж, паркомісце.",
        "spec": "4–8 IP-камер, нічний режим, PoE, архів 14–30 днів, UPS.",
        "price": "Відеоспостереження для двору — від 29 900 ₴.",
        "keyword": "ДВІР",
    },
    {
        "topic": "Ложні тривоги Ajax: чому систему вимикають",
        "category": "Ajax",
        "brand": "Ajax",
        "hook": "Найгірша сигналізація — та, яку вимкнули.",
        "problem": "Через хибні спрацювання власник перестає довіряти системі та вимикає охорону.",
        "solution": "Перевіряємо висоту датчиків, тварин, штори, протяги, сценарії, затримки та якість зв’язку.",
        "spec": "Ajax Hub, MotionProtect, DoorProtect, сирени, сценарії, користувачі, резерв.",
        "price": "Аудит і переналаштування Ajax — від 1 800 ₴.",
        "keyword": "ТРИВОГА",
    },
    {
        "topic": "Під’їзд ОСББ: домофон, доводчик і контроль входу",
        "category": "ОСББ",
        "brand": "Dahua / Hikvision / U-Prox",
        "hook": "Ваш під’їзд теж відкритий для всіх?",
        "problem": "Двері не закриваються, мешканці сваряться, а сторонні проходять без контролю.",
        "solution": "Робимо систему входу: домофон, зчитувач, доводчик, електрозамок, БЖ і зрозумілий доступ.",
        "spec": "IP-домофон, зчитувач, електрозамок, доводчик, блок живлення, ключі/брелоки.",
        "price": "Рішення для під’їзду — від 22 900 ₴.",
        "keyword": "ПІДЇЗД",
    },
    {
        "topic": "Самостійний монтаж: чому переробка часто дорожча",
        "category": "факап",
        "brand": "ALT-CAM",
        "hook": "Дешево спочатку — дорого після переробки.",
        "problem": "Кабелі висять, камера дивиться занадто високо, архів не пишеться, застосунок втрачає зв’язок.",
        "solution": "Переробляємо схему, кабель, кути камер, архів, доступ і резерв так, щоб система працювала цілісно.",
        "spec": "Аудит, кабель-канал, перенесення камер, NVR/HDD, PoE, налаштування смартфона.",
        "price": "Виправлення помилок монтажу — від 3 900 ₴.",
        "keyword": "АУДИТ",
    },
    {
        "topic": "Скільки днів архіву реально потрібно",
        "category": "архів",
        "brand": "Hikvision / Dahua / Uniview",
        "hook": "Камери пишуть. Але потрібного дня вже немає.",
        "problem": "Диск підібрали “на око”, і архів стирається раніше, ніж власник помічає проблему.",
        "solution": "Рахуємо архів за кількістю камер, бітрейтом, режимом запису, роздільною здатністю і сценарієм об’єкта.",
        "spec": "HDD 2–8 ТБ, H.265/H.265+, запис за рухом або постійно, NVR.",
        "price": "Підбір архіву та диска — від 900 ₴; HDD додається окремо.",
        "keyword": "АРХІВ",
    },
]


CONTOURS = [
    ("1 — Captivate", "Captivate", "Вірусний захват / помилки / міфи / тести"),
    ("2 — Expert", "Expert", "Експертний розбір технології"),
    ("3 — Proof", "Proof", "Соціальний доказ / кейс / до-після"),
    ("4 — Offer", "Offer", "Пропозиція / комплект / розрахунок"),
]

ANGLES = [
    {
        "name": "міф",
        "suffix": "міф, який коштує грошей",
        "hook_prefix": "Міф:",
        "neighbor_line": "Сусід теж думав, що цього достатньо — поки система не знадобилась.",
    },
    {
        "name": "помилка",
        "suffix": "помилка, яку видно лише після проблеми",
        "hook_prefix": "Помилка:",
        "neighbor_line": "У сусіда все виглядало нормально, але запис не допоміг.",
    },
    {
        "name": "тест",
        "suffix": "тест на реальному сценарії",
        "hook_prefix": "Тест:",
        "neighbor_line": "Порівняйте: як працює випадкове рішення і як працює продумана система.",
    },
    {
        "name": "до-після",
        "suffix": "до/після без прикрас",
        "hook_prefix": "До/після:",
        "neighbor_line": "Коли бачиш різницю до і після — питання “навіщо” зникає.",
    },
    {
        "name": "ціна помилки",
        "suffix": "скільки коштує помилка",
        "hook_prefix": "Ціна помилки:",
        "neighbor_line": "Найдорожче — переробляти тоді, коли проблема вже сталася.",
    },
    {
        "name": "чек-лист",
        "suffix": "чек-лист перед покупкою",
        "hook_prefix": "Перевірте:",
        "neighbor_line": "Більшість пропускає цей пункт, а потім дивується результату.",
    },
    {
        "name": "провокація",
        "suffix": "чесне питання власнику",
        "hook_prefix": "Чесно:",
        "neighbor_line": "Якщо відповідь “не знаю” — систему треба перевірити до проблеми.",
    },
    {
        "name": "антифакап",
        "suffix": "антифакап для дому й бізнесу",
        "hook_prefix": "Не робіть так:",
        "neighbor_line": "Саме з таких дрібниць починаються великі переробки.",
    },
]

OBJECTS = [
    "квартира",
    "приватний будинок",
    "магазин",
    "офіс",
    "склад",
    "ОСББ",
    "паркінг",
    "кав’ярня",
    "салон",
    "виробництво",
]

VIRAL_PATTERNS = [
    "різкий zoom-in на проблему",
    "контраст “у сусіда / у нас”",
    "кадр із телефоном, де видно біль",
    "жовта підсвітка проблемної зони",
    "до/після одним монтажним переходом",
    "пауза перед вердиктом",
    "швидка нарізка 3 помилок",
    "фінальний кадр із чітким CTA",
]

def unique_angle(index: int) -> dict:
    return ANGLES[index % len(ANGLES)]


def object_for_day(index: int) -> str:
    return OBJECTS[(index * 3) % len(OBJECTS)]


def viral_pattern(index: int) -> str:
    return VIRAL_PATTERNS[(index * 5) % len(VIRAL_PATTERNS)]


def money_for_day(topic: dict, day_index: int) -> str:
    if day_index % 4 == 3:
        return topic["price"]
    return topic["price"].replace(" — ", " — орієнтир: ")


def build_day(start, index: int) -> dict:
    current_date = start + timedelta(days=index)
    contour_id, contour, contour_note = CONTOURS[index % len(CONTOURS)]
    base = TOPICS[index % len(TOPICS)]
    angle = unique_angle(index)
    object_type = object_for_day(index)
    viral = viral_pattern(index)
    topic_title = f"{base['topic']} для {object_type}: {angle['suffix']}"
    price = money_for_day(base, index)
    visual_hook = f"{angle['hook_prefix']} {base['hook']}"
    audio_hook = f"{visual_hook} Покажу на прикладі {object_type}, чому це важливо перевірити до проблеми."
    object_problem = f"{base['problem']} Особливо критично для формату: {object_type}."
    object_solution = f"{base['solution']} Адаптуємо під об’єкт: {object_type}."

    frames = [
        {
            "frame": 1,
            "time": "0–3s",
            "purpose": "гачок",
            "visual": f"{viral}. Крупний план проблеми для об’єкта “{object_type}”: {base['problem']}",
            "onscreen_text": visual_hook,
        },
        {
            "frame": 2,
            "time": "3–8s",
            "purpose": "як може бути / як у сусіда",
            "visual": angle["neighbor_line"],
            "onscreen_text": "У сусіда було так само",
        },
        {
            "frame": 3,
            "time": "8–15s",
            "purpose": "рішення",
            "visual": f"Монтажник ALT-CAM у брендованій формі показує рішення для {object_type}: {object_solution}",
            "onscreen_text": "Рішення ALT-CAM",
        },
        {
            "frame": 4,
            "time": "15–23s",
            "purpose": "доказ / специфікація",
            "visual": f"Показати обладнання, застосунок, акуратний монтаж або схему: {base['spec']}",
            "onscreen_text": "Перевірено на об’єкті",
        },
        {
            "frame": 5,
            "time": "23–30s",
            "purpose": "CTA",
            "visual": "Фінальний кадр із логотипом ALT-CAM, Telegram-ботом і географією роботи.",
            "onscreen_text": f"Напишіть «{base['keyword']}» у бот",
        },
    ]

    carousel_slides = [
        visual_hook,
        f"Проблема для {object_type}: {base['problem']}",
        f"Як це виглядає на практиці: {angle['neighbor_line']}",
        f"Рішення: {object_solution}",
        f"Обладнання: {base['spec']}",
        f"{price}. Точніше — у квизі {BOT_HANDLE}",
    ]

    caption = (
        f"{visual_hook}\n\n"
        f"Проблема для об’єкта “{object_type}”: {base['problem']}\n\n"
        f"Як у сусіда: {angle['neighbor_line']}\n\n"
        f"Рішення ALT-CAM: {object_solution}\n\n"
        f"Специфікація: {base['spec']}\n\n"
        f"💰 {price}\n"
        "Фінальна сума залежить від об’єкта, довжини трас, архіву, резерву й обраного обладнання.\n\n"
        f"🤖 Пройдіть короткий квиз у Telegram-боті: {BOT}\n"
        f"🌐 {SITE}\n"
        f"📍 {LOCATION}\n\n"
        f"{HASHTAGS}"
    )

    threads = [
        f"1/7 {visual_hook}",
        f"2/7 Об’єкт: {object_type}. Проблема: {base['problem']}",
        f"3/7 Як це буває: {angle['neighbor_line']}",
        f"4/7 Рішення ALT-CAM: {object_solution}",
        f"5/7 Технічна база: {base['spec']}",
        f"6/7 Бюджет: {price}",
        f"7/7 У вас {object_type} чи інший об’єкт? Напишіть у коментарях — підкажемо перший крок. Квиз: {BOT}",
    ]

    youtube_title = f"{base['topic']} — {base['brand']} | ALT-CAM Security UA"
    youtube_description = (
        f"У цьому відео розбираємо: {topic_title}.\n\n"
        f"Проблема: {object_problem}\n"
        f"Рішення: {object_solution}\n"
        f"Обладнання: {base['spec']}\n"
        f"Орієнтир бюджету: {price}\n\n"
        f"🤖 Розрахунок у Telegram-боті: {BOT}\n"
        f"🌐 {SITE}\n"
        f"📍 {LOCATION}\n\n"
        f"{HASHTAGS}"
    )

    return {
        "day": index + 1,
        "date": current_date.isoformat(),
        "weekday": current_date.strftime("%A"),
        "publish_time": "18:30 Europe/Kyiv",
        "contour": contour_id,
        "content_type": contour,
        "content_note": contour_note,
        "topic": topic_title,
        "category": base["category"],
        "object_type": object_type,
        "viral_pattern": viral,
        "angle": angle["name"],
        "brands": base["brand"],
        "keyword": base["keyword"],
        "tiktok_shorts_reels": {
            "cover_title": visual_hook,
            "visual_hook_first_3s": visual_hook,
            "audio_hook": audio_hook,
            "scenario_by_seconds": {
                "0-3s": frames[0]["visual"],
                "3-15s": frames[1]["visual"] + " " + frames[2]["visual"],
                "15-30s": frames[3]["visual"] + " " + frames[4]["visual"],
            },
            "generation_frames_3_5": frames,
            "on_screen_text": [frame["onscreen_text"] for frame in frames],
            "cta": f"Перейдіть у Telegram-бот {BOT_HANDLE} і напишіть «{base['keyword']}».",
        },
        "instagram_facebook": {
            "format": "Reels + карусель 6 слайдів" if contour in {"Captivate", "Offer"} else "Карусель / Single Photo / Reels",
            "carousel_title": visual_hook,
            "slides": carousel_slides,
            "caption": caption,
            "hashtags": HASHTAGS,
        },
        "threads": {
            "format": "Міні-тред для обговорення",
            "thread_posts": threads,
            "first_comment": "Напишіть тип об’єкта: квартира / будинок / магазин / офіс / склад — підкажемо, з чого почати.",
        },
        "youtube_long": {
            "title": youtube_title,
            "timecodes": [
                "00:00 Вступ і проблема",
                "01:30 Що часто роблять неправильно",
                "03:30 Огляд обладнання та брендів",
                "05:00 Монтаж / налаштування / схема",
                "08:30 Координація в Telegram-боті",
                "09:30 Висновок і CTA",
            ],
            "description": youtube_description,
            "pinned_comment": f"Який у вас об’єкт і що потрібно вирішити? Напишіть у коментарях або пройдіть квиз: {BOT}",
            "community_post": (
                f"{visual_hook}\n\n"
                f"Що у вас зараз актуальніше: {base['category']} чи інша система безпеки?\n"
                "1️⃣ Камери\n2️⃣ Ajax\n3️⃣ Домофон / СКУД\n4️⃣ Резерв живлення\n\n"
                f"За найчастішими відповідями зробимо наступний розбір. Квиз: {BOT}"
            ),
        },
        "telegram": {
            "format": "Текстовий розбір із фото / чек-лист / акція",
            "text": (
                f"**{visual_hook}**\n\n"
                f"{base['problem']}\n\n"
                f"**Рішення ALT-CAM:** {base['solution']}\n\n"
                f"**Обладнання:** {base['spec']}\n\n"
                f"`{price}`\n\n"
                f"Для точного розрахунку пройдіть короткий квиз: {BOT}\n\n"
                f"📍 {LOCATION}"
            ),
            "inline_button": {"text": "🤖 Розрахувати вартість у боті", "url": BOT},
        },
    }


def build_plan(start, days: int) -> dict:
    return {
        "brand": "ALT-CAM Security UA",
        "period": {"start": start.isoformat(), "days": days, "end": (start + timedelta(days=days - 1)).isoformat()},
        "language": "uk-UA",
        "timezone": "Europe/Kyiv",
        "platforms": ["Facebook", "Instagram", "TikTok", "Telegram", "YouTube", "Threads"],
        "content_cycle": [item[1] for item in CONTOURS],
        "posting_goal": "вести користувача в Telegram-бот ALT-CAM для квизу/калькулятора",
        "status": "draft",
        "approval_required": True,
        "days": [build_day(start, index) for index in range(days)],
    }


def posting_drafts(plan: dict) -> dict:
    posts = []
    for day in plan["days"]:
        posts.append({
            "id": f"altcam-60d-{day['date']}-d{day['day']:02d}",
            "scheduled_at": f"{day['date']}T18:30:00+03:00",
            "platforms": ["facebook", "instagram", "tiktok", "threads", "telegram", "youtube"],
            "status": "draft",
            "approval_required": True,
            "content_type": day["content_type"],
            "topic": day["topic"],
            "caption": day["instagram_facebook"]["caption"],
            "captions": {
                "facebook": day["instagram_facebook"]["caption"],
                "instagram": day["instagram_facebook"]["caption"],
                "tiktok": day["tiktok_shorts_reels"]["visual_hook_first_3s"] + "\n\n" + day["tiktok_shorts_reels"]["cta"] + "\n" + HASHTAGS,
                "threads": "\n\n".join(day["threads"]["thread_posts"]),
                "telegram": day["telegram"]["text"],
                "youtube": day["youtube_long"]["description"],
                "youtube_community": day["youtube_long"]["community_post"],
            },
            "production_plan": day,
        })
    return {"posts": posts}


def render_md(plan: dict) -> str:
    lines = [
        "# ALT-CAM Security UA — контент-план на 60 днів",
        "",
        f"Період: **{plan['period']['start']} — {plan['period']['end']}**",
        "",
        "Мета: системно вести аудиторію в Telegram-бот ALT-CAM для квизу/калькулятора.",
        "",
        "Матриця: **Captivate → Expert → Proof → Offer**.",
        "",
        "> Статус: чернетка. Ціни в ₴ орієнтовні; перед публікацією перевірити обладнання, наявність і актуальність цін.",
        "",
        "## Швидкий календар",
        "",
        "| День | Дата | Контур | Тема | CTA |",
        "|---:|---|---|---|---|",
    ]
    for day in plan["days"]:
        lines.append(f"| {day['day']} | {day['date']} | {day['content_type']} | {day['topic']} | {day['keyword']} |")

    for day in plan["days"]:
        short = day["tiktok_shorts_reels"]
        meta = day["instagram_facebook"]
        youtube = day["youtube_long"]
        telegram = day["telegram"]
        lines.extend([
            "",
            "---",
            "",
            f"## День {day['day']} — {day['date']} — {day['contour']}",
            "",
            f"**Тема:** {day['topic']}  ",
            f"**Категорія:** {day['category']}  ",
            f"**Бренди:** {day['brands']}  ",
            f"**Час:** {day['publish_time']}",
            "",
            "### TikTok / Shorts / Reels",
            "",
            f"- **Заставка / cover:** {short['cover_title']}",
            f"- **Visual Hook:** {short['visual_hook_first_3s']}",
            f"- **Audio Hook:** {short['audio_hook']}",
            "- **Сценарій по секундах:**",
        ])
        for period, text in short["scenario_by_seconds"].items():
            lines.append(f"  - `{period}` — {text}")
        lines.extend(["- **3–5 кадрів для генерації:**"])
        for frame in short["generation_frames_3_5"]:
            lines.append(f"  - Кадр {frame['frame']} ({frame['time']}): {frame['visual']} / текст: `{frame['onscreen_text']}`")
        lines.extend([
            f"- **CTA:** {short['cta']}",
            "",
            "### Instagram / Facebook",
            "",
            f"- **Формат:** {meta['format']}",
            f"- **Заголовок каруселі:** {meta['carousel_title']}",
            "- **Слайди:**",
        ])
        for index, slide in enumerate(meta["slides"], 1):
            lines.append(f"  {index}. {slide}")
        lines.extend([
            "",
            "**Текст поста:**",
            "",
            meta["caption"],
            "",
            "### Threads",
            "",
            "- **Формат:** Міні-тред для обговорення",
        ])
        for post in day["threads"]["thread_posts"]:
            lines.append(f"- {post}")
        lines.extend([
            f"- **Перший коментар:** {day['threads']['first_comment']}",
            "",
            "### YouTube Long",
            "",
            f"- **Назва:** {youtube['title']}",
            "- **Таймкоди:**",
        ])
        for timecode in youtube["timecodes"]:
            lines.append(f"  - {timecode}")
        lines.extend([
            "",
            "**Опис:**",
            "",
            youtube["description"],
            "",
            f"**Закріплений коментар:** {youtube['pinned_comment']}",
            "",
            "**YouTube Community:**",
            "",
            youtube["community_post"],
            "",
            "### Telegram",
            "",
            f"- **Формат:** {telegram['format']}",
            "",
            telegram["text"],
            "",
            f"Кнопка: [{telegram['inline_button']['text']}]({telegram['inline_button']['url']})",
        ])
    return "\n".join(lines) + "\n"


def write_csv(plan: dict, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["day", "date", "content_type", "topic", "category", "brands", "keyword"])
        writer.writeheader()
        for day in plan["days"]:
            writer.writerow({
                "day": day["day"],
                "date": day["date"],
                "content_type": day["content_type"],
                "topic": day["topic"],
                "category": day["category"],
                "brands": day["brands"],
                "keyword": day["keyword"],
            })


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ALT-CAM 60-day content matrix for 6 channels.")
    parser.add_argument("--start", default="2026-08-03", help="Start date YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=60, help="Number of days")
    args = parser.parse_args()
    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    plan = build_plan(start, args.days)
    out = ROOT / "social-posts" / "content-plans" / f"{start.isoformat()}-{args.days}-day-matrix"
    out.mkdir(parents=True, exist_ok=True)
    (out / "PLAN.md").write_text(render_md(plan), encoding="utf-8")
    (out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "posting-drafts.json").write_text(json.dumps(posting_drafts(plan), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(plan, out / "calendar-summary.csv")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
