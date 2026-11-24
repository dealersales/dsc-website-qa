---
name: dsc-website-qa
description: "Use when QA-ing a client website. Severity findings."
version: 1.0.0
author: Paul "Woody" Wood, Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [dsc, website, qa, audit, quality-assurance, dealership]
    related_skills: [dsc-seo-audit, dsc-gbp-audit, uk-car-dealer-copy, dsc-fca-compliance]
---

# DSC Website QA

Structured functional and content QA framework for UK dealership websites. Produces a report with numbered findings, severity ratings (Critical / High / Medium / Low / Info), expected vs. actual behaviour, and a priority-ordered action list. Designed for iterative passes — findings are updated across sessions as fixes are confirmed.

Images zoomed/cropped reported: `references/rendering-diagnosis.md`.

## When to Use

- A site built by cloning a template kit or another client's build **carries the original owner's links and assets**. Sweep every external URL in the live Elementor data and menus, and resolve each one — a footer Google icon was sending customers to a different garage. Revisions must be filtered out or the sweep is noise.
- Elementor's locally-downloaded Google Font CSS bakes in the site URL at download time; on a site styled on staging, every `@font-face` points at the dead host and the whole site renders in fallback type. Flushing the CSS cache does **not** fix it. Procedure, plus the CID-link fix for wrong Maps links and the escaped-slash `/` gotcha in stored Elementor JSON: `references/elementor-cloned-site-contamination.md`
- A client asks for **N new pages built on an existing Elementor site** ("build the 7 pages", "add service pages") — clone the site's own `elementor_library` template rather than hand-authoring, write `_elementor_data` with `wp_slash()`, and never open the Elementor editor on a live site: `references/elementor-page-building-via-wp-cli.md` (header/nav styling is §9)
- **Access has been granted and the fixes are yours to apply** — locate the shared `elementor_library` template first, clear `_elementor_element_cache` or a correct fix keeps serving the old markup, and write `_elementor_data` through one dry-run-by-default script that re-reads and self-rolls-back: `references/elementor-fix-application-over-wpcli.md`
- **A widget renders nothing although the HTML is present** (a contact form that never appears, a booking widget, a popup). jQuery does not isolate event-handler exceptions, so one plugin throwing inside `elementor/frontend/init` silently kills every handler bound after it. Diagnose by blocking suspect scripts one at a time and re-measuring: `references/diagnosing-client-side-render-failures.md`
- `bot-walls` / SiteGround's `🐴 Robot Challenge` (HTTP 202 on every request including assets) and you have **SSH to the host**, build an SSH-fetched reverse proxy on localhost and rewrite absolute URLs, or the assets get ORB-blocked and you chase bugs that do not exist. **Without SSH, fetch the JS-rendered outer HTML through `api.microlink.io` instead** — it carries every head-layer, form and link-state check, and the routes that waste a pass are listed so you skip them: `references/bot-walled-site-browser-verification.md`
- **You are handed a staging build you did not write and asked to review it.** Indexability is a WordPress *option*, not a `robots.txt` line — `wp option get blog_public`, and set it to `0` before anything else — that also disables the WordPress sitemap, so an empty `/wp-sitemap.xml` on staging is expected rather than a finding, and it returns with `blog_public 1` at cutover; when the `noindex` tag is absent, check the option rather than hunting for a theme filter that strips it. Read `wp plugin list` in the same pass: it names the template kit the build came from (plus the form plugin, the importer, and any leftover admin users) before you have looked at a page. Access, WP-CLI recipes and the verification traps: `references/siteground-ssh-wp-cli-access.md`
- **You are asked to review every dealer site on the host as one piece of work** ("a summary review of just the car dealer websites for the coordinator and the platform owner", "what do we need to fix across the estate") — enumerate the host live, run one defect matrix, and deliver one document of P-numbered workstreams with owners and effort, not sixteen separate audits. Document shape: `references/dealer-estate-inventory.md` §5–§6; per-site matrix: `scripts/estate_survey.py domains.txt`. Count estate totals in code — the one figure that gets retracted is an absence claim.
- **Fixing a live PHP site over SSH** — backups outside the docroot, lint before upload, absolute scp paths: `references/live-php-server-edits.md`
- The user says "run the QA for [client name]"
- A client's site needs a functional audit before or after development
- **A dealer is complaining, handing in their notice, or asking "did we check this before it went live?"** — the deliverable is provenance, not another audit: whether the defect came with the build or with the dealer's data, and what the record actually shows about prior checks. The build mirror under `~/Documents/<project>/ftp-mirror/<domain>/` (stale `sitemap.xml`, missing `robots.txt`, seeded `data/*.json`, the launch email in `docs/`) settles the first; the session-DB window settles the second. Workflow and pitfalls: `references/defect-provenance-and-history.md`
- A batch of client sites is queued to go live and needs the standard SEO/QA pass before launch ("run the usual checks on all these new sites") — see `references/platform-audit-patterns.md`
- A batch build is moving to a new domain or host and the domain estate has to be untangled before anyone can build a canonical on it — see `references/domain-migration-and-ips-tags.md`. **Includes the case where the client says "the current URL is through <SaaS platform>"**: a merchant dashboard (Ecwid, Shopify, Wix) usually holds the catalogue and a domain *binding*, not the DNS — verify what actually answers on the domain, map the four control points, and release the store's binding before the DNS moves. **And check the mail layer in the same pass** — a nameserver change takes MX/SPF with it, and an in-zone `mx.` host disappears entirely (§8).
- A pre-launch `sitemap.xml` or `robots.txt` has to be regenerated off a staging host — `scripts/check-prelaunch-sitemap.py` both writes the corrected pair and fails loudly (exit 1) on dev-host references (`127.0.0.1`, `localhost`, `:81`, `:232`), so it can gate the go-live
- A the platform build is days from launch and the head-layer pass is done — run the deeper data-integrity sweep in `references/platform-data-integrity-checks.md` (soft-404s, stock-count and price claims, duplicate feed rows, consent/reCAPTCHA gaps, redirect-map harvest, and — on a build already live — sitemap staleness/malformed locs, the request-derived canonical, and how to verify a template fix in a scratch copy before deploying)
- **The head-layer sweep is clean and the build still has launch-blocking defects.** Titles, canonicals, OG tags and encoding all pass, and underneath them sit an unfinished primary CTA, a sitemap wrong in *both* host and URL shape, a pagination clamp, a second stock page, and a closed FRN record behind an "authorised and regulated" claim — every one of which a status-code and presence sweep scores as a pass. The checks that catch them: `references/prelaunch-defects-beyond-the-sweep.md`
- **A client's domain stops resolving, a site is unreachable, or their email has stopped working** — decide which layer is broken before anything leaves your notes: a domain that no longer resolves, a domain that resolves perfectly to a machine with nothing listening, or a mailbox host that is dead behind a healthy MX. Work the ladders in `references/site-down-triage.md`; the same reference covers the mail layer, and a `250 Accepted` from the MX does **not** mean the mailbox is reachable.
- **A site has just gone live and you are asked for a post-live check** — the launch pass and the post-cutover pass are two different jobs, and the second is where the configuration regressions hide: the canonical host, redirect-map coverage per URL shape, response headers that did not follow the file copy, and a staging host left crawlable while still nominating itself as canonical. Workflow: `references/production-live-site-patterns.md` → "After the cutover"
- **The map is only half built and you are asked for the redirects themselves** — "draft the redirect map" means produce the deliverable, not report coverage a second time. The old URL set comes from the Wayback CDX index (the outgoing site is often already gone), the vehicle patterns need a fingerprint guard or they swallow the live inventory, and the rules file has to survive Apache's parser: `references/redirect-map-construction.md`
- **The fixes are on a platform/template PHP build rather than WordPress** — no WP-CLI and no REST: edit the
  template, `php -l` it, upload to a temp name and rename, then verify the block's numbers against the
  site's own filters rather than against its markup. Mechanics: `references/post-qa-fix-workflow.md`
  §"The the platform PHP route"; file access and the `.htaccess` ordering trap: `platform-estate-deploy`. **Before patching, classify the site's template generation and use the proven four-file patch** — the dead `$pageTitle` after the header include, the `index.php` 404 guard, the `/sitemap.xml` rewrite plus deleting the stale file, and the `car.php` H1 — with the local `php -S` harness that proves it: `references/template-quick-fixes.md`.
