/* =========================================================
   КОНТАКТИ — замініть значення нижче на реальні перед публікацією.
   Telegram: ім'я користувача без символу @
   WhatsApp/телефон: тільки цифри у міжнародному форматі
   ========================================================= */
const CONTACTS = {
  telegram: "",
  whatsapp: "",
  phone: "+380000000000",
  phoneLabel: "+380 (00) 000-00-00",
  email: "info@alt-cam.ua",
  facebook: "https://facebook.com/",
  instagram: "https://instagram.com/",
  tiktok: "https://tiktok.com/",
  messenger: "https://m.me/",
  viber: ""
};

/* Вставьте идентификаторы после создания сервисов.
   webhook — URL Google Apps Script/CRM, который принимает JSON-заявки
   и отправляет их в Google Sheets, Telegram и Email. */
const INTEGRATIONS = {
  crmWebhook: "",
  ga4Id: "",
  metaPixelId: "",
  clarityId: ""
};

function sendLeadToCrm(payload) {
  if (!INTEGRATIONS.crmWebhook) return;
  fetch(INTEGRATIONS.crmWebhook, {
    method: "POST",
    headers: { "Content-Type": "text/plain;charset=utf-8" },
    body: JSON.stringify({
      ...payload,
      source: "alt-cam.ua",
      createdAt: new Date().toISOString()
    })
  }).catch(() => {
    // Месенджер все одно відкриється; збій CRM не блокує заявку.
  });
}

function trackEvent(name, parameters = {}) {
  if (typeof window.gtag === "function") window.gtag("event", name, parameters);
  if (typeof window.fbq === "function") window.fbq("trackCustom", name, parameters);
}

function initAnalytics() {
  if (INTEGRATIONS.ga4Id) {
    const gaScript = document.createElement("script");
    gaScript.async = true;
    gaScript.src = `https://www.googletagmanager.com/gtag/js?id=${INTEGRATIONS.ga4Id}`;
    document.head.appendChild(gaScript);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function gtag() { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", INTEGRATIONS.ga4Id);
  }

  if (INTEGRATIONS.metaPixelId) {
    window.fbq = window.fbq || function fbq() {
      (window.fbq.queue = window.fbq.queue || []).push(arguments);
    };
    const metaScript = document.createElement("script");
    metaScript.async = true;
    metaScript.src = "https://connect.facebook.net/en_US/fbevents.js";
    document.head.appendChild(metaScript);
    window.fbq("init", INTEGRATIONS.metaPixelId);
    window.fbq("track", "PageView");
  }

  if (INTEGRATIONS.clarityId) {
    window.clarity = window.clarity || function clarity() {
      (window.clarity.q = window.clarity.q || []).push(arguments);
    };
    const clarityScript = document.createElement("script");
    clarityScript.async = true;
    clarityScript.src = `https://www.clarity.ms/tag/${INTEGRATIONS.clarityId}`;
    document.head.appendChild(clarityScript);
  }
}

initAnalytics();

const header = document.querySelector(".header");
const menuButton = document.querySelector(".menu-toggle");
const menu = document.querySelector(".nav-links");

function updateHeader() {
  header.classList.toggle("scrolled", window.scrollY > 20);
}

updateHeader();
window.addEventListener("scroll", updateHeader, { passive: true });

menuButton.addEventListener("click", () => {
  const isOpen = menu.classList.toggle("open");
  menuButton.classList.toggle("active", isOpen);
  menuButton.setAttribute("aria-expanded", String(isOpen));
  document.body.classList.toggle("menu-open", isOpen);
});

document.querySelectorAll(".nav-links a").forEach((link) => {
  link.addEventListener("click", () => {
    menu.classList.remove("open");
    menuButton.classList.remove("active");
    menuButton.setAttribute("aria-expanded", "false");
    document.body.classList.remove("menu-open");
  });
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.08 });

document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));

function telegramUrl(text = "Вітаю! Хочу отримати консультацію щодо системи безпеки.") {
  return CONTACTS.telegram
    ? `https://t.me/${CONTACTS.telegram}?text=${encodeURIComponent(text)}`
    : `https://t.me/share/url?url=&text=${encodeURIComponent(text)}`;
}

document.querySelectorAll(".js-telegram").forEach((link) => {
  link.href = telegramUrl("Вітаю! Хочу отримати безкоштовну консультацію щодо системи безпеки.");
  link.target = "_blank";
  link.rel = "noopener noreferrer";
});

const leadForm = document.querySelector("#lead-form");
let selectedChannel = "telegram";

leadForm.querySelectorAll("[data-channel]").forEach((button) => {
  button.addEventListener("click", () => {
    selectedChannel = button.dataset.channel;
  });
});

leadForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!leadForm.reportValidity()) return;

  const data = new FormData(leadForm);
  const message = [
    "Заявка з сайту Alt-Cam Security UA",
    "",
    `Ім’я: ${data.get("name")}`,
    `Телефон: ${data.get("phone")}`,
    `Тип об’єкта: ${data.get("object")}`,
    `Коментар: ${data.get("comment") || "Не вказано"}`
  ].join("\n");

  const url = selectedChannel === "whatsapp"
    ? `https://wa.me/${CONTACTS.whatsapp ? CONTACTS.whatsapp : ""}?text=${encodeURIComponent(message)}`
    : telegramUrl(message);

  sendLeadToCrm({
    type: "contact_form",
    name: data.get("name"),
    phone: data.get("phone"),
    object: data.get("object"),
    comment: data.get("comment") || ""
  });
  trackEvent("generate_lead", { form: "contact_form", channel: selectedChannel });
  window.open(url, "_blank", "noopener,noreferrer");
});

document.querySelectorAll(".js-phone").forEach((phoneLink) => {
  phoneLink.href = `tel:${CONTACTS.phone}`;
  if (!phoneLink.classList.contains("mobile-call")) {
    phoneLink.textContent = CONTACTS.phoneLabel;
  }
});

const emailLink = document.querySelector(".js-email");
emailLink.href = `mailto:${CONTACTS.email}`;
emailLink.textContent = CONTACTS.email;

["facebook", "instagram", "tiktok"].forEach((network) => {
  const link = document.querySelector(`.js-${network}`);
  link.href = CONTACTS[network];
  link.target = "_blank";
  link.rel = "noopener noreferrer";
});

const messengerLink = document.querySelector(".js-messenger");
messengerLink.href = CONTACTS.messenger;
messengerLink.target = "_blank";
messengerLink.rel = "noopener noreferrer";

const viberLink = document.querySelector(".js-viber");
viberLink.href = CONTACTS.viber
  ? `viber://chat?number=${encodeURIComponent(CONTACTS.viber)}`
  : "#request";

const whatsAppLink = document.querySelector(".js-whatsapp");
whatsAppLink.href = CONTACTS.whatsapp
  ? `https://wa.me/${CONTACTS.whatsapp}?text=${encodeURIComponent("Вітаю! Хочу отримати консультацію щодо системи безпеки.")}`
  : "#request";
if (CONTACTS.whatsapp) {
  whatsAppLink.target = "_blank";
  whatsAppLink.rel = "noopener noreferrer";
}

document.querySelector("#year").textContent = new Date().getFullYear();

const calculator = document.querySelector("#security-calculator");
const calcState = {};

function money(value) {
  return new Intl.NumberFormat("uk-UA", {
    style: "currency",
    currency: "UAH",
    maximumFractionDigits: 0
  }).format(value);
}

function nextRecorderSize(cameraCount) {
  return [4, 8, 16, 32, 64].find((size) => size >= cameraCount) || 64;
}

function nextDiskSize(requiredTb) {
  return [1, 2, 4, 6, 8, 10, 12, 16, 20].find((size) => size >= requiredTb) || 20;
}

