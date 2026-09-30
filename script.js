/* =========================================================
   SITE_URL: https://alt-cam.net.ua/
   Telegram: ім'я користувача без символу @
   WhatsApp/телефон: тільки цифри у міжнародному форматі
   ========================================================= */
const SITE_URL = "https://alt-cam.net.ua/";

const CONTACTS = window.ALTCAM_CONTACTS || {};

const { PRICE_POLICY, roundMoney, priced, applyPricePolicy, videoCameraInstallRate } = window.ALTCAM_PRICING;

const PDF_RATES = window.ALTCAM_RATES;

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

function formText(data, name, fallback = "Не вказано") {
  const value = data.get(name);
  return value && String(value).trim() ? String(value).trim() : fallback;
}

function collectSiteDiagnostics(data, prefix = "") {
  const field = (name) => `${prefix}${name}`;
  return {
    objectType: formText(data, field("ObjectType"), formText(data, "object")),
    repairStage: formText(data, field("RepairStage"), formText(data, "repairStage")),
    wallMaterial: formText(data, field("WallMaterial"), formText(data, "wallMaterial")),
    mountHeight: formText(data, field("MountHeight"), formText(data, "mountHeight")),
    cableRoute: formText(data, field("CableRoute"), formText(data, "cableRoute")),
    routeLength: formText(data, field("RouteLength"), formText(data, "routeLength")),
    networkPower: formText(data, field("NetworkPower"), formText(data, "networkPower")),
    directionDetails: formText(data, field("DirectionDetails"), "Не вказано"),
    photoGeneral: data.get(`${prefix}PhotoGeneral`) === "on" || data.get("photoReady") === "on",
    photoNode: data.get(`${prefix}PhotoNode`) === "on" || data.get("photoReady") === "on",
    photoComplex: data.get(`${prefix}PhotoComplex`) === "on" || data.get("photoReady") === "on"
  };
}

function diagnosticLines(diagnostics) {
  if (!diagnostics) return [];
  return [
    "",
    "Технічний контур об’єкта:",
    `Тип об’єкта: ${diagnostics.objectType}`,
    `Стадія ремонту: ${diagnostics.repairStage}`,
    `Стіни / стеля: ${diagnostics.wallMaterial}`,
    `Висота монтажу: ${diagnostics.mountHeight}`,
    `Кабельні траси: ${diagnostics.cableRoute}`,
    `Найдовша траса: ${diagnostics.routeLength === "Не вказано" ? diagnostics.routeLength : `${diagnostics.routeLength} м`}`,
    `Інтернет / 220 В / доступ: ${diagnostics.networkPower}`,
    `Деталі за напрямком: ${diagnostics.directionDetails}`,
    "",
    "Фото-діагностика:",
    `Загальний план: ${diagnostics.photoGeneral ? "клієнт підтвердив" : "потрібно запросити"}`,
    `Центральний вузол: ${diagnostics.photoNode ? "клієнт підтвердив" : "потрібно запросити"}`,
    `Складний вузол: ${diagnostics.photoComplex ? "клієнт підтвердив" : "потрібно запросити"}`
  ];
}

function buildQuoteMessage(state, client = null) {
  const clientLines = client ? [
    "",
    "Дані клієнта:",
    `Ім’я: ${client.name}`,
    `Телефон: ${client.phone}`,
    `Email: ${client.email}`,
    `Бажана дата: ${client.date}`,
    `Коментар: ${client.comment || "Не вказано"}`,
    ...diagnosticLines(client.diagnostics)
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
  crmWebhook: `${CONTACTS.apiBase || 'https://alt-cam-crm-api.onrender.com'}/site-lead`,
  ga4Id: "",
  metaPixelId: "",
  clarityId: ""
};

async function sendLeadToCrm(payload) {
  if (!INTEGRATIONS.crmWebhook) return false;
  const lead = window.AltcamLead.buildLeadPayload(payload.type, {
    ...(payload.client || payload),
    message: payload.message,
    details: payload.details || {object:payload.object, cameras:payload.cameras,
      nightVision:payload.nightVision, phoneView:payload.phoneView,
      technicalNote:payload.technicalNote, diagnostics:payload.diagnostics,
      quote:payload.quote}
  });
  try {
    await window.AltcamLead.post('/site-lead', {
      ...payload,
      ...lead,
      client: {...(payload.client || {}), ...lead.client},
      createdAt: new Date().toISOString()
    });
    return true;
  } catch {
    return false;
  }
}

function trackEvent(name, parameters = {}) {
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ event: name, ...parameters });
  window.altcamAnalytics?.(name, parameters);
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

document.querySelectorAll("img[data-approved-asset]").forEach((image) => {
  image.addEventListener("error", () => {
    image.closest(".package-media, .hero-visual")?.classList.add("asset-awaiting-approval");
    image.hidden = true;
  }, { once: true });
});