- **The site is a JS/API app, not a CMS** (thin HTML shell, `js/*.js` modules, `/api/`): get endpoints from the modules, probe each unauthenticated, test any published demo login read-only — demo scaffolding live in production is a Critical. `references/api-driven-site-audit.md`
- You're checking a site across desktop and mobile breakpoints
- You need to track bugs across multiple sessions with fix status

**Don't use for:** SEO-specific audits (use `dsc-seo-audit`), GBP audits (use `dsc-gbp-audit`), or standalone copywriting (use `uk-car-dealer-copy`).

## Prerequisites

- Client's website URL (live and/or staging)
- Access via browser or web fetch tools
- A browser session where the client's site loads (for JS-dependent testing)
- The `/qa` command convention — say `/qa` to trigger a fresh QA pass, `/qa update` when fixes have been confirmed

## Procedure

### 1. Initial Pass — Scan Every Page Type

Visit every distinct page template:

- Homepage
- Stock / search / listing page
- Vehicle detail page
- About Us
- Contact
- Finance (if present)
- **Reviews / testimonials** — a page the template ships populated, so it reads as finished and gets skipped. Check it as content, not just as a page that loads.
- Any custom landing pages
- Privacy policy / terms

For each, check:

- **Layout:** no broken layout, content fits viewport, no horizontal scroll
- **Navigation:** all menus open and close, all links go to valid pages
- **Forms:** contact forms submit (note: may not be testable without actual submission), finance forms, call-to-action buttons
- **Content:** no placeholder text, no obvious typos or grammatical errors, no boilerplate that was meant to be customised
- **Demo scaffolding left live:** a build pushed public with its demo layer attached — published demo credentials that authenticate against the live API, seeded fixtures reported as live data, a "demonstration build" copyright line, `http://` serving without a redirect to `https://`. Test any published credential rather than merely noting it, and drive each role's sign-up: `references/api-driven-site-audit.md`
- **Images:** all load, alt text present, no stretched or distorted images
- **Vehicle spec fields:** all populated correctly (make, model, year, fuel, mileage, transmission, colour, doors, engine size, CO2)
- **Prices:** correct display, currency sign (£), no missing or obviously wrong figures
- **Finance:** correct broker named, correct APR/representative example if shown
- **Titles and headings (standing client rule):** vehicle detail and category pages must be *transactional*, not merely informative — `{Make} {Model} for Sale in {Town}` in the H1, title tag and meta description. A bare `{Make} {Model}` H1 is a finding even when the title tag reads well, and every `?make=` filter serving one generic title means no category page exists. Full rule, patterns and the length trap: `dsc-seo-audit` §3.

