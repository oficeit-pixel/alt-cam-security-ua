/* =========================================================
   SITE_URL: https://oficeit-pixel.github.io/alt-cam-security-ua/
   TODO: вставити реальні контактні дані перед запуском.
   Telegram: ім'я користувача без символу @
   WhatsApp/телефон: тільки цифри у міжнародному форматі
   ========================================================= */
const SITE_URL = "https://oficeit-pixel.github.io/alt-cam-security-ua/";

const CONTACTS = {
  telegram: "OficeITHelp",
  whatsapp: "",
  phone: "",
  phoneLabel: "",
  email: "",
  facebook: "",
  instagram: "",
  tiktok: "",
  messenger: "",
  viber: ""
};

const PRICE_POLICY = {
  baseDiscount: 0.05,
  highTotalThreshold: 50000,
  highTotalDiscount: 0.05,
  equipmentDepositRate: 0.3
};

const PDF_RATES = {
  video: {
    indoorCamera: { one: 1100, two: 800, threeToEight: 600, overEight: 500, heightFactor: 1.3 },
    outdoorCamera: { one: 1200, two: 900, threeToEight: 700, overEight: 600, heightFactor: 1.5 },
    recorderSetup: 800,
    mobileAppSetup: 150,
    speedDomeMin: 1200,
    cableIndoorPerMeter: 16,
    cableOutdoorPerMeter: 22,
    junctionBox: 250,
    bracket: 200
  },
  intercom: {
    analogKit: 1400,
    analogMobileKit: 1800,
    ipKit: 2200,
    ipPanelSurface: 1100,
    ipMonitor: 1100,
    mobilePlace: 300
  },
  access: {
    magneticLock: 700,
    lockConnection: 400,
    controller: 700,
    reader: 600,
    exitButtonSurface: 250,
    backupPower: 350,
    keyProgramming: 20
  },
  ajax: {
    starterKit: 900,
    motionIndoor: 250,
    motionOutdoor: 400,
    opening: 200,
    leak: 100,
    hubSetup: 500,
    sirenIndoor: 250,
    sirenOutdoor: 350,
    keypad: 250
  },
  additional: {
    routerSetup: 400,
    officeSetup: 500,
    remoteSetupMin: 500,
    remoteSetupMax: 1000,
    cableBoxPerMeter: 35,
    serverCabinetAssembly: 800,
    powerSupply: 350,
    monitorInstall: 300
  }
};

function setHidden(element, shouldHide) {
  if (!element) return;
  element.classList.toggle("is-hidden", shouldHide);
  element.toggleAttribute("aria-hidden", shouldHide);
  if (shouldHide) {
    element.setAttribute("tabindex", "-1");
  } else {
    element.removeAttribute("tabindex");
  }
}

function roundMoney(value) {
  return Math.round(value / 10) * 10;
}

function priced(value) {
  return roundMoney(value * (1 - PRICE_POLICY.baseDiscount));
}

function applyPricePolicy(equipment, work, materials = 0) {
  const original = roundMoney(equipment + work + materials);
  const afterBaseDiscount = roundMoney(original * (1 - PRICE_POLICY.baseDiscount));
  const highTotalDiscount = afterBaseDiscount > PRICE_POLICY.highTotalThreshold
    ? roundMoney(afterBaseDiscount * PRICE_POLICY.highTotalDiscount)
    : 0;
  const total = roundMoney(afterBaseDiscount - highTotalDiscount);
  const discount = original - total;
  const deposit = roundMoney(Math.max(0, equipment) * PRICE_POLICY.equipmentDepositRate);
  return { original, afterBaseDiscount, highTotalDiscount, total, discount, deposit };
}

function videoCameraInstallRate(count, isOutdoor) {
  if (count <= 0) return 0;
  const table = isOutdoor ? PDF_RATES.video.outdoorCamera : PDF_RATES.video.indoorCamera;
  if (count === 1) return table.one;
  if (count === 2) return table.two;
  if (count <= 8) return table.threeToEight;
  return table.overEight;
}

