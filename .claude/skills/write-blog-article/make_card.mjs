#!/usr/bin/env node
/*
 * Generate one branded 1200x630 OG/social card for a blog article.
 * Usage:  node make_card.mjs "<slug>" "<Title>" "<KICKER>"
 * Writes: <repo>/images/blog/<slug>.png   (repo = 3 levels up from this file)
 *
 * The card is what shows as the link preview on X, LinkedIn, Bluesky, Slack, etc.,
 * and doubles as the blog-index thumbnail. Dark brand background, green R badge.
 */
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '../../..'); // <repo>/.claude/skills/write-blog-article -> <repo>
const OUT = path.join(REPO, 'images', 'blog');
const CHROME = process.env.CHROME || 'chromium';

const [slug, title, kicker = ''] = process.argv.slice(2);
if (!slug || !title) {
  console.error('usage: node make_card.mjs "<slug>" "<Title>" "<KICKER>"');
  process.exit(1);
}

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const fontFor = (t) => (t.length > 60 ? 50 : t.length > 46 ? 56 : 64);

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:1200px;height:630px}
  body{font-family:'DejaVu Sans','Liberation Sans',sans-serif;color:#eef1f7;
    background:radial-gradient(1200px 700px at 80% -12%, #113524 0%, #0a0e17 52%, #070a12 100%);
    padding:74px 80px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden}
  .glow{position:absolute;right:-150px;top:-150px;width:460px;height:460px;border-radius:50%;
    background:radial-gradient(circle,rgba(74,222,128,.20),transparent 68%)}
  .top{display:flex;align-items:center;gap:18px;z-index:1}
  .badge{width:56px;height:56px;border-radius:14px;background:#4ade80;color:#08120a;font-weight:800;font-size:36px;
    display:flex;align-items:center;justify-content:center}
  .brand{font-size:22px;font-weight:700;letter-spacing:3px;color:#cdd5e3;text-transform:uppercase}
  .mid{z-index:1}
  .kicker{color:#4ade80;font-weight:700;font-size:23px;letter-spacing:2px;text-transform:uppercase;margin-bottom:20px}
  h1{font-size:${fontFor(title)}px;line-height:1.12;font-weight:800;max-width:1040px;letter-spacing:-1px}
  .foot{display:flex;align-items:center;gap:20px;font-size:24px;color:#98a2b3;z-index:1}
  .bar{height:8px;width:130px;background:linear-gradient(90deg,#4ade80,#2dd4bf);border-radius:99px}
</style></head><body>
  <div class="glow"></div>
  <div class="top"><div class="badge">R</div><div class="brand">Rebel Studios Software</div></div>
  <div class="mid">${kicker ? `<div class="kicker">${esc(kicker)}</div>` : ''}<h1>${esc(title)}</h1></div>
  <div class="foot"><div class="bar"></div>rebelstudiossoftware.com</div>
</body></html>`;

fs.mkdirSync(OUT, { recursive: true });
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ogcard-'));
const htmlPath = path.join(tmp, slug + '.html');
fs.writeFileSync(htmlPath, html);
const outPath = path.join(OUT, slug + '.png');
execFileSync(CHROME, ['--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
  '--force-device-scale-factor=1', '--window-size=1200,630',
  '--screenshot=' + outPath, 'file://' + htmlPath], { stdio: ['ignore', 'ignore', 'ignore'] });
console.log('wrote', outPath);
