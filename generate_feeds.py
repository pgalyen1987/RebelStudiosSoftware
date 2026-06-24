#!/usr/bin/env python3
"""Generate sitemap.xml and feed.xml from blog HTML files."""

import re
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

BASE = "https://rebelstudiossoftware.com"
ROOT = Path(__file__).parent

STATIC_PAGES = [
    ("", "2026-06-24", "monthly", "1.0"),
    ("apps.html", "2026-06-23", "monthly", "0.8"),
    ("websites.html", "2026-06-23", "monthly", "0.8"),
    ("vigilo.html", "2026-06-24", "monthly", "0.8"),
    ("about.html", "2026-06-24", "monthly", "0.8"),
    ("blog.html", "2026-06-24", "weekly", "0.9"),
    ("privacy.html", "2026-06-23", "yearly", "0.3"),
    ("research.html", "2026-06-24", "monthly", "0.7"),
]


def parse_blog_post(path: Path) -> dict | None:
    html = path.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", html)
    desc = re.search(r'<meta name="description" content="(.*?)"', html)
    date = re.search(r'<meta property="article:published_time" content="(.*?)"', html)
    if not title or not desc:
        return None
    return {
        "file": path.name,
        "title": title.group(1).replace(" - Rebel Studios Software", ""),
        "description": desc.group(1),
        "date": date.group(1) if date else "2026-06-01",
    }


def build_sitemap(posts: list[dict]) -> str:
    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for loc_suffix, lastmod, freq, priority in STATIC_PAGES:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = BASE + ("/" if loc_suffix == "" else f"/{loc_suffix}")
        SubElement(url, "lastmod").text = lastmod
        SubElement(url, "changefreq").text = freq
        SubElement(url, "priority").text = priority
    for post in sorted(posts, key=lambda p: p["date"], reverse=True):
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = f"{BASE}/{post['file']}"
        SubElement(url, "lastmod").text = post["date"]
        SubElement(url, "changefreq").text = "yearly"
        SubElement(url, "priority").text = "0.6"
    xml = tostring(urlset, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml.replace('><', '>\n<') + "\n"


def rfc822_date(iso_date: str) -> str:
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return format_datetime(dt)


def build_feed(posts: list[dict]) -> str:
    items = sorted(posts, key=lambda p: p["date"], reverse=True)
    latest = items[0]["date"] if items else "2026-06-23"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        "    <title>Rebel Studios Software Blog</title>",
        f"    <link>{BASE}/blog.html</link>",
        "    <description>Insights on security, AI, and software engineering from Rebel Studios Software.</description>",
        "    <language>en-us</language>",
        f"    <lastBuildDate>{rfc822_date(latest)}</lastBuildDate>",
        f'    <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>',
        "    <image>",
        f"      <url>{BASE}/images/og-image.png</url>",
        "      <title>Rebel Studios Software</title>",
        f"      <link>{BASE}/</link>",
        "    </image>",
    ]
    for post in items:
        link = f"{BASE}/{post['file']}"
        desc = post["description"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        title = post["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.extend([
            "    <item>",
            f"      <title>{title}</title>",
            f"      <link>{link}</link>",
            f"      <guid isPermaLink=\"true\">{link}</guid>",
            f"      <pubDate>{rfc822_date(post['date'])}</pubDate>",
            f"      <description>{desc}</description>",
            "    </item>",
        ])
    lines.extend(["  </channel>", "</rss>", ""])
    return "\n".join(lines)


def main() -> None:
    posts = []
    for path in sorted(ROOT.glob("blog-*.html")):
        parsed = parse_blog_post(path)
        if parsed:
            posts.append(parsed)
    (ROOT / "sitemap.xml").write_text(build_sitemap(posts), encoding="utf-8")
    (ROOT / "feed.xml").write_text(build_feed(posts), encoding="utf-8")
    print(f"Generated sitemap.xml and feed.xml ({len(posts)} blog posts)")


if __name__ == "__main__":
    main()
