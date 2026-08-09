from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SQUARE_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-10-product-week" / "media" / "square"
VERTICAL_DIR = ROOT / "social-posts" / "content-plans" / "2026-08-10-product-week" / "media" / "vertical"


SHEETS = [
    (
        Path(r"C:\Users\Net_w\.codex\generated_images\019f3167-a726-7c91-9715-a1b9ce714731\call_iyNtOocYoCmdLkCqviguXCr7.png"),
        [
            ("aug-01-utp-cat6.jpg", "UTP / RJ45", "кабель для IP-камер • PoE", "КАБЕЛЬ"),
            ("aug-02-outdoor-cable.jpg", "ЗОВНІШНІЙ КАБЕЛЬ", "лінія для фасаду / двору", "МОНТАЖ"),
            ("aug-03-bnc-dc-cable-kit.jpg", "BNC + DC КОМПЛЕКТ", "для аналогових камер", "КАБЕЛЬ"),
            ("aug-04-junction-box.jpg", "МОНТАЖНА КОРОБКА", "захист з’єднань на вулиці", "АКСЕСУАР"),
            ("aug-05-camera-bracket.jpg", "КРОНШТЕЙН КАМЕРИ", "правильний кут і фіксація", "КРОНШТЕЙН"),
            ("aug-06-pole-mount.jpg", "КРІПЛЕННЯ НА СТОВП", "камера без зайвих рішень", "КРОНШТЕЙН"),
            ("aug-07-mounting-box-glands.jpg", "БОКС + ГЕРМОВВОДИ", "чистий і безпечний монтаж", "БОКС"),
            ("aug-08-crimping-tool.jpg", "ОБЖИМНИЙ ІНСТРУМЕНТ", "RJ45 • тест • конектори", "ІНСТРУМЕНТ"),
            ("aug-09-network-tester.jpg", "ТЕСТЕР ЛІНІЇ", "перевірка кабелю до запуску", "ПРИЛАД"),
            ("aug-10-poe-injector-switch.jpg", "PoE ІНЖЕКТОР / SWITCH", "живлення камер по кабелю", "PoE"),
            ("aug-11-low-voltage-tools.jpg", "ІНСТРУМЕНТИ МОНТАЖНИКА", "акуратність починається з бази", "СЕРВІС"),
            ("aug-12-installer-drilling.jpg", "МОНТАЖ КРОНШТЕЙНА", "без перекосу і зайвих дірок", "МОНТАЖ"),
            ("aug-13-cable-trunking.jpg", "КАБЕЛЬ-КАНАЛ", "коли дроти не мають псувати вигляд", "АКСЕСУАР"),
            ("aug-14-rack-cable-manager.jpg", "КАБЕЛЬ-МЕНЕДЖМЕНТ", "шафа без хаосу", "ШАФА"),
            ("aug-15-patch-panel.jpg", "ПАТЧ-ПАНЕЛЬ", "порядок для IP-мережі", "МЕРЕЖА"),
            ("aug-16-conduit-pipe.jpg", "ГОФРА / ТРУБА", "захист траси на об’єкті", "МОНТАЖ"),
            ("aug-17-anchors-kit.jpg", "КРІПЛЕННЯ", "дюбелі • саморізи • стяжки", "КОМПЛЕКТ"),
            ("aug-18-waterproof-connector.jpg", "ГЕРМЕТИЧНИЙ РОЗ’ЄМ", "з’єднання, яке не боїться дощу", "АКСЕСУАР"),
            ("aug-19-power-supply-12v.jpg", "БЛОК ЖИВЛЕННЯ 12В", "стабільність для камер і замків", "ЖИВЛЕННЯ"),
            ("aug-20-router-ups.jpg", "UPS ДЛЯ РОУТЕРА", "інтернет і камери під резервом", "РЕЗЕРВ"),
        ],
    ),
    (
        Path(r"C:\Users\Net_w\.codex\generated_images\019f3167-a726-7c91-9715-a1b9ce714731\call_tmWU4MAI0b6AHqP42sMLaZTM.png"),
        [
            ("aug-21-house-camera-install.jpg", "КАМЕРА НА ФАСАДІ", "приватний будинок під контролем", "ОБ’ЄКТ"),
            ("aug-22-gate-camera.jpg", "КОНТРОЛЬ ВОРІТ", "хто заїжджає — видно одразу", "ВОРИТА"),
            ("aug-23-premium-gate-intercom.jpg", "ВІДЕОДОМОФОН НА ХВІРТКУ", "бачите гостя до відкриття", "ДОМОФОН"),
            ("aug-24-intercom-smartphone.jpg", "ДЗВІНОК НА СМАРТФОН", "контроль входу з телефону", "ДОМОФОН"),
            ("aug-25-office-glass-access.jpg", "СКУД ДЛЯ ОФІСУ", "доступ своїм — закрито для чужих", "СКУД"),
            ("aug-26-qr-reader-access.jpg", "QR / RFID ДОСТУП", "швидкий вхід без ключів", "СКУД"),
            ("aug-27-server-cabinet.jpg", "СЕРВЕРНА ШАФА", "NVR • PoE • UPS в порядку", "ШАФА"),
            ("aug-28-technician-tablet.jpg", "НАЛАШТУВАННЯ З ТЕЛЕФОНУ", "камери працюють як треба", "СЕРВІС"),
            ("aug-29-ajax-apartment.jpg", "AJAX У КВАРТИРІ", "датчики, які не псують інтер’єр", "AJAX"),
            ("aug-30-siren-office.jpg", "СИРЕНА + ДАТЧИК", "реакція на вторгнення", "СИГНАЛ"),
            ("aug-31-retail-dome-camera.jpg", "КАМЕРИ ДЛЯ МАГАЗИНУ", "каса, зал, персонал, відвідувачі", "РИТЕЙЛ"),
            ("aug-32-warehouse-bullet-camera.jpg", "СКЛАД ПІД НАГЛЯДОМ", "ряди, ворота, зона відвантаження", "СКЛАД"),
            ("aug-33-parking-ptz.jpg", "PTZ ДЛЯ ПАРКІНГУ", "огляд там, де одна камера не тягне", "PTZ"),
            ("aug-34-apartment-corridor.jpg", "ПІД’ЇЗД / КОРИДОР", "контроль входу без конфліктів", "ОСББ"),
            ("aug-35-cafe-camera.jpg", "КАМЕРИ ДЛЯ КАФЕ", "безпека без псування атмосфери", "КАФЕ"),
            ("aug-36-office-reception-access.jpg", "РЕСЕПШН ПІД КОНТРОЛЕМ", "доступ, відео, журнал подій", "ОФІС"),
            ("aug-37-battery-backup-internet.jpg", "РЕЗЕРВ ДЛЯ ІНТЕРНЕТУ", "зв’язок є навіть без світла", "РЕЗЕРВ"),
            ("aug-38-thermal-industrial-fence.jpg", "ПЕРИМЕТР ВНОЧІ", "тепловізійний контроль зони", "ПЕРИМЕТР"),
            ("aug-39-cable-before-after.jpg", "КАБЕЛІ БЕЗ ХАОСУ", "до / після нормального монтажу", "МОНТАЖ"),
            ("aug-40-line-testing.jpg", "ТЕСТ ЛІНІЇ", "перевіряємо до здачі об’єкта", "ПРИЛАД"),
        ],
    ),
    (
        Path(r"C:\Users\Net_w\.codex\generated_images\019f3167-a726-7c91-9715-a1b9ce714731\call_8cBnNAlKXv77hKcVYrKZnk7j.png"),
        [
            ("aug-41-dome-dual-light.jpg", "DUAL LIGHT КАМЕРА", "нічна картинка без сюрпризів", "КАМЕРА"),
            ("aug-42-black-bullet-mic.jpg", "BLACK BULLET + MIC", "відео і звук в одному сценарії", "КАМЕРА"),
            ("aug-43-panoramic-ptz.jpg", "ПАНОРАМА + PTZ", "широкий огляд і деталізація", "PTZ"),
            ("aug-44-mini-ptz-eave.jpg", "MINI PTZ", "поворотний огляд для входу", "PTZ"),
            ("aug-45-ai-nvr-black.jpg", "AI NVR", "реєстратор для розумної системи", "NVR"),
            ("aug-46-4ch-poe-nvr.jpg", "4CH PoE NVR", "малий комплект без зайвого", "NVR"),
            ("aug-47-white-intercom-monitor.jpg", "7” ВІДЕОДОМОФОН", "екран для входу й камер", "ДОМОФОН"),
            ("aug-48-black-intercom-monitor.jpg", "BLACK ДОМОФОН", "преміальний вигляд для інтер’єру", "ДОМОФОН"),
            ("aug-49-call-panel-slim.jpg", "SLIM ВИКЛИЧНА ПАНЕЛЬ", "акуратний вхід без зайвого", "ПАНЕЛЬ"),
            ("aug-50-face-terminal.jpg", "ТЕРМІНАЛ ДОСТУПУ", "обличчя / картка / журнал подій", "СКУД"),
            ("aug-51-rfid-reader-ip65.jpg", "RFID IP65", "зчитувач для складних умов", "СКУД"),
            ("aug-52-exit-button-magnetic-lock.jpg", "КНОПКА + МАГНІТНИЙ ЗАМОК", "базовий контроль дверей", "ЗАМОК"),
            ("aug-53-door-closer-strike.jpg", "ДОВОДЧИК + ЕЛЕКТРОЗАМОК", "двері закриваються самі", "ДВЕРІ"),
            ("aug-54-unmanaged-poe-switch.jpg", "PoE SWITCH", "камери + живлення одним кабелем", "PoE"),
            ("aug-55-managed-24-poe-switch.jpg", "24 PORT PoE", "мережа для великого об’єкта", "МЕРЕЖА"),
            ("aug-56-sfp-fiber.jpg", "SFP / ОПТИКА", "зв’язок між шафами й будівлями", "ОПТИКА"),
            ("aug-57-lithium-battery-module.jpg", "LITHIUM BACKUP", "довше тримає систему", "РЕЗЕРВ"),
            ("aug-58-inverter-battery-backup.jpg", "ІНВЕРТОР + АКБ", "енергонезалежність об’єкта", "ЖИВЛЕННЯ"),
            ("aug-59-ajax-black-hub.jpg", "AJAX BLACK", "стильно, розумно, під охороною", "AJAX"),
            ("aug-60-smart-home-sensors.jpg", "SMART HOME SENSORS", "безпека + комфорт", "ДАТЧИКИ"),
        ],
    ),
]

