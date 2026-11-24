# Auditing a JS/API-driven site

Applies when the target has no CMS: the page HTML is a thin shell, behaviour comes from `js/*.js` modules, and an `/api/` serves the data. The dealership-site procedure in SKILL.md assumes a rendered page; on an app like this the page-by-page pass finds almost nothing and the real findings sit one layer down.

## Why the normal crawl is not enough

Page-extraction tools return rendered copy. On a shell homepage that leaves a handful of words, and the head layer, the module scripts and the endpoint map are all stripped. Byte size is the first signal: a homepage of 2–4 KB is a shell, and its visible word count is the whole of its indexable content.

## Procedure

1. **Raw-fetch every page.** `curl -sS -o page_<name>.html -w "%{http_code} %{size_download}\n" <url>` across the routes, plus `robots.txt`, `sitemap.xml`, `manifest.json`, `.git/config`, `package.json`, `.env`. A branded 404 body is normal; what matters is whether the file exists at all.
2. **Enumerate routes from the app, not the nav.** The header/footer are usually JS-injected, so read the module that builds them — `NAV_BY_ROLE`, footer column definitions — and curl every href it lists. A footer link to a page that 404s is a live defect no rendered-page check surfaces.
3. **Inventory the API.** Download `js/api.js` (or equivalent) and read the exported client: it is a method → path map, including endpoints no UI exposes. Then `grep -rn "fetch(\|/api/\|api\." js/` for hand-rolled calls. The same file reveals the payload shapes, which saves a false bug report later.
4. **Probe every endpoint unauthenticated.** For each: status, content-type, and whether real data comes back. Highest-value on this shape of app:
   - `GET /api/config` — pricing internals, feature flags, sometimes third-party keys.
   - `GET /api/<entity>/locations` or any "live" feed — named individuals' real-time GPS.
   - `GET /api/<resource>/<public-id>` — an IDOR when the id is guessable or public (number plate, short tracking code). Compare what the JSON returns against what the UI chose to hide: `showAddress: false` in the renderer is not redaction on the server.
   - `POST /api/auth/register` — does it take `role` from the client?
   - `GET /api/admin/*` — repeat every admin call with no cookie. 401 is the pass; data is the finding.
5. **Test the credentials the site publishes.** A demo-account panel on a live login page is a vulnerability, not a design note. Sign in, enumerate what the role reaches read-only, and stop there — no writes, no deletes, no password resets. Record that the reset endpoint exists and what it would allow; never put secret values or full PII in the report, and never leave test records behind.
6. **Look for seed data presented as production.** Tells: a copyright line reading "demonstration build", 555 or sequential phone numbers, accounts named after the demo persona, a "Live" badge over a position weeks old, every record sharing one creation timestamp, an ETA computed from a stale fix.
7. **Drive each role's registration through the UI.** One form usually serves every role and the payload may hard-code one of them, so a "Create <role> Account" heading can post a different role entirely and demand a field hidden from that user. Submit and read the validation error — aim for the branch that fails before the network call.
8. **Canonical and redirect hygiene, proven twice.** Curl `http://`, `https://www.`, and `/index.html`: 200 on all three means no redirect and no canonical. Then search `site:<domain>` — the indexed URL variants (`http://…/index.html`, `https://www.…`) are the evidence to quote, and they show the SERP already split across hosts.
9. **Cookie and header posture.** `Set-Cookie` flags come from CDP `Network.getAllCookies` after a login (`httpOnly`, `secure`, `sameSite`, expiry) — some harnesses mask the header entirely. Read response headers for HSTS, redirects, `X-Frame-Options`, CSP; read the certificate SANs with `openssl s_client -connect <host>:443 -servername <host> | openssl x509 -noout -text` — a cert named for `mail.<domain>` usually still carries the apex, so confirm before claiming a mismatch.
10. **Weight and caching.** Sum the assets and check `content-encoding` with an `Accept-Encoding` request. A hand-written app is often 70–80 KB in total, which is a finding worth stating positively so the client knows what not to break.

## False-positive guards (these apply to every QA pass, not just API apps)

- **Drive the UI before calling any feature broken.** A hand-built API payload is a guess at the contract; the UI passes resolved objects (coordinates, town, ids) that the client code never documents. If the UI produces the result, the feature works and the payload was wrong.
- **A blank map, iframe or embed on the first screenshot is load timing, not a defect.** Re-capture after ~8 s and look for the provider's DOM nodes (`.gm-style`, `canvas`) before writing it up.
- **Cross-check DOM anomalies against raw HTML.** `document.title` and `innerText` carry harness and browser injections; if a `grep` of the downloaded source does not contain it, the site did not put it there.
- **Clear cookies between role and login-form tests.** `Network.clearBrowserCookies` first, or a session left over from an earlier demo login bounces `/login.html` straight to the dashboard and the form you meant to test never appears.
- **A dead-looking button may be missing configuration, not missing code.** Re-test the endpoint it calls before writing it up: `{"error":"Vehicle lookup is not set up"}` from `/api/<service>/lookup` is an unconfigured key, and the fix is a decision for the owner rather than a defect in the handler.
- **Confirm the status code, not just the content.** A 404 served with a designed error page still reads like a working page in an extraction; check `%{http_code}` before deciding a route exists.

## Reporting shape

Severity first, evidence second, commercial consequence third. Each Critical carries the exact request and the shape of the response (values redacted), then what an attacker or a customer does next, then the fix. On a booking or lead-generation app every technical hole also has a revenue side — an impossible signup, a dead lookup button, a margin printed on the customer's own quote — and stating it is what makes the report actionable rather than a scanner dump.
