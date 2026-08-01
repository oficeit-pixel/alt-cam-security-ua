from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = "https://t.me/alt_cam_bot"
CHANNEL = "https://t.me/altcam_security_ua"
SITE = "https://alt-cam.net.ua"
LOCATION = "Київ • Вишгород • Київська область"
HASHTAGS = "#відеоспостереженнякиїв #монтажкамер #системибезпеки #Київ #Вишгород #altcam"


IDEAS = [
    {
        "contour": "1 — Captivate",
        "topic": "5 помилок монтажу камер",
        "format": "Reels / коротке відео з реального об'єкта",
        "presenter": "Сергій",
        "visual": "СТОП. Так камера не захистить будинок",
        "audio": "Камера може бути дорогою, але через ці п'ять помилок вона не дасть потрібного доказу.",
        "beats": ["Швидка нарізка: засвіт, сліпа зона, низький монтаж.", "П'ять помилок: кут, висота, контрове світло, слабкий архів, відсутність резерву.", "Показати правильний ракурс і запросити пройти розрахунок у боті."],
        "screen": ["1. Неправильний кут", "2. Засвіт обличчя", "3. Сліпа зона", "4. Мало архіву", "5. Немає резерву"],
        "slides": ["5 помилок, через які камера не допоможе", "Камера високо — обличчя не видно", "Сонце або фара засвічує кадр", "Сліпі зони залишають головний маршрут", "Архів закінчується раніше події", "Рішення: схема, тест ночі та резерв"],
        "problem": "Камери встановлені, але обличчя, номер або момент події не читаються.",
        "solution": "Проєктуємо кути огляду, перевіряємо нічну сцену та розраховуємо архів до монтажу.",
        "spec": "Hikvision або Dahua, 4 Мп, AcuSense/SMD, HDD від 2 ТБ, UPS.",
        "price": "Аудит готової системи — від 1 500 ₴; монтаж камери — від 2 500 ₴.",
        "youtube": "5 помилок монтажу камер відеоспостереження: чому не видно обличчя",
    },
    {
        "contour": "2 — Expert",
        "topic": "AcuSense та ColorVu без маркетингового туману",
        "format": "Карусель + експертний Reels",
        "presenter": "Аліса",
        "visual": "ColorVu чи AcuSense — що обрати?",
        "audio": "Це не конкуренти: одна технологія покращує картинку, інша відсіює зайві тривоги.",
        "beats": ["Порівняння двох нічних кадрів.", "Пояснити ColorVu, AcuSense та Dahua WizSense простими словами.", "Дати три сценарії вибору для дому, магазину та складу."],
        "screen": ["ColorVu = колір уночі", "AcuSense = людина/авто", "WizSense = розумна фільтрація", "Вибір залежить від сцени"],
        "slides": ["ColorVu чи AcuSense?", "ColorVu: кольорові деталі вночі", "AcuSense: фільтр людей та авто", "Dahua WizSense: аналогічна логіка подій", "Для двору важливі світло й об'єктив", "Підберемо технологію під вашу сцену"],
        "problem": "Покупець переплачує за назву технології, не розуміючи, що саме вона вирішує.",
        "solution": "Порівнюємо реальні нічні сцени та підбираємо функцію відповідно до потреб об'єкта.",
        "spec": "Hikvision ColorVu/AcuSense або Dahua WizSense, 4 Мп, PoE, архів 14–30 днів.",
        "price": "Система на 4 камери з монтажем — орієнтовно від 24 900 ₴.",
        "youtube": "Hikvision ColorVu та AcuSense: різниця, налаштування і вибір камери",
    },
    {
        "contour": "3 — Proof",
        "topic": "Домофонія: реальний об'єкт до та після",
        "format": "Карусель із реальних фото",
        "presenter": "Сергій",
        "visual": "Було: ключ і пропущені гості. Стало: контроль зі смартфона",
        "audio": "Покажу, як ми перетворили звичайний вхід на керовану систему доступу.",
        "beats": ["Вхід до монтажу.", "Панель, замок, кабель і налаштування застосунку.", "Готовий вигляд та дзвінок на смартфон."],
        "screen": ["До", "Монтаж без зайвих дротів", "Виклик на смартфон", "Відкриття дистанційно", "Після"],
        "slides": ["Домофонія: до та після", "Потреба: хвіртка й дистанційний доступ", "Акуратна установка викличної панелі", "Електрозамок і захищене живлення", "Виклик у застосунку", "Результат і підтримка ALT-CAM"],
        "problem": "Власник не бачить відвідувача та не може відкрити хвіртку, коли його немає вдома.",
        "solution": "Відеодомофон, виклична панель, електрозамок і мобільний доступ.",
        "spec": "Dahua або Hikvision IP-домофон, панель, монітор, замок, резерв живлення.",
        "price": "Комплект домофонії з монтажем — орієнтовно від 18 900 ₴.",
        "youtube": "IP-домофон для приватного будинку: монтаж Dahua та керування зі смартфона",
    },
    {
        "contour": "4 — Offer",
        "topic": "Готовий комплект відеоспостереження на 4 камери",
        "format": "Карусель-пропозиція + Reels",
        "presenter": "Аліса",
        "visual": "4 камери під ключ — що входить у ціну?",
        "audio": "Не просто коробка з камерами: показую повний комплект, який можна нормально здати клієнту.",
        "beats": ["Усе обладнання одним кадром.", "Камери, реєстратор, диск, PoE, монтаж і застосунок.", "Ціна від та кнопка розрахунку для конкретного об'єкта."],
        "screen": ["4 IP-камери", "Реєстратор + HDD", "Монтаж і кабель", "Доступ зі смартфона", "Від 24 900 ₴"],
        "slides": ["4 камери під ключ", "Hikvision / Dahua / Uniview", "Реєстратор і HDD для архіву", "Кабель, PoE та монтаж", "Налаштування смартфона", "Від 24 900 ₴ — точний розрахунок у боті"],
        "problem": "У дешевих наборах часто не враховані диск, кабель, живлення, налаштування та нормальний монтаж.",
        "solution": "Формуємо повний кошторис без прихованих обов'язкових позицій.",
        "spec": "4 IP-камери Hikvision/Dahua/Uniview 4 Мп, NVR, HDD 2 ТБ, PoE, кабель до 100 м.",
        "price": "Комплект із базовим монтажем — орієнтовно від 24 900 ₴.",
        "youtube": "Комплект відеоспостереження на 4 камери під ключ: ціна та комплектація",
    },
    {
        "contour": "1 — Captivate",
        "topic": "Блекаут: що відключиться першим",
        "format": "Тест на реальному обладнанні",
        "presenter": "Сергій",
        "visual": "Вимикаємо світло. Скільки протримається ваша безпека?",
        "audio": "Зараз вимкнемо мережу й перевіримо, чи залишаться камери, роутер та Ajax онлайн.",
        "beats": ["Вимкнення автомата й таймер на екрані.", "Показати споживання NVR, PoE, роутера та Ajax.", "Пояснити різницю UPS і LiFePO4 та дати формулу підбору."],
        "screen": ["230 В — OFF", "Камери — ONLINE", "Роутер — ONLINE", "Ajax — ONLINE", "Резерв рахуємо за навантаженням"],
        "slides": ["Що вимкнеться першим під час блекауту?", "Рахуємо споживання камер і NVR", "Не забуваємо про роутер та ONU", "UPS — короткий резерв", "LiFePO4 — довша автономність", "Підбір резерву в боті"],
        "problem": "Камери мають резерв, але відключається роутер або оптичний термінал — віддаленого доступу немає.",
        "solution": "Резервуємо весь ланцюг: NVR, PoE, роутер, ONU та Ajax.",
        "spec": "UPS або LiFePO4, чиста синусоїда за потреби, захист АКБ, розрахунок у ват-годинах.",
        "price": "Базовий резерв для мережі та системи безпеки — від 8 900 ₴.",
        "youtube": "Резервне живлення для камер, роутера та Ajax: UPS чи LiFePO4",
    },
    {
        "contour": "2 — Expert",
        "topic": "Hik-Connect, DMSS та Imou Life: безпечне налаштування",
        "format": "Екранний запис + ведуча",
        "presenter": "Аліса",
        "visual": "Не передавайте пароль від камер монтажнику назавжди",
        "audio": "Віддалений доступ можна налаштувати без спільного пароля на всіх телефонах.",
        "beats": ["Показати небезпечний спосіб зі спільним логіном.", "Додавання пристрою, запрошення користувача, 2FA та обмеження прав.", "Чек-лист безпечної передачі системи клієнту."],
        "screen": ["Окремий акаунт власника", "2FA", "Запрошення користувача", "Мінімальні права", "Резервний код — власнику"],
        "slides": ["Безпечний доступ до камер зі смартфона", "Hik-Connect: власник створює акаунт", "DMSS: доступ через запрошення", "Imou Life: не діліться паролем", "Увімкніть 2FA та перевірте права", "ALT-CAM налаштує й навчить"],
        "problem": "Один пароль передають усім користувачам, а власник не контролює доступ.",
        "solution": "Створюємо акаунт власника, вмикаємо 2FA та надаємо доступ через запрошення.",
        "spec": "Hik-Connect, DMSS або Imou Life; окремі користувачі, push-сповіщення, перевірка оновлень.",
        "price": "Налаштування віддаленого доступу та навчання — від 1 200 ₴.",
        "youtube": "Як налаштувати Hik-Connect, DMSS та Imou Life безпечно",
    },
    {
        "contour": "3 — Proof",
        "topic": "Ajax і камери в одному сценарії безпеки",
        "format": "Кейс + схема реакції",
        "presenter": "Сергій",
        "visual": "Тривога Ajax — і одразу видно, що сталося",
        "audio": "Датчик повідомляє про рух, а камера допомагає зрозуміти: це загроза чи хибна тривога.",
        "beats": ["Push від Ajax та відкриття камери.", "Сценарій: датчик, сирена, запис, світло, повідомлення.", "Результат на реальному об'єкті й CTA на розрахунок."],
        "screen": ["Ajax: тривога", "Камера: верифікація", "Сирена: реакція", "Резерв: система онлайн", "Один сценарій"],
        "slides": ["Ajax + відеоспостереження", "Датчик фіксує подію", "Камера дає візуальну перевірку", "Сирена та сценарій реакції", "Резерв тримає систему онлайн", "Рішення під ваш об'єкт"],
        "problem": "Окремі системи дають багато сповіщень, але не пояснюють користувачу, що відбувається.",
        "solution": "Об'єднуємо логіку тривоги, відеоперевірку та резервне живлення в зрозумілий сценарій.",
        "spec": "Ajax Hub, MotionProtect/DoorProtect, сирена, Hikvision/Dahua/Uniview або Imou, UPS.",
        "price": "Комплекс Ajax + відеоспостереження — орієнтовно від 34 900 ₴.",
        "youtube": "Ajax і відеоспостереження: як об'єднати тривогу та камери",
    },
]


