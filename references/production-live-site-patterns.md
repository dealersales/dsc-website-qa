# Production Live-Site Audit + Go-Live Verification (the platform/DSC builds)

Observed auditing `<dealer-domain>` at go-live (Sep 2026). Complements
`platform-audit-patterns.md`, which documents the STAGING build
(`<dealer>.platform-host`). The production DSC build is a different beast:
SEO fundamentals are usually present. Audit the live domain separately from staging.

## Go-Live Verification Workflow (use when a dealer site "goes live")

When DNS is repointed to a new server (developer says "point A-records to X"):

1. **DNS**: `dig +short <domain> A` — confirm it now returns the new IP.
2. **HTTP**: `curl -sI -o /dev/null -w "%{http_code}" http://<domain>` — expect 200.
3. **HTTPS**: `curl -sI --max-time 10 -o /dev/null -w "%{http_code}" https://<domain>` —
   expect 200. Exit `000` + `SSL Verify: 1` means cert not live yet.
4. **Cert details**: `echo | openssl s_client -connect <domain>:443 -servername <domain> 2>/dev/null | openssl x509 -noout -subject -issuer -dates`
   — confirms Let's Encrypt/issuer and validity window.
5. **Redirect**: HTTP should 301 → HTTPS once the cert is up.
6. **Key page smoke test**: fetch homepage + showroom; confirm stock renders and any
   promised feature (e.g. "cars for sale by make" footer counts) is present.

**Pitfall — canonicals can point to https:// before the cert exists.** the platform owner uploaded
code whose canonical/OG/schema/sitemap URLs were already `https://` while the SSL
cert was not yet installed on the new server. Until the cert is live, Google cannot
crawl the canonical URLs at all — worse than an http:// canonical. Verify HTTPS
FIRST, then check canonical scheme matches what actually serves.

**Pitfall — SSL is often enabled minutes-to-hours after the developer says "done".**
a dealer's cert (Let's Encrypt) appeared during the audit session, after the initial
TLS handshake failed with `tlsv1 alert internal error` (alert 80). If HTTPS fails at
first check, schedule a re-check (e.g. cron one-shot next morning) rather than
immediately chasing the developer.

**Workflow pattern — "check again in the morning before going back to the platform owner":**
Woody's standing preference for chasing developers on infra fixes is to verify
independently first, and only escalate if the fix hasn't landed. Use a one-shot cron
job scheduled for the next morning that runs the DNS/HTTPS/cert checks and reports
"fixed — no need to chase" vs "still broken — chase developer". Remove the job once
resolved (do not leave one-shot jobs firing).

## After the cutover — re-verify on the host the customers actually reach

The go-live checks above prove the site is **up**. These prove it is **correct**, and they are a
separate pass: the copy carries the files, not the config, so a build verified on staging can regress
the moment it moves.

- **Diff the response headers between the staging host and the live host, header by header.** A vhost
  setting does not travel with the code, so a header present through the whole staging life can simply
  be missing in production. One build lost `Strict-Transport-Security` in the move — staging sent
  `max-age=31536000; includeSubDomains`, live sent none — while every other security header survived,
  so a blanket "security headers present" check passes and the regression hides. Read the full set off
  both hosts and compare them explicitly.
- **Confirm the canonical reads the live domain, on every page — and check the other places the host
  is written.** The pre-launch fix lands in the build; verify it survived the copy rather than assuming
  it did. The hardcoded host hides in more than the canonical tag: `og:url`, every JSON-LD `url`/`@id`,
  the WhatsApp/share enquiry text and a finance plugin's `linkBackUrl`. Grep the served page for the
  staging hostname and require the count to be **zero**.
- **Test the redirect map by URL shape, not by spot-check.** See the SKILL.md pitfall — a map can
  cover the keyworded landing pages and nothing else, and the family that 404s is the one carrying the
  indexed URLs.
- **Check what the staging host is doing now.** After cutover a still-live staging host is not merely
  duplicate content: if its canonical still points at itself it is a second full copy *claiming* to be
  the canonical version, competing with the site just launched. Read its `meta robots`,
  `X-Robots-Tag` and its own canonical `href`, then get it taken down or noindexed.
- **Confirm the tracking ID carried over.** Reusing the outgoing site's analytics property is what
  preserves the client's history through a domain move — check it is still present on the live host,
  and note that while the old site and the new one are both answering, the two double-count.
- **Re-run the stock counts and any price/range claim against the live host.** Stock moves between the
  pre-launch audit and cutover, so a figure that was accurate on staging can be wrong on launch day.
- **Anchor every verdict to the host it was measured against.** A "fixed" verdict taken on a host no
  customer is reaching is not a verification. Name the host in the report, and re-confirm resolution at
  write-up time — DNS can move under you mid-session.

## Production Build Observations (<dealer-domain>, Sep 2026)

