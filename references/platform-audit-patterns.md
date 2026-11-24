# the platform Platform Audit Patterns

Recurring findings from auditing the platform-built dealership websites (PHP, not WordPress).
Observed across several platform builds on `{dealer}.platform-host`. Expect these on other platform sites.

## Platform Architecture

- **PHP pages**, not WordPress: `index.php`, `vehicles.php`, `vehicle.php?id={hash}`, `about.php`, `contact.php`, etc.
- **Staging URL pattern**: `{dealer}.platform-host`
- **Stock images**: served from `stockimages.lon1.cdn.digitaloceanspaces.com` (DigitalOcean Spaces CDN) and `stockimages.<platform-host>` (the platform's own CDN with base64-encoded ImageLoad.php URLs)
- **VDP URLs**: `vehicle.php?id={32-char-hex-hash}` — query string based, need canonicals
- **CSS**: single `assets/css/site.css` file — check for media queries (a dealer had 24, good responsive framework)
- **Fonts**: Google Fonts (Poppins) loaded via `<link>` — render-blocking
- **Forms**: Contact Form 7 (`wpcf7-` classes) on contact and sell pages; custom enquiry form on VDPs

### The newest generation looks nothing like the older ones — fingerprint it first

The a dealer build (Sep 2026) is a third shape again, and none of the older assumptions held:

- **Self-contained front end.** One compiled stylesheet (`/assets/css/output.css`, ~33 KB) and
  **five inline `<script>` blocks** — no jQuery, no Bootstrap, no carousel plugin, no Tailwind Play
  CDN, no third-party JS whatsoever. Grepping for `jquery`/`cdn.`/`unpkg` returns nothing, which is a
  strong performance *pass*, not a failure to detect. Do not infer "no JS" from a missing
  `<script src>`: the nav toggle, hero slider and contact modal are all inline.
- **URL scheme is `/stock` + a routed `/vehicle/…` template** (`vehicle_router.php`), not
  `vehicle.php?id=`. Unknown paths return a **genuine 404** (~38 KB distinct error page), and the 404
  and `/thank-you.php` both correctly carry `noindex, follow` — but they also carry a
  self-referencing canonical pointing at the URL that 404'd.
- **Legacy aliases are hand-listed, not systematic.** `/contact-us` and `/stock/used-cars-in-holmfirth`
  resolved; `/part-exchange`, `/content/great-wall` and `/about-us` did not. Probe the outgoing
  site's real paths rather than assuming a prefix rule.
- **A real `/llms.txt` at the root** listing services and the correct live domain, and a developer
  **`/readme.md` answering 200** with the full internal file map.
- **`robots.txt` advertises `Allow: /` for every AI crawler by name** (GPTBot, ClaudeBot,
  PerplexityBot, Applebot, Bytespider) alongside the standard ones.
- The stale canonical base is still `http://{dealer}.platform-host:232/`, and this generation
  repeats it in `og:url` **and** both `og:image`/`twitter:image` — so a social share renders a broken
  image, which is a second finding under the same root cause. Check all four tags, not the canonical
  alone.

### Which generation is this build? Fingerprint it, then decide patch-or-port

When the question is "is this site on the old template?", do not guess from the design. Compare the
**asset layer and the routing** against a build you already know is current — the four tells below
separate the generations cleanly, and a build either has the current set or it does not:

| | Older generation | Current generation |
|---|---|---|
| CSS | theme file only (`greenblack.css` / `whitered.css`, ~14 KB of `!important` overrides) | one compiled `output.css`, ~34 KB, no overrides layer |
| Tailwind | `cdn.tailwindcss.com`, ~400 KB JS, 302 to a version path | compiled at build; no CDN reference |
| Unknown URL | 200 + homepage (soft-404) | genuine 404, distinct error page |
| Compliance layer | no analytics, no consent banner, no privacy page | GA4 + Consent Mode, banner, `/policies` linked |

The theme-file name is also the fingerprint that groups builds: two sites sharing a theme kit and a
soft-404 router are the same generation even when the colours differ, so a defect found on one
should be assumed on the other until checked (this is how the wrong-domain sitemap was traced to a
sibling site). The VDP title is a quick confirmation either way — `Vehicle Details - {Dealer}` on
every car is the older shape; `{Make} {Model} For Sale in {Town} | {Dealer}` is the current one.

**Recommend porting rather than patching when the gap is a generation.** Enumerate what the
current template already solves — compiled CSS, real 404s, consent, a policies page, sitemap and
canonical bases derived from the host, transactional VDP titles, offer schema — and count how many
open findings the port closes. On one build that was six of nine Highs and two of five Criticals,
which makes a per-item repair list the more expensive path. Say so explicitly in the report, with
the table, rather than leaving the reader to infer it.

### The newest generation is config-driven — and still hardcodes the dealer in ten files

A fourth shape now exists (a dealer `dealerA2`, Oct 2026), and it is the best base for a
port: `config.php` defines `SITE_URL`, `LIVE_DOMAIN`, `IS_STAGING`, `DEALER_COMPANY_NAME`,
`DEALER_COMPANY_NO`, GA4 id, phone and address; the footer renders the company number from those;
`IS_STAGING` blocks search engines until go-live; consent-gated GA4; `asset_version()` filemtime
cache-busting instead of a hand-typed `?v=1793193283`; a real `404.php`; a dynamic sitemap served
at `/sitemap.xml`; `llms.txt`; privacy **and** complaints policies; and an `.htaccess` with host
groups (PRODUCTION / LOCAL / LAN / PROXY) so only the live host gets scheme and host redirects.

**Do not trust the config layer to have been used everywhere.** In the same build the dealer's
identity is still hardcoded in ten files, and two of them are launch-blocking:

| File | Hardcoded | Consequence if cloned as-is |
|---|---|---|
| `sitemap.php` | `$base = 'https://www.<previous-dealer>.co.uk'` | the live sitemap lists another dealer's URLs — the exact defect that shipped on Moorside |
| `_sendenquiry.php` | `$_POST['dealeremail'] = 'info@<previous-dealer>…'` | **enquiries delivered to the wrong dealership, silently** |
| `robots.txt` | `Sitemap:` line | points crawlers at the previous domain |
| `llms.txt` | every URL and the email | wrong identity in the AI-facing file |
| `header.php` / `footer.php` / `functions.php` | social `sameAs` URLs | links to the previous dealer's Facebook/Instagram/TikTok |
| `.htaccess` | production host regex | the new domain never canonicalises |
| `config.example.php` | all dealer fields | only safe if the clone actually renames it to `config.php` and edits it |

So the pre-clone check is not "does a config exist" but `grep -rIn '<previous-domain>\|<previous-email>'
--include=*.php --include=.htaccess --include=*.txt .` — it must return nothing but the README.
Run it in both directions (old dealer out, new dealer in) before deploying, and add "sitemap host
count" and "form recipient" to the go-live checklist regardless of which template is used.

## SEO Fundamentals — Per-Build, Not Per-Platform

**Do not inherit the list below as expected absences.** the platform ships at least two SEO generations.
The older a dealer/a dealer builds were missing *all* eight items; the current generation gets
them all right — descriptive titles, populated meta descriptions, self-referencing canonicals,
Open Graph and Twitter Cards, a real `text/plain` robots.txt, a valid `sitemap.xml` with no dev
hosts, favicons and `AutoDealer` JSON-LD on every page. Reporting any of them as absent on such a
build is a false finding. Count each one per build (per-page head sweep below) and report only
what the bytes actually show:

1. **Meta descriptions** — zero across all pages. The `<head>` has title + robots meta only.
2. **Canonical tags** — none. Combined with HTTP/HTTPS duplicate content, every page exists twice.
3. **Open Graph / Twitter Card tags** — none. Social shares show bare links.
4. **robots.txt** — 404 on most builds. Not created by default.
5. **sitemap.xml** — either 404, or a **soft-404**: an HTML page returned with HTTP 200. Judge it by the body, not the status code. Where a real sitemap does exist it may contain dev URLs (see below).
6. **Favicon** — no `<link rel="icon">` in the `<head>`.
7. **Homepage title tag** — tends to be duplicative (e.g. "a dealer | a dealer") with no keyword or location.
8. **Homepage AutoDealer/LocalBusiness JSON-LD** — missing. VDPs DO have Vehicle schema (good), but homepage has no business schema for Local SEO.

## Feed-Level Data Quality Issues

These come from the platform stock feed, not the site template. Fix at source in the platform:

- **"HPI Cleaer" typo** — appears in every vehicle description. Should be "HPI Clear". Feed-level text, propagates to all VDPs.
- **Duplicate warranty phrase** — "3 month warranty included 3 months warranty" — the warranty statement appears twice in succession in the description template.
- **Missing colour spec** — 8 of 12 vehicles on the showroom listing had no colour displayed. Likely a feed mapping gap (colour data exists in the platform but isn't mapped to the listing template for some stock items).
- **Missing VDP spec fields** — Doors, CO2, Engine Size, Body Type not shown on VDP spec table. Only Year, Transmission, Fuel, Mileage, Colour, Service History, Interior Trim displayed. Service History and Interior Trim show "N/A".

## Finance / FCA Patterns

- **Monthly payment figure displayed without APR** — VDPs show "£135.33/month" next to cash price, but NO representative APR example, NO "subject to status", NO "credit broker not a lender" disclaimer. This is an FCA compliance issue (High severity).
- **"Apply for Finance" button** — links to `contact.php` (generic contact page), not a finance application form or third-party broker redirect. The privacy policy mentions redirecting to a third-party provider for finance applications, but the actual site doesn't do this.

## Security Header Patterns

- **Server/X-Powered-By headers leak versions** — "Apache/2.4.58 (Win64) OpenSSL/3.1.3 PHP/8.2.12" and "PHP/8.2.12" visible. Fix: `ServerTokens Prod`, `ServerSignature Off`, `expose_php = Off`.
- **Missing security headers** — X-Frame-Options, X-Content-Type-Options, Content-Security-Policy, Referrer-Policy all absent. HSTS IS present (good).
- **HTTP serves content without redirecting to HTTPS** — duplicate content. Fix: 301 redirect at server level.

## GDPR / Form Patterns

- **VDP enquiry form** — no GDPR consent checkbox (Name, Email, Phone, Message only)
- **Contact form** — no GDPR consent checkbox (Name, Phone, Email, Message)
- **Sell Your Car form** — DOES have acceptance checkbox with privacy policy link — the pattern exists in the platform but isn't applied consistently

### Other dealers' inventory inside the sitemap

Dev URLs are the common case, but a platform `sitemap.xml` can carry **an entirely
different dealership's stock list** — the template/demo build's inventory, not this
dealer's. a dealer Teesside (a sub-£15k used-car forecourt, live stock £2,490–£14,990)
shipped a sitemap whose 88 `<loc>` entries listed Porsche 911s, Bentley Continentals,
Ferraris, a McLaren 720S and a Rolls-Royce Spectre, and whose URL scheme
(`/car/{make}-{model}-{year}/{id}`) did not match the live scheme (`/car/{id}/{slug}`).

**Check the HOST of every `<loc>` first — that is the cheaper half and it is the one that
ships.** A sitemap can be perfectly valid, correctly typed `application/xml`, served 200, and
have **every single entry on a different dealership's domain** — not a demo inventory, the whole
file generated from another client's base URL. Count the hosts before reading a single path:

```python
from urllib.parse import urlparse
from collections import Counter
locs = re.findall(r"<loc>([^<]+)</loc>", body)
print(Counter(urlparse(u).netloc for u in locs))   # one key, not this site = Critical
```

Zero occurrences of the site's own hostname in its own sitemap is the finding; the inventory
check below is the second question, not the first. Because the base URL is baked into the
generator, this is a **template-generation defect, not a typo**: assume every sibling build on
the same generation has it and check them the same day. It survives go-live, so re-run the host
count on the **live** domain as a post-launch item — a sitemap fault found pre-launch and not
fixed will be sitting there afterwards, still valid, still typed correctly, still wrong.

Have the fix key off the site's own host (`$_SERVER['HTTP_HOST']` or the site config) rather
than a constant, and gate the build on "no `<loc>` outside this host".

Then sanity-check the *inventory inside the sitemap* against the live listing page. A sitemap
that is syntactically valid, returns 200 and is `application/xml` can still be naming a
competitor's stock as this site's canonical URLs. Cross-check the price band and the make mix
against `/cars`.

### Apex and www both serve the build, each self-canonicalising

Do not assume apex 301s to www. On a dealer (Sep 2026) both
`https://<dealer-domain>/` and `https://www.<dealer-domain>/` returned **200** with an
8-byte-apart body, the only difference being the canonical: each host declared *itself*
canonical. Every page therefore existed twice with no consolidation signal. Test with:

```bash
curl -sSI -A "$UA" https://{domain}/           # look for 301/308, NOT 200
curl -sS  -A "$UA" https://{domain}/      | grep -o 'rel="canonical" href="[^"]*"'
curl -sS  -A "$UA" https://www.{domain}/ | grep -o 'rel="canonical" href="[^"]*"'
```

### Extension-less and `.php` variants — probe the pair, a 301 is the pass

On older builds the platform answered `/about` **and** `/about.php` (likewise `/finance`,
`/privacy-policy.php`) with HTTP 200, and the `.php` copy declared *itself* canonical — two
indexable copies of every static page. The current generation instead **301s** `/about.php`
to `/about`, and `http://` to `https://`, which is correct. So request the pair and read the
status before writing the finding: two 200s self-canonicalising is the duplicate-content
finding, a 301 is a pass. Either way check the canonical of each variant, not just that the
page loads.

### Soft-404 on unknown paths — test it, it is a per-build setting

Older live the platform builds return the homepage with **HTTP 200** for any unknown path
(`/whatevs.php`, `/terms`, `/this-page-does-not-exist`), while a malformed-but-recognised
route (`/car/999999/nonexistent`) does return a clean 404. A status-code sweep therefore
reports every internal link as healthy. The current generation returns genuine 404s — a
distinct ~28 KB error page for every unknown path. Distinguish either way **by body size**
against the homepage, or by md5: same bytes as `/` = soft-404. Where the 404 page is real,
check one thing more — that it does not carry a `rel="canonical"` pointing at the URL that
just 404'd, which hands search engines a canonical for a page that does not exist.

### `robots.txt` served as the homepage

The common the platform shape is not a 404 but a **200 with `content-type: text/html`** and the
homepage as the body. Confirm with `content-type` and a `Disallow` grep, never the status:

```bash
curl -sS -D - -o /tmp/r.txt -A "$UA" https://{domain}/robots.txt | grep -i content-type
grep -c Disallow /tmp/r.txt   # 0 + text/html body = no robots.txt exists
```

### A real `robots.txt` is a map of the build's junk files — probe every `Disallow`

The current generation ships a genuine `text/plain` robots.txt, so it passes the check above and
reads as a win. Read the **Disallow list** before accepting it: it enumerates the template's
development and debug scripts, which makes it simultaneously an information-disclosure artefact
and a ready-made probe list — and those files sit publicly at the site root. One build's list
named `test.php`, `test-car.php`, `stock-debug.php`, `debug-rewrite.php`, `gencars.php`,
`car2.php`, `vehicleT5.php`, `car - Copy.php`, `content.json`, `config.php`, `_captcha.php`,
`_codeweavers.php`, `_financecalc.php`, `_sendenquiry.php`, `admin.php`, `package.json` and the
dotfiles. Status-check the whole list, then read what the 200s expose:

| Path | What it exposes |
|---|---|
| `/stock-debug.php` | the platform **dealer ID**, the `StockExportJSON.php` API endpoint, the absolute `public_html` path, and the stock cache filenames + hashes |
| `/debug-rewrite.php` | `SCRIPT_FILENAME` — the absolute server path |
| `/content.json` | the entire site copy source (hero, about, reviews blocks) |
| `/test-car.php` | stock internals — total vehicle count and the first five makes |
| `/package.json` | the build system: app name, the Tailwind build scripts, devDependencies |
| `/admin.php` | a live admin **login form**, with no CSRF token in the markup |
| `/gencars.php` | a **write** endpoint — it regenerates the stock cache and answers `file written` |

Two outrank the rest, so lead the cluster with them: `gencars.php` is a state-changing endpoint
any anonymous visitor can hit, and `stock-debug.php` hands over the dealer ID and API URL needed
to pull the stock feed directly. The fix is one server-level rule — deny these paths, then
**delete them from `robots.txt`**, because advertising a path invites the request rather than
preventing it. Also strip `x-powered-by`, `server`, `platform` and `panel`: they fingerprint the
PHP version and the host.

The probe generalises — treat every `Disallow:` entry on any build as a filename that exists, and
test it. This is usually the highest-severity cluster on a build whose SEO head-layer is otherwise
correct, so it can change the report's headline.

### VDP spec fields — render the page before calling anything blank

The VDP is **JavaScript-driven**: the body ships empty containers and the page's JS fetches the
vehicle from the platform API and paints the spec grid at runtime. On the current generation a
`curl` of a healthy VDP therefore shows *every* label with an empty value node, and a raw-HTML
sweep reads that as "all spec fields blank" — a false finding on all counts. One build read
`Year => ''`, `Mileage => ''`, `Transmission => ''`, `Colour => ''`, `Service History => ''`,
and every one of them populated correctly in a browser: Year 2017, Mileage 86,654 mi,
Transmission Automatic, Fuel Diesel, Colour Daytona Grey, Service History Full, Interior Trim
Black Half Leather.

**Never file a blank-spec, missing-H1, missing-price or empty-listing finding from `curl` output
alone.** Load the page in a real browser and read `document.body.innerText` first; JS-rendered
VDPs and listing pages are the default case here, so absence findings from raw HTML are false
findings. The same applies to spec values sitting behind a tab or accordion — they may need a
click to render at all.

What *is* a real finding is a field the browser render **also** lacks. The grid carries Year,
Transmission, Fuel, Mileage, Colour, Service History and Interior Trim while **Doors, Engine
Size, CO2, Body Type and Seats are absent from the template** even though the feed data is present
in the description text ("2.0 TDI", "SUV 5dr", "Euro 6"). Read the value node in the render, not
the label.

Genuinely blank fields do occur on the older generation — `Year` rendered empty on every VDP
(`>Year</p><p ...></p`), so the spec grid showed a labelled tile with no value at all. Vehicles
whose feed rows lack make/model ship as slug `manual-{colour}-cars-for-sale-in-teesside` with an
**empty H1** and blank Make/Model tiles (4 of 27 on a dealer). Count these off the listing page:
any `/car/{id}/` slug matching `^(manual|automatic)-` has no make or model.

Also check the engine-size segment of the slug — a truncated value (`mercedes-s-class-automatic-3`
for a 3.0-litre) means the cc field is being coerced, not mapped.

### Listing, filter and footer counts drift from the live stock

Counts are typed into templates independently of the feed, so they go stale silently. Three
comparisons, each cheap, each a finding when they disagree:

- **The footer's make list against the rendered per-make counts.** One build's "Browse Cars by
  Make" block totalled 13 cars against 18 actually listed — BMW showed 2 (actual 3) and
  Volkswagen 1 (actual 3) — and **two makes in stock, Hyundai and Peugeot, had no footer link at
  all**, so those vehicles were reachable only through the full stock page. Get the real numbers by
  rendering `/cars?make=<make>` for every make and counting distinct `a[href*="/car/"]`; the
  footer list is usually hard-coded, so a make appearing in stock for the first time never gets a
  link.
- **Any "N cars" or price-range claim against the listings** — same battery as
  `references/platform-data-integrity-checks.md`.
- **The sitemap's vehicle set against what returns 200, and against the feed's own count.** A
  the platform sitemap can be generated from a cache that still holds unavailable stock, so it emits
  URLs that 404 — and the feed's debug output is the tell, reporting e.g. `Total Vehicles 18,
  Available 13` while the sitemap carries 18. Fix the generator, not just the one line.
- **The sitemap's static set against the site's own navigation — a page built after the generator was
  written is linked in the nav and absent from the sitemap.** `grep -c '<new-page>' sitemap.xml`
  returns 0 on the staging *and* the live host, because one generator emitted both. A newly added
  reviews/testimonials page is the usual case: it is the page everyone is watching, and its
  discoverability is still only the nav.

### Make-filter pages cannot rank, yet canonicalising them is still correct

Every `?make=` filter returning one generic title and H1 means **no make-level page exists**, so
nothing can rank for "Audi for sale {town}". Two things are true at once and the recommendation
has to hold both: canonicalising each filter to `/cars` is the **right** duplicate-content
handling and should be left alone, *and* it is precisely what stops a filtered view being a
landing page. So the fix is not to un-canonicalise or index the filters — it is to build real
category pages at static paths (`/used-cars/audi`) with a transactional title and H1 carrying the
town, a short unique intro and the filtered stock, leaving the `?make=` canonicals as they are.
This is usually the largest organic gap on an otherwise well-built site, because make-plus-town is
the highest-intent query a forecourt has.

### The FCA disclosure page carrying privacy-policy copy

The `/fca-disclosure.php` page opened with verbatim privacy-policy text ("The purpose of this
policy is to outline how we use your data… This Privacy Policy will cover all aspects of this
business.") above the genuinely FCA content, and ran ~2x the length of `/privacy-policy.php`.
A disclosure page *existing* proves nothing — read its first screen and compare it to the
privacy page.

### APR on the VDPs contradicting the representative example

VDPs quoted `From £63.73/month (48mo HP @ 11% APR)` on every car while `/finance` carried a
representative example at **Representative APR 15.6%**. Two different APRs for the same product
offered by the same firm is a compliance finding, not a copy nit. Grep every APR value on the
site and reconcile them. Note also that the per-car monthly figure needs "subject to status"
and a representative example in reach of the quote, not only on a separate page.

**When the confirmed rate is not yet available, remove the site's own APR claim rather than leave it
standing.** A figure described as *representative* is a defined term: it cannot stay on the page
unverified while the lender's module on the same page shows a different one. Replace it with wording
that survives confirmation — "ask for a personalised quotation and a representative example", or "a
representative example is available on request" — and restore the figure in one edit when it lands
(two files: the homepage content include and the finance page). Removing a regulated claim is a safe
unilateral fix; inventing or guessing its replacement is not.

**A "rates from X%" line and a "representative APR of Y%" are not automatically a contradiction.**
They are different figures and both are legitimate in one module: the first is the best case offered,
the second is the rate a defined share of customers actually get. Only flag them when the *site's own
copy* asserts a representative rate that disagrees with the module's representative example.

### Brand-name and address drift

One build rendered the business as `a dealer`, `the dealer` and `the dealer` across title tags,
body and footer, and the registered address three ways — footer "7 Stephenson Street, <town>,
<town>", `/fca-disclosure.php` "7 Stephenson Street, Stockton on Tees" (no <town>),
and schema `streetAddress: "the dealer"` with `addressLocality: "<town>"`
(two localities comma-joined, no space). Legal name for FCA copy must match Companies House
(`MOTOR PLUG TEESSIDE LIMITED`).

**The privacy policy and the About page carry their own address strings, and those are the ones that
drift.** The site-wide footer is usually right; the registered-office block inside `/privacy.php`
("X is the trading name of X whose registered office is at: …") and an About-page `Location:` line are
inherited copy that survives the rebuild. On one build both stated `5 Chancellor Street, Woodhouse,
Leeds LS26 2TE` while the footer, Companies House and every directory said `Unit 4, 10 Chancellor
Street, Leeds LS6 2TE` — a wrong street number *and* a wrong postcode (`LS26` is a different district
from `LS6`), with the company number absent from the site entirely. So grep **every** page for the
address tokens and the postcode, not just the footer, and read the register: a **recently changed
registered office** (check the filing history) is the usual reason the site's copy is stale. Read the
whole block too — the same one called the company "the trading name of <its own name>" and left an
empty `( )` where the data-protection email belonged.

### The FCA disclosure block is a bare paragraph, not a `<footer>` element

Grep for the **wording**, never for `<footer>`. On the current generation the whole compliance
statement sits as an unmarked paragraph slotted between the modal JavaScript and the footer
markup, so a `<footer>…</footer>` extraction returns nothing and the page looks like it carries no
company details at all — and a site-wide "is the FCA statement present?" check written against the
footer fails on every page. Search the rendered text for `authorised and regulated` and
`credit broker, not a lender`.

That one sentence carries three separate facts, each verifiable only against an external register:
the **legal entity name** and the **company number** against Companies House, and the **FRN**
against the FCA register — a trading name has no FRN of its own, so the number must belong to the
entity named in the block. A block that is present *and* correctly worded can still name the wrong
entity, and that is a compliance priority rather than a copy error (see `dsc-fca-compliance`).
Also record where the block renders: if it appears only on the homepage and the finance page,
every other page carries no company details.

### Opening hours disagreeing three ways

a dealer's About page carried two different sets on the one page ("Monday – Friday 10:00am –
5:30pm / Saturday 9:00am – 3:00pm / Sundays Closed" beside "Mon – Sat: 10:00am – 6:00pm /
Sun: 10:30am – 4:00pm") and the Contact page a third ("Monday – Friday: 9am – 6pm / Saturday:
9am – 5pm"). Grep every page for hour patterns and diff them — and then against the GBP.

### Front-end build artefacts shipped to production

Watch the **CSS engine**, not just the head tags. The a dealer build carried
`<script src="https://cdn.tailwindcss.com"></script>` plus an inline `tailwind.config` on all
22 pages — Tailwind's **Play CDN**, a development-only build that ships the entire framework and
compiles styles in the browser at runtime. Render-blocking, dependent on a third party the client
does not control, and the site is unstyled if that CDN is blocked. Compile the CSS at build time
into `/assets/css/` and drop the script.

Check the stylesheet basename too: `/assets/css/blackorange.css` is the *template theme's* name,
visible to anyone who views source. Grep the saved HTML for `tailwindcss`, `cdn.`, `unpkg`,
`jsdelivr` and the stylesheet basename before writing a performance verdict — these are build-layer
defects for the developer handover, not the client list. Note the framework varies by build
(the template build shipped Bootstrap + jQuery, a dealer Tailwind), so identify it per site rather than
assuming. On the current generation the public pages are genuinely clean — Tailwind is compiled at
build time into `/public/assets/css/style.css` by a `package.json` script — while `/admin.php`
still pulls the **Play CDN** plus Bootstrap and Summernote from jsDelivr and cdnjs. Fetch the
non-public endpoints too before declaring the front end clean.

### The the platform build now also ships on third-party hosting — fingerprint before assuming staging

The newest shape is a **live** the platform site on **Hostinger** (not `{dealer}.platform-host`), so none of the
staging assumptions apply. Tell:

- `package.json` at the web root answers 200 with `"name": "platform-motors-php"` and the Tailwind build scripts.
- Response headers carry `platform: hostinger`, `panel: hpanel`, `server: hcdn` (and `x-powered-by: PHP/8.3.33`).
- `/public/assets/css/style.css` returns a **real compiled stylesheet** (`text/css`, tens of KB) while the
  pages link nothing — they run the **Play CDN** instead. So the Play CDN finding arrives with its own fix
  already on the server: link the compiled file and drop the CDN script. Check that path by name; on the
  older builds the equivalent lookup is `assets/css/site.css`.

### The `/` build path is hand-listed and *excludes* `robots.txt` — probe the junk names by hand

`robots.txt` may legitimately not exist (a soft-404), which removes the usual `Disallow:` harvest — but the
debug files are still there. Probe the platform's known names directly rather than waiting for a Disallow
list to nominate them. On this build the result was a **live 85 KB `/stock-debug.php`** and a live
`/_financecalc.php`, while `test.php`, `gencars.php`, `debug-rewrite.php`, `content.json`, `admin.php`,
`cars.php` and friends merely soft-404'd to the homepage.

Two of those are their own class:

- **`/stock-debug.php` chains into the stock API.** It publishes the platform **dealer ID**, the
  `StockExportJSON.php` endpoint, the server's stock-cache filenames, and a **full raw vehicle record
  including the VIN and engine number** (`vin: ZFA…`, `engineno: …`, `regno`, `stid`). The dealer ID it
  leaks is the only credential the feed needs — so the debug page and the unauthenticated
  `StockExportJSON.php?did=<id>&website=1` are one finding split in two. Report them separately (different
  owners: host vs the platform) but say explicitly that the first publishes the input the second consumes.
- **A standalone `_financecalc.php` is a public finance tool with a hard-coded APR** (`const apr = 9.9;`,
  term slider defaulting to an odd 37 months), printing a bare monthly figure with **no representative
  example, no "subject to status" and no credit broker named**. Grep any `_*.php` the platform exposes for
  an `APR` literal and reconcile it against every other rate on the estate — this build carried **four**
  (9.9% calculator / 8.9–16.9% in the platform finance iframe / APR 11 in the stock feed / none on `/finance`)
  and named **two** credit brokers (the dealer on its own `/finance`, "the platform Finance" inside the iframe).

A `200` with a **0-byte body** (`config.php`, `_captcha.php`) means the file exists and ran without output —
record it as reassurance, not as a leak, unless the PHP handler can be made to fail. **A non-zero body is the
opposite, and a form handler is where it hides.** A `_*.php` POST endpoint asked with a bare **GET** can answer
200 with a `print_r` of the server's own variables — one build's `_sendenquiry.php` returned
`hereArray([did] => <the platform dealer id>, [dealeremail] => …, [clientip] => 192.168.1.x, [soe] => …, [host] => …)`,
i.e. the dealer ID the stock API is keyed on plus an internal address. Request every `_*.php` handler the build
references with **both** GET and a harmless POST and read the bytes; the paths named in `robots.txt` are a
starting list, not the whole exposure surface.

### A soft-404 can carry a canonical — and that is worse than the plain soft-404

Confirmed on this build: unknown paths return the homepage with HTTP 200 **and the head rewritten to claim
the requested, non-existent URL as canonical and as `og:url`**. A `rel="canonical"` for a page that does
not exist is the defect to report, not the 200. It is also invisible to a body-size check, because the body
*is* the homepage — so when md5s differ slightly between `/` and a junk path, **diff the two responses** and
read what changed. Here the canonical and `og:url` were the **only** differences; the size delta alone
(16–20 bytes) is not enough to conclude "soft-404, same body".

### The finance CTA and the finance modal can be wired to opposite halves of the feature

Two independent parts have to meet: a control with `id="applyFinanceBtn"`, and a listener script that looks
it up and unhides `#financeModal` (an iframe to the platform's finance app). Check them as a **pair**:

- Is `id="applyFinanceBtn"` present in the rendered markup of any page? (`grep -l` across every saved page.)
- Do the listener scripts load on the page where it exists?

On this build the button existed **only on the orphan calculator page**, the listeners **only on the main
template pages** — and the visible "Apply for Finance" CTA was wired to the *contact* modal instead. So the
finance application was unreachable while the page looked complete. A CTA labelled "Apply for Finance"
opening a generic contact form is the finding; the dead JS is only Low.

### Checklist additions for this generation

- Diff `/` against an unknown path — do not stop at the status code or the byte count.
- Probe `stock-debug.php` and `_financecalc.php` by name; read what a 200 actually contains.
- Check `/public/assets/css/style.css` by name and confirm whether the pages link it.
- Check `id="applyFinanceBtn"` presence *and* listener co-location.
- Grep every exposed page for an `APR` literal and list every rate on the estate side by side.

## Fleet-wide passes belong in `dealer-estate-inventory.md`

When the job is the whole server rather than one site — "list every dealer site", "what is on the platform owner's
box", an estate-wide defect count — the population, the classification buckets, the mixed-generation
sampling and the review document's shape are all in `references/dealer-estate-inventory.md`. This file
stays about what one build does; do not restate the fleet procedure here.

The one thing worth repeating where you are already reading per-site patterns: **a sample of a handful of
vehicle pages cannot clear a feed-driven defect.** Six VDPs showed zero encoding faults on a site whose
full-stock pass found 42 of 62 affected — the sample drew clean cars. Loop the whole stock for feed
defects, and label everything else as sampled.

## What the platform Gets Right

- **Vehicle JSON-LD schema** — comprehensive Vehicle type with manufacturer, model, bodyType, color, fuelType, vehicleTransmission, productionDate, mileageFromOdometer, and Offer with price/currency/availability/AutoDealer seller. Well structured. **But do not assume it ships — it is a per-build setting.** The the template build build (Sep 2026) had ZERO JSON-LD on all 15 templates and all 6 VDPs, no canonical and no OG tags, i.e. none of the "what the platform gets right" items. Always count `application/ld+json` per page rather than trusting this list.
- **Image alt text** — all stock images have descriptive alt text (make + model)
- **Responsive CSS** — 24 media queries covering 320px to 1380px, hamburger menu, prefers-reduced-motion
- **Google Maps embed** — correctly configured on contact page
- **H1 hierarchy** — one H1 per page, clean structure
- **Microdata** — SiteNavigationElement and WebPage itemtypes used (though JSON-LD is better for VDPs)

## Audit Technique for the platform Sites

Use `curl -sL` for raw HTML extraction — you need the full `<head>` section (meta tags, canonicals, OG tags, JSON-LD) which `web_extract` does not return in full. Fetch:
1. Homepage (`index.php` or `/`)
2. Showroom (`vehicles.php`)
3. At least 2 VDPs (`vehicle.php?id={hash}`) — check feed-level issues across multiple vehicles
4. All static pages (`about.php`, `contact.php`, `warranty.php`, `sell.php`, `privacy.php`)
5. `robots.txt` and `sitemap.xml` at root
6. HTTP version of homepage (check for HTTPS redirect)
7. `assets/css/site.css` (check media queries, responsive framework)

## Pre-launch staging batch (sites queued to go live)

DSC routinely receives a batch of the platform builds at once, days from launch on
`{dealer}.platform-host` and still ahead of the domain move. Every item below
is a launch blocker and every one of them is invisible to a status-code-only pass.

### Establish the launch dates before you write anything

The priority order for a pre-launch batch comes from the **launch dates**, not from
finding severity, and the two orders can invert: the build that reads as most urgent
(notice served, domain move requested) can be months from go-live, while a site nine
days out carries the same gaps and needs them fixed now. Get the dates first.

- **Where the comms live:** mail addressed to `paul@sales-consultants.com` arrives in
  the **marketing** himalaya account (`paul@onlinewebstudio.co.uk`) — there is no
  himalaya account for `sales-consultants.com` itself. the client coordinator writes from
  `<coordinator-email>` as well as `<coordinator-email>`, and the platform owner
  from `<platform-owner>@<platform-host>`; the site-status threads usually cc all three.
- **Search by field, not free text:** a bare-word himalaya envelope search (e.g. a
  dealer name) can silently return an empty table, which reads as "no such mail"
  rather than "bad query". Use `"subject <word>"` / `"from <address>"`, or list a page
  of envelopes and grep it for the senders, then read messages by ID.
- **`envelope list` takes no query, and options must precede the query.** Filtering is
  `himalaya envelope search`, not `envelope list -q` (there is no `-q`; it errors
  `unexpected argument`), and the query is the **trailing positional**, so any option
  placed after it is swallowed into the query and fails with `cannot parse search
  emails query`. Put `-a <acct>` and `--page-size N` first: `himalaya envelope search
  -a <mail-account> --page-size 10 "from <dealer-domain>"`. The DSL is `from|to|subject|body
  <pattern>`, `date|after <yyyy-mm-dd>`, `flag <seen|answered|flagged|draft>`, combined
  with `and`/`or`/`not`, sorting with `order by date|from|to|subject`.
- **A supplier's address in an old thread is not their address now.** the client coordinator alone
  appears across `<coordinator-email>`, `<coordinator-email>` and
  `<coordinator-email>`; build agencies answer from a **support desk**
  (`support@<dealer-domain>`) with `Re:[## <ref> ##]` ticket tags rather than from an
  individual. Re-search for the address you are about to write to instead of reusing
  the one in the message you happen to be reading.
- **The latest status message supersedes the handover.** A later "status" email
  routinely corrects go-live dates, and it can add a site that was never in the
  original batch brief. Re-read the thread rather than working from the brief alone.
- **Capture go-live prerequisites alongside the dates** — which provider holds the
  domain / IPS tag, the live domain the staging build replaces, and any third-party
  link still outstanding (finance provider, stock feed). These are what actually
  block a go-live, and they come out of the same thread.
- **Report both orders.** Lead with the launch-date order for what to fix first, and
  keep severity inside each site's findings; put the date and its source on every row
  so the client can see why the order is what it is.

### Batch procedure

One pass per site, then aggregate — do not interleave the sites:

1. Fetch homepage + 4–5 key pages + `robots.txt` + all three sitemap candidates
   (`/sitemap.xml`, `/sitemap_index.xml`, `/wp-sitemap.xml`) into
   `~/Documents/<project>/<batch>/<site>/`.
2. Parse every homepage in ONE script: title, meta description, canonical, meta
   robots, H1 count, OG/Twitter count, JSON-LD count, SEO-plugin signals, image alt
   coverage, privacy / cookie-consent / company-number signals.
3. Status-check every internal href (see the extraction trap below).
4. Sweep the inner pages for title/meta/canonical/H1 — homepage-only checks miss
   duplicate titles and missing canonicals on inner pages.
5. Write the report as a **cross-site status table + one cross-cutting findings
   section + per-site findings**, rather than repeating the same pattern five times.

### Stale build artefacts that ship by default

- **Dev URLs inside sitemap.xml.** All `<loc>` entries pointing at
  `http://127.0.0.1:81:81/client-site/dealer-sites/template1/v2/...` — the local build
  server, doubled port. The file is valid XML and returns 200, so nothing flags it.
  Grep the sitemap for `127.0.0.1`, `localhost` and `:81` before launch: submitting it
  tells Google that every page's canonical home is an unreachable localhost address.
- **Canonical carrying the staging host and a build port**, e.g.
  `http://{dealer}.platform-host:232/` on every page. Tell-tale: the site's own
  `robots.txt`/sitemap already name the correct live domain, so the right value is
  configured somewhere and only the canonical base is stale.
- **Absolute staging links in the body** on the same host+port.

### Indexability — check this first

A staging host must not be indexable while the real site is still up, or the two
compete as duplicate content and the staging URLs can outrank the live domain:

```bash
curl -sI -A "$UA" https://{dealer}.platform-host/ | grep -i x-robots
```

An absent `meta robots` tag IS the finding (absent = indexable by default) — do not
score it as a pass. No `noindex` on any page + no `robots.txt` = Critical. Add
`noindex, nofollow` now, and make removing it a line on each go-live checklist.

### The staging host is not the launch host

`{dealer}.platform-host` resolves to the **developer's own dev machine**, not to the server
the site will launch on. Live sites go to a separate shared host (given as a bare IP when a
build is signed off) and the build is uploaded there on approval. Three consequences:

- The staging host **can stop responding at any moment** — a reboot, a shut laptop. A failed
  fetch mid-audit is not a finding about the site; re-fetch before recording it.
- **Every fix verified on the staging URL has to be re-verified on the launch host after the
  upload.** A build port, a stale canonical base and a dev sitemap all survive the copy; the
  domain does not. Write the post-upload recheck as its own pass in the report.
- When the launch host is named as a bare IP, record it — it is what the domain will be
  pointed at, and it is the address to re-test against before calling go-live.

### Link styles are NOT uniform across a batch

Builds in the same batch used four different shapes — root-relative (`/about.php`),
extension-less (`/about`, `/cars`), bare relative (`about.php`, `stock.php`,
`vehicle.php?id=…`) and path-slug (`/car/{id}/{slug}`). Do not assume one build's
template matches the next, and check sitemap presence per build.

**Extraction trap:** a regex anchored on `href="/` silently returns ZERO internal
paths on a bare-relative build, which reads as "this site has no internal links"
rather than "my pattern missed". Match every href first, then drop assets:

```python
paths = sorted(set(re.findall(r'href=["\']([^"\'#?]+)', raw)))
paths = [p for p in paths if not re.search(r'\.(png|jpe?g|svg|ico|css|js|webp|gif|woff2?|xml|txt|webmanifest|pdf)$', p, re.I)]
```

Prepend `/` to anything not already starting with `http` or `/` before status-checking
it — otherwise host + `stock.php` concatenates into an invalid URL and every check
reports a false failure.

### Compliance gaps that recur across a batch

- **Privacy policy absent, not merely unlinked** — separate the two failure modes, because a
  build can fail the harder one. Grep every page for `href="[^"]*privacy` *and* status-check the
  likely slugs (`/privacy-policy`, `/privacy`, `/privacy-policy.php`). One build ran enquiry forms
  collecting name, phone and email with **no privacy notice anywhere in the HTML and no privacy
  page at all** — both slugs 404. Collecting personal data through forms without a reachable
  notice is Critical, not a copy nit; and a policies page existing (e.g. `/policies`) is not the
  same as it being linked.
- **No cookie-consent platform** (scan for `cookieyes|complianz|cookiebot|onetrust|termly`) — but
  establish whether any trackers are actually running before writing the finding. A build with
  **zero** analytics (no `gtag`, `googletagmanager` or GA id anywhere) has a different and smaller
  problem from one running GA4 with no banner: the first is a measurement gap, the second is a
  consent breach. Check, then say which you found rather than assuming the analytics are there.
- **No company number / registered office in the footer** — a Companies Act display
  requirement for Ltd companies. Only some builds carry the registered line.
- **FCA wording varies per build** — one build can ship an `/fca-disclosure.php` and
  still omit "credit broker, not a lender" and "subject to status" from the homepage.
  A disclosure page existing is not compliant copy; run the `dsc-fca-compliance` pass
  regardless.
- **The disclosure block ships with unfilled placeholders.** The template's Financial
  Disclosure block goes live still reading `Company No. [Company No.]` and `FCA No. [FCA No.]`,
  and it renders on the disclosure page only rather than in the shared footer — so every other
  page carries no company details at all. Grep the rendered text of every page for a
  bracketed placeholder; a checklist item reading "FCA statement present" passes while the
  Critical sits underneath it.

### What is usually fine (say so explicitly)

Titles, meta descriptions, H1s and internal link integrity are typically solid on
the platform builds, and encoding is clean (zero U+FFFD, no mojibake). Lead the report with
what passed — the gaps above are a build-layer problem, not a content problem.
