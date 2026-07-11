import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const ROOT = process.cwd();
const TARGET_EXTENSIONS = new Set([".html", ".js", ".json", ".xml"]);
const IGNORED_DIRS = new Set([".git", "node_modules", ".agents", ".codex"]);
const ALLOWED_TERMS = [
  "Hikvision",
  "Dahua",
  "Ajax",
  "U-PROX",
  "IMOU",
  "Uniview",
  "TP-Link",
  "Ubiquiti",
  "MikroTik",
  "NVR",
  "DVR",
  "PTZ",
  "PoE",
  "IP",
  "UPS",
  "FAQ",
  "LiFePO4",
  "AGM",
  "GEL",
  "Android",
  "iOS",
  "Telegram",
  "WhatsApp",
  "RJ-45",
];

const FORBIDDEN_WORDS = [
  "задача",
  "задачі",
  "задачу",
  "задач",
  "отправка",
  "подзвонити",
  "узнать",
  "настройка",
  "оборудование",
  "видеонаблюдение",
  "безопасность",
  "камера работает",
  "заказать",
  "подробнее",
  "скидка",
  "бесплатно",
  "клиент",
  "звонок",
];

function walk(directory) {
  const entries = fs.readdirSync(directory, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      return IGNORED_DIRS.has(entry.name) ? [] : walk(fullPath);
    }
    return TARGET_EXTENSIONS.has(path.extname(entry.name).toLowerCase()) ? [fullPath] : [];
  });
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function normalizeLine(line) {
  let normalized = line.replace(/https?:\/\/[^\s"'<>]+/g, " ");
  normalized = normalized.replace(/\b[\w.-]+@[\w.-]+\.\w+\b/g, " ");
  normalized = normalized.replace(/\b(?:class|id|href|src|rel|type|name|value|for)=["'][^"']*["']/g, " ");
  for (const term of ALLOWED_TERMS) {
    normalized = normalized.replace(new RegExp(escapeRegExp(term), "g"), " ");
  }
  return normalized;
}

const wordPatterns = FORBIDDEN_WORDS.map((word) => ({
  word,
  pattern: new RegExp(`(^|[^\\p{L}])${escapeRegExp(word)}([^\\p{L}]|$)`, "iu"),
}));

const problems = [];

for (const file of walk(ROOT)) {
  const relative = path.relative(ROOT, file);
  const lines = fs.readFileSync(file, "utf8").split(/\r?\n/);
  lines.forEach((line, index) => {
    const normalized = normalizeLine(line);
    for (const { word, pattern } of wordPatterns) {
      if (pattern.test(normalized)) {
        problems.push(`${relative}:${index + 1}: знайдено небажане слово "${word}"`);
      }
    }
  });
}

if (problems.length) {
  console.error(problems.join("\n"));
  process.exit(1);
}

console.log("Український текст перевірено: небажаних слів не знайдено.");
