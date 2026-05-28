#!/usr/bin/env node
// Validates every <script type="application/ld+json"> block across the static site.
// Catches regressions like the EN/JA Article block's stray `if False else` Python expression.
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

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

const RE_BLOCK = /<script type="application\/ld\+json">([\s\S]*?)<\/script>/g;
const files = walk(ROOT);

let totalBlocks = 0, totalFiles = 0, errors = 0;
for (const f of files) {
  const s = fs.readFileSync(f, 'utf8');
  let m;
  let fileBlocks = 0;
  RE_BLOCK.lastIndex = 0;
  while ((m = RE_BLOCK.exec(s)) !== null) {
    fileBlocks++;
    totalBlocks++;
    try {
      const parsed = JSON.parse(m[1]);
      // schema.org minimums
      const items = Array.isArray(parsed) ? parsed : [parsed];
      for (const item of items) {
        if (!item['@context']) {
          console.error(`✗ ${path.relative(ROOT, f)} block ${fileBlocks}: missing @context`);
          errors++;
        }
        if (!item['@type']) {
          console.error(`✗ ${path.relative(ROOT, f)} block ${fileBlocks}: missing @type`);
          errors++;
        }
      }
    } catch (e) {
      console.error(`✗ ${path.relative(ROOT, f)} block ${fileBlocks}: ${e.message}`);
      errors++;
    }
  }
  if (fileBlocks > 0) totalFiles++;
}

console.log(`\nJSON-LD validation:`);
console.log(`  files with JSON-LD: ${totalFiles}`);
console.log(`  total blocks:       ${totalBlocks}`);
console.log(`  errors:             ${errors}`);
process.exit(errors ? 1 : 0);
