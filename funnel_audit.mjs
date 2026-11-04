#!/usr/bin/env node
// Measures two things the recurring "durable distribution" mission keeps asking by hand:
//   1. SEARCH METADATA - can each indexable page be indexed and shared (desc/canonical/og:image/JSON-LD/sitemap)?
//   2. FUNNEL ROUTES   - does each blog post that is ABOUT a product actually link to THAT product?
//   3. TOOL ENTRY       - which $1 tools under tools/ have NO blog post linking them, i.e. no way in from search?
// Written 2026-11-01 after a night block re-derived both with one-off `node -e` and misread its own
// output twice. Two traps it encodes, so nobody pays for them again:
//   - A product can live on its own domain (trade-guard.pro, gate402.app) or be a plain page
//     (indemnity.html). Checking only "<slug>.html" reports false leaks.
//   - Redirect stubs (agent-browser.html) are deliberately noindex + out of the sitemap. Correct, not broken.
//   - EVERY page under tools/ is noindex by design (0db59c8, 2026-09-02: they are conversion pages, and
//     indexing them fits Google's doorway pattern). Do not "fix" that. The consequence is measurement 3:
//     a tool's ONLY route from a search engine is a blog post that links it, so a tool no post links is
//     unreachable. That is a backlog item, not a defect, so it does NOT set the exit code - leaks do.
// Usage: node funnel_audit.mjs            (run from the site root; exits 1 if a real leak is found)
import fs from 'node:fs';

// A post is "about" a product when its filename matches; the product is linked when any target appears.
const PRODUCTS = {
  TradeGuard:    { about: /coi|certificate-holder|additional-insured|subcontractor/i, links: ['trade-guard.pro'] },
  gate402:       { about: /http-402|monetize-api-x402|x402|mcp-web-access/i,          links: ['gate402.app'] },
  Indemnity:     { about: /escrow-by-default|erc20/i,                                 links: ['indemnity.html'] },
  thinbrowser:   { about: /playwright|networkidle|logged-in-chrome|agent-reads-the-whole-page|overlay|secrets-out-of-agent-context/i,
                   links: ['thinbrowser.html', 'agent-browser.html', 'npmjs.com/package/thinbrowser'] },
  ResumeMatcher: { about: /ats-|resume/i,            links: ['resume-matcher.html', 'job-hunt-tracker.html'] },
  wcInvoices:    { about: /invoice|packing-slip/i,   links: ['wc-invoices.html', 'wc-invoices-pro.html'] },
  wcEvents:      { about: /eventbrite|event-ticket/i,links: ['wc-events.html', 'wc-events-pro.html'] },
  wcRestaurant:  { about: /restaurant|online-ordering|commission-free/i, links: ['wc-restaurant.html', 'wc-restaurant-pro.html'] },
  Membership:    { about: /paywall|membership|patreon/i, links: ['membership-content-restriction.html'] },
  Boilerplate:   { about: /freemium-wordpress-plugin|plugin-boilerplate/i, links: ['wp-plugin-boilerplate.html'] },
  OAK:           { about: /knight|chess/i,           links: ['oops-all-knights'] },
};

const body = (html) => html
  .replace(/<head[\s\S]*?<\/head>/gi, '')
  .replace(/<nav[\s\S]*?<\/nav>/gi, '')
  .replace(/<footer[\s\S]*?<\/footer>/gi, '');

const sitemap = fs.existsSync('sitemap.xml') ? fs.readFileSync('sitemap.xml', 'utf8') : '';
const files = fs.readdirSync('.').filter((f) => f.endsWith('.html'));

const metaGaps = [];
const leaks = [];
let indexable = 0;
let posts = 0;
let routed = 0;

