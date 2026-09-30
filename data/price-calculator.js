// Shared estimate model, extracted without changing existing rates or discounts.
(() => {
const PRICE_POLICY = {
  baseDiscount: 0.05,
  highTotalThreshold: 50000,
  highTotalDiscount: 0.05,
  equipmentDepositRate: 0.3
};
const PDF_RATES = window.ALTCAM_RATES;
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


function calculateVideo(data) {
  const clamp = window.ALTCAM_CALC_CORE.clampNumber;
  const indoor = clamp(data.get("videoIndoor"), 0, 64, true);
  const outdoor = clamp(data.get("videoOutdoor"), 0, 64, true);
  const ptz = clamp(data.get("videoPtz"), 0, 16, true);
  const videoBrand = data.get("videoBrand") || "auto";
  const videoResolution = data.get("videoResolution") || "auto";
  const videoNightMode = data.get("videoNightMode") || "auto";
  const nvrChannels = [4,8,16].includes(Number(data.get("videoNvr"))) ? Number(data.get("videoNvr")) : 4;
  const hddTb = [1,2,4].includes(Number(data.get("videoHdd"))) ? Number(data.get("videoHdd")) : 1;
  const includeInstall = data.get("videoInstall") === "on";
  const nvrPrices = { 4: 1800, 8: 3200, 16: 5400 };
  const hddPrices = { 1: 2400, 2: 3500, 4: 5200 };
  const brandProfiles = {
    auto: { label: "Без бренду — підбір за завданням та бюджетом", cameraFactor: 1, nvrFactor: 1 },
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
  const centralPrice = cameras ? Math.round(nvrPrices[nvrChannels] * brandProfile.nvrFactor + hddPrices[hddTb]) : 0;
  const cableMeters = cameras ? indoor * 12 + outdoor * 18 + ptz * 22 + 10 : 0;
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
return { indoor, outdoor, ptz, videoBrand, videoResolution, videoNightMode, nvrChannels, hddTb, includeInstall, brandProfile, resolutionProfile, nightProfile, cameras, cameraPrice, centralPrice, cableMeters, materials, installation, policy };
}
window.ALTCAM_PRICING = Object.freeze({ PRICE_POLICY, roundMoney, priced, applyPricePolicy, videoCameraInstallRate, calculateVideo });
})();
