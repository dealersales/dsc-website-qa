# the platform data-integrity checks (deep pass)

Proven on the template build (`<dealer>.platform-host`, Sep 2026) — a new build 9 days from
go-live, where the homepage-only pass had already found the head-layer gaps and this deeper pass
found the bugs that actually hurt. Run this **after** `platform-audit-patterns.md`,
on every page type, before a launch.

The head-layer gaps (no canonical, no schema, no OG, no H1) are real but they are *build-configuration*
failures that recur identically. The findings below are **data-integrity** failures — they differ per
site, a status-code sweep cannot see them, and they are what the client will hit in week one.

**Prove every one by comparison, not by eye.** Hash bodies, count elements, compare against the
outgoing site. "Looks fine" is how the soft-404 below survives every status-code-only pass.

## 1. Soft-404: an invalid `vehicle.php?id=` serves the whole stock page with HTTP 200

The single highest-value test on any `vehicle.php?id=` build:

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
B="https://{dealer}.platform-host"
curl -sL -A "$UA" "$B/stock.php"   -o stock.html
curl -sL -A "$UA" "$B/vehicle.php?id=deadbeefdeadbeefdeadbeefdeadbeef" -o invalid.html
md5 -q stock.html invalid.html        # identical hash = CONFIRMED soft-404
```

On the template build the invalid-id response was a byte-identical 65,217-byte copy of `stock.php`, md5
`224b1798174f0687a64c145abbd20861`, with the stock page's title and H1.

Why it matters: every sold car becomes another indexable near-duplicate forever; a customer
following a link to a car that has sold gets the whole stock list with no explanation; and an
uptime monitor cannot distinguish it from a real page, so a genuine stock-page outage reads healthy.
Report it as its own finding — it defeats monitoring as well as SEO.

## 2. Pagination that clamps, and duplicate card slots

Walk `?page=1..6` and compare **both** the byte size and the distinct vehicle ids per page:

```python
# page 1: 12 cards, 11 distinct      page 4: IDENTICAL to page 3
# page 2: 12 cards, 12 distinct      page 5: IDENTICAL to page 3
# page 3:  6 cards,  6 distinct      page 6: IDENTICAL to page 3
# total: 30 card slots, 28 distinct vehicles
```

Two failure shapes, usually together:
- **Clamp:** `?page=4`+ serves page N again with **HTTP 200** (not 404, not a redirect) and the pagination
  widget silently rewrites itself to "Page 3 / 3". Infinite near-duplicate URLs.
- **Duplicate rows:** card slots > distinct ids, i.e. two stock records appear on more than one page.
  Expect this to be the *cause* of the inflated count below.

Count cards by their container class (`class="col-md-6 col-lg-4"`), not by `vehicle.php` mentions —
each card links the same id from the image and the title, so mention-counts double.

## 3. Stock counts: there are usually three numbers and none of them agree

Harvest the count from every place it appears and compare to the truth:

| Source | the template build |
|---|---|
| Body copy | "around **35** quality used cars in stock" |
| Listing link / search counter | "View all **30** in stock" |
| **Distinct vehicles actually listed** | **28** |
| Outgoing site's dynamic counter | 27 cars + 1 motorhome = **28** ✓ |

Overstating stock is a CAP Code / consumer-protection exposure, not a copy nit — say so. The fix is
often just "the old site already does this dynamically from the same feed".

## 4. Price-range claims vs the actual listings

Pull every price off the listing pages and compare to the advertised range:

```python
for m in re.finditer(r'class="price"[^>]*>(.*?)</div>', raw, re.S):
    t = html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).replace('£','').replace(',','').strip()
