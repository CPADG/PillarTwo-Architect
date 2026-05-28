#!/usr/bin/env node
// Regenerates sitemap.xml from canonical data + auto-sets lastmod to today.
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const BASE = 'https://pillartwo.app';
const today = new Date().toISOString().slice(0, 10);

function discoverSlugs(dir) {
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.html') && f !== 'index.html')
    .map(f => f.replace(/\.html$/, ''))
    .sort();
}

const slugs = discoverSlugs(path.join(ROOT, 'jurisdictions'));
const slugsEn = discoverSlugs(path.join(ROOT, 'jurisdictions/en'));
const slugsJa = discoverSlugs(path.join(ROOT, 'jurisdictions/ja'));

const missingEn = slugs.filter(s => !slugsEn.includes(s));
const missingJa = slugs.filter(s => !slugsJa.includes(s));
if (missingEn.length || missingJa.length) {
  console.warn('⚠ ko 슬러그 중 en/ja 미생성:', { missingEn, missingJa });
}

function url(loc, priority, changefreq, alts) {
  let s = `  <url>\n    <loc>${BASE}${loc}</loc>\n    <lastmod>${today}</lastmod>\n    <changefreq>${changefreq}</changefreq>\n    <priority>${priority}</priority>\n`;
  if (alts) for (const [hl, href] of alts) s += `    <xhtml:link rel="alternate" hreflang="${hl}" href="${BASE}${href}"/>\n`;
  s += `  </url>\n`;
  return s;
}

let out = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n`;

// — SPA pages (single canonical URL; JS toggles lang in-place, no separate URL per lang)
out += url('/', '1.0', 'weekly');
for (const slug of ['/about', '/overview', '/glossary']) {
  out += url(slug, '0.8', 'monthly');
}

// — Jurisdictions indexes (ko/en/ja separate URLs)
out += url('/jurisdictions/', '0.9', 'weekly', [
  ['ko', '/jurisdictions/'], ['en', '/jurisdictions/en/'], ['ja', '/jurisdictions/ja/'], ['x-default', '/jurisdictions/'],
]);
out += url('/jurisdictions/en/', '0.85', 'weekly', [
  ['ko', '/jurisdictions/'], ['en', '/jurisdictions/en/'], ['ja', '/jurisdictions/ja/'], ['x-default', '/jurisdictions/'],
]);
out += url('/jurisdictions/ja/', '0.85', 'weekly', [
  ['ko', '/jurisdictions/'], ['en', '/jurisdictions/en/'], ['ja', '/jurisdictions/ja/'], ['x-default', '/jurisdictions/'],
]);

// — Jurisdictions country detail × 3 langs
for (const slug of slugs) {
  const alts = [
    ['ko', `/jurisdictions/${slug}`],
    ['en', `/jurisdictions/en/${slug}`],
    ['ja', `/jurisdictions/ja/${slug}`],
    ['x-default', `/jurisdictions/${slug}`],
  ];
  out += url(`/jurisdictions/${slug}`, '0.75', 'monthly', alts);
  if (slugsEn.includes(slug)) out += url(`/jurisdictions/en/${slug}`, '0.7', 'monthly', alts);
  if (slugsJa.includes(slug)) out += url(`/jurisdictions/ja/${slug}`, '0.7', 'monthly', alts);
}

out += `</urlset>\n`;
fs.writeFileSync(path.join(ROOT, 'sitemap.xml'), out, 'utf8');

const urlCount = (out.match(/<url>/g) || []).length;
console.log(`sitemap.xml: ${urlCount} URLs, lastmod=${today}`);
console.log(`  ko detail: ${slugs.length} / en: ${slugsEn.length} / ja: ${slugsJa.length}`);