def short_video(idea: dict) -> dict:
    return {
        "platforms": ["TikTok", "Instagram Reels", "YouTube Shorts"],
        "visual_hook_0_3": idea["visual"],
        "audio_hook": idea["audio"],
        "timeline": {"0-3s": idea["beats"][0], "3-15s": idea["beats"][1], "15-30s": idea["beats"][2]},
        "on_screen_text": idea["screen"],
        "cta": "Пройдіть короткий розрахунок у Telegram-боті @alt_cam_bot.",
        "link": BOT,
    }


def meta_post(idea: dict) -> dict:
    caption = (
        f"{idea['visual']}\n\nПроблема: {idea['problem']}\n\n"
        f"Рішення ALT-CAM: {idea['solution']}\n\n"
        f"Обладнання: {idea['spec']}\n\n💰 {idea['price']}\n"
        "Фінальна ціна залежить від об'єкта, довжини трас і потрібного архіву.\n\n"
        f"🤖 Розрахувати комплектацію: {BOT}\n📢 Канал: {CHANNEL}\n🌐 {SITE}\n"
        f"📍 {LOCATION}\n\n{HASHTAGS}"
    )
    return {"format": idea["format"], "carousel_title": idea["slides"][0], "slides": idea["slides"], "caption": caption, "hashtags": HASHTAGS}


