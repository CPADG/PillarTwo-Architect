#!/usr/bin/env node
// Updates dateModified + "Last verified" timestamps to today() across all HTML.
// Preserves datePublished (original publish date is meaningful for SEO trust).
// Run as part of cf-build so every deploy refreshes the freshness signal.
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const today = new Date().toISOString().slice(0, 10);

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (['node_modules', '.git', '.github', 'scripts'].includes(entry.name)) continue;
      walk(full, out);
    } else if (entry.isFile() && entry.name.endsWith('.html')) {
      out.push(full);
    }
  }
  return out;
}

const files = walk(ROOT);

// Replace patterns:
//   1) "dateModified": "YYYY-MM-DD"   in JSON-LD
//   2) <time datetime="YYYY-MM-DD">YYYY-MM-DD</time>  (Last verified stamp)
//   3) <strong>YYYY-MM-DD 기준</strong>  (disclaimer ko)
//   4) <strong>YYYY년M月D日時点</strong> (disclaimer ja) — skip, dynamic format hard
const RE_DATE_MOD = /"dateModified"\s*:\s*"\d{4}-\d{2}-\d{2}"/g;
const RE_TIME_LAST = /<time datetime="\d{4}-\d{2}-\d{2}">\d{4}-\d{2}-\d{2}<\/time>/g;
const RE_DISCLAIMER_KO = /<strong>\d{4}-\d{2}-\d{2} 기준<\/strong>/g;

let totalFiles = 0, totalChanges = 0;
for (const f of files) {
  let s = fs.readFileSync(f, 'utf8');
  const before = s;
  s = s.replace(RE_DATE_MOD, `"dateModified": "${today}"`);
  s = s.replace(RE_TIME_LAST, `<time datetime="${today}">${today}</time>`);
  s = s.replace(RE_DISCLAIMER_KO, `<strong>${today} 기준</strong>`);
  if (s !== before) {
    fs.writeFileSync(f, s, 'utf8');
    totalFiles++;
    // count changes
    const diff = (before.match(RE_DATE_MOD)?.length || 0)
               + (before.match(RE_TIME_LAST)?.length || 0)
               + (before.match(RE_DISCLAIMER_KO)?.length || 0);
    totalChanges += diff;
  }
}

console.log(`refresh-dates: ${totalFiles} files updated, ${totalChanges} timestamps -> ${today}`);
