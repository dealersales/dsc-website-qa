#!/usr/bin/env python3
"""Estate survey — many dealer sites on one platform, in one pass.

For each domain it records the things that are wrong site-by-site rather than
per-template: sitemap state, robots state, the catch-all answer for an unknown
URL, the head layer of the homepage, where the company/FCA disclosure actually
sits (footer, homepage, finance page, dedicated disclosure page), and a sample
of vehicle pages (title shape, H1 count, double-encoded entities, broken \\u00a3
escapes).

Usage:
    python3 estate_survey.py domains.txt            # one domain per line
    python3 estate_survey.py --vdp 6 domains.txt    # sample 6 vehicle pages

Writes estate-survey.json and estate-survey.csv beside the domain list and
prints a per-site summary. Read the counts from the CSV, not from the terminal
scrollback: an absence claim ("no site carries an FRN") is exactly the finding
that gets retracted, so count domains in code.
"""

import argparse
import concurrent.futures
import csv
import json
import random
import re
import string
import sys
import urllib.error
import urllib.request

UA = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36")}

# Where dealers actually put the compliance block — placement follows the
# template generation, so a footer-only probe under-reports the count.
LEGAL_PATHS = ("/", "/finance", "/finance.php", "/about", "/about.php",
               "/fca-disclosure.php", "/fca-disclosure", "/privacy-policy",
               "/privacy-policy.php", "/policies", "/terms")

FRN_RE = re.compile(r"(?:FCA|FRN|firm reference)[^0-9]{0,30}(\d{6,7})", re.I)
CO_RE = re.compile(r"company (?:registration )?(?:no\.?|number)[^0-9]{0,15}(\d{6,8})", re.I)


def get(url, timeout=25):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
    return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)


def text_of(html):
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def head_bits(html):
    t = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
    d = re.search(r"<meta[^>]+name=['\"]description['\"][^>]*content=['\"](.*?)['\"]", html, re.S | re.I)
    c = re.search(r"<link[^>]+rel=['\"]canonical['\"][^>]*href=['\"]([^'\"]+)", html, re.I)
    h1 = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).strip()
          for x in re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.S)]
    return {"title": re.sub(r"\s+", " ", t.group(1)).strip() if t else "",
            "desc": re.sub(r"\s+", " ", d.group(1)).strip() if d else "",
            "canonical": c.group(1) if c else "", "h1": h1}


def vehicle_links(base, html, limit):
    """Any internal link that is not nav/static, validated later by content."""
    skip = re.compile(r"(about|contact|finance|warranty|review|sell|privacy|terms|"
                      r"polic|servicing|mot|news|sitemap|admin|login|"
                      r"\.(css|js|png|jpe?g|ico|svg|webp|pdf|zip)$)", re.I)
    found = []
    for m in re.finditer(r'href=["\']([^"\'#]+)', html):
        u = m.group(1)
        u = u if u.startswith("http") else base + u
        if not u.startswith(base) or skip.search(u.replace(base, "")):
            continue
        if u not in found:
            found.append(u)
    return found[: limit * 3]


