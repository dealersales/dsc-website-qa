# URL migration & the Elementor element cache

Proven on Four Plus 4 (fourplus4.co.uk), Sep 2026 — a WordPress + Elementor site
that had been built on a SiteGround staging domain (`paulw466.sg-host.com`) and
migrated to its live domain. 653 stale URL references were hiding in the DB.

## The two separate problems

A site migration leaves **two** classes of stale URL, and they need different
fixes:

1. **Stored URLs** — in `postmeta`, `posts`, `options`. Fix with `wp search-replace`.
2. **Cached renders** — Elementor caches rendered widget HTML. `search-replace`
   cannot see it and does not fix it. See below.

Symptom of (2): the front end shows an old URL, but the *stored* Elementor data
and `wp_get_attachment_url()` both return the correct new URL. Everything at the
WordPress level looks right; only the rendered page is wrong. Do not keep
re-running search-replace — it will report 0 and you will go in circles.

## Watch out for escaped slashes

Elementor stores `_elementor_data` as JSON, so URLs are escaped:
`https:\/\/example.com\/wp-content\/...`

A scheme-qualified search like `http://old-domain.com` therefore matches almost
nothing. **Search on the bare host** (`old-domain.com`) — it has no slashes and
matches both the escaped and plain forms:

```bash
wp search-replace 'old-domain.com' 'new-domain.com' --all-tables --precise --report-changed-only
```

Then normalise the scheme separately, covering both forms:

```bash
wp search-replace 'http:\/\/new-domain.com' 'https:\/\/new-domain.com' --all-tables --precise
wp search-replace 'http://new-domain.com/' 'https://new-domain.com/' --all-tables --precise   # trailing slash protects siteurl
```

## Procedure

1. **Back up first.** `wp db export ~/backup/db-before-$TS.sql --tables=<prefix>_postmeta,<prefix>_posts,<prefix>_options`
2. **Find the table prefix.** It is often not `wp_` — read it from `wp db tables`.
3. **Dry-run the scope:** `wp search-replace 'old-host' '@@X@@' --all-tables --dry-run`
4. **Replace the bare host**, then normalise the scheme (commands above).
5. **Set siteurl/home to https** if the site serves https: `wp option update siteurl` / `home`.
   Leaving them on http makes dynamically-built URLs (e.g. attachment URLs) come
   out http even when every stored URL is https.
6. **Delete the Elementor element cache** (the step everyone misses):
   ```bash
   wp db query "DELETE FROM <prefix>_postmeta WHERE meta_key='_elementor_element_cache';"
   ```
7. **Clear remaining caches:**
   ```bash
   wp eval 'if (class_exists("\\Elementor\\Plugin")) { \\Elementor\\Plugin::$instance->files_manager->clear_cache(); }'
   wp sg purge          # SiteGround: purges Speed Optimizer assets + dynamic cache
   ```
   Also delete stale `wp-content/uploads/siteground-optimizer-assets/siteground-optimizer-combined-css-*.css`
   files — they hold thousands of pre-migration URLs and must be regenerated.
8. **Verify on the rendered page, not the DB.** Crawl each page and count
   `old-host` and `http://` occurrences in the *rendered HTML*. The DB can be
   spotless while the page still serves stale URLs.

## Verification that actually proves it

```bash
for pg in / /about-us/ /contact-us/; do
  HTML=$(curl -s -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36' "https://domain$pg")
  echo "$pg sg-host=$(echo "$HTML" | grep -c 'old-host') http-refs=$(echo "$HTML" | grep -c 'http://domain')"
done
```

## Other gotchas seen alongside this

- **SiteGround blocks a burst of connections.** Repeated SSH/curl from one IP
  gets the IP firewalled on the SSH port for a few minutes ("Operation timed
  out"), and heavy curl escalates to `sgcaptcha` (an HTTP 202 with a
  `/.well-known/sgcaptcha/` redirect). Wait it out, batch work into fewer
  connections, or route via a VPN.
- **`/contact-us/` returning 403 for one user-agent but 200 for another** is the
  hosting anti-bot, not a site fault. Test with a full Chrome UA before flagging.
- **Attachment-derived URLs** (e.g. a logo rendered from an attachment ID) are
  built at render time from `siteurl`/`wp_upload_dir()["baseurl"]` — fix those by
  correcting `siteurl`, not by editing the widget.
- **A leftover batch of helper `.php` files in the account home dir** is common
  after an SSH-applied fix. Move them into the backup folder when done; keep the
  DB exports for rollback.
- **A staged replace leaves hybrid fragments that the full-string count misses.**
  When a swap has been run in more than one pass — or an earlier attempt only
  partially matched — the stored value ends up holding a hybrid: a stray
  character left over from the old value fused to the new one. `wp
  search-replace` then reports `0` changes and a `COUNT()` of the full old string
  returns zero, while the wrong text is still rendering. This reads as "the
  replace worked and the cache is stale", which sends you chasing caches that
  are innocent. After any bulk replace, assert **both** that the full old token
  returns zero **and** that obvious fragments of it return zero, on the rendered
  HTML as well as in the DB.
