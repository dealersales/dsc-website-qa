# the platform dealer sites — the quick template fixes

The the platform PHP dealer sites on the platform owner's Hostinger account share two or three template
generations, and the same four head-layer defects recur on every one. This is the
patch that fixes them, proven on a local PHP render of a live site's own files
before anything is deployed.

## Which generation a site is

Classify from `car.php` before writing anything — the fix differs:

| Generation | Signature | Title behaviour |
|---|---|---|
| A | `$pageTitle = 'Vehicle Details'`, then a make/model assignment **after** `require_once 'includes/header.php'` | dead code — every VDP titles itself "Vehicle Details" |
| B | `$pageTitle = $summary . ' for Sale in {Town}'` before the include; header has a 60-char title-length branch | already correct — leave alone |
| C | single-file build: `$pageTitle` set inline, `<h1 class="car-title">`, no `sitemap.php`, and the navigation lives in a root `header.php` while `includes/` holds a **second, different** template | bespoke — see "Gen C" below |

`grep -q "for Sale in" car.php` → B. `grep -q "pageTitle = 'Vehicle Details"` → A.
Under ~9 KB with no `sitemap.php` → C. **Do not use the presence of an `includes/` dir as the
test** — Gen C ships one, and it serves a different template entirely. On a mixed estate the split is usually A for most builds, B for one or
two, and C for a handful.

## The four defects and their fixes (Gen A)

1. **Every VDP titled "Vehicle Details"** — `car.php` assigns `$pageTitle` *after* the
   header include, so the value is never used. Move it above the include and build it
   from the car: `{Year} {Make} {Model} for Sale in {Town}`. The header appends
   ` - {Dealer}` itself, so keep the town short (strip after the comma).
2. **Bare make/model H1** — same block; append " for Sale in {Town}".
3. **Unknown URLs return the homepage with HTTP 200** — `.htaccess` has a catch-all
   `RewriteRule ^(.*)$ index.php`, and `index.php` just renders the homepage. Guard at
   the top of `index.php`: any path other than `/` or `/index.php` gets
   `http_response_code(404)` and a 404 body.
4. **`/sitemap.xml` serves a stale dev file** — `RewriteRule ^sitemap$ sitemap.php`
   matches only the extension-less path. Add `RewriteRule ^sitemap\.xml$ sitemap.php [L]`
   **and delete the static `sitemap.xml`**: Apache serves an existing file before any
   rewrite, so the rule alone does nothing. Proven both ways in a local harness.

## Two traps that ship as bugs if you patch from the obvious reading

- **The town is not at `dealer.city`.** It lives at `$config['contact']['address']['city']`
  (e.g. `"Rochdale, Lancashire"`). Read that, then `explode(',', …)[0]`, or you publish
  "for Sale in " with nothing after it. Keep the full string for the meta description.
- **`includes/header.php` builds the canonical from `$_SERVER['REQUEST_URI']`**, so
  `/car/<id>/<any-slug>` returns 200 and self-canonicalises. Separate fix: move to
  `$canonicalUrl = $canonicalUrl ?? 'https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'];`
  and set the real one in `car.php` from the stored slug. Ship the canonical before any
  sitemap regeneration, which re-slugs cars from current feed fields.

## Gen C — the two-template build

Gen C is not one template badly built; it is **two templates in one docroot**, and every
head-layer finding depends on which one serves the page you are looking at.

| Serves | Header / footer | Notes |
|---|---|---|
| index, stock, sold, car, about, contact, reviews, sell, sites, privacy, terms | **root** `header.php` / `footer.php` | no canonical, one hardcoded `description` on every page, no OG, nav lives here |
| finance, warranty, sell-your-car, thank-you | **`includes/`** `header.php` / `footer.php` | canonical + OG + JSON-LD, Tailwind Play CDN (`cdn.tailwindcss.com`), its own nav with no showroom |

So `grep canonical includes/header.php` finds one and tells you nothing: the pages a customer
actually lands on have none. Fix the root pair — that is where the description, canonical, OG
tags, `tel:` normalisation and the mobile toggle live. And note the nav asymmetry: the
`includes/` pages are unreachable from the menu, so finance — the page carrying the APR — is
only ever found by direct URL.

Other Gen C facts worth knowing before you patch:

- **The finance block is platform data, not template copy.** Each stock record carries
  `finance: {amountfinanced, apr, hp24, hp36, hp48, hp60}`, cached at `cache/stock.json` and
  rendered by `car.php`. The template prints `apr` and the 24/36/48 payments and silently drops
  `hp60` and `amountfinanced`. Changing the rate is a feed change; **withholding** an
  unsupported monthly figure until a representative example exists is a template change, and
  that is the half you can do.
- **De-duplicate on `vehicleid`, not `regno`.** The feed returns the same car twice for a few
  rows, and `regno` is empty on most records, so a regno key silently keeps every duplicate.