function calculateSecuritySystem() {
  return calculateSecuritySystemExact();
  /* Попередня площинна модель залишена нижче для історії версій. */
  const data = new FormData(calculator);
  const type = data.get("calcType");
  const length = Math.max(3, Number(data.get("calcLength")) || 3);
  const width = Math.max(3, Number(data.get("calcWidth")) || 3);
  const height = Number(data.get("calcHeight"));
  const quality = data.get("calcQuality");
  const archiveDays = Number(data.get("calcArchive"));
  const includeUps = data.get("calcUps") === "on";

  const area = Math.round(length * width);
  const perimeter = (length + width) * 2;
  const coverage = {
    building: { "2mp": 55, "4mp": 45, "8mp": 36 },
    yard: { "2mp": 90, "4mp": 72, "8mp": 58 },
    commerce: { "2mp": 48, "4mp": 40, "8mp": 32 },
    warehouse: { "2mp": 75, "4mp": 62, "8mp": 48 }
  }[type][quality];
  const perimeterStep = type === "yard" ? 22 : type === "warehouse" ? 28 : 25;
  const minimum = type === "commerce" ? 3 : 2;
  const cameras = Math.min(64, Math.max(minimum, Math.ceil(area / coverage), Math.ceil(perimeter / perimeterStep)));
  const recorderChannels = nextRecorderSize(cameras);
  const cableFactor = type === "yard" ? 1.55 : type === "warehouse" ? 1.35 : 1.2;
  const cable = Math.ceil((perimeter * cableFactor + cameras * height + 15) / 5) * 5;
  const bitrate = { "2mp": 2.1, "4mp": 4.2, "8mp": 7.5 }[quality];
  const requiredTb = bitrate * cameras * 86400 * archiveDays / 8 / 1024 / 1024 * 0.72;
  const storageTb = nextDiskSize(requiredTb);
  const cameraPrice = { "2mp": 2200, "4mp": 3400, "8mp": 5900 }[quality];
  const recorderPrice = 3200 + recorderChannels * 410;
  const diskPrice = storageTb * 1250 + 1100;
  const upsPrice = includeUps ? 4800 + Math.max(0, cameras - 4) * 280 : 0;
  const equipment = Math.round(cameras * cameraPrice + recorderPrice + diskPrice + cable * 19 + cameras * 720 + upsPrice);
  const heightFactor = height <= 3.5 ? 1 : height <= 5 ? 1.18 : height <= 8 ? 1.42 : 1.75;
  const work = Math.round((cameras * 1750 + cable * 20 + 2600) * heightFactor);
  const total = equipment + work;
  const low = Math.round(total * 0.9 / 500) * 500;
  const high = Math.round(total * 1.12 / 500) * 500;

  calcState.message = [
    "Попередній розрахунок Alt-Cam Security UA",
    "",
    `Об’єкт: ${calculator.elements.calcType.options[calculator.elements.calcType.selectedIndex].text}`,
    `План: ${length} × ${width} м (${area} м²)`,
    `Висота монтажу: ${height.toFixed(1)} м`,
    `Якість: ${calculator.elements.calcQuality.options[calculator.elements.calcQuality.selectedIndex].text}`,
    `Архів: ${archiveDays} днів`,
    "",
    `Камери: ${cameras} шт.`,
    `Реєстратор: ${recorderChannels} каналів`,
    `Кабель: близько ${cable} м`,
    `Жорсткий диск: ${storageTb} ТБ`,
    `Резервне живлення: ${includeUps ? "так" : "ні"}`,
    `Обладнання: близько ${money(equipment)}`,
    `Монтаж і налаштування: близько ${money(work)}`,
    `Загальний діапазон: ${money(low)} — ${money(high)}`,
    "",
    "Хочу уточнити цей розрахунок."
  ].join("\n");
  calcState.quote = {
    object: calculator.elements.calcType.options[calculator.elements.calcType.selectedIndex].text,
    dimensions: `${length} × ${width} м`,
    area,
    height: `${height.toFixed(1)} м`,
    quality: calculator.elements.calcQuality.options[calculator.elements.calcQuality.selectedIndex].text,
    archiveDays,
    cameras,
    recorderChannels,
    cable,
    storageTb,
    includeUps,
    equipment,
    work,
    low,
    high
  };

  document.querySelector("#height-output").textContent = `${height.toFixed(1).replace(".", ",")} м`;
  document.querySelector("#calc-area").textContent = area;
  document.querySelector("#calc-total").textContent = `${money(low)} — ${money(high)}`;
  document.querySelector("#calc-cameras").textContent = `${cameras} шт.`;
  document.querySelector("#calc-recorder").textContent = `${recorderChannels} каналів`;
  document.querySelector("#calc-cable").textContent = `≈ ${cable} м`;
  document.querySelector("#calc-storage").textContent = `${storageTb} ТБ`;
  document.querySelector("#calc-equipment").textContent = `≈ ${money(equipment)}`;
  document.querySelector("#calc-work").textContent = `≈ ${money(work)}`;
}

function calculateSecuritySystemExact() {
  const data = new FormData(calculator);
  const indoor = Math.max(0, Number(data.get("videoIndoor")) || 0);
  const outdoor = Math.max(0, Number(data.get("videoOutdoor")) || 0);
  const ptz = Math.max(0, Number(data.get("videoPtz")) || 0);
  const nvrChannels = Number(data.get("videoNvr"));
  const hddTb = Number(data.get("videoHdd"));
  const includeInstall = data.get("videoInstall") === "on";
  const nvrPrices = { 4: 1800, 8: 3200, 16: 5400 };
  const hddPrices = { 1: 2400, 2: 3500, 4: 5200 };
  const cameras = indoor + outdoor + ptz;
  const cameraPrice = indoor * 1450 + outdoor * 1950 + ptz * 4200;
  const centralPrice = nvrPrices[nvrChannels] + hddPrices[hddTb];
  const materials = indoor * 450 + outdoor * 650 + ptz * 700 + 400;
  const installation = includeInstall
    ? indoor * 750 + outdoor * 950 + ptz * 1500 + 1200
    : 0;
  const total = cameraPrice + centralPrice + materials + installation;
  const channelWarning = cameras > nvrChannels
    ? ` Увага: обраний NVR має ${nvrChannels} каналів для ${cameras} камер.`
    : "";

  calcState.message = [
    "Точний розрахунок IP-відеоспостереження Alt-Cam",
    "",
    `Внутрішні купольні камери: ${indoor} шт.`,
    `Вуличні циліндричні камери: ${outdoor} шт.`,
    `Поворотні PTZ: ${ptz} шт.`,
    `NVR: ${nvrChannels} каналів`,
    `WD Purple: ${hddTb} ТБ`,
    "",
    `Камери: ${money(cameraPrice)}`,
    `Центральний вузол: ${money(centralPrice)}`,
    `Витратні матеріали: ${money(materials)}`,
    `Монтаж і налаштування: ${money(installation)}`,
    `Загальна вартість: ${money(total)}`,
    channelWarning.trim(),
    "",
    "Хочу уточнити цей розрахунок."
  ].filter(Boolean).join("\n");
  calcState.quote = {
    indoor,
    outdoor,
    ptz,
    cameras,
    nvrChannels,
    hddTb,
    cameraPrice,
    centralPrice,
    materials,
    installation,
    total
  };

  document.querySelector("#calc-total").textContent = money(total);
  document.querySelector("#calc-camera-count").textContent = cameras;
  document.querySelector("#calc-cameras-price").textContent = money(cameraPrice);
  document.querySelector("#calc-central-price").textContent = money(centralPrice);
  document.querySelector("#calc-materials-price").textContent = money(materials);
  document.querySelector("#calc-install-price").textContent = money(installation);
  document.querySelector("#calc-note").textContent =
    `Витратні матеріали включають кабель, RJ-45, гермокоробки, кріплення та патч-корди.${channelWarning}`;
}