```

the template build advertised **"Cars from £3,000 to £90,000"** in four body locations *and the homepage meta
description*. Actual range across 30 cards: **£5,995 – £27,495** — nothing under £5,995, nothing over
£27,495, zero vehicles above £50,000. The search dropdown also offered a £2,000 minimum and a
£100,000 maximum, so both extremes returned an empty result set.
Always test the filter extremes after reading the copy — a filter that returns nothing is the moment
the false claim becomes visible to the customer.

## 5. One vehicle, two cards, two prices

Group listing/VDP links by id and print the titles+prices behind each. On the template build the homepage
"Latest Arrivals" showed the same Volkswagen Passat twice, at **£13,495** and **£13,995**, both
linking to `vehicle.php?id=2d753bfe…` (which resolves to the £13,495 car). The identical image-count
badge on both cards ("52") confirmed the duplicate feed row. Root cause is the same as §2.

## 6. Feed copy published as code — escape codes and double-encoded entities

Two corruptions from the same import stage. Neither shows up in a mojibake scan, both are invisible in a
spec-table or status-code pass, and both print *code* where the customer should read a character:

- **Stripped Unicode escape.** The backslash of a `\uXXXX` escape is lost in the feed, so the raw code is
  published. Seen as `u2013` in opening hours and as `u00a3` for every pound sign inside advert copy:
  > WE ARE OPEN MONDAY**u2013**SATURDAY 9AM**u20136**PM … ONLY **u00a320** PER YEAR ROAD TAX … AMAZING VALUE AT ONLY **u00a34000**
- **Double-encoded entities.** Text already containing `&quot;` / `&amp;` is escaped once more on output,
  so `&amp;amp;quot;` reaches the browser and the page reads:
  > FINISHED IN THE STUNNING **&quot;**NARDO GREY**&quot;** PAINTWORK … PREMIUM LEATHER **&amp;** ALCANTARA **&quot;**RECARO**&quot;** SPORTS SEATS

Count both across **every** saved VDP — one build had `u2013` on 1 of 6 VDPs, which is why a spot check
reports the estate clean:

```python
import re, glob, html, csv
rows = []
for f in glob.glob('vdp/*.html'):
    s = open(f, encoding='utf-8', errors='replace').read()
    cid = re.search(r'/car/(\d+)/', s).group(1)
    d = (re.search(r'Description\s*</h2>\s*<div[^>]*>\s*<p[^>]*>(.*?)</p>', s, re.S) or [None, ''])[1]
    shown = html.unescape(d)                      # what one browser parse leaves visible
    ent = re.findall(r'&amp;[a-z#0-9]+;?', shown)   # leftover entities = double-encoded
    esc = re.findall(r'\bu00[a-f0-9]{2}', shown)     # £ / en dash published as code
    rows.append((cid, len(ent), len(esc), shown))
```

**Report the union with the overlap, not one count per signature.** Two per-signature numbers read as two
isolated medium findings; on a live 62-car site it was 28 entity-hit + 29 escape-hit, overlapping on 15 →
**42 of 62 adverts (68%) affected**, which is the sentence that matches a dealer saying "full of errors
including strange letters and signs". Both counts being right and the headline being wrong is the failure
mode to avoid.

### The control group decides who broke it — and it costs one comparison

Do **not** report this as "the dealer's adverts are wrong" or "the feed is dirty" until you have checked
the *clean* records for the same characters. If the unaffected descriptions contain not a single `"`, `&`
or `£`, then every special character in the estate is encoded and nothing is being passed through
literally: the fault is an encode-without-decode in the import, and the adverts at source are probably
fine. On that site all 20 clean cars contained no quote, ampersand or pound sign at all — decisive, and it
reframes the finding from a data-quality complaint into a one-function platform fix.

```python
# control group: clean records should contain literal punctuation if the source is clean
clean = [r for r in rows if not r[1] and not r[2]]
print(len(clean), sum(1 for r in clean if re.search(r'["&£]', r[3])))
```

If instead the clean records *do* carry literal `"`/`&`/`£` and the broken ones do not, the corruption is
per-record and the source text (or the person who pasted it) is where the entities came from — different
owner, different fix.

### Repair and hand-over

- **Fix at the write, not the read:** decode once when the feed is imported into the CMS (`html_entity_decode`
  one pass, plus a repair for `\uXXXX` escapes), then repair the existing rows. Deploying an
  `html_entity_decode` into the *template* instead double-decodes anything genuinely containing an
  ampersand and hides the stored corruption, so the records stay wrong for the next consumer of the feed.
- **Add a publish guard** that rejects `&amp;amp;` and `u00[0-9a-f]{2}` in the description field, or the next
  cron run reintroduces it.
- **Deliver a per-car CSV** — car id, registration, price, count per fault, and the offending sentence —
  so the dealer or feed provider can see their own cars and the fix can be verified car by car. It is the
  artefact that turns "full of errors" into a work list, and it is what a retention conversation needs.
- **Separate the sound data from the broken text** in the same pass and say so: unique registrations, no
  duplicate rows, listing prices matching the VDPs, year/mileage present. A dealer told "your copy is
  mangled by our import, your car data is correct" hears something different from "your adverts are full
  of mistakes", and only one of those makes them stay.
- Check the description against the car beside it while you are in there: a 2014 Hyundai i30 whose advert
  opens "2013 HYUNDAI i30" is a real mismatch, and it reads as one more "error" in a complaint that is
  mostly about encoding.

## 7. Review pages: truncated attribution

