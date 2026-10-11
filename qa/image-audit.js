// Image audit: lists every <img> whose rendered box ratio differs from its natural ratio
// by more than 2% while object-fit is "fill" (the pixels really are stretched), and every
// image shown wider than its pixels allow on a 2x screen ("soft").
// Serve the site first (python3 -m http.server 5611 --bind 127.0.0.1), then:
//   PLAYWRIGHT_CORE=~/agent-browser/node_modules/playwright-core node qa/image-audit.js [page.html ...]
const { chromium } = require(process.env.PLAYWRIGHT_CORE || 'playwright-core');
const fs = require('fs');
const path = require('path');
const ROOT = process.env.ROOT || path.resolve(__dirname, '..');
const BASE = process.env.BASE || 'http://127.0.0.1:5611/';

let pages = process.argv.slice(2);
if (!pages.length) {
  pages = fs.readdirSync(ROOT).filter((f) => f.endsWith('.html'))
    .concat(fs.readdirSync(path.join(ROOT, 'tools')).filter((f) => f.endsWith('.html')).map((f) => 'tools/' + f));
}

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || '/usr/bin/chromium', args: ['--no-sandbox'] });
  const findings = [];
  for (const width of [1440, 390]) {
    const ctx = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
    // never let analytics/ads load during audits
    await ctx.route(/googletagmanager|googlesyndication|google-analytics|doubleclick/, (r) => r.abort());
    const page = await ctx.newPage();
    for (const p of pages) {
      try {
        await page.goto(BASE + p, { waitUntil: 'load', timeout: 30000 });
      } catch (e) { findings.push({ page: p, width, err: String(e).slice(0, 120) }); continue; }
      const rows = await page.evaluate(async () => {
        document.querySelectorAll('.screenshot-slide').forEach((el) => { el.style.display = 'block'; el.style.opacity = '1'; });
        const imgs = [...document.querySelectorAll('img')].filter((i) => i.getAttribute('src'));
        imgs.forEach((i) => { i.loading = 'eager'; });
        await Promise.all(imgs.map((i) => i.complete ? null : new Promise((r) => { i.onload = i.onerror = r; setTimeout(r, 4000); })));
        const out = [];
        for (const i of imgs) {
          const r = i.getBoundingClientRect();
          const cs = getComputedStyle(i);
          const src = i.currentSrc || i.src;
          if (!i.naturalWidth) { out.push({ src, issue: 'not loaded' }); continue; }
          if (r.width < 2 || r.height < 2) continue; // hidden (carousel slide etc.)
          const nat = i.naturalWidth / i.naturalHeight;
          // content box
          const pw = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight) + parseFloat(cs.borderLeftWidth) + parseFloat(cs.borderRightWidth);
          const ph = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom) + parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth);
          const ren = (r.width - pw) / (r.height - ph);
          const diff = Math.abs(ren / nat - 1);
          if (diff > 0.02 && (cs.objectFit === 'fill' || cs.objectFit === '')) {
            out.push({ src, natural: `${i.naturalWidth}x${i.naturalHeight}`, rendered: `${Math.round(r.width)}x${Math.round(r.height)}`, diff: +(diff * 100).toFixed(1), cls: i.className });
          }
          // soft: shown bigger than its pixels allow on a 2x screen (only for images over 120px wide)
          const shownW = cs.objectFit === 'contain' ? Math.min(r.width, r.height * nat) : r.width; // what the eye sees
          if (shownW > 120 && i.naturalWidth < shownW * 1.5) out.push({ src, soft: true, natural: `${i.naturalWidth}x${i.naturalHeight}`, shown: Math.round(shownW) });
        }
        return out;
      });
      for (const row of rows) findings.push({ page: p, width, ...row });
    }
    await ctx.close();
  }
  await browser.close();
  for (const f of findings) console.log(JSON.stringify(f));
  console.log(`TOTAL ${findings.length} findings across ${pages.length} pages x 2 widths`);
})();