Things the production DSC build DOES have (vs the raw the platform staging build, which
lacks them — see platform-audit-patterns.md):

- Meta descriptions, canonicals, Open Graph/Twitter tags on every page — all https://
- Homepage JSON-LD: Organization + AutoDealer (NAP, geo, opening hours) + WebSite
  with SearchAction. VDPs have Vehicle schema + BreadcrumbList.
- `robots.txt` present and deliberate: allows Google + AI citation bots
  (OAI-SearchBot, ChatGPT-User, ClaudeBot, GPTBot, Google-Extended…), blocks
  CCBot/Bytespider, disallows `/cache/`, `/ajax-models.php`, `/enquiry.php`.
- `sitemap.xml` present, includes all vehicle.php URLs (hash IDs) + static pages.
- `llms.txt` present (LLM-friendly summary with key pages + NAP).
- FCA disclaimer present on VDPs: "is a credit broker, not a lender. Finance is
  subject to status…" — correct pattern.
- Static pages: About/Contact/Warranty/Sell/Privacy each have title + meta + one H1.
  VDP H1 includes make/model ("BMW 1 Series for sale").
- Social links exist but only on the Contact page — header/footer `.social-icons`
  containers are empty.

### Findings observed (likely to recur on other production DSC builds)

1. **"Finance" buttons `href="#"`** — dead CTA on every homepage carousel card.
   Browser pass over `document.querySelectorAll('a.button')` confirms. High severity:
   lost finance enquiries. (Also captured in SKILL.md pitfalls.)
2. **Old WordPress-style URLs 404 after rebuild.** Previous site used `/about-us/`,
   `/sell-your-car/` etc. New build uses `about.php`, `sell.php`… Old URLs return
   404 with no 301 redirect. Google still shows the OLD indexed snippet containing
   another dealer's name ("At Blakewater Cars…") — the recurring wrong-dealer-name
   issue survives in the SERP even after the live copy is fixed. Fix: 301 old →
   new URLs; resubmit to GSC. **Check legacy URL patterns on every rebuild.**
3. **NAP mismatch with Auto Trader**: website "Unit 4, 10 Chancellor Street" vs AT
   dealer page "5 Chancellor Street" (LS6 2TE same) vs Companies House registered
   office at a different site entirely (Gemini Business Park, LS7 3JB — legal office,
   may be fine). Flag website-vs-AT mismatches; confirm physical address with dealer.
4. **Empty `"color":""` in Vehicle JSON-LD** while page renders fine → feed mapping
   gap at the platform level (also in SKILL.md pitfalls).
5. **VDP H1 styling**: `<h1>` with inline `background:#1e1e1e; color:#fff` and a
   nested white `<span>` — harmless but sloppy inline styling; whitespace-heavy
   source (parser must collapse whitespace before reading the H1).
6. Homepage carousel may list fewer vehicles than showroom/footer counts (10 in
   carousel vs 13 on showroom) — carousel is a subset; don't flag as missing stock.
7. Contact page `<form>` uses `wpcf7-` classes but posts to `thank-you.php`
   (custom PHP, not actual Contact Form 7 / WordPress) — verify the POST target
   exists (301 → 200) rather than assuming CF7 processing.

## Audit technique notes

- Use `curl -sL` + python regex over saved files for `<head>` metadata (web_extract
  strips it). Save each page to /tmp as you go; parse repeatedly without re-fetching.
- When the site is mid-deploy, prices/content can differ between fetches minutes
  apart — always take a fresh final fetch before recording results.
- The homepage "listing-box" regex must collapse whitespace; `Our Price` label and
  the following `<span>` can both contain `£` (yields `££` in naive captures).
- Footer "Used Cars For Sale" make-count links (e.g. "4 Land Rover for sale") are a
  handy live count of total stock — cross-check against showroom listing count.

## Making fixes on a live client site with no staging

When the site is already live and there is no staging to work on, the pass is: back up, edit the specific
file, lint, upload, then verify by fetching the live page — never by trusting the upload.

- **Access.** Hostinger SSH is on **port 65002** with the same credentials as FTP, and sites sit at
  `~/domains/<domain>/public_html`, one docroot per domain. Do not assume a shared codebase across the
  estate: the same template is copied per site and drifts.
- **Backups go outside the docroot.** `~/backups/<client>-<date>/`, mirroring the tree. A `.bak` file left
  in `public_html` is a published file — `.bak` is not in `robots.txt`, Apache serves it, and a
  `config.php.bak` is a credential disclosure. Fetch one afterwards and require a 404.
- **Lint before uploading.** There is no system PHP locally; use the static CLI at
  `~/.local/php-static/php -l <file>`. A syntax error scp'd onto a live site is an outage.