The rebuilt reviews template commonly loses the **year** from every attribution:
new `"James O in July 17,"` vs old `"James O · AutoTrader · July 17, 2024"`. Grep for the dangling pattern:

```bash
grep -oh 'in [A-Z][a-z]* [0-9]\{2\},' reviews.html | sort | uniq -c
```

Ten reviews, ten missing years, in the the template build case. Also check for double spaces in reviewer names
(`"Amer  Rehman"`).

**False-positive trap:** review body text is user-generated. A reviewer writing "the template build
motors" in lowercase, or mentioning Japanese imports at a dealership whose stock you did not check,
is **not** a copy error and **not** a wrong-dealer-name finding. Confirm the reviews are genuinely
that dealer's (the outgoing site carries the same reviewers with names, source and dates) before
flagging anything.

## 8. WhatsApp / share links carrying the staging host

```bash
grep -oh 'https://wa\.me/[0-9]*?text=[^"]*' *.html | head
```

Decoded, every the template build VDP pre-filled: *"I am interested in this 2023 Volkswagen T-Roc:
**http://<dealer>.platform-host**/vehicle.php?id=…"* — staging host **and** plain http.
After go-live every enquiry the dealer receives contains a dead URL. Grep the whole build for
`platform-host` and `http://` inside share/enquiry templates.

## 9. Orphan pages

Fetch a list of plausible `.php` names and check each one's inbound links:

```bash
for u in about about-us sell sell-your-car vehicle-delivery privacy cookies terms faq blog news; do
  printf "%-18s %s\n" "$u" "$(curl -sL -o /dev/null -A "$UA" -w '%{http_code}' "$B/$u.php")"
done
grep -l 'vehicle-delivery' *.html || echo "NOT LINKED from any fetched page (orphan)"
```

`vehicle-delivery.php` returned 200 with real copy and a correct H1 but was linked from **nothing** —
while the outgoing site had it in the nav. With no sitemap it is undiscoverable to users *and*
crawlers. Check the outgoing site's nav list against the new nav: a page that exists on both but is
only linked on the old one is a cosmetic-looking omission that costs real content.

## 10. Forms: count consent inside the form, not on the page

`grep -c 'type="checkbox"' page.html` returns the **cookie banner's** checkboxes, not the form's, and
`recaptcha` matches the footer's *claim* of protection. Parse each `<form>` block instead:

```python
for i, blk in enumerate(re.findall(r'(?s)<form.*?</form>', raw), 1):
    fields = re.findall(r'<(?:input|textarea|select)[^>]*name="([^"]*)"', blk)
    print(i, fields, '| checkbox:', len(re.findall('type="checkbox"', blk)),
          '| privacy link:', len(re.findall('polic', blk, re.I)))
```

On the template build all four forms (contact, VDP enquiry, finance, part-exchange — the last capturing VRM,
version, mileage and condition) had **no consent checkbox, no privacy link and no reCAPTCHA**. The
old site had `g-recaptcha-response` *and* a `__RequestVerificationToken` CSRF field, both lost in the
rebuild. Dump every `<script src>` plus `js/site.js` and grep for `recaptcha|gtag|analytics` — if it
appears nowhere, the footer's reCAPTCHA sentence is a false claim and the forms are unprotected.

## 11. Analytics inventory, and the privacy policy that contradicts it

```bash
grep -oh '<script[^>]*src="[^"]*"' *.html | sed 's/.*src="\([^"]*\)"/\1/' | sort -u
```

the template build's entire JS inventory was jQuery, Bootstrap, Swiper, AOS, lazyload and `js/site.js` — **no
GTM, no GA4, no pixel** — while the outgoing site loaded GA4 `G-W2FM2JP033` + GTM, and the new
`policies.php` stated *"We use Google Analytics 4 (GA4) to analyse website traffic"*. Two findings in
one: no measurement, and a policy describing tracking that does not exist. Reuse the existing GA4
property id so history survives the domain move.

## 12. Cookie banner defaults

Read the markup, not the modal. A pre-ticked non-essential category is not valid PECR consent:

```html
<input id="consent-analytics" type="checkbox" value="Analytics" checked …>
<input id="consent-preferences" type="checkbox" value="Preferences" checked …>
```

Also scan for a real CMP (`cookieyes|complianz|cookiebot|onetrust|termly`) — a hand-rolled modal with
no CMP is the norm on these builds, and where no analytics are installed the Analytics toggle is
decorative.

## 13. The outgoing site is the best evidence source — crawl it the same day

Every claim of loss or regression should be a measurement. Fetch the outgoing site's homepage and
key pages in the same session and diff:

