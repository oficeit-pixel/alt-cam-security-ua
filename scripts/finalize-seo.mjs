import fs from 'node:fs/promises';
import path from 'node:path';

export function enhanceHead(html) {
  if (!/<head\b/i.test(html)) return html;
  html = html.replace(/<link\b[^>]*rel=["'](?:icon|shortcut icon|apple-touch-icon)["'][^>]*>/gi, '');
  const additions = [
    '<link rel="icon" type="image/png" sizes="96x96" href="/assets/favicon-96.png">',
    '<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png">',
  ];
  const title = html.match(/<title>([^<]*)<\/title>/i)?.[1];
  const canonical = html.match(/<link\b[^>]*rel="canonical"[^>]*href="([^"]+)"/i)?.[1];
  const description = html.match(/<meta\b[^>]*name="description"[^>]*content="([^"]*)"/i)?.[1];
  const safe = s => s.replace(/"/g, '&quot;');
  for (const [key, value] of Object.entries({'og:site_name':'ALT-CAM Security UA','og:locale':'uk_UA','og:type':'website','og:title':title,'og:description':description,'og:url':canonical,'og:image':'https://alt-cam.net.ua/assets/alt-cam-mark.png'})) {
    if (value && !html.includes(`property="${key}"`)) additions.push(`<meta property="${key}" content="${safe(value)}">`);
  }
  if (!html.includes('name="twitter:card"')) additions.push('<meta name="twitter:card" content="summary">');
  return html.replace(/<\/head>/i, additions.join('\n') + '\n</head>');
}

export async function finalizeSeo(directory) {
  for (const entry of await fs.readdir(directory, {withFileTypes:true})) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      if (!['assets','social-posts'].includes(entry.name)) await finalizeSeo(file);
    } else if (entry.name.endsWith('.html')) {
      const html = await fs.readFile(file, 'utf8');
      await fs.writeFile(file, enhanceHead(html));
    }
  }
}
