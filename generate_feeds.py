#!/usr/bin/env python3
"""Generate sitemap.xml and feed.xml from the pages that are actually on disk.

The sitemap used to come from a hand-maintained STATIC_PAGES list, and on 2026-11-01 that list
was wrong in two measurable ways:

  * 6 indexable pages were missing entirely - press.html, indemnity.html, app-terms.html and the
    three per-game privacy pages. A page absent from the sitemap is a page Google has no reason to
    recrawl, and press.html exists precisely so writers can find it.
  * Every date was typed by hand and 28 of 121 were behind the real edit: index.html claimed
    2026-06-24 after an 2026-10-29 rewrite, oops-all-knights.html claimed 2026-10-11 the day its
    hero was rebuilt.

Pages are now discovered, and two rules keep the result honest:

  * A page is in the sitemap unless it says it does not want to be. robots noindex or a
    meta-refresh stub excludes it. That is what keeps the 22 templated $1-tool pages out
    (commit 0db59c8 noindexed them on purpose as Google "doorway / little added value" pages)
    and chart-rush.html out while it is unreleased - without anyone having to remember.
  * lastmod ignores sweep commits. 61 of the 121 entries in the sitemap this replaces claimed
    2026-10-29, the day a single footer link was added to 82 pages. So a commit touching >=20
    html pages counts for a page only when THIS page got far more than the rest: over 3x that
    commit's median lines and over 10. Measured across all 34 site-wide commits that leaves 0-6
    pages each - the font swap, the phi radius scale and the footer link count for nobody, while
    pages genuinely rewritten inside the 2026-10-11 copy sweep (117 lines against a median of 4)
    keep that date. Line count is a proxy for "did the content change" and it errs toward the
    older date: understating freshness is the safe direction for a signal Google drops once it
    catches you overstating.

No <changefreq> or <priority>: Google documents that it ignores both, so 127 hand-picked values
were 127 chances to be wrong about nothing.
"""

import re
import subprocess
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

BASE = "https://rebelstudiossoftware.com"
ROOT = Path(__file__).parent




SWEEP_FILES = 20   # a commit touching this many html pages is a site-wide edit
SWEEP_MULT = 3     # ...and counts for a page only above 3x its median lines
SWEEP_FLOOR = 10   #    and above this, so a median of 1 cannot let a 2-line edit through

NOT_A_PAGE = {"404.html"}          # noindex already, but it must never be a candidate
PAGE_DIRS = [Path("."), Path("tools")]  # art/ is 1200x630 OG-card templates, not pages


def html_history() -> list[dict]:
    """Newest-first: every commit that touched an html file, with lines changed per file."""
    try:
        out = subprocess.run(
            ["git", "log", "--no-merges", "--no-renames", "--format=C|%cs", "--numstat", "--", "*.html"],
            capture_output=True, text=True, timeout=60, cwd=ROOT,
        ).stdout
    except Exception:
        return []
    commits: list[dict] = []
    cur: dict | None = None
    for line in out.splitlines():
        if line.startswith("C|"):
            cur = {"date": line[2:], "files": {}}
            commits.append(cur)
            continue
        parts = line.split("\t")
        if cur is not None and len(parts) == 3:
            try:
                cur["files"][parts[2]] = int(parts[0]) + int(parts[1])
            except ValueError:   # binary diff
                cur["files"][parts[2]] = 0
    for commit in commits:
        sizes = sorted(commit["files"].values())
        commit["sweep"] = len(sizes) >= SWEEP_FILES
        commit["bar"] = max(SWEEP_FLOOR, SWEEP_MULT * sizes[len(sizes) // 2]) if commit["sweep"] else 0
    return commits


HISTORY = html_history()


def last_real_edit(rel: str) -> str:
    """Date of the newest commit that changed this page's own content (see the module docstring)."""
    touching = [c for c in HISTORY if rel in c["files"]]
    for commit in touching:
        if not commit["sweep"] or commit["files"][rel] > commit["bar"]:
            return commit["date"]
    if touching:
        return touching[-1]["date"]      # only ever swept: use the commit that created it
    return datetime.now().strftime("%Y-%m-%d")   # untracked, so it changed just now


def wants_out(html: str) -> bool:
    head = html[: html.lower().find("</head>") + 1 or 4000]
    return bool(re.search(r'name="robots"[^>]*content="[^"]*noindex', head, re.I)
                or re.search(r'http-equiv="refresh"', head, re.I))


def sitemap_pages() -> list[tuple[str, str]]:
    """(loc suffix, lastmod) for every page that wants to be indexed."""
    pages = []
    for directory in PAGE_DIRS:
        for path in sorted((ROOT / directory).glob("*.html")):
            rel = path.name if directory == Path(".") else f"{directory}/{path.name}"
            if rel in NOT_A_PAGE or wants_out(path.read_text(encoding="utf-8")):
                continue
            # index.html is served as the directory itself, which is what its canonical says.
            if path.name == "index.html":
                suffix = "" if directory == Path(".") else f"{directory}/"
            else:
                suffix = rel
            pages.append((suffix, last_real_edit(rel)))
    # Homepage first, then alphabetical: a stable order means a readable diff.
    return sorted(pages, key=lambda p: (p[0] != "", p[0]))




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


def build_sitemap() -> str:
    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for suffix, lastmod in sitemap_pages():
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = BASE + ("/" if suffix == "" else f"/{suffix}")
        SubElement(url, "lastmod").text = lastmod
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
        "    <description>What we broke, measured and fixed while building Rebel Studios: security, AI agents, WordPress and apps.</description>",
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
    (ROOT / "sitemap.xml").write_text(build_sitemap(), encoding="utf-8")
    (ROOT / "feed.xml").write_text(build_feed(posts), encoding="utf-8")
    print(f"Generated sitemap.xml ({len(sitemap_pages())} indexable pages) and feed.xml ({len(posts)} blog posts)")


if __name__ == "__main__":
    main()
