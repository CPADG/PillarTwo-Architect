#!/usr/bin/env node
/**
 * build-doc-pages.js — content 페이지(overview/about/glossary)의 언어별 정적 URL 생성.
 *
 * 배경: content 페이지는 본문이 data-i18n 구동(동적). 언어별 실제 URL(/en/overview 등)을
 *       만들어 hreflang·canonical·og·JSON-LD를 언어별로 baked-in 하되, 본문은 data-i18n 유지(DRY).
 *       경로 기반 lang-lock(translations.js)이 /en/·/ja/ 경로에서 언어를 강제하므로 본문도 일치.
 *
 * 동작: ko 원본(overview.html 등)을 템플릿으로, /en/<page>.html · /ja/<page>.html 생성.
 *       + ko 원본에 hreflang 클러스터 + navigate-toggle 패치.
 *       FAQ JSON-LD는 화면에 보이는 항목과 언어가 일치하도록 TRANSLATIONS에서 재생성.
 *
 * 실행: node scripts/build-doc-pages.js [overview|about|glossary ...]   (인자 없으면 overview만)
 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const BASE = 'https://pillartwo.app';

// ── TRANSLATIONS 객체만 안전 추출 (IIFE/함수 실행 없이 객체 리터럴만 eval) ──
function loadTranslations() {
  const src = fs.readFileSync(path.join(ROOT, 'translations.js'), 'utf8');
  const start = src.indexOf('const TRANSLATIONS');
  const eq = src.indexOf('{', start);
  // 객체의 끝: 다음 최상위 선언(`\nlet _lang` 또는 `\nfunction t(`) 직전
  let end = src.indexOf('\nlet _lang');
  if (end < 0) end = src.indexOf('\nfunction t(');
  const objSrc = src.slice(eq, src.lastIndexOf('}', end) + 1);
  // eslint-disable-next-line no-eval
  return eval('(' + objSrc + ')');
}
const T = loadTranslations();
const tr = (lang, key) => (T[lang] && T[lang][key]) ?? (T.ko[key]) ?? key;

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const stripTags = (s) => s.replace(/<[^>]+>/g, '');
const jstr = (s) => JSON.stringify(stripTags(s));

const LANG_LOCALE = { ko: 'ko_KR', en: 'en_US', ja: 'ja_JP' };
const LANG_HTML = { ko: 'ko', en: 'en', ja: 'ja' };

// ── 페이지별 설정 ──
const PAGES = {
  overview: {
    slug: 'overview',
    // FAQ: 보편 항목(q,a 키쌍) — 모든 언어 공통, 화면 표시 순서
    faqUniversal: [
      ['overview.faq.q1', 'overview.faq.a1'],
      ['overview.faq.q2', 'overview.faq.a2'],
      ['overview.faq.q4', 'overview.faq.a4'],
      ['overview.faq.q5', 'overview.faq.a5'],
      ['about.faq.q1', 'about.faq.a1'],
      ['about.faq.q2', 'about.faq.a2'],
      ['about.faq.q3', 'about.faq.a3'],
      ['about.faq.q4', 'about.faq.a4'],
      ['about.faq.q5', 'about.faq.a5'],
    ],
    // lang-only 타이밍 항목 (해당 언어에서만 표시 = 해당 언어 JSON-LD에만 포함). 평문.
    faqLangOnly: {
      ko: { q: '한국은 언제부터 시행되나요?', a: '한국은 국제조세조정에 관한 법률 개정으로 IIR은 2024-01-01 이후 개시 사업연도부터, UTPR은 2025-01-01 이후 개시 사업연도부터, QDMTT는 2026-01-01 이후 개시 사업연도부터 시행됩니다.', after: 'overview.faq.q2' },
      ja: { q: '日本はいつから施行されますか?', a: '日本は、令和5年度税制改正により所得算入規則(IIR)を2024年4月1日以後開始事業年度から、軽課税所得規則(UTPR)および適格国内ミニマム課税(QDMTT)を2026年4月1日以後開始事業年度から施行します。', after: 'overview.faq.q2' },
    },
    hasFaqJsonLd: true,
  },
  about: {
    slug: 'about',
    faqUniversal: [
      ['about.faq.q1', 'about.faq.a1'],
      ['about.faq.q2', 'about.faq.a2'],
      ['about.faq.q3', 'about.faq.a3'],
      ['about.faq.q4', 'about.faq.a4'],
      ['about.faq.q5', 'about.faq.a5'],
    ],
    faqLangOnly: {},
    hasFaqJsonLd: true,
  },
  glossary: {
    // 정적 3개국어 meta + DefinedTermSet(정의만 data-i18n). FAQ 없음.
    // meta는 정적 트라이링궐이라 그대로 두고(번역키 없음 → baking 스킵), 본문 정의는 lang-lock으로 언어별.
    slug: 'glossary',
    faqUniversal: [],
    faqLangOnly: {},
    hasFaqJsonLd: false,
  },
};

// ── FAQ JSON-LD 생성 (언어별, 화면 표시 항목과 일치) ──
function buildFaqJsonLd(page, lang) {
  const items = [];
  for (const [qk, ak] of page.faqUniversal) {
    items.push({ q: tr(lang, qk), a: tr(lang, ak) });
    // lang-only 항목은 q2 직후 삽입
    if (page.faqLangOnly[lang] && page.faqLangOnly[lang].after === qk) {
      items.push({ q: page.faqLangOnly[lang].q, a: page.faqLangOnly[lang].a, raw: true });
    }
  }
  const mainEntity = items.map(it => ({
    qn: stripTags(it.q), an: stripTags(it.a),
  }));
  const obj = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    inLanguage: lang,
    mainEntity: mainEntity.map(m => ({
      '@type': 'Question',
      name: m.qn,
      acceptedAnswer: { '@type': 'Answer', text: m.an },
    })),
  };
  return '<script type="application/ld+json">\n' + JSON.stringify(obj, null, 2) + '\n</script>';
}

// ── hreflang 클러스터 ──
function hreflangBlock(slug) {
  return [
    `<link rel="alternate" hreflang="ko" href="${BASE}/${slug}">`,
    `<link rel="alternate" hreflang="en" href="${BASE}/en/${slug}">`,
    `<link rel="alternate" hreflang="ja" href="${BASE}/ja/${slug}">`,
    `<link rel="alternate" hreflang="x-default" href="${BASE}/${slug}">`,
  ].join('\n');
}

// ── navigate-toggle IIFE (♢ <script> 래퍼 없음 — 기존 토글 IIFE만 교체, glossary의 검색 IIFE 보존) ──
function toggleIIFE(slug, lang) {
  return `(function(){
    var LANG=${JSON.stringify(lang)};
    var URLS={ko:'/${slug}',en:'/en/${slug}',ja:'/ja/${slug}'};
    document.querySelectorAll('.docs-lang-btn').forEach(function(b){
      b.classList.toggle('active', b.dataset.lang===LANG);
      b.addEventListener('click',function(){
        var nl=b.dataset.lang;
        try{ localStorage.setItem('p2a.lang', nl); }catch(e){}
        if(URLS[nl] && nl!==LANG) location.href=URLS[nl];
      });
    });
  })();`;
}

// ── canonical 다음에 hreflang 삽입 (이미 있으면 교체) ──
function ensureHreflang(html, slug) {
  const block = hreflangBlock(slug);
  // 기존 hreflang 라인 제거
  html = html.replace(/^\s*<link rel="alternate" hreflang="[^"]*" href="[^"]*">\s*\n/gm, '');
  // canonical 라인 뒤에 삽입
  return html.replace(/(<link rel="canonical"[^>]*>)/, `$1\n${block}`);
}

// ── 기존 lang-toggle IIFE 교체 (docs-lang-btn 포함 IIFE만; })(); 경계 안 넘어 검색 IIFE 보존) ──
// 구버전(let lang='ko' 인-플레이스)·신버전(navigate) 모두 매칭 → 재실행 idempotent.
function replaceToggle(html, slug, lang) {
  const re = /\(function\(\)\{(?:(?!\}\)\(\);)[\s\S])*?docs-lang-btn(?:(?!\}\)\(\);)[\s\S])*?\}\)\(\);/;
  if (!re.test(html)) throw new Error(`toggle IIFE not found in ${slug}`);
  return html.replace(re, toggleIIFE(slug, lang));
}

function buildLangPage(page, lang) {
  const slug = page.slug;
  let html = fs.readFileSync(path.join(ROOT, `${slug}.html`), 'utf8');

  const has = (key) => !!(T[lang] && T[lang][key]);

  // 1) html lang + data-lang-lock (URL이 언어의 단일 진실 — translations.js가 이 속성으로 언어 고정)
  html = html.replace(/<html lang="ko"[^>]*>/, `<html lang="${LANG_HTML[lang]}" data-lang-lock="${LANG_HTML[lang]}">`);

  // 2) <title data-i18n="..."> 텍스트 baked (data-i18n 선언 + 번역 존재 시에만)
  html = html.replace(/(<title data-i18n="([^"]+)">)[^<]*(<\/title>)/, (m, open, key, close) =>
    has(key) ? open + esc(tr(lang, key)) + close : m);

  // 3) meta description content baked (data-i18n-content 선언 + 번역 존재 시에만)
  html = html.replace(/(<meta name="description" data-i18n-content="([^"]+)" content=")[^"]*(">)/, (m, open, key, close) =>
    has(key) ? open + esc(tr(lang, key)) + close : m);

  // 4) canonical → 언어 URL
  html = html.replace(/(<link rel="canonical" href="[^"]*)\/(?:overview|about|glossary)(">)/,
    `<link rel="canonical" href="${BASE}/${lang}/${slug}">`);

  // 5) hreflang
  html = ensureHreflang(html, slug);

  // 6) FAQ JSON-LD 교체 (언어별)
  if (page.hasFaqJsonLd) {
    const faqRe = /<script type="application\/ld\+json">(?:(?!<\/script>)[\s\S])*?"@type":\s*"FAQPage"(?:(?!<\/script>)[\s\S])*?<\/script>/;
    if (!faqRe.test(html)) throw new Error(`FAQPage JSON-LD not found in ${slug}`);
    html = html.replace(faqRe, buildFaqJsonLd(page, lang));
  }

  // 6b) DefinedTermSet 용어 정의(description) 언어별 현지화 (glossary).
  //     각 DefinedTerm의 @id 앵커(#pillartwo 등) → glossary.t.<앵커>.def 키로 매핑해 description 교체.
  html = html.replace(
    /("@id": "https:\/\/pillartwo\.app\/glossary#([a-z0-9]+)",\s*\n\s*"name": "(?:[^"\\]|\\.)*",\s*\n\s*"description": )"(?:[^"\\]|\\.)*"/g,
    (m, prefix, anchor) => {
      const key = 'glossary.t.' + anchor + '.def';
      return has(key) ? prefix + JSON.stringify(stripTags(tr(lang, key))) : m;
    }
  );

  // 7) BreadcrumbList item URL → 언어 URL
  html = html.replace(new RegExp(`("item": ")${BASE}/${slug}(")`), `$1${BASE}/${lang}/${slug}$2`);

  // 8) og / twitter (locale·url은 항상; title·desc는 번역 키 존재 시에만 — glossary 등 정적 meta 보존)
  html = html.replace(/<meta property="og:locale" content="ko_KR">/, `<meta property="og:locale" content="${LANG_LOCALE[lang]}">`);
  html = html.replace(/<meta property="og:locale:alternate" content="en_US">\n<meta property="og:locale:alternate" content="ja_JP">/,
    ['ko', 'en', 'ja'].filter(l => l !== lang).map(l => `<meta property="og:locale:alternate" content="${LANG_LOCALE[l]}">`).join('\n'));
  html = html.replace(/(<meta property="og:url" content="[^"]*)\/(?:overview|about|glossary)(">)/, `<meta property="og:url" content="${BASE}/${lang}/${slug}">`);
  if (has(`${slug}.meta.title`)) {
    const title = tr(lang, `${slug}.meta.title`);
    html = html.replace(/(<meta property="og:title" content=")[^"]*(">)/, `$1${esc(title)}$2`);
    html = html.replace(/(<meta name="twitter:title" content=")[^"]*(">)/, `$1${esc(title)}$2`);
  }
  if (has(`${slug}.meta.desc`)) {
    const desc = tr(lang, `${slug}.meta.desc`);
    html = html.replace(/(<meta property="og:description" content=")[^"]*(">)/, `$1${esc(desc)}$2`);
    html = html.replace(/(<meta name="twitter:description" content=")[^"]*(">)/, `$1${esc(desc)}$2`);
  }

  // 9) toggle navigate
  html = replaceToggle(html, slug, lang);

  // 10) 경로 보정 — /en/·/ja/ 깊이에서 상대경로가 깨지는 것 방지 (CSS/JS 404 → 스타일 전무 버그 수정).
  //     자산(styles.css·docs.css·translations.min.js)은 루트 절대경로로, doc 내부링크는 같은 언어 URL로.
  const REL_FIX = { 'styles.css': '/styles.css', 'docs.css': '/docs.css', 'translations.min.js': '/translations.min.js', './': '/' };
  html = html.replace(/(href|src)="([^"]+)"/g, (m, attr, val) => {
    if (REL_FIX[val]) return `${attr}="${REL_FIX[val]}"`;
    const dm = val.match(/^(overview|about|glossary)\.html$/);
    if (dm) return `${attr}="/${lang}/${dm[1]}"`;
    return m;
  });

  const outDir = path.join(ROOT, lang);
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, `${slug}.html`), html);
  console.log(`wrote ${lang}/${slug}.html (${html.length} chars)`);
}

// ── ko 원본 패치: hreflang + navigate-toggle (JSON-LD는 유지) ──
function patchKo(page) {
  const slug = page.slug;
  const p = path.join(ROOT, `${slug}.html`);
  let html = fs.readFileSync(p, 'utf8');
  html = html.replace(/<html lang="ko"[^>]*>/, '<html lang="ko" data-lang-lock="ko">');
  html = ensureHreflang(html, slug);
  html = replaceToggle(html, slug, 'ko');
  fs.writeFileSync(p, html);
  console.log(`patched ${slug}.html (ko: lang-lock + hreflang + navigate-toggle)`);
}

const args = process.argv.slice(2);
const targets = args.length ? args : ['overview'];
for (const name of targets) {
  const page = PAGES[name];
  if (!page) { console.error(`unknown page: ${name}`); continue; }
  buildLangPage(page, 'en');
  buildLangPage(page, 'ja');
  patchKo(page);
}
console.log('done.');
