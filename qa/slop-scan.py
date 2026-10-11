#!/usr/bin/env python3
"""Scan the site's pages for the tells that make copy read as machine-written.

Usage: python3 qa/slop-scan.py [--list] [page.html ...]
Prints a count per category, split into blog posts and everything else; --list also
prints each hit with its page and the sentence it sits in. Reads files as bytes and
strips NULs first (grep goes silent on a file with a NUL in it; see blog.html).

Categories:
  phrase      filler words and phrases (unlock, seamless, elevate, leverage, robust ...)
  describes   copy that describes instead of saying (solution, platform for, powerful ...)
  emdash      a paragraph with two or more em dashes, or a page above 10 per 1,000 words
  tricolon    "fast, simple, and secure": three one-word items closing a sentence
  emoji       emoji in visible text (bullets, headings, status lines)
  three-up    a grid of exactly three same-class cards
"""
import glob
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PHRASES = [
    r"in today'?s fast[- ]paced world", r"fast[- ]paced", r"\bseamless(ly)?\b",
    r"\bunlock(s|ing)? (the power|the potential|your (potential|business|growth|data)|new (levels|possibilities|opportunities)|insights|potential|value)\b",
    r"\belevat(e|es|ed|ing)\b", r"\bgame[- ]?changer\b", r"\bdive (in|into|deep)\b", r"\bdeep[- ]dive\b",
    r"\blet'?s (explore|dive)\b", r"\bleverag(e|es|ed|ing)\b", r"\bempower(s|ed|ing|ment)?\b", r"\brobust\b",
    r"\bcutting[- ]edge\b", r"\brevolutioni[sz](e|es|ed|ing)\b", r"\brevolutionary\b", r"\bharness(es|ed|ing)? (the )?(power|potential|ai)\b",
    r"\bsupercharg(e|es|ed|ing)\b", r"\bunleash(es|ed|ing)?\b", r"\bstreamlin(e|es|ed|ing)\b",
    r"\beffortless(ly)?\b", r"\bdelv(e|es|ed|ing)\b", r"\bstunning\b", r"\bworld[- ]class\b",
    r"\bstate[- ]of[- ]the[- ]art\b", r"\bnext[- ]level\b", r"\bbest[- ]in[- ]class\b", r"\bbuilt to scale\b",
    r"\bproduction[- ]ready\b", r"\btake (it|your \w+) to the next level\b", r"\blook no further\b",
    r"\bwhether you'?re\b", r"\bin the realm of\b", r"\bit'?s worth noting\b", r"\btapestry\b",
    r"\bbeautiful(ly)?\b", r"\bconversion[- ]focused\b", r"\bjourney\b", r"\bnavigat(e|ing) the\b",
    r"\bscalable\b", r"\bpixel[- ]perfect\b", r"\btailored\b", r"\bpassionate\b", r"\btop[- ]notch\b",
    r"\bhigh[- ]quality\b", r"\bseo[- ]optimi[sz]ed\b", r"\bproof, not promises\b", r"\bno spam\b",
]
DESCRIBES = [
    r"\bsolutions?\b", r"\bplatform for (construction|creators|teams|businesses|developers|professionals|\w+ professionals)\b", r"\bbuilt to help\b", r"\bhelps you\b",
    r"\ballows you to\b", r"\benables you to\b", r"\bpowerful\b", r"\binnovative\b", r"\bcomprehensive\b",
    r"\bend-to-end (guide|solution|platform)\b", r"\bbuilt end-to-end\b", r"\bone-stop\b", r"\ball-in-one\b",
    r"\bmodern (android )?(architecture|design|stack|look|ui|approach|solutions?|tech|technolog\w+|tooling|businesses)\b",
]
# Reviewed, literal uses: a hit whose sentence matches one of these is counted as "allowed",
# not as a tell (a product that really is a platform, a list that really has three items).
ALLOW = [
    r"paying a platform for the privilege",
    r"JSON: format, minify, and repair",
    r"re-encodes at high quality", r"at high quality is visually harmless",
    r"shoot on seamless",                                   # photography: seamless paper
    r"protects (the|your) subcontractor beautifully",       # a deliberate contrast, not decoration
    r"most powerful technology companies",                  # literal: a powerful company
    r"all-in-one backend \(hosting",                       # quoting Firebase's own pitch
    r"navigating the physical chaos",                       # literal
    r"I stopped logging in after a week",                   # "powerful" in quotes, as the foil
    r"isn.t robust enough for future scale",                # the perfectionist's own voice, on purpose
    r"than a beautiful, pristine branch",                   # same
]
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF⭐]")
ARROWS_OK = set("✓✔✗")  # check marks in comparison tables are symbols, not decoration
TRICOLON = re.compile(r"(?:^|[.!?]\s+|:\s+)([A-Z]?[a-z]+), ([a-z]+),? and ([a-z]+)[.!]")


