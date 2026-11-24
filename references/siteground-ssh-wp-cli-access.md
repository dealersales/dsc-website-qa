# SiteGround SSH + WP-CLI access

The most reliable way into a client WordPress site on SiteGround: no bot challenge, no
browser, no REST nonce. Worth asking the client for up front whenever a job turns into a
list of live-site edits.

## Before touching anything: confirm the account owns the domain

SSH credentials are easy to mix up between client accounts, **and a wrong-account key will
authenticate quite happily**. Wrong credentials look like success until you read a
directory listing.

```bash
ssh -p 18765 -i ~/.ssh/<key> <user>@<server>.siteground.biz 'ls ~/www'
```

If the target domain is not in `~/www`, you have the wrong account — **stop and ask**; do
not edit. Then pin the install down:

```bash
cd ~/www/<domain>/public_html
wp option get siteurl     # proves the install really is that site
wp core version
```

One SiteGround account often carries two entries for the same client — the live domain and
a `<domain>.clickds.dev` staging site. Always `cd` into the intended one.

## A site you did not build: the `ssh.<account>.sg-host.com` gateway

Handed a staging URL you did not build (`<account>.sg-host.com`) and asked to review it, ask
the client for the three values on Site Tools → Devs → **SSH Keys Manager**: SSH hostname,
username, port. The hostname is a gateway of the form `ssh.<account>.sg-host.com`, and the
username is a `u<digits>-<random>` string — not the account's display name. Generate a key
**dedicated to that account** so it can be revoked on its own, hand over the public half only,
and confirm the landed server with `hostname` (the gateway resolves to something like
`uk46.siteground.eu` — record it, it is the direct route if you ever need it).

Keep the invocation self-contained rather than relying on a `~/.ssh/config` entry, which is
per-machine state that may be absent or bound to a different account:

```bash
ssh -i ~/.ssh/<key> -p 18765 \
  -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=25 \
  <user>@ssh.<account>.sg-host.com 'COMMAND'
```

`IdentitiesOnly=yes` stops the agent offering keys the account has never seen;
`StrictHostKeyChecking=accept-new` avoids an interactive host-key prompt on a first connect.

## Layout and binaries

| Thing | Where |
|-------|-------|
| Site roots | `~/www/<domain>/public_html` |
| WP-CLI | `/usr/local/bin/wp` (already on PATH) |
| Bedrock sites | nested deeper — see `wordpress-admin-operations` → `references/sage-bedrock-ssh-editing.md` |

## Which key? Try every one in `~/.ssh`

The key whose name *looks* right is not necessarily the one registered to the account.
`Permission denied (publickey)` from one key says nothing about the others.

```bash
for k in hermes_sg hermes-marketing-nicole id_ed25519; do
  echo "--- key: $k"
  ssh -p 18765 -i ~/.ssh/$k -o BatchMode=yes -o ConnectTimeout=15 \
      <user>@<server>.siteground.biz 'echo CONNECTED; pwd' 2>&1 | tail -1
done
```

`-o BatchMode=yes` keeps it non-interactive, so a missing key fails fast instead of hanging
on a password prompt. If none work, the key must be added under Site Tools → SSH Keys
Manager **for that account**.

## WP-CLI recipes for the usual client asks

```bash
# --- snapshot first; it makes every edit below reversible ---
wp db export ~/backup-$(date +%Y%m%d-%H%M).sql

wp post list --post_type=page --fields=ID,post_title,post_status --format=csv
wp post delete <id>                                        # trash a leftover demo post
wp post meta get <page-id> _elementor_data                 # Elementor page data
wp post meta update <item-id> _menu_item_url 'https://…'   # custom menu link URL
wp menu list                                               # menu ids
wp cache flush
wp sg purge                                                # SG Optimizer: dynamic cache + assets
wp option update blog_public 0                             # staging: noindex (see below)
```

Elementor data is JSON stored in post meta. For anything beyond a trivial change, write a
PHP script that `json_decode`s, edits and re-`json_encode`s, `scp` it up, and run
`wp eval-file` — **do not** sed/awk JSON.

Custom menu items keep their target in `_menu_item_url` post meta, so a stray `http://`
link on an `https` site is a one-line fix. Menu order is `menu_order`, 1-indexed — bump the
following items up before inserting a new item between them.

