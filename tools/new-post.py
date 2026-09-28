#!/usr/bin/env python3
"""Build a blog post page from an existing one, so the boilerplate cannot drift.

Every post carries the same analytics snippet, consent banner, nav, schema block and footer. Hand
-copying that is how one page ends up without the GA tag or with last year's nav, so the template
is a REAL post read off disk and only the parts that differ are replaced.

    python3 tools/new-post.py            # writes the posts defined in POSTS below

It also inserts the card into blog.html and the item into feed.xml, because a post nothing links
to is a post nobody reads, and forgetting one of those two is the usual way it happens.
"""
import html
import io
import os
import re
from datetime import datetime

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(HERE, "blog-recursive-prompting.html")
SITE = "https://rebelstudiossoftware.com"


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, s):
    io.open(p, "w", encoding="utf-8").write(s)


def build(post, template):
    s = template
    old_slug = "blog-recursive-prompting"
    old_img = "images/blog/recursive-prompting.jpg"
    old_title = "Most &ldquo;Recursive Prompting&rdquo; Is a Loop"
    old_desc = ("Feeding a prompt its own output is still a loop - one that remembers. Real "
                "recursion means the work splits into smaller copies of itself and has a bottom. "
                "Why the distinction decides which failure you get: a plateau, or a bill.")
    old_date_iso = "2026-08-25"
    old_date_txt = "August 25, 2026"
    old_sub = ("Feeding a prompt its own output is a loop that remembers. Only one of the three "
               "common shapes is actually recursive &mdash; and it is the one that fails by exploding")

    # the article body, between the content div and the footer nav
    a = s.index('<div class="article-content">')
    b = s.index('<div class="article-footer-nav">')
    body = '<div class="article-content">\n' + post["body"] + "\n                </div>\n\n                "
    s = s[:a] + body + s[b:]

    # the two figures above the content: one diagram, and drop the stock hero
    s = re.sub(r'\s*<figure class="article-figure">.*?</figure>', "", s, flags=re.S)
    s = re.sub(r'\s*<figure class="article-hero">.*?</figure>',
               '\n                <figure class="article-hero"><img src="images/blog/%s.png" alt="%s" '
               'width="1200" height="630" loading="lazy"></figure>\n' % (post["slug"], html.escape(post["alt"])),
               s, flags=re.S)

    for old, new in [
        (old_img, "images/blog/%s.png" % post["slug"]),
        (old_slug, "blog-" + post["slug"]),
        (old_title, post["title"]),
        (old_desc, post["desc"]),
        (old_sub, post["sub"]),
        (old_date_iso, post["date_iso"]),
        (old_date_txt, post["date_txt"]),
    ]:
        s = s.replace(old, new)

    # the "read next" link at the foot, so the three refer to each other
    s = re.sub(r'<a href="blog-[a-z0-9-]+\.html" class="btn btn-secondary">Read:[^<]*</a>',
               '<a href="blog-%s.html" class="btn btn-secondary">Read: %s</a>' % (post["next_slug"], post["next_title"]),
               s)
    return s


def add_to_index(post, idx):
    card = (
        '                <a href="blog-%s.html" class="blog-card" style="--cat: 110;">\n'
        '                    <div class="blog-card-img"><img src="images/blog/%s.png" alt="%s" width="1200" height="630" loading="lazy"></div>\n'
        '                    <div class="blog-card-content">\n'
        '                        <span class="blog-card-date">%s</span>\n'
        '                        <h3>%s</h3>\n'
        '                        <p>%s</p>\n'
        '                        <span class="blog-card-read">Read Article &rarr;</span>\n'
        '                    </div>\n'
        '                </a>\n' % (post["slug"], post["slug"], html.escape(post["alt"]),
                                    post["date_txt"], post["title"], post["desc"])
    )
    if 'href="blog-%s.html"' % post["slug"] in idx:
        return idx                                    # already listed; do not duplicate
    # newest first: insert before the first existing card
    m = re.search(r'^\s*<a href="blog-[a-z0-9-]+\.html" class="blog-card"', idx, flags=re.M)
    return idx[:m.start()] + card + idx[m.start():]


def add_to_feed(post, feed):
    if "blog-%s.html" % post["slug"] in feed:
        return feed
    pub = datetime.strptime(post["date_iso"], "%Y-%m-%d").strftime("%a, %d %b %Y 09:00:00 +0000")
    item = (
        "<item>\n"
        "<title>%s</title>\n"
        "<link>%s/blog-%s.html</link>\n"
        "<guid isPermaLink=\"true\">%s/blog-%s.html</guid>\n"
        "<pubDate>%s</pubDate>\n"
        "<description>%s</description>\n"
        "</item>\n" % (post["title"], SITE, post["slug"], SITE, post["slug"], pub, post["desc"])
    )
    i = feed.index("<item>")
    return feed[:i] + item + feed[i:]