- **Stock count** — old dynamic counter vs new hardcoded number (§3).
- **Filter facets** — old had Make, Model, Price, Status, Version, Body Type, Fuel, Transmission,
  Engine Size, Mileage, Vehicle Type, Seats, Colour, Year, VAT, ULEZ; new had Make, Model, Min/Max
  Price. The new cards *badge* ULEZ compliance but the user cannot filter by it — a specific miss for
  a Bradford clean-air-zone audience.
- **Analytics + reCAPTCHA** — both present on the old site, both absent on the new (§10, §11).
- **OG tags** — old had 7, new had 0.
- **Trading name** — the new site said "the template build **Motors**", the live site said "the template build **Motor
  Group**" in its title, nav, footer and H1s (and so did the email, Facebook and Instagram), while
  AutoTrader said "the template build". Surface this as a **decision for the client**, not a build fix:
  whichever name the Google Business Profile carries is what everything else must match.
- **Warranty / MOT / service promises** — written into several pages independently, so they drift.
  New homepage and About Us: "Minimum **6 months** warranty … on every car over £5,000"; the warranty
  page (inherited unchanged): "**3 Months** Free dealer warranty on all cars". The old homepage made
  no warranty claim at all — that absence is what establishes which wording is this rebuild's.

## 14. Build the redirect map from the old link graph

The outgoing site's `sitemap.xml` is often a soft-404 (HTML body, HTTP 200), so there is no URL
inventory to inherit. Crawl it instead and dedupe:

```python
paths = re.findall(r'href=["\']([^"\']+)', raw)   # unanchored — link styles vary per build
# strip the host, drop assets and cdn-cgi, then prepend '/' to anything not starting with http or /
```

That recovered **35 content URLs + 22 vehicle URLs** for the template build, including:
- 11+ keyworded landing pages (`/stock/used-bmws-in-bradford-west-yorkshire`, `/stock/used-audis-…`,
  `/stock/motorhomes-…`) that the flat new build replaces with query-string filters — the single
  biggest SEO regression in a platform rebuild.
- **Two URL shapes for the same vehicle:** `/vehicle/{slug}-{guid}` *and* a bare `/{slug}-{guid}` —
  the second appears in the old site's own WhatsApp share text, and both may be indexed, so the
  redirect map must cover both.
- A motorhome/Polaris section that vanished entirely: the new build still offers **Polaris** in its
  make dropdown and the feed still carries the vehicle, but "motorhome" appears 0 times on the new
  site vs 14 on the old one. Ask whether that stock line is still being sold — a silent product gap
  is a revenue finding, not an SEO one.

### When the outgoing site is already gone — rebuild the inventory from the Wayback CDX index

Post-launch there is nothing left to crawl, and the outgoing `sitemap.xml` was a soft-404 anyway. The
CDX API returns every URL the archive ever captured, which is enough to enumerate every shape that
needed mapping:

```bash
curl -sS "http://web.archive.org/cdx/search/cdx?url=DOMAIN/*&output=json&fl=original&collapse=urlkey&limit=2000"
```

Strip non-page assets by extension, dedupe on the path, probe each one against the live host, and
bucket the responses (301 / 404 / 200). A count is what turns "the redirects need finishing" into a
ticket with a size on it — one the platform rebuild measured **205 archived page URLs, 204 of them 404 and
none redirecting**. Expect a long tail of older site generations (`/search/{make}/{model}/`,
`/used-car/…`, `/_pages/…`) that were already dead long before this rebuild: separate those from the
previous generation's URLs, which are the ones carrying the actual loss, and say which bucket each
falls in rather than reporting one total.

### A rebuild that changes the URL shape needs the OLD shape mapped, per family

Adding an extension to a path is enough to orphan every URL under it. One build redirected **all 13**
keyworded `/stock/…` landing pages to the correct filters while every extensionless static page
(`/finance`, `/contact-us`, `/about-us`, `/warranty`) 404'd against the `.php` equivalent the new site
actually serves. Probe one URL from each family — landing pages, static pages, vehicle detail in every
slug form the old site used (both `/vehicle/{slug}-{guid}` and the bare `/{slug}-{guid}` form its own
share links emitted) — because a map written for the pages the developer thought of passes a spot
check. Where the old and new sites use entirely different slug conventions, expect every old vehicle
URL to need a rule even when the car itself is long sold: map it to the stock page rather than letting
it 404.

## 15. Sitemap: stale file, malformed URLs, and the canonical that follows the request

On a **live** the platform build (as opposed to the pre-launch passes above) the sitemap is where the
biggest silent loss sits, because it is generated by a script nobody triggers.

