# ALT-CAM Security UA: premium design system

## Visual direction

Shift the brand from budget utility service to premium tech security partner.

- Background: anthracite, not pure black. Use `#121212` and `#1A1A1A`.
- Main text: off-white `#F5F5F7`.
- Secondary text: muted gray `#86868B`.
- Accent: brand yellow `#FFCC00`, only for CTA, active states, icons, thin highlights and soft glow.
- Avoid yellow as a full banner, big card background or large container.
- Use real installation photos: camera angle, rack, NVR, cable route, intercom panel, phone app screen.

## Ready CSS overrides

```css
:root {
  --bg: #121212;
  --surface: #1a1a1a;
  --text: #f5f5f7;
  --muted: #86868b;
  --accent: #ffcc00;
  --glass: rgba(255,255,255,.03);
  --glass-border: rgba(255,255,255,.08);
}

body {
  font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--text);
}

.btn-primary {
  border-radius: 8px;
  color: #121212;
  background: var(--accent);
  transition: transform .22s ease, box-shadow .22s ease, background .22s ease;
}

.btn-primary:hover {
  transform: scale(1.02);
  box-shadow: 0 0 15px rgba(255,204,0,.4);
}

.glass-card {
  background: rgba(255,255,255,.03);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,.08);
}
```

## Tailwind config

Use this only if the project moves to Tailwind later.

```js
export default {
  theme: {
    extend: {
      colors: {
        altcam: {
          bg: "#121212",
          surface: "#1A1A1A",
          text: "#F5F5F7",
          muted: "#86868B",
          accent: "#FFCC00"
        }
      },
      borderRadius: {
        button: "8px"
      },
      boxShadow: {
        "accent-glow": "0 0 15px rgba(255,204,0,.4)",
        glass: "0 24px 80px rgba(0,0,0,.28)"
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"]
      }
    }
  }
};
```

## Website: works block

The “Київ та область” block should use real photos instead of generic stock.

Best photo set for each case:

- Wide shot: full object context, entrance, shop, office, warehouse, garage.
- Detail shot: camera, junction box, intercom panel, lock, rack or NVR.
- Proof shot: phone with Hik-Connect / DMSS / Ajax app open.
- Result shot: clean final installation with cables hidden or routed neatly.

Use captions like:

- “Магазин, Київ: каса, вхід, архів 14 днів”
- “Приватний будинок, Буча: IP-домофон і відкриття зі смартфона”
- “Склад, Бровари: периметр, нічна підсвітка, контроль воріт”

Do not use copied stock people. If a doorphone banner needs a person, show a courier on the outdoor panel screen and a real smartphone UI with an “Open Door” action.

## Instagram / Facebook / TikTok templates

Format:

- Instagram feed: 1080 × 1350.
- Stories/Reels cover/TikTok: 1080 × 1920.
- Carousel: keep the first slide very clear; one idea per slide.

Layout:

- Background: `#121212`.
- No thick borders and no boxed “poster” frames.
- Use negative space. Let devices, cameras and text breathe.
- Prefer one real object photo plus one floating UI element.
- Add a subtle glass panel only behind small technical details, not behind the headline.

Text hierarchy:

- H1: bold, 64-92 px for 1080 × 1350.
- Body: 28-36 px, short and direct.
- CTA: yellow button or yellow underline, never a yellow full-width banner.
- Left align headings and keep body text under 2 lines where possible.

Doorphone/intercom banner:

- Left: headline, e.g. “Відкривайте двері зі смартфона”.
- Right: real outdoor panel with courier visible on screen.
- Foreground: smartphone screen with active interface and “Open Door” / “Відкрити” button.
- Remove duplicated stock people and hard borders.
- Use natural spacing and soft shadows to separate objects.

Carousel structure:

1. Problem: “Камера є, але обличчя не видно?”
2. Cause: wrong angle, weak IR, bad archive settings.
3. Fix: correct lens, height, light and storage.
4. Proof: real installation photo.
5. CTA: “Надішліть план об’єкта — підберемо систему”.

## Figma / Canva component rules

- Create styles: `BG/Anthracite`, `Text/Primary`, `Text/Muted`, `Accent/Yellow`.
- Buttons: 8 px radius, yellow fill, black text, subtle glow.
- Cards: glass fill `rgba(255,255,255,.03)`, 1 px border `rgba(255,255,255,.08)`, blur 10.
- Icons: yellow line icons on transparent or dark glass, not yellow tiles.
- Keep brand logo small and premium: top-left or bottom-left, no oversized watermark.
