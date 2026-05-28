#!/usr/bin/env node
// Prepend a fresh build timestamp to large static assets so every Pages
// deploy gets a unique content hash. Works around Cloudflare Pages'
// content-addressed asset CDN, where a failed upload registers the hash
// but not the blob — leaving subsequent deploys with broken pointers
// because CF reports "already uploaded" and skips the file forever.
// See commit a8524ff for the incident this prevents.

const fs = require('fs');
const path = require('path');

const stamp = `/* build: ${new Date().toISOString()} */\n`;
const slashStamp = `// build: ${new Date().toISOString()}\n`;

// Files large or stable enough to risk hash-cache poisoning.
// All are content-only (no parser sensitive to leading comments).
const cssTargets = ['styles.css', 'docs.css'];
const jsTargets  = ['app.min.js', 'translations.min.js', 'globe-engine.min.js', 'iir-db.min.js'];

function strip(content) {
  return content
    .replace(/^\s*\/\* build: [^*]+ \*\/\s*\n/, '')
    .replace(/^\s*\/\* cf-hash-bust: [^*]+ \*\/\s*\n/, '')
    .replace(/^\s*\/\/ build: [^\n]+\n/, '')
    .replace(/^\s*\/\/ cf-hash-bust: [^\n]+\n/, '');
}

function stampFile(file, prefix) {
  const p = path.resolve(file);
  if (!fs.existsSync(p)) return false;
  const original = fs.readFileSync(p, 'utf8');
  fs.writeFileSync(p, prefix + strip(original));
  return true;
}

let n = 0;
for (const f of cssTargets) if (stampFile(f, stamp)) { console.log(`stamped: ${f}`); n++; }
for (const f of jsTargets)  if (stampFile(f, stamp)) { console.log(`stamped: ${f}`); n++; }
console.log(`done — ${n} files stamped`);
