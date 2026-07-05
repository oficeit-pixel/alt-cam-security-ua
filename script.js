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
    <div class="item"><span>Об’єкт</span><strong>${quote.object}</strong></div>
    <div class="item"><span>Площа</span><strong>${quote.area} м² (${quote.dimensions})</strong></div>
    <div class="item"><span>Висота монтажу</span><strong>${quote.height}</strong></div>
    <div class="item"><span>Якість і архів</span><strong>${quote.quality}, ${quote.archiveDays} днів</strong></div>
  </div>
  <table>
    <tr><td>Камери</td><td>${quote.cameras} шт.</td></tr>
    <tr><td>Реєстратор</td><td>${quote.recorderChannels} каналів</td></tr>
    <tr><td>Кабель</td><td>≈ ${quote.cable} м</td></tr>
    <tr><td>Жорсткий диск</td><td>${quote.storageTb} ТБ</td></tr>
    <tr><td>Резервне живлення</td><td>${quote.includeUps ? "Включено" : "Не включено"}</td></tr>
    <tr><td>Обладнання</td><td>≈ ${money(quote.equipment)}</td></tr>
    <tr><td>Монтаж і налаштування</td><td>≈ ${money(quote.work)}</td></tr>
  </table>
  <div class="total"><span>Орієнтовний бюджет</span><strong>${money(quote.low)} — ${money(quote.high)}</strong></div>
  <footer>Цей документ є попереднім автоматичним розрахунком і не є публічною офертою. Точна конфігурація та вартість визначаються після уточнення зон огляду й умов монтажу.</footer>
  <button class="print" onclick="window.print()">Зберегти як PDF / Друкувати</button>
  </body></html>`);
  proposalWindow.document.close();
  trackEvent("proposal_open", { cameras: quote.cameras });
});
calculateSecuritySystem();

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
