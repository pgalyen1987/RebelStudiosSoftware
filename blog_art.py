#!/usr/bin/env python3
"""One image per blog post, each made for that post: a photo, a screenshot of the tool or product
the post is about, or a diagram drawn for it. No shared title-card template.

The manifest, blog_art.json, says what each post's image is:

    "<slug>": {"kind": "photo",   "pexels": 123, "alt": "...", "focus": 0.5}     a Pexels photo (free licence),
                                                                                credited under the article's hero
    "<slug>": {"kind": "crop",    "src": "images/products/x/shot-1.png",
               "box": [x, y, w, h], "alt": "..."}                               part of an existing screenshot
    "<slug>": {"kind": "page",    "url": "tools/csv-json.html", "alt": "...",
               "steps": [["fill", "#in", "a,b"], ["click", "#go"], ["upload", "input[type=file]", "art/samples/x.jpg"],
                         ["wait", 800], ["eval", "js"]],
               "clip": "#output" | [x, y, w, h], "viewport": [w, h]}            a live screenshot of our own page
    "<slug>": {"kind": "diagram", "html": "art/<slug>.html", "alt": "..."}      drawn for the post

    python3 blog_art.py render [slug ...]     make images/blog/<slug>.(jpg|png) (all posts if none given)
    python3 blog_art.py apply [slug ...]      point the post's og/twitter/JSON-LD image and its blog.html card at it
    python3 blog_art.py photos <query> [n]    Pexels candidates for a post, as a numbered contact sheet
    python3 blog_art.py sheet [out.png]       every card image on the blog index, to look for repeats
    python3 blog_art.py fetch <pexels-id> <name>   a photo into art/assets/<name>.jpg for a drawing to build on
                                                (prints the credit to put in the drawing)

Output is 1200x630: the share image and the index card. Photos need PEXELS_API_KEY
(~/.config/rebel-studios/creds.env).
"""
import http.server
import io
import json
import os
import re
import sys
import threading
import urllib.request
from functools import partial
from pathlib import Path

# The machine's global PYTHONPATH points at a system Playwright that can't start; run without it.
if "dist-packages" in os.environ.get("PYTHONPATH", ""):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    os.execvpe(sys.executable, [sys.executable, *sys.argv], env)

from PIL import Image, ImageDraw  # noqa: E402

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "blog_art.json"
OUT = ROOT / "images" / "blog"
W, H = 1200, 630
SITE = "https://rebelstudiossoftware.com/"


def load():
    return json.loads(MANIFEST.read_text())


def save(m):
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")


def creds(name):
    if os.environ.get(name):
        return os.environ[name]
    for line in (Path.home() / ".config/rebel-studios/creds.env").read_text().splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"')
    sys.exit(f"{name} not set")


def cover(im, focus=0.5):
    """Scale and crop to 1200x630; `focus` is where the crop sits vertically (0 top, 1 bottom)."""
    im = im.convert("RGB")
    scale = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x = (im.width - W) // 2
    y = round((im.height - H) * focus)
    return im.crop((x, y, x + W, y + H))


def pexels(path):
    req = urllib.request.Request("https://api.pexels.com/v1/" + path, headers={"Authorization": creds("PEXELS_API_KEY"), "User-Agent": "rebelstudios-blog-art"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "rebelstudios-blog-art"})
    return urllib.request.urlopen(req, timeout=60).read()


class Server:
    """The site served from disk, so tool pages can be screenshotted before (or without) a deploy."""

    def __enter__(self):
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
        handler.log_message = lambda *a: None
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{self.httpd.server_port}/"

    def __exit__(self, *a):
        self.httpd.shutdown()


def browser_shots(jobs):
    """jobs: list of (slug, spec). Renders page and diagram entries with one browser."""
    from playwright.sync_api import sync_playwright
    out = {}
    with Server() as base, sync_playwright() as p:
        b = p.chromium.launch()
        for slug, s in jobs:
            vw, vh = s.get("viewport", [W, H])
            pg = b.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=s.get("scale", 1))
            # the cookie banner would be in every screenshot
            pg.add_init_script("try{localStorage.setItem('rs_consent','denied')}catch(e){}")
            pg.goto(base + (s["url"] if s["kind"] == "page" else s["html"]), wait_until="networkidle")
            for step in s.get("steps", []):
                op, *args = step
                if op == "fill":
                    pg.fill(args[0], args[1])
                elif op == "click":
                    pg.click(args[0])
                elif op == "upload":
                    pg.set_input_files(args[0], str(ROOT / args[1]))
                elif op == "wait":
                    pg.wait_for_timeout(args[0])
                elif op == "eval":
                    pg.evaluate(args[0])
                elif op == "scroll":
                    pg.evaluate(f"window.scrollTo(0, {args[0]})")
            pg.evaluate("document.fonts.ready")
            clip = s.get("clip")
            if isinstance(clip, str):
                png = pg.locator(clip).first.screenshot()
            elif clip:
                png = pg.screenshot(clip=dict(zip("x y width height".split(), clip)))
            else:
                png = pg.screenshot()
            out[slug] = Image.open(io.BytesIO(png))
            pg.close()
        b.close()
    return out