## Staging indexability: `blog_public`, not just `robots.txt`

A staging site left crawlable is both a duplicate-content source and a live-site de-indexing
bug on cutover — and the switch that matters is WordPress's own option, not a line in
`robots.txt`:

```bash
wp option get blog_public        # 1 = indexable, 0 = noindex, nofollow
wp option update blog_public 0
```

`0` makes `wp_robots()` emit `noindex, nofollow` in every page head. Check it first on any
staging site you are handed: it is the cheapest correct fix in the whole pre-launch list, one
option, and it reverts with `wp option update blog_public 1`.

**`blog_public 0` also disables the WordPress sitemap outright.** `wp_sitemaps_enabled()` returns
false, so `/wp-sitemap.xml` and every child index come back empty or 404 — on a staging build that
is the option doing its job, **not a missing or broken sitemap**, and writing it up as a finding
wastes a pass and undermines the real Criticals beside it. Confirm before reporting:

```bash
wp option get blog_public          # 0 -> the empty sitemap is expected
```

The pair moves together: `wp option update blog_public 1` restores the sitemap at cutover. Say so
in the cutover list rather than leaving the client to discover it. **When the `noindex` tag is
absent, check this option before you go hunting for a theme or plugin filter that strips it**
— on a handed-over build the usual answer is that nobody ever turned it off.

## Verifying after an edit

`wp post meta get` proves the data changed; it does not prove the page renders. To check
the front end without the workstation's network being involved, fetch the page **from the
server itself** — the server is not subject to the bot challenge that may be blocking local
requests:

```bash
ssh -p 18765 -i ~/.ssh/<key> <user>@<server>.siteground.biz \
  "curl -s https://<domain>/<path>/ | grep -c '<expected string>'"
```

Two things will make that check lie, and both produce a **false negative that reads as "the
fix did not apply"**:

**Match attributes quote-agnostically.** WordPress and Elementor print single-quoted
attributes — `<meta name='robots' content='noindex, nofollow' />` is the real output — so a
grep written against `name="robots"` finds nothing. Anchor on the tag name loosely and assert
on the **value**:

```bash
grep -o -iE "<meta[^>]+robots[^>]*>" page.html      # then require 'noindex' in the result
```

**Run the check as a script, not a heredoc, and quote the heredoc delimiter if you do.** The
shell expands an unquoted heredoc, so `python3 - <<PY` silently mangles every backslash on the
way through: `\x27`, `\"` and `\d+` arrive as `x27`, `"` and `d+`, and a pattern that relied on
them matches nothing or raises `SyntaxError`. Both read as a broken site. Use `python3 - <<'PY'`,
or better, `scp` the script up and run it — remote parsers are one of the places this bites most,
because the failure surfaces as a site-side symptom.

**Prove the URL is not answering from a cache.** A third-party render service and the host's
edge cache can each hand back a pre-change page long after the edit landed. When the served
value disagrees with the database, re-read from the server before believing the disagreement
— and purge (`wp sg purge`, `wp cache flush`) as part of the write, not as an afterthought.

## Pitfalls

- Wrong-account credentials authenticate cleanly; only `ls ~/www` reveals the mistake.
- One account can host several sites — confirm with `wp option get siteurl`, not the
  directory name alone.
- SiteGround's SSH port is **18765**, not 22.
- A key named after one client's project may be the one registered on a *different*
  client's account, because keys are added per SiteGround account, not per brand.
- Ask for SSH details **scoped to the right account** — "the SSH details" handed over may
  belong to whichever client's account was open in the host dashboard at the time.
- `wp post delete` **trashes** by default and is reversible with `wp post untrash <id>`; only
  `--force` is permanent. Prefer the trash on a build someone else owns.
- `wp sg purge` may report `Unable to Purge File Cache` beside two successes. That warning is
  benign when the file cache is not enabled; the dynamic cache and the assets folder are the
  two that matter.
- **Read `wp plugin list` early — it is the fastest way to learn what the site is actually
  built from.** It exposes form plugins, importers and kit tooling that no amount of front-end
  inspection will show you, and it identifies the template kit a handed-over build came from
  before you have looked at a single page. See `elementor-cloned-site-contamination.md`.
