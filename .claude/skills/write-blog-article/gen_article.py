#!/usr/bin/env python3
"""
Render one blog article HTML file from a JSON spec, matching the Rebel Studios template
(GA4 + consent, canonical, per-article OG/Twitter card, JSON-LD, nav, footer).

Usage:
    python3 gen_article.py spec.json

spec.json fields:
    slug         (required)  e.g. "ai-agents-money"  -> blog-ai-agents-money.html
    title        (required)  used in <title>, og:title, h1, JSON-LD headline
    subtitle     (required)  page-header sub-line
    description  (required)  meta description / og:description / JSON-LD (plain text)
    body_html    (required)  the inner HTML of <div class="article-content"> (already escaped)
    next_href    (required)  e.g. "blog-other.html"
    next_label   (required)  link text for the "next" button
    date_iso     (optional)  default today (YYYY-MM-DD)
    date_human   (optional)  default derived from date_iso ("August 12, 2026")
    hero         (optional)  image src for an in-article hero, e.g. "images/blog/foo.jpg".
                             Omit for a text-first (opinion) piece.
    hero_alt     (optional)  alt text for the hero
    og_card      (optional)  default "images/blog/<slug>.png" (generate it with make_card.mjs)

Does NOT publish. After generating, add a card to blog.html, run generate_feeds.py, and
leave it for human review before committing (see SKILL.md).
"""
import os, sys, json, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]  # <repo>/.claude/skills/write-blog-article -> <repo>

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) + Consent Mode + cookie banner -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-00TNDVMQNM"></script>
    <script>
      window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
      gtag('js',new Date());
      var RSc;try{RSc=localStorage.getItem('rs_consent')}catch(e){RSc=null}
      gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:RSc==='granted'?'granted':'denied'});
      gtag('config','G-00TNDVMQNM');
      window.addEventListener('DOMContentLoaded',function(){var d;try{d=localStorage.getItem('rs_consent')}catch(e){return}if(d)return;var b=document.createElement('div');b.style.cssText='position:fixed;left:0;right:0;bottom:0;z-index:99999;background:#0b0f17;color:#e6e9ef;padding:14px 18px;font:14px/1.5 system-ui,-apple-system,sans-serif;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:center;border-top:1px solid #2a3140';b.innerHTML='<span style="max-width:620px">We use cookies for analytics to understand traffic and improve the site. See our <a href="https://rebelstudiossoftware.com/privacy.html" style="color:#4ade80">Privacy Policy</a>.</span>';function mk(t,bg,fg){var x=document.createElement('button');x.textContent=t;x.style.cssText='cursor:pointer;border:0;border-radius:8px;padding:8px 16px;font-weight:600;background:'+bg+';color:'+fg;return x}var a=mk('Accept','#4ade80','#0b0f17'),n=mk('Decline','#3a424f','#e6e9ef');a.onclick=function(){try{localStorage.setItem('rs_consent','granted')}catch(e){}gtag('consent','update',{analytics_storage:'granted'});b.remove()};n.onclick=function(){try{localStorage.setItem('rs_consent','denied')}catch(e){}b.remove()};b.appendChild(a);b.appendChild(n);document.body.appendChild(b)});
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-adsense-account" content="ca-pub-4668633509273232">
    <meta name="description" content="%%DESC%%">
    <link rel="canonical" href="https://rebelstudiossoftware.com/blog-%%SLUG%%.html">
    <link rel="icon" href="images/RS-logo.png" type="image/png">
    <link rel="alternate" type="application/rss+xml" title="Rebel Studios Blog" href="https://rebelstudiossoftware.com/feed.xml">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://rebelstudiossoftware.com/blog-%%SLUG%%.html">
    <meta property="og:title" content="%%TITLE%%">
    <meta property="og:description" content="%%DESC%%">
    <meta property="og:image" content="https://rebelstudiossoftware.com/%%OGCARD%%">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:site_name" content="Rebel Studios Software">
    <meta property="article:published_time" content="%%DATE_ISO%%">
    <meta property="article:author" content="Patrick Galyen">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="%%TITLE%%">
    <meta name="twitter:description" content="%%DESC%%">
    <meta name="twitter:image" content="https://rebelstudiossoftware.com/%%OGCARD%%">
    <script type="application/ld+json">{"@context":"https://schema.org","@type":"BlogPosting","headline":"%%TITLE%%","description":"%%DESC%%","datePublished":"%%DATE_ISO%%","author":{"@type":"Person","name":"Patrick Galyen","url":"https://www.linkedin.com/in/patrick-galyen-5410b9a7/"},"publisher":{"@type":"Organization","name":"Rebel Studios Software","logo":{"@type":"ImageObject","url":"https://rebelstudiossoftware.com/images/RS-logo.png"}},"mainEntityOfPage":{"@type":"WebPage","@id":"https://rebelstudiossoftware.com/blog-%%SLUG%%.html"},"image":"https://rebelstudiossoftware.com/%%OGCARD%%"}</script>
    <title>%%TITLE%% - Rebel Studios Software</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
    <meta name="theme-color" content="#07090f">
    <link rel="stylesheet" href="styles.css">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4668633509273232"
         crossorigin="anonymous"></script>
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <div class="nav-brand">
                <a href="index.html" class="brand-link">
                    <img src="images/RS-logo.png" alt="Rebel Studios" class="logo">
                    <span class="brand-name">Rebel Studios</span>
                </a>
            </div>
            <ul class="nav-menu">
                <li><a href="index.html">Home</a></li>
                <li><a href="websites.html">Websites</a></li>
                <li><a href="apps.html">Mobile Apps</a></li>
                <li><a href="tools/index.html">Tools</a></li>
                <li><a href="about.html">About</a></li>
                <li><a href="blog.html" class="active">Blog</a></li>
                <li><a href="index.html#contact" class="nav-contact-btn">Hire Us</a></li>
            </ul>
            <div class="hamburger">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    </nav>

    <section class="page-header">
        <div class="container">
            <h1>%%TITLE%%</h1>
            <p>%%SUBTITLE%%</p>
        </div>
    </section>

    <article class="blog-article">
        <div class="container">
            <div class="article-wrapper">
                <div class="article-meta">
                    <span class="article-date">%%DATE_HUMAN%%</span>
                    <a href="https://www.linkedin.com/in/patrick-galyen-5410b9a7/" class="article-author" target="_blank" rel="noopener noreferrer">Patrick Galyen</a>
                </div>