calculator.addEventListener("input", calculateSecuritySystem);
calculator.addEventListener("change", calculateSecuritySystem);
document.querySelector("#send-calculation").addEventListener("click", () => {
  trackEvent("calculator_send", { cameras: calcState.quote.cameras });
  window.open(telegramUrl(calcState.message), "_blank", "noopener,noreferrer");
});

document.querySelector("#download-proposal").addEventListener("click", () => {
  const quote = calcState.quote;
  const proposalWindow = window.open("", "_blank");
  if (!proposalWindow) return;
  const today = new Intl.DateTimeFormat("uk-UA", { dateStyle: "long" }).format(new Date());
  proposalWindow.document.write(`<!doctype html>
  <html lang="uk"><head><meta charset="utf-8"><title>Комерційна пропозиція Alt-Cam</title>
  <style>
    body{font-family:Arial,sans-serif;color:#07111f;margin:0;padding:42px;line-height:1.5}
    header{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:4px solid #ffc400;padding-bottom:24px;margin-bottom:30px}
    h1{font-size:28px;margin:0 0 7px}.brand{font-weight:800;font-size:20px}.brand span{color:#b88900}
    .muted{color:#667386;font-size:12px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:24px 0}
    .item{border:1px solid #dfe5ec;border-radius:8px;padding:12px}.item span,.item strong{display:block}.item span{font-size:10px;color:#667386}.item strong{margin-top:4px}
    table{width:100%;border-collapse:collapse;margin:25px 0}td{padding:11px;border-bottom:1px solid #dfe5ec}td:last-child{text-align:right;font-weight:700}
    .total{background:#07111f;color:white;border-radius:10px;padding:20px;display:flex;justify-content:space-between;align-items:center}.total strong{color:#ffc400;font-size:23px}
    footer{margin-top:34px;font-size:10px;color:#667386}.print{margin-top:25px;padding:12px 20px;border:0;border-radius:7px;background:#ffc400;font-weight:700;cursor:pointer}
    @media print{.print{display:none}body{padding:10mm}}
  </style></head><body>
  <header><div><h1>Комерційна пропозиція</h1><div class="muted">Попередній розрахунок системи відеоспостереження</div></div><div class="brand">ALT-CAM <span>SECURITY UA</span></div></header>
  <div class="muted">Сформовано: ${today}</div>
  <div class="grid">
    <div class="item"><span>Внутрішні камери</span><strong>${quote.indoor} шт.</strong></div>
    <div class="item"><span>Вуличні камери</span><strong>${quote.outdoor} шт.</strong></div>
    <div class="item"><span>Поворотні PTZ</span><strong>${quote.ptz} шт.</strong></div>
    <div class="item"><span>Центральний вузол</span><strong>NVR ${quote.nvrChannels} каналів, HDD ${quote.hddTb} ТБ</strong></div>
  </div>
  <table>
    <tr><td>IP-камери</td><td>${money(quote.cameraPrice)}</td></tr>
    <tr><td>NVR + WD Purple</td><td>${money(quote.centralPrice)}</td></tr>
    <tr><td>Кріплення та витратні матеріали</td><td>${money(quote.materials)}</td></tr>
    <tr><td>Монтаж і пусконалагодження</td><td>${money(quote.installation)}</td></tr>
  </table>
  <div class="total"><span>Загальна вартість</span><strong>${money(quote.total)}</strong></div>
  <footer>Цей документ є попереднім автоматичним розрахунком і не є публічною офертою. Точна конфігурація та вартість визначаються після уточнення зон огляду й умов монтажу.</footer>
  <button class="print" onclick="window.print()">Зберегти як PDF / Друкувати</button>
  </body></html>`);
  proposalWindow.document.close();
  trackEvent("proposal_open", { cameras: quote.cameras });
});
calculateSecuritySystem();