def visible(raw):
    s = raw.replace("\x00", "")
    head = s.split("<body", 1)[0]
    metas = re.findall(r'<meta (?:name|property)="(?:description|og:description)" content="([^"]*)"', head)
    title = re.findall(r"<title>(.*?)</title>", head, re.S)
    body = s.split("<body", 1)[-1]
    body = re.sub(r"<(script|style|noscript|svg|pre|code)\b.*?</\1>", " ", body, flags=re.S | re.I)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    # paragraphs: split on block-level tags
    blocks = re.split(r"</?(?:p|li|h[1-6]|dd|dt|figcaption|td|th|blockquote|div|section|span class=\"[^\"]*(?:sub|tag|type)[^\"]*\")[^>]*>", body)
    out = []
    for b in title + metas + blocks:
        t = html.unescape(re.sub(r"<[^>]+>", " ", b))
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            out.append(t)
    return out, body


def scan(path):
    raw = open(path, "rb").read().decode("utf-8", "replace")
    blocks, body = visible(raw)
    hits = []
    words = sum(len(b.split()) for b in blocks)
    dashes = 0
    for b in blocks:
        low = b.lower()
        for pat in PHRASES:
            for m in re.finditer(pat, low):
                hits.append(("phrase", m.group(0), b))
        for pat in DESCRIBES:
            for m in re.finditer(pat, low):
                hits.append(("describes", m.group(0), b))
        n = b.count("—")
        dashes += n
        if n >= 2:
            hits.append(("emdash", f"{n} em dashes", b))
        for m in TRICOLON.finditer(b):
            if all(len(x) > 2 for x in m.groups()):
                hits.append(("tricolon", m.group(0).strip(" .:"), b))
        for ch in EMOJI.findall(b):
            if ch not in ARROWS_OK:
                hits.append(("emoji", ch, b))
    if words and dashes / words * 1000 > 10:
        hits.append(("emdash", f"page density {dashes / words * 1000:.1f} per 1,000 words", ""))
    # three-up: a grid whose direct children are exactly three elements sharing a card-ish class
    for m in re.finditer(r'<div class="([^"]*grid[^"]*)"([^>]*)>', body):
        if 'data-three="earned"' in m.group(2):
            continue
        start = m.end()
        depth, i, kids = 1, start, []
        tag = re.compile(r"<(/?)(div|a|article|section)\b([^>]*)>")
        for t in tag.finditer(body, start):
            if t.group(1):
                depth -= 1
                if depth == 0:
                    break
            else:
                if depth == 1:
                    c = re.search(r'class="([^"]*)"', t.group(3))
                    kids.append(c.group(1).split()[0] if c else "")
                depth += 1
        if len(kids) == 3 and len(set(kids)) == 1 and re.search(r"card|item|feature|tier|plan", kids[0]):
            hits.append(("three-up", f"{m.group(1)} > 3 x .{kids[0]}", ""))
    return hits


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pages = args or sorted(glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(os.path.join(ROOT, "tools", "*.html")))
    totals = {"blog": {}, "site": {}}
    listing = []
    for p in pages:
        rel = os.path.relpath(p, ROOT)
        kind = "blog" if os.path.basename(rel).startswith("blog-") else "site"
        for cat, what, ctx in scan(p):
            if ctx and any(re.search(a, ctx) for a in ALLOW):
                cat = "allowed"
            totals[kind][cat] = totals[kind].get(cat, 0) + 1
            listing.append((rel, cat, what, ctx[:220]))
    if "--list" in sys.argv:
        for rel, cat, what, ctx in listing:
            print(f"{rel}\t{cat}\t{what}\t{ctx}")
    for kind in ("site", "blog"):
        t = totals[kind]
        tells = sum(v for k, v in t.items() if k != "allowed")
        print(f"{kind:5s} tells {tells:4d}  " + "  ".join(f"{k} {v}" for k, v in sorted(t.items())))


if __name__ == "__main__":
    main()