def youtube(idea: dict) -> dict:
    return {
        "title": idea["youtube"] + " | ALT-CAM Security UA",
        "timecodes": ["00:00 Вступ і проблема", "01:30 Огляд технології та обладнання", "05:00 Монтаж або налаштування", "08:30 Розрахунок у Telegram-боті", "09:30 Висновки"],
        "description": f"Практичний розбір від ALT-CAM Security UA: {idea['topic']}.\n\nОбладнання: {idea['spec']}\nОрієнтир: {idea['price']}\n\n🤖 Розрахунок: {BOT}\n📢 Telegram-канал: {CHANNEL}\n🌐 {SITE}\n📍 {LOCATION}\n\n{HASHTAGS}",
    }


def threads_article(idea: dict) -> dict:
    opening_questions = {
        "1 — Captivate": "Ви теж бачили системи безпеки, які наче є, але в критичний момент не допомагають?",
        "2 — Expert": "Маркетинг у камерах звучить красиво. Але що реально потрібно саме вашому об’єкту?",
        "3 — Proof": "Найкраща реклама системи безпеки — це коли видно різницю “до” і “після”.",
        "4 — Offer": "Ціна “за камеру” майже ніколи не дорівнює ціні робочої системи під ключ.",
    }
    question = opening_questions.get(idea["contour"], "Розберімо одну типову помилку в системах безпеки.")
    posts = [
        f"1/7 {question}",
        f"2/7 Проблема: {idea['problem']}",
        f"3/7 Як це виглядає на практиці: власник думає, що все під контролем, але система не дає відповіді в потрібний момент.",
        f"4/7 Рішення ALT-CAM: {idea['solution']}",
        f"5/7 Технічна база: {idea['spec']}",
        f"6/7 Орієнтир бюджету: {idea['price']} Точну суму рахуємо після короткого квизу.",
        f"7/7 Що у вас зараз болить сильніше: камери, Ajax, домофон, доступ чи резерв? Напишіть у коментарях — підкажемо перший крок. 🤖 {BOT}",
    ]
    return {
        "format": "Threads-стаття / міні-тред для обговорення",
        "hook": question,
        "thread": posts,
        "engagement_question": "Що у вас зараз болить сильніше: камери, Ajax, домофон, доступ чи резерв?",
        "comment_seed": "Якщо хочете — напишіть тип об’єкта: квартира / будинок / магазин / офіс. Я підкажу, з чого почати.",
    }


