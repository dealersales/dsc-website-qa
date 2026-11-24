# Verifying fixes on a live site

A fix you have not re-measured is a claim. Once a site is live and you are patching it over SSH,
build a small harness that runs the checks against the live host and exits non-zero on failure, so
every fix is proved and every regression surfaces immediately.

## The harness

One script, `check_<client>.py`, ~20 checks, `PASS`/`FAIL` per line plus an evidence line under `-v`,
and a final score (`18/22 checks pass`). Keep it with the audit, not in the site's repo.

Checks that earned their place:

| Area | Check |
|---|---|
| Sitemap | content type is XML; every `<loc>` is on this domain (count hosts, do not eyeball); vehicle URLs present |
| robots.txt | `text/plain` and a `Sitemap:` line |
| 404 | unknown path returns 404; the 404's head does not contain the requested path |
| Redirects | one URL from each outgoing family returns 301, not 200 |
| Canonical host | apex and www resolve to one host, one of them by 301 |
| Email | the **published** address's domain has MX (not the site's domain) |
| Privacy | page exists and is linked from the homepage |
| Consent | banner string present in the page |
| Analytics | a real `G-[A-Z0-9]{8,}` measurement ID is configured |
| Contact | trading address and phone render |
| Head | no keywords meta; `og:image` absolute; viewport allows zoom |
| Finance | page copy does not contradict the finance module's rate |

## Traps that produce false passes

- **Grep for the loader string scores analytics as present when nothing loads.** A consent-gated
  loader contains `googletagmanager.com/gtag/js` in its JS whether or not an ID is set. Assert on a
  real measurement ID (`G-[A-Z0-9]{8,}`), not on the presence of the word.
- **After canonicalising to www, every path check against the apex sees a 301.** A harness with
  `follow=False` then reports "no 404" and "privacy page missing" for a site that is fine. Point all
  path checks at the canonical host and test the apex separately as its own redirect check.
- **A soft-404 router makes status codes meaningless.** On a build that serves the homepage with 200
  for unknown paths, `/assets/css/output.css` answers 200 with tens of KB of HTML. Judge by body
  content for every "does this exist" question until a real 404 is in place.
- **Fix the harness when it disagrees with reality — and check you have not written a check that
  cannot fail.** Both mistakes happened in one session: an APR regex that only matched `9.9% APR`
  and not `APR 9.9%`, and an analytics check satisfied by the loader string.

## Measuring overflow (the clipped-CTA class of bug)

`document.documentElement.scrollWidth` proves nothing on a site that ships
`html, body { overflow-x: hidden }` or `* { max-width: 100% }` — the document never grows, the wide
row is clipped, and a scrollWidth check reports a pass while the CTA is cut off on screen.

Measure **element right edges against `window.innerWidth`**:

```python
js("""(() => { let worst=0,label='';
  document.querySelectorAll('header a, header button').forEach(el=>{const r=el.getBoundingClientRect();
    if(r.width<1)return; if(r.right>worst){worst=r.right;label=(el.textContent||'').trim().slice(0,14);}});
  return {worst:Math.round(worst),label,inner:window.innerWidth};})()""")
```

Drive it over CDP: launch the real Chrome with `--headless=new --remote-debugging-port=PORT`, connect
with `websocket-client` (present on this machine), `Emulation.setDeviceMetricsOverride` per width, then
`Runtime.evaluate`. Take the widths where the design breaks and the ones either side of it — a header
usually fails at the *bottom* of a breakpoint range, not at every width.

**Test the candidate fix before deploying it.** Inject a `<style>` element with the proposed media
query, re-measure, and compare slack. This caught that tightening the nav alone left the CTA 18px
over at the narrowest width, and that hiding the WhatsApp button would have removed WhatsApp entirely
because the floating button is `lg:hidden`. Only then write the rule into the site.

## Consent-gated analytics: prove it fires

Server HTML cannot show this — the tag is injected on acceptance. Capture network traffic instead:

1. `Network.enable`, navigate, confirm the banner is visible and `typeof window.gtag === 'undefined'`.
2. Click the accept button via `Runtime.evaluate`.
3. **Drain events for several seconds after the eval returns** — the collect beacon lands later, and a
   listener that stops at the next command response records zero calls.
4. Assert both: `googletagmanager.com/gtag/js?id=<ID>` and a `/g/collect` request whose `tid=` is the
   measurement ID.
5. Re-run with the consent already stored to prove the returning-visitor path.

## Live-editing over SSH

- **An existing static file beats a rewrite.** Apache serves `/sitemap.xml` before any `RewriteRule`
  matches it, so routing `^sitemap\.xml$` to the generator does nothing while the old file sits there.
  Delete the file first, then add the rule.
- **Never leave `*.bak` files inside the webroot.** A backup of `config.php` is a credentials file
  served as plain text to anyone who guesses the name. Copy them to `~/backups/<site>-<date>/` outside
  the docroot and confirm the old path returns 404.
- **Any schema or canonical built from `REQUEST_URI` must be suppressed on a 404**, or the 404 page
  nominates its own junk URL as canonical and as `url` in JSON-LD. Wrap the block in the same
  `$is404` guard as the canonical tag.
- **Check what the rule ordering protects.** A `RewriteRule ^servicing$ index.php` ahead of the
  catch-all means that path legitimately lands on `index.php`; whitelist it in a new 404 guard rather
  than letting the guard turn a working page into a 404.