### 2. Record Findings

Each finding follows this structure:

```
### Finding N: [Brief Title]

**Page:** [URL]
**Severity:** Critical | High | Medium | Low | Info
**Expected:** [what the page should do]
**Actual:** [what it actually does]
**Evidence:** [quote, screenshot reference, or console error]
**Recommendation:** [how to fix it]
**Status:** Open | Fixed → verified | Confirmed resolved | Deferred
```

### 3. Mobile Breakpoint Testing

- Use a browser to test at ~375px width (mobile)
- **React/Javascript hamburger menus:** synthetic `.click()` may not work. Use CDP-level events (`dispatchEvent` with full MouseEvent sequence) or inject a `<style>` override to force the menu open (e.g. `body.menu-open nav { display: block !important; }`). See the a dealer/a dealer QA sessions for the established workaround.
- Check: tap targets are ≥ 48px, text is readable without zoom, forms are usable on mobile, no content hidden off-screen

### 4. Iterative Updates

- When a client confirms a fix is deployed, re-check the finding on the live site
- **Verify by value, not by presence.** Read the actual string — the canonical's `href` *and its host*,
  the real title tag, the served header — rather than testing whether the tag now exists. A presence
  test reports a fix closed while the value is wrong: canonicals appeared on all 10 pages of one build
  (presence ✓) with every one pointing at the *staging* host (value ✗), which is a worse defect than
  the missing-tag finding it replaced, because it now de-indexes the live site on cutover. **For a canonical or host question, the decisive check is the search engine's own index, not the tags:** `site:<domain>` and read whether both `www` and the bare host come back with the same pages. One build declared no canonical on any page, `www` answered 200 alongside the apex, and the index carried every page twice; a presence test on `<link rel="canonical">` would have reported the tag missing and stopped there, while the search result shows the damage the tag was supposed to prevent.