document.querySelectorAll("[data-track]").forEach((element) => {
  element.addEventListener("click", () => trackEvent(element.dataset.track, {
    location: element.dataset.trackLocation || "page",
    package: element.dataset.package || undefined
  }));
});

document.querySelectorAll("[data-package]").forEach((link) => {
  const config = window.ALTCAM_PACKAGES?.[link.dataset.package];
  if (config) {
    const estimate = window.ALTCAM_PRICING.calculateVideo(new Map(Object.entries(config)));
    const price = link.closest('.package-card')?.querySelector('.package-price');
    if (price) {
      price.textContent = `Орієнтовно ${money(estimate.policy.total)}`;
      const scope = document.createElement('p');
      scope.className = 'service-price-note';
      scope.textContent = `${config.videoIndoor} внутрішні + ${config.videoOutdoor} зовнішні камери, NVR ${config.videoNvr} каналів, HDD ${config.videoHdd} ТБ. Обладнання + монтаж + базові матеріали. Попередня оцінка калькулятора, не фіксована пропозиція.`;
      price.after(scope);
    }
    link.href = '#calculator';
    link.textContent = 'Переглянути розрахунок';
  }
  link.addEventListener("click", () => {
    if (config) {
      const form = document.querySelector('#security-calculator');
      for (const [key, value] of Object.entries({videoBrand:'auto',videoNightMode:'auto',...config})) {
        const field = form.elements.namedItem(key);
        if (!field) continue;
        if (field.type === 'checkbox') field.checked = value === 'on';
        else field.value = String(value);
      }
      form.dispatchEvent(new Event('change', {bubbles:true}));
    }
    sessionStorage.setItem("altcam-selected-package", link.dataset.package);
    document.dispatchEvent(new CustomEvent("altcam:package", { detail: link.dataset.package }));
  });
});

const header = document.querySelector(".header");
const menuButton = document.querySelector(".menu-toggle");
const menu = document.querySelector(".nav-links");
const contact = document.querySelector('.header-contact');
if (contact) {
  const toggle = contact.querySelector('.contact-toggle');
  const panel = contact.querySelector('.header-contact-panel');
  const setOpen = open => {
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
  };
  toggle.addEventListener('click', event => setOpen(event.pointerType === 'mouse' ? true : panel.hidden));
  contact.addEventListener('pointerenter', event => {
    if (event.pointerType === 'mouse') setOpen(true);
  });
  contact.addEventListener('pointerleave', () => {
    if (!contact.contains(document.activeElement)) setOpen(false);
  });
  contact.addEventListener('focusout', event => {
    if (!contact.contains(event.relatedTarget)) setOpen(false);
  });
  document.addEventListener('click', event => {
    if (!contact.contains(event.target)) setOpen(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) { setOpen(false); toggle.focus(); }
  });
}

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

const workCards = document.querySelectorAll(".work-card");

workCards.forEach((card) => {
  card.addEventListener("pointerenter", () => {
    if (window.matchMedia("(hover: hover)").matches) {
      card.classList.add("is-active");
    }
  });

  card.addEventListener("pointerleave", () => {
    if (window.matchMedia("(hover: hover)").matches) {
      card.classList.remove("is-active");
    }
  });

  card.addEventListener("click", () => {
    if (!window.matchMedia("(hover: none)").matches) return;
    const isActive = card.classList.contains("is-active");
    workCards.forEach((item) => item.classList.remove("is-active"));
    card.classList.toggle("is-active", !isActive);
  });
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".work-card")) {
    workCards.forEach((card) => card.classList.remove("is-active"));
  }
});

function telegramUrl(text = "Вітаю! Хочу отримати консультацію щодо системи безпеки.") {
  return CONTACTS.telegram
    ? `https://t.me/${CONTACTS.telegram}?text=${encodeURIComponent(text)}`
    : `https://t.me/share/url?url=&text=${encodeURIComponent(text)}`;
}

function telegramChannelUrl() {
  return CONTACTS.telegramChannel
    ? `https://t.me/${CONTACTS.telegramChannel}`
    : telegramUrl("Вітаю! Хочу перейти до Telegram-каналу Alt-Cam Security UA.");
}

document.querySelectorAll(".js-telegram").forEach((link) => {
  link.href = telegramUrl("Вітаю! Хочу отримати безкоштовну консультацію щодо системи безпеки.");
  link.target = "_blank";
  link.rel = "noopener noreferrer";
});

document.querySelectorAll(".js-telegram-channel").forEach((link) => {
  link.href = telegramChannelUrl();
  link.target = "_blank";
  link.rel = "noopener noreferrer";
});