- **The enquiry handler reads `$config['contact']['enquiryemail']`, which is usually unset.**
  A form that posts to `thank-you.php` therefore reaches the lead endpoint with no notification
  address, and where the lead lands is unverified — say so rather than reporting the form as
  working end to end.
- **`.btn` is only styled inside scoped contexts** (`.hero-content .btn`,
  `.vehicle-card__actions .btn`, `.welcome-section .btn`), so a new bare
  `<button class="btn">` renders as an unstyled native control. Add a global rule before
  adding UI.
- **Two sell-your-car pages can both exist** — the one in the menu without a form, and a
  longer one with the form that is outside the menu and the sitemap. Check which one the nav
  actually points at before deciding the site "has" or "has not" got a valuation form.

## Verify on a local render, not on the live site

Pull the docroot files (FTP or the mirror), patch, then run
`php -S 127.0.0.1:8123 router.php` with a router that mirrors the `.htaccess` order:
**static file first**, then `/car/<id>/<slug>`, then the clean-URL map, then the
catch-all. Assert by value, not by presence: the VDP title string, the H1, a 404 status
on a junk path, `/sitemap.xml` returning `application/xml` from the generator,
`/robots.txt` returning text.

The router itself has two gotchas that read as "the patch failed":
`file_exists($root . '/' . $map[$path])` — a missing slash silently falls through to the
homepage — and `php -S` can serve a cached router, so restart the server (or run it with
`-d opcache.enable=0`) after editing it.

**A port that is already bound serves somebody else's build, and it looks exactly like a patch that
did not apply.** The second `php -S` on a busy port exits with `Address already in use`, the old
process keeps answering, and every request returns the *previous* code — junk URL still 200, the old
title still in the `<head>`. Pick an unused port each run and confirm the responder is yours before
believing a result: `curl -sI` the URL and check the process, or simply watch the new server's own
log file as you make the first request.

## Who owns the fix — establish access before assigning it away

An audit's fix list naturally says "Build" for anything in the template, and that is a guess about
capability rather than a fact. Before a finding is put on a third party, establish what we can
do ourselves, in this order:

1. **Credential in the keychain** (`security find-generic-password -s <item>`) — presence only, never
   print the value; read it into a variable and pass it to `ftplib`.
2. **A listing of the docroot**, plus one `retrbinary` to prove read access.
3. **`main` against production**, file by file, over the downloaded source (below). A checkout that
   matches live is a working base; one that does not is a snapshot and must not be patched.

If all three hold, the template work is ours and the fix list should say so. What remains with the
platform owner is the part that is genuinely theirs: the feed values behind the template, the shared
service endpoints, and permission to deploy to their server — which is a conversation, not a
capability gap. Say which is which in the handover, because "we can do this, the platform owner only has to agree"
and "this needs the platform owner" produce completely different timelines for whoever is chasing the client.

Two more that cost a cycle each:

- **Seed the stock cache instead of depending on the API.** `includes/stock-loader.php` caches
to `includes/cache/stock_<md5(serialize($filters))>_<did>.json` for 300s; with no filters that
key is `stock_40cd750bba9870f18aada2478b24840a_<did>.json`. Download the live copy off the
server, write it under that name in the test tree, and the build renders real stock offline.
- **Fetch the docroot with Python `ftplib`, not curl.** `FTP_TLS(host)` → `login(user, pw)` →
`prot_p()` → `retrbinary("RETR <file>", buf.append)`. curl's `--ftp-ssl` answers `234`
("not found") for every path on the estate host including `/`, which reads as a bad login or a
wrong directory. Print the password's length only, never the value.
- **Diff source against source.** Curling `/index.php` returns rendered HTML, so comparing it
to the repo's `.php` reads as "DIFFERS" on a checkout that is in fact identical. "The clone
matches production" is only true if you compared the downloaded source.

Deploy discipline: dated backup of each file on the server, one canary site, 24h watch,
then batches. Verify the live values afterwards — a successful upload is not a deploy.

## Where the compliance copy actually lives

A footer-only scan reports "no FCA number anywhere" and is wrong on at least five sites.
Check, in this order: `/`, `/finance`, `/about`, `/fca-disclosure.php`,
`/privacy-policy`, `/policies`, `/terms`. The number is frequently in a disclaimer block
at the foot of *every* page rather than in a footer element, and a dealer's sits behind
`/fca-disclosure.php`, which is nine tenths privacy policy under an FCA heading.

## The embedded finance widget names the broker, and gets it wrong

Two addresses, two different firms and two different headline rates:

- `…/financeapp/index.html` → "the platform Finance is a Credit Broker not a lender. Rates from 8.9% APR"
- `…/financeapp/index.php?did=<id>` → "Forward Finance is a Credit Broker not a lender. Rates from 9.9% APR"

Neither is necessarily the dealer's own broker — a dealer's disclosure names a dealer
Teesside Ltd (FRN 1005856) with Close Consumer Finance and Motion Finance as lenders. The
same representative example sits under both. Report it as platform copy for the platform owner; no
dealer can fix an iframe.