def render(slugs):
    m = load()
    slugs = slugs or list(m)
    browser = [(s, m[s]) for s in slugs if m[s]["kind"] in ("page", "diagram")]
    shots = browser_shots(browser) if browser else {}
    for slug in slugs:
        s = m[slug]
        if s["kind"] == "photo":
            photo = pexels(f"photos/{s['pexels']}")
            im = cover(Image.open(io.BytesIO(fetch(photo["src"]["large2x"]))), s.get("focus", 0.5))
            s["credit"] = {"name": photo["photographer"], "url": photo["photographer_url"], "photo": photo["url"]}
        elif s["kind"] == "crop":
            src = Image.open(ROOT / s["src"])
            x, y, w, h = s.get("box", [0, 0, src.width, src.height])
            im = cover(src.crop((x, y, x + w, y + h)), s.get("focus", 0.5))
        else:
            im = cover(shots[slug], s.get("focus", 0.5))
        ext = "jpg" if s["kind"] == "photo" else "png"
        path = OUT / f"{slug}.{ext}"
        if ext == "jpg":
            im.save(path, quality=84, optimize=True, progressive=True)
        else:
            im.save(path, optimize=True)
        s["image"] = f"images/blog/{slug}.{ext}"
        print(f"{slug}: {s['kind']} → {s['image']}")
    save(m)


def apply(slugs):
    m = load()
    index = (ROOT / "blog.html").read_text()
    for slug in slugs or list(m):
        s = m[slug]
        if "image" not in s:
            print(f"{slug}: not rendered yet, skipped")
            continue
        url, alt = SITE + s["image"], s["alt"].replace('"', "&quot;")
        post = ROOT / f"blog-{slug}.html"
        h = post.read_text()
        h = re.sub(r'(<meta property="og:image" content=")[^"]*(")', rf"\g<1>{url}\2", h)
        h = re.sub(r'(<meta name="twitter:image" content=")[^"]*(")', rf"\g<1>{url}\2", h)
        h = re.sub(r'("@type":"BlogPosting".*?"image":")[^"]*(")', rf"\g<1>{url}\2", h, count=1, flags=re.S)
        if s["kind"] == "photo":
            # the photo also opens the essay, credited, like the older photo essays
            c = s["credit"]
            fig = (f'<figure class="article-hero"><img src="{s["image"]}" alt="{alt}" width="1200" height="630" loading="lazy">'
                   f'<figcaption class="article-credit">Photo: <a href="{c["photo"]}" target="_blank" rel="noopener">{c["name"]}</a> on Pexels</figcaption></figure>')
            if '<figure class="article-hero">' in h:
                h = re.sub(r'<figure class="article-hero">.*?</figure>', lambda _: fig, h, count=1, flags=re.S)
            else:
                h = h.replace('<div class="article-content">', fig + '\n\n                <div class="article-content">', 1)
        post.write_text(h)
        card = re.compile(rf'(<a href="blog-{re.escape(slug)}\.html" class="blog-card"[^>]*>\s*<div class="blog-card-img"><img src=")[^"]*(" alt=")[^"]*(")')
        if card.search(index):
            index = card.sub(rf"\g<1>{s['image']}\g<2>{alt}\3", index)
        else:
            bare = re.compile(rf'(<a href="blog-{re.escape(slug)}\.html" class="blog-card"[^>]*>)(\s*)(<div class="blog-card-content">)')
            if not bare.search(index):
                print(f"{slug}: no card in blog.html")
            index = bare.sub(lambda mm: f'{mm.group(1)}{mm.group(2)}<div class="blog-card-img"><img src="{s["image"]}" alt="{alt}" width="1200" height="630" loading="lazy"></div>{mm.group(2)}{mm.group(3)}', index)
        print(f"{slug}: applied")
    (ROOT / "blog.html").write_text(index)


def photos(query, n=12):
    res = pexels(f"search?query={urllib.request.quote(query)}&per_page={n}&orientation=landscape")["photos"]
    tw, th = 400, 210
    sheet = Image.new("RGB", (tw * 4, (th + 22) * ((len(res) + 3) // 4)), "white")
    d = ImageDraw.Draw(sheet)
    for i, p in enumerate(res):
        im = cover(Image.open(io.BytesIO(fetch(p["src"]["medium"])))).resize((tw, th))
        x, y = (i % 4) * tw, (i // 4) * (th + 22)
        sheet.paste(im, (x, y))
        d.text((x + 4, y + th + 4), f"{i + 1}. {p['id']}  {p['photographer'][:30]}", fill="black")
        print(f"{i + 1}. {p['id']}  {p['alt'][:90]!r}  by {p['photographer']}")
    out = Path("/tmp") / f"pexels-{re.sub(r'[^a-z0-9]+', '-', query.lower())}.png"
    sheet.save(out)
    print(out)


def fetch_asset(pid, name):
    photo = pexels(f"photos/{pid}")
    dest = ROOT / "art" / "assets" / f"{name}.jpg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(io.BytesIO(fetch(photo["src"]["large2x"]))).convert("RGB")
    im.save(dest, quality=88)
    print(f"{dest.relative_to(ROOT)}  {im.width}x{im.height}  Photo: {photo['photographer']} / Pexels  {photo['url']}")


def sheet(out):
    index = (ROOT / "blog.html").read_text()
    imgs = re.findall(r'class="blog-card"[^>]*>\s*<div class="blog-card-img"><img src="([^"]+)"', index)
    tw, th, cols = 300, 158, 6
    S = Image.new("RGB", (tw * cols, th * ((len(imgs) + cols - 1) // cols)), "white")
    for i, f in enumerate(imgs):
        S.paste(Image.open(ROOT / f).convert("RGB").resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    S.save(out)
    print(out, len(imgs))


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["help"]
    if cmd == "render":
        render(args)
    elif cmd == "apply":
        apply(args)
    elif cmd == "photos":
        photos(args[0], int(args[1]) if len(args) > 1 else 12)
    elif cmd == "fetch":
        fetch_asset(args[0], args[1])
    elif cmd == "sheet":
        sheet(args[0] if args else "/tmp/blog-cards.png")
    else:
        print(__doc__)