function buildQuoteMessage(state, client = null) {
  const clientLines = client ? [
    "",
    "Дані клієнта:",
    `Ім’я: ${client.name}`,
    `Телефон: ${client.phone}`,
    `Email: ${client.email}`,
    `Бажана дата: ${client.date}`,
    `Коментар: ${client.comment || "Не вказано"}`
  ] : [];
  return [
    state.message,
    "",
    `Сума до знижок: ${money(state.quote.original)}`,
    `Знижка: ${money(state.quote.discount)}`,
    `До сплати після знижок: ${money(state.quote.total)}`,
    `Рекомендований завдаток на обладнання: ${money(state.quote.deposit)}`,
    ...clientLines
  ].join("\n");
}

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
      source: SITE_URL,
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

const onlineDemoModal = document.querySelector("#online-demo-modal");
const onlineDemoTrigger = document.querySelector(".online-demo-trigger");
const onlineDemoCloseElements = document.querySelectorAll("[data-close-online-demo]");
const onlineDemoCtaElements = document.querySelectorAll("[data-online-demo-cta]");
const onlineDemoVideo = document.querySelector(".demo-video-frame");

function openOnlineDemo() {
  if (!onlineDemoModal) return;
  onlineDemoModal.classList.remove("video-finished");
  if (onlineDemoVideo) {
    onlineDemoVideo.currentTime = 0;
    onlineDemoVideo.play().catch(() => {});
  }
  onlineDemoModal.hidden = false;
  document.body.classList.add("modal-open");
  onlineDemoModal.querySelector(".online-demo-close")?.focus();
}

function closeOnlineDemo() {
  if (!onlineDemoModal || onlineDemoModal.hidden) return;
  onlineDemoModal.hidden = true;
  if (onlineDemoVideo) {
    onlineDemoVideo.pause();
    onlineDemoVideo.currentTime = 0;
  }
  document.body.classList.remove("modal-open");
  onlineDemoTrigger?.focus();
}

