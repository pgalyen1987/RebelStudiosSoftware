#!/usr/bin/env python3
"""Draw the diagram for a blog post from the numbers in it.

Not decoration. Each of these plots a measurement the post actually reports, so the card image
carries information instead of mood. A stock photograph of nobody, or a gradient, is the tell that
a post was assembled rather than written.

    python3 tools/make-post-art.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630
BG = (7, 9, 15)
FG = (230, 233, 239)
DIM = (122, 132, 150)
GREEN = (143, 224, 90)
RED = (232, 93, 93)
AMBER = (232, 168, 61)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "images", "blog")


def font(size, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""),
              "/usr/share/fonts/truetype/liberation/LiberationSans%s.ttf" % ("-Bold" if bold else "")):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def frame(title, sub):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((64, 54), title, font=font(40, True), fill=FG)
    d.text((64, 108), sub, font=font(22), fill=DIM)
    d.line([(64, 156), (W - 64, 156)], fill=(38, 44, 58), width=2)
    return im, d


def jump_ceiling():
    """The roof at y=80 against a 136px jump from a ledge at y=147."""
    im, d = frame("A 136px jump, and 29px of headroom",
                  "Nug's jump arc from the tallest ledge, against the ceiling constant")
    x0, y0, x1, y1 = 90, 210, W - 90, H - 96
    # Map only the band that matters (-60..230 in world units) across the whole box. Scaling the
    # full 540-tall world crushed every line into the top third and left the image mostly empty.
    lo, hi = -60.0, 230.0
    def gy(wy):
        return y0 + (wy - lo) / (hi - lo) * (y1 - y0)

    apex = gy(-27)
    d.line([(x0, apex), (x1 - 330, apex)], fill=GREEN, width=3)
    d.text((x0 + 8, apex - 30), "where a full jump peaks   y = -27", font=font(20, True), fill=GREEN)

    roof = gy(80)
    d.line([(x0, roof), (x1 - 330, roof)], fill=RED, width=3)
    d.text((x0 + 8, roof - 30), "ROOF = 80, the ceiling as shipped", font=font(20, True), fill=RED)

    head = gy(109)
    d.line([(x0, head), (x1 - 330, head)], fill=(80, 90, 110), width=2)
    d.text((x0 + 8, head + 8), "Nug's head, standing   y = 109", font=font(18), fill=DIM)

    ledge = gy(147)
    d.line([(x0, ledge), (x0 + 330, ledge)], fill=(96, 106, 126), width=8)
    d.text((x0 + 8, ledge + 14), "the tallest ledge in any level   y = 147", font=font(18), fill=DIM)

    # The two spans, in their own column on the right so nothing collides.
    cx_want, cx_got = x1 - 300, x1 - 170
    d.line([(cx_want, head), (cx_want, apex)], fill=GREEN, width=5)
    d.text((cx_want + 12, (head + apex) / 2 - 14), "136px", font=font(26, True), fill=GREEN)
    d.text((cx_want + 12, (head + apex) / 2 + 16), "the jump", font=font(17), fill=GREEN)
    d.line([(cx_got, head), (cx_got, roof)], fill=RED, width=5)
    d.text((cx_got + 12, (head + roof) / 2 - 14), "29px", font=font(26, True), fill=RED)
    d.text((cx_got + 12, (head + roof) / 2 + 16), "allowed", font=font(17), fill=RED)

    d.text((x0, H - 56), "Clipped to a fifth of its height on every high ledge.",
           font=font(21, True), fill=FG)
    d.text((x0, H - 30), "Six of the seven levels became uncrossable, and the test harness "
                         "modelled open sky, so it never saw it.", font=font(19), fill=DIM)
    im.save(os.path.join(OUT, "test-modelled-open-sky.png"))


def working_dir():
    """What `railway up` sends, versus what people assume it sends."""
    im, d = frame("What `railway up` actually uploads",
                  "Nine commits sat live-invisible for seven hours because of this gap")
    boxw, boxh = 300, 150
    top, bottom = 230, 430

    def box(x, y, label, sub, colour):
        d.rounded_rectangle([x, y, x + boxw, y + boxh], 12, outline=colour, width=3)
        d.text((x + 20, y + 26), label, font=font(24, True), fill=colour)
        d.text((x + 20, y + 68), sub, font=font(18), fill=DIM)

    box(80, top, "your commit", "what you pushed\nand reviewed", GREEN)
    box(80, bottom, "your working dir", "plus whatever is\nuncommitted right now", AMBER)
    box(W - 80 - boxw, (top + bottom) // 2, "the server", "what users get", FG)

    # the arrow that does not exist
    d.line([(80 + boxw + 10, top + boxh // 2), (W - 80 - boxw - 10, (top + bottom) // 2 + 40)],
           fill=(70, 78, 96), width=3)
    d.text((520, top + 8), "git push", font=font(21, True), fill=(120, 130, 150))
    d.text((470, top + 40), "deploys nothing: no source connected", font=font(18), fill=RED)

    # the arrow that does
    d.line([(80 + boxw + 10, bottom + boxh // 2), (W - 80 - boxw - 10, (top + bottom) // 2 + 110)],
           fill=AMBER, width=4)
    d.text((520, bottom + 60), "railway up", font=font(21, True), fill=AMBER)
    d.text((470, bottom + 92), "uploads the folder, not the commit", font=font(18), fill=AMBER)
    im.save(os.path.join(OUT, "railway-up-working-directory.png"))


def stale_base():
    """A branch taken from an old base, pushed, dropping four commits."""
    im, d = frame("Every gate passed. Four commits were gone.",
                  "An agent branched from a stale base and pushed a history that omitted them")
    y_main, y_work = 280, 470
    d.text((80, y_main - 58), "master", font=font(22, True), fill=FG)
    d.text((80, y_work - 58), "the agent's branch", font=font(22, True), fill=AMBER)
    xs = [180, 300, 420, 540, 660, 780, 900, 1020]
    # master line
    d.line([(150, y_main), (1080, y_main)], fill=(60, 68, 86), width=3)
    labels = ["", "", "search", "hero", "ROOF fix", "bot+gates", "", ""]
    for i, x in enumerate(xs):
        lost = labels[i] != ""
        col = RED if lost else (90, 100, 120)
        d.ellipse([x - 11, y_main - 11, x + 11, y_main + 11], fill=col)
        if lost:
            d.text((x - 34, y_main - 46), labels[i], font=font(16, True), fill=RED)
    # the branch point, well behind
    bx = xs[1]
    d.line([(bx, y_main), (bx, y_work)], fill=AMBER, width=3)
    d.line([(bx, y_work), (1080, y_work)], fill=AMBER, width=3)
    for x in xs[3:]:
        d.ellipse([x - 11, y_work - 11, x + 11, y_work + 11], fill=AMBER)
    d.text((bx - 58, y_work + 28), "branched here", font=font(17), fill=AMBER)
    d.text((760, y_work + 28), "pushed over master", font=font(17, True), fill=AMBER)
    d.text((80, H - 52), "The four red commits were not in the pushed history. "
                         "A known game-breaking bug came back, and every test was green.",
           font=font(20), fill=FG)
    im.save(os.path.join(OUT, "stale-base-dropped-commits.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    jump_ceiling()
    working_dir()
    stale_base()
    print("wrote 3 diagrams to", OUT)
