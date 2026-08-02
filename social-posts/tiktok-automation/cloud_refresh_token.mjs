import crypto from "node:crypto";
import fs from "node:fs/promises";

const encryptedUrl = new URL("cloud-token.enc.json", import.meta.url);
const initMode = process.argv.includes("--init");
const key = Buffer.from(process.env.TIKTOK_TOKEN_ENCRYPTION_KEY ?? "", "base64");

if (key.length !== 32) {
  throw new Error("TIKTOK_TOKEN_ENCRYPTION_KEY must be a base64-encoded 32-byte key.");
}

const encrypt = (value) => {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  const ciphertext = Buffer.concat([cipher.update(value, "utf8"), cipher.final()]);
  return {
    version: 1,
    algorithm: "aes-256-gcm",
    iv: iv.toString("base64"),
    tag: cipher.getAuthTag().toString("base64"),
    ciphertext: ciphertext.toString("base64"),
    updated_at: new Date().toISOString(),
  };
};

const decrypt = (payload) => {
  const decipher = crypto.createDecipheriv(
    "aes-256-gcm",
    key,
    Buffer.from(payload.iv, "base64"),
  );
  decipher.setAuthTag(Buffer.from(payload.tag, "base64"));
  return Buffer.concat([
    decipher.update(Buffer.from(payload.ciphertext, "base64")),
    decipher.final(),
  ]).toString("utf8");
};

if (initMode) {
  const refreshToken = process.env.TIKTOK_REFRESH_TOKEN ?? "";
  const accessToken = process.env.TIKTOK_ACCESS_TOKEN ?? "";
  const obtainedAt = Date.parse(process.env.TIKTOK_TOKEN_OBTAINED_AT ?? "");
  const expiresIn = Number(process.env.TIKTOK_ACCESS_EXPIRES_IN ?? 0) * 1000;
  if (!refreshToken || !accessToken) {
    throw new Error("TIKTOK_REFRESH_TOKEN and TIKTOK_ACCESS_TOKEN are required for initialization.");
  }
  const bundle = JSON.stringify({
    access_token: accessToken,
    refresh_token: refreshToken,
    expires_at: Number.isFinite(obtainedAt + expiresIn)
      ? obtainedAt + expiresIn
      : Date.now(),
  });
  await fs.writeFile(encryptedUrl, `${JSON.stringify(encrypt(bundle), null, 2)}\n`);
  console.log(JSON.stringify({ initialized: true }));
  process.exit(0);
}

const encrypted = JSON.parse(await fs.readFile(encryptedUrl, "utf8"));
const bundle = JSON.parse(decrypt(encrypted));
if (bundle.access_token && Number(bundle.expires_at) > Date.now() + 10 * 60 * 1000) {
  console.log(`::add-mask::${bundle.access_token}`);
  await fs.appendFile(process.env.GITHUB_ENV, `TIKTOK_ACCESS_TOKEN=${bundle.access_token}\n`);
  console.log(JSON.stringify({ reused: true, expires_at: bundle.expires_at }));
  process.exit(0);
}
const refreshToken = bundle.refresh_token;
const response = await fetch("https://open.tiktokapis.com/v2/oauth/token/", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({
    client_key: process.env.TIKTOK_CLIENT_KEY ?? "",
    client_secret: process.env.TIKTOK_CLIENT_SECRET ?? "",
    grant_type: "refresh_token",
    refresh_token: refreshToken,
  }),
});
const payload = await response.json();
if (!response.ok || !payload.access_token) {
  throw new Error(JSON.stringify({
    http: response.status,
    error: payload.error,
    error_description: payload.error_description,
  }));
}

const nextRefreshToken = payload.refresh_token ?? refreshToken;
console.log(`::add-mask::${payload.access_token}`);
console.log(`::add-mask::${nextRefreshToken}`);
await fs.appendFile(process.env.GITHUB_ENV, `TIKTOK_ACCESS_TOKEN=${payload.access_token}\n`);
const nextBundle = JSON.stringify({
  access_token: payload.access_token,
  refresh_token: nextRefreshToken,
  expires_at: Date.now() + Number(payload.expires_in ?? 0) * 1000,
});
await fs.writeFile(encryptedUrl, `${JSON.stringify(encrypt(nextBundle), null, 2)}\n`);
console.log(JSON.stringify({
  refreshed: true,
  scope: payload.scope,
  expires_in: payload.expires_in,
  refresh_expires_in: payload.refresh_expires_in,
}));