REEL_TITLES = [
    ("altcam-reel-2026-08-17-08.jpg", "КАБЕЛЬ ВИРІШУЄ ВСЕ", "погана лінія вбиває хорошу камеру"),
    ("altcam-reel-2026-08-18-09.jpg", "КРОНШТЕЙН — НЕ ДРІБНИЦЯ", "кут огляду = доказ або просто пляма"),
    ("altcam-reel-2026-08-19-10.jpg", "СКУД БЕЗ ХАОСУ", "хто заходив, коли і куди"),
    ("altcam-reel-2026-08-20-11.jpg", "СЕРВЕРНА ШАФА ЯК У ЛЮДЕЙ", "PoE, NVR, UPS — усе на місці"),
    ("altcam-reel-2026-08-21-12.jpg", "КАМЕРА ДЛЯ МАГАЗИНУ", "каса, зал, склад — різні задачі"),
    ("altcam-reel-2026-08-22-13.jpg", "ДОМОФОН ДЛЯ ВОРІТ", "бачите гостя до відкриття"),
    ("altcam-reel-2026-08-23-14.jpg", "РЕЗЕРВ ЖИВЛЕННЯ", "без світла система не повинна сліпнути"),
    ("altcam-reel-2026-08-24-15.jpg", "AJAX НЕ ТІЛЬКИ ДЛЯ КВАРТИРИ", "офіс, магазин, будинок — різні сценарії"),
    ("altcam-reel-2026-08-25-16.jpg", "ТЕСТ ЛІНІЇ ДО ЗДАЧІ", "щоб потім не шукати проблему вночі"),
    ("altcam-reel-2026-08-26-17.jpg", "ПЕРИМЕТР ВНОЧІ", "тепловізор бачить там, де камера здається"),
    ("altcam-reel-2026-08-27-18.jpg", "PoE ДЛЯ IP-КАМЕР", "менше блоків живлення, більше порядку"),
    ("altcam-reel-2026-08-28-19.jpg", "НЕ СТАВТЕ КАМЕРУ НАВМАННЯ", "спочатку задача, потім модель"),
    ("altcam-reel-2026-08-29-20.jpg", "МОНТАЖ БЕЗ ЗАЙВИХ ДІРОК", "акуратно, сервісно, з перевіркою"),
    ("altcam-reel-2026-08-30-21.jpg", "ВІДЕО + ДОСТУП + РЕЗЕРВ", "система працює як єдине ціле"),
    ("altcam-reel-2026-08-31-22.jpg", "ALT-CAM ПІДБІР ПІД ОБʼЄКТ", "не продаємо зайве — закриваємо задачу"),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def add_square_text(card: Image.Image, title: str, subtitle: str, tag: str) -> Image.Image:
    card = card.convert("RGBA")
    overlay = Image.new("RGBA", card.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((42, 42, 1190, 276), radius=28, fill=(0, 0, 0, 170), outline=(255, 204, 0, 120), width=2)
    draw.text((78, 70), title, font=font(54, True), fill=(245, 245, 247, 255))
    draw.text((80, 148), subtitle, font=font(35), fill=(224, 224, 230, 238))
    tag_width = max(240, int(draw.textlength(tag, font=font(32, True))) + 62)
    draw.rounded_rectangle((80, 206, 80 + tag_width, 255), radius=18, fill=(255, 204, 0, 238))
    draw.text((110, 212), tag, font=font(32, True), fill=(18, 18, 18, 255))
    draw.rounded_rectangle((42, 1240, 1366, 1366), radius=34, fill=(0, 0, 0, 172), outline=(255, 204, 0, 95), width=2)
    draw.text((84, 1262), "ALT-CAM Security UA", font=font(44, True), fill=(245, 245, 247, 255))
    draw.text((760, 1270), "Київ • Вишгород • область", font=font(33), fill=(255, 204, 0, 255))
    return Image.alpha_composite(card, overlay).convert("RGB")


def create_square_cards() -> list[Path]:
    SQUARE_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for source, cards in SHEETS:
        image = Image.open(source).convert("RGB")
        width, height = image.size
        for index, (filename, title, subtitle, tag) in enumerate(cards):
            col = index % 5
            row = index // 5
            box = (
                round(col * width / 5),
                round(row * height / 4),
                round((col + 1) * width / 5),
                round((row + 1) * height / 4),
            )
            card = image.crop(box).resize((1408, 1408), Image.Resampling.LANCZOS)
            card = add_square_text(card, title, subtitle, tag)
            out = SQUARE_DIR / filename
            card.save(out, quality=94, optimize=True)
            outputs.append(out)
    return outputs


def create_reel_covers(square_paths: list[Path]) -> list[Path]:
    VERTICAL_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    selected = [
        "aug-01-utp-cat6.jpg",
        "aug-05-camera-bracket.jpg",
        "aug-26-qr-reader-access.jpg",
        "aug-27-server-cabinet.jpg",
        "aug-31-retail-dome-camera.jpg",
        "aug-23-premium-gate-intercom.jpg",
        "aug-20-router-ups.jpg",
        "aug-29-ajax-apartment.jpg",
        "aug-40-line-testing.jpg",
        "aug-38-thermal-industrial-fence.jpg",
        "aug-54-unmanaged-poe-switch.jpg",
        "aug-42-black-bullet-mic.jpg",
        "aug-12-installer-drilling.jpg",
        "aug-58-inverter-battery-backup.jpg",
        "aug-10-poe-injector-switch.jpg",
    ]
    by_name = {path.name: path for path in square_paths}
    for (filename, title, subtitle), source_name in zip(REEL_TITLES, selected):
        base = Image.open(by_name[source_name]).convert("RGB")
        bg = base.resize((1080, 1920), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(18))
        bg = Image.blend(bg, Image.new("RGB", bg.size, (12, 12, 14)), 0.50).convert("RGBA")
        product = base.resize((860, 860), Image.Resampling.LANCZOS).convert("RGBA")
        overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rounded_rectangle((70, 110, 1010, 520), radius=34, fill=(0, 0, 0, 190), outline=(255, 204, 0, 125), width=3)
        draw.text((104, 152), title, font=font(62, True), fill=(245, 245, 247, 255))
        draw.text((108, 276), subtitle, font=font(40), fill=(255, 204, 0, 255))
        draw.text((108, 400), "ALT-CAM Security UA", font=font(40, True), fill=(245, 245, 247, 240))
        bg.alpha_composite(product, (110, 635))
        draw.rounded_rectangle((70, 1600, 1010, 1815), radius=40, fill=(255, 204, 0, 240))
        draw.text((116, 1645), "НАПИШІТЬ У TELEGRAM", font=font(48, True), fill=(18, 18, 18, 255))
        draw.text((116, 1710), "підберемо рішення під ваш обʼєкт", font=font(34), fill=(18, 18, 18, 235))
        final = Image.alpha_composite(bg, overlay).convert("RGB")
        out = VERTICAL_DIR / filename
        final.save(out, quality=94, optimize=True)
        outputs.append(out)
    return outputs


def main() -> int:
    squares = create_square_cards()
    verticals = create_reel_covers(squares)
    for path in [*squares, *verticals]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