- **Where the defect is a duplicate value, assert the wrong one's ABSENCE — the right one being present proves nothing.** A footer can carry the correct number in the credentials line and the wrong one in the compliance paragraph a few lines away, so `page.count('<correct>') == 1` reads as fixed while the defect is untouched. Enumerate *every* match of the pattern (`\b\d{6}\b`, the tag name, the URL family) and print each one with its surrounding text, then require **zero** occurrences of the wrong value before closing the finding. The same shape applies to a duplicated rating, a duplicated opening-hours block and a superseded domain still linked from one template — any defect whose symptom is "both values are live on the same page" cannot be closed by a presence test.
- **Classify every re-checked item as fixed / still open / new — and expect `new`.** The fix for a
  Critical routinely creates the next one: a canonical added with the staging base, an opening-hours
  change that no longer matches the GBP listing, a `robots.txt` block written but left commented out.
  A pass that only confirms the original finding is gone misses all of it, and the re-check is the
  only place these surface before the client does.
- **A fix can be staged rather than applied.** A template change committed but not deployed, or a
  directive written into a file by hand, reads as done in the diff and is not live. Re-read the served
  output, not the change note.
- **A builder's "done" covers what is in their build, not the config that follows the domain move.**
  When the developer/template owner reports the work complete, expect the content and template items to
  be genuinely closed and the cutover items — canonical base, staging `noindex`, hardcoded host in
  share and finance links, server config — to be untouched, because those sit outside the build they
  own. Verify by category rather than by the headline claim, and say which categories were checked so
  "done" and "verified" are not conflated in the handover.
- **A finding can stop reproducing between the audit and the reissue, because the artefact regenerates itself.**
  A sitemap that is only rebuilt when something requests the generator will jump from "last written three
  months ago, 47 dead entries" to "today's date, all entries live" the moment anyone hits it — the staleness
  was the finding, and it silently fixed itself. Before re-quoting any count on a dated document, read the
  file's own timestamp (`MDTM` over FTP, `Last-Modified` over HTTP) and restate against the artefact that is
  there now; and keep the mechanism in the finding ("nothing schedules the rebuild") because that is the part
  that is still true.
- Update the finding status and note the verification date
- If the fix didn't work or created a new issue, note it and escalate
- Cross-session: the `/qa` command should pull existing findings from the session's history or a shared QA tracker; findings persist across `/qa update` calls

### 5. Deliver

Generate the QA report as .docx (branded with DSC header). Include:

- Summary: total findings by severity
- Full findings list ordered by severity
- Re-test log (findings that were fixed but re-checked)
- Deferred / out-of-scope items

Three references carry the rest — open the one that matches the job.

**Building and handing over the file** — `references/deliver-report-build-and-handover.md`: stamping the cover date from `date` and reconciling it against the `Audited:` line, verifying the built .docx/.pdf with their own parsers rather than a byte grep, the house renderer (`templates/build_report.py`) and the cover-block H1 trap, the attachment path check that decides whether a `MEDIA:` line attaches, and the informal internal-document voice.

**Choosing whose document it is** — `references/deliver-audience-variants.md`: the developer message (with its 6-part structure), the client report re-cut for a non-technical reader, the peer note between colleagues, Woody's disposition on every finding before the client version is finalised, and the email you send when the client says "send it to the developer yourself" — including evidencing the recipient address.

**Reissue, status and ownership** — `references/deliver-reissue-and-status.md`: the reissue pass (re-verify before re-dating, one copy on disk), turning the report into a status board once fixes exist, the one-upload subset when a deadline is attached, the reframing for an already-live site, anchoring deadlines to dates, owner labels, and establishing what is genuinely outside our reach before parking work on a third party.

## Pitfalls

Short rules and pointers, always on. The long entries are split out by theme below — open the linked file when its title applies.

- **Rendering claims and WAF access:** see `references/rendering-claims-and-waf-access.md`.

- **Verify layout findings by measuring, not eyeballing** — right edges vs `innerWidth` (not `scrollWidth`), sub-44 px tap targets counted. Visual defects (cropped, zoomed, overlapping): diagnose from the render, with a control pair — `references/visual-defects-and-rendering.md`.

- **Staging domains may behave differently from live domains** — a dealer's staging required fetching a parent listing page before detail URLs would load. Record any workarounds needed for each client.

- **FCA-regulated content** — if finance terms name the wrong credit broker or use incorrect regulatory wording, treat as Critical severity. See `dsc-fca-compliance`.

- **WordPress/Elementor template demo content left live is a recurring Critical** — check every page (especially About/Team and "Why choose us") for lorem ipsum ("a small river named Duden"), placeholder staff names, `+1 (859) …` phone numbers and `info@example.com`. Also check for the host's stock blog post (e.g. "WordPress Resources at SiteGround") published and in the sitemap.