def youtube_engagement(idea: dict) -> dict:
    return {
        "community_title": f"Питання до аудиторії: {idea['topic']}",
        "community_post": (
            f"{idea['visual']}\n\n"
            f"Ситуація: {idea['problem']}\n\n"
            "Хочемо зняти розбір на практиці й показати рішення без рекламного туману.\n\n"
            "Напишіть у коментарях, що вам ближче:\n"
            "1️⃣ квартира\n2️⃣ приватний будинок\n3️⃣ магазин / офіс\n4️⃣ склад / виробництво\n\n"
            f"За найчастішими відповідями зробимо наступний ролик. 🤖 Розрахунок: {BOT}"
        ),
        "pinned_comment": (
            f"Який у вас об’єкт і що потрібно вирішити? {idea['topic']} / камери / Ajax / домофон / СКУД / резерв. "
            f"Для швидкого прорахунку переходьте в бот: {BOT}"
        ),
        "discussion_prompts": [
            "Що для вас важливіше: ціна, якість картинки, автономність чи акуратний монтаж?",
            "Скільки днів архіву вам реально потрібно?",
            "Ви хочете бачити більше оглядів обладнання чи реальні кейси з об’єктів?",
        ],
    }


def telegram(idea: dict) -> dict:
    text = (
        f"**{idea['visual']}**\n\n{idea['problem']}\n\n"
        f"**Що робимо:** {idea['solution']}\n\n**Комплектація:** {idea['spec']}\n\n"
        f"`{idea['price']}`\n\nЦіна орієнтовна — точний кошторис формуємо після короткого опитування.\n\n📍 {LOCATION}"
    )
    return {"format": "Текстовий розбір із фото / чек-лист", "text": text, "inline_button": {"text": "🤖 Розрахувати вартість у боті", "url": BOT}}


def build_week(start: date) -> dict:
    days = []
    for i, idea in enumerate(IDEAS):
        day = start + timedelta(days=i)
        days.append({
            "day": i + 1,
            "date": day.isoformat(),
            "publish_time": "18:30 Europe/Kyiv",
            "contour": idea["contour"],
            "topic": idea["topic"],
            "presenter": idea["presenter"],
            "media_source": "Google Drive: 02_На обробці; обов'язкова перевірка приватності",
            "short_video": short_video(idea),
            "instagram_facebook": meta_post(idea),
            "youtube_long": youtube(idea),
            "youtube_community": youtube_engagement(idea),
            "threads_article": threads_article(idea),
            "telegram": telegram(idea),
        })
    return {
        "brand": "ALT-CAM Security UA",
        "language": "uk-UA",
        "timezone": "Europe/Kyiv",
        "start_date": start.isoformat(),
        "status": "draft",
        "approval_required": True,
        "price_policy": "Усі ціни орієнтовні та позначені 'від'; перевірити перед публікацією.",
        "telegram_bot_unverified": "@alt_cam_bot",
        "content_cycle": ["Captivate", "Expert", "Proof", "Offer"],
        "days": days,
    }