```python
import re, urllib.request
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
xml = urllib.request.urlopen(urllib.request.Request(B + "/sitemap.xml", headers={"User-Agent": UA})).read().decode()
locs = re.findall(r"<loc>([^<]+)</loc>", xml)
print(len(locs), "locs; lastmods:", set(re.findall(r"<lastmod>([^<]+)", xml)))
for u in locs:
    if "/car/" not in u: continue
    fixed = u.replace("//car/", "/car/")
    print(u, "->", status(u), "| corrected ->", status(fixed))
```

A real case: 78 locs, 68 of them vehicle pages, **every** vehicle loc double-slashed, **47 of the 68
a 404 even at the corrected address**, and one `lastmod` date for the whole file three months old.
Three separate findings came out of that one file:

- **stale** — one identical `lastmod` across every URL is the age of the file. `/sitemap.xml` was a
  static file; `sitemap.php` regenerated only when something requested `/sitemap` (no extension).
  Fix the routing (`RewriteRule ^sitemap\.xml$ sitemap.php [L]`), not just the file.
- **malformed** — `$baseUrl = 'https://site.co.uk/'` concatenated with a `getCarUrl()` that returns
  `/car/…`. Count the corrected-form 200s, not the raw ones.
- **stale inventory** — the corrected-form 404s are sold cars the generator never prunes.

**The canonical trap sits underneath it.** `car.php` resolves a vehicle by `id` alone and ignores the
slug, while `includes/header.php` sets `$canonicalUrl = 'https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']`.
So `/car/70401/wrong-slug-test` → **200**, canonical pointing at `wrong-slug-test`, and the correct
slug behaves identically. One car, unlimited indexable URLs, each declaring itself canonical. Confirm
with two fetches (wrong slug, real slug) and read the `<link rel="canonical">` value, not its presence.
Because a regenerated sitemap re-slugs cars from current feed fields (the live slug may predate a field
the feed now emits), **fix the canonical before the sitemap** or the sitemap fix doubles the URL count
instead of consolidating it.

## 16. Verifying a template fix locally before it goes anywhere near the live host

When the fix is in a template (`sitemap.php`, `.htaccess`, a partial) and the live host is not yours to
touch yet, prove the change in a scratch copy rather than shipping blind. The stock loader's API key is
redacted in the mirror, so stub the feed:

```bash
PHP=~/.local/php-static/php
S="$HOME/.hermes/profiles/dsc/cache/scratch/sitemap_test"
rm -rf "$S"; mkdir -p "$S/includes" "$S/custom"
cp sitemap.php "$S/"; cp includes/stock-loader.php "$S/includes/"
cp config.example.php "$S/config.php"
printf '%s\n' '<?php $config = ["dealer"=>["did"=>4028],"api"=>["base_url"=>"","stock_endpoint"=>""],"seo"=>["default_title"=>"t","default_description"=>"d","default_keywords"=>"k"]];' > "$S/custom/config.php"
# then point the copy's $apiUrl at file:///…/feed.json holding two real vehicle rows and run it
$PHP "$S/sitemap.php" > "$S/out.xml"
```

This exercises the **real** `getCarUrl()` and the real slug builder, so the output proves the URLs it
will publish. Assert on the artefacts, not the console: `grep -c '//car' out.xml` is 0, the car locs
carry single slashes, and `python3 -c "import xml.etree.ElementTree as ET; ET.parse('out.xml')"`
parses. `php -l` both changed PHP files as the syntax gate. Keep the untouched originals beside the
edited files as `*.bak-YYYYMMDD` so the deploy is reversible, and say in the reply that nothing was
uploaded.

**A `.htaccess` catch-all cannot become a 404 until you have enumerated the extension-less links the
site actually uses.** Grep every `href` for paths with no file extension and confirm each one has an
explicit `RewriteRule`; only then swap `RewriteRule ^(.*)$ index.php` for a real 404 handler plus
`ErrorDocument 404 /404.php`. A real `robots.txt` file is served automatically once the catch-all
stops swallowing it, because `RewriteCond %{REQUEST_FILENAME} !-f` then lets it through.

## Ordering the launch-blocker list

Lead with the three that make a launch *unsafe* rather than merely suboptimal, then the data
integrity bugs, then the compliance items:

1. `noindex` the staging host (and add "remove noindex" to the go-live checklist).
2. Canonicals + the homepage H1.
3. Stock count, duplicate rows and the price-range claim (§2–§5).
4. Analytics + reCAPTCHA (§10, §11).
5. robots.txt + sitemap + the 301 map (§14).
6. FCA wording, consent checkboxes and cookie defaults.
