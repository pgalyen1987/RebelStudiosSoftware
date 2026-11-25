#!/usr/bin/env python3
"""Audit every page's identifying metadata against the page itself.

The bug this catches is mechanical and it has bitten this site before: a <head> block is
copy-pasted from a sibling page and the identifying fields are never updated. On 2026-09-29
games.html carried apps.html's canonical, og:url, og:title, og:description and JSON-LD, so
Google treated it as a duplicate and dropped it, and every social post of it shared the wrong
title. Nothing in the build would have noticed.

Page discovery copies generate_feeds.py exactly - same PAGE_DIRS, same NOT_A_PAGE, same
wants_out() - so a page that is in the sitemap is a page this audit covers, and the 22
deliberately noindexed tools/ pages are out of both.

Two tiers, because the first run of this script flagged 125 of 143 pages and most of that was
the script being wrong rather than the site:

  DEFECT   something is absent, unparseable, or points at another page. Always worth fixing.
           Includes a raw HTML entity inside a ld+json block: a <script> body is raw text, so
           "&amp;" there is five characters Google reads literally, not an ampersand.
  ADVISORY a title over 60 chars or a description over 155 (Google cuts near there, so the
           promise never renders), and an og:/json-ld wording that differs from the page's own
           on purpose. A social headline is allowed to differ from a SERP title, so this tier
           is a reading list, not a bug list. Which of these to rewrite is a question for GSC
           impressions, not for this script.

What separates the two is attribution, not equality. A low word overlap with the page's own
title is not enough on its own: "Seven licences shipped. We had written down two." shares no
words with its page's title and is a deliberate social hook. So a mismatched value is searched
against EVERY other page's title and description, and it is only a defect when some other page
is a clearly better match than this one. That is what the bug looks like - on 2026-11-25 this
found blog-app-review-guideline-2-1.html carrying the Solana tokenised-stocks post's headline
and the open-source-funding post's description inside its own JSON-LD.

Exit status is 1 when any DEFECT is found, so it can gate a commit. Advisories never fail it.

Usage:  env -u PYTHONPATH python3 meta_audit.py [--advisories]
"""

import json
import re
import sys
from html import unescape
from pathlib import Path

BASE = "https://rebelstudiossoftware.com"
ROOT = Path(__file__).parent

NOT_A_PAGE = {"404.html"}
PAGE_DIRS = [Path("."), Path("tools")]

TITLE_MAX = 60
DESC_MAX = 155
OVERLAP_MIN = 0.34   # below this, two strings are about different pages

# A suffix the <title> may carry that og:title is allowed to drop. Measured 2026-11-22: every
# one of about.html's 104 impressions is brand confusion with other companies, so the suffix
# pays nothing on an informational page and dropping it is a fix, not a defect.
BRAND_SUFFIXES = (" | Rebel Studios Software", " - Rebel Studios Software",
                  " | Rebel Studios", " - Rebel Studios")

# JSON-LD types that describe THIS page, so their url/@id must be this page. An Organization
# node's url is the site root on every page and that is correct - the first version of this
# script called that a defect on about.html.
PAGE_TYPES = {"WebPage", "Article", "BlogPosting", "NewsArticle", "TechArticle",
              "Product", "SoftwareApplication", "WebApplication", "MobileApplication",
              "FAQPage", "HowTo", "CollectionPage", "AboutPage", "ScholarlyArticle"}


def wants_out(html: str) -> bool:
    head = html[: html.lower().find("</head>") + 1 or 4000]
    return bool(re.search(r'name="robots"[^>]*content="[^"]*noindex', head, re.I)
                or re.search(r'http-equiv="refresh"', head, re.I))


def pages() -> list[tuple[str, Path, str]]:
    """(rel, path, html) for every page that wants to be indexed."""
    found = []
    for directory in PAGE_DIRS:
        for path in sorted((ROOT / directory).glob("*.html")):
            rel = path.name if directory == Path(".") else f"{directory}/{path.name}"
            html = path.read_text(encoding="utf-8")
            if rel in NOT_A_PAGE or wants_out(html):
                continue
            found.append((rel, path, html))
    return found


