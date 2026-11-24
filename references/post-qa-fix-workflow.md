# After the QA pass: fix what you found

Proven on Four Plus 4 (fourplus4.co.uk), Sep 2026. Read this alongside section 5
("Deliver") of the parent skill.

## The expectation

Woody treats a QA pass as the **start** of the work, not the end of it. When the review
happens in a session where you also hold live-site access, expect the follow-up
instruction — in the Four Plus 4 session it arrived verbatim as:

> "also carry out any website updates"

So: do not hand back a findings list and stop. **Fix the unambiguous findings in the same
session**, then report them as done-and-verified with evidence. Anything else wastes the
access you already paid for in set-up time.

## Before you ask for access — check three places first

Asking the user for credentials they have already given you wastes a round trip and reads as not
having looked. Check, in this order:

1. **`~/.ssh/config`** for a host alias — the key names in `~/.ssh/` say what each one is for.
2. **The macOS Keychain.** `security find-generic-password -s <keychain-item>` names the account; the
   secret is available to `sshpass` without ever being printed:

   ```bash
   export SSHPASS="$(security find-generic-password -s <keychain-item> -w)"
   sshpass -e ssh -o StrictHostKeyChecking=no -p 65002 <acct>@<host> 'ls ~/domains | head'
   unset SSHPASS
   ```

   The shared dealer host answers on **65002**, not 22, with the same account as FTP; each site is at
   `~/domains/<domain>/public_html`. `nc -z <host> 65002` confirms it before you guess at auth.
3. **The repo's own README and the estate references** — they record which host, which port and which
   access route was already established.

Only after all three come back empty should you ask, and then say what you checked.

**Then check the site is actually in the repo before assuming a template fix applies.** One site in a
batch had no folder at all, so a branch of template fixes that had already shipped to ten siblings had
never reached it — the fix existed, the site was simply outside version control. List the repo folders
against the sites you are about to fix.

**Do not compose a remote path into a shell variable.** `D=~/domains/x` expands `~` on the *local*
machine, so `scp file host:$D/` writes to `/Users/<you>/domains/...` and fails with "No such file or
directory" that names a path you never typed. Use the absolute remote path (`/home/<acct>/domains/...`)
or leave the `~` inside the quoted remote spec.

## Fix without asking — these are unambiguous

- broken / 404 internal links — test every internal href, not just the menu; body service
  cards routinely point at stale slugs the menu itself gets right
- template demo content still live, fake staff/contact details, the host's leftover starter
  blog post
- stale copyright year
- `http://` links on an `https` site (nav items, catalogue PDFs)
- broken images still pointing at an old staging host (e.g. `*.sg-host.com`)
- NAP formatting drift (phone spacing, address punctuation) and brand-name capitalisation
  drifting away from the client's own usage

## Leave outstanding — and say so explicitly

Keep a short **"needs your input"** list and state it plainly:

- anything requiring a client decision, or a real-world fact you do not hold — company
  number, registered office, staff names, review text
- anything requiring a platform/plugin choice — an SEO plugin for meta descriptions (a site
  with no SEO plugin has nowhere to store them), a cookie-consent tool, a gallery plugin
- new marketing copy, or any claim that contradicts another claim already on the site

Do not invent the first category. Removing fabricated content is a fix; inventing its
replacement is not.

## Report the split

Lead with what changed and **how it was verified** (live HTML contains the new string,
image count and rendered dimensions, HTTP status), then the blocked list with the reason
for each. Woody acts on the "done" list and forwards the "blocked" list to the client.

## The the platform PHP route — FTP to a template-built dealer site

Different mechanics from the WordPress routes above: no WP-CLI, no REST, no database. The site is a PHP
template rendering a stock feed, and the fix is an edit to `index.php` / `vehicle.php` / `functions.php`.
Access, the `.htaccess` ordering trap and the public-root sweep live in `platform-estate-deploy`.

1. **Find out who owns the code before editing it, because the answer changes the whole route.** If the site
   is in the platform owner's repo and their `main` is what production serves, **change it there** — worktree
   off `origin/main`, one commit per change, push a branch, open a PR. Editing the live file and syncing the
   repo back afterwards *is* the drift that makes the next deploy revert your fix, and it is drift this
   estate already suffers from. A local clone may be a stale import: diff one known file with line endings
   normalised (`tr -d '\r'`) and compare content, never md5 — a CRLF/LF difference makes identical files look
   different and turns "the repo is out of date" into a conclusion that looks proven. **A repo URL that 404s
   is usually the wrong logged-in `gh` account**: `gh auth status` lists them, `gh auth switch --user <name>`
   fixes it, and neither the repo nor the invite is missing. Fall back to FTP only where there is no repo or
   the owner wants it that way, and then still keep the repo copy in step.
