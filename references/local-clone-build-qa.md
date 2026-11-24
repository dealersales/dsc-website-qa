# QA-ing a local build cloned from another dealer's template

Applies when a rebuild is handed over before it is live: source on disk, no URL to fetch,
and a template that came from a sibling dealership.

Two companions sit beside this file: `references/reviews-and-testimonials.md` (fabricated-testimonial
fallbacks, platform seed data, and the filter-and-label rule for "good reviews only") and
`references/render-and-artefact-verification.md` (proving the PDF/DOCX before delivery).

1. Serve it behind real Apache, not `php -S`
2. Grep the clone for the source dealer's identity — including non-visible values
3. Hidden containers are not page content
4. Replay the outgoing site's sitemap, and anchor the vehicle rule
5. Check each filter's field name against the payload, not the template
6. A fresh clone serves its own build files, caches and raw feed
7. Hand back a diff and a harness, not edits to the builder's repo
8. Opening hours have one home, and the profile is the truth
9. Give them a URL before it goes live
10. Look at the pictures the build ships
11. The deliverable is a worklist, not a changelog

## 1. Serve it behind real Apache, not `php -S`

`.htaccess` carries the rewrites, the 404 handler, the security headers and the canonical-host
rules, and `php -S` ignores every one of them — so a server-only defect (or a false pass) never
shows. Mount the docroot and a vhost into the stock PHP image:

```bash
docker run -d --name sc2 -p 127.0.0.1:8181:80 \
  -v <site>:/var/www/html \
  -v <conf>:/etc/apache2/sites-enabled/000-default.conf:ro php:8.2-apache
docker exec sc2 bash -lc 'a2enmod rewrite headers expires deflate; apache2ctl -k restart'
```

vhost: `DocumentRoot /var/www/html`, `<Directory>` with `AllowOverride All`, `DirectoryIndex index.php`.

**Bind a specific port and assert you are testing the right site.** `8080` is contended on a working
dev machine — another session's `php -S`, or a leftover container, can hold `127.0.0.1:8080` and answer
`200` with a *different dealership's* site. Every check then passes or fails against the wrong build,
and the results look plausible, which is what makes it dangerous. Publish on a high, unusual port
(`127.0.0.1:8181:80` rather than `0.0.0.0:8080:80`), and make the first assertion in every harness the
identity of the page: the `<title>` contains the dealer's name. `lsof -nP -iTCP:<port> -sTCP:LISTEN`
shows who actually holds it — a `php` process beside the docker proxy means you have two servers and
the more specific bind wins.

Two follow-ons that cost a cycle each if you meet them cold:

- **The container cannot reach the host's `127.0.0.1`.** To exercise a form against a stubbed
  upstream, point the include at `http://host.docker.internal:<port>/...` and bind the stub on the host.
- **`socketserver.TCPServer` needs `allow_reuse_address = True`**, or the second run dies with
  `OSError: [Errno 48] Address already in use` on a port `lsof` says is free.

Run `php -l` over the tree as well; a build can render and still carry a syntax error in an
include that only some pages reach.

## 2. Grep the clone for the source dealer's identity — including non-visible values

Copy strings in the visible copy are the easy half (`{template}`, `{town}`, another dealer's name,
phone, address, `25 years`). The half that survives a copy review is the **config and API keys**:

- **There are two finance includes, not one**, and they fail differently. `_codeweavers.php` drives
  the calculator on vehicle pages; `_codeweavers_finance.php` drives the Apply for Finance page.
  Both are copied file-for-file between builds, legacy commented-out keys included. On one rebuild the
  calculator held a stranger's key (blank 1,356 px iframe, applications routed to another dealership)
  *and* the finance include held a third, shorter key nobody could account for — the apply page printed
  `Status Code: 401 … Failed to authenticate` in the middle of the live page. Fixing the calculator
  file alone looks like a complete fix and leaves the application journey dead. Compare **both** against
  the outgoing site's own pages: a dealer normally uses one key for both. Never write a key into a note,
  a report or this file — record that they differ and where.