onlineDemoTrigger?.addEventListener("click", openOnlineDemo);
onlineDemoCloseElements.forEach((element) => element.addEventListener("click", closeOnlineDemo));
onlineDemoVideo?.addEventListener("ended", () => {
  onlineDemoModal?.classList.add("video-finished");
});
onlineDemoCtaElements.forEach((element) => {
  element.addEventListener("click", () => {
    onlineDemoModal.hidden = true;
    if (onlineDemoVideo) {
      onlineDemoVideo.pause();
      onlineDemoVideo.currentTime = 0;
    }
    document.body.classList.remove("modal-open");
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeOnlineDemo();
  }
});

const leadForm = document.querySelector("#lead-form");
let selectedChannel = "telegram";

leadForm.querySelectorAll("[data-channel]").forEach((button) => {
  if (button.dataset.channel === "whatsapp") {
    setHidden(button, !CONTACTS.whatsapp);
  }
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
  setHidden(phoneLink, !CONTACTS.phone);
  if (!CONTACTS.phone) return;
  phoneLink.href = `tel:${CONTACTS.phone}`;
  if (!phoneLink.classList.contains("mobile-call")) {
    phoneLink.textContent = CONTACTS.phoneLabel;
  }
});

const emailLink = document.querySelector(".js-email");
setHidden(emailLink, !CONTACTS.email);
if (CONTACTS.email) {
  emailLink.href = `mailto:${CONTACTS.email}`;
  emailLink.textContent = CONTACTS.email;
}

["facebook", "instagram", "tiktok"].forEach((network) => {
  const link = document.querySelector(`.js-${network}`);
  setHidden(link, !CONTACTS[network]);
  if (!CONTACTS[network]) return;
  link.href = CONTACTS[network];
  link.target = "_blank";
  link.rel = "noopener noreferrer";
});

const messengerLink = document.querySelector(".js-messenger");
setHidden(messengerLink, !CONTACTS.messenger);
if (CONTACTS.messenger) {
  messengerLink.href = CONTACTS.messenger;
  messengerLink.target = "_blank";
  messengerLink.rel = "noopener noreferrer";
}

const viberLink = document.querySelector(".js-viber");
setHidden(viberLink, !CONTACTS.viber);
if (CONTACTS.viber) {
  viberLink.href = `viber://chat?number=${encodeURIComponent(CONTACTS.viber)}`;
}

const whatsAppLink = document.querySelector(".js-whatsapp");
setHidden(whatsAppLink, !CONTACTS.whatsapp);
if (CONTACTS.whatsapp) {
  whatsAppLink.href = `https://wa.me/${CONTACTS.whatsapp}?text=${encodeURIComponent("Вітаю! Хочу отримати консультацію щодо системи безпеки.")}`;
  whatsAppLink.target = "_blank";
  whatsAppLink.rel = "noopener noreferrer";
}

const quoteModal = document.querySelector("#quote-modal");
const quoteForm = document.querySelector("#quote-confirm-form");
const quoteSummaryList = document.querySelector("#quote-summary-list");
const quoteCloseElements = document.querySelectorAll("[data-close-quote]");
let activeQuoteState = null;

function quoteRows(state) {
  const quote = state.quote;
  return [
    ["Тип розрахунку", quote.type],
    ["Сума до знижок", money(quote.original)],
    ["Знижка", `− ${money(quote.discount)}`],
    ["До сплати після знижок", money(quote.total), "quote-total"],
    ["Завдаток на обладнання", money(quote.deposit)]
  ];
}

function renderQuoteSummary(state) {
  quoteSummaryList.innerHTML = quoteRows(state).map(([label, value, className]) => (
    `<div class="${className || ""}"><span>${label}</span><strong>${value}</strong></div>`
  )).join("");
}

function openQuoteModal(state) {
  activeQuoteState = state;
  renderQuoteSummary(state);
  quoteModal.hidden = false;
  document.body.classList.add("modal-open");
  quoteForm.querySelector("input[name='quoteName']")?.focus();
}

function closeQuoteModal() {
  if (!quoteModal || quoteModal.hidden) return;
  quoteModal.hidden = true;
  document.body.classList.remove("modal-open");
}

quoteCloseElements.forEach((element) => element.addEventListener("click", closeQuoteModal));

quoteForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!quoteForm.reportValidity() || !activeQuoteState) return;

  const data = new FormData(quoteForm);
  const client = {
    name: data.get("quoteName").trim(),
    phone: data.get("quotePhone").trim(),
    email: data.get("quoteEmail").trim(),
    date: data.get("quoteDate"),
    comment: data.get("quoteComment").trim()
  };
  const message = buildQuoteMessage(activeQuoteState, client);
  sendLeadToCrm({
    type: "quote_confirmation",
    quote: activeQuoteState.quote,
    message,
    client,
    nextStep: "Після підтвердження дати надіслати клієнту email із розрахунком і сумою завдатку на обладнання."
  });
  trackEvent("quote_confirm", { type: activeQuoteState.quote.type, total: activeQuoteState.quote.total });
  window.open(telegramUrl(message), "_blank", "noopener,noreferrer");
  quoteForm.reset();
  closeQuoteModal();
  alert("Заявку на підтвердження надіслано. Менеджер перевірить дату та підготує email із розрахунком і завдатком.");
});

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
  const videoBrand = data.get("videoBrand") || "auto";
  const videoResolution = data.get("videoResolution") || "auto";
  const videoNightMode = data.get("videoNightMode") || "auto";
  const nvrChannels = Number(data.get("videoNvr"));
  const hddTb = Number(data.get("videoHdd"));
  const includeInstall = data.get("videoInstall") === "on";
  const nvrPrices = { 4: 1800, 8: 3200, 16: 5400 };
  const hddPrices = { 1: 2400, 2: 3500, 4: 5200 };
  const brandProfiles = {
    auto: { label: "Без бренду — підбір за задачею та бюджетом", cameraFactor: 1, nvrFactor: 1 },
    hikvision: { label: "Hikvision — AcuSense / ColorVu", cameraFactor: 1.18, nvrFactor: 1.12 },
    dahua: { label: "Dahua — WizSense / TiOC", cameraFactor: 1.15, nvrFactor: 1.1 },
    uniview: { label: "Uniview — LightHunter / ColorHunter", cameraFactor: 1.08, nvrFactor: 1.06 },
    imou: { label: "IMOU — дім / малий офіс", cameraFactor: 0.92, nvrFactor: 0.95 }
  };
  const resolutionProfiles = {
    auto: { label: "Роздільна здатність підбирається після огляду зон", factor: 1 },
    "2mp": { label: "2 Мп — базовий огляд", factor: 0.88 },
    "4mp": { label: "4 Мп — оптимальна деталізація", factor: 1 },
    "8mp": { label: "8 Мп / 4K — висока деталізація", factor: 1.45 }
  };
  const nightProfiles = {
    auto: { label: "Нічний режим підбирається по освітленню", factor: 1 },
    ir: { label: "ІЧ-підсвітка", factor: 1 },
    color: { label: "Кольорове нічне бачення", factor: 1.18 },
    ai: { label: "AI-детекція людей / авто", factor: 1.22 }
  };
  const brandProfile = brandProfiles[videoBrand] || brandProfiles.auto;
  const resolutionProfile = resolutionProfiles[videoResolution] || resolutionProfiles.auto;
  const nightProfile = nightProfiles[videoNightMode] || nightProfiles.auto;
  const cameras = indoor + outdoor + ptz;
  const cameraBasePrice = indoor * 1450 + outdoor * 1950 + ptz * 4200;
  const cameraPrice = Math.round(cameraBasePrice * brandProfile.cameraFactor * resolutionProfile.factor * nightProfile.factor);
  const centralPrice = Math.round(nvrPrices[nvrChannels] * brandProfile.nvrFactor + hddPrices[hddTb]);
  const cableMeters = indoor * 12 + outdoor * 18 + ptz * 22 + 10;
  const materials =
    cableMeters * PDF_RATES.video.cableIndoorPerMeter +
    outdoor * (PDF_RATES.video.junctionBox + PDF_RATES.video.bracket) +
    ptz * (PDF_RATES.video.junctionBox + PDF_RATES.video.bracket) +
    indoor * PDF_RATES.video.bracket;
  const installation = includeInstall
    ? indoor * videoCameraInstallRate(indoor, false) +
      outdoor * videoCameraInstallRate(outdoor, true) +
      ptz * PDF_RATES.video.speedDomeMin +
      (cameras ? PDF_RATES.video.recorderSetup + PDF_RATES.video.mobileAppSetup : 0)
    : 0;
  const policy = applyPricePolicy(cameraPrice + centralPrice, installation, materials);
  const channelWarning = cameras > nvrChannels
    ? ` Увага: обраний NVR має ${nvrChannels} каналів для ${cameras} камер.`
    : "";
  const archiveHint = hddTb === 1
    ? "короткий архів для невеликої кількості камер"
    : hddTb === 2
      ? "оптимальний архів для типового об’єкта"
      : "збільшений архів для довшого зберігання";

  calcState.message = [
    "Точний розрахунок IP-відеоспостереження Alt-Cam",
    "",
    `Внутрішні купольні камери: ${indoor} шт.`,
    `Вуличні циліндричні камери: ${outdoor} шт.`,
    `Поворотні PTZ: ${ptz} шт.`,
    `Бренд / клас камер: ${brandProfile.label}`,
    `Роздільна здатність: ${resolutionProfile.label}`,
    `Нічний режим / аналітика: ${nightProfile.label}`,
    `NVR: ${nvrChannels} каналів`,
    `WD Purple: ${hddTb} ТБ (${archiveHint})`,
    "",
    `Камери: ${money(cameraPrice)}`,
    `Центральний вузол: ${money(centralPrice)}`,
    `Витратні матеріали за прайсом: ${money(materials)}`,
    `Монтаж і налаштування за прайсом: ${money(installation)}`,
    `Знижка 5%: застосовано`,
    policy.highTotalDiscount ? `Додаткова знижка 5% від 50 000 грн: ${money(policy.highTotalDiscount)}` : "Додаткова знижка від 50 000 грн: не застосовується",
    `Загальна вартість після знижок: ${money(policy.total)}`,
    `Рекомендований завдаток на обладнання: ${money(policy.deposit)}`,
    channelWarning.trim(),
    "",
    "Хочу уточнити цей розрахунок."
  ].filter(Boolean).join("\n");
  calcState.quote = {
    type: "IP-відеоспостереження",
    indoor,
    outdoor,
    ptz,
    cameras,
    videoBrand: brandProfile.label,
    videoResolution: resolutionProfile.label,
    videoNightMode: nightProfile.label,
    nvrChannels,
    hddTb,
    archiveHint,
    cameraPrice,
    centralPrice,
    materials,
    installation,
    ...policy
  };

  document.querySelector("#calc-total").textContent = money(policy.total);
  document.querySelector("#calc-camera-count").textContent = cameras;
  document.querySelector("#calc-cameras-price").textContent = money(cameraPrice);
  document.querySelector("#calc-central-price").textContent = money(centralPrice);
  document.querySelector("#calc-materials-price").textContent = money(materials);
  document.querySelector("#calc-install-price").textContent = money(installation);
  document.querySelector("#calc-discount").textContent = `− ${money(policy.discount)}`;
  document.querySelector("#calc-deposit").textContent = money(policy.deposit);
  document.querySelector("#calc-note").textContent =
    `Підбір: ${brandProfile.label}; ${resolutionProfile.label}; ${nightProfile.label}. Роботи рахуються за PDF-прайсом монтажу: камери, NVR, мобільний застосунок, кабель і кріплення. ${archiveHint}.${channelWarning}`;
}

