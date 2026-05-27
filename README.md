# PillarTwo Architect

A browser-based workspace for designing multinational group structures and analysing Pillar Two (Global Minimum Tax) outcomes — IIR, UTPR, and QDMTT obligations — in real time.

🌐 **Live:** [pillartwo.app](https://pillartwo.app)
🗣️ **Languages:** 한국어 · English · 日本語

---

## What it does

Pillar Two analysis traditionally takes hours of careful ownership-mapping, jurisdictional checks, and rule application — usually done in spreadsheets, document-by-document. PillarTwo Architect collapses that work into a single interactive canvas:

- **Draw the group.** Double-click to add entities, drag to connect ownership. Tidy-tree auto-layout keeps the picture clean.
- **Run the engine.** Identify Constituent Entities, Joint Ventures, MOPEs, POPEs, IPEs and map IIR · UTPR · QDMTT obligations across jurisdictions.
- **Iterate.** Edit any entity, ownership ratio, or charging provision — rerun the analysis and watch the impact ripple through instantly.
- **Drill down.** Click any entity to highlight its tax flow, payment obligations, and ownership chain — relationships animate in for one-glance clarity.

What would otherwise be a multi-day desk-research exercise becomes a few minutes of structured input and visual review.

---

## Core features

| | |
|---|---|
| **Visual structure design** | Double-click to add, drag to connect, auto-layout to tidy. |
| **Analysis engine** | Direct/indirect ownership closure, circular-ownership handling, multi-stage CE/JV/MOPE/POPE/IPE/UTPR determination. |
| **Real-time iteration** | Modify and rerun — results update instantly. |
| **Per-entity insights** | Click an entity to see top-up tax flow, payment obligations, and ownership chain tailored to that entity. |
| **Trilingual** | Korean · English · Japanese, with OECD model rules and jurisdictional terminology preserved. |
| **Encrypted save** | AES-GCM 256-bit password-protected `.p2a` files. |
| **Continuous management** | Save and reload as `.p2a` to track architectures by fiscal year and structural-change milestone. |
| **Local-only** | `.p2a` files stay on your machine. Entity data, ownership, and accounting figures never leave the browser. |

---

## Who it's for

- **In-house tax teams** modelling Pillar Two impact across MNE structures
- **Tax advisors** running scenario comparisons for client groups
- **Researchers and academics** studying Pillar Two implementation
- **Practitioners and students** learning the GloBE rules through hands-on structure design

---

## Background

Built by a practitioner specialising in Pillar Two implementation, the engine codifies the GloBE Model Rules, the OECD Commentary, and Administrative Guidance — together with each adopting jurisdiction's domestic implementation — into a deterministic analysis pipeline. The aim is to keep the rigorous logic of professional review while removing the spreadsheet overhead.

Results are reference outputs based on user inputs and the encoded ruleset. Always have a seasoned Pillar Two specialist review the output before applying it in practice.

---

## Quick start

1. Visit [pillartwo.app](https://pillartwo.app)
2. Try the built-in tutorial, or click **Load Sample Architecture** for a worked example
3. Add entities, connect ownership, set charging provisions per jurisdiction
4. Click **Analyze** to compute CE/JV/MOPE/POPE/IPE/UTPR roles and the resulting top-up tax obligations
5. Save your work as a `.p2a` file (optionally password-encrypted) for later reload

---

## Privacy

The service does not collect or transmit analysis data. Entity information, ownership ratios, accounting data, and analysis results are processed entirely client-side. Only the contact form (Formspree) and standard third-party assets (OpenStreetMap tiles, jsDelivr CDN) generate any outbound network traffic; opt-in usage analytics (Google Analytics, Microsoft Clarity) are gated by Consent Mode v2 and remain off until the user agrees.

See the in-app **Privacy Policy** for the full data-handling notice.

---

## Tech

- Static single-page app on Cloudflare Pages
- Vanilla JavaScript / DOM — no framework, no build pipeline
- Leaflet + world-atlas TopoJSON for the in-canvas world map
- Client-side AES-GCM encryption (Web Crypto API) for `.p2a` files

---

## Feedback

In-app contact form: click **Contact** in the lower-right of the map widget.

---

© 2026 PillarTwo Architect
