#!/usr/bin/env node
// Validates hreflang cluster integrity across the static site.
// Rules:
//   1. Every page that declares hreflang must include itself.
//   2. The set of (hreflang, href) tuples MUST be identical on every page
//      that references the same canonical cluster (reciprocity).
//   3. x-default must exist when ko/en/ja exist.
//   4. ko-KR etc. region codes flagged for review (we use ko/en/ja per OECD docs convention).
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const SCAN_ROOTS = ['', 'jurisdictions', 'jurisdictions/en', 'jurisdictions/ja', 'en', 'ja'];

const files = [];
for (const r of SCAN_ROOTS) {
  const dir = path.join(ROOT, r);
  if (!fs.existsSync(dir)) continue;
  for (const f of fs.readdirSync(dir)) {
    if (f.endsWith('.html')) files.push(path.join(dir, f));
  }
}

const RE_HREFLANG = /<link\s+rel=["']alternate["']\s+hreflang=["']([^"']+)["']\s+href=["']([^"']+)["']/g;
const RE_LINK_ALT_ANY = /rel=["']alternate["']/;
const RE_CANONICAL = /<link\s+rel=["']canonical["']\s+href=["']([^"']+)["']/;

const pages = files.map(f => {
  const s = fs.readFileSync(f, 'utf8');
  const canonical = (s.match(RE_CANONICAL) || [])[1] || null;
  const hreflangs = [...s.matchAll(RE_HREFLANG)].map(m => [m[1], m[2]]);
  return { file: path.relative(ROOT, f), canonical, hreflangs };
});

let errors = 0, warnings = 0;
const cluster = new Map(); // signature -> [files]
for (const p of pages) {
  if (!p.hreflangs.length) continue;
  // 1. self-inclusion
  const langs = p.hreflangs.map(([l]) => l);
  if (!p.hreflangs.some(([_, h]) => h === p.canonical)) {
    console.error(`✗ ${p.file}: canonical (${p.canonical}) not in hreflang set`);
    errors++;
  }
  // 3. x-default presence
  if ((langs.includes('ko') || langs.includes('en') || langs.includes('ja')) && !langs.includes('x-default')) {
    console.error(`✗ ${p.file}: missing x-default`);
    errors++;
  }
  // 4. region-tag warn
  for (const l of langs) {
    if (/-[A-Z]{2}$/.test(l)) {
      console.warn(`⚠ ${p.file}: region-tagged hreflang "${l}" — consider plain "${l.split('-')[0]}"`);
      warnings++;
    }
  }
  // 2. reciprocity: group by sorted signature
  const sig = p.hreflangs.map(([l, h]) => `${l}=${h}`).sort().join('|');
  if (!cluster.has(sig)) cluster.set(sig, []);
  cluster.get(sig).push(p);
}

// Reciprocity: for each cluster, verify every href in sig points to a page in the cluster
let reciprocityViolations = 0;
for (const [sig, members] of cluster) {
  const declaredHrefs = sig.split('|')
    .map(p => p.split('='))
    .filter(([l]) => l !== 'x-default')
    .map(([, h]) => h);
  const memberCanon = new Set(members.map(m => m.canonical));
  for (const h of declaredHrefs) {
    if (!memberCanon.has(h)) {
      console.error(`✗ Cluster references ${h} but that page does NOT echo the same hreflang set`);
      console.error(`  cluster members: ${members.map(m => m.file).join(', ')}`);
      reciprocityViolations++;
      errors++;
    }
  }
}

console.log(`\nhreflang validation:`);
console.log(`  pages scanned: ${pages.length}`);
console.log(`  pages with hreflang: ${pages.filter(p => p.hreflangs.length).length}`);
console.log(`  clusters: ${cluster.size}`);
console.log(`  errors: ${errors}, warnings: ${warnings}`);
process.exit(errors ? 1 : 0);
