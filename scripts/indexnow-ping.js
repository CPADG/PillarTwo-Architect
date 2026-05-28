#!/usr/bin/env node
// IndexNow ping — notifies Bing/Naver of changed URLs.
// Reads sitemap.xml, sends batched URL list to api.indexnow.org.
// Requires INDEXNOW_KEY env var (or scripts/indexnow.key file) and
// a key-verification file at https://pillartwo.app/<KEY>.txt containing the same key.
const fs = require('fs');
const path = require('path');
const https = require('https');

const ROOT = path.resolve(__dirname, '..');
const HOST = 'pillartwo.app';

const KEY = process.env.INDEXNOW_KEY ||
  (fs.existsSync(path.join(ROOT, 'scripts/indexnow.key'))
    ? fs.readFileSync(path.join(ROOT, 'scripts/indexnow.key'), 'utf8').trim()
    : null);

if (!KEY) {
  console.error('✗ INDEXNOW_KEY not set — generate one and place at scripts/indexnow.key (or env)');
  console.error('  e.g. node -e "console.log(require(\'crypto\').randomBytes(16).toString(\'hex\'))"');
  console.error('  Also place a file <KEY>.txt at site root containing the same key.');
  process.exit(1);
}

const sitemap = fs.readFileSync(path.join(ROOT, 'sitemap.xml'), 'utf8');
const urls = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)]
  .map(m => m[1])
  .filter(u => u.includes(HOST));

console.log(`IndexNow: ${urls.length} URLs queued (host=${HOST}, keyPrefix=${KEY.slice(0, 6)}…)`);

const body = JSON.stringify({
  host: HOST,
  key: KEY,
  keyLocation: `https://${HOST}/${KEY}.txt`,
  urlList: urls,
});

const req = https.request({
  hostname: 'api.indexnow.org',
  port: 443,
  path: '/IndexNow',
  method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': Buffer.byteLength(body) },
}, res => {
  let data = '';
  res.on('data', c => data += c);
  res.on('end', () => {
    console.log(`IndexNow response: HTTP ${res.statusCode}`);
    if (data) console.log(data);
    if (res.statusCode >= 200 && res.statusCode < 300) {
      console.log('✓ Submitted. Bing/Yandex will crawl shortly; Naver picks up via Bing endpoint.');
    } else {
      process.exit(2);
    }
  });
});
req.on('error', e => { console.error('IndexNow request failed:', e); process.exit(3); });
req.write(body);
req.end();
