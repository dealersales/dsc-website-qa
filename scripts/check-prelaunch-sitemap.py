#!/usr/bin/env python3
"""Pre-launch sitemap + robots.txt gate for a staging build moving to a live domain.

Usage:
    # Fail loudly if the staging sitemap still points at the build server
    python3 check-prelaunch-sitemap.py check https://<dealer>.platform-host

    # Rewrite it for the live domain and emit a matching robots.txt
    python3 check-prelaunch-sitemap.py build https://<dealer>.platform-host \
        https://www.livedomain.co.uk ./out

'check' exits 1 on any dev-host reference, so it can gate go-live.

Why this exists: the platform sitemap ships valid XML that returns 200 with all <loc>
entries pointing at http://127.0.0.1:81:81/client-site/... (the local build server,
doubled port). Nothing flags it, and submitting it tells Google every page's canonical
home is an unreachable localhost address. The staging host is usually the developer's
own dev machine, so the sitemap self-identifies as the wrong host until it is rewritten.
"""
import datetime
import os
import re
import sys
import urllib.request
from urllib.parse import urlsplit

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

BAD = ("127.0.0.1", "localhost", ":81", ":232", "platform-host")
LOC = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.S)
URL_BLOCK = re.compile(r"<url>(.*?)</url>", re.S)
CHANGEFREQ = re.compile(r"<changefreq>(.*?)</changefreq>", re.S)
PRIORITY = re.compile(r"<priority>(.*?)</priority>", re.S)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", "replace")


def parse(xml):
    out = []
    for block in URL_BLOCK.findall(xml):
        loc = LOC.search(block)
        if not loc:
            continue
        cf = CHANGEFREQ.search(block)
        pr = PRIORITY.search(block)
        out.append((loc.group(1).strip(),
                    cf.group(1) if cf else "weekly",
                    pr.group(1) if pr else "0.5"))
    return out


def prefix_of(locs):
    """Longest shared prefix. On a platform build the root <loc> is the dev URL exactly,
    so the shared prefix lands on the build root and nothing deeper."""
    prefix = os.path.commonprefix(locs)
    if not prefix.endswith("/"):
        prefix = prefix.rsplit("/", 1)[0] + "/"
    return prefix


def rel(loc, dev_prefix):
    if loc.startswith(dev_prefix):
        return loc[len(dev_prefix):]
    if loc.startswith("http"):
        return urlsplit(loc).path.lstrip("/")
    return loc.lstrip("/")


def build(base, entries, dev_prefix):
    base = base.rstrip("/")
    today = datetime.date.today().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, cf, pr in entries:
        lines.append("  <url><loc>%s/%s</loc><lastmod>%s</lastmod>"
                     "<changefreq>%s</changefreq><priority>%s</priority></url>"
                     % (base, rel(loc, dev_prefix), today, cf, pr))
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def robots(base):
    return ("User-agent: *\nAllow: /\n\n"
            "# Pre-launch: change the line above to 'Disallow: /' until go-live,"
            " then remove it.\n"
            "Sitemap: %s/sitemap.xml\n" % base.rstrip("/"))


def report(xml, label):
    locs = LOC.findall(xml)
    hosts = sorted({re.sub(r"^(https?://[^/]+).*", r"\1", u) for u in locs})
    print("%s: %d <loc>, hosts %s" % (label, len(locs), hosts))
    bad = [b for b in BAD if b in xml]
    if bad:
        print("  FAIL - dev/staging references present: %s" % bad)
        return False
    print("  PASS - no 127.0.0.1 / localhost / :81 / :232 / staging host")
    return True


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    mode, staging = sys.argv[1], sys.argv[2].rstrip("/")
    xml = get(staging + "/sitemap.xml")
    if mode == "check":
        return 0 if report(xml, staging) else 1
    if mode != "build" or len(sys.argv) < 4:
        print(__doc__)
        return 2
    live = sys.argv[3].rstrip("/")
    outdir = sys.argv[4] if len(sys.argv) > 4 else "."
    entries = parse(xml)
    dev_prefix = prefix_of([e[0] for e in entries])
    print("derived dev prefix: %s" % dev_prefix)
    print("  -- confirm that looks like the build root before trusting the output")
    sm = build(live, entries, dev_prefix)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(sm)
    with open(os.path.join(outdir, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(robots(live))
    print("wrote %s/sitemap.xml and %s/robots.txt" % (outdir, outdir))
    return 0 if report(sm, live) else 1


if __name__ == "__main__":
    sys.exit(main())