%%HERO%%
                <div class="article-content">
%%BODY%%
                </div>

                <div class="article-footer-nav">
                    <a href="blog.html" class="btn btn-primary">&larr; Back to Blog</a>
                    <a href="%%NEXT_HREF%%" class="btn btn-secondary">Read: %%NEXT_LABEL%% &rarr;</a>
                </div>
            </div>
        </div>
    </article>

    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-brand">
                    <img src="images/RS-logo.png" alt="Rebel Studios" class="footer-logo">
                    <span>Rebel Studios Software</span>
                </div>
                <div class="footer-links">
                    <a href="websites.html">Websites</a>
                    <a href="apps.html">Mobile Apps</a>
                    <a href="tools/index.html">Tools</a>
                    <a href="blog.html">Blog</a>
                    <a href="privacy.html">Privacy</a>
                    <a href="terms.html">Terms</a>
                    <a href="index.html#contact">Contact</a>
                </div>
            </div>
            <p class="footer-copy">&copy; 2026 Rebel Studios Software. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>
'''

MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]


def main():
    if len(sys.argv) < 2:
        print("usage: python3 gen_article.py spec.json"); sys.exit(1)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))

    for req in ("slug", "title", "subtitle", "description", "body_html", "next_href", "next_label"):
        if not spec.get(req):
            print("missing required field:", req); sys.exit(1)

    slug = spec["slug"]
    date_iso = spec.get("date_iso") or datetime.date.today().isoformat()
    if spec.get("date_human"):
        date_human = spec["date_human"]
    else:
        y, m, d = date_iso.split("-")
        date_human = f"{MONTHS[int(m)-1]} {int(d)}, {y}"
    og_card = spec.get("og_card") or f"images/blog/{slug}.png"

    if spec.get("hero"):
        alt = spec.get("hero_alt", spec["title"])
        hero = f'\n                <figure class="article-hero"><img src="{spec["hero"]}" alt="{alt}" width="1280" height="720" loading="lazy"></figure>\n'
    else:
        hero = ""

    html = TEMPLATE
    for k, v in {
        "%%SLUG%%": slug,
        "%%TITLE%%": spec["title"],
        "%%SUBTITLE%%": spec["subtitle"],
        "%%DESC%%": spec["description"],
        "%%OGCARD%%": og_card,
        "%%DATE_ISO%%": date_iso,
        "%%DATE_HUMAN%%": date_human,
        "%%HERO%%": hero,
        "%%BODY%%": spec["body_html"],
        "%%NEXT_HREF%%": spec["next_href"],
        "%%NEXT_LABEL%%": spec["next_label"],
    }.items():
        html = html.replace(k, v)

    out = REPO / f"blog-{slug}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