const calculatorTabs = [...document.querySelectorAll("[data-calc-tab]")];
const calculatorPanels = [...document.querySelectorAll("[data-calc-panel]")];

calculatorTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.calcTab;
    calculatorTabs.forEach((item) => {
      const isActive = item === tab;
      item.classList.toggle("active", isActive);
      item.setAttribute("aria-selected", String(isActive));
    });
    calculatorPanels.forEach((panel) => {
      panel.classList.toggle("active", panel.dataset.calcPanel === target);
    });
    trackEvent("calculator_mode", { mode: target });
  });
});

const powerCalculator = document.querySelector("#power-calculator");
const powerState = {};

function nextPowerSize(requiredKw) {
  return [1, 2, 3, 5, 8, 10, 15, 20].find((size) => size >= requiredKw) || 20;
}

function nextBatterySize(requiredKwh) {
  return [1.28, 2.56, 5.12, 7.68, 10.24, 15.36, 20.48, 25.6].find((size) => size >= requiredKwh) || 25.6;
}

function calculateBackupPower() {
  return calculateBackupPowerExact();
  /* Попередня модель підбору комплекту залишена нижче для історії версій. */
  const data = new FormData(powerCalculator);
  const type = data.get("powerType");
  const area = Math.max(20, Number(data.get("powerArea")) || 20);
  const hours = Number(data.get("powerHours"));
  const hasLights = data.get("powerLights") === "on";
  const hasRouter = data.get("powerRouter") === "on";
  const hasFridge = data.get("powerFridge") === "on";
  const hasHeating = data.get("powerHeating") === "on";
  const hasCctv = data.get("powerCctv") === "on";
  const hasWorkplace = data.get("powerWorkplace") === "on";

  const typeFactor = { apartment: 0.85, house: 1, office: 1.35 }[type];
  const lighting = hasLights ? Math.min(900, area * 4.5) : 0;
  const router = hasRouter ? 35 : 0;
  const fridge = hasFridge ? 140 : 0;
  const heating = hasHeating ? 160 : 0;
  const cctv = hasCctv ? (type === "office" ? 180 : 100) : 0;
  const workplace = hasWorkplace ? (type === "office" ? 450 : 180) : 0;
  const continuousLoad = Math.max(80, Math.round((lighting + router + fridge + heating + cctv + workplace) * typeFactor));
  const surgeLoad = continuousLoad + (hasFridge ? 650 : 0) + (hasHeating ? 250 : 0);
  const inverterKw = nextPowerSize(Math.max(continuousLoad * 1.35, surgeLoad) / 1000);
  const requiredKwh = continuousLoad * hours / 1000 / 0.85;
  const batteryKwh = nextBatterySize(requiredKwh);
  const realRuntime = batteryKwh * 0.85 * 1000 / continuousLoad;
  const inverterPrice = 8500 + inverterKw * 6200;
  const batteryPrice = batteryKwh * 11800;
  const protectionPrice = 6200 + inverterKw * 550;
  const equipment = Math.round(inverterPrice + batteryPrice + protectionPrice);
  const work = Math.round(5200 + inverterKw * 950 + (type === "office" ? 2800 : 0));
  const total = equipment + work;
  const low = Math.round(total * 0.92 / 500) * 500;
  const high = Math.round(total * 1.12 / 500) * 500;

  powerState.message = [
    "Попередній розрахунок резервного живлення Alt-Cam",
    "",
    `Об’єкт: ${powerCalculator.elements.powerType.options[powerCalculator.elements.powerType.selectedIndex].text}`,
    `Площа: ${area} м²`,
    `Потрібна автономність: ${hours} год`,
    `Розрахункове навантаження: ${continuousLoad} Вт`,
    "",
    `Інвертор: ${inverterKw} кВт, чиста синусоїда`,
    `Акумулятор LiFePO₄: ${batteryKwh.toFixed(2)} кВт·год`,
    `Очікувана автономність: близько ${realRuntime.toFixed(1)} год`,
    `Обладнання: близько ${money(equipment)}`,
    `Монтаж і запуск: близько ${money(work)}`,
    `Загальний діапазон: ${money(low)} — ${money(high)}`,
    "",
    "Потрібна консультація та точний розрахунок."
  ].join("\n");

  document.querySelector("#power-hours-output").textContent = `${hours} год`;
  document.querySelector("#power-total").textContent = `${money(low)} — ${money(high)}`;
  document.querySelector("#power-load").textContent = `${continuousLoad} Вт`;
  document.querySelector("#power-inverter").textContent = `${inverterKw} кВт, чистий синус`;
  document.querySelector("#power-battery").textContent = `${batteryKwh.toFixed(2)} кВт·год`;
  document.querySelector("#power-runtime").textContent = `≈ ${realRuntime.toFixed(1)} год`;
  document.querySelector("#power-equipment").textContent = `≈ ${money(equipment)}`;
  document.querySelector("#power-work").textContent = `≈ ${money(work)}`;
}