2. **Grep `functions.php` for an existing helper before writing any code.** `get_make_counts()`,
   `make_plural_label()`, `display_make()`, `get_stock_price_range()` and `get_vehicle_image_count()` are
   usually already there. A block driven by the feed re-counts on every render; numbers typed into the
   markup are wrong the next time stock turns over, and a hardcoded count is the finding you will be
   writing next month. Use `display_make()` where a make has one car — "1 Used Ford for sale", never
   "1 Used Fords for sale".
3. **Copy the classes of the same control elsewhere on the site** (the stock page's
   `btn btn-sm btn-outline-secondary rounded-pill`) rather than inventing a style, so the block reads as
   native. Lift the existing markup's shape, not just its intent.
4. **`php -l` the candidate** with `~/.local/php-static/php`, then compare `<div` and `</div>` counts across
   the whole file — inserting markup into a template is where stray closers come from, and a diff that
   realigns its hunks can hide one. Check the fragment's own opens/closes separately.
5. **Upload to `.php.dsc-tmp`, then `RNFR`/`RNTO`.** Keep the rollback **outside the web root** —
   `/domains/<domain>/backups-YYYYMMDD/` — because a `.php.bak` left in `public_html` is served as plain
   text to anyone who guesses the name, and `config.php` holds the dealer's contact details and anything
   else in it. `.htaccess` is the only file Apache protects by name (`^\.ht`). `Path('index.php.live').with_suffix('.php.new')` writes `index.php.php.new` — `ls` the
   filename you believe you wrote, or you lint the wrong path and conclude the edit failed. Dealer PHP line
   endings vary **per file**, not per estate — CRLF on some builds, LF on others. Read with `newline=''`,
   detect, and re-emit the same ending (`"\r\n" if "\r\n" in text[:2000] else "\n"`) instead of assuming:
   getting it wrong rewrites every line of the file and the diff becomes unreadable exactly where the
   reviewer needs to look.
6. **Verify against the data, not the markup.** Extract the new block from the live page and assert every
   number in it against the matching filter (`/stock.php?make=X` returns as many vehicles as the pill
   claims). Then fetch a VDP and one static page — a bad include can leave the homepage perfect and every
   inner page broken.
7. **Screenshot the block.** Scroll by the element's `getBoundingClientRect()`, not `scrollIntoView` on a
   heading (which can land off-screen), and dismiss the cookie banner first — it covers exactly the band
   you are checking.

### Copy that lives in five files, and how to prove it changed

A single visible fact — opening hours, a phone number, "viewing by appointment only" — is usually typed
into five or six files, some config-driven and some hardcoded, and shared includes render it on every page
type. Grep the whole docroot (top level, `custom/`, `includes/`) for the string family before editing, then
edit every hit:

| Surface | Typical carrier |
|---|---|
| Hours table on vehicle pages | `$config['contact']['hours']` in `custom/config.php` (live only; the mirror ships `config.example.php`) |
| Footer hours and the appointment line | `includes/footer.php` |
| Enquiry panel / contact modal | `includes/contact-modal.php` |
| Contact-page hours | `content.json` → `contact.opening_hours`, `json_decode`d by `contact.php` |
| Homepage and About "visit us" blocks | `custom/homepage.php`, `custom/about.php` — rows hardcoded |
| Legacy vehicle templates | `vehicleT5.php`, `car2.php` — still served if requested |

The config value and the hardcoded rows drift apart silently, which is how a site publishes three
different sets of hours at once. **A legacy-looking `content.json` may still be live content** — grep the
PHP for the filename before calling it dead.

Then prove it on the whole set, not a sample: loop the static pages *and* every VDP and count the old
string and the new one (`(?i)appointment\s+only`, `9:30am`, `10:00am - 6:00pm`), and quote the page count
checked. Two traps in that verification:

