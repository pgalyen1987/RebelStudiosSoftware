#!/usr/bin/env python3
"""Which over-length snippets are worth rewriting? Join meta_audit advisories to GSC impressions.

WHY. meta_audit.py reports 124 pages with advisories -- 27 titles over 60 chars, 61 descriptions
over 155. Rewriting all of them is a bulk edit of copy Google has never shown, and a title rewrite
can cost rank. The only pages where a truncated snippet costs anything are the ones Google
ACTUALLY SHOWS at a position a human scrolls to. That is a Search Console question, so ask it:
rank the advisory pages by impressions, keep the ones whose average position is on page 1-2.

Ranking rule, stated because it is a judgement and not a measurement: impressions decide worth,
average position decides whether a snippet is seen at all. At our volume (954 impressions, 2
clicks in 28 days) a per-page CTR change is NOT measurable -- do not claim one. The case for the
edit is that a description cut at 155 chars loses its payoff every time it is shown, which is
true whether or not n is big enough to prove it.

    python3 snippet_targets.py [days]
"""
import re
import subprocess
import sys
import urllib.parse

sys.path.insert(0, "/home/me/boss/work/wp-mkt")
import gsc  # auth + call live there; never re-implement a key read

HERE = "/home/me/RebelStudiosSoftware"
LEN_ADVISORY = re.compile(r"advisory (<title>|meta description) is (\d+) chars")


def gsc_pages(days: int) -> dict:
    """{filename: (impressions, clicks, position)} -- full URLs, no display truncation."""
    start, end = gsc.window(days)
    body = {"startDate": start, "endDate": end, "dimensions": ["page"],
            "rowLimit": 500, "dataState": "all"}
    path = f"sites/{urllib.parse.quote(gsc.SITE, safe='')}/searchAnalytics/query"
    d, err = gsc.call(path, body)
    if err:
        print(f"FAILED to read GSC: {err}")
        sys.exit(2)
    out = {}
    for r in d.get("rows") or []:
        name = r["keys"][0].rsplit("/", 1)[-1] or "index.html"
        out[name] = (r["impressions"], r["clicks"], r["position"])
    return out, start, end


def advisories() -> dict:
    """{filename: {'title': n, 'desc': n}} for LENGTH advisories only.

    The 'reworded' advisories are deliberate -- a social hook is meant to differ from a search
    description -- so they are not targets and are skipped here on purpose.
    """
    txt = subprocess.run([sys.executable, "meta_audit.py", "--advisories"], cwd=HERE,
                         capture_output=True, text=True).stdout
    out, cur = {}, None
    for line in txt.splitlines():
        if line and not line.startswith(" "):
            cur = line.strip()
        elif cur:
            m = LEN_ADVISORY.search(line)
            if m:
                out.setdefault(cur, {})["title" if m.group(1) == "<title>" else "desc"] = int(m.group(2))
    return out


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 28
    pages, start, end = gsc_pages(days)
    adv = advisories()
    rows = []
    for name, lens in adv.items():
        impr, clicks, pos = pages.get(name, (0, 0, 0.0))
        rows.append((impr, pos, clicks, name, lens))
    rows.sort(key=lambda r: (-r[0], r[1]))
    shown = sum(1 for r in rows if r[0] > 0)
    print(f"{gsc.SITE}   {start} .. {end}")
    print(f"{len(adv)} pages carry a LENGTH advisory; {shown} of them had an impression.\n")
    print(f"  {'page':<52}{'impr':>6}{'clicks':>7}{'pos':>7}  {'title':>5} {'desc':>5}")
    for impr, pos, clicks, name, lens in rows:
        if impr == 0:
            continue
        t = lens.get("title", 0) or "-"
        dd = lens.get("desc", 0) or "-"
        flag = "  <== page 1-2" if pos and pos <= 20 else ""
        print(f"  {name[:51]:<52}{impr:>6.0f}{clicks:>7.0f}{pos:>7.1f}  {t:>5} {dd:>5}{flag}")
    print(f"\n  {len(rows) - shown} advisory pages have never been shown for any query; leave them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