- **On a client site, WordPress's default user surfaces publish the agency's own identity.** The users sitemap, the author archive and an unauthenticated `/wp-json/wp/v2/users` together disclose the build agency's email address and admin username. Check them on every build handed over, and note that the REST route map being public is normal WordPress and not itself a finding.

- **A 200 is not a pass, and its body is not proof of anything until you have diffed it.** Any unknown path served the homepage, unknown-path canonical included. Worth checking on every build: `curl` `/` and a junk path, diff the two, and read the head rather than inferring from the size delta.

- **Check nav vs body links separately** — a correct nav menu can sit above body service-card links pointing at 404 slugs (`/mot-testing/` when the real page is `/jlr-mot-testing/`). Test every internal href, not just the menu.

- **Soft-404s look like successes** — on PHP/template builds a missing `robots.txt` or `sitemap.xml` often serves the homepage with **HTTP 200** instead of a clean 404, so a status-code-only check reports "present". Confirm by inspecting the body (valid XML / `Disallow:` lines), not the code — and log the soft-404 as its own finding, since it also defeats uptime monitors.

- **Order a pre-launch batch by launch date, not finding severity** — pull the client-comms thread for the go-live dates before writing the priority list. A later status email can overturn the handover brief and invert the order (the site that looks most urgent may be months away). Where the comms live, and the himalaya search quirk that hides them: `references/platform-audit-patterns.md`.

- **CDP-verify behaviour, not screenshots**: consent gating, layout overflow, first-run state — `references/live-fix-and-verification.md`.

- **Internal docs: informal, first names, team voice (we/us)** — never "Prepared for: Name (Company)"; soften blame, own your own slips.