- **Removal cannot be proved by status code on these builds.** The catch-all serves the homepage with a
  200 for any unknown path, so `…/car.php.bak-20260101` answers 200 whether the backup is gone or not.
  Prove removal with a directory listing (`f.nlst(docroot)` filtered for `.bak` / `.dsc-tmp`) plus a body
  check that the response is the homepage rather than PHP source.
- **A 500 straight after your upload is not proof you broke it.** Upload the pre-change backup as
  `<name>-orig-test.php`, request both, compare, then `f.delete` the test copy — an orphan template that
  fatals on direct access looks exactly like a regression and costs a rollback to be sure.

### Prove the template patch locally before it goes near the fleet

A template fix on a fleet of dealer sites can be reproduced and tested off-server in minutes, and that
is the difference between a canary you trust and one you hope about. Pull the docroot's PHP files over
FTP, run `php -S 127.0.0.1:8124 router.php` from the copy, and drive it with a small probe.

- **The router must mirror Apache's order: real file first, then rewrites.** Serve `return false` for
  anything that exists on disk before applying the URL rules. A router that rewrites first hides exactly
  the defect you are chasing — Apache answers a request for an existing `sitemap.xml` from the file, so
  the rewrite never fires. **A stale `sitemap.xml` must be deleted, not merely re-routed.**
- **Log the resolved absolute path when a mapped file is reported missing.** `file_exists($root . $map[$path])`
  with a missing separator between the docroot and the filename returns false for a file that is sitting
  right there, and the symptom is a 404 from the catch-all that reads as "the rewrite does not work".
- **If the harness returns 200 for a file `php -l` says will not parse, it is serving a stale copy —
  restart the server** before debugging the patch. Debugging a stale process cost four test cycles on one
  build; a restart is two seconds.
- **Assert on the rendered head, not on the source diff:** status code, `<title>`, every `<h1>`, and the
  canonical on four URLs — homepage, a vehicle page, a vehicle page with a deliberately wrong slug, and a
  junk path. Print before and after; that table is also the evidence to show the platform owner.

### The 404 guard: whitelist the routes that target index.php, and silence the canonical

Turning a soft-404 into a real 404 is a three-part edit. Doing only the first part ships a new defect.

1. **Enumerate every `.htaccess` rule whose target is `index.php` before writing the guard.** The catch-all
   is not the only one — builds routinely map a live page to the same file (`RewriteRule ^servicing$ index.php`),
   so a guard written as "anything that is not `/` gets a 404" takes a working page off the site.
   `grep -n 'index.php' .htaccess` and whitelist every path it names alongside `/` and `/index.php`.
2. **Suppress the canonical and `og:url` in the 404 branch.** The shared header builds `$canonicalUrl` from
   `$_SERVER['REQUEST_URI']`, so a 404 that still renders it nominates the non-existent URL as canonical —
   worse than the soft-404 it replaced. Set a flag before requiring the header (`$dsc404 = true;`) and wrap
   both tags in `if (empty($dsc404))`.
3. **Drop the query string from the canonical while you are in that line** — `strtok($_SERVER['REQUEST_URI'], '?')`.
   Otherwise every `?make=` filter self-canonicalises and competes with the stock page, which is the
   duplicate-content defect sitting underneath the 404 one.

Verify with a junk path: 404 status, **no** `canonical` in the head, and the page still rendering the branded
header and footer. Then re-request the route the guard could have swallowed.

### A generated sitemap can double the slash after the host

A generator concatenating a base ending in `/` with a helper returning a path starting in `/` emits
`https://domain//car/…`. Apache usually still answers it, so nothing errors and the sitemap reads as fixed.
Assert the generated set, not just its status: every `<loc>` has exactly one `/` after the host, and treat
`//` after the domain, `localhost`, `127.0.0.1` and any foreign host as failures in the same check.

### A check that finds nothing is not a pass

Every extraction-based assertion must fail when the extraction returns an empty set, or it reports a clean
bill on the strength of a regex that never matched. One harness passed "one representative APR on the site"
with `APRs found: []` because the pattern expected `9.9% APR` while the page said `APR 9.9%`; matching both
orders turned it into a real test — and a real failure.

When several fixes land in one sitting, write the checks as a small pass/fail harness rather than as prose:
it gives the next person a re-runnable scoreboard (`5/22 → 14/22`) instead of a claim, and it catches the
regression the next change introduces.

