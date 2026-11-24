# the platform pre-launch: defects that survive the standard sweep

Patterns found on the dealer Motors (`<dealer>.platform-host`, Sep 2026) that the usual head-layer and
status-code checks report as passes. Run these on every platform build in a pre-launch batch — each
one scored "correct" on a build whose titles, canonicals, OG tags and encoding were all fine.

## 1. The sitemap can be wrong twice over — probe a URL, never just the host

the dealer's sitemap had **88 `<loc>` entries on `http://127.0.0.1:81:81`** (the known finding) *and* used
the wrong URL scheme: `/car/{make-model-year}/{id}` against a live site that serves
`/car/{id}/{long-slug}`. **All 83 vehicle URLs returned 404.** Fixing only the host would have
shipped 83 dead URLs and looked like a fix.

```bash
# after grepping the sitemap for the dev host, always fetch one vehicle URL from it
p=$(grep -o '<loc>[^<]*</loc>' sitemap.xml | sed -n '6p' | sed 's/<[^>]*>//g' | sed 's|.*template1/v2||')
curl -s -o /dev/null -w '%{http_code}\n' -A "$UA" "$SITE$p"      # expect 404 on this build
```

Also reconcile the sitemap against the crawled inventory in both directions: the dealer listed 5 static
pages and **omitted 13 live ones** (`/cars`, `/contact`, `/servicing`, `/mot`, `/body-repairs`,
`/aircon`, `/tyres`, `/diagnostics`, `/sell-your-car`, `/enquiry`, `/privacy-policy`,
`/fca-disclosure`, `/vehicles`).

## 2. Test the site's primary call to action as a page, not a link

Every the dealer page linked **"Book a Service" 324 times**, and the target `/bookservice.php` read
*"Service Booking Module to be added here!"* with **no `<form>` on it at all**. A link that
resolves to 200 passes every link check. Grep every CTA target for unfinished markers:

```bash
grep -oiE "to be added|coming soon|TBC|TODO|lorem ipsum" page.html
```

Signals to pair with it: a target page with **zero `<form>` elements**, a page name no other page
uses (`bookservice.php` when everything else is extension-less), and a title tag borrowed from a
different page.

## 3. `?page=N` beyond the last page is not clamped by the framework

41 vehicles over 2 pages: pages 3–6 served page 2's content with **HTTP 200** while the widget
rewrote itself to "Page 2 of 2". Compare **id sets**, not byte sizes — the md5 differs between
clamped pages because of a token, so identical-size is not a proof. `set(p3_ids) == set(p2_ids)` is.

## 4. A second stock page, not just the `.php` twin

Beyond the extension-less/`.php` pairs, the dealer served **`/cars` and `/vehicles`** — the same 27
vehicles under "Our Car Collection" and "Our Vehicle Collection", both self-canonicalising. Diff
the id sets of any two candidate listing URLs before assuming one is an alias.

Note the current platform generation does **not** 301 `.php` to extension-less: the dealer returned
200 self-canonicalising on both forms of five pages (`/about`, `/contact`, `/`, `/fca-disclosure`,
`/privacy-policy`). Probe the pair per build rather than inheriting the 301 expectation.

## 5. `_financecalc.php` and friends are the exposure cluster — probe the guesses