- **A pre-launch rebuild handed over as source on disk** (cloned from another dealer's template): serve it behind real Apache rather than `php -S`, replay the outgoing sitemap, and assign work by which files we can edit, not by who wrote them: `references/local-clone-build-qa.md`

- **UK spelling:** organise, colour, licence, behaviour, centre, practice (noun).

### Front-end behaviour and tooling

`references/pitfalls-frontend-and-tooling.md`

- **React hamburger menus are notoriously unresponsive to synthetic clicks**
- **Before reporting a mobile menu as broken, check whether the toggle is bound TWICE**
- **A measurement can be correct and still target the wrong element, or the wrong moment — two false Criticals in one pass**
- **Check what the CSS framework is, not just the head tags**
- **A form's markup in the page source proves nothing — count `<form>` elements in the rendered DOM**
- **A modal that opens blank is usually a framing header, not a broken endpoint**
- **Count `<form>` elements on the page the CTA actually points at, not on the site**
- **URL migrations leave stale URLs in two places**
- **Never open the Elementor editor on a live client site to change one value**
- **SiteGround Optimizer's combined CSS bundles carry absolute URLs, so a staging host outlives the migration**
- **Match HTML attributes quote-agnostically — WordPress and Elementor print single-quoted attributes, so a…**
- **Distinguish a UA-specific crawler block from rate limiting by testing several UAs inside the same minute**
- **Never trust a single failed status code**
- **Never `pkill -f "Google Chrome"` — it kills the Hermes-managed browser**
- **Check that every published email address can actually receive mail**
- **Probe the rendered PDF with `unicodedata.normalize("NFKC", …)` or a text check reports a fix as missing**
- **Prove the access before you promise the fix**
- **Look at the page you just patched, even when it is only on a local server**
- **`sips` renders a Chrome PDF's transparent page background as black, so a correct report looks like an illegible…**

### Hosts, URLs, launches and migrations

`references/pitfalls-hosts-urls-and-launch.md`

- **The staging subdomain is usually not the machine the site launches on**
- **Test whether the build is already on the live domain before accepting the brief's host labels**
- **Build the redirect map against a fingerprint, never against a path prefix**
- **Apache does not support inline comments after a directive, so a "helpful" annotation breaks the config**
- **A partially-working redirect set has two readings, and only probing by URL SHAPE tells them apart**
- **`/readme.md`, `/llms.txt` and the build's own docs directory are worth a direct probe**
- **Crawl the outgoing site the same day, before reporting a regression**
- **A sitemap can live at a non-standard path, so probe several before reporting "no sitemap" — then read what it…**
- **A served sitemap can be a static snapshot with the generator sitting unused, and a malformed URL hides the…**
- **When a defect is in the shared template, count the estate before writing it up — and check whether the site's own…**
- **Probe the exposure surface on every new build before writing the page-by-page findings**
- **A go-live date passing is not evidence the cutover happened, and the DNS can move under you mid-session**
- **A pre-launch check inherits two false assumptions: that staging is reachable, and that the launch host has the build**
- **You cannot diff a PHP file over HTTP — the request executes it, so every file looks months out of date**
- **Check whether every outbound CTA destination still exists — including off-site ones**
- **Never extract internal links with `href="/`**

### Content, claims, compliance and reporting

`references/pitfalls-content-claims-and-findings.md`

- **Check for cross-client contamination on any shared-platform build**
- **Feed copy arrives encoded, and both encoding faults publish code instead of characters — loop every VDP, then prove…**
- **Blank spec fields**
- **Yard descriptions are copy-pasted between a dealer's own cars, so read them as data**
- **A phone number on the site that belongs to another business is not necessarily contamination — check the dealer's…**
- **Grep for Latin filler by its word pattern, never for the literal string `lorem ipsum`**
- **A wrong contact address in a live contact block is High, not a copy nit — the misroute is silent at both ends**
- **Fabricated testimonials on the reviews page are their own Critical, not a copy nit**
- **Two Google Business Profiles for one business is a NAP finding, and it splits the reviews**
- **Test every filter parameter independently — one working filter proves nothing about the others**
- **Client marketing claims are findings, not colour**
- **The same promise written twice, differently, is its own finding**
- **A browse-by-X link block needs a coverage count, not just a link-health check**
- **A make-and-model H1 is informative; the client standard is transactional**
- **A fix applied by find-and-replace damages the copy around it — re-read the sentence, not just the string**
- **A claim removed in one phrasing survives in another — grep the concept, not the string**
- **A fix can create the obligation it was meant to satisfy**
- **An absence claim about company or FCA details must be measured across the page set, never the footer block alone**
- **A company name in a footer is a fact to look up, not a string to write**
- **Extraction-tool mojibake is a false-positive trap**
- **Text you stripped out of the HTML is not necessarily visible on the page — strip `<!-- … -->` before you strip tags**
- **The output pipeline redacts secret-shaped strings, so extracted code can look corrupted when the file is fine**
- **A status-code sweep cannot see data-integrity bugs**
- **Derive the page set for any "N pages do X" claim from the crawled URL inventory, not from the templates you…**
- **A headline figure is duplicated across four artefacts — correct all of them in one pass**
- **A finding you have to retract spreads further than a count does — and a retraction needs a visible correction…**
- **Precompute a regex result before putting it in an f-string**
- **Client-confirmed fixes may not survive a site rebuild or cache purge**
- **Never record an identifier as present on a bare digit pattern — anchor it to its label and print the surrounding text**

## Verification

- [ ] Every page type visited and checked
- [ ] Findings recorded with severity, expected vs actual, evidence, recommendation, and status
- [ ] Mobile breakpoint tested for all critical interactions
- [ ] React hamburger menu tested (including CDP-level workaround)
- [ ] Vehicle spec fields spot-checked on at least 2 detail pages, **then every VDP looped for null-rendered values (`Unlisted`, `N/A`) and for description copy contradicting the car it sits on**
- [ ] Finance wording checked for correct broker name
- [ ] Vehicle detail **and** category pages carry transactional titles/headings (`{Make} {Model} for Sale in {Town}`), with a second filter tested
- [ ] Exposure surface probed — every `robots.txt` `Disallow:` entry status-checked, and what the 200s leak recorded
- [ ] Staging indexability settled at the WordPress level on any pre-launch build (`wp option get blog_public` returns `0`), not only via `robots.txt`
- [ ] Privacy notice reachable (page exists *and* is linked), company details render on every page rather than one footer, and any tracker present has a consent mechanism
- [ ] On any domain or hosting move: registrant/account holder established (whois is redacted, the registrar of record may be wholesale), and every MX/SPF record identified — including in-zone mail hosts — and recreated at the new registrar before the nameservers change
- [ ] Re-checked fixes classified fixed / still open / new, each verified by value (canonical host, actual title string, served header) rather than by the tag's presence
- [ ] Every item assigned to the platform owner can be shown to sit in a file or system we cannot reach — not merely in code someone else wrote
- [ ] Report generated as branded .docx