def survey(domain, vdp_samples):
    base = f"https://{domain}"
    row = {"domain": domain, "error": ""}
    try:
        _, home, hdrs = get(base + "/")
    except Exception as exc:
        row["error"] = f"home {type(exc).__name__}"
        return row

    row.update(head_bits(home))
    row["title_len"] = len(row["title"])
    row["hsts"] = "Strict-Transport-Security" in hdrs
    row["analytics"] = bool(re.search(r"googletagmanager|gtag\(|google-analytics|fbq\(", home, re.I))

    # catch-all: does an unknown path answer 200?
    junk = "/" + "".join(random.choices(string.ascii_lowercase, k=10)) + "-zz"
    try:
        js, jbody, _ = get(base + junk)
        row["junk_status"] = js
        row["junk_serves_home"] = js == 200 and row["title"] in jbody
    except urllib.error.HTTPError as exc:
        row["junk_status"] = exc.code
        row["junk_serves_home"] = False
    except Exception:
        row["junk_status"] = "err"

    # sitemap + robots
    for key, path in (("sitemap", "/sitemap.xml"), ("robots", "/robots.txt")):
        try:
            _, body, hdrs2 = get(base + path, timeout=20)
            is_html = "<html" in body[:400].lower()
            if key == "sitemap":
                locs = len(re.findall(r"<loc>", body))
                row["sitemap_locs"] = locs
                row["sitemap_devhost"] = "127.0.0.1" in body or "localhost" in body
                row["sitemap_state"] = ("dev file" if row["sitemap_devhost"] else
                                        (f"{locs} urls" if locs else
                                         ("serves HTML" if is_html else "empty")))
            else:
                row["robots_state"] = "HTML soft-404" if is_html else "present"
        except urllib.error.HTTPError as exc:
            row[f"{key}_state"] = f"missing ({exc.code})"
        except Exception:
            row[f"{key}_state"] = "error"

    # legal + compliance block: probe every known surface, not just the footer
    frn, cono, privacy = set(), set(), False
    for path in LEGAL_PATHS:
        try:
            _, body, _ = get(base + path, timeout=20)
        except Exception:
            continue
        if "<html" not in body[:400].lower() and len(body) < 800:
            continue
        txt = text_of(body)
        frn.update(FRN_RE.findall(txt))
        cono.update(CO_RE.findall(txt))
        if re.search(r'href="[^"]*privacy', body, re.I):
            privacy = True
    row["frn"] = ",".join(sorted(frn))
    row["company_no"] = ",".join(sorted(cono))
    row["privacy_link"] = privacy

    # vehicle page sample
    titles, h1_counts, ents, uesc = [], [], 0, 0
    try:
        for listing in ("/cars", "/vehicles", "/stock", "/used-cars", "/vehicles.php", "/stock.php"):
            try:
                _, lh, _ = get(base + listing)
            except Exception:
                continue
            cands = vehicle_links(base, lh, vdp_samples)
            if cands:
                break
        got = 0
        for u in cands:
            if got >= vdp_samples:
                break
            try:
                _, vh, _ = get(u)
            except Exception:
                continue
            if not (re.search(r"£\s?[\d,]{3,}", vh) and re.search(r"[\d,]+\s*(?:miles|mi)\b", vh, re.I)):
                continue
            b = head_bits(vh)
            titles.append(b["title"])
            h1_counts.append(len(b["h1"]))
            body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", vh, flags=re.S)
            ents += len(re.findall(r"&amp;(?:quot|amp|#0?39|gt|lt);", body))
            uesc += len(re.findall(r"\bu00[a-f0-9]{2}", body))
            got += 1
        row["vdp_sampled"] = got
        row["vdp_generic_titles"] = sum(1 for t in titles if re.match(r"(vehicle details|used car details)", t, re.I))
        row["vdp_two_h1"] = sum(1 for n in h1_counts if n > 1)
        row["vdp_entities"] = ents
        row["vdp_u00a3"] = uesc
    except Exception as exc:
        row["vdp_sampled"] = 0
        row["error"] = row["error"] or f"vdp {type(exc).__name__}"
    return row


FIELDS = ["domain", "sitemap_state", "robots_state", "junk_status", "junk_serves_home",
          "title", "title_len", "desc", "canonical", "h1", "frn", "company_no",
          "privacy_link", "analytics", "hsts", "vdp_sampled", "vdp_generic_titles",
          "vdp_two_h1", "vdp_entities", "vdp_u00a3", "sitemap_locs", "error"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domains", help="text file, one domain per line")
    ap.add_argument("--vdp", type=int, default=4, help="vehicle pages to sample per site")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    domains = [l.strip() for l in open(args.domains) if l.strip() and not l.startswith("#")]
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for r in ex.map(lambda d: survey(d, args.vdp), domains):
            rows.append(r)
            print(f"{r['domain']:<36} sm={str(r.get('sitemap_state')):<16} "
                  f"rb={str(r.get('robots_state')):<16} junk={r.get('junk_status')} "
                  f"frn={r.get('frn') or '-'}", flush=True)

    with open("estate-survey.json", "w") as fh:
        json.dump(rows, fh, indent=1)
    with open("estate-survey.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})

    # counts you can quote — in domains, not pages
    print("\n--- estate totals (domains) ---")
    print("sites surveyed:        ", len(rows))
    print("no usable sitemap:     ", sum(1 for r in rows if "dev file" in str(r.get("sitemap_state")) or "missing" in str(r.get("sitemap_state")) or "HTML" in str(r.get("sitemap_state"))))
    print("no robots.txt:         ", sum(1 for r in rows if str(r.get("robots_state")) != "present"))
    print("soft-404 catch-all:    ", sum(1 for r in rows if r.get("junk_status") == 200))
    print("publish an FRN:        ", sum(1 for r in rows if r.get("frn")))
    print("publish a company no.: ", sum(1 for r in rows if r.get("company_no")))
    print("\nwrote estate-survey.json / .csv")


if __name__ == "__main__":
    sys.exit(main())