**A fix can invalidate the harness's own assumptions — re-point it the same day.** Adding an apex-to-www
301 makes every check that requests the apex see the redirect instead of the page, so the 404, privacy
and sitemap checks all flip to FAIL while the site is healthier than it was. Point the harness's base URL
at the canonical host and assert the apex separately by expecting the 301. A burst of failures immediately
after a correct redirect fix is the harness reporting the redirect, not a regression — say which before
touching the site again.

**And make the checks fail on presence, not on strings that merely exist in the source.** An
"analytics present" check written as `"googletagmanager" in html` passes on a consent-gated loader that
requests nothing until the visitor accepts. Assert the thing that does the work — a real `<script src>`,
or a measurement ID matching `G-[A-Z0-9]{8,}` — or the check certifies a page that measures nothing.

**And check the iframes.** A finance or reviews module framed from the platform
(`app.<platform>/…/financeapp/`) carries its own rates and wording in a separate document, so a page-text
sweep sees none of them. Fetch the iframe URL directly and compare its figures against the page copy — that
is how a site presents two different "representative" APRs while every page-level grep finds one.

`templates/check-live-site.py` is a starter version of that harness — copy it beside the audit folder,
pass the domain as the first argument, delete the checks that do not apply to the build, and add the
site's own legacy URL families. It prints `PASS`/`FAIL`/`INFO` and exits non-zero on any failure, so it
can gate a fix batch and be re-run afterwards for the before/after score.

### Classify the template generations before promising one deploy

The sites share a server, not a codebase. Probe each docroot's `car.php` for a signature and group them:

- a literal `$pageTitle = 'Vehicle Details'` present ⇒ the generation that titles every car "Vehicle Details"
- `for Sale in` already in `car.php` ⇒ that site is already transactional; skip it and say so
- a small `car.php` (single-figure KB) with no `includes/` ⇒ its own single-file build; the patch does not apply

Write the patch as a **script that refuses when the signature is missing** (`raise SystemExit("generation
differs, stop")`) and stamps a marker comment (`// DSC: …`) so a second run is a no-op. Nine sites patched
by a script that cannot mis-apply beats one site patched by hand and eight by memory.

### Variables the header include consumes must be set before it

On the platform template, `car.php` assigns `$pageTitle` twice — once as a literal before
`require_once 'includes/header.php'`, and once with the make and model *after* it. The second assignment is
dead code, which is why every vehicle page titles itself "Vehicle Details". When a title, description or
canonical is wrong on a template page, find the include that emits it and read what is set above it; the
fix is usually to move one block, not to add markup.

**There are two header includes in the file, and the first belongs to the 404 branch.** `if (!$car)` opens the
page and calls `require_once 'includes/header.php'` for the vehicle-not-found state before the main template
starts. Replacing the *first* occurrence patches that one, leaves the real include where it was, and the page
keeps its old title while the diff reads as a plausible fix: `php -l` passes, nothing errors, nothing changes.
Anchor on the include immediately *preceding* the dead assignment being deleted (or the last occurrence before
the template body), then confirm by reading the rendered `<title>` — never by reading the diff.

**Dump the config's shape before interpolating any field, because the same value sits under a different key
in each generation.** The town that belongs in a transactional title is `$config['contact']['address']['city']`
on the current template, `$config['dealer']['city']` on one generation and a bare `$config['city']` on a third
— and a wrong path renders an **empty string mid-sentence**, so the patch publishes "for Sale in " with
nothing after it and reads as a copy bug rather than a bad key. One command settles it:
`~/.local/php-static/php -r 'require "config.php"; var_export(array_keys($config));'`, then walk the nested
keys printing values for identity fields only. Then trim at the first comma — the stored value is usually
"Rochdale, Lancashire" and the title wants "Rochdale" — and take the town from the config rather than
hardcoding it, or the patch is right on one site and wrong on the next eight. The local render is what
catches this: a `for Sale in` with a trailing space is invisible in a diff and obvious in the probe output.

## Layout defects: measure element edges, never `scrollWidth`

A “the header is clipped at 1280” report cannot be confirmed with `document.documentElement.scrollWidth`
on this estate, because the template ships:

```css
html, body { overflow-x: hidden; max-width: 100%; }
* { max-width: 100%; }
```