calculator.addEventListener("input", calculateSecuritySystem);
calculator.addEventListener("change", calculateSecuritySystem);
document.querySelector("#send-calculation").addEventListener("click", () => {
  trackEvent("calculator_confirm_open", { mode: "video", total: calcState.quote.total });
  openQuoteModal(calcState);
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
    <div class="item"><span>Бренд / клас камер</span><strong>${quote.videoBrand}</strong></div>
    <div class="item"><span>Параметри камер</span><strong>${quote.videoResolution}; ${quote.videoNightMode}</strong></div>
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
  const powerProfileKey = data.get("powerProfile") || "auto";
  const powerBrandKey = data.get("powerBrand") || "auto";
  const reserveFactor = Number(data.get("powerReserve")) || 1.15;
  const voltage = Number(data.get("powerVoltage"));
  const capacityAh = Math.max(1, Number(data.get("powerAh")) || 1);
  const batteryCount = Math.max(1, Number(data.get("powerCount")) || 1);
  const dod = Number(data.get("powerBatteryType"));
  const efficiency = Number(data.get("powerEfficiency"));
  const powerProfiles = {
    auto: { label: "Не знаю — підбір оптимального формату", factor: 1.05 },
    network: { label: "Роутер / NVR / камери", factor: 1 },
    home: { label: "Будинок: котел, світло, зв’язок", factor: 1.12 },
    business: { label: "Офіс / магазин з запасом", factor: 1.18 }
  };
  const powerBrands = {
    auto: { label: "Без бренду — підбір за бюджетом", factor: 1 },
    logicpower: { label: "LogicPower / LP — доступний сегмент", factor: 0.96 },
    must: { label: "Must / Deye — інверторні системи", factor: 1.08 },
    victron: { label: "Victron — преміум-надійність", factor: 1.2 },
    station: { label: "EcoFlow / Bluetti — портативні станції", factor: 1.15 }
  };
  const powerProfile = powerProfiles[powerProfileKey] || powerProfiles.auto;
  const powerBrand = powerBrands[powerBrandKey] || powerBrands.auto;
  const recommendedPower = Math.ceil(load * reserveFactor);
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
  const serviceBase =
    Math.round((
      PDF_RATES.additional.powerSupply +
      PDF_RATES.additional.routerSetup +
      PDF_RATES.additional.officeSetup +
      Math.ceil(load / 500) * PDF_RATES.additional.cableBoxPerMeter * 5
    ) * powerProfile.factor * powerBrand.factor * Math.max(1, reserveFactor / 1.15));
  const policy = applyPricePolicy(0, serviceBase, 0);

  powerState.message = [
    "Електротехнічний розрахунок резервного живлення Alt-Cam",
    "",
    `Формат резерву: ${powerProfile.label}`,
    `Бренд / клас: ${powerBrand.label}`,
    `Навантаження: ${load} Вт`,
    `Рекомендований запас потужності: ${recommendedPower} Вт`,
    `Система: ${voltage} V`,
    `Акумулятори: ${batteryCount} × ${capacityAh} А·год`,
    `Тип АКБ: ${batteryLabel}`,
    `Інвертор: ${inverterLabel}`,
    "",
    `Загальний запас: ${totalCapacityKwh.toFixed(2)} кВт·год`,
    `Доступна енергія: ${Math.round(effectiveWh)} Вт·год`,
    `Час автономної роботи: ${runtimeText}`,
    `Монтаж і налаштування за прайсом: ${money(serviceBase)}`,
    `Знижка 5%: застосовано`,
    policy.highTotalDiscount ? `Додаткова знижка 5% від 50 000 грн: ${money(policy.highTotalDiscount)}` : "Додаткова знижка від 50 000 грн: не застосовується",
    `Орієнтовна вартість робіт після знижок: ${money(policy.total)}`,
    "",
    "Потрібен підбір сумісного інвертора та акумуляторів."
  ].join("\n");
  powerState.quote = {
    type: "Резервне живлення",
    load,
    powerProfile: powerProfile.label,
    powerBrand: powerBrand.label,
    reserveFactor,
    recommendedPower,
    voltage,
    capacityAh,
    batteryCount,
    batteryLabel,
    inverterLabel,
    totalCapacityKwh,
    effectiveWh,
    runtimeText,
    serviceBase,
    equipment: 0,
    work: serviceBase,
    materials: 0,
    ...policy
  };

  document.querySelector("#power-runtime-main").textContent = runtimeText;
  document.querySelector("#power-load").textContent = `${load} Вт`;
  document.querySelector("#power-capacity").textContent = `${totalCapacityKwh.toFixed(2)} кВт·год`;
  document.querySelector("#power-effective").textContent = `${Math.round(effectiveWh)} Вт·год`;
  document.querySelector("#power-dod").textContent = `${Math.round(dod * 100)}%`;
  document.querySelector("#power-loss").textContent = `${Math.round((1 - efficiency) * 100)}%`;
  document.querySelector("#power-service-price").textContent = money(policy.total);
  document.querySelector("#power-discount").textContent = `− ${money(policy.discount)}`;
}

powerCalculator.addEventListener("input", calculateBackupPower);
powerCalculator.addEventListener("change", calculateBackupPower);
document.querySelector("#send-power-calculation").addEventListener("click", () => {
  trackEvent("calculator_confirm_open", { mode: "backup_power", total: powerState.quote.total });
  openQuoteModal(powerState);
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
  const ajaxLineKey = data.get("ajaxLine") || "auto";
  const intercomBrandKey = data.get("intercomBrand") || "auto";
  const accessBrandKey = data.get("accessBrand") || "auto";
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
  const ajaxLines = {
    auto: { label: "Ajax — підбір комплекту після уточнення об’єкта", hubPrice: 5100, sensorFactor: 1 },
    hub2: { label: "Ajax Hub 2 — базова охорона", hubPrice: 5100, sensorFactor: 1 },
    motioncam: { label: "Ajax Hub 2 + MotionCam — фотоверифікація", hubPrice: 6500, sensorFactor: 1.25 },
    hub2plus: { label: "Ajax Hub 2 Plus — більше каналів зв’язку", hubPrice: 9800, sensorFactor: 1.15 }
  };
  const intercomBrands = {
    auto: { label: "Домофонія — підбір під об’єкт", factor: 1 },
    hikvision: { label: "Hikvision — IP-домофонія", factor: 1 },
    dahua: { label: "Dahua — IP-домофонія", factor: 1.05 },
    akuvox: { label: "Akuvox — преміум IP-рішення", factor: 1.25 },
    basip: { label: "BAS-IP — преміум-домофонія", factor: 1.35 }
  };
  const accessBrands = {
    auto: { label: "СКУД — підбір за задачею", factor: 1 },
    yli: { label: "YLI / ATIS — замки та контролери", factor: 1 },
    hikvision: { label: "Hikvision — СКУД + відео", factor: 1.15 },
    zkteco: { label: "ZKTeco — доступ і облік часу", factor: 1.1 },
    premium: { label: "Преміум-комплект з розширенням", factor: 1.22 }
  };
  const ajaxLine = ajaxLines[ajaxLineKey] || ajaxLines.auto;
  const intercomBrand = intercomBrands[intercomBrandKey] || intercomBrands.auto;
  const accessBrand = accessBrands[accessBrandKey] || accessBrands.auto;

  const ajaxEquipment =
    (includeHub ? ajaxLine.hubPrice : 0) +
    Math.round((motion * 1350 + door * 1050 + leaks * 1250) * ajaxLine.sensorFactor);
  const accessCore =
    (includeLock ? 2100 : 0) +
    (includeController ? 3600 : 0) +
    (hasAccess ? 1200 : 0);
  const accessEquipment =
    Math.round(accessCore * accessBrand.factor + (includeIntercom ? 8900 * intercomBrand.factor : 0));
  const materials = hasWiredSystem
    ? PDF_RATES.additional.cableBoxPerMeter * 12 + PDF_RATES.video.junctionBox
    : 0;
  const work = includeInstall
    ? (hasAjax ? PDF_RATES.ajax.starterKit + PDF_RATES.ajax.hubSetup : 0) +
      motion * PDF_RATES.ajax.motionIndoor +
      door * PDF_RATES.ajax.opening +
      leaks * PDF_RATES.ajax.leak +
      (includeLock ? PDF_RATES.access.magneticLock + PDF_RATES.access.lockConnection : 0) +
      (includeController ? PDF_RATES.access.controller + PDF_RATES.access.reader : 0) +
      (includeIntercom ? PDF_RATES.intercom.ipKit + PDF_RATES.intercom.mobilePlace : 0) +
      (hasAccess ? PDF_RATES.access.backupPower : 0)
    : 0;
  const policy = applyPricePolicy(ajaxEquipment + accessEquipment, work, materials);
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
    `Лінійка Ajax: ${ajaxLine.label}`,
    `Хаб Ajax: ${includeHub ? "так" : "ні"}`,
    `MotionProtect: ${motion} шт.`,
    `DoorProtect: ${door} шт.`,
    `LeaksProtect: ${leaks} шт.`,
    `Бренд / клас СКУД: ${accessBrand.label}`,
    `Бренд домофонії: ${intercomBrand.label}`,
    `Електромагнітний замок: ${includeLock ? "так" : "ні"}`,
    `Контролер і зчитувач: ${includeController ? "так" : "ні"}`,
    `IP-домофон: ${includeIntercom ? "так" : "ні"}`,
    `ББЖ 12 В + АКБ 7 А·год: ${hasAccess ? "додано автоматично" : "не потрібен"}`,
    "",
    `Обладнання Ajax: ${money(ajaxEquipment)}`,
    `СКУД, домофонія та ББЖ: ${money(accessEquipment)}`,
    `Витратні матеріали: ${money(materials)}`,
    `Монтаж і програмування за прайсом: ${money(work)}`,
    `Знижка 5%: застосовано`,
    policy.highTotalDiscount ? `Додаткова знижка 5% від 50 000 грн: ${money(policy.highTotalDiscount)}` : "Додаткова знижка від 50 000 грн: не застосовується",
    `Загальна вартість після знижок: ${money(policy.total)}`,
    `Рекомендований завдаток на обладнання: ${money(policy.deposit)}`,
    "",
    "Хочу уточнити цей комплекс."
  ].join("\n");
  ajaxState.quote = {
    type: "Ajax, СКУД та домофонія",
    ajaxLine: ajaxLine.label,
    intercomBrand: intercomBrand.label,
    accessBrand: accessBrand.label,
    includeHub,
    motion,
    door,
    leaks,
    includeLock,
    includeController,
    includeIntercom,
    includeInstall,
    ajaxEquipment,
    accessEquipment,
    materials,
    work,
    totalComponents,
    ...policy
  };

  document.querySelector("#ajax-total").textContent = money(policy.total);
  document.querySelector("#ajax-devices").textContent = totalComponents;
  document.querySelector("#ajax-equipment-price").textContent = money(ajaxEquipment);
  document.querySelector("#access-equipment-price").textContent = money(accessEquipment);
  document.querySelector("#security-materials-price").textContent = money(materials);
  document.querySelector("#security-work-price").textContent = money(work);
  document.querySelector("#ajax-discount").textContent = `− ${money(policy.discount)}`;
  document.querySelector("#ajax-deposit").textContent = money(policy.deposit);
}

ajaxCalculator.addEventListener("input", calculateAjaxSystem);
ajaxCalculator.addEventListener("change", calculateAjaxSystem);
document.querySelector("#send-ajax-calculation").addEventListener("click", () => {
  trackEvent("calculator_confirm_open", { mode: "ajax_security", total: ajaxState.quote.total });
  openQuoteModal(ajaxState);
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
    `Перегляд зі смартфона: ${data.get("quizPhoneView")}`,
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