const onlineDemoModal = document.querySelector("#online-demo-modal");
const onlineDemoTrigger = document.querySelector(".online-demo-trigger");
const onlineDemoCloseElements = document.querySelectorAll("[data-close-online-demo]");
const onlineDemoCtaElements = document.querySelectorAll("[data-online-demo-cta]");
const onlineDemoVideo = document.querySelector(".demo-video-frame");

const calcFab = document.querySelector(".calc-fab");
const footerElement = document.querySelector(".footer");

if (calcFab && footerElement) {
  const setCalcFabFooterState = (footerIsVisible) => {
    calcFab.classList.toggle("is-footer-hidden", footerIsVisible);
    calcFab.setAttribute("aria-hidden", String(footerIsVisible));
    calcFab.tabIndex = footerIsVisible ? -1 : 0;
  };
  const updateCalcFabFooterState = () => {
    const footerTop = footerElement.getBoundingClientRect().top;
    const contactsHashIsActive = window.location.hash === "#contacts";
    setCalcFabFooterState(contactsHashIsActive || footerTop < window.innerHeight - 80);
  };

  updateCalcFabFooterState();
  window.addEventListener("scroll", updateCalcFabFooterState, { passive: true });
  window.addEventListener("resize", updateCalcFabFooterState);
  window.addEventListener("hashchange", updateCalcFabFooterState);

  if ("IntersectionObserver" in window) {
    const calcFabFooterObserver = new IntersectionObserver((entries) => {
      const footerIsVisible = entries.some((entry) => entry.isIntersecting);
      setCalcFabFooterState(footerIsVisible);
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.01 });
    calcFabFooterObserver.observe(footerElement);
  }
}

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

leadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!leadForm.reportValidity()) return;

  const data = new FormData(leadForm);
  const diagnostics = collectSiteDiagnostics(data);
  const message = [
    "Заявка з сайту Alt-Cam Security UA",
    "",
    `Ім’я: ${data.get("name")}`,
    `Телефон: ${data.get("phone")}`,
    `Тип об’єкта: ${data.get("object")}`,
    `Коментар: ${data.get("comment") || "Не вказано"}`,
    ...diagnosticLines(diagnostics),
    "",
    "Наступний крок: попросити клієнта прикріпити 2–3 фото в чаті, якщо фото ще не надіслані."
  ].join("\n");

  const sentToTelegram = await window.AltcamLead.submit(leadForm, event.submitter, message, () => sendLeadToCrm({
    type: "contact_form",
    message,
    name: data.get("name"),
    phone: data.get("phone"),
    object: data.get("object"),
    comment: data.get("comment") || "",
    diagnostics
  }));
  if (sentToTelegram) trackEvent("submit_lead", { form: "contact_form", channel: selectedChannel });
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

["facebook", "instagram", "threads", "tiktok"].forEach((network) => {
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
  const detailsField = quoteForm.querySelector("textarea[name='quoteDirectionDetails']");
  if (detailsField) {
    const type = state.quote.type;
    const placeholders = {
      "IP-відеоспостереження": "Архів 7/14/30 днів, фіксація номерів чи облич, широкий кут 2.8 мм або зум, ColorVu/Full-color, грозозахист для вулиці.",
      "Резервне живлення": "Що має працювати без світла, потрібна автономність 2–4 / 8–12 / 24+ год, місце для інвертора та АКБ, вентиляція.",
      "Ajax, СКУД та домофонія": "Тип дверей, замок уже встановлений чи ні, картки/код/біометрія, тварини вдома, сирени, пультова охорона, виклик на смартфон."
    };
    detailsField.placeholder = placeholders[type] || "Опишіть важливі деталі об’єкта, які впливають на монтаж.";
  }
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

quoteForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!quoteForm.reportValidity() || !activeQuoteState) return;

  const data = new FormData(quoteForm);
  const client = {
    name: data.get("quoteName").trim(),
    phone: data.get("quotePhone").trim(),
    email: data.get("quoteEmail").trim(),
    date: data.get("quoteDate"),
    comment: data.get("quoteComment").trim(),
    diagnostics: collectSiteDiagnostics(data, "quote")
  };
  const message = buildQuoteMessage(activeQuoteState, client);
  const sentToTelegram = await window.AltcamLead.submit(quoteForm, event.submitter, message, () => sendLeadToCrm({
    type: "quote_confirmation",
    quote: activeQuoteState.quote,
    message,
    client,
    diagnostics: client.diagnostics,
    nextStep: "Після підтвердження дати перевірити фото, сформувати картку монтажника, надіслати клієнту email із розрахунком і сумою завдатку на обладнання."
  }));
  if (sentToTelegram) {
    trackEvent("submit_calculator", { type: activeQuoteState.quote.type, total: activeQuoteState.quote.total });
  }
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
}

