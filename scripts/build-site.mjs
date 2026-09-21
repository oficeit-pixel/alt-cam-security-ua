import fs from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const out = path.join(root, '_site');
await fs.mkdir(out, { recursive: true });
// Publish an allowlist, never server code, workflow state or credentials.
const files = ['index.html', 'catalog.html', 'admin.html', 'privacy-policy.html',
  'terms-of-service.html', 'delivery-and-returns.html', 'data-deletion.html',
  'tiktok-oauth-callback.html', 'tiktokoVpj7mZL347GV0n5bjaavAO1ZLPlsG1V.txt',
  'robots.txt', 'sitemap.xml', '.nojekyll', 'styles.css', 'custom-style.css',
  'catalog.css', 'admin.css', 'service-prices.css', 'script.js', 'catalog.js',
  'admin.js', 'contacts.js', 'service-rates-draft.js'];
for (const name of files) await fs.copyFile(path.join(root, name), path.join(out, name));
for (const name of ['assets', 'blanks']) await fs.cp(path.join(root, name), path.join(out, name), { recursive: true });
await fs.mkdir(path.join(out, 'feeds'), { recursive: true });
await fs.copyFile('feeds/meta-catalog.csv', path.join(out, 'feeds/meta-catalog.csv'));
await fs.cp('social-posts', path.join(out, 'social-posts'), {
  recursive: true,
  filter: async source => (await fs.stat(source)).isDirectory() || /\.(?:webp|png|jpe?g|gif|mp4)$/i.test(source)
});
const source = await fs.readFile('catalog-data.js', 'utf8');
const match = source.match(/^\s*window\.ALTCAM_CATALOG\s*=\s*([\s\S]*?);?\s*$/);
if (!match) throw new Error('Unexpected catalog format');
const data = JSON.parse(match[1].replace(/;\s*$/, ''));
const compact = `window.ALTCAM_CATALOG=${JSON.stringify(data)};`;
await fs.writeFile(path.join(out, 'catalog-data.js'), compact);
await fs.mkdir(path.join(out, 'admin'), { recursive: true });
const admin = await fs.readFile('admin.html', 'utf8');
await fs.writeFile(path.join(out, 'admin/index.html'), admin.replace('<head>', '<head><base href="../">'));
console.log(`Catalog: ${Buffer.byteLength(source)} → ${Buffer.byteLength(compact)} bytes; ${data.length} products preserved`);