def tags(html: str, name: str) -> list[dict[str, str]]:
    """Every <name ...> element's attributes, scanned quote-aware.

    A regex of the form <meta[^>]*> is wrong on this site: the stable-tag post's own meta
    description contains the literal text "tags/<Stable tag>", so [^>]* ends the element in
    the middle of the attribute value and the page looks like it has no description at all.
    That false negative then hid a real defect in the same page's JSON-LD, which is the whole
    argument for parsing instead of pattern-matching.
    """
    out = []
    for m in re.finditer(rf"<{name}\b", html, re.I):
        i, quote = m.end(), ""
        while i < len(html):
            c = html[i]
            if quote:
                if c == quote:
                    quote = ""
            elif c in "\"'":
                quote = c
            elif c == ">":
                break
            i += 1
        attrs = {}
        for a in re.finditer(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)',
                             html[m.end():i]):
            attrs[a.group(1).lower()] = unescape(a.group(2).strip("\"'"))
        out.append(attrs)
    return out


def meta(html: str, value: str) -> str | None:
    """The content= of the <meta> whose name= or property= is `value`."""
    for attrs in tags(html, "meta"):
        if value.lower() in (attrs.get("name", "").lower(), attrs.get("property", "").lower()):
            if "content" in attrs:
                return attrs["content"].strip()
    return None


def canonical_of(html: str) -> str | None:
    for attrs in tags(html, "link"):
        if attrs.get("rel", "").lower() == "canonical" and "href" in attrs:
            return attrs["href"].strip()
    return None


def title_of(html: str) -> str | None:
    m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    return unescape(m.group(1)).strip() if m else None


def jsonld_of(html: str) -> tuple[list[dict], list[str]]:
    """Every parsed ld+json node, plus a message per block that would not parse or carries
    a raw HTML entity (a script body is raw text, so the entity never decodes)."""
    nodes, broken = [], []
    for m in re.finditer(r'<script[^>]*type=(["\'])application/ld\+json\1[^>]*>(.*?)</script>',
                         html, re.I | re.S):
        raw = m.group(2).strip()
        entities = sorted(set(re.findall(r"&(?:[a-zA-Z]+|#\d+);", raw)))
        if entities:
            broken.append(f"json-ld carries undecoded HTML entities Google reads literally: "
                          f"{', '.join(entities)}")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            broken.append(f"json-ld does not parse: {exc}")
            continue
        for node in (data if isinstance(data, list) else [data]):
            if isinstance(node, dict):
                nodes.append(node)
                for sub in node.get("@graph", []):
                    if isinstance(sub, dict):
                        nodes.append(sub)
    return nodes, broken


def expected_url(rel: str) -> str:
    """The one URL this file should claim. index.html is served as its directory."""
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return f"{BASE}/{rel[: -len('index.html')]}"
    return f"{BASE}/{rel}"


def same_url(a: str, b: str) -> bool:
    return a.rstrip("/") == b.rstrip("/")


def strip_brand(title: str) -> str:
    for suffix in BRAND_SUFFIXES:
        if title.endswith(suffix):
            return title[: -len(suffix)].strip()
    return title


def overlap(a: str, b: str) -> float:
    """Share of the shorter string's words that the longer one also has."""
    wa = set(re.findall(r"[a-z0-9]+", a.lower()))
    wb = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


def attribute(text: str, rel: str, index: dict[str, list[str]]) -> str | None:
    """The page `text` matches better than `rel` does, if any. That is the copy-paste bug.

    A deliberate social hook shares few words with its own title but matches nothing else
    either, so it comes back None and the caller files an advisory instead of a defect.
    """
    own = max((overlap(text, c) for c in index.get(rel, [])), default=0.0)
    best, best_share = None, own + 0.25   # another page has to win clearly, not narrowly
    for other, candidates in index.items():
        if other == rel:
            continue
        share = max((overlap(text, c) for c in candidates), default=0.0)
        if share > best_share:
            best, best_share = other, share
    return f"{best} ({best_share:.0%} match, {own:.0%} against its own)" if best else None


def page_scoped(node: dict) -> bool:
    types = node.get("@type")
    types = types if isinstance(types, list) else [types]
    return any(t in PAGE_TYPES for t in types if isinstance(t, str))