for (const f of files) {
  const html = fs.readFileSync(f, 'utf8');
  const isStub = /name="robots"\s+content="noindex/i.test(html) || /http-equiv="refresh"/i.test(html);
  if (!isStub && f !== '404.html') {
    indexable++;
    const missing = [];
    if (!/<meta\s+name="description"/i.test(html)) missing.push('desc');
    if (!/rel="canonical"/i.test(html)) missing.push('canonical');
    if (!/property="og:image"/i.test(html)) missing.push('og:image');
    if (!/"@type"/.test(html)) missing.push('json-ld');
    const slug = f.replace(/\.html$/, '');
    const inMap = sitemap.includes(`${slug}.html`) || sitemap.includes(`/${slug}`) ||
      (slug === 'index' && sitemap.includes('rebelstudiossoftware.com/'));
    if (!inMap) missing.push('sitemap');
    if (missing.length) metaGaps.push([f, missing.join(',')]);
  }
  if (!f.startsWith('blog-') || isStub) continue;
  const owners = Object.entries(PRODUCTS).filter(([, p]) => p.about.test(f));
  if (!owners.length) continue; // an essay with no product behind it is not a leak
  posts++;
  const text = body(html);
  const unlinked = owners.filter(([, p]) => !p.links.some((t) => text.includes(t)));
  // Routed if it links AT LEAST ONE product it is about: a post can match two topics and
  // legitimately sell only one (the escrow post sells Indemnity, not gate402).
  if (unlinked.length === owners.length) leaks.push([f, owners.map(([n]) => n).join('|')]);
  else routed++;
}

// 3. TOOL ENTRY POINTS. tools/ is noindex by design, so each tool needs a post pointing at it.
const toolDir = 'tools';
const toolRows = [];
if (fs.existsSync(toolDir)) {
  const postText = files.filter((f) => f.startsWith('blog-'))
    .map((f) => body(fs.readFileSync(f, 'utf8')));
  for (const t of fs.readdirSync(toolDir).filter((f) => f.endsWith('.html') && f !== 'index.html')) {
    const slug = `tools/${t}`;
    const n = postText.filter((x) => x.includes(slug)).length;
    toolRows.push([t.replace(/\.html$/, ''), n]);
  }
}
const orphanTools = toolRows.filter(([, n]) => n === 0);

// 4. SCHEMA TRUTH. A post is usually built by copying the last one and replacing its title
// everywhere, which is how author.name and publisher.name end up holding the headline. Google
// reads those two fields; a publisher named after the article is worse than no publisher at all.
const AUTHOR = 'Rebel Studios Software';
const PUBLISHER = 'Rebel Studios Software';
const schemaBad = [];
for (const f of files) {
  const html = fs.readFileSync(f, 'utf8');
  for (const m of html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)) {
    let parsed;
    try { parsed = JSON.parse(m[1]); } catch { schemaBad.push([f, 'does not parse as JSON']); continue; }
    for (const o of (Array.isArray(parsed) ? parsed : [parsed])) {
      const title = o.headline || o.name;
      const author = o.author && o.author.name;
      const pub = o.publisher && o.publisher.name;
      const probs = [];
      if (title && author === title) probs.push('author.name is the headline');
      if (title && pub === title) probs.push('publisher.name is the headline');
      // Only an article has to be written by a person. A product page crediting the studio as
      // author is correct, so the exact-name rule applies to posts only.
      if (/^(BlogPosting|Article)$/.test(o['@type'])) {
        if (!author) probs.push('no author');
        else if (author !== AUTHOR) probs.push(`author.name is "${author}"`);
        if (!pub) probs.push('no publisher');
        else if (pub !== PUBLISHER) probs.push(`publisher.name is "${pub}"`);
      }
      if (probs.length) schemaBad.push([f, probs.join('; ')]);
    }
  }
}

console.log(`SEARCH METADATA  ${indexable} indexable pages, ${metaGaps.length} with gaps`);
for (const [f, m] of metaGaps) console.log(`   ${f.padEnd(40)} ${m}`);
console.log(`\nFUNNEL ROUTES    ${posts} product-topic posts, ${routed} route to a product, ${leaks.length} dead-end`);
for (const [f, p] of leaks) console.log(`   LEAK ${f.padEnd(40)} about ${p}, links neither`);
if (!leaks.length) console.log('   no dead-end posts: every product-topic post links a product it is about');

console.log(`\nTOOL ENTRY       ${toolRows.length} tools under tools/ (all noindex by design), ${orphanTools.length} with no post linking them`);
for (const [t] of orphanTools) console.log(`   NO WAY IN  tools/${t}.html`);
if (!orphanTools.length) console.log('   every tool has at least one post linking it');

console.log(`\nSCHEMA TRUTH     ${schemaBad.length} JSON-LD blocks naming the wrong author or publisher`);
for (const [f, why] of schemaBad) console.log(`   WRONG ${f.padEnd(40)} ${why}`);
if (!schemaBad.length) console.log(`   every JSON-LD block parses and credits ${AUTHOR} / ${PUBLISHER}`);
process.exit(leaks.length || schemaBad.length ? 1 : 0);
