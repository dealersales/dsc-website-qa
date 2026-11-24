# Applying and verifying fixes on a live site

For jobs where the build has no staging and fixes go straight to production, and the result has to be
proved rather than assumed. Covers the access check, the backup discipline, the deploy mechanics that
bite, and scripted verification of behaviour that a screenshot cannot show.

## 1. Look for access before asking for it

Before writing "I need access", check what already exists: `~/.ssh/config`, the Keychain
(`security find-generic-password -s <label>` returns attributes without the secret), and the site
repo's own README. An access request that duplicates a credential already stored costs a day and makes
the agent look like it has not read its own notes.

- Hostinger accounts answer SSH on **65002**, not 22, with the same username/password as FTP. Probe
  with `nc -z -G 8 <ip> 65002` rather than assuming FTP-only.
- Sites live at `~/domains/<domain>/public_html`.
- **A 403 on every path across every sibling vhost is an IP allowlist, not a broken site.** Probe two
  or three siblings before reporting one site as down; the finding and its owner are different.

## 2. Back up outside the webroot

Taking `cp -a file file.bak-<date>` and leaving it there publishes the file: `foo.php.bak` is
downloadable by URL, and a backup of `config.php` hands over every credential in it. Move backups out
of the docroot in the same step:

```bash
mkdir -p ~/backups/<site>-<date> && mv <path>/*.bak-<date> ~/backups/<site>-<date>/
```

Then prove it: request the old backup path and require 404. Do the same sweep for `.sql`, `.zip`,
`.orig` and `- Copy` files left by whoever built the site.

## 3. Uploading: the `~` trap

```bash
R=user@host; D=~/domains/example.co.uk/public_html
scp file "$R:$D/file"        # WRONG - ~ expanded on the local machine
scp file "$R:/home/<user>/domains/example.co.uk/public_html/file"   # correct
```

A local variable holding a remote path expands `~` locally, so scp reports `No such file or directory`
for a path under your own home. Use the absolute remote path. Afterwards fetch the URL and read the
served bytes — a silent scp is not a deployed change.

## 4. Rewrite and router ordering

- **Apache serves an existing file before any rewrite.** A rule mapping `/sitemap.xml` to a generator
does nothing while a stale `sitemap.xml` sits in the docroot. Delete the file *and* add the rule, then
confirm the response body is generated (count `<loc>` hosts), not the old bytes.
- **Redirect blocks go above the catch-all** (`RewriteRule ^(.*)$ index.php`). If another rule also
targets `index.php` (a `/servicing` alias, say), whitelist that path inside any new PHP 404 guard or
it starts returning 404.
- **Put structured data and canonical output inside the same `$dsc404` guard as the 404 page.** Adding
a `url` field to JSON-LD on a router that echoes `REQUEST_URI` starts printing the requested junk path
into the head — a regression introduced by the fix, invisible unless you re-read a 404.
- Strip the query string when building canonicals (`strtok($uri, '?')`), or every `?filter=` view
self-canonicalises and competes with the clean page.

## 5. Verify over CDP, not by screenshot

Screenshots show appearance; they do not prove consent gating, first-run state or whether an element is
inside the viewport. Drive Chrome directly.

**Setup.** `websocket-client` is installed in system `python3` (not the Hermes venv). Launch with
`--headless=new --disable-gpu --no-sandbox --remote-debugging-port=N --user-data-dir=/tmp/<unique>`, read
the ws URL from `http://127.0.0.1:N/json` (pick `type == "page"`), then send CDP commands as JSON. Use a
**fresh** `--user-data-dir` per run: `localStorage` persists, so a second run silently skips the
first-visit path you are trying to test. Kill the process by its `Popen` handle — never
`pkill -f "Google Chrome"`, which takes out the agent's own browser.

**Layout defects.** Set `Emulation.setDeviceMetricsOverride(width, height, deviceScaleFactor, mobile)`
and, for every element in the header/nav/CTA, compare `getBoundingClientRect().right` against
`window.innerWidth`; report the furthest right edge and the slack.

Do **not** trust `document.documentElement.scrollWidth` on a site that ships `overflow-x: hidden` (or
`* { max-width: 100% }`): the overflow is clipped rather than scrollable, so `scrollWidth` reports no
problem while the primary CTA is cut off. That is exactly how a header can be broken at three widths and
pass every width check.

Test candidate CSS by injecting a `<style>` and re-measuring at several widths before deploying — it
turns a guess into a measured choice, and it lets you reject a fix that solves the layout by deleting a
feature (hiding a button that has no other entry point on those widths).

**Consent-gated analytics.** Enable `Network` before navigating, then:

1. Before consent, assert the banner is visible, `typeof window.gtag === 'undefined'`, no
   `googletagmanager` request, and no stored consent.
2. Click via `Runtime.evaluate` (`document.getElementById('cookieAccept').click()`).
3. **Drain the socket for several seconds.** CDP events are only consumed while a command is awaiting a
   response, so anything fired during a plain `sleep()` is never read and the beacon looks missing.
4. Assert both halves: `gtag/js?id=<ID>` requested, and a collect beacon to
   `region1.google-analytics.com/g/collect` carrying `tid=<ID>` in the query string.

`"No data received"` in GA4 is the expected state for a consent-gated install until a consented visit
happens — verify by network capture and tell the user to click Accept and watch Realtime, rather than
repeatedly reinstalling the tag.

## 6. Make the harness able to fail

A check that cannot fail converts "not checked" into "checked and clean". Two shapes seen in practice:

- A regex that only matches `9.9% APR` reports no APR problem on a page saying `APR 9.9%`.
- A presence test for `googletagmanager` in the HTML passes on a consent-gated loader that never fires,
  because the string is in the inline script. Assert on the measurement ID (`G-[A-Z0-9]{8,}`) or the
  network request instead.

Where a fix changes the canonical host, re-point the harness at the canonical host and make the
redirect check request the apex explicitly — otherwise every path check measures the 301, not the page.