Content that overruns is **clipped, not scrollable**, so `scrollWidth` equals the viewport and a
width-only check reports a clean pass on a page whose primary CTA is half off-screen. Measure the
**right edge of every interactive element against `window.innerWidth`** at each suspect width instead.

Procedure:

1. **Measure before changing anything**, at every width the claim covers plus one either side (a
   “1280” bug is often a 1024–1170 band). Report the furthest right edge and the slack in pixels.
2. **Test candidate fixes by injecting CSS**, not by deploying and squinting. Append a `<style>` over
   CDP, re-measure, and keep the variant with real slack — aim for ≥16px, not zero. Compare at least
   two candidates.
3. **Check a candidate has not removed a function.** Hiding a header button is an easy way to make the
   row fit; if the floating equivalent is `lg:hidden`, hiding the header one leaves that whole width
   band with no WhatsApp or phone CTA at all. The cheapest fix that fits is not always the one to ship.
4. **Deploy the rule where it cannot be defeated by caching** — the theme-scoped inline `<style>` block
   in the header include ships with the page; a theme stylesheet may be served from cache with no
   version query to bust it.
5. **Re-measure live** at the same widths and confirm mobile is untouched (no horizontal scroll, the
   mobile menu still visible, desktop nav `display:none`).

`scripts/measure-layout.py` does steps 1, 2 and 5: pass a URL and widths, optionally a CSS file or string
to inject, and it prints the furthest right edge per width with the slack and a PASS/FAIL verdict.

## The compliance layer: privacy, consent and analytics

These three ship together, and the order matters — the banner must exist before analytics is installed,
so the first consented visit is not also the first non-compliant one.

- **Re-test every pre-launch finding against the live host the day after cutover.** A site can go live with
  none of them applied: the fixes exist on a branch, the domain moves anyway, and the handover reads as
  finished. Run the earlier report's findings as a checklist before writing a new one — that is how a
  wrong-domain sitemap or a dead published email gets caught on day one instead of at the next audit.
- **Build the privacy page out of the site's own page pattern**, not as a new design. On this template a
  page is a thin wrapper (`$pageTitle`, `require includes/header.php`, `include custom/<page>.php`) plus a
  content file, so `privacy.php` + `custom/privacy.php` inherits the header, footer and enquiry modal.
- **Make the registered-company block conditional on the config constant** — `if (defined('DEALER_COMPANY_NO')
  && DEALER_COMPANY_NO)`. A sole trader has no company number, so the block simply never renders, which is
  the correct outcome; a Ltd client gets it the moment the constant is set. It also means no `[Company No.]`
  placeholder can ever ship.
- **Find the shared form include before editing forms.** Every page's enquiry form is usually the same
  `includes/contact-modal.php`, so one consent line above the submit button covers the whole site; editing a
  per-page contact template reaches one page out of twenty.
- **Load no analytics at all until consent**, rather than loading the tag with Consent Mode denied. Both are
  defensible, but the stricter one is easier to explain, easier to prove, and makes the banner the single
  control. Store the choice in `localStorage`, offer Accept *and* Decline, and give the footer a
  "Cookie settings" link that clears it so the choice can be revisited.
- **Verify analytics by the request it makes, not by the tag in the page.** Click Accept over CDP with
  `Network.enable` and assert a `…/g/collect?…tid=G-XXXX` beacon. A page that merely contains the ID proves
  nothing: a consent-gated loader ships the ID in every page and sends nothing until someone accepts.
- **"No data received" in GA4 is the expected state on a consent-gated property**, not a broken install.
  Say so before anyone spends an afternoon re-tagging — it clears on the first real consented visit, and
  headless or bot traffic can be filtered, so the reliable check is a human visit to Realtime.
- **When a rate is unconfirmed, remove your own claim rather than leave it live.** If the client says the APR
  is TBC while the embedded finance module shows a different representative example, take your figure out and
  say a representative example is available on request. An unsubstantiated representative APR is a regulated
  statement; the lender's module is at least attributable. Restoring the confirmed number is one edit.

## Related

- `references/applying-fixes-via-in-session-rest.md` — the mechanics for pushing edits live
- `references/finding-evidence-and-drilldown.md` — retaining `qa/crawl/` and answering "where is that finding"
  from the markup once the report is out, including the three ways a drill-down corrects the report
- `references/siteground-ssh-wp-cli-access.md` — the SSH + WP-CLI route for hosts where
  REST is bot-challenged