def render_markdown(plan: dict) -> str:
    lines = ["# ALT-CAM — контент-план на 7 днів", "", f"Період: {plan['start_date']} — {plan['days'][-1]['date']}", "", "> Статус: чернетка. Ціни та Telegram-бот перевірити перед підтвердженням.", ""]
    for day in plan["days"]:
        lines += [f"## День {day['day']} — {day['date']} — {day['contour']}", "", f"**Тема:** {day['topic']}  ", f"**Ведучий:** {day['presenter']}  ", f"**Час:** {day['publish_time']}", "", "### TikTok / Reels / Shorts", "", f"- Visual Hook: {day['short_video']['visual_hook_0_3']}", f"- Audio Hook: {day['short_video']['audio_hook']}"]
        for period, text in day["short_video"]["timeline"].items():
            lines.append(f"- {period}: {text}")
        lines += ["- On-screen: " + " • ".join(day["short_video"]["on_screen_text"]), f"- CTA: {day['short_video']['cta']}", "", "### Instagram / Facebook", "", f"**Формат:** {day['instagram_facebook']['format']}", "", "**Слайди:**"]
        for n, slide in enumerate(day["instagram_facebook"]["slides"], 1):
            lines.append(f"{n}. {slide}")
        lines += ["", "**Текст поста:**", "", day["instagram_facebook"]["caption"], "", "### YouTube Long", "", f"**Назва:** {day['youtube_long']['title']}", "", "**Таймкоди:**"]
        lines += [f"- {x}" for x in day["youtube_long"]["timecodes"]]
        lines += ["", day["youtube_long"]["description"], "", "### YouTube Community / коментарі для обговорення", "", f"**Community title:** {day['youtube_community']['community_title']}", "", day["youtube_community"]["community_post"], "", f"**Закріплений коментар:** {day['youtube_community']['pinned_comment']}", "", "**Питання для розвитку коментарів:**"]
        lines += [f"- {x}" for x in day["youtube_community"]["discussion_prompts"]]
        lines += ["", "### Threads", "", f"**Формат:** {day['threads_article']['format']}", "", "**Міні-тред:**"]
        lines += [f"- {x}" for x in day["threads_article"]["thread"]]
        lines += ["", f"**Перший коментар для розгону:** {day['threads_article']['comment_seed']}", "", "### Telegram", "", day["telegram"]["text"], "", f"Кнопка: [{day['telegram']['inline_button']['text']}]({day['telegram']['inline_button']['url']})", ""]
    return "\n".join(lines) + "\n"


def append_calendar(plan: dict) -> int:
    path = ROOT / "social-posts" / "meta-automation" / "posts.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    existing = {p["id"]: index for index, p in enumerate(data.get("posts", []))}
    added = 0
    for entry in build_posting_drafts(plan):
        post_id = entry["id"]
        if post_id in existing:
            data["posts"][existing[post_id]] = entry
        else:
            data["posts"].append(entry)
            added += 1
    data["posts"].sort(key=lambda p: p.get("scheduled_at", ""))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return added


def build_posting_drafts(plan: dict) -> list[dict]:
    entries = []
    for day in plan["days"]:
        entries.append({
            "id": f"altcam-matrix-{day['date']}-d{day['day']}",
            "scheduled_at": f"{day['date']}T18:30:00+03:00",
            "platforms": ["facebook", "instagram", "tiktok", "threads", "telegram", "youtube"],
            "status": "draft",
            "approval_required": True,
            "content_contour": day["contour"],
            "presenter": day["presenter"],
            "source_mode": "google_drive_real_photos_required",
            "privacy_review_required": True,
            "caption": day["instagram_facebook"]["caption"],
            "captions": {
                "facebook": day["instagram_facebook"]["caption"],
                "instagram": day["instagram_facebook"]["caption"],
                "threads": "\n\n".join(day["threads_article"]["thread"]),
                "tiktok": day["short_video"]["visual_hook_0_3"] + "\n\n" + day["short_video"]["cta"] + "\n" + HASHTAGS,
                "telegram": day["telegram"]["text"] + "\n\n" + BOT,
                "youtube": day["youtube_long"]["description"],
                "youtube_community": day["youtube_community"]["community_post"],
            },
            "production_plan": day,
        })
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a 7-day ALT-CAM 1-2-3-4 content matrix.")
    parser.add_argument("--start", default="2026-08-03", help="First day, YYYY-MM-DD")
    parser.add_argument("--append-calendar", action="store_true", help="Append safe draft entries to the main calendar")
    args = parser.parse_args()
    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    plan = build_week(start)
    output = ROOT / "social-posts" / "content-plans" / f"{start.isoformat()}-weekly-matrix"
    output.mkdir(parents=True, exist_ok=True)
    (output / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "PLAN.md").write_text(render_markdown(plan), encoding="utf-8")
    (output / "posting-drafts.json").write_text(json.dumps({"posts": build_posting_drafts(plan)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    added = append_calendar(plan) if args.append_calendar else 0
    print(f"Generated: {output}")
    print(f"Calendar drafts added: {added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