- **A provider's error text is never page copy.** Wrap the widget area so raw API output (`Status Code`,
  `Failed to authenticate`, `API URL`, any 4xx body) is replaced by a short failure message carrying the
  dealer's phone number. A page returning 200 while displaying a 401 body passes every status check,
  which is why this survives a sweep.
- Same for the analytics ID (compare against the outgoing site's HTML), the stock API dealer id,
  the WhatsApp number hardcoded in `functions.php`, and any `linkBackUrl`.

One command settles it: `grep -rn 'ApiKey\|G-\|did=' ~/Documents/<project>/repo/customer-websites/*/`
and diff the target build's file against both the template and the outgoing site.

## 3. Hidden containers are not page content

A print spec sheet (`<div id="printSheet" class="d-none">`, revealed only by
`@media print { #printSheet{display:block} }`) duplicates the whole vehicle record. Strip tags and
every field appears twice, which reads as a Critical duplicate-content defect. Check what is
actually painted — `getComputedStyle(el).display` over CDP, or a screenshot — before writing it up;
here it was `none`, and the real defect on the same page was the description rendered in `.text-danger`.
Same rule for `d-print-none`: hidden DOM is page weight at most, never a rendering fault.

## 4. Replay the outgoing site's sitemap, and anchor the vehicle rule

A build can redirect the legacy families its developer remembered and still miss everything the
current site publishes. Take the live `sitemap.xml` (plus any page reachable only from a button —
`/finance2.php` was the live site's apply-for-finance target), request each path with redirects off,
and report the split. dealerA2: 7 of 28 resolved, 21 × 404, including all 17 vehicle URLs and
`/cars.php`.

The vehicle rule is usually one line, because the VDP already resolves a numeric id and 301s to the
canonical slug — but **anchor it to a token the old format always has** and the new one never does:

```apache
RewriteRule ^vehicle/used-(.+)-([0-9]{4,6})/?$ /vehicle/$2 [R=301,L]
```

Each archived slug starts `used-`; no generated slug does. The unanchored form
(`^vehicle/(.+)-([0-9]{4,6})`) is unsafe the moment you also shorten slugs, because a
`year-make-model-stockno` slug ends in the same stock number — the rule then catches the *live*
inventory and 301s every car to `/vehicle/<id>`. Two rules interacting, each correct alone.

Validate both ways, and **re-run the both-ways gate after any change to the slug generator**, not only
when you first write the redirect: every archived URL caught, and **every current vehicle URL returns
`200`**. Fetch the whole set, never a sample — a single-car check passes or fails by which car happens
to sort first.

## 5. Check each filter's field name against the payload, not the template

A filter written against a field the feed does not populate fails **all-or-nothing**, silently, and
returns 200 throughout — so it reads as working unless you compare the result set to the stock:

| Symptom | Cause |
|---|---|
| `min_x` returns **0** rows, `max_x` returns **every** row | the key is missing, so both bounds compare against `0`: `0 < min` excludes all, `0 > max` excludes none |
| a dropdown offers one option, or the right option returns 1 of 8 | the option list is built from the same missing key |

On the platform feed the populated keys are **`modelyear`** (not `year`, which exists but is blank on
nearly every record) and **`bodystyle`** (not `bodytype`, which does not exist at all). `fuel` and
`transmission` are reliable; `enginesize` is cc.

Probe every parameter independently and read the **counts**, not the status: `?bodytype=SUV` → "1 of
17" is a defect on a forecourt of eleven SUVs, and the same request against the dropdown's own value
list tells you whether the list or the comparison is wrong. Then fix by helper rather than by inline
key — `vehicle_year()` falling back to `1stregdate`, and `get_body_type()` falling back to a
model/spec/description match — so a record with the field empty still sorts into the right bucket
instead of vanishing from every filtered view.

## 6. A fresh clone serves its own build files, caches and raw feed

Nothing in the repo blocks them, and they are not in `robots.txt` because nobody classified them:
`/README.md` (the internal file map), `/httpd-vhosts.conf` (the developer's absolute path),
`/config.example.php`, `/stock-feed.php` and `/cache/stock_cache.json` (the full CRM export — VIN,
engine number, cost and supplier fields) and `/includes/*.php` as partial markup. Directory listing
is usually off (`403` on `/cache/`), which is why a listing sweep reports it clean while the files
inside serve `200`.

Check each by path, and block them in `.htaccess` beside the redirects:
`RewriteRule ^(?:cache|includes)/ - [R=404,L]` plus a `(...)$` alternation for the named files.
Then re-check that `robots.txt`, `llms.txt`, `sitemap.xml` and the assets still answer `200` — the
block is easy to write one path too wide.

## 7. Hand back a diff and a harness, not edits to the builder's repo

The build belongs to whoever owns it; a clone under `<platform>/repo/` is not ours to commit to.
**Writing the fix is still ours.** Do not let "it is their code" turn into parking work with the
platform owner: the test for ownership is whether the change lives in a file we can reach, not who
authored it. On this estate we hold a local copy of every template, the `.htaccess`, the sitemap
generator and the CSS, plus a local Apache to prove a change against — so a defect is ours to write
and theirs only to deploy. Reserve the platform bucket for what is not a file at all: the stock feed's
per-record values, a third-party endpoint's field mapping, an API key pair issued from an account, and
the deployment itself. When a first draft assigns build items to the developer, expect the challenge
"can we not do any of these?" — and check, file by file, before answering.

**Label owners by first name** — the person, not a company or a bucket ("Us — DSC" is not an owner;
"Paul" is). Dealer-side decisions all go to the dealer contact, whatever their subject.
Work on a throwaway copy, then deliver:

- a **unified diff** against the commit audited (`diff -u --label a/f --label b/f` per file), which
the builder can accept, rework or bin;
- a **scripted harness** that asserts the fixes by value and guards the regression the fix could
  cause — for the redirect rule that means proving every archived URL is caught *and* every current
  slug still returns `200`;
- the **counts before and after** in the handover, because "SUV 1 → 11, year 0/17 → 8+9" is what
  makes the patch credible, and "fixed the filters" is not.

**Derive the harness's expected counts from the feed, never type them in.** A stock feed is live: the dealer sells a car mid-week and every hardcoded assertion (`"17 vehicles in stock"`, `SUV == 11`) fails as though the site had broken. Fetch the feed at the top of the run, compute the totals from it, and assert the *site* agrees with the *feed* — `len(feed)`, the count of each `bodystyle`, and `min_year + max_year == total`. The relational form survives stock changes and still catches the defect it was written for; the literal form costs a false alarm on the first run after a sale and, worse, trains you to wave a red result through.

**The audit of record stays as found, and severities do not demote.** Write the findings against the
build that exists, and when a fix is written but not deployed leave the severity where it is: the
severity measures the build, and a fix in a branch nobody has deployed has not changed the thing the
reader is looking at. The failure mode to avoid in either direction is a document whose severity table
no longer matches the code anyone can read.

## 8. Opening hours have one home, and the profile is the truth

Hours are typed three times — the footer partial, the contact aside, and the `OpeningHoursSpecification`
in the JSON-LD — so they drift, and the schema ends up disagreeing with the block a customer is reading.
Put them in **one config constant** (`DEALER_HOURS`, ISO day number => `[open, close]`) and derive the
open/closed badge, the visible rows and the schema from that array. Generated schema cannot contradict
the page; three hand-typed copies will.

When site and profile disagree, **the Google Business Profile is authoritative** — it is the listing a
customer checks before driving over, and the one that gets updated when hours change. Match the site to
the profile, never the reverse.

Reading the full week off a profile is not reliably automatable in a browser session: Maps serves a
limited panel, the hours dropdown ignores synthetic `click()` and CDP mouse events, and a few rapid
requests get the IP rate-limited on Search. What you *can* read is the current-day line ("Open · Closes
8 pm"), which is enough to prove a weekday discrepancy and fix it. **Name the days you could not
confirm** in the finding and leave them unchanged — inventing Saturday and Sunday is worse than asking,
because a customer acts on it.

If a page's stated weekday contradicts `date`, believe the page and check the clock: a drifted system
clock silently falsifies "open now", published dates and the date on the audit itself.

## 9. Give them a URL before it goes live

A pre-launch build nobody can click is hard to sign off. A static crawl of the local build, pushed to a
GitHub Pages branch, gives the client and the dealer a phone-friendly preview and a progress page.
Traps, all silent:

- Inline `style="background-image:url('/assets/x.jpg')"` and JSON/meta attributes are invisible to a
  rewrite that only touches `href`, `src` and `srcset` — the hero renders **black** and everything else
  looks fine.
- A `fixed-top` header sits over the preview banner; push the page down by the banner's height in the
  preview CSS rather than living with the overlap.
- A builder that clears its own output directory takes `.git` with it — preserve it or the push fails
  after an otherwise clean build.
- Add `noindex` to the preview before sharing it; a crawled clone competing with the live domain is a
  worse outcome than no preview.

## 10. Look at the pictures the build ships

A QA pass that only reads markup and status codes misses the two things a visitor judges in the first
second, because both are structurally invisible: which photograph is on screen, and whether it is any good.

**Identify every image in a hero rotator by eye, not by filename.** A background rotator is a list of
paths, and nothing in the HTML says what they depict. On one rebuild the list held two of the dealer's own
Range Rovers, a **stock Mini convertible** with a blank plate, and a generic row of cars on a forecourt.
The Mini was the frame the rotator frequently landed on, so the first thing a visitor saw was a car the
dealership does not sell, on the page whose job is selling its stock — and on a page quoting "cars from
£7,200" a pictured Mini is a description problem as well as a quality one. Pull the list
(`data-hero-slides`, the CSS, or the `<img>` set), open each file, and check the subject: keep the
dealer's own photography, drop stock. Collapsing the rotation to a single own-photo frame is usually the
whole fix; the unused files can stay on disk.

**Judge the stock photographs as listing copy.** Feed images are the dealer's own and cannot be fixed in
the template, but their quality decides whether the rebuild looks better than the site it replaces: one
car was photographed on the workshop ramp with the lift and an oil drum behind it, where the rest of the
stock had clean showroom shots. Report it as a note for the dealer rather than a build defect — the fix is
how the forecourt photographs stock, and it is worth saying before the new site starts sending traffic.

## 11. The deliverable is a worklist, not a changelog

When the document goes to the people who have to act — the builder, the client's coordinator — every line must
answer "what do I do next". Revision history is not their business and it dilutes the one thing they need.

Woody states it directly: *"dont explain the changes in the doc, this is to give to the client and the platform owner to show what
needs doing and not showing the changes to the doc that i've made"*.

So a document that is going to a builder or a dealer carries **only**:

- Page / Severity / **Owner** / Expected / Actual / Evidence / Recommendation, per finding
- a short who-does-what table at the front, using first names (Paul / the platform owner / the coordinator) rather than company names
- passes worth recording, and a launch checklist

and it does **not** carry: a status board (Done / Still to do / The dealer's), a "status at reissue" note,
"fixed in the patch — not deployed" lines, a cover reissue line, or any sentence beginning "this version…".
Those belong in the working `.md`, in the handover message to the builder, and in the digest.

**Two artefacts, two jobs.** The report says what is wrong and who fixes it. The patch plus a short note to
the builder says what has already been written and how it was proved. Letting the second leak into the first
is the failure — a reader triaging a to-do list does not need to know it was reissued twice in an afternoon.

This ordering matters because the instinct on a reissue is wrong: the status board, the "nothing here is
live" note and the fixed/not-deployed column feel like honesty, and to a builder they are. To the reader
holding a list of jobs they read as process noise, and they bury the one column that matters — the owner.
