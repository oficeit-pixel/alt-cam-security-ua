import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';

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

const origin = 'https://alt-cam.net.ua';
const xml = value => value.replace(/&/g, '&amp;').replace(/</g, '&lt;');
export async function finalizeSeo(directory) {
  const maps = {pages: [], products: []}, dates = new Map();
  const landingSources = new Map();
  for (const name of await fs.readdir(new URL('../content/',import.meta.url)).catch(()=>[])) {
    if (!/^landing-.*\.md$/.test(name)) continue;
    const source = await fs.readFile(new URL('../content/'+name,import.meta.url),'utf8');
    const slug = source.match(/^slug:\s*([a-z0-9-]+)\s*$/m)?.[1];
    if (slug) landingSources.set(slug+'/index.html','content/'+name);
  }
  function modified(relative) {
    const source = landingSources.get(relative) || (relative.startsWith('products/') ? 'catalog-data.js' : /^(videosposterezhennia|videodomofony|rezervne-zhyvlennia)\//.test(relative) ? 'scripts/build-seo-pages.mjs' : relative.includes('/') ? 'scripts/build-local-pages.mjs' : relative);
    if (!dates.has(source)) {
      let date = '';
      const sources = relative==='index.html' ? ['index.html','content/homepage.md','scripts/build-homepage.mjs','contacts.js','data/service-rates.js'] : [source];
      try { date = execFileSync('git', ['log', '-1', '--format=%cI', '--', ...sources], {encoding:'utf8', stdio:['ignore','pipe','ignore']}).trim(); } catch {}
      dates.set(source, date || new Date().toISOString());
    }
    return dates.get(source);
  }
  async function walk(folder) {
    for (const entry of await fs.readdir(folder, {withFileTypes:true})) {
      const file = path.join(folder, entry.name);
      if (entry.isDirectory()) {
        if (!['assets','social-posts'].includes(entry.name)) await walk(file);
      } else if (entry.name.endsWith('.html')) {
        const relative = path.relative(directory, file).replaceAll('\\', '/');
        const route = '/' + relative.replace(/(^|\/)index\.html$/, '$1');
        const url = origin + route;
        let html = await fs.readFile(file, 'utf8');
        const privatePage = /^(admin(?:\/|\.html$)|blanks\/|.*oauth.*\.html$)/i.test(relative);
        const redirect = /http-equiv=["']refresh["']/i.test(html);
        if (privatePage) {
          html = html.replace(/<meta\b[^>]*name=["']robots["'][^>]*>/gi, '');
          html = html.replace(/<\/head>/i, '<meta name="robots" content="noindex,nofollow"></head>');
        }
        if (!redirect) {
          html = html.replace(/<link\b[^>]*rel=["']canonical["'][^>]*>/gi, '');
          html = html.replace(/<\/head>/i, `<link rel="canonical" href="${url}"></head>`);
        }
        html = html.replace(/href=(["'])(?:\.\/)?index\.html#/g, 'href=$1/#');
        html = enhanceHead(html);
        await fs.writeFile(file, html);
        if (!privatePage && !redirect && !/<meta[^>]+content=["'][^"']*noindex/i.test(html)) {
          if (!/<title>[^<]+<\/title>/i.test(html) || !/<meta[^>]+name="description"[^>]+content="[^"]+"/i.test(html)) throw new Error(`Missing SEO metadata: ${relative}`);
          maps[relative.startsWith('products/') ? 'products' : 'pages'].push({url, date:modified(relative)});
        }
      }
    }
  }
  await walk(directory);
  for (const [name, entries] of Object.entries(maps)) {
    entries.sort((a,b) => a.url.localeCompare(b.url));
    await fs.writeFile(path.join(directory, `sitemap-${name}.xml`), '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + entries.map(({url,date})=>`<url><loc>${xml(url)}</loc><lastmod>${date}</lastmod></url>`).join('') + '</urlset>');
  }
  await fs.writeFile(path.join(directory, 'sitemap.xml'), '<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + Object.keys(maps).map(name=>`<sitemap><loc>${origin}/sitemap-${name}.xml</loc></sitemap>`).join('') + '</sitemapindex>');
  console.log(`Sitemap: ${maps.pages.length} pages, ${maps.products.length} products`);
}
