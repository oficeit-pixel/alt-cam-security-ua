import fs from 'node:fs/promises';
import path from 'node:path';
import { buildSeoPages } from './build-seo-pages.mjs';
import { buildProductPages } from './build-product-pages.mjs';
import { buildLocalPages } from './build-local-pages.mjs';
import { finalizeSeo } from './finalize-seo.mjs';
import { localizeCatalog } from './localize-catalog.mjs';
import { renderContacts, renderBusinessDetails, contacts } from './contacts.mjs';
import { buildHomepage } from './build-homepage.mjs';
import { buildLegalPages } from './build-legal-pages.mjs';
import { buildBlog } from './build-blog.mjs';
import { buildTravelPages } from './build-travel-pages.mjs';

const root = process.cwd();
const out = path.join(root, '_site');
// Generated output must not retain products from a previous catalog build.
// Never follow a linked output directory or remove anything outside this root.
if (path.dirname(out) !== root || path.basename(out) !== '_site') throw new Error('Unsafe build output');
const outputStat = await fs.lstat(out).catch(error => { if (error.code !== 'ENOENT') throw error; return null; });
if (outputStat?.isSymbolicLink()) throw new Error('Build output must not be a symlink');
await fs.rm(out, { recursive: true, force: true });
await fs.mkdir(out, { recursive: true });
// Publish an allowlist, never server code, workflow state or credentials.
const files = ['index.html', 'catalog.html', 'admin.html', 'privacy-policy.html',
  'terms-of-service.html', 'delivery-and-returns.html', 'data-deletion.html',
  'tiktok-oauth-callback.html', 'tiktokoVpj7mZL347GV0n5bjaavAO1ZLPlsG1V.txt',
  'robots.txt', 'sitemap.xml', '.nojekyll', 'styles.css', 'custom-style.css',
  'catalog.css', 'admin.css', 'landing.css', 'homepage.css', 'regional-links.css', 'legal.css', 'service-prices.css', 'blog.css', 'script.js', 'catalog.js',
  'admin.js', 'analytics.js', 'contacts.js', 'lead-payload.js', 'cart-link.js', 'cart-state.js', 'ai-chat.js', 'contact-widget.js', 'catalog-canonical.js'];