def audit_page(rel: str, html: str, index: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    defects, advisories = [], []
    want = expected_url(rel)
    title = title_of(html)
    desc = meta(html, "description")

    canon = canonical_of(html)
    if not canon:
        defects.append("no rel=canonical")
    elif not same_url(canon, want):
        defects.append(f"canonical points at {canon} (should be {want})")

    og_url = meta(html, "og:url")
    if not og_url:
        defects.append("no og:url")
    elif not same_url(og_url, want):
        defects.append(f"og:url points at {og_url} (should be {want})")

    if not title:
        defects.append("no <title>")
    elif len(title) > TITLE_MAX:
        advisories.append(f"<title> is {len(title)} chars (Google cuts near {TITLE_MAX})")

    if not desc:
        defects.append("no meta description")
    elif len(desc) > DESC_MAX:
        advisories.append(f"meta description is {len(desc)} chars (cuts near {DESC_MAX})")

    og_title = meta(html, "og:title")
    if not og_title:
        defects.append("no og:title")
    elif title:
        elsewhere = (attribute(og_title, rel, index)
                     if overlap(strip_brand(og_title), strip_brand(title)) < OVERLAP_MIN else None)
        if elsewhere:
            defects.append(f"og:title belongs to {elsewhere}: {og_title!r}")
        elif strip_brand(og_title) != strip_brand(title):
            advisories.append(f"og:title reworded: {og_title!r} vs <title> {title!r}")

    og_desc = meta(html, "og:description")
    if not og_desc:
        defects.append("no og:description")
    elif desc:
        elsewhere = attribute(og_desc, rel, index) if overlap(og_desc, desc) < OVERLAP_MIN else None
        if elsewhere:
            defects.append(f"og:description belongs to {elsewhere}")
        elif og_desc != desc:
            advisories.append("og:description reworded against the meta description")

    og_image = meta(html, "og:image")
    if not og_image:
        defects.append("no og:image")
    else:
        if not og_image.startswith("http"):
            defects.append(f"og:image is not absolute: {og_image}")
        local = ROOT / og_image.replace(BASE + "/", "")
        if og_image.startswith(BASE) and not local.exists():
            defects.append(f"og:image file is missing on disk: {og_image}")

    if not meta(html, "twitter:card"):
        defects.append("no twitter:card (X renders the link as a bare URL)")

    nodes, broken = jsonld_of(html)
    defects += broken
    if not nodes and not broken:
        advisories.append("no json-ld")
    for node in nodes:
        if page_scoped(node):
            for field in ("url", "@id", "mainEntityOfPage"):
                val = node.get(field)
                if isinstance(val, dict):
                    val = val.get("@id") or val.get("url")
                if isinstance(val, str) and val.startswith(BASE) and not same_url(val, want):
                    defects.append(f"json-ld {field} points at {val} (should be {want})")
        body = node.get("description")
        if isinstance(body, str) and desc and overlap(body, desc) < OVERLAP_MIN:
            elsewhere = attribute(body, rel, index)
            if elsewhere:
                defects.append(f"json-ld description belongs to {elsewhere}")
        head = node.get("headline")
        if isinstance(head, str) and title:
            elsewhere = (attribute(head, rel, index)
                         if overlap(strip_brand(head), strip_brand(title)) < OVERLAP_MIN else None)
            if elsewhere:
                defects.append(f"json-ld headline belongs to {elsewhere}: {head!r}")
            elif strip_brand(head) != strip_brand(title):
                advisories.append(f"json-ld headline reworded: {head!r} vs <title> {title!r}")
    return defects, advisories


def main() -> int:
    show_advisories = "--advisories" in sys.argv
    found = pages()
    # Every page's own words, so a stray value can be traced to the page it was copied from.
    index = {rel: [t for t in (title_of(html), meta(html, "description")) if t]
             for rel, _path, html in found}
    with_defects = advisory_pages = 0
    for rel, _path, html in found:
        defects, advisories = audit_page(rel, html, index)
        if defects:
            with_defects += 1
        if advisories:
            advisory_pages += 1
        lines = [("DEFECT  ", d) for d in defects]
        if show_advisories:
            lines += [("advisory", a) for a in advisories]
        if lines:
            print(f"\n{rel}")
            for tag, text in lines:
                print(f"  {tag} {text}")
    print(f"\n{len(found)} pages audited: {with_defects} with defects, "
          f"{advisory_pages} with advisories"
          + ("" if show_advisories else " (--advisories to list them)"))
    return 1 if with_defects else 0


if __name__ == "__main__":
    sys.exit(main())
