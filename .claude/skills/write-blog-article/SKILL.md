---
name: write-blog-article
description: Write a Rebel Studios blog article that targets real reader demand. Starts from NicheScout / content-queue demand data to pick a topic, writes it in the Rebel voice (how-to funnel OR opinion piece), gives it an image of its own (photo, screenshot or diagram via blog_art.py), wires it into the blog index and feeds, and STOPS for human review. Use when the user wants a new blog post, to turn a queued topic into a draft, or to grow blog readership.
---

# Write a Rebel Studios blog article

Goal: publishable drafts that **build up readers** — via search (target real demand, rank) and social (opinion pieces that get reshared). Never auto-publish; a human reviews before it goes live (Google's scaled-content-abuse policy penalizes bulk unreviewed AI content, which would sink SEO and AdSense).

Paths (this repo = the site root, `~/RebelStudiosSoftware`):
- Demand data: `~/rebel-monitor/content-queue.md` (daily NicheScout topics), `~/rebel-monitor/tool-ideas.md`, seed list `~/rebel-monitor/tech-niches.txt`
- NicheScout CLI: `~/NicheScout/scout scan --seed-file <file> --geo US --timeframe "today 12-m" --json <out>` (often throttled by Google Trends — don't block on it)
- Helper scripts: `gen_article.py` (this skill dir), `blog_art.py` (site root: each post's image)
- Publish plumbing: `blog.html` (index cards), `generate_feeds.py` (sitemap + feed, auto-discovers `blog-*.html`)

## Step 1 — Pick a target topic (from demand, not vibes)

1. Read `~/rebel-monitor/content-queue.md` for today's queued topics (the daily engine ranks them by NicheScout demand score when Trends isn't throttled). Prefer topics with a real `demand score` / rising shape.
2. If the queue is stale or empty, pick from `~/rebel-monitor/tech-niches.txt`, or run a fresh `scout scan` on a few candidates.
3. **Dedupe**: skip anything already covered — check `ls blog-*.html`. Match on the core keyword tokens, not the exact slug.
4. Confirm the topic fits Rebel (software, AI, agents, dev tooling, automation, the trades/COI vertical, indie building). If it doesn't, pick another.

## Step 2 — Decide the genre (this determines everything downstream)

- **How-to / funnel article** — for topics with *search intent* ("convert heic to jpg", "merge pdf files", "format json"). Job: rank for the query and convert to a $1 tool. Lead with the free/manual method, be fast and practical, then funnel to the matching tool at `tools/<tool>.html` (or flag it to build). Give it an in-article hero image.
- **Opinion / thought-leadership piece** — for unresolvable, debatable questions ("should agents have wallets", "ship code you don't understand", "dark mode"). Job: get shared, build credibility. Take a clear side, argue it, tie it to Rebel, end with a question that invites disagreement. Usually text-first (no hero — the OG card carries the title).

Match genre to intent. A meditation on "how to convert HEIC" would kill a how-to; a bullet-list listicle would kill an opinion piece.

## Step 3 — Write in the Rebel voice

Read two existing articles first to calibrate: an opinion piece (`blog-can-everybody-be-rich.html`, `blog-ai-agents-money.html`) and a how-to (`blog-json-repair.html`).

**Register — philosophy × news × technology.** This is the heart of the Rebel essay voice. Every thought-leadership piece braids three strands:
- **News** — open on something happening *now*: a shift, a release, a live tension in the industry. Timeliness and stakes, the way a good reporter leads with the development and why it matters this week.
- **Philosophy** — don't stop at the surface. Find the first-principles or human question underneath: what are we actually deciding, what does this *mean*, who does it change. Use thought experiments; follow the idea somewhere uncomfortable.
- **Technology** — stay technically honest and specific. Real mechanisms, real systems, a builder's understanding — never hand-wavy futurism.

The synthesis: *a current technology development, examined for the deeper idea underneath, written with a reporter's clarity.* Reach for Stratechery or a sharp Atlantic tech essay, not a vendor blog. Avoid the two failure modes — dry news with no ideas, and floaty philosophy with no technical ground or news hook. (How-to funnel articles stay practical, but even they can open with a one-line "why this matters now" framing.)

Voice rules:
- **Earn the read in the first two sentences.** A concrete hook, a surprising claim, or a sharp question — never "In today's fast-paced world…".
- Direct, confident, second person. Short punchy sentences mixed with longer ones. Concrete over abstract. Em dashes sparingly (a couple per article at most): a sentence per dash reads as machine-written; use a full stop, a comma or a colon instead.
- **Bring Rebel in early**, not just the CTA — one natural aside mid-article, then the close.
- Apply the **second-order-effects lens**: what does this change downstream, who does it affect. That's the Rebel differentiator.
- No corporate filler, no "5 ways AI will revolutionize", no fake statistics, no invented case studies. If a real first-hand example would help, add an HTML comment placeholder `<!-- PATRICK: real example here -->` rather than fabricating one.
- Structure: hook → `<h2>` sections → one `<div class="article-highlight">` or `<div class="article-callout">` box for the key point → strong close → the italic CTA linking `index.html#contact`.
- Internal-link to 1–2 related articles and any relevant tool (`tools/<slug>.html`) — good for SEO and reader depth.
- Length: substantial, never padded. How-tos ~1000–1500 words; opinion/essays ~1100–1600. Reach the length by adding real depth — concrete examples, a second-order angle, an honest counterpoint, a "here's what it looks like in practice" section — not filler. A short piece reads as thin to both readers and Google; a padded one reads as worse. Earn every paragraph.

Write the article body as the inner HTML of `<div class="article-content">` (use `&mdash; &rsquo; &ldquo; &rdquo;` entities, `<h2>`, `<p>`, `<ul class="article-list">`, highlight/callout boxes — mirror the existing articles exactly).

## Step 4 — Give it its own image

Every post gets an image made for it; there is no shared title-card template (46 posts looked identical that way, 2026-09-18). Pick the kind that shows the post's substance, add an entry to `blog_art.json` at the site root, and render:

- **photo**: essays and opinion pieces. `python3 blog_art.py photos "<query>"` shows Pexels candidates (free licence); choose one that carries the argument, not the title (the xz-utils essay got rusted valves and gauges, not a padlock). It opens the essay with a credit line.
- **crop**: a real screenshot of the product or tool the post leads to (`images/products/...`), cropped to the part that matters.
- **diagram**: `art/<slug>.html` drawn for this post with `art/art.css`: the article's own example, table or numbers (measured where possible: the regex post charts real timings). Vary the layout; a photo can be built in with `python3 blog_art.py fetch <pexels-id> <name>`, credited inside the image.

```
python3 blog_art.py render <slug>     # images/blog/<slug>.jpg|png
python3 blog_art.py apply <slug>      # og/twitter/JSON-LD image + the blog.html card
python3 blog_art.py sheet             # the whole index at once: no two cards should look alike
```

## Step 5 — Generate the article HTML

Write a JSON spec then render:
```
python3 .claude/skills/write-blog-article/gen_article.py spec.json
```
Spec fields: `slug, title, subtitle, description, body_html, next_href, next_label` (required); `date_iso, hero, hero_alt, og_card` (optional). For how-tos set `hero` to an in-article image; omit it for opinion pieces. The generator wires in GA4/consent, canonical, per-article OG/Twitter card, and JSON-LD automatically. Writes `blog-<slug>.html`.

- `title`/`description` must contain the target search phrase for how-tos (SEO).
- `description` is plain text (no HTML entities — it goes in meta attributes).

## Step 6 — Wire it into the site

1. Add a card at the **top** of the `<div class="blog-grid">` in `blog.html` (newest first), mirroring an existing `<a class="blog-card">` block — image as set by `blog_art.py apply` (or add the card first, then apply), today's date, title, one-sentence description, "Read Article →".
2. Regenerate feeds: `python3 generate_feeds.py` (adds it to `sitemap.xml` + `feed.xml`).

## Step 7 — STOP. Human review, then publish

Do **not** commit/push automatically. Present a summary: the topic + why it targets demand, the stance/angle, the opening lines, and any `PATRICK:` placeholders that need a real example. Only after the user approves:
- `git add` the new `blog-<slug>.html`, its image in `images/blog/`, `blog_art.json` (and `art/<slug>.html` if drawn), `blog.html`, `sitemap.xml`, `feed.xml` and commit + push.
- It then flows into the daily social poster (`~/rebel-monitor/social_share.mjs`) automatically — opinion pieces drive the most reshares, how-tos drive search traffic.

## Distribution reminder (how readers actually show up)
- **Search**: how-tos targeting real NicheScout demand, with the query in title/H1/description, internal links, and an image of its own.
- **Social**: opinion pieces are the fuel for Bluesky/LinkedIn/X — a clear side + a closing question gets replies and shares. The poster picks up any `blog-*.html` that links a tool or reads as a funnel piece.
- **Cadence over bursts**: one well-targeted, human-reviewed piece beats ten generic ones — and keeps you clear of scaled-content-abuse penalties.