for (const name of files) await fs.copyFile(path.join(root, name), path.join(out, name));
await buildLegalPages(out);
const homePath = path.join(out, 'index.html');
await fs.writeFile(homePath, await buildHomepage(await fs.readFile(homePath,'utf8')));
// Ship calculator dependencies and consumers as one ordered, content-versioned asset.
// A cached HTML page cannot mix versions or run before a separately failed price script.
const calculatorFiles = ['data/service-rates.js', 'data/calc-core.js', 'data/price-calculator.js', 'data/package-configs.js', 'script.js'];
const calculatorBundle = (await Promise.all(calculatorFiles.map(name => fs.readFile(name, 'utf8')))).join('\n;\n');
const { createHash } = await import('node:crypto');
const calculatorName = `calculator-${createHash('sha256').update(calculatorBundle).digest('hex').slice(0,12)}.js`;
await fs.writeFile(path.join(out, calculatorName), calculatorBundle);
let bundledHome = await fs.readFile(homePath, 'utf8');
for (const name of calculatorFiles.slice(0,-1)) bundledHome = bundledHome.replace(new RegExp('<script src="'+name.replaceAll('.', '\\.')+'(?:\\?[^"<]*)?"></script>'), '');
bundledHome = bundledHome.replace(/<script src="script\.js[^"<]*"><\/script>/, `<script src="${calculatorName}"></script>`);
await fs.writeFile(homePath, bundledHome);
await fs.mkdir(path.join(out, 'data'), { recursive: true });
for (const name of ['service-rates.js', 'services.js', 'calc-core.js', 'price-calculator.js', 'package-configs.js']) {
  await fs.copyFile(path.join(root, 'data', name), path.join(out, 'data', name));
}
await fs.rm(path.join(out, 'service-rates-draft.js'), { force: true });
for (const name of files.filter(name => name.endsWith('.html') && !name.startsWith('admin') && !name.startsWith('tiktok'))) {
  const file=path.join(out,name);
  let html=(await fs.readFile(file,'utf8')).replaceAll('https://oficeit-pixel.github.io/alt-cam-security-ua/','https://alt-cam.net.ua/');
  html=html.replace(/<body([^>]*)>/i,'<body$1><script src="/analytics.js"></script>');
  await fs.writeFile(file,html);
}
for (const name of ['sitemap.xml','robots.txt']) {
  const file=path.join(out,name);await fs.writeFile(file,(await fs.readFile(file,'utf8')).replaceAll('https://oficeit-pixel.github.io/alt-cam-security-ua/','https://alt-cam.net.ua/'));
}
for (const name of ['assets', 'blanks']) await fs.cp(path.join(root, name), path.join(out, name), { recursive: true });
await fs.mkdir(path.join(out, 'feeds'), { recursive: true });
await fs.copyFile('feeds/meta-catalog.csv', path.join(out, 'feeds/meta-catalog.csv'));
await fs.cp('social-posts', path.join(out, 'social-posts'), {
  recursive: true,
  filter: async source => (await fs.stat(source)).isDirectory() || /\.(?:webp|png|jpe?g|gif|mp4)$/i.test(source)
});
// Only the reviewed photo calendar is public; publisher state stays excluded.
for (const name of ['photo-publications-autopost.html', 'photo-publications-autopost-data.js']) {
  await fs.mkdir(path.join(out, 'social-posts/calendar'), { recursive: true });
  await fs.copyFile(path.join('social-posts/calendar', name), path.join(out, 'social-posts/calendar', name));
}
for (const name of ['publishing-posts.json', 'READY_POSTS.md', 'import-report.json']) {
  const relative = path.join('social-posts/content-plans/2026-09-14-photo-publications', name);
  await fs.copyFile(relative, path.join(out, relative));
}
const source = await fs.readFile('catalog-data.js', 'utf8');
const match = source.match(/^\s*window\.ALTCAM_CATALOG\s*=\s*([\s\S]*?);?\s*$/);
if (!match) throw new Error('Unexpected catalog format');
const data = localizeCatalog(JSON.parse(match[1].replace(/;\s*$/, '')));
await buildSeoPages(out, data);
await buildLocalPages(out);
await buildBlog(out);
await buildTravelPages(out);
await buildProductPages(out, data);
const catalogScript=await fs.readFile(path.join(out,'catalog.js'),'utf8');
await fs.writeFile(path.join(out,'catalog.js'),catalogScript.replace('<button class="product-more" data-details="${item.id}">Докладніше</button>','<a class="product-more" href="${item.page_url}">Докладніше</a>'));
const compact = `window.ALTCAM_CATALOG=${JSON.stringify(data)};`;
await fs.writeFile(path.join(out, 'catalog-data.js'), compact);
await fs.mkdir(path.join(out, 'admin'), { recursive: true });
const admin = await fs.readFile('admin.html', 'utf8');
await fs.writeFile(path.join(out, 'admin/index.html'), admin.replace('<head>', '<head><base href="../">'));
await finalizeSeo(out);
async function finalizeContacts(directory) {
  for(const entry of await fs.readdir(directory,{withFileTypes:true})){
    const file=path.join(directory,entry.name);
    if(entry.isDirectory())await finalizeContacts(file);
    else if(entry.name.endsWith('.html')){
      const html=await fs.readFile(file,'utf8');
      const relative=path.relative(out,file).replaceAll('\\','/');
      const internal=/^(admin(?:\/|\.html)|blanks\/|tiktok-oauth-callback\.html)/.test(relative);
      let updated=renderContacts(internal?html:renderBusinessDetails(html));
      updated=updated.replace(/<a\b[^>]*target=["']_blank["'][^>]*>/gi, tag=>{
        const rel=tag.match(/\brel=["']([^"']*)["']/i);
        const value=[...new Set([...(rel?rel[1].split(/\s+/):[]),'noopener','noreferrer'])].join(' ');
        return rel?tag.replace(rel[0],`rel="${value}"`):tag.replace(/>$/, ` rel="${value}">`);
      });
      // Logo mark repeats the adjacent visible brand text; keep it decorative.
      updated=updated.replace(/<img\b(?=[^>]*src="\/?assets\/alt-cam-mark\.png")(?=[^>]*alt="")[^>]*>/g,
        tag=>tag.includes('aria-hidden=')?tag:tag.replace('<img','<img aria-hidden="true"'));
      if(!internal){
        updated=updated.replace(/<script\b[^>]*src="(?:\/)?ai-chat\.js[^\"]*"[^>]*><\/script>/g,'');
        for(const name of ['contacts.js','lead-payload.js','contact-widget.js']){
          if(!new RegExp('src="/?'+name.replaceAll('.','\\.')+'(?:[?\"])').test(updated))updated=updated.replace('</body>',`<script src="/${name}" defer></script></body>`);
        }
      }
      if(!internal&&!updated.includes('src="/cart-state.js"')&&!updated.includes('src="cart-state.js"'))updated=updated.replace('</body>','<script src="/cart-state.js"></script></body>');
      if(updated!==html)await fs.writeFile(file,updated);
    }
  }
}
await finalizeContacts(out);
console.log(`Catalog: ${Buffer.byteLength(source)} → ${Buffer.byteLength(compact)} bytes; ${data.length} products preserved`);
