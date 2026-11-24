#!/usr/bin/env python3
"""Starter live-site health harness for a platform-built dealer site.

Copy next to the audit folder, set HOST (or pass it as argv[1]), then run after every
launch and after every fix batch. It gives a re-runnable scoreboard instead of a claim:
`14/22 checks pass`, and it fails loudly on the regressions the next change introduces.

    python3 check-live-site.py example.co.uk        # summary
    python3 check-live-site.py example.co.uk -v     # with evidence per check

This is a starter, not a universal law: the privacy paths, the finance iframe and the
company-number pattern are the shapes seen on this platform. Delete checks that do not
apply, and add the site's own legacy URL families. Every extraction-based check prints
INFO rather than PASS when it finds nothing, so a regex that has stopped matching can
never read as a clean bill.
"""
import re, sys, subprocess, urllib.request, urllib.error
from collections import Counter
from urllib.parse import urlparse

HOST = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "example.co.uk"


# Work out the canonical host BEFORE any check runs. After an apex->www redirect every
# follow=False check (404, privacy page, canonical) sees a 301 instead of the page and
# reports a false failure — a burst of red immediately after a correct redirect fix.
def _status(url):
    class NR(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    try:
        return urllib.request.build_opener(NR).open(urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Macintosh) Chrome/141.0"}), timeout=20).status
    except Exception:
        return 0


BASE_HOST = f"www.{HOST}" if _status(f"https://www.{HOST}/") == 200 else HOST
BASE = f"https://{BASE_HOST}"
VERBOSE = "-v" in sys.argv
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0 Safari/537.36")
results = []


def fetch(url, follow=True):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    handler = urllib.request.HTTPRedirectHandler if follow else NoRedirect
    opener = urllib.request.build_opener(handler)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        r = opener.open(req, timeout=30)
        return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, {}, str(e)


def check(name, state, evidence=""):
    """state: True (pass), False (fail), None (info - extraction found nothing)."""
    results.append((name, state, evidence))
    label = "PASS" if state is True else ("FAIL" if state is False else "INFO")
    print(f"  {label}  {name}")
    if VERBOSE and evidence:
        print(f"        {evidence}")


def mx_records(domain):
    try:
        return subprocess.run(["dig", "+short", "MX", domain, "@1.1.1.1"],
                              capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


print(f"Live-site harness - {BASE}\n")

st, hd, home = fetch(BASE + "/")
check("Homepage returns 200", st == 200, f"status={st}")
if st != 200:
    print("\nCannot continue: homepage did not load.")
    sys.exit(1)

# --- sitemap: valid, own host, contains vehicles -------------------------------
st, hd, sm = fetch(BASE + "/sitemap.xml")
locs = re.findall(r"<loc>([^<]+)</loc>", sm)
hosts = Counter(urlparse(u).netloc for u in locs)
own = hosts.get(HOST, 0) + hosts.get("www." + HOST, 0)
check("Sitemap is XML", "xml" in hd.get("Content-Type", "").lower(), hd.get("Content-Type", ""))
check("Sitemap lists only this domain", bool(locs) and own == len(locs), f"hosts={dict(hosts)}")
check("Sitemap URLs have no doubled slash", bool(locs) and not any("//" in u.split("://", 1)[1] for u in locs),
      f"{sum('//' in u.split('://', 1)[1] for u in locs)} of {len(locs)}")
vehicles = [u for u in locs if "/car/" in u or "/vehicle/" in u]
check("Sitemap includes vehicles", bool(vehicles), f"{len(vehicles)} vehicle URLs")

# --- robots.txt ---------------------------------------------------------------
st, hd, rb = fetch(BASE + "/robots.txt")
check("robots.txt is text/plain", "text/plain" in hd.get("Content-Type", "").lower(),
      hd.get("Content-Type", ""))
check("robots.txt declares the sitemap", "Sitemap:" in rb,
      next((l for l in rb.splitlines() if l.strip().lower().startswith("sitemap")), "absent"))

# --- real 404, and it must not canonicalise itself ----------------------------
junk = "/this-page-does-not-exist-xyz123"
st, hd, b404 = fetch(BASE + junk, follow=False)
head = b404.split("</head>")[0]
check("Unknown URL returns 404", st == 404, f"status={st}")
check("404 does not self-canonicalise", "this-page-does-not-exist" not in head,
      "canonical echoes the requested junk path")

# --- one canonical host -------------------------------------------------------
st_a, _, ba = fetch(BASE + "/", follow=False)
st_w, _, bw = fetch(f"https://www.{HOST}/", follow=False)
check("Apex and www settle to one host", st_a in (301, 308) or st_w in (301, 308),
      f"apex={st_a} www={st_w}")

# --- mail ---------------------------------------------------------------------
# The PUBLISHED address matters, not the site's own domain: a dealer on a free mailbox has a
# deliverable address while the domain itself carries no MX at all, and the reverse trap is a
# domain with MX whose published info@ mailbox was never created.
pub = (re.findall(r"[\w.+-]+@[\w.-]+\.\w+", home) or [""])[0]
mx = mx_records(pub.split("@")[-1]) if pub else ""
check("Published email domain has MX", bool(mx),
      f"{pub or 'no email published'} -> {mx or 'no MX - enquiries would bounce'}")

# --- privacy ------------------------------------------------------------------
pp = None
for p in ["/privacy.php", "/privacy-policy.php", "/policies.php", "/privacy", "/policies"]:
    st, hd, b = fetch(BASE + p, follow=False)
    title = re.findall(r"<title>(.*?)</title>", b, re.S + re.I)
    if st == 200 and len(b) > 2000 and title and "not found" not in title[0].lower():
        pp = p
        break
check("Privacy page exists", pp is not None, pp or "every candidate returned 404 or the homepage")
check("Privacy linked from homepage",
      bool(re.search(r'href="[^"]*(privacy|policies)[^"]*"', home, re.I)), "no privacy link")

# --- consent, analytics, company details --------------------------------------
check("Cookie consent mechanism present",
      None if not re.search(r"cookie|consent", home, re.I) else True,
      "no consent string found - confirm whether any tracker is running before calling it a breach")
# Assert the ID, not the loader string. A consent-gated loader ships "googletagmanager" in
# every page and requests nothing until the visitor accepts, so a substring test certifies
# a site that measures nothing.
ga = re.search(r"\bG-[A-Z0-9]{8,}\b", home)
check("GA4 measurement ID configured", bool(ga),
      ga.group(0) if ga else "no G- id (loader may exist and send nothing)")
# A sole trader has no company number, so absence is not a failure — record it as INFO and
# establish what the business actually is before writing it up. Never let a harness push you
# towards inventing an entity for the footer.
company = re.search(r"(?:company\s*(?:registration\s*)?(?:no|number)|registered\s+in\s+england)[^<]{0,60}?\d{6,8}",
                    home, re.I)
check("Company number in page", True if company else None,
      company.group(0)[:80] if company else "no company number - sole trader, or genuinely missing")

# --- head hygiene -------------------------------------------------------------
check("No keywords meta tag", not re.search(r'name=["\']keywords["\']', home, re.I), "keywords meta present")
check("og:image is absolute", bool(re.search(r'property=["\']og:image["\'] content=["\']https?://', home)),
      re.findall(r'property=["\']og:image["\'] content=["\']([^"\']+)', home)[:1])
vp = re.findall(r'name=["\']viewport["\'] content=["\']([^"\']+)', home)
check("Viewport allows pinch-zoom", bool(vp) and "user-scalable=no" not in vp[0], vp[:1])

# --- finance rates: page copy (and the iframe, when one is framed) -------------
apr_re = re.compile(r"APR[^0-9%]{0,25}(\d{1,2}(?:\.\d)?)\s*%|(\d{1,2}(?:\.\d)?)\s*%\s*APR", re.I)
aprs = set()
for p in ["/", "/finance.php", "/finance"]:
    _, _, b = fetch(BASE + p)
    for m in apr_re.finditer(b):
        g = next((x for x in m.groups() if x), None)
        if g:
            aprs.add(g)
if not aprs:
    check("Representative APR consistent", None, "no APR found in page copy - check manually")
else:
    check("One representative APR in page copy", len(aprs) <= 1, f"found {sorted(aprs)}")

iframe = re.search(r'<iframe[^>]+src=["\']([^"\']+finance[^"\']*)', home, re.I)
if iframe:
    st, hd, fin = fetch(iframe.group(1) if iframe.group(1).startswith("http") else BASE + iframe.group(1))
    framed = {next((x for x in m.groups() if x), None) for m in apr_re.finditer(fin)} - {None}
    all_rates = aprs | framed
    check("Framed finance module agrees with page copy", len(all_rates) <= 1,
          f"page={sorted(aprs)} iframe={sorted(framed)}")

failed = [r for r in results if r[1] is False]
inform = [r for r in results if r[1] is None]
print(f"\n{len(results) - len(failed) - len(inform)}/{len(results)} checks pass"
      + (f", {len(inform)} need a look" if inform else ""))
for n, state, e in results:
    if state is False:
        print(f"  FAIL  {n}" + (f"  [{e}]" if e else ""))
sys.exit(1 if failed else 0)