function calculateSecuritySystemExact() {
  window.ALTCAM_CALC_CORE.clampForm(calculator);
  const data = new FormData(calculator);
  const { indoor, outdoor, ptz, videoBrand, videoResolution, videoNightMode, nvrChannels, hddTb, includeInstall, brandProfile, resolutionProfile, nightProfile, cameras, cameraPrice, centralPrice, cableMeters, materials, installation, policy } = window.ALTCAM_PRICING.calculateVideo(data);
  for (const id of ['send-calculation','download-proposal']) document.getElementById(id).disabled = cameras === 0;
  if (!cameras) {
    calcState.quote = null;
    calcState.message = '';
    for (const id of ['calc-total','calc-cameras-price','calc-central-price','calc-materials-price','calc-install-price','calc-discount','calc-deposit']) document.getElementById(id).textContent = '—';
    document.getElementById('calc-camera-count').textContent = '0';
    document.getElementById('calc-note').textContent = 'Додайте хоча б одну камеру';
    return;
  }
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
  if (!calcState.quote) return;
  trackEvent("calculator_confirm_open", { mode: "video", total: calcState.quote.total });
  openQuoteModal(calcState);
});

document.querySelector("#download-proposal").addEventListener("click", () => {
  if (!calcState.quote) return;
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
}

function calculateBackupPowerExact() {
  window.ALTCAM_CALC_CORE.clampForm(powerCalculator);
  const data = new FormData(powerCalculator);
  const load = window.ALTCAM_CALC_CORE.clampNumber(data.get("powerLoad"), 10, 30000);
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
  const {effectiveWh, runtimeHours} = window.ALTCAM_CALC_CORE.powerRuntime({load, capacityAh, batteryCount, voltage, dod, efficiency});
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

function formatRuntime(hoursValue) {
  let hours = Math.floor(hoursValue);
  let minutes = Math.round((hoursValue - hours) * 60);
  if (minutes === 60) { hours += 1; minutes = 0; }
  return `${hours} год. ${String(minutes).padStart(2, "0")} хв.`;
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
}

function calculateAjaxAccessExact() {
  window.ALTCAM_CALC_CORE.clampForm(ajaxCalculator);
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
    auto: { label: "СКУД — підбір за завданням", factor: 1 },
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

const packageSelection = sessionStorage.getItem("altcam-selected-package");
const packagePresets = {
  "kit-2cam": { cameras: "1–2 камери", note: "Цікавить комплект відеоспостереження на 2 камери." },
  "kit-4cam": { cameras: "3–4 камери", note: "Цікавить комплект відеоспостереження на 4 камери." },
  "kit-8cam": { cameras: "5–8 камер", note: "Цікавить комплект відеоспостереження на 8 камер." },
  "kit-doorphone": { cameras: "Не знаю — потрібна консультація", note: "Цікавить комплект відеодомофона з контролем доступу." },
  "kit-ajax": { cameras: "Не знаю — потрібна консультація", note: "Цікавить комплект охоронної системи Ajax." },
  "kit-ups": { cameras: "Не знаю — потрібна консультація", note: "Потрібне резервне живлення для системи безпеки." }
};
function applyPackagePreset(packageId) {
  const preset = packagePresets[packageId];
  if (!preset) return;
  const cameras = quiz.querySelector(`input[name="quizCameras"][value="${preset.cameras}"]`);
  if (cameras) cameras.checked = true;
  quiz.elements.quizTech.value = preset.note;
}
document.addEventListener("altcam:package", (event) => applyPackagePreset(event.detail));
if (packagePresets[packageSelection]) {
  applyPackagePreset(packageSelection);
  sessionStorage.removeItem("altcam-selected-package");
}

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

quizNext.addEventListener("click", async () => {
  window.AltcamLead.warmup();
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
    `Що відомо про монтаж: ${data.get("quizTech") || "Не вказано"}`,
    `Фото-діагностика: ${data.get("quizPhotoReady") === "on" ? "клієнт готовий підготувати фото" : "потрібно запросити фото"}`,
    "",
    "Перед виїздом уточнити: ремонт, матеріал стін, висоту монтажу, кабельні траси, інтернет і 220 В.",
    "Прошу підготувати попередній розрахунок."
  ].join("\n");
  const sent = await window.AltcamLead.submit(quiz, quizNext, message, () => sendLeadToCrm({
    type: "quiz",
    message,
    object: data.get("quizObject"),
    cameras: data.get("quizCameras"),
    nightVision: data.get("quizNight"),
    phoneView: data.get("quizPhoneView"),
    name: data.get("quizName"),
    phone: data.get("quizContact"),
    technicalNote: data.get("quizTech") || "",
    photoReady: data.get("quizPhotoReady") === "on"
  }));
  if (sent) trackEvent("submit_quiz", { form: "quiz", channel: "telegram" });
});

quizBack.addEventListener("click", () => {
  if (currentQuizStep > 0) {
    currentQuizStep -= 1;
    renderQuizStep();
  }
});

renderQuizStep();
