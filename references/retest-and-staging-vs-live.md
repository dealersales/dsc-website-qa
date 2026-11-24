# Retest & Staging-vs-Live Workflow

Proven on a dealer Car Sales (Sep 2026) — the platform staging build at
`<dealer>.platform-host` replacing a live WordPress site at
`<dealer-domain>`. The recheck pass found 19 of 24 findings fixed
in one pass; the staging-vs-live comparison eliminated 3 false Criticals.

## Retest after developer fixes

When a developer (the platform owner at the platform, or anyone) says "all corrections are done":

1. **Re-fetch every page** with the same `curl -sL` method from the initial pass.
   Do not trust `web_extract` — it renders text, not raw `<head>` tags. You need
   `curl` to see meta descriptions, canonicals, OG tags, JSON-LD blocks,
   favicon links, and title tags.
2. **Run one programmatic check per original finding**. Build a script that
   regex-matches each finding's signal (e.g. `re.search(r'<meta\s+name=["\']description["\']', html)`
   for Finding 1, `re.search(r'href=["\'].*icon.*["\']', html)` for favicon, etc.).
   Print ✅ Fixed / ❌ Still open per finding in a single pass.
3. **Report as a table** — one row per finding, columns for status and notes.
4. **Check for bonus improvements** — the developer may have fixed things not
   in the original audit (VDP titles improved from reg number to model name,
   JSON-LD enhanced with `numberOfDoors` / `vehicleEngine`, additional spec
   fields like Body Type / Engine Size / Doors added). Acknowledge these.

### Findings that are typically staging-specific (check live before reporting)

These commonly fail on a platform staging subdomain but already work on the
client's current live site:

| Finding | Why it's staging-specific |
|---------|--------------------------|
| No HTTP→HTTPS 301 redirect | Live domain usually has it; staging subdomain may not |
| No robots.txt | Staging may not have one; live usually does |
| No canonical tags | Staging PHP build may omit; live WordPress may have them via Yoast |
| Server/X-Powered-By header leak | Different server stack on staging vs live |
| Missing security headers | Different Apache/LiteSpeed config on staging vs live |

Always `curl -sI` the live domain and compare before flagging these as Critical.

## Staging vs live URL structure differences

the platform staging builds use PHP query-string URLs:
- `vehicle.php?id={32-char-hex-hash}`
- `vehicles.php`, `about.php`, `contact.php`, etc.

The live WordPress site uses clean permalinks:
- `/vehicles/{make}-{reg}/`
- `/vehicles/`, `/about-us/`, `/contact/`, etc.

When comparing stock counts between staging and live, the vehicle slug lists
will differ in format but should match by registration number or vehicle identity.

## Stock count recheck against AutoTrader

AutoTrader blocks `curl` — a `curl -sL` to an AT page returns a near-empty
HTML shell with no stock data. Use `browser_exec` (Browser Use CLI) to:

1. Navigate to the AT dealer stock page:
   `https://www.autotrader.co.uk/cars/retailer/stock?sort=desirability-desc&page=1&retailerId={ID}&advertising-location=at_cars`
2. Read `document.body.innerText` — the stock count appears as "X results" and
   each car listing shows make, model, price, mileage, location.
3. Cross-reference each AT car against the staging/live vehicle list by price
   and mileage (prices should match exactly for all cars that appear on both).

The AT dealer profile page also shows "Used cars (N)" — this is the definitive
stock count. Navigate to the dealer profile URL to see it.

## GBP verification: email vs video

When a client's GBP is claimed but not verified:

1. **Check if email verification is possible** — run `dig +short MX {domain}`.
   If no MX records exist, email verification is not possible unless the client
   sets up email forwarding (Namecheap Private Email or ImprovMX can forward
   `info@{domain}` to their existing Gmail).
2. **Video verification** is the fallback — takes 1–5 business days for Google
   to review. The client records a video of the business premises and uploads
   it through the GBP verification flow.
3. **Once verified**: photos can be updated, reviews can be replied to, posts
   can be created, and edits become visible to customers.
4. **While in GBP manager**: check opening hours match across GBP, AT, and the
   website. NAP discrepancies between GBP and directories are the #1 local
   ranking factor.

### Namecheap email forwarding + Gmail DMARC trap

If the client sets up Namecheap email forwarding (`eforward*.registrar-servers.com`
MX records) to forward `info@{domain}` to a Gmail address, **Gmail will likely
silently drop the forwarded email**. This affects GBP verification codes AND
any future contact form submissions forwarded to Gmail.

**Root cause**: Namecheap's basic email forwarding does NOT rewrite the From:
header (no SRS — Sender Rewriting Scheme). When an email from
`paul@example.com` is forwarded to `client@example.com`:

1. Email arrives at Namecheap from `paul@example.com`
2. Namecheap forwards it to `client@example.com` with the original From: header intact
3. Gmail checks DMARC alignment — the forwarding server (Namecheap) is NOT in
   `example.com`'s SPF record
4. Gmail silently drops the email — no bounce, no spam folder, just gone

**Confirmed Sep 2026**: a dealer Car Sales set up Namecheap email forwarding
for `info@<dealer-domain>` → `<dealer-email>`. MX records
correct (`eforward1-5.registrar-servers.com`), SMTP servers accepting mail
(verified via `nc` / Python `smtplib`), but test emails from
`paul@sales-consultants.com` never arrived in Gmail. No bounces either.

**Fixes**:
- **Namecheap Private Email** (~91p/month): real mailbox at `info@{domain}`,
  accessed via webmail or mail client. No forwarding = no DMARC issue. Change
  MX records to `mx1.privateemail.com` / `mx2.privateemail.com`.
- **Video verification**: skip email entirely, use video verification through
  the GBP flow (1–5 business days).