On the dealer the 200s were `/gencars.php` (a **write** endpoint that deletes its own guards: it executed,
answered `file written` and leaked `E:\<user>\SVN\client-sites\dealer-site\…`),
`/stock-debug.php` (the platform **dealer ID** + the stock API URL **with its key in clear text**),
`/debug-rewrite.php` (SCRIPT_FILENAME), `/content.json` (all site copy, including the template's
placeholder testimonials), `/test-car.php` (`Total cars: N` + the first five vehicles),
`/admin.php` (login form, no CSRF token), `/_financecalc.php` (PHP warnings + absolute path ×5),
`/package.json` and `/readme.md`. `/config.php`, `/_captcha.php` and `/_sendenquiry.php` answered
200 with empty bodies — they execute rather than being blocked. Also watch for a `readme.md`
describing a **different stack** (the dealer's documented a Next.js/React build on a PHP site).

## 6. Verify the FRN against a mirror, then say you could not confirm it

`register.fca.org.uk` is a JavaScript app and its API returns
`{"Success":"false", … "Missing Headers."}` to a keyless request, so the register cannot be read
directly. **`firmchecker.co.uk/firm/<FRN>`** renders server-side and returns the status in text —
on the dealer, FRN 658713 came back **"No longer authorised … the record is closed"** for a build whose
disclosure block read "authorised and regulated … FRN: [FCA No.]".

Report it as **flagged for confirmation on the official register or the client's IDD**, never as
established fact: a mirror is a secondary source, and this is a regulatory claim. Pair it with the
unfilled `[FCA No.]` / `[Company No.]` placeholders, which is what makes the finding concrete —
check the *rendered text* of every page for bracketed tokens, since a checklist item saying
"FCA statement present" passes while the placeholder sits underneath it.

## 7. Read the outgoing site's nav for the regression list

The outgoing `dealer-site.co.uk` published **two trading addresses** — car sales at Park Road,
Thackley BD10 0RR and servicing/MOT at New Mill, Cross Road, Idle BD10 9RU. The rebuild carried
only the first, while selling MOT and servicing off a "Book a Service" CTA. Grep the mirrored
pages for each old address token (`BD10 9RU`, `Cross Road`, `Idle`, `New Mill`): one hit confined
to the archived old-site copy is the finding.

Its `sitemap.xml` was a valid 9-URL list, giving the full redirect map for free. It also carried
`Template-Do-Not-Delete` in a page name and `cloudwebagency.com` in the footer — record the
outgoing agency, it names who to ask for the DNS and analytics history.

## 8. Hours and phone: grep, then diff per page

the dealer published **four** conflicting weekday closures (footer 6pm ×20 pages, `/about` 5:30pm,
`/contact` 6pm, `/bookservice.php` 5:30pm) and the Saturday opening vanished on three of them.
A regex for `(Mon|Tue|…)[a-z]*\s*[-–]\s*(Mon|…)[a-z]*\s*:?\s*[\d:.apm]+\s*[-–]\s*[\d:.apm]+`
run over every saved page, counted by unique string, finds this in one pass. The WhatsApp target
(`wa.me/44…`) is a separate number from the published landline — check it is the dealer's own.

## 9. The quoted APR and the arithmetic behind the monthly payment disagree

A finance calculator that divides the APR by 12 is treating it as a **nominal** rate, so the payment it
prints implies a higher APR than the one on the page. Enter `19.9` and the quote comes out at
**21.82%**; quote `12.9%` as both interest rate and APR and the true figure is **13.69%** — a 0.79 pp
understatement, in regulated copy, on every vehicle page.

Use the effective form, and keep the rate in one constant so the card quote, the worked example and the
vehicle-page line cannot drift apart:

```php
$i = pow(1 + $apr / 100, 1 / 12) - 1;          // NOT $apr / 100 / 12
$monthly = $credit * $i / (1 - pow(1 + $i, -$months));
```

Two checks that find it without reading the code:

- **Reverse the published payment.** Feed the cash price, deposit and term through the effective formula
  and see which APR reproduces the number on screen. If it is not the APR printed beside it, that is the
  finding.
- **Count the mentions of each rate site-wide**, not on the homepage. One rebuild carried the "from"
  rate **16 times** (meta description, hero, badge, body copy, FAQ, `llms.txt`, template default) and the
  representative APR **5 times**, buried inside the worked example. Under CONC the representative APR has
  to be at least as prominent as any other rate: pair every mention (`from 10.4% APR · 19.9% APR
  representative`) or drop the rate and say "finance available".
- Fix the worked example to a **fixed cash price** rather than "whichever vehicle sorts first", or the
  published example changes when the dealer sells a car.
- The provider's widget quotes its own figures. If its representative APR differs from the site's copy,
  one of them is wrong — get the rate in writing before publishing either.

## 10. The full-viewport flash: an iframe at `height:100%` inside a padded wrapper

Symptom: the whole page goes blank — black, then white after a half-fix — for about a second at one
scroll position, **on every page**. The cause is usually the footer map: the wrapper sizes itself with
`padding-bottom: 360px` while the iframe inside asks for `height: 100%`, so before layout settles the
height resolves against the **viewport** and the iframe paints full-screen. Write it up as a finding;
the fix and its probe script live in `dealer-website-build` (`scripts/scroll_flash_probe.py`) so the
remedy is not maintained twice.

```css
.map-wrap { position: relative; min-height: 360px; }   /* not padding-bottom */
.map-wrap iframe { position: absolute; inset: 0; width: 100%; height: 100%; }
```

Two neighbours that turn the same transient into a visible defect: a near-black `html` canvas
(`background-color: hsl(0,0%,12%)`) shows through whenever the body is mid-repaint, and
`background-attachment: fixed` on the hero forces a full-viewport repaint on every scroll frame.

**Probe it instead of watching the recording.** Scroll over CDP, capture a frame immediately after each
scroll, capture again after ~1.2 s, and compare mean brightness:

| scroll | instant | settled | reading |
|---|---|---|---|
| y=3500 | 78.9 | 78.9 | clean |
| y=4200 | **0.0** | 163.6 | the defect |

An instant frame that matches the settled frame is clean whatever the page looks like. Sampling a screen
recording at a few frames a second misses a sub-quarter-second flash and makes it look intermittent —
reproduce it deterministically rather than reviewing the video.