- **The repo is not a deploy artefact.** Sites in the dsc-websites repo were sanitised with
  `REDACTED-RUN-ON-SERVER`, so pulling or copying the repo over a live site breaks credential paths. Edit
  the server, commit afterwards.
- **Build a pass/fail harness and re-run it after every fix.** A dozen checks against the live domain
  (sitemap host, 404 behaviour, redirect families, canonical host, privacy link, analytics ID, head tags)
  turns "fixed" into a number, and makes a regression visible immediately. **Prove each check can fail** —
  a regex that matched `9.9% APR` but not `APR 9.9%` reported a clean pass on a live defect. When the
  site's scope changes, rewrite the checks to test the new truth rather than leaving stale ones passing.

### Two Apache ordering traps

- **An existing static file is served before any `RewriteRule`.** Routing `/sitemap.xml` to a generator
  does nothing while a `sitemap.xml` file is present — the rule never runs, so a stale sitemap keeps
  being served and looks "fixed" in the repo. Delete the static file *and* add the rule.
- **A stale clean-URL rule above your redirect wins.** Removing a page leaves rules like
  `RewriteRule ^finance$ finance.php [L]` pointing at a deleted file, so `/finance` 404s while
  `/finance.php` correctly redirects — a partial fix that looks like a caching problem. Grep `.htaccess`
  for the page name, delete the old rule, then test **both** the extensionless and `.php` forms.

### Removing a product or service from a site

One page is never the whole job. Sweep every layer, then prove it with a grep:

1. the page and its wrapper → 301 to the nearest surviving page (contact is usually right)
2. shared header/footer: **nav often lives in two arrays** (mobile and a desktop "More" menu), plus the
   footer disclaimer, plus any modal markup **and** the script block that drives it
3. homepage: services tiles, feature sections, FAQ entries, why-choose cards — retitle a card that still
   has a survivor concept ("Finance & Part Exchange" → "Part Exchange") rather than deleting it
4. templated pages: every block that quotes it (monthly figures, the CTA, the representative example)
5. config/meta: both meta descriptions, schema and service lists
6. the privacy notice: the section **and** the rows it contributed to elsewhere (what we collect, lawful
   basis, sharing, retention)
7. the sitemap generator's page list
8. orphaned handlers and unreferenced duplicate templates that still carry the copy

Verify with `grep -i <term>` on the homepage, a templated detail page, the privacy page and the sitemap —
all must be **0** — and confirm every retired URL 301s.

**Distinguish selling the product from administering the customer's existing one.** "We settle outstanding
finance on your part exchange" is not an offer of finance; deleting it wrongly implies a financed car
cannot be part-exchanged. Keep it and flag the judgement to the client rather than silently removing it.

### Installing analytics behind consent — and proving it fires

- Load the tag **only after consent** rather than shipping consent-mode-denied by default; that is the
  stricter PECR reading and what the client's banner copy then describes. Say so if they later want
  modelled data.
- **Prove it with a collect beacon, not a script tag.** The page containing `gtag` proves nothing — the
  loader may sit behind a consent flag. Over CDP: enable `Network`, click Accept, drain events, then look
  for `googletagmanager.com/gtag/js?id=G-…` **and** `region1.google-analytics.com/g/collect?…tid=G-…`.
- **Drain the event stream after the click.** The beacon lands after the eval returns; a fixed sleep with
  no draining shows zero collect calls and reads as a failure when the tag is working.
- Check the returning-visitor path too: consent already stored, tag loads on page load, no banner.
- The outgoing site's property is often **Universal Analytics** (`UA-…`), which stopped processing in
  2023 — there is no history to inherit, so a new GA4 property is the only option.

### Layout overflow: `scrollWidth` lies on most of these builds

`document.documentElement.scrollWidth > innerWidth` is the standard horizontal-scroll check and it returns
a **false pass** wherever the site carries `html, body { overflow-x: hidden }` (commonly paired with
`* { max-width: 100% }`): the overflow is clipped, not scrolled, so the document never widens. A primary
CTA sat 146px outside the viewport on a build every width check called clean.

Measure **element right edges against `innerWidth`** — for each header `a`/`button` with non-zero width,
`getBoundingClientRect().right` — at several widths (1024/1100/1200/1280/1366/1600), because the failure
band on a laptop-width nav is narrow and one width misses it. Test candidate CSS by injecting it over CDP
and re-measuring before writing it into the build, and prefer **tightening spacing** over hiding a control:
removing a secondary button often fixes the row but leaves a viewport band with no instance of that channel
(a floating WhatsApp button is frequently `lg:hidden`).

### Published email deliverability

Check MX on the domain of the **published** address, not the site's own domain — a site can publish an
address whose mailbox exists while carrying no MX at all, and the reverse. After swapping an address,
re-check the enquiry handler's config key and the JSON-LD `email`, and grep every page for the old one.