function formatRuntime(hoursValue) {
  let hours = Math.floor(hoursValue);
  let minutes = Math.round((hoursValue - hours) * 60);
  if (minutes === 60) {
    hours += 1;
    minutes = 0;
  }
  return `${hours} год. ${String(minutes).padStart(2, "0")} хв.`;
}

function calculateBackupPowerExact() {
  const data = new FormData(powerCalculator);
  const load = Math.max(1, Number(data.get("powerLoad")) || 1);
  const voltage = Number(data.get("powerVoltage"));
  const capacityAh = Math.max(1, Number(data.get("powerAh")) || 1);
  const batteryCount = Math.max(1, Number(data.get("powerCount")) || 1);
  const dod = Number(data.get("powerBatteryType"));
  const efficiency = Number(data.get("powerEfficiency"));
  const totalCapacityKwh = capacityAh * voltage * batteryCount / 1000;
  const effectiveWh = capacityAh * voltage * batteryCount * dod * efficiency;
  const runtimeHours = effectiveWh / load;
  const runtimeText = formatRuntime(runtimeHours);
  const batteryLabel = powerCalculator.elements.powerBatteryType.options[
    powerCalculator.elements.powerBatteryType.selectedIndex
  ].text;
  const inverterLabel = powerCalculator.elements.powerEfficiency.options[
    powerCalculator.elements.powerEfficiency.selectedIndex
  ].text;

  powerState.message = [
    "Електротехнічний розрахунок резервного живлення Alt-Cam",
    "",
    `Навантаження: ${load} Вт`,
    `Система: ${voltage} V`,
    `Акумулятори: ${batteryCount} × ${capacityAh} А·год`,
    `Тип АКБ: ${batteryLabel}`,
    `Інвертор: ${inverterLabel}`,
    "",
    `Загальний запас: ${totalCapacityKwh.toFixed(2)} кВт·год`,
    `Доступна енергія: ${Math.round(effectiveWh)} Вт·год`,
    `Час автономної роботи: ${runtimeText}`,
    "",
    "Потрібен підбір сумісного інвертора та акумуляторів."
  ].join("\n");

  document.querySelector("#power-runtime-main").textContent = runtimeText;
  document.querySelector("#power-load").textContent = `${load} Вт`;
  document.querySelector("#power-capacity").textContent = `${totalCapacityKwh.toFixed(2)} кВт·год`;
  document.querySelector("#power-effective").textContent = `${Math.round(effectiveWh)} Вт·год`;
  document.querySelector("#power-dod").textContent = `${Math.round(dod * 100)}%`;
  document.querySelector("#power-loss").textContent = `${Math.round((1 - efficiency) * 100)}%`;
}

powerCalculator.addEventListener("input", calculateBackupPower);
powerCalculator.addEventListener("change", calculateBackupPower);
document.querySelector("#send-power-calculation").addEventListener("click", () => {
  trackEvent("calculator_send", { mode: "backup_power" });
  window.open(telegramUrl(powerState.message), "_blank", "noopener,noreferrer");
});
calculateBackupPower();

const ajaxCalculator = document.querySelector("#ajax-calculator");
const ajaxState = {};

