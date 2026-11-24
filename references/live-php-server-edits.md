# Applying fixes to a live dealer site over SSH

The estate's the platform builds are raw PHP on Hostinger, not WordPress. Fixes are made by editing files
on the server: the `dsc-websites` repo holds a **sanitised** copy (credentials replaced with
`REDACTED-RUN-ON-SERVER`) and is explicitly not a deploy artefact, so `git pull` onto a live site
breaks it.

## Before touching anything

- **Confirm the site is in the repo before assuming a branch fix reached it.** A build with no
  folder in `dsc-websites` never receives the estate-wide patches, however many commits the branch
  carries. Grep the repo for the domain: zero hits means the fixes must be applied by hand.
- **Prove access read-only first.** SSH to the Hostinger account on **port 65002** (not 22), sites at
  `~/domains/<domain>/public_html`. The credential lives in the macOS Keychain (`<keychain-item>`); load it
  into the environment with `security find-generic-password -s <keychain-item> -w` and `sshpass -e`, never
  echo it. `ls` the docroot before changing a byte.
- **Never print a config file.** `config.php` / `custom/config.php` hold stock-API keys and dealer
  credentials. Change them by targeted string substitution with a count printed, not by `cat`.

## Procedure

1. **Back up every file you will touch — outside the docroot.**
   ```bash
   mkdir -p ~/backups/<site>/<date>
   cp -a index.php ~/backups/<site>/<date>/index.php
   ```
   A `.bak` left beside the original is a public file: `config.php.bak` is downloadable source with
   its keys in it, and `.htaccess.bak` may be readable too. Move all backups out, then request one
   backup URL and confirm it 404s.
2. **Pull the file down, patch it locally, lint it locally.** There is no system PHP on the Mac; use
   the static binary at `~/.local/php-static/php` (`php -l file.php`). Never upload unlinted PHP.
3. **Upload with an ABSOLUTE remote path.**
   ```bash
   # WRONG - ~ expands on the local machine, so scp targets /Users/... and fails
   D=~/domains/example.co.uk/public_html
   sshpass -e scp -P 65002 file.php user@host:$D/file.php
   # RIGHT
   sshpass -e scp -P 65002 file.php user@host:/home/uXXXX/domains/example.co.uk/public_html/file.php
   ```
4. **Smoke-test within seconds of the upload**, before the next file: homepage plus two or three key
   pages plus the specific behaviour you changed. A `.htaccess` typo 500s the whole site; the backup
   and restore command should already be in your scrollback.
5. **Keep a change log with rollback commands** in the client folder, listing every file changed, the
   backup path, and what was verified. That file is what lets the next session undo a bad deploy.

## Pitfalls that cost time on this stack

- **Apache serves an existing static file before any rewrite.** Routing `/sitemap.xml` to a generator
  does nothing while a stale `sitemap.xml` sits on disk — the commonest cause of "the generator is
  correct but the live sitemap is another dealer's". Delete the file *and* add the rule.
- **A catch-all rewrite makes every unknown path the homepage with a 200.** Guarding that in
  `index.php` is right, but the allow-list must include the paths `.htaccess` deliberately maps to
  `index.php` (a `/servicing` alias, for instance) or they start returning 404.
- **A 404 guard must suppress structured data as well as the canonical.** Guarding `rel=canonical`
  and `og:url` is not enough: adding a JSON-LD `url` built from `REQUEST_URI` puts the junk path back
  into the head. Wrap the whole `ld+json` block in the same flag.
- **A canonical-host redirect changes every absolute URL in the build.** Decide apex vs `www` before
  touching anything else, then make the sitemap generator's base match it — otherwise the sitemap and
  the canonical disagree and you have swapped one duplicate-host problem for another. Prefer whichever
  host already carries the inbound links and the generator's base.
- **Do not strip a fixed string across the site and stop at the first match.** The same wording appears
  in page content, includes, config and a `<strong>`-wrapped variant; grep for the *concept* and list
  every hit before and after.

## The verification harness is part of the fix

Write one script that scores the live site (sitemap hosts, 404 status, redirect families, robots
content-type, canonical host, consent, email MX, schema) and re-run it after every change. Two rules
for the harness itself, because a false pass is worse than no check:

- **Every check must be able to fail on a known-bad input.** A pattern that only matches one word
  order misses the other: `\d+\.\d% APR` finds nothing in `APR 9.9%`, and an "analytics present" test
  that matches the loader string passes on a page with no measurement ID at all.
- **When the canonical host changes, the harness's own base URL must change with it.** Otherwise every
  path check follows a 301 and reports the redirect as the result — a whole page of false failures
  that looks like a site regression.
