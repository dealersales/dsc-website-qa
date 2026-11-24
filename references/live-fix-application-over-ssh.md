# Applying fixes to a live dealer site over SSH

Use when the audit is done and the job is to *fix* the live site, not report it. The repo is a
snapshot, not a deployment source (credentials are `REDACTED-RUN-ON-SERVER`), so on these hosts the
change is made on the server and recorded afterwards.

## 0. Find the access you already have before asking for it

The user will push back, correctly, if you ask for credentials that are already configured. Check,
in this order, and only ask for what is genuinely missing:

```bash
ls ~/.ssh/ && grep -iE "^Host|hostname|user " ~/.ssh/config   # keys + named hosts
ssh -G <host> | head -5                                        # what would actually be used
git remote -v && gh auth status                                # repo + push rights
security find-generic-password -s <label> 2>&1 | head -5       # keychain item exists? (metadata only)
```

Also read the skills that cover the estate — access notes, ports and account names live in their
`references/`, not in the chat. A "we have no access" claim that turns out to be wrong costs more
credibility than any single finding.

## 1. Confirm the route and the account

```bash
nc -z -G 8 <server-ip> 65002            # Hostinger SSH is 65002, not 22
export SSHPASS="$(security find-generic-password -s <keychain-item> -w)"
sshpass -e ssh -o StrictHostKeyChecking=no -p 65002 <user>@<ip> 'whoami; ls ~/domains/ | head'
unset SSHPASS
```

`sshpass -e` reads the secret from the environment, so the password never appears in a command line,
a log, or the transcript. Never `-p <password>`. Never echo the variable.

Dealer docroots are `/home/<user>/domains/<domain>/public_html`. There is **no `.git` in the
docroot** — that is why the repo and the live site drift apart.

## 2. `~` expands on YOUR machine, not the server

This silently writes to the wrong place:

```bash
scp file $USER@host:~/domains/example.co.uk/public_html/   # ~ becomes /Users/you
D=~/domains/example.co.uk/public_html                      # same trap in a shell variable
```

Use the absolute remote path: `host:/home/<user>/domains/<domain>/public_html`. The failure message
names a local path you never typed, which is the tell.

## 3. Back up, then lint locally before uploading

```bash
ssh host 'cd <docroot> && cp -a index.php index.php.bak-YYYYMMDD'
cp file.php file.php.new && $PHP -l file.php.new     # PHP at ~/.local/php-static/php
```

Keep a copy of every original locally too, and write the exact rollback commands into the change log
before uploading. A copy of the file is the rollback; a described intention is not.

## 4. The recurring the platform fixes, as recipes

### Real 404 instead of a soft-404 homepage

Root cause is the `.htaccess` catch-all sending every unmatched path to `index.php`, which renders the
homepage with 200 and a canonical built from `REQUEST_URI`.

1. Guard at the top of `index.php`, **before** the header include.
2. **Allowlist every path the `.htaccess` deliberately routes to `index.php`** — grep for
   `index.php` in the file first; a `RewriteRule ^servicing$ index.php` means a naive guard turns that
   page into a 404.
3. Set `$dsc404 = true` and, in `includes/header.php`, skip the canonical and `og:url` when it is set.
   Without this the 404 page self-canonicalises and the finding is only half closed.
4. Drop the query string from the canonical (`strtok($_SERVER['REQUEST_URI'], '?')`) so `?make=`
filters consolidate onto the listing page instead of competing with it.

### A sitemap that lists another dealer's domain

Two independent faults, and fixing one looks like fixing both:

- **The generator's base URL is hardcoded.** Point it at the site's own host or config.
- **A stale static `sitemap.xml` shadows a correct generator.** Apache serves an existing file before
  any rewrite, so adding `RewriteRule ^sitemap\.xml$ sitemap.php [L]` changes nothing while the file
  sits there. Delete the file *and* add the rule, then confirm by counting hosts in the response.

Also check for `//` in generated vehicle URLs — a base ending in `/` concatenated with a path
starting in `/` produces `…co.uk//car/…`, which resolves but is a second URL for the same car.
`ltrim($path, '/')` fixes it.

### robots.txt

Ship a real `text/plain` file, not a soft-404. Disallow the build's admin and debug scripts, allow the
answer-engine crawlers by name, and declare the sitemap. Treat every path you list as public
knowledge; the better fix for a debug endpoint is to delete it.

### Legacy 301 map

Insert the rules **before** the catch-all, anchor vehicle patterns on a token the new URLs never carry
(on these builds, the trailing numeric AT id), then verify both directions: every archived URL
redirects, and no current URL is caught.

### Canonical host

One 301 at the very top of `.htaccess`. Whichever host wins, the sitemap base must match it or the
sitemap and the canonical will nominate different origins.

### Privacy notice, consent and analytics, when the site has none

- Page wrapper (`$pageTitle`, header, `custom/<page>.php`, footer) plus the content include — that is
the whole pattern for a new page on this build.
- Footer link **and** a consent line in the shared contact modal: that one include is the only form
  on the site, so one edit covers every page.
- Render the registered-company block only when the constant exists
  (`if (defined('DEALER_COMPANY_NO') && DEALER_COMPANY_NO)`), so no placeholder can ship and the block
turns itself on when the client confirms the entity.
- Consent banner: store the choice in `localStorage`, request **no** analytics script before consent,
  and expose a "Cookie settings" link that clears the stored choice. Keep the measurement ID as a
  single `define('GA4_MEASUREMENT_ID', '')` — with it empty the site is still compliant, and filling
  it in is a one-line change.

## 5. Verify with real Chrome, including at several widths

When the browser harness is slow or timing out, drive Chrome directly — it needs no daemon:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --virtual-time-budget=6000 --dump-dom https://<domain>/ > dom.html
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --hide-scrollbars --window-size=1280,900 --virtual-time-budget=6000 \
  --screenshot=/tmp/shot.png https://<domain>/
```

`--dump-dom` runs the JS, so it proves behaviour rather than markup: the consent banner flipping to
`display:block`, zero `googletagmanager` script tags before consent. **Screenshot at 1440, 1280 and
1100** — header overflow and a clipped primary CTA are invisible at one width and obvious across
three, and they are not detectable from HTML at all.

## 6. Make the verification harness able to fail

Every false pass in this class of work came from a check that could not fail:

- **After adding a canonical-host 301, request the canonical host.** A harness still pointed at the
  apex reports `301` for every path and scores working pages as broken; the apex check itself must
  request the apex explicitly, or it compares www with www and always passes.
- **Match both word orders** for a label-value pair: `9.9% APR` and `APR 9.9%`. One pattern silently
  finds nothing and the check passes as "only one rate on the site".
- **A loader string is not an installed product.** `googletagmanager` appearing in inline JS means the
  code is there; require a real `G-` measurement ID before scoring analytics as present.
- **Count hosts, not status codes,** for a sitemap; count `<loc>` values and compare against the
  site's own host.

Before trusting the score, feed each check one known-bad input and confirm it reports FAIL.

## 7. Record it

Write a change log beside the audit: files touched, backup filenames, rollback commands, what was
verified after, and what is still open with who owns it. If the site has a repo folder, mirror the
change there; if it does not, say so explicitly — an untracked live site is how the same defect ships
twice.