function calculateAjaxSystem() {
  return calculateAjaxAccessExact();
  /* Попередня площинна модель залишена нижче для історії версій. */
  const data = new FormData(ajaxCalculator);
  const type = data.get("ajaxType");
  const area = Math.max(20, Number(data.get("ajaxArea")) || 20);
  const floors = Math.max(1, Number(data.get("ajaxFloors")) || 1);
  const doors = Math.max(1, Number(data.get("ajaxDoors")) || 1);
  const windows = Math.max(0, Number(data.get("ajaxWindows")) || 0);
  const includeFire = data.get("ajaxFire") === "on";
  const includeLeaks = data.get("ajaxLeaks") === "on";
  const includeKeypad = data.get("ajaxKeypad") === "on";
  const includeSiren = data.get("ajaxSiren") === "on";

  const coverage = { apartment: 45, house: 55, office: 50, warehouse: 75 }[type];
  const motion = Math.max(floors, Math.ceil(area / coverage));
  const opening = doors + windows;
  const fire = includeFire ? Math.max(floors, Math.ceil(area / 80)) : 0;
  const leaks = includeLeaks ? Math.max(1, type === "house" ? floors + 1 : Math.ceil(area / 120)) : 0;
  const totalDevices = 1 + motion + opening + fire + leaks + (includeKeypad ? 1 : 0) + (includeSiren ? 1 : 0);
  const hubName = totalDevices > 28 || type === "warehouse" ? "Hub 2 Plus" : "Hub 2";
  const hubPrice = hubName === "Hub 2 Plus" ? 10500 : 7200;
  const equipment = Math.round(
    hubPrice +
    motion * 1950 +
    opening * 1250 +
    fire * 3850 +
    leaks * 1550 +
    (includeKeypad ? 3700 : 0) +
    (includeSiren ? 2450 : 0)
  );
  const work = Math.round(2800 + (totalDevices - 1) * 520 + floors * 450);
  const total = equipment + work;
  const low = Math.round(total * 0.94 / 500) * 500;
  const high = Math.round(total * 1.1 / 500) * 500;

  ajaxState.message = [
    "Попередній розрахунок системи Ajax — Alt-Cam",
    "",
    `Об’єкт: ${ajaxCalculator.elements.ajaxType.options[ajaxCalculator.elements.ajaxType.selectedIndex].text}`,
    `Площа: ${area} м², поверхів: ${floors}`,
    `Двері: ${doors}, вікна: ${windows}`,
    "",
    `Централь: Ajax ${hubName}`,
    `Датчики руху: ${motion} шт.`,
    `Датчики відкриття: ${opening} шт.`,
    `Пожежні датчики: ${fire} шт.`,
    `Датчики протікання: ${leaks} шт.`,
    `Клавіатура: ${includeKeypad ? "так" : "ні"}`,
    `Сирена: ${includeSiren ? "так" : "ні"}`,
    `Усього пристроїв: ${totalDevices}`,
    "",
    `Обладнання: близько ${money(equipment)}`,
    `Монтаж і налаштування: близько ${money(work)}`,
    `Загальний діапазон: ${money(low)} — ${money(high)}`,
    "",
    "Хочу уточнити склад системи."
  ].join("\n");

  document.querySelector("#ajax-total").textContent = `${money(low)} — ${money(high)}`;
  document.querySelector("#ajax-devices").textContent = totalDevices;
  document.querySelector("#ajax-hub").textContent = hubName;
  document.querySelector("#ajax-motion").textContent = `${motion} шт.`;
  document.querySelector("#ajax-opening").textContent = `${opening} шт.`;
  document.querySelector("#ajax-safety").textContent = `${fire} / ${leaks} шт.`;
  document.querySelector("#ajax-equipment").textContent = `≈ ${money(equipment)}`;
  document.querySelector("#ajax-work").textContent = `≈ ${money(work)}`;
}

function calculateAjaxAccessExact() {
  const data = new FormData(ajaxCalculator);
  const includeHub = data.get("ajaxHub") === "on";
  const motion = Math.max(0, Number(data.get("ajaxMotion")) || 0);
  const door = Math.max(0, Number(data.get("ajaxDoor")) || 0);
  const leaks = Math.max(0, Number(data.get("ajaxLeaks")) || 0);
  const includeLock = data.get("accessLock") === "on";
  const includeController = data.get("accessController") === "on";
  const includeIntercom = data.get("accessIntercom") === "on";
  const includeInstall = data.get("securityInstall") === "on";
  const hasAjax = includeHub || motion + door + leaks > 0;
  const hasAccess = includeLock || includeController;
  const hasWiredSystem = hasAccess || includeIntercom;
  const sensorCount = motion + door + leaks;

  const ajaxEquipment =
    (includeHub ? 5100 : 0) +
    motion * 1350 +
    door * 1050 +
    leaks * 1250;
  const accessEquipment =
    (includeLock ? 2100 : 0) +
    (includeController ? 3600 : 0) +
    (includeIntercom ? 8900 : 0) +
    (hasAccess ? 1200 : 0);
  const materials = hasWiredSystem ? 900 : 0;
  const work = includeInstall
    ? (hasAjax ? 1000 + sensorCount * 200 : 0) +
      (hasAccess ? 2500 : 0) +
      (includeIntercom ? 1500 : 0)
    : 0;
  const total = ajaxEquipment + accessEquipment + materials + work;
  const totalComponents =
    (includeHub ? 1 : 0) +
    sensorCount +
    (includeLock ? 1 : 0) +
    (includeController ? 1 : 0) +
    (includeIntercom ? 1 : 0) +
    (hasAccess ? 1 : 0);

  ajaxState.message = [
    "Розрахунок Ajax, СКУД та домофонії — Alt-Cam",
    "",
    `Ajax Hub 2: ${includeHub ? "так" : "ні"}`,
    `MotionProtect: ${motion} шт.`,
    `DoorProtect: ${door} шт.`,
    `LeaksProtect: ${leaks} шт.`,
    `Електромагнітний замок: ${includeLock ? "так" : "ні"}`,
    `Контролер і зчитувач: ${includeController ? "так" : "ні"}`,
    `IP-домофон Hikvision: ${includeIntercom ? "так" : "ні"}`,
    `ББЖ 12 В + АКБ 7 А·год: ${hasAccess ? "додано автоматично" : "не потрібен"}`,
    "",
    `Обладнання Ajax: ${money(ajaxEquipment)}`,
    `СКУД, домофонія та ББЖ: ${money(accessEquipment)}`,
    `Витратні матеріали: ${money(materials)}`,
    `Монтаж і програмування: ${money(work)}`,
    `Загальна вартість: ${money(total)}`,
    "",
    "Хочу уточнити цей комплекс."
  ].join("\n");

  document.querySelector("#ajax-total").textContent = money(total);
  document.querySelector("#ajax-devices").textContent = totalComponents;
  document.querySelector("#ajax-equipment-price").textContent = money(ajaxEquipment);
  document.querySelector("#access-equipment-price").textContent = money(accessEquipment);
  document.querySelector("#security-materials-price").textContent = money(materials);
  document.querySelector("#security-work-price").textContent = money(work);
}

ajaxCalculator.addEventListener("input", calculateAjaxSystem);
ajaxCalculator.addEventListener("change", calculateAjaxSystem);
document.querySelector("#send-ajax-calculation").addEventListener("click", () => {
  trackEvent("calculator_send", { mode: "ajax_security" });
  window.open(telegramUrl(ajaxState.message), "_blank", "noopener,noreferrer");
});
calculateAjaxSystem();

const quiz = document.querySelector("#security-quiz");
const quizSteps = [...quiz.querySelectorAll(".quiz-step")];
const quizNext = document.querySelector("#quiz-next");
const quizBack = document.querySelector("#quiz-back");
const quizError = document.querySelector("#quiz-error");
const quizCurrent = document.querySelector("#quiz-current");
const quizPercent = document.querySelector("#quiz-percent");
const quizProgressBar = document.querySelector("#quiz-progress-bar");
let currentQuizStep = 0;

function renderQuizStep() {
  quizSteps.forEach((step, index) => step.classList.toggle("active", index === currentQuizStep));
  const progress = Math.round((currentQuizStep + 1) / quizSteps.length * 100);
  quizCurrent.textContent = currentQuizStep + 1;
  quizPercent.textContent = `${progress}%`;
  quizProgressBar.style.width = `${progress}%`;
  quizBack.disabled = currentQuizStep === 0;
  quizNext.innerHTML = currentQuizStep === quizSteps.length - 1
    ? 'Отримати розрахунок <svg><use href="#i-send"/></svg>'
    : 'Далі <svg><use href="#i-arrow"/></svg>';
  quizError.textContent = "";
}

function validateQuizStep() {
  const activeStep = quizSteps[currentQuizStep];
  if (currentQuizStep < 4) {
    const selected = activeStep.querySelector('input[type="radio"]:checked');
    if (!selected) {
      quizError.textContent = "Оберіть один із варіантів, щоб продовжити.";
      return false;
    }
  } else {
    const name = quiz.elements.quizName.value.trim();
    const contact = quiz.elements.quizContact.value.trim();
    if (!name || !contact) {
      quizError.textContent = "Вкажіть ім’я та номер телефону для зв’язку.";
      return false;
    }
  }
  return true;
}

quizNext.addEventListener("click", () => {
  if (!validateQuizStep()) return;
  if (currentQuizStep < quizSteps.length - 1) {
    currentQuizStep += 1;
    renderQuizStep();
    return;
  }

  const data = new FormData(quiz);
  const message = [
    "Нова заявка з квізу Alt-Cam Security UA",
    "",
    `Об’єкт: ${data.get("quizObject")}`,
    `Кількість камер: ${data.get("quizCameras")}`,
    `Нічне бачення: ${data.get("quizNight")}`,
    `Перегляд з телефону: ${data.get("quizPhoneView")}`,
    "",
    `Ім’я: ${data.get("quizName")}`,
    `Телефон: ${data.get("quizContact")}`,
    "",
    "Прошу підготувати попередній розрахунок."
  ].join("\n");
  sendLeadToCrm({
    type: "quiz",
    object: data.get("quizObject"),
    cameras: data.get("quizCameras"),
    nightVision: data.get("quizNight"),
    phoneView: data.get("quizPhoneView"),
    name: data.get("quizName"),
    phone: data.get("quizContact")
  });
  trackEvent("generate_lead", { form: "quiz", channel: "telegram" });
  window.open(telegramUrl(message), "_blank", "noopener,noreferrer");
});

quizBack.addEventListener("click", () => {
  if (currentQuizStep > 0) {
    currentQuizStep -= 1;
    renderQuizStep();
  }
});

renderQuizStep();